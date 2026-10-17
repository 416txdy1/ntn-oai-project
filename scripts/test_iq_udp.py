"""验证 IQ 负载预算及真实 UDP 双向收发，不需要 OAI 或 root。"""
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from typing import Callable

from iq_udp import packet_budget, summarize, write_json


class IqUdpTests(unittest.TestCase):
    def test_budget(self) -> None:
        self.assertEqual(packet_budget(100, 100), 0)
        self.assertEqual(packet_budget(100, 101), 10)
        self.assertEqual(packet_budget(100, 196), 1000)
        for current in (99, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                packet_budget(100, current)

    def test_missing_tail_is_loss(self) -> None:
        result = summarize({'sent': [[0, 1], [1, 2]], 'start_iq': 0, 'last_iq': 2,
                            'sending_wall_seconds': 20}, {'received': [[0, 1]]})
        self.assertEqual(result['missing_sequences'], [1])
        self.assertEqual(result['missing_send_iq_s'], [2])
        self.assertEqual(result['sent_bits_per_iq_second'], 9600)
        self.assertEqual(result['bits_per_second'], 480)

    def test_loopback_clock_freeze_and_bidirectional_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clock = root / 'clock.json'
            write_json(clock, {'start': 10, 'current': 10, 'running': False})
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.bind(('127.0.0.1', 0))
                port = probe.getsockname()[1]
            processes = []
            paths = [root / f'{index}.json' for index in (1, 2)]
            def read() -> list:
                return [json.loads(path.read_text()) for path in paths]
            def wait_for(predicate: Callable[[list], bool]) -> list:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if all(path.exists() for path in paths):
                        states = read()
                        if predicate(states):
                            return states
                    time.sleep(.03)
                self.fail('probe checkpoint timed out')
            try:
                for index, path in zip((1, 2), paths):
                    processes.append(subprocess.Popen([sys.executable, str(Path(__file__).with_name('iq_udp.py')),
                        '--bind', f'127.0.0.{index}', '--peer', f'127.0.0.{3-index}', '--port', str(port),
                        '--clock', str(clock), '--report', str(path), '--token', '12' * 16]))
                wait_for(lambda states: all(s['ready'] for s in states))
                write_json(clock, {'start': 10, 'current': 11, 'running': True})
                wait_for(lambda states: all(len(s['sent']) == len(s['received']) == 10 for s in states))
                time.sleep(1.2)
                self.assertTrue(all(len(s['sent']) == 10 for s in read()))
                write_json(clock, {'start': 10, 'current': 12.4, 'running': True})
                wait_for(lambda states: all(len(s['sent']) == len(s['received']) == 25 for s in states))
                for process in processes:
                    process.send_signal(signal.SIGINT)
                for process in processes:
                    self.assertEqual(process.wait(timeout=8), 0)
                states = read()
                self.assertTrue(all(s['complete'] for s in states))
                self.assertEqual(summarize(*states)['lost_packets'], 0)
                self.assertAlmostEqual(summarize(*states)['sent_bits_per_iq_second'], 100000)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                        process.wait()


if __name__ == '__main__':
    unittest.main()
