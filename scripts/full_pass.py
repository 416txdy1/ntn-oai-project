"""以 IQ 时钟覆盖示例完整轨迹；持续 ping 和双向各 100 Kbit/s UDP。"""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'local_ntn'
FS = 7680000.0
NUMERIC = re.compile(r'STKTRACE2 (UL|DL) IQ=([\d.]+) STK=([\d.]+).*?valid=(\d+) samples=(\d+)')

def run(*args, **kwargs):
    return subprocess.run(list(args), check=True, **kwargs)

def finish(process, sig=signal.SIGINT, timeout=8):
    if process.poll() is None:
        process.send_signal(sig)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)

def numeric_state(path):
    text = path.read_text(errors='replace') if path.exists() else ''
    rows = [(int(m[5]) / FS, int(m[4])) for m in NUMERIC.finditer(text)]
    return rows, text

def udp_summary(path):
    data = json.loads(path.read_text())
    end = data.get('end', {})
    value = end.get('sum_received') or end.get('sum')
    if not value or value.get('sender', False) or value.get('packets', 0) <= 0:
        raise ValueError('missing UDP receiver counters: ' + path.name)
    result = {k: value.get(k) for k in ('seconds', 'bytes', 'bits_per_second', 'jitter_ms', 'lost_packets', 'packets', 'lost_percent')}
    result['interrupted'] = bool(data.get('error'))
    result['bytes_source'] = 'final_summary'
    # iperf3 被 SIGINT 中断时可能把 end.bytes 清零；保留事实并使用分段接收字节数。
    if result['bytes'] == 0:
        intervals = [item.get('sum', {}) for item in data.get('intervals', [])]
        if not intervals or any(item.get('sender', False) for item in intervals):
            raise ValueError('missing receiver interval counters: ' + path.name)
        result['reported_final_bytes'] = 0
        result['bytes'] = sum(item.get('bytes', 0) for item in intervals)
        result['bits_per_second'] = result['bytes'] * 8 / result['seconds']
        result['bytes_source'] = 'receiver_intervals'
        if result['bytes'] <= 0:
            raise ValueError('no received UDP bytes: ' + path.name)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-wall-seconds', type=int, default=1800)
    args = parser.parse_args()
    if args.max_wall_seconds < 120:
        parser.error('max wall seconds must be >=120')
    if os.geteuid() != 0:
        parser.error('run as root after source scripts/env.sh')
    trace = Path(os.environ['OAI_STK_TRACE'])
    rows = list(csv.reader(s for s in trace.read_text().splitlines()[1:] if s and not s.startswith('#')))
    duration = float(rows[-1][0]) - float(rows[0][0])
    if duration != 361:
        parser.error('this acceptance profile requires the bundled 361-second trace')
    # STKTRACE2 每一秒输出一次；最后有效记录约为 360.999 秒。
    target = duration - .1
    os.umask(0o077)
    reports = ROOT / '.runtime/reports'
    reports.mkdir(parents=True, exist_ok=True)
    label = 'fullpass-' + str(time.time_ns())
    output = reports / label
    output.mkdir()
    report = {'label': label, 'rate': 1, 'trace_duration_s': duration,
              'target_last_logged_iq_s': target, 'interpolation': os.environ.get('OAI_STK_TRACE_INTERPOLATION', 'hermite'), 'blend_timing_assist': os.environ.get('OAI_STK_BLEND_TIMING_ASSIST', '0'), 'passed': False}
    processes = []
    handles = []
    owned = False
    started = time.monotonic()
    def spawn(name, command):
        handle = (output / (name + '.log')).open('w')
        handles.append(handle)
        process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT)
        processes.append(process)
        return process
    try:
        # 拒绝接管其他正在运行的 modem。
        for name in ('nr-softmodem', 'nr-uesoftmodem'):
            if subprocess.run(['pgrep', '-x', name], stdout=subprocess.DEVNULL).returncode == 0:
                raise RuntimeError('existing modem: ' + name)
        with (output / 'start.log').open('w') as log:
            owned = True
            run('python3', str(BASE / 'experiment.py'), 'start', '--rate', '1', '--label', label,
                stdout=log, stderr=subprocess.STDOUT, timeout=90)
        deadline = time.monotonic() + 120
        address = None
        while time.monotonic() < deadline:
            result = subprocess.run(['ip', '-n', 'oai-stk-ue', '-j', '-4', 'addr', 'show', 'dev', 'oaitun_ue1'], capture_output=True, text=True)
            if result.returncode == 0:
                address = next((a['local'] for item in json.loads(result.stdout) for a in item.get('addr_info', []) if a.get('scope') == 'global'), None)
                if address:
                    break
            time.sleep(.5)
        if not address:
            raise RuntimeError('PDU timeout')
        report['pdu_ready'] = True
        run('python3', str(BASE / 'verify_network.py'), stdout=subprocess.DEVNULL)
        destination = os.environ['OAI_EXT_DN_IP']
        container = json.loads(subprocess.check_output(['docker', 'inspect', os.environ['OAI_EXT_DN_CONTAINER']]))[0]
        if not container['State']['Running']:
            raise RuntimeError('ext-DN is not running')
        run('ip', '-n', 'oai-stk-ue', 'route', 'replace', destination + '/32', 'dev', 'oaitun_ue1', 'src', address)
        iperf = ['env', 'LD_LIBRARY_PATH=' + os.environ['OAI_IPERF3_LIBRARY_PATH'], os.environ['OAI_IPERF3_BIN']]
        server_prefix = ['nsenter', '-t', str(container['State']['Pid']), '-n']
        ue_prefix = ['ip', 'netns', 'exec', 'oai-stk-ue']
        servers = [spawn(direction + '-server', server_prefix + iperf + ['-s', '-1', '-p', str(port), '-J']) for direction, port in [('uplink', 5203), ('downlink', 5204)]]
        time.sleep(.4)
        if any(p.poll() is not None for p in servers):
            raise RuntimeError('iperf server failed; inspect local private logs')
        ping = spawn('ping', ue_prefix + ['python3', str(ROOT / 'scripts/monotonic_ping.py'), '--destination', destination, '--interface', 'oaitun_ue1', '--report', str(output / 'ping.json')])
        clients = [spawn(direction + '-client', ue_prefix + iperf + ['-c', destination, '-p', str(port), '-B', address, '-u', '-b', '100K', '-t', str(args.max_wall_seconds + 60), '-i', '10', '-J'] + flags) for direction, port, flags in [('uplink', 5203, []), ('downlink', 5204, ['-R'])]]
        report['traffic_start_iq_s'] = {}
        for kind in ('gnb', 'ue'):
            records, _ = numeric_state(BASE / f'{kind}-{label}.log')
            report['traffic_start_iq_s'][kind] = records[-1][0] if records else None
        print(json.dumps({'label': label, 'state': 'traffic_started', 'traffic_start_iq_s': report['traffic_start_iq_s']}), flush=True)
        last_progress = time.monotonic()
        previous = -1
        next_message = 0
        while True:
            values = {}
            for kind in ('gnb', 'ue'):
                records, _ = numeric_state(BASE / f'{kind}-{label}.log')
                values[kind] = records[-1][0] if records else 0
                if any(valid != 1 for iq, valid in records if iq <= duration):
                    raise RuntimeError('invalid trace inside valid interval: ' + kind)
            progress = min(values.values())
            now = time.monotonic()
            if progress > previous:
                previous = progress
                last_progress = now
            if now >= next_message:
                ping_text = (output / 'ping.log').read_text(errors='replace')
                print(json.dumps({'wall_s': round(now - started, 1), 'iq_s': values, 'ping_replies': ping_text.count('bytes from')}), flush=True)
                next_message = now + 30
            if progress >= target:
                report['end_trigger_iq_s'] = values
                report['reached_end'] = True
                break
            if any(p.poll() is not None for p in clients + servers + [ping]):
                raise RuntimeError('traffic process exited before trace end')
            if now - last_progress > 60:
                raise RuntimeError('IQ clock stalled for 60 wall seconds')
            if now - started > args.max_wall_seconds:
                raise RuntimeError('wall clock deadline before trace end')
            time.sleep(.1)
    except Exception as error:
        report['error'] = str(error)
    finally:
        # 先停止流量，再停止本次启动的 modem；服务器仅限本脚本的 Popen 句柄。
        for process in locals().get('clients', []):
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
        if 'ping' in locals():
            finish(ping)
        for process in locals().get('clients', []):
            finish(process)
        for process in locals().get('servers', []):
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                finish(process)
        for process in processes:
            if process.poll() is None:
                finish(process)
        for handle in handles:
            handle.close()
        if owned:
            result = subprocess.run(['python3', str(BASE / 'experiment.py'), 'stop'], capture_output=True, text=True, timeout=25)
            report['stop_exit'] = result.returncode
        report['wall_seconds'] = time.monotonic() - started
        try:
            ping_text = (output / 'ping.log').read_text()
            counters = json.loads((output / 'ping.json').read_text())
            report['ping'] = {**counters, 'clock_backwards': False}
            report['uplink'] = udp_summary(output / 'uplink-server.log')
            report['downlink'] = udp_summary(output / 'downlink-client.log')
            for direction, sender_log in [('uplink', 'uplink-client.log'), ('downlink', 'downlink-server.log')]:
                sender_end = json.loads((output / sender_log).read_text()).get('end', {})
                sender = sender_end.get('sum_sent') or sender_end.get('sum')
                if not sender or not sender.get('sender') or sender.get('packets', 0) <= 0:
                    raise ValueError('missing sender counters: ' + sender_log)
                report[direction]['sent_packets'] = sender['packets']
                report[direction]['sent_minus_received_packets'] = sender['packets'] - report[direction]['packets']
                # 收发结束时刻可能不同；差额不能直接当丢包率，也不能当成零丢包。
            for kind in ('gnb', 'ue'):
                records, text = numeric_state(BASE / f'{kind}-{label}.log')
                valid = [iq for iq, flag in records if flag == 1 and iq <= duration]
                report[kind] = {'valid_iq_interval_s': [min(valid), max(valid)], 'valid_rows': len(valid), 'exhausted_log_rows': text.count('STKTRACE2 exhausted'), 'qd_loaded': text.count('QDCHANNEL1 loaded'), 'trace_loaded': text.count('STKTRACE2 loaded'), 'pbch_failures': text.count('Error decoding PBCH'), 'blend_timing_logs': text.count('STK blend timing:')}
            report['passed'] = bool(report.get('reached_end') and 'error' not in report and report.get('stop_exit') == 0 and report['ping']['sent'] == report['ping']['received'] and not report['ping']['clock_backwards'] and all(report[d]['lost_packets'] == 0 and report[d]['sent_minus_received_packets'] == 0 for d in ('uplink', 'downlink')) and all(report[k]['qd_loaded'] == report[k]['trace_loaded'] == 1 and report[k]['pbch_failures'] == 0 for k in ('gnb', 'ue')))
        except Exception as error:
            report['summary_error'] = str(error)
        (reports / (label + '.json')).write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), flush=True)
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
