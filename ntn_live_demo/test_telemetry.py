"""Ensure displayed channel fields come from structured observations and expire."""
from pathlib import Path
import tempfile
import unittest
from demo import load_helpers
from telemetry import RadioTelemetry


class TelemetryTests(unittest.TestCase):
    def test_direction_parameters_and_partial_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);log=root/'ue-live-demo.log'
            log.write_text('private credentials never forwarded\nSTKTRACE2 DL IQ=73.000000 STK=8273.000000 delay=14.964000ms Doppler=23090.700Hz gain=-0.030dB C/N=3.834dB valid=1 samples=560640000')
            reader=RadioTelemetry(load_helpers(),root);reader.poll()
            self.assertEqual(reader.snapshot(),{},'An incomplete physical line is not a new observation')
            with log.open('a') as stream:stream.write('\n')
            reader.poll();dl=reader.snapshot(74)['dl']
            self.assertEqual(dl['cn_db'],3.834);self.assertEqual(dl['doppler_hz'],23090.7)
            self.assertEqual(dl['delay_ms'],14.964);self.assertEqual(dl['lag_iq_s'],1)
            self.assertNotIn('private',str(dl));observed=dl['observed_host_monotonic_ns']
            reader.poll();self.assertEqual(reader.snapshot(80)['dl']['observed_host_monotonic_ns'],observed)
            self.assertEqual(reader.snapshot(80)['dl']['lag_iq_s'],7)

    def test_uplink_is_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'gnb-live-demo.log').write_text('STKTRACE2 UL IQ=73.000000 STK=8273.000000 delay=14.964000ms Doppler=14985.100Hz gain=-0.030dB C/N=13.590dB valid=1 samples=560640000\n')
            reader=RadioTelemetry(load_helpers(),root);reader.poll()
            self.assertEqual(set(reader.snapshot()),{'ul'})
            self.assertEqual(reader.snapshot()['ul']['cn_db'],13.59)


if __name__=='__main__':unittest.main()
