"""Portable tests: partial writes, privacy, stage errors and suite ordering."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('full_test', Path(__file__).with_name('full_test.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LauncherTests(unittest.TestCase):
    def test_partial_lines_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events'
            reader = module.Lines(path)
            self.assertEqual(reader.read(), [])
            path.write_bytes(b'{"event":')
            self.assertEqual(reader.read(), [])
            with path.open('ab') as stream:
                stream.write(b'"ready"}\nnext\npartial')
            self.assertEqual(reader.read(), ['{"event":"ready"}', 'next'])
            self.assertEqual(reader.read(), [])

    def test_console_filters_secrets_and_deduplicates_phases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'acceptance').mkdir()
            (root / 'gnb-acceptance.log').write_text(
                'private-secret-do-not-print\n'
                'STKSCHEDULE UL IQ=39.000000 STK=8239.000000 satellite_id=OAI_LEO_P01_S06 '
                'elevation_deg=5.000 visible=1 switched=0 phase=prepare previous=OAI_LEO_P01_S06 '
                'next=OAI_LEO_P01_S05 samples=299520000 private-secret-do-not-print\n'
                'STKSCHEDULE UL IQ=39.100000 STK=8239.100000 satellite_id=OAI_LEO_P01_S06 '
                'elevation_deg=5.000 visible=1 switched=0 phase=prepare previous=OAI_LEO_P01_S06 '
                'next=OAI_LEO_P01_S05 samples=300288000\n')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                monitor = module.Live(root)
                monitor.poll(force=True)
                monitor.poll(force=True)
            text = output.getvalue()
            self.assertEqual(text.count('phase=prepare'), 1)
            self.assertIn('IQ=39.000s STK=8239.000s', text)
            self.assertNotIn('private-secret', text)

    def test_worker_pending_not_mislabeled_as_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / 'acceptance'
            evidence.mkdir()
            events = [dict(event='send', sequence=1, send_ns=1),
                      dict(event='send', sequence=2, send_ns=1),
                      dict(event='receive', sequence=1, wall_rtt_ms=123, duplicate=False)]
            (evidence / 'ping.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in events))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                module.Live(root).poll(force=True)
            self.assertIn('ping:sent=2 received=1 pending=1 pending_over_5s=1', output.getvalue())
            self.assertNotIn('loss=', output.getvalue())

    def test_child_exit_failure_and_output_private(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = module.Runner(root, root, dict(os.environ))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                with self.assertRaises(RuntimeError):
                    runner.stage('failed-child', [sys.executable, '-c',
                        "print('private-secret-do-not-print');raise SystemExit(7)"], timeout=10)
            self.assertEqual(runner.records[0]['exit'], 7)
            self.assertNotIn('private-secret', output.getvalue())
            self.assertIn('private-secret', (root/'failed-child.private.log').read_text())

    def test_matrix_order_and_parameters(self):
        self.assertEqual([c for c, _ in module.CASES],
                         ['firsthandover', 'firsthandover', 'full', 'legacy', 'static'])
        self.assertEqual(len({suffix for _, suffix in module.CASES}), 5)
        self.assertEqual(module.PARAMETERS['OAI_NTN_PUSCH_FAILURE_THRES'], '100')
        self.assertEqual(module.PARAMETERS['OAI_NTN_PDCP_REORDERING_MS'], '500')

    def test_acceptance_failure_still_stops_modems_and_core(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / '.runtime/runs/integrated-handover/example-first-a'
            run.mkdir(parents=True)
            (run/'run.json').write_text('{}')
            runner = module.Runner(root, root, {})
            calls = []
            def stage(name, *_args, **_kwargs):
                calls.append(name)
                if name == 'first-a-acceptance':
                    raise RuntimeError('simulated failed acceptance')
            with mock.patch.object(runner, 'stage', side_effect=stage):
                with self.assertRaisesRegex(RuntimeError, 'simulated failed acceptance'):
                    runner.case('firsthandover', 'first-a', 'example')
            self.assertEqual(calls, ['first-a-core-up', 'first-a-core-health', 'first-a-acceptance',
                                     'first-a-stop-check', 'first-a-core-down'])

    def test_cleanup_failure_does_not_prevent_core_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / '.runtime/runs/integrated-handover/example-first-a'
            run.mkdir(parents=True)
            (run/'run.json').write_text('{}')
            runner = module.Runner(root, root, {})
            calls = []
            def stage(name, *_args, **_kwargs):
                calls.append(name)
                if name in ('first-a-acceptance', 'first-a-stop-check'):
                    raise RuntimeError('simulated failure')
            with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(runner, 'stage', side_effect=stage):
                with self.assertRaises(RuntimeError):
                    runner.case('firsthandover', 'first-a', 'example')
            self.assertEqual(calls[-1], 'first-a-core-down')

    @unittest.skipUnless(sys.platform == 'linux', 'Linux process-group cleanup')
    def test_timeout_interrupts_owned_child(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = module.Runner(root, root, dict(os.environ))
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'Stage wall timeout'):
                    runner.stage('timeout-child', [sys.executable, '-c', 'import time;time.sleep(60)'], timeout=.1)
            self.assertIsNotNone(runner.records[0]['exit'])
            self.assertLess(runner.records[0]['wall_seconds'], 10)


if __name__ == '__main__':
    unittest.main()
