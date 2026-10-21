"""独立审计完整IQ业务，保留strict结果，只豁免已约定的旧尾段。"""
import argparse
import bisect
import json
from pathlib import Path

from iq_udp import packet_budget, summarize

# gNB STKTRACE2记录在整秒前约1ms；这是日志边界误差，不是扩大尾段1秒。
TAIL_LOG_BOUNDARY = 357.0 - .0011


def audit(report_path: Path) -> dict:
    report = json.loads(report_path.read_text())
    run = report_path.with_suffix('')
    probes = {role: json.loads((run / f'{role}-iq-udp.json').read_text()) for role in ('ue', 'dn')}
    observations = [json.loads(line) for line in (run / 'iq-observations.jsonl').read_text().splitlines()]
    times = [row['monotonic_s'] for row in observations]
    failures = []
    def require(condition: bool, reason: str) -> None:
        if not condition:
            failures.append(reason)
    require(report['traffic_clock'] == 'iq' and report['trace_duration_s'] == 361 and report['rate'] == 1, 'wrong experiment profile')
    require(report.get('reached_end') and report.get('stop_exit') == 0 and not report.get('error') and not report.get('summary_error'), 'incomplete run')
    require(bool(observations) and times == sorted(times), 'invalid IQ observation timeline')
    result = {'label': report['label'], 'strict_passed': report['passed'],
              'tail_log_boundary_s': TAIL_LOG_BOUNDARY,
              'boundary_note': '旧尾段357秒；gNB日志约提前1ms。发包IQ是最近样本日志读数，不宣称逐包精确物理时刻。',
              'directions': {}, 'failures': failures}
    for direction, sender, receiver in [('uplink', probes['ue'], probes['dn']), ('downlink', probes['dn'], probes['ue'])]:
        summary = summarize(sender, receiver)
        require(sender.get('complete') and receiver.get('complete') and not sender.get('error') and not receiver.get('error'), direction + ': incomplete probe')
        require(sender.get('peer_ready') and sender.get('ack_received', 0) > 0, direction + ': handshake absent')
        require(len(sender['sent']) == packet_budget(sender['start_iq'], sender['last_iq']), direction + ': wrong offered load')
        require(sender['start_iq'] < 10 and sender['last_iq'] >= 360.9, direction + ': insufficient coverage')
        require(not summary['unexpected_sequences'] and summary['invalid_packets'] == 0 and summary['duplicate_packets'] == 0, direction + ': invalid/duplicate packets')
        early = [seq for seq in summary['missing_sequences'] if sender['sent'][seq][1] < TAIL_LOG_BOUNDARY]
        require(not early, direction + ': packet loss before allowed tail')
        delays = [(row[3] - sender['sent'][int(row[0])][2]) for row in receiver['received'] if int(row[0]) < len(sender['sent'])]
        result['directions'][direction] = {**summary, 'early_missing_sequences': early,
            'max_one_way_wall_seconds': max(delays, default=None)}
    ping = report['ping']
    require(ping['sent'] > 0 and ping['sent'] - ping['received'] == len(ping['missing_sequences']), 'invalid ping counters')
    missing_ping = []
    for sequence in ping['missing_sequences']:
        sent = ping['sent_monotonic_ns'][str(sequence)] / 1e9
        index = bisect.bisect_right(times, sent) - 1
        iq = min(observations[index]['iq_s'].values()) if index >= 0 else -1
        missing_ping.append({'sequence': sequence, 'preceding_iq_s': iq})
        require(iq >= TAIL_LOG_BOUNDARY, 'ping loss before allowed tail: ' + str(sequence))
    result['missing_ping_locations'] = missing_ping
    location = json.loads(report_path.with_name(report_path.stem + '-fidelity-location.json').read_text())
    for role in ('gnb', 'ue'):
        modem = report[role]
        require(modem['qd_loaded'] == modem['trace_loaded'] == 1, role + ': channel/trace not loaded exactly once')
        require(modem['valid_iq_interval_s'][1] >= 360.9, role + ': IQ coverage incomplete')
        failure = location['modems'][role]['first_failure_preceding_iq_s']
        require(not modem['pbch_failures'] or failure is not None and failure >= TAIL_LOG_BOUNDARY, role + ': early PBCH failure')
    result['accepted_with_known_tail'] = not failures
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.report)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({'label': result['label'], 'accepted_with_known_tail': result['accepted_with_known_tail'], 'failures': result['failures']}, ensure_ascii=False))
    return 0 if result['accepted_with_known_tail'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
