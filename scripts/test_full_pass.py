"""验收器的接收端统计和 IQ 时间解析回归。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('full_pass', Path(__file__).with_name('full_pass.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class AcceptanceParsingTests(unittest.TestCase):
    def test_receiver_summary_uses_receiver(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'udp.json'
            path.write_text(json.dumps({'end': {'sum_received': {'sender': False, 'packets': 123, 'lost_packets': 2, 'bytes': 1000}, 'sum_sent': {'sender': True, 'packets': 125}}}))
            result = module.udp_summary(path)
            self.assertEqual(result['packets'], 123)
            self.assertEqual(result['lost_packets'], 2)

    def test_sender_and_empty_traffic_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'udp.json'
            for value in ({'sender': True, 'packets': 10}, {'sender': False, 'packets': 0}):
                path.write_text(json.dumps({'end': {'sum': value}}))
                with self.assertRaises(ValueError):
                    module.udp_summary(path)

    def test_sample_counter_is_time_authority(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'numeric.log'
            path.write_text('STKTRACE2 DL IQ=0.000000 STK=7883.000000 delay=14.700000ms Doppler=0.000Hz gain=0.000dB C/N=30.000dB valid=1 samples=7680000\n')
            records, _ = module.numeric_state(path)
            self.assertEqual(records, [(1.0, 1)])

    def test_actual_nondefault_sample_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'numeric.log'
            path.write_text('STKTRACE2 DL IQ=0.000000 STK=8200.000000 valid=1 samples=1000\n')
            self.assertEqual(module.numeric_state(path,2000),([(.5,1)],path.read_text()))

    def test_interrupted_summary_recovers_interval_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'udp.json'
            path.write_text(json.dumps({'error': 'interrupt', 'end': {'sum': {'sender': False, 'packets': 20, 'lost_packets': 0, 'seconds': 10, 'bytes': 0}}, 'intervals': [{'sum': {'sender': False, 'bytes': 100}}, {'sum': {'sender': False, 'bytes': 150}}]}))
            result = module.udp_summary(path)
            self.assertEqual(result['bytes'], 250)
            self.assertEqual(result['bits_per_second'], 200)
            self.assertEqual(result['bytes_source'], 'receiver_intervals')
            self.assertEqual(result['reported_final_bytes'], 0)
            self.assertTrue(result['interrupted'])

    def test_missing_log_is_not_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(module.numeric_state(Path(folder) / 'missing'), ([], ''))

class TraceContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('continuity', Path(__file__).with_name('audit_trace_continuity.py'))
        cls.audit_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.audit_module)

    def rows(self):
        result = []
        for time in (0, 1):
            row = [0.0] * 22
            row[0] = time
            row[1] = 7000000 + 7000*time
            row[4] = 7000
            row[13] = 6371000
            result.append(row)
        return result

    def test_consistent_straight_track_passes(self):
        self.assertTrue(self.audit_module.audit(self.rows(), 20000)['passed'])

    def test_blended_position_with_unchanged_velocity_fails(self):
        rows = self.rows()
        rows[1][1] += 760000
        result = self.audit_module.audit(rows, 20000)
        self.assertFalse(result['passed'])
        self.assertGreater(result['issues'][0]['sampled_hermite_max_speed_km_s'], 1000)

if __name__ == '__main__':
    unittest.main()
