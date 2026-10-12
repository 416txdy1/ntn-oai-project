"""Isolated pseudo handover compatibility probes; full IQ acceptance is separate."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from runtime_config import resolve_runtime
from run_state import process_identity
from slice_trace import read_pair

BASE = Path(__file__).resolve().parent


def build_plan(config, tag, duration, rate, initial_lead):
    _, _, header, schedule, times = read_pair(config.trace, config.schedule)
    selector = ['--profile', config.profile, '--run-id', config.run_id]
    def experiment(action, *args):
        return [sys.executable, str(BASE / 'experiment.py'), action, *selector, *args]
    phase = header.index('handover_phase') if 'handover_phase' in header else None
    return {'profile': config.profile, 'run_id': config.run_id, 'namespace': config.namespace,
            'run_dir': str(config.run_dir), 'environment': config.to_env(),
            'trace': {'path': str(config.trace), 'rows': len(times), 'start': times[0], 'stop': times[-1]},
            'schedule': {'path': str(config.schedule), 'complete_stk_s':
                         [float(row[0]) for row in schedule if phase is not None and row[phase] == 'complete']},
            'commands': {
                'core': [sys.executable, str(BASE.parent / 'scripts/core_lab.py'), 'preflight', *selector],
                'start': experiment('start', '--rate', str(rate), '--label', tag,
                                    '--initial-lead-rfsim', str(initial_lead)),
                'stop': experiment('stop'), 'status': experiment('status'),
                'namespace_probe': ['ip', '-n', config.namespace, '-4', 'addr', 'show', 'dev', 'oaitun_ue1'],
                'ping': experiment('ping', '--ping-count', str(duration)),
                'uplink': experiment('iperf', '--iperf-seconds', str(duration)),
                'downlink': experiment('iperf', '--iperf-seconds', str(duration), '--reverse')},
            'logs': {name: str(config.run_dir / f'{name}-seamless-{tag}.txt')
                     for name in ('controller', 'ping', 'uplink', 'downlink')}}


def stop_probe(process, identity):
    if process.poll() is not None:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if identity is not None and process_identity(process.pid) == identity:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass
    raise RuntimeError('Owned traffic process shutdown timed out')


def execute_plan(config, plan, duration, environment):
    if os.geteuid() != 0:
        raise ValueError('requires root: use sudo -E python3 local_ntn/test_seamless.py '
                         f'--profile {config.profile} --run-id {config.run_id}')
    env = dict(environment)
    env.update(config.to_env())
    # No implicit core startup: preflight validates only this profile/project.
    subprocess.run(plan['commands']['core'], env=env, check=True, capture_output=True)
    config.run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    streams = {}
    probes = []
    started = False
    try:
        for name, path in plan['logs'].items():
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            streams[name] = os.fdopen(fd, 'w')
        subprocess.run(plan['commands']['start'], env=env, check=True,
                       stdout=streams['controller'], stderr=subprocess.STDOUT)
        started = True
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            result = subprocess.run(plan['commands']['namespace_probe'], env=env, capture_output=True, text=True)
            if result.returncode == 0 and 'inet ' in result.stdout:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('No PDU session within 60 wall seconds')
        def launch(name):
            process = subprocess.Popen(plan['commands'][name], env=env, stdout=streams[name],
                                       stderr=subprocess.STDOUT, start_new_session=True)
            probes.append((process, process_identity(process.pid)))
            return process
        ping = launch('ping')
        uplink = launch('uplink')
        codes = {'uplink': uplink.wait(timeout=duration * 6 + 60)}
        # Both directions use the existing traffic controller port; do not overlap servers.
        downlink = launch('downlink')
        codes['downlink'] = downlink.wait(timeout=duration * 6 + 60)
        codes['ping'] = ping.wait(timeout=duration * 6 + 60)
        subprocess.run(plan['commands']['status'], env=env, check=True,
                       stdout=streams['controller'], stderr=subprocess.STDOUT)
        print(json.dumps({'compatibility_probe_exit_codes': codes,
                          'full_iq_handover_acceptance': 'not evaluated'}))
        return 0 if all(code == 0 for code in codes.values()) else 1
    finally:
        try:
            for process, identity in probes:
                stop_probe(process, identity)
        finally:
            try:
                if started:
                    subprocess.run(plan['commands']['stop'], env=env, check=True,
                                   stdout=streams['controller'], stderr=subprocess.STDOUT)
            finally:
                for stream in streams.values():
                    stream.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='')
    parser.add_argument('--run-id', default='')
    parser.add_argument('--tag', default='seamless-20260924')
    parser.add_argument('--duration', type=int, default=620)
    parser.add_argument('--rate', type=float, default=float(os.environ.get('OAI_STK_TRACE_RATE', '0.1')))
    parser.add_argument('--initial-lead-rfsim', type=float,
                        default=float(os.environ.get('OAI_STK_INITIAL_LEAD_RFSIM', '0')))
    parser.add_argument('--dry-run', action='store_true', help='print non-secret argv/config; no system changes')
    args = parser.parse_args(argv)
    try:
        if args.duration < 1 or not math.isfinite(args.rate) or not 0 < args.rate <= 1:
            raise ValueError('duration must be positive; rate must be finite in (0, 1]')
        if not math.isfinite(args.initial_lead_rfsim) or args.initial_lead_rfsim < 0:
            raise ValueError('initial lead must be finite and nonnegative')
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]+', args.tag):
            raise ValueError('invalid tag')
        profile = args.profile or os.environ.get('OAI_NTN_PROFILE') or 'integrated-handover'
        config = resolve_runtime(BASE.parent, profile, args.run_id, os.environ)
        if config.schedule is None:
            raise ValueError('pseudo handover probes require a selected trace/schedule pair')
        plan = build_plan(config, args.tag, args.duration, args.rate, args.initial_lead_rfsim)
        if args.dry_run:
            print(json.dumps(plan, indent=2))
            return 0
        return execute_plan(config, plan, args.duration, os.environ)
    except (ValueError, OSError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        # Captured child output can contain credentials; never echo it here.
        parser.exit(1, f'Pseudo handover probe refused ({type(error).__name__}): '
                    + (str(error) if not isinstance(error, subprocess.SubprocessError) else 'child command failed') + '\n')


if __name__ == '__main__':
    sys.exit(main())
