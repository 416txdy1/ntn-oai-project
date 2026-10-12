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
            for name in ('paths.py', 'run_local.sh', 'runtime_config.py'):
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
                       OAI_NTN_RUN_DIR=str(root),OAI_GNB_CONFIG=str(root/'gnb.local.conf'),
                       OAI_INITIAL_DELAY_FILE=str(root/'initial_delay_ms.txt'),
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

    def test_legacy_stop_waits_and_preserves_unowned(self):
        from run_state import stop_owned
        for needs_kill in (False,True):
            with self.subTest(needs_kill=needs_kill),tempfile.TemporaryDirectory() as directory:
                state=Path(directory)/'processes.json'
                state.write_text(json.dumps({'gnb':{'pid':42000,'start':'123'},'ue':{'pid':42001,'start':'old'}}))
                live={42000:('123','/build/nr-softmodem'),42001:('reused','/build/nr-uesoftmodem')}
                clock=[0.0];term=[False]
                def kill(pid,sig):
                    self.assertEqual(pid,42000)
                    if sig==signal.SIGTERM:term[0]=True
                    else:live.pop(pid)
                def sleep(seconds):
                    clock[0]+=seconds
                    if term[0] and not needs_kill and clock[0]>=.3:live.pop(42000,None)
                with patch('run_state.process_identity',side_effect=lambda pid:live.get(pid)), \
                     patch('os.killpg',side_effect=kill) as signals, \
                     patch('time.monotonic',side_effect=lambda:clock[0]),patch('time.sleep',side_effect=sleep):
                    stop_owned(state,'default')
                self.assertGreaterEqual(clock[0],10 if needs_kill else .3)
                self.assertEqual(signals.call_count,2 if needs_kill else 1)
                self.assertEqual(live,{42001:('reused','/build/nr-uesoftmodem')})
                self.assertEqual(json.loads(state.read_text()),{})

class ProfilePreflightTest(unittest.TestCase):
    def test_isolated_launcher_uses_run_port_epoch_and_only_selected_libraries(self):
        from runtime_config import resolve_runtime
        with tempfile.TemporaryDirectory(prefix='isolated launcher ') as directory:
            root=Path(directory)
            scripts=root/'local_ntn'
            scripts.mkdir()
            for name in ('runtime_config.py','run_local.sh'):
                shutil.copy2(Path(__file__).parent/name,scripts/name)
            (scripts/'verify_network.py').write_text('')
            config=resolve_runtime(root,'legacy-handover','launcher',{})
            config.build_dir.mkdir(parents=True)
            config.run_dir.mkdir(parents=True)
            config.initial_delay_file.write_text('15\n')
            stub='#!/usr/bin/env python3\nimport os,json,sys\nprint(json.dumps({"epoch":os.environ.get("OAI_STK_TRACE_EPOCH"),"rate":os.environ["OAI_STK_TRACE_RATE"],"library":os.environ["LD_LIBRARY_PATH"],"args":sys.argv[1:]}))\n'
            for name in ('nr-softmodem','nr-uesoftmodem'):
                binary=config.build_dir/name
                binary.write_text(stub)
                binary.chmod(0o755)
            ip=root/'ip'
            ip.write_text('#!/bin/sh\nshift 3\nexec "$@"\n')
            ip.chmod(0o755)
            env={k:v for k,v in os.environ.items() if not k.startswith('OAI_')}
            env.update(config.to_env())
            env.update(OAI_STK_TRACE_EPOCH='8200',OAI_STK_TRACE_RATE='1',LD_LIBRARY_PATH='/foreign-build',
                       PATH=str(root)+os.pathsep+os.environ['PATH'])
            for kind in ('gnb','ue'):
                result=subprocess.run(['bash',str(scripts/'run_local.sh'),kind],env=env,text=True,capture_output=True,check=True)
                payload=json.loads(result.stdout)
                self.assertEqual(payload['epoch'],'8200')
                self.assertEqual(payload['rate'],'1')
                self.assertEqual(payload['library'],str(config.build_dir))
                args=payload['args']
                self.assertEqual(args[args.index('--rfsimulator.[0].serverport')+1],'4044')
                if kind=='gnb':self.assertEqual(args[args.index('-O')+1],str(config.gnb_config))
                else:
                    self.assertEqual(args[args.index('--rfsimulator.[0].serveraddr')+1],'10.202.0.1')
                    self.assertEqual(args[args.index('-O')+1],str(config.ue_config))

            contaminated=dict(env,OAI_NTN_RUN_DIR=str(scripts))
            result=subprocess.run(['bash',str(scripts/'run_local.sh'),'gnb'],env=contaminated,text=True,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('escapes',result.stderr)
            self.assertNotIn('"args"',result.stdout)

    def test_integrated_producer_launcher_and_real_verify_boundary(self):
        import experiment
        from runtime_config import resolve_runtime
        with tempfile.TemporaryDirectory(prefix='integrated boundary ') as directory:
            root=Path(directory)
            scripts=root/'local_ntn'
            scripts.mkdir()
            for name in ('runtime_config.py','run_local.sh','network_owner.py'):
                shutil.copy2(Path(__file__).parent/name,scripts/name)
            shutil.copy2(Path(__file__).parent/'verify_network.py',scripts/'verify_impl.py')
            # Run the real verification CLI/resolver, mocking only privilege/kernel manager.
            (scripts/'verify_network.py').write_text('''import os,runpy
from pathlib import Path
from unittest.mock import patch
def verify(claim=False):
    assert not os.environ.get('OAI_QD_CHANNEL'), 'generic channel leaked into verification'
    Path(os.environ['VERIFY_MARKER']).write_text('verified')
with patch('os.geteuid',return_value=0),patch('network_owner.NetworkManager') as manager:
    manager.return_value.verify.side_effect=verify
    runpy.run_path(str(Path(__file__).with_name('verify_impl.py')),run_name='__main__')
''')
            config=resolve_runtime(root,'integrated-handover','boundary',{})
            config.build_dir.mkdir(parents=True)
            config.run_dir.mkdir(parents=True)
            config.initial_delay_file.write_text('15\n')
            stub='#!/usr/bin/env python3\nimport os,json,sys\nprint(json.dumps({"qd":os.environ.get("OAI_QD_CHANNEL"),"args":sys.argv[1:]}))\n'
            for name in ('nr-softmodem','nr-uesoftmodem'):
                binary=config.build_dir/name
                binary.write_text(stub)
                binary.chmod(0o755)
            ip=root/'ip'
            ip.write_text('#!/bin/sh\nshift 3\nexec "$@"\n')
            ip.chmod(0o755)
            env={k:v for k,v in os.environ.items() if not k.startswith('OAI_')}
            env.update(config.to_env())
            env.update(VERIFY_MARKER=str(root/'verified'),PATH=str(root)+os.pathsep+os.environ['PATH'])
            # Exercise the producer that start() actually invokes before its Popen boundary.
            producer=getattr(experiment,'launcher_environments',channel_environments)
            children=producer(env,qd_required=True)
            for kind,bundle in (('gnb',config.ul_bundle),('ue',config.dl_bundle)):
                result=subprocess.run(['bash',str(scripts/'run_local.sh'),kind],env=children[kind],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
                payload=json.loads(result.stdout.splitlines()[-1])
                self.assertEqual(payload['qd'],str(bundle))
                self.assertEqual((root/'verified').read_text(),'verified')
                (root/'verified').unlink()
            # Direct valid shell entry derives the same role without a generic user input.
            for kind,bundle in (('gnb',config.ul_bundle),('ue',config.dl_bundle)):
                result=subprocess.run(['bash',str(scripts/'run_local.sh'),kind],env=env,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout.splitlines()[-1])['qd'],str(bundle))
                (root/'verified').unlink()
            polluted=dict(env,OAI_QD_CHANNEL=str(config.ul_bundle))
            with self.assertRaises(ValueError):producer(polluted,qd_required=True)
            result=subprocess.run(['bash',str(scripts/'run_local.sh'),'gnb'],env=polluted,text=True,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('separate isolated DL/UL',result.stderr)
            self.assertFalse((root/'verified').exists())
            self.assertNotIn('"qd"',result.stdout)

    def test_integrated_requires_both_bundles(self):
        for env in ({}, {'OAI_QD_DL_CHANNEL':'/tmp/dl'}, {'OAI_QD_UL_CHANNEL':'/tmp/ul'}):
            with self.assertRaises(ValueError):channel_environments(env,qd_required=True)
        children=channel_environments({'OAI_QD_DL_CHANNEL':'/tmp/dl','OAI_QD_UL_CHANNEL':'/tmp/ul'},qd_required=True)
        self.assertEqual(children['gnb']['OAI_QD_CHANNEL'],'/tmp/ul')
        self.assertEqual(children['ue']['OAI_QD_CHANNEL'],'/tmp/dl')

    def test_legacy_runtime_clears_inherited_qd(self):
        import preflight as module
        from runtime_config import resolve_runtime
        with tempfile.TemporaryDirectory() as directory:
            config=resolve_runtime(Path(directory),'legacy-handover','fixture',{})
            with patch.object(module,'read_trace',return_value=[[0]+[0]*12+[6377900,0,0]+[0]*6,[1]+[0]*21]), \
                 patch.object(module,'check_template'),patch.object(Path,'is_file',return_value=True), \
                 patch('os.access',return_value=True),patch.object(Path,'read_text',return_value='position0 = { x = 6377900; y = 0; z = 0; };'), \
                 patch.object(Path,'read_bytes',return_value=b'fixture'),patch.object(module,'check_bundle') as bundle:
                result=module.preflight(0,{'OAI_QD_CHANNEL':'/foreign','OAI_QD_DL_CHANNEL':'/foreign'},runtime=config)
            self.assertEqual(result['mode'],'STK-only')
            self.assertEqual(result['source_repo'],str(config.oai_repo))
            self.assertEqual(result['trace'],str(config.trace))
            bundle.assert_not_called()

if __name__ == '__main__':
    unittest.main()
