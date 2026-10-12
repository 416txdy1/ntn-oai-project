import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from runtime_config import resolve_runtime
from network_owner import create_owner, validate_owner, read_marker, NetworkManager

class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.c = replace(resolve_runtime(self.root, 'integrated-handover', 'run1', {}), owner_file=self.root/'owner.json')
        self.t = {'host': {'ifname':self.c.host_veth,'ifindex':11,'link_index':12,'linkinfo':{'info_kind':'veth'}}, 'peer':{'ifname':self.c.ue_veth,'ifindex':12,'link_index':11,'linkinfo':{'info_kind':'veth'}}, 'netns_inode':99,'host_addresses':[{'local':self.c.rf_host_ip,'prefixlen':30}], 'peer_addresses':[{'local':self.c.rf_ue_ip,'prefixlen':30}], 'interfaces':['lo',self.c.ue_veth]}
    def test_identity(self):
        marker=create_owner(self.c,self.t)
        validate_owner(self.c,self.t,marker)
        for field,value in [('run_id','another'),('host_ifindex',3),('netns_inode',100),('profile','zky')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_owner(self.c,self.t,dict(marker,**{field:value}))
        for change in [{'host':dict(self.t['host'],ifname='oai-stk-host')},{'interfaces':['lo','alien']},{'host_addresses':[{'local':'10.201.0.1','prefixlen':30}]}]:
            with self.assertRaises(ValueError): create_owner(self.c,dict(self.t,**change))
    def test_marker_security(self):
        self.c.owner_file.write_text(json.dumps(create_owner(self.c,self.t)))
        with patch('network_owner.os.lstat',return_value=type('S',(),{'st_uid':1000,'st_mode':0o100600})()):
            with self.assertRaises(ValueError):read_marker(self.c.owner_file)
        self.c.owner_file.unlink()
        self.c.owner_file.symlink_to(self.root/'missing')
        with self.assertRaises(ValueError):read_marker(self.c.owner_file)
    def test_down_refuses_other_run_without_commands(self):
        self.c.owner_file.write_text(json.dumps(create_owner(replace(self.c,run_id='other'),self.t)))
        commands=[]
        manager=NetworkManager(self.c,runner=lambda cmd: commands.append(cmd))
        with patch.object(manager,'topology',return_value=self.t), patch('network_owner.read_marker',return_value=create_owner(replace(self.c,run_id='other'),self.t)):
            with self.assertRaises(ValueError):manager.down()
        self.assertFalse(any('delete' in cmd or 'add' in cmd for cmd in commands))
    def test_partial_failure_rolls_back_only_created_identity(self):
        commands=[]
        def run(cmd):
            commands.append(cmd)
            if cmd[:4]==['ip','link','set',self.c.ue_veth]:raise RuntimeError('injected failure')
            return '[]'
        manager=NetworkManager(self.c,runner=run)
        with patch.object(manager,'preflight'),patch.object(manager,'inode',return_value=99),patch.object(manager,'link',return_value=self.t['host']):
            with self.assertRaises(RuntimeError):manager.up()
        self.assertIn(['ip','link','delete',self.c.host_veth],commands)
        self.assertIn(['ip','netns','delete',self.c.namespace],commands)
        self.assertFalse(self.c.owner_file.exists())
        commands.clear()
        with patch.object(manager,'preflight',side_effect=ValueError('preexisting')):
            with self.assertRaises(ValueError):manager.up()
        self.assertFalse(any('delete' in cmd or 'add' in cmd for cmd in commands))

    def test_rollback_does_not_delete_replacements(self):
        commands=[]
        def run(cmd):
            commands.append(cmd)
            if cmd[:4]==['ip','link','set',self.c.ue_veth]:raise RuntimeError('injected')
            return '[]'
        manager=NetworkManager(self.c,runner=run)
        with patch.object(manager,'preflight'),patch.object(manager,'inode',side_effect=[99,100]),patch.object(manager,'link',side_effect=[self.t['host'],dict(self.t['host'],ifindex=77)]):
            with self.assertRaises(RuntimeError):manager.up()
        self.assertFalse(any('delete' in cmd for cmd in commands))
    def test_preflight_conflict_command_boundary(self):
        commands=[]
        def run(cmd):
            commands.append(cmd)
            if cmd==['ip','-j','netns','list']:return '[]'
            if cmd==['ip','-j','link','show']:return json.dumps([{'ifname':self.c.host_veth}])
            raise AssertionError(cmd)
        with self.assertRaises(ValueError):NetworkManager(self.c,runner=run).up()
        self.assertFalse(any('add' in cmd or 'delete' in cmd for cmd in commands))
    def test_legacy_marker_format_unchanged(self):
        c=replace(self.c,profile='zky')
        marker=create_owner(c,self.t)
        self.assertEqual(marker,{'schema':1,'host_ifindex':11,'peer_ifindex':12,'netns_inode':99})
        validate_owner(c,self.t,marker)

if __name__=='__main__': unittest.main()
