"""尾部例外必须拒绝首批缺包，不能把strict失败改写成strict通过。"""
import json
from pathlib import Path
import tempfile
import unittest

from audit_iq_business import audit
from iq_udp import packet_budget


class AuditTests(unittest.TestCase):
    def test_tail_exception_and_early_loss(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / 'fullpass-fixture'
            run.mkdir()
            report_path = run.with_suffix('.json')
            start, end = 3.999, 360.999
            count = packet_budget(start, end)
            sent = [[i, start + (i + 1) * .096, (i + 1) * .96] for i in range(count)]
            received = [[i, sent[i][1], sent[i][1], sent[i][2] + .1] for i in range(count - 1)]
            probe = {'sent': sent, 'received': received, 'start_iq': start, 'last_iq': end,
                     'sending_wall_seconds': 3570, 'complete': True, 'peer_ready': True, 'ack_received': 1}
            for role in ('ue', 'dn'):
                (run / f'{role}-iq-udp.json').write_text(json.dumps(probe))
            (run / 'iq-observations.jsonl').write_text('\n'.join(json.dumps({'monotonic_s': i * 10,
                'iq_s': {'gnb': start + i, 'ue': start + i}}) for i in range(358)))
            modem = {'qd_loaded': 1, 'trace_loaded': 1, 'valid_iq_interval_s': [2, end], 'pbch_failures': 200}
            report = {'label': run.name, 'passed': False, 'traffic_clock': 'iq', 'trace_duration_s': 361,
                'rate': 1, 'reached_end': True, 'stop_exit': 0, 'gnb': modem, 'ue': modem,
                'ping': {'sent': 10, 'received': 9, 'missing_sequences': [10], 'sent_monotonic_ns': {'10': int(3560.5e9)}}}
            report_path.write_text(json.dumps(report))
            location = {'modems': {role: {'first_failure_preceding_iq_s': 356.99955} for role in ('gnb', 'ue')}}
            (root / 'fullpass-fixture-fidelity-location.json').write_text(json.dumps(location))
            result = audit(report_path)
            self.assertTrue(result['accepted_with_known_tail'], result['failures'])
            self.assertFalse(result['strict_passed'])
            # 原首批缺包必须触发失败；不允许尾部例外吞掉早期故障。
            probe['received'] = received[10:]
            (run / 'ue-iq-udp.json').write_text(json.dumps(probe))
            result = audit(report_path)
            self.assertFalse(result['accepted_with_known_tail'])
            self.assertEqual(result['directions']['downlink']['early_missing_sequences'], list(range(10)))
            (run / 'ue-iq-udp.json').write_text(json.dumps({**probe, 'received': received}))
            report['ping']['sent_monotonic_ns']['10'] = int(3000e9)
            report_path.write_text(json.dumps(report))
            self.assertIn('ping loss before allowed tail: 10', audit(report_path)['failures'])


if __name__ == '__main__':
    unittest.main()
