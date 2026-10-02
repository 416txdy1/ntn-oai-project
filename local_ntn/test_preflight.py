"""启动预检查、进程环境隔离与失败清理回归；不启动真实 modem。"""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import signal
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

from preflight import channel_environments, read_trace, check_template, check_bundle
from paths import OAI_REPO


class PreflightTest(unittest.TestCase):
    def test_direction_and_independent_environments(self):
        original = {'OAI_QD_DL_CHANNEL': '/tmp/downlink', 'OAI_QD_UL_CHANNEL': '/tmp/uplink'}
        children = channel_environments(original)
        self.assertEqual(children['gnb']['OAI_QD_CHANNEL'], '/tmp/uplink')
        self.assertEqual(children['ue']['OAI_QD_CHANNEL'], '/tmp/downlink')
        children['gnb']['new'] = 'value'
        self.assertNotIn('new', children['ue'])
        self.assertNotIn('OAI_QD_CHANNEL', original)

    def test_stk_only(self):
        self.assertNotIn('OAI_QD_CHANNEL', channel_environments({})['gnb'])

    def test_missing_direction_rejected(self):
        for env in ({'OAI_QD_DL_CHANNEL': '/tmp/dl'}, {'OAI_QD_UL_CHANNEL': '/tmp/ul'}):
            with self.assertRaisesRegex(ValueError, '同时指定'):
                channel_environments(env)

    def test_shared_bundle_rejected(self):
        with self.assertRaisesRegex(ValueError, '不能共用'):
            channel_environments({'OAI_QD_CHANNEL': '/tmp/shared'})

    def test_template_frequency_guard(self):
        original = (OAI_REPO / 'ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf').read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'template.conf'
            path.write_text(original)
            check_template(path)
            path.write_text(original.replace('497230', '497231'))
            with self.assertRaisesRegex(ValueError, '载频'):
                check_template(path)

    def test_bundle_direction_and_frequency_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            path = bundle / 'manifest.json'
            path.write_text(json.dumps({'radio': {'link_direction': 'uplink', 'center_frequency_hz': 2e9}}))
            with self.assertRaisesRegex(ValueError, '方向错误'):
                check_bundle(bundle, bundle / 'trace.csv', 'downlink', 2488400000)
            with self.assertRaisesRegex(ValueError, '载频'):
                check_bundle(bundle, bundle / 'trace.csv', 'uplink', 1614900000)

    def test_trace_time_and_finite_guards(self):
        row = [0, 7000000, 0, 0, 100, 0, 0, 0, 0, 0, 6377900, 0, 0, 6377900, 0, 0, -100, -100, 20, 20, 1, 1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.csv'
            def write(second):
                path.write_text('STKTRACE2\n' + '\n'.join(','.join(map(str, values)) for values in [row, second]) + '\n')
            write([1, *row[1:]])
            self.assertEqual(len(read_trace(path)), 2)
            write(row)
            with self.assertRaisesRegex(ValueError, '递增'): read_trace(path)
            write([float('nan'), *row[1:]])
            with self.assertRaisesRegex(ValueError, '有限'): read_trace(path)

    def test_launcher_uses_selected_build_trace_and_frequency(self):
        with tempfile.TemporaryDirectory(prefix='qd launch ') as directory:
            root = Path(directory)
            here = Path(__file__).parent
            for name in ('paths.py', 'run_local.sh'):
                shutil.copy2(here / name, root / name)
            build = root / 'chosen build'
            build.mkdir()
            stub = '#!/usr/bin/env python3\nimport os,json,sys\nprint(json.dumps({"trace":os.environ["OAI_STK_TRACE"],"library":os.environ["LD_LIBRARY_PATH"],"args":sys.argv[1:]}))\n'
            for name in ('nr-softmodem', 'nr-uesoftmodem'):
                path = build / name
                path.write_text(stub)
                path.chmod(0o755)
            (root / 'verify_network.py').write_text('')
            (root / 'initial_delay_ms.txt').write_text('15\n')
            ip = root / 'ip'
            ip.write_text('#!/bin/sh\nshift 3\nexec "$@"\n')
            ip.chmod(0o755)
            trace = root / 'chosen trace.csv'
            env = dict(os.environ, OAI_BUILD_DIR=str(build), OAI_STK_TRACE=str(trace),
                       PATH=str(root) + os.pathsep + os.environ['PATH'])
            for kind in ('gnb', 'ue'):
                result = subprocess.run(['bash', str(root / 'run_local.sh'), kind], env=env,
                                        text=True, capture_output=True, check=True)
                payload = json.loads(result.stdout)
                self.assertEqual(payload['trace'], str(trace))
                self.assertEqual(payload['library'].split(':')[0], str(build))
                if kind == 'ue':
                    args = payload['args']
                    self.assertEqual(args[args.index('-C') + 1], '2488400000')
                    self.assertEqual(args[args.index('--CO') + 1], '-873500000')

    def test_stop_waits_for_owned_exit_and_preserves_unowned(self):
        source = Path(__file__).with_name('experiment.py').read_text()
        for needs_kill in (False, True):
            with self.subTest(needs_kill=needs_kill), tempfile.TemporaryDirectory() as directory:
                script = Path(directory) / 'experiment.py'
                script.write_text(source)
                state = Path(directory) / 'processes.json'
                state.write_text(json.dumps({'gnb': {'pid': 42000, 'start': '123'},
                                             'ue': {'pid': 42001, 'start': 'old'}}))
                live = {42000: '123', 42001: 'reused'}
                clock = [0.0]
                term = [False]
                real_read = Path.read_text
                def read(path, *args, **kwargs):
                    if str(path).startswith('/proc/'):
                        value = live.get(int(path.parts[2]))
                        if value is None: raise FileNotFoundError()
                        return ' '.join(['0'] * 21 + [value])
                    return real_read(path, *args, **kwargs)
                def kill(pid, sig):
                    self.assertEqual(pid, 42000)
                    if sig == signal.SIGTERM: term[0] = True
                    else: live.pop(pid)
                def sleep(seconds):
                    clock[0] += seconds
                    if term[0] and not needs_kill and clock[0] >= .3:
                        live.pop(42000, None)
                with patch.object(sys, 'argv', [str(script), 'stop']), \
                     patch.object(Path, 'read_text', read), patch('os.killpg', side_effect=kill) as kills, \
                     patch('time.sleep', side_effect=sleep), patch('time.monotonic', side_effect=lambda: clock[0]), \
                     contextlib.redirect_stdout(io.StringIO()):
                    runpy.run_path(str(script), run_name='__main__')
                self.assertGreaterEqual(clock[0], 10 if needs_kill else .3)
                self.assertEqual(kills.call_count, 2 if needs_kill else 1)
                self.assertEqual(live, {42001: 'reused'})
                self.assertEqual(json.loads(state.read_text()), {})

    def test_start_failure_cleans_only_created_groups(self):
        # 运行真实 controller 代码，隔离所有进程/网络调用和输出文件。
        source = Path(__file__).with_name('experiment.py').read_text()
        for failed_kind in ('gnb', 'ue'):
            with self.subTest(failed_kind=failed_kind), tempfile.TemporaryDirectory() as directory:
                script = Path(directory) / 'experiment.py'
                script.write_text(source)
                created = []
                real_read = Path.read_text
                def read(path, *args, **kwargs):
                    if str(path).startswith('/proc/'):
                        return ' '.join(['0'] * 21 + ['123'])
                    return real_read(path, *args, **kwargs)
                def popen(command, **kwargs):
                    kind = command[-1]
                    process = Mock(pid=42000 + len(created))
                    process.poll.return_value = 1 if kind == failed_kind else None
                    kwargs['stdout'].write('No connected device\n')
                    kwargs['stdout'].flush()
                    created.append(process)
                    return process
                def run(command, **kwargs):
                    return subprocess.CompletedProcess(command, 1 if command[0] == 'pgrep' else 0)
                with patch.object(sys, 'argv', [str(script), 'start']), \
                     patch('preflight.preflight', return_value={}), patch('network_config.check_network', return_value={}), \
                     patch('os.geteuid', return_value=0), patch('subprocess.run', side_effect=run), \
                     patch('subprocess.Popen', side_effect=popen), patch.object(Path, 'read_text', read), \
                     patch('os.killpg') as kill, patch('time.sleep'), \
                     patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(SystemExit, 'exited'):
                        runpy.run_path(str(script), run_name='__main__')
                self.assertEqual(kill.call_count, len(created))
                for process in created:
                    kill.assert_any_call(process.pid, signal.SIGTERM)
                    process.wait.assert_called_once_with(timeout=5)
                self.assertEqual(json.loads((Path(directory) / 'processes.json').read_text()), {})


if __name__ == '__main__':
    unittest.main()
