"""Offline protection boundaries; no Docker/network/modem side effects."""
import importlib.util
import json
from pathlib import Path
import signal
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

if __name__=='__main__':unittest.main()

