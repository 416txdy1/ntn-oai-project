"""Run ownership regressions; every process and network boundary is mocked."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import Mock, patch

from runtime_config import resolve_runtime
from run_state import process_identity, stop_owned
import experiment


class RunStateTest(unittest.TestCase):
    def write_state(self, root, run='mine'):
        path = root / 'processes.json'
        path.write_text(json.dumps({'schema': 2, 'run_id': run, 'processes': {
            'gnb': {'pid': 42000, 'start': '123', 'executable': '/build/nr-softmodem'},
            'ue': {'pid': 42001, 'start': '124', 'executable': '/build/nr-uesoftmodem'}}}))
        return path

    def test_process_identity_handles_comm_and_zombie(self):
        fields = ['S'] + ['0'] * 18 + ['123'] + ['0'] * 4
        with patch.object(Path, 'read_text', return_value='42000 (name with ) spaces) ' + ' '.join(fields)), \
             patch('os.readlink', return_value='/build/nr-softmodem'):
            self.assertEqual(process_identity(42000), ('123', '/build/nr-softmodem'))
        fields[0] = 'Z'
        with patch.object(Path, 'read_text', return_value='42000 (gone) ' + ' '.join(fields)):
            self.assertIsNone(process_identity(42000))

    def test_stop_ignores_reused_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.write_state(Path(directory))
            live = {42000: ('123', '/build/nr-softmodem'), 42001: ('999', '/build/nr-uesoftmodem')}
            clock = [0.0]
            def kill(pid, sig):
                self.assertEqual(pid, 42000)
                if sig == signal.SIGKILL: live.pop(pid)
            with patch('run_state.process_identity', side_effect=lambda pid: live.get(pid)), \
                 patch('os.killpg', side_effect=kill) as signals, \
                 patch('time.monotonic', side_effect=lambda: clock[0]), \
                 patch('time.sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0]+seconds)):
                stop_owned(state, 'mine')
            self.assertEqual(signals.call_args_list[0].args, (42000, signal.SIGTERM))
            self.assertEqual(signals.call_args_list[-1].args, (42000, signal.SIGKILL))
            self.assertIn(42001, live)
            self.assertGreaterEqual(clock[0], 10)

    def test_stop_ignores_other_run(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.write_state(Path(directory), 'other')
            original = state.read_bytes()
            with patch('os.killpg') as signals:
                with self.assertRaisesRegex(ValueError, 'run'): stop_owned(state, 'mine')
            signals.assert_not_called()
            self.assertEqual(original, state.read_bytes())

    def test_executable_mismatch_and_timeout_retain_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            state = self.write_state(Path(directory))
            with patch('run_state.process_identity', return_value=('123', '/foreign')), \
                 patch('os.killpg') as signals:
                stop_owned(state, 'mine')
            signals.assert_not_called()
            state = self.write_state(Path(directory))
            clock = [0.0]
            with patch('run_state.process_identity', side_effect=lambda pid: ('123','/build/nr-softmodem') if pid==42000 else None), \
                 patch('os.killpg'), patch('time.monotonic', side_effect=lambda: clock[0]), \
                 patch('time.sleep', side_effect=lambda s: clock.__setitem__(0,clock[0]+s)):
                with self.assertRaisesRegex(RuntimeError, 'timed out'): stop_owned(state, 'mine')
            self.assertIn('gnb', json.loads(state.read_text())['processes'])

    def test_launch_failure_cleans_only_started(self):
        for failed_kind in ('gnb', 'ue'):
            with self.subTest(kind=failed_kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = resolve_runtime(root, 'legacy-handover', 'failure', {})
                config.run_dir.mkdir(parents=True)
                processes = []
                def popen(command, **kwargs):
                    kind = command[-1]
                    process = Mock(pid=42000+len(processes))
                    process.poll.return_value = 1 if kind == failed_kind else None
                    kwargs['stdout'].write('No connected device\n')
                    kwargs['stdout'].flush()
                    processes.append(process)
                    return process
                def identity(pid):
                    kind='gnb' if pid==42000 else 'ue'
                    return ('123' if pid==42000 else '124', '/bin/bash' if kind==failed_kind else str(config.build_dir/('nr-softmodem' if kind=='gnb' else 'nr-uesoftmodem')))
                with patch('experiment.preflight', return_value={}), \
                     patch('experiment.check_network', return_value={}), \
                     patch('experiment.build_manifest', return_value={'run_id':'failure','network':{},'logs':{}}), \
                     patch('experiment.NetworkManager') as network, \
                     patch('experiment.read_trace', return_value=[[0]*22]), patch('experiment.call'), patch('os.geteuid', return_value=0), \
                     patch('subprocess.run', return_value=Mock(returncode=1)), \
                     patch('subprocess.Popen', side_effect=popen), \
                     patch('experiment.process_identity', side_effect=identity), \
                     patch('experiment.stop_owned') as stop, patch('time.sleep'), \
                     contextlib.redirect_stdout(io.StringIO()):
                    network.return_value.up.return_value={}
                    with self.assertRaisesRegex(SystemExit, 'exited'):
                        experiment.start(config, Mock(rate=0, label='failure', initial_lead_rfsim=0), {})
                    stop.assert_called_once_with(config.state_file, 'failure')
                    network.return_value.down.assert_called_once()
                records = json.loads(config.state_file.read_text())['processes']
                self.assertEqual({v['pid'] for v in records.values()}, {p.pid for p in processes})
                self.assertTrue((config.run_dir/'run.json').is_file())

    def test_shell_exec_transition_records_authoritative_modem(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=resolve_runtime(root,'legacy-handover','ready',{})
            sequence={42000:iter([('123','/bin/bash'),('123',str(config.build_dir/'nr-softmodem'))]),
                      42001:iter([('124','/bin/bash'),('124',str(config.build_dir/'nr-uesoftmodem'))])}
            created=[]
            def popen(argv,**kwargs):
                process=Mock(pid=42000+len(created));process.poll.return_value=None
                kwargs['stdout'].write('No connected device\n');kwargs['stdout'].flush()
                created.append(process);return process
            with patch('experiment.preflight',return_value={}), patch('experiment.check_network',return_value={}), \
                 patch('experiment.build_manifest',return_value={'run_id':'ready','network':{},'logs':{}}), patch('experiment.NetworkManager') as network, \
                 patch('experiment.read_trace',return_value=[[0]*22]), patch('experiment.call'), patch('os.geteuid',return_value=0), \
                 patch('subprocess.run',return_value=Mock(returncode=1)), patch('subprocess.Popen',side_effect=popen), \
                 patch('experiment.process_identity',side_effect=lambda pid:next(sequence[pid])), \
                 patch('time.sleep'),contextlib.redirect_stdout(io.StringIO()):
                network.return_value.up.return_value={}
                experiment.start(config,Mock(rate=0,label='ready',initial_lead_rfsim=0),{})
            records=json.loads(config.state_file.read_text())['processes']
            self.assertEqual(records['gnb']['executable'],str(config.build_dir/'nr-softmodem'))
            self.assertEqual(records['ue']['executable'],str(config.build_dir/'nr-uesoftmodem'))
            with patch('experiment.preflight') as check:
                with self.assertRaisesRegex(ValueError,'exists'):
                    network.return_value.up.return_value={}
                experiment.start(config,Mock(rate=0,label='ready',initial_lead_rfsim=0),{})
                check.assert_not_called()

    def test_sample_rate_must_be_observed_on_both_sides(self):
        self.assertIsNone(experiment.observed_sample_rate({'gnb':'unrelated 7680000','ue':'unrelated 7680000'}))
        self.assertEqual(experiment.observed_sample_rate({'gnb':'sample_rate_hz=7680000','ue':'sample_rate_hz=7680000'}),7680000)
        self.assertIsNone(experiment.observed_sample_rate({'gnb':'sample_rate_hz=7680000','ue':''}))
        with self.assertRaisesRegex(ValueError,'sample rate'):
            experiment.observed_sample_rate({'gnb':'sample_rate_hz=7680000','ue':'sample_rate_hz=15360000'})


if __name__=='__main__':unittest.main()


