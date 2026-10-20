import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'local_ntn'))
from runtime_config import resolve_runtime
from init_lab import main as init
from core_lab import CoreLab

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        shutil.copytree(Path(__file__).resolve().parents[1]/'configs',self.root/'configs')
        self.c=resolve_runtime(self.root,'integrated-handover','run1',{})
    def render(self):
        with patch('init_lab.ROOT',self.root),patch('init_lab.secrets.token_hex',side_effect=['test-password-distinct','test-key-distinct','test-opc-distinct']),contextlib.redirect_stdout(io.StringIO()) as out:
            init(['--profile','integrated-handover'])
        return out.getvalue()
    def test_render_and_refuse_overwrite(self):
        originals={p:p.read_bytes() for p in (self.root/'configs/core').iterdir() if p.is_file()}
        out=self.render()
        compose=(self.c.private_dir/'core/compose.yaml').read_text()
        config=(self.c.private_dir/'core/conf/config.yaml').read_text()
        self.assertIn('ntn-qd-integrated-oai-ext-dn',compose)
        self.assertIn('192.168.71.128/26',compose)
        self.assertIn('ip route add 12.2.1.0/24 via 192.168.71.134',compose)
        self.assertIn('grep 12.2.1.0/24',compose)
        self.assertIn('ipv4_subnet: "12.2.1.0/24"',config)
        for dnn in ['openairinterface','ims','default']:
            self.assertNotIn('dnn: "'+dnn+'"',config)
        self.assertNotIn('10.0.',config)
        credentials=(self.c.private_dir/'ue.conf').read_text()
        for secret in ('test-password-distinct','test-key-distinct','test-opc-distinct'):
            self.assertNotIn(secret,out)
        self.assertTrue(all(p.read_bytes()==v for p,v in originals.items()))
        before=(self.c.private_dir/'ue.conf').read_bytes()
        with self.assertRaises(SystemExit):self.render()
        self.assertEqual(before,(self.c.private_dir/'ue.conf').read_bytes())
    def test_builtin_network_null_ipam_does_not_block_core_preflight(self):
        self.render();lab=CoreLab(self.c)
        builtin=[{'Id':'host','Name':'host','IPAM':{'Config':None},'Options':None},
                 {'Id':'none','Name':'none','IPAM':{'Config':None},'Options':{}}]
        with patch.object(lab,'inventory',return_value=([],builtin)):
            self.assertEqual(lab.preflight(),([],builtin))
        for ipam,options in (({},{}),('bad',{}),([],'bad')):
            with patch.object(lab,'inventory',return_value=([],[dict(builtin[0],IPAM={'Config':ipam},Options=options)])):
                with self.assertRaises(ValueError):lab.preflight()
        conflict={'Id':'foreign','Name':'foreign','IPAM':{'Config':[{'Subnet':'192.168.71.128/26'}]},'Options':{}}
        with patch.object(lab,'inventory',return_value=([],builtin+[conflict])):
            with self.assertRaises(ValueError):lab.preflight()

    def test_batched_inventory_complete_and_exact(self):
        ids=[format(i,'064x') for i in range(1,20)]
        nets=[format(i,'064x') for i in range(100,103)]
        calls=[]
        def runner(cmd):
            calls.append(cmd)
            if cmd==['docker','ps','-aq','--no-trunc']:return '\n'.join(ids)
            if cmd==['docker','network','ls','-q','--no-trunc']:return '\n'.join(nets)
            if cmd==['docker','inspect',*ids]:return json.dumps([{'Id':i} for i in reversed(ids)])
            if cmd==['docker','network','inspect',*nets]:return json.dumps([{'Id':i} for i in nets])
            raise AssertionError(cmd)
        lab=CoreLab(self.c,runner)
        containers,networks=lab.inventory()
        self.assertEqual({i['Id'] for i in containers},set(ids))
        self.assertEqual({i['Id'] for i in networks},set(nets))
        self.assertEqual(len(calls),4)
        empty_calls=[]
        self.assertEqual(CoreLab(self.c,lambda cmd:empty_calls.append(cmd) or '').inventory(),([],[]))
        self.assertEqual(len(empty_calls),2)
        for bad in [[],[{'Id':ids[0]}]*19,[{'Id':i} for i in ids[:-1]]+[{'Id':'foreign'}],{},[{'Id':None}],None]:
            def broken(cmd):
                if cmd[:2]==['docker','ps']:return '\n'.join(ids)
                return json.dumps(bad)
            with self.assertRaises(ValueError):CoreLab(self.c,broken).inventory()
        def failed(cmd):
            if cmd[:2]==['docker','ps']:return '\n'.join(ids)
            raise RuntimeError('partial inspect failed')
        with self.assertRaises(RuntimeError):CoreLab(self.c,failed).inventory()
        def invalid_json(cmd):
            if cmd[:2]==['docker','ps']:return '\n'.join(ids)
            return '{'
        with self.assertRaises(ValueError):CoreLab(self.c,invalid_json).inventory()

    def test_default_zky_rendering_keeps_existing_pool_and_names(self):
        with patch('init_lab.ROOT',self.root),contextlib.redirect_stdout(io.StringIO()):
            init([])
        private=self.root/'.private'
        compose=(private/'core/compose.yaml').read_text()
        config=(private/'core/conf/config.yaml').read_text()
        self.assertIn('ntn-local-oai-ext-dn',compose)
        self.assertIn('192.168.70.128/26',compose)
        self.assertIn('ip route add 10.0.0.0/16 via 192.168.70.134',compose)
        self.assertIn('grep 10.0.0',compose)
        self.assertIn('ipv4_subnet: "10.0.0.0/24"',config)
        self.assertIn('dnn: "ims"',config)
        self.assertNotIn('ntn.workspace',compose)
    def test_consumer_commands_and_conflicts(self):
        self.render();calls=[]
        def runner(cmd):
            calls.append(cmd)
            if cmd[:3]==['docker','ps','-aq']:return 'foreign\n'
            if cmd[:3]==['docker','inspect','foreign']:return json.dumps([{'Id':'foreign','Name':'/ntn-qd-integrated-oai-amf','Config':{'Labels':{'com.docker.compose.project':'other'}}}])
            if cmd[:3]==['docker','network','ls']:return ''
            return ''
        lab=CoreLab(self.c,runner=runner)
        with self.assertRaises(ValueError):lab.preflight()
        self.assertFalse(any('up' in cmd or 'down' in cmd for cmd in calls))
    def test_owner_workspace_hash_and_serial_run(self):
        self.render();calls=[]
        lab=CoreLab(self.c,runner=lambda cmd:calls.append(cmd) or '')
        marker=lab.identity()
        lab.validate(marker)
        CoreLab(replace(self.c,run_id='run2')).validate(marker)
        for field,value in [('workspace','/foreign'),('project','oai'),('config_hash','bad')]:
            with self.assertRaises(ValueError):lab.validate(dict(marker,**{field:value}))
        with patch.object(lab,'preflight',return_value=([],[])),patch.object(lab,'inventory',return_value=([],[])),patch.object(lab,'wait_ready') as ready:
            lab.up()
            ready.assert_called_once_with()
        self.assertIn(['docker','compose','--project-name',self.c.core_project,'--file',str(self.c.private_dir/'core/compose.yaml'),'up','-d'],calls)
        (self.c.private_dir/'core/conf/config.yaml').write_text('changed')
        with self.assertRaises(ValueError):lab.down()
        self.assertFalse(any('down' in cmd for cmd in calls))

    def test_ready_waits_for_every_owned_service(self):
        lab=CoreLab(self.c)
        pending=[{'Name':'/amf','State':{'Running':True,'Health':{'Status':'starting'}}},
                 {'Name':'/db','State':{'Running':True,'Health':{'Status':'healthy'}}}]
        ready=[dict(item,State={'Running':True,'Health':{'Status':'healthy'}}) for item in pending]
        with patch.object(lab,'names',return_value={'amf','db'}), patch.object(lab,'own_container',return_value=True), \
             patch.object(lab,'preflight',side_effect=[(pending,[]),(ready,[])]), patch('core_lab.time.sleep') as sleep:
            lab.wait_ready()
            sleep.assert_called_once()

    def test_readiness_rejects_missing_stopped_unhealthy_and_foreign(self):
        lab=CoreLab(self.c)
        for state,owned in [({},True),({'Running':False},True),
                            ({'Running':True,'Health':{'Status':'unhealthy'}},True),
                            ({'Running':True,'Health':{'Status':'healthy'}},False)]:
            with patch.object(lab,'names',return_value={'amf'}), patch.object(lab,'own_container',return_value=owned), \
                 patch.object(lab,'preflight',return_value=([{'Name':'/amf','State':state}],[])):
                with self.assertRaises(TimeoutError):lab.wait_ready(0)
        with patch.object(lab,'names',return_value={'amf','db'}), patch.object(lab,'own_container',return_value=True), \
             patch.object(lab,'preflight',return_value=([{'Name':'/amf','State':{'Running':True}}],[])):
            with self.assertRaises(TimeoutError):lab.wait_ready(0)
        for timeout in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):lab.wait_ready(timeout)

    def test_overlapping_foreign_network_refused(self):
        self.render()
        network={'Id':'foreign-net','Name':'other-net','Labels':{},'IPAM':{'Config':[{'Subnet':'192.168.71.0/24'}]}}
        lab=CoreLab(self.c)
        with patch.object(lab,'inventory',return_value=([],[network])):
            with self.assertRaises(ValueError):lab.preflight()
    def test_failed_start_removes_only_new_owned_ids(self):
        self.render();calls=[];lab=CoreLab(self.c)
        labels={'com.docker.compose.project':self.c.core_project,'com.docker.compose.project.working_dir':str(lab.core),'com.docker.compose.project.config_files':str(lab.compose)}
        old={'Id':'old','Name':'/ntn-qd-integrated-oai-amf','Config':{'Labels':labels}}
        new={'Id':'new','Name':'/ntn-qd-integrated-oai-smf','Config':{'Labels':labels}}
        alien={'Id':'alien','Name':'/other','Config':{'Labels':{}}}
        def run(cmd):
            calls.append(cmd)
            if 'up' in cmd:raise RuntimeError('injected startup failure')
            return ''
        lab.run=run
        with patch.object(lab,'preflight',return_value=([old],[])),patch.object(lab,'inventory',return_value=([old,new,alien],[])):
            with self.assertRaises(RuntimeError):lab.up()
        self.assertIn(['docker','rm','-f','new'],calls)
        self.assertNotIn(['docker','rm','-f','old'],calls)
        self.assertNotIn(['docker','rm','-f','alien'],calls)
        self.assertFalse(any('down' in cmd for cmd in calls))

if __name__=='__main__':unittest.main()
