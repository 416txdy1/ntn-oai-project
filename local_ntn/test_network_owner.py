import json
import os
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

    def test_resolver_to_manager_rejects_marker_symlink_before_down(self):
        link=self.root/'selected-owner.json';target=self.root/'target-owner.json'
        env={'OAI_NTN_OWNER_FILE':str(link)}
        c=resolve_runtime(self.root,'zky','default',env)
        t=dict(self.t,host=dict(self.t['host'],ifname=c.host_veth),peer=dict(self.t['peer'],ifname=c.ue_veth),host_addresses=[{'local':c.rf_host_ip,'prefixlen':30}],peer_addresses=[{'local':c.rf_ue_ip,'prefixlen':30}],interfaces=['lo',c.ue_veth])
        target.write_text(json.dumps(create_owner(c,t)))
        original=target.read_bytes();link.symlink_to(target)
        # Simulate root-owned test files without sudo or writing anything in /run.
        real_lstat=os.lstat;real_fstat=os.fstat
        def root_stat(info):
            fields=list(info);fields[4]=0;return os.stat_result(fields)
        commands=[]
        with patch('network_owner.os.lstat',side_effect=lambda *a,**kw:root_stat(real_lstat(*a,**kw))),patch('network_owner.os.fstat',side_effect=lambda fd:root_stat(real_fstat(fd))):
            c=resolve_runtime(self.root,'zky','default',env)
            manager=NetworkManager(c,runner=lambda cmd:commands.append(cmd))
            with patch.object(manager,'topology',return_value=t):
                for action in ('verify','down'):
                    with self.subTest(action=action), self.assertRaises(ValueError):
                        getattr(manager,action)()
        self.assertEqual(commands,[])
        self.assertTrue(link.is_symlink())
        self.assertEqual(target.read_bytes(),original)
        # The same resolved consumer still accepts a nonsymlink legacy marker.
        link.unlink();link.write_bytes(original)
        with patch('network_owner.os.lstat',side_effect=lambda *a,**kw:root_stat(real_lstat(*a,**kw))),patch('network_owner.os.fstat',side_effect=lambda fd:root_stat(real_fstat(fd))):
            c=resolve_runtime(self.root,'zky','default',env)
            manager=NetworkManager(c,runner=lambda cmd:commands.append(cmd))
            with patch.object(manager,'topology',return_value=t):
                self.assertEqual(manager.verify(),create_owner(c,t))
    def test_default_zky_owner_path_never_follows_marker_symlink(self):
        original_resolve=Path.resolve
        default=Path('/run/oai-stk-ue.owner.json')
        target=self.root/'default-target.json'
        def fake_resolve(path,*args,**kwargs):
            if path==default:return target
            return original_resolve(path,*args,**kwargs)
        with patch.object(Path,'resolve',fake_resolve):
            c=resolve_runtime(self.root,'zky','default',{})
        self.assertEqual(c.owner_file,default)

    def test_isolated_owner_still_rejects_resolved_fixed_path_redirection(self):
        original_resolve=Path.resolve
        default=Path('/run/ntn-qd-ue.owner.json')
        target=self.root/'isolated-target.json'
        def fake_resolve(path,*args,**kwargs):
            if path==default:return target
            return original_resolve(path,*args,**kwargs)
        with patch.object(Path,'resolve',fake_resolve):
            for profile in ('integrated-handover','legacy-handover'):
                with self.subTest(profile=profile),self.assertRaises(ValueError):
                    resolve_runtime(self.root,profile,'run',{})


    def test_retained_marker_inode_rejects_identical_replacement_both_profiles(self):
        real_lstat=os.lstat;real_fstat=os.fstat
        def rooted(info):
            fields=list(info);fields[4]=0;return os.stat_result(fields)
        for profile in ('zky','integrated-handover'):
            c=replace(self.c,profile=profile)
            c.owner_file.write_text(json.dumps(create_owner(c,self.t)))
            commands=[];manager=NetworkManager(c,runner=lambda cmd:commands.append(cmd))
            with patch('network_owner.os.lstat',side_effect=lambda *a,**kw:rooted(real_lstat(*a,**kw))),patch('network_owner.os.fstat',side_effect=lambda fd:rooted(real_fstat(fd))),patch.object(manager,'topology',return_value=self.t),patch.object(manager,'inode',return_value=99):
                manager.verify()
                replacement=self.root/'replacement.json';replacement.write_bytes(c.owner_file.read_bytes())
                os.replace(replacement,c.owner_file)
                saved=c.owner_file.read_bytes()
                with self.assertRaises(ValueError):manager.down()
                self.assertEqual(commands,[])
                self.assertEqual(c.owner_file.read_bytes(),saved)
            c.owner_file.unlink()
    def test_created_original_marker_success_and_symlink_replace(self):
        real_lstat=os.lstat;real_fstat=os.fstat
        def rooted(info):
            fields=list(info);fields[4]=0;return os.stat_result(fields)
        for replacement in (False,True):
            c=replace(self.c,profile='zky');commands=[]
            manager=NetworkManager(c,runner=lambda cmd:commands.append(cmd))
            with patch('network_owner.os.lstat',side_effect=lambda *a,**kw:rooted(real_lstat(*a,**kw))),patch('network_owner.os.fstat',side_effect=lambda fd:rooted(real_fstat(fd))),patch.object(manager,'topology',return_value=self.t),patch.object(manager,'inode',return_value=99):
                manager.verify(claim=True)
                if replacement:
                    target=self.root/'target.json';target.write_bytes(c.owner_file.read_bytes())
                    c.owner_file.unlink();c.owner_file.symlink_to(target)
                    with self.assertRaises(ValueError):manager.down()
                    self.assertTrue(c.owner_file.is_symlink());self.assertTrue(target.exists())
                else:
                    manager.down();self.assertFalse(c.owner_file.exists())
                    self.assertIn(['ip','link','delete',c.host_veth],commands)
                    self.assertIn(['ip','netns','delete',c.namespace],commands)
            if c.owner_file.is_symlink():c.owner_file.unlink()


    def test_partial_claim_rollback_only_created_marker_inode(self):
        real_lstat=os.lstat;real_fstat=os.fstat
        def rooted(info):
            fields=list(info);fields[4]=0;return os.stat_result(fields)
        for replaced in (False,True):
            c=self.c;commands=[]
            manager=NetworkManager(c,runner=lambda cmd:commands.append(cmd) or '[]')
            verify=manager.verify
            def fail_after_claim(claim=False):
                verify(claim)
                if replaced:
                    replacement=self.root/'new-marker';replacement.write_bytes(c.owner_file.read_bytes())
                    os.replace(replacement,c.owner_file)
                raise RuntimeError('failure after marker creation')
            with patch('network_owner.os.lstat',side_effect=lambda *a,**kw:rooted(real_lstat(*a,**kw))),patch('network_owner.os.fstat',side_effect=lambda fd:rooted(real_fstat(fd))),patch.object(manager,'preflight'),patch.object(manager,'inode',return_value=99),patch.object(manager,'link',return_value=self.t['host']),patch.object(manager,'topology',return_value=self.t),patch.object(manager,'verify',side_effect=fail_after_claim):
                with self.assertRaises(RuntimeError):manager.up()
            self.assertEqual(c.owner_file.exists(),replaced)
            if replaced:c.owner_file.unlink()
    def test_path_replacement_between_lstat_and_open_is_refused(self):
        real_lstat=os.lstat;real_fstat=os.fstat;real_open=os.open
        def rooted(info):
            fields=list(info);fields[4]=0;return os.stat_result(fields)
        self.c.owner_file.write_text(json.dumps(create_owner(self.c,self.t)))
        replacement=self.root/'new-marker';replacement.write_bytes(self.c.owner_file.read_bytes())
        def replaced_open(path,*args,**kwargs):
            fd=real_open(path,*args,**kwargs)
            if Path(path)==self.c.owner_file:os.replace(replacement,self.c.owner_file)
            return fd
        commands=[];manager=NetworkManager(self.c,runner=lambda cmd:commands.append(cmd))
        with patch('network_owner.os.lstat',side_effect=lambda *a,**kw:rooted(real_lstat(*a,**kw))),patch('network_owner.os.fstat',side_effect=lambda fd:rooted(real_fstat(fd))),patch('network_owner.os.open',side_effect=replaced_open),patch.object(manager,'topology',return_value=self.t):
            with self.assertRaises(ValueError):manager.verify()
        self.assertEqual(commands,[]);self.assertTrue(self.c.owner_file.exists())

if __name__=='__main__': unittest.main()
