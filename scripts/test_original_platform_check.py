"""Offline protection boundaries; no Docker/network/modem side effects."""
import importlib.util
import json
from pathlib import Path
import signal,sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('protection',Path(__file__).with_name('original_platform_check.py'))
protection=importlib.util.module_from_spec(spec)
spec.loader.exec_module(protection)

class FakeOps:
    def __init__(self,fail=None):
        self.calls=[];self.fail=fail;self.private_output='K=DO_NOT_PUBLISH'
    def step(self,name):
        self.calls.append(name)
        if self.fail==name:raise RuntimeError(self.private_output)
        if self.fail=='signal' and name=='business':raise KeyboardInterrupt()
    def preflight(self):self.step('preflight')
    def core_up(self):self.step('core_up')
    def network_up(self):self.step('network_up')
    def start(self):self.step('start')
    def business(self):
        self.step('business')
        return dict(ping=dict(sent=30,received=30),uplink=dict(lost=0,total=130),downlink=dict(lost=0,total=130))
    def cleanup(self):self.step('cleanup')

class ProtectionTests(unittest.TestCase):
    def test_existing_process_or_stale_marker_never_starts(self):
        op=FakeOps('preflight')
        result=protection.run_short(op)
        self.assertFalse(result['passed'])
        self.assertEqual(op.calls,['preflight','cleanup'])
        self.assertNotIn('DO_NOT_PUBLISH',json.dumps(result))
    def test_start_failure_and_signal_always_cleanup(self):
        for fail in ['core_up','network_up','start','signal']:
            op=FakeOps(fail);result=protection.run_short(op)
            self.assertFalse(result['passed']);self.assertEqual(op.calls[-1],'cleanup')
    def test_success_requires_real_business_counts(self):
        op=FakeOps();self.assertTrue(protection.run_short(op)['passed'])
        op.business=lambda:dict(ping=dict(sent=30,received=29),uplink=dict(lost=0,total=130),downlink=dict(lost=0,total=130))
        self.assertFalse(protection.run_short(op)['passed'])
    def test_cleanup_failure_cannot_pass(self):
        result=protection.run_short(FakeOps('cleanup'))
        self.assertFalse(result['passed']);self.assertEqual(result['cleanup_error'],'RuntimeError')
    def test_parse_only_numeric_receiver_summary(self):
        raw='K=DO_NOT_PUBLISH\n30 packets transmitted, 30 received, 0% packet loss\n'
        self.assertEqual(protection.parse_ping(raw),dict(sent=30,received=30))
        raw='OPc=DO_NOT_PUBLISH\n[ 5] 0.00-15.00 sec 184 KBytes 100 Kbits/sec 2.0 ms 0/130 (0%) receiver\n'
        self.assertEqual(protection.parse_udp(raw),dict(lost=0,total=130))
        with self.assertRaises(ValueError):protection.parse_udp(raw.replace('receiver','sender'))
    def test_git_errors_not_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as d:
            def runner(argv):
                raise subprocess.CalledProcessError(128,argv,output='fatal dubious ownership')
            with self.assertRaises(subprocess.CalledProcessError):
                protection.source_snapshot(Path(d),runner)
    def test_dirty_file_change_same_status_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);file=root/'source.c';file.write_text('before')
            def runner(argv):
                if argv[-1]=='HEAD':return 'a'*40+'\n'
                if argv[-1]=='--show-toplevel':return str(root)+'\n'
                if '--porcelain=v1' in argv:return ' M source.c\0'
                return 'source.c\0'
            a=protection.source_snapshot(root,runner)
            file.write_text('after')
            b=protection.source_snapshot(root,runner)
            self.assertNotEqual(a,b)
            diff=protection.compare_snapshots({'schema':1,'sources':{'x':a},'files':{},'containers':{},'network':{}},
                                              {'schema':1,'sources':{'x':b},'files':{},'containers':{},'network':{}})
            self.assertIn('sources',diff)
    def test_pid_reuse_or_changed_executable_never_signalled(self):
        record=dict(pid=456,start='77',executable='/original/modem')
        for identity in [('78','/original/modem'),('77','/foreign/program'),None]:
            with patch.object(protection,'process_identity',return_value=identity),patch.object(protection.os,'killpg') as kill:
                with self.assertRaises(ValueError):
                    protection.signal_record(record,signal.SIGTERM)
                kill.assert_not_called()
    def test_owner_changed_never_deleted(self):
        class Manager:
            def verify(self):return {'netns_inode':2,'host_ifindex':4}
            def down(self):raise AssertionError('must not delete')
        with self.assertRaises(ValueError):protection.release_network(Manager(),{'netns_inode':1,'host_ifindex':4})
    def test_foreign_or_replaced_container_never_stopped(self):
        original={'id':'a'*64,'name':'oai-amf','labels':{'com.docker.compose.project':'demo-oai'}}
        for changed in [dict(original,id='b'*64),dict(original,labels={})]:
            with self.assertRaises(ValueError):protection.require_container_identity(original,changed)
    def test_invalid_early_git_fields_are_reported_not_repaired(self):
        early={'files':{'x':{'sha256':'a'*64,'mtime_ns':2}},'sources':{'x':{'head':'fatal: dubious ownership','status':'fatal'}}}
        current={'files':early['files'],'sources':{'x':{'head':'b'*40,'status':''}}}
        report=protection.compare_early(early,current)
        self.assertTrue(report['protected_files_match'])
        self.assertFalse(report['early_source_state_verified'])
        self.assertEqual(early['sources']['x']['head'],'fatal: dubious ownership')
    def test_restore_only_containers_started_by_invocation(self):
        before={'a':False,'b':True,'foreign':False}
        current={'a':True,'b':True,'foreign':False}
        self.assertEqual(protection.started_container_ids(before,current,{'a','b'}),['a'])


class ConcreteBoundaryTests(unittest.TestCase):
    def make_ops(self,root):
        with patch.object(protection,'ROOT',root):
            return protection.OriginalShortRun('fresh',{},root/'.private/check')
    def test_failed_preflight_does_not_archive_existing_log(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ops=self.make_ops(root)
            log=root/'preexisting.log';log.write_text('private existing data')
            ops.log_paths=[log]
            with patch.object(ops,'collect'):
                ops.cleanup()
            self.assertEqual(log.read_text(),'private existing data')
            self.assertFalse((ops.output/log.name).exists())
    def test_foreign_state_record_not_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ops=self.make_ops(root);ops.state=root/'state.json'
            foreign=json.dumps({'ue':{'pid':7,'start':'99'}}).encode();ops.state.write_bytes(foreign)
            ops.old_state=b'original inactive';ops.records={'7':{'pid':7,'start':'98','executable':'/modem'}}
            with self.assertRaises(ValueError):ops.restore_state()
            self.assertEqual(ops.state.read_bytes(),foreign)
    def test_reused_pid_cannot_replace_owned_record(self):
        with tempfile.TemporaryDirectory() as d:
            ops=self.make_ops(Path(d));ops.records={'7':dict(pid=7,start='98',executable='/modem')}
            with self.assertRaises(ValueError):ops.remember(7,('99','/modem'))
    def test_replaced_container_cleanup_has_no_stop(self):
        with tempfile.TemporaryDirectory() as d:
            ops=self.make_ops(Path(d));before={'id':'a','name':'oai-amf','labels':{}}
            ops.started={'oai-amf':before}
            raw={'Id':'b','Name':'/oai-amf','State':{'Running':True},'Config':{'Labels':{}}}
            with patch.object(ops,'collect'),patch.object(protection,'command',return_value=json.dumps([raw])),patch.object(ops,'capture') as stop:
                with self.assertRaises(RuntimeError):ops.cleanup()
                stop.assert_not_called()
    def test_true_sigterm_runs_owned_cleanup(self):
        ops=FakeOps()
        def interrupt():os.kill(os.getpid(),signal.SIGTERM)
        import os
        ops.business=interrupt
        with protection.SignalGuard():
            result=protection.run_short(ops)
        self.assertFalse(result['passed']);self.assertEqual(ops.calls[-1],'cleanup')


    def test_capture_sigterm_stops_only_its_session(self):
        import os,threading
        unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        try:
            with tempfile.TemporaryDirectory() as d,patch.object(protection,'ROOT',Path(d)):
                ops=self.make_ops(Path(d))
                timer=threading.Timer(.3,lambda:os.kill(os.getpid(),signal.SIGTERM))
                timer.start()
                try:
                    with protection.SignalGuard(),self.assertRaises(KeyboardInterrupt):
                        ops.capture('owned-python',[sys.executable,'-c','import time;time.sleep(30)'],10)
                finally:timer.join()
                self.assertIsNone(unrelated.poll())
                owned=json.loads(next(ops.output.glob('capture-*-owned.json')).read_text())
                self.assertEqual(owned['processes'],{})
                for record in owned['stopped_processes'].values():
                    self.assertIsNone(protection.process_identity(record['pid']))
        finally:unrelated.terminate();unrelated.wait(timeout=5)


    def test_real_git_staged_only_changed_content_same_status(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def git(*argv):
                return subprocess.run(['git','-C',d,'-c','user.name=Offline test','-c','user.email=offline@example.invalid',*argv],
                    check=True,capture_output=True,text=True).stdout
            git('init');(root/'a.c').write_text('base');git('add','a.c');git('commit','-m','fixture')
            (root/'a.c').write_text('staged-one');git('add','a.c')
            one=protection.source_snapshot(root)
            (root/'a.c').write_text('staged-two');git('add','a.c')
            two=protection.source_snapshot(root)
            self.assertEqual(one['status'],two['status'])
            self.assertNotEqual(one['dirty_files'],two['dirty_files'])
            self.assertNotEqual(one['index_sha256'],two['index_sha256'])


    def test_dead_owned_launcher_state_still_restored(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ops=self.make_ops(root);ops.state=root/'state.json'
            ops.log_paths=[root/'gnb-fresh.log',root/'ue-fresh.log'];ops.old_state=b'old inactive bytes'
            value={'gnb':{'pid':777,'start':'99','log':str(ops.log_paths[0]),'rate':1}}
            raw=json.dumps(value).encode();ops.state.write_bytes(raw)
            with patch.object(protection,'process_identity',return_value=None):
                ops.claim_state(raw,value)
            self.assertTrue(ops.state_owned)
            ops.restore_state();self.assertEqual(ops.state.read_bytes(),ops.old_state)
    def test_state_changes_after_claim_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ops=self.make_ops(root);ops.state=root/'state.json'
            ops.log_paths=[root/'gnb-fresh.log'];ops.old_state=b'old'
            value={'gnb':{'pid':777,'start':'99','log':str(ops.log_paths[0]),'rate':1}}
            raw=json.dumps(value).encode();ops.state.write_bytes(raw)
            with patch.object(protection,'process_identity',return_value=None):ops.claim_state(raw,value)
            foreign=b'foreign state';ops.state.write_bytes(foreign)
            with self.assertRaises(ValueError):ops.restore_state()
            self.assertEqual(ops.state.read_bytes(),foreign)


    def test_incomplete_snapshot_or_wrong_revision_refused(self):
        files={str(p):{'type':'file','sha256':'a'*64,'mtime_ns':1} for p in protection.PROTECTED}
        sources={str(protection.ORIGINAL):{'head':'f30bc90a626214d227a7991d7429cf7723233f96'},
          str(protection.OAI):{'head':'c4125d1c740181ab1f7da0e7dd1d04ed07c37670'},
          str(protection.CORE):{'head':'212f92fc6a2fb82b5df1e8f4ef20075e75acefb3'}}
        valid={'schema':1,'files':files,'sources':sources}
        self.assertEqual(protection.validate_snapshot(valid),valid)
        valid['sources'][str(protection.OAI)]['head']='b'*40
        with self.assertRaises(ValueError):protection.validate_snapshot(valid)
        valid['files'].pop(str(protection.PROTECTED[0]))
        with self.assertRaises(ValueError):protection.validate_snapshot(valid)


    def test_failed_start_then_external_running_container_is_not_stopped(self):
        with tempfile.TemporaryDirectory() as d:
            ops=self.make_ops(Path(d))
            raw={'Id':'a','Name':'/oai-amf','State':{'Running':False},'Config':{'Labels':{}}}
            original=protection.container_info(raw)
            ops.before={'containers':{'oai-amf':original}}
            calls=[]
            def fail_start(name,argv,timeout=120):
                calls.append(argv)
                raw['State']['Running']=True
                raise RuntimeError('start command failed; other actor started this container')
            with patch.object(protection,'CORE_ORDER',('oai-amf',)),patch.object(protection,'command',side_effect=lambda _:json.dumps([raw])),patch.object(ops,'capture',side_effect=fail_start),patch.object(ops,'collect'):
                with self.assertRaises(RuntimeError):ops.core_up()
                try:ops.cleanup()
                except RuntimeError:pass
            self.assertFalse(any(argv[:2]==['docker','stop'] for argv in calls))


    def test_confirmed_start_and_external_restart_cleanup_boundary(self):
        for scenario in ('owned','outside-operation','restarted'):
            with self.subTest(scenario=scenario),tempfile.TemporaryDirectory() as d:
                ops=self.make_ops(Path(d))
                raw={'Id':'a','Name':'/oai-amf','State':{'Running':False,'StartedAt':'old'},'Config':{'Labels':{}}}
                ops.before={'containers':{'oai-amf':protection.container_info(raw)}};calls=[]
                def capture(name,argv,timeout=120):
                    calls.append(argv)
                    if argv[:2]==['docker','start']:
                        raw['State'].update(Running=True,StartedAt='1970-01-01T00:00:01.500000000Z' if scenario!='outside-operation' else '1970-01-01T00:00:00.500000000Z')
                    else:raw['State']['Running']=False
                    return 'a\n'
                with patch.object(protection,'CORE_ORDER',('oai-amf',)),patch.object(protection.time,'time_ns',side_effect=[1000000000,2000000000]),patch.object(protection,'command',side_effect=lambda _:json.dumps([raw])),patch.object(ops,'capture',side_effect=capture),patch.object(ops,'collect'):
                    if scenario=='outside-operation':
                        with self.assertRaises(ValueError):ops.core_up()
                    else:ops.core_up()
                    if scenario=='restarted':raw['State']['StartedAt']='1970-01-01T00:00:02.500000000Z'
                    if scenario=='restarted':
                        with self.assertRaises(RuntimeError):ops.cleanup()
                    else:ops.cleanup()
                self.assertEqual(sum(argv[:2]==['docker','stop'] for argv in calls),1 if scenario=='owned' else 0)


    def test_unknown_first_executable_retains_network_and_state(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ops=self.make_ops(root);ops.state=root/'state.json'
            ops.log_paths=[root/'gnb-fresh.log'];ops.logs_claimed=True;ops.old_state=b'original'
            raw=json.dumps({'gnb':dict(pid=777,start='99',log=str(ops.log_paths[0]),rate=1)}).encode()
            ops.state.write_bytes(raw);ops.owner={'owned':True}
            with patch.object(protection,'process_identity',return_value=('99','/foreign/unknown')),patch.object(ops,'has_token',return_value=True),patch.object(protection.os,'getpgid',return_value=777),patch.object(protection.os,'getsid',return_value=777),patch.object(Path,'iterdir',return_value=iter([])),patch.object(protection,'release_network') as release:
                with self.assertRaises(RuntimeError):ops.cleanup()
                release.assert_not_called()
            self.assertEqual(ops.state.read_bytes(),raw)
    def test_missing_state_approved_shell_and_foreign_token_shell(self):
        for argv,approved in [(['bash',str(protection.ORIGINAL/'local_ntn/run_local.sh'),'gnb'],True),
                               (['bash','/foreign/run.sh','gnb'],False)]:
            with self.subTest(argv=argv),tempfile.TemporaryDirectory() as d:
                root=Path(d);ops=self.make_ops(root);ops.state=root/'missing'
                with patch.object(Path,'iterdir',return_value=iter([Path('/proc/777')])),patch.object(protection,'process_identity',return_value=('99','/usr/bin/bash')),patch.object(ops,'has_token',return_value=True),patch.object(protection.os,'getpgid',return_value=777),patch.object(protection.os,'getsid',return_value=777),patch.object(protection,'process_argv',return_value=argv,create=True):
                    if approved:
                        ops.collect()
                        record=ops.records['777']
                        self.assertEqual(record['phase'],'launching')
                        self.assertEqual(record['expected_executable'],str(protection.BUILD/'nr-softmodem'))
                    else:
                        with self.assertRaises(ValueError):ops.collect()
                        self.assertEqual(ops.records,{})
    def test_launch_shell_transition_race_and_reuse_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            ops=self.make_ops(Path(d))
            record={'pid':777,'start':'99','executable':'/usr/bin/bash','phase':'launching',
                    'expected_executable':str(protection.BUILD/'nr-softmodem')}
            ops.records={'777':record.copy()}
            import run_state
            with patch.object(run_state,'process_identity',return_value=('99',record['expected_executable'])):
                self.assertTrue(run_state.matches(record))
            ops.remember(777,('99',record['expected_executable']))
            self.assertNotIn('phase',ops.records['777'])
            with self.assertRaises(ValueError):ops.remember(777,('99','/unknown'))
            with self.assertRaises(ValueError):ops.remember(777,('100',record['expected_executable']))

if __name__=='__main__':unittest.main()
