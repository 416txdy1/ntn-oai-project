"""Real git/archive provenance boundaries, including WSL root launch."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local_ntn'))
import experiment as e


class ProvenanceTests(unittest.TestCase):
    def test_archive_does_not_borrow_parent_git_head(self):
        if not (ROOT/'.runtime/oai/.archive-sha256').is_file():
            self.skipTest('archive fixture only exists in independent Linux clone')
        source=e.source_identity(ROOT,ROOT/'.runtime/oai')
        self.assertEqual(source['kind'],'verified_archive')
        self.assertEqual(source['commit'],'1e0c78bfbb80424f275e73a3103f582e0f903413')
        self.assertTrue(source['overlay_sha256'])
        self.assertEqual(source['archive_sha256'],json.loads((ROOT/'vendor/checksums.json').read_text())['oai-source.tar.gz'])

    def test_parent_repository_is_not_source_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);subprocess.run(['git','init','-q',str(root)],check=True)
            child=root/'source';child.mkdir()
            with self.assertRaises(ValueError):e.commit_at(child)

    def test_root_git_uses_command_scoped_safe_directory(self):
        def fake(command,**kwargs):
            self.assertIn('-c',command)
            self.assertIn('safe.directory='+str(ROOT.resolve()),command)
            self.assertTrue(kwargs.get('check'))
            value=str(ROOT.resolve()) if '--show-toplevel' in command else 'a'*40
            return subprocess.CompletedProcess(command,0,value+'\n','')
        with patch.object(e.subprocess,'run',side_effect=fake):
            self.assertEqual(e.commit_at(ROOT),'a'*40)

    def test_git_failure_and_non_hex_not_accepted(self):
        with patch.object(e.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'bad\n','')):
            with self.assertRaises(ValueError):e.commit_at(ROOT)

    def test_real_root_commit_at(self):
        if sys.platform!='linux':self.skipTest('WSL real identity')
        value=e.commit_at(ROOT)
        self.assertRegex(value,r'^[0-9a-f]{40}$')


    def archive_fixture(self,root):
        import hashlib
        vendor=root/'vendor';vendor.mkdir()
        archive=vendor/'oai-source.tar.gz';archive.write_bytes(b'verified archive fixture')
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        (vendor/'checksums.json').write_text(json.dumps({'oai-source.tar.gz':digest}))
        (vendor/'source-manifest.json').write_text(json.dumps({'oai':{'commit':'1e0c78bfbb80424f275e73a3103f582e0f903413'},'oai-source.tar.gz':{'sha256':digest}}))
        repo=root/'.runtime/oai';repo.mkdir(parents=True)
        (repo/'.archive-sha256').write_text(digest)
        overlay=root/'oai_patch/current/radio/rfsimulator';overlay.mkdir(parents=True)
        (overlay/'fixture.c').write_text('actual deployed overlay\n')
        deployed=repo/'radio/rfsimulator';deployed.mkdir(parents=True)
        (deployed/'fixture.c').write_text('actual deployed overlay\n')
        quadriga=root/'quadriga/oai';quadriga.mkdir(parents=True)
        for name in ('qd_channel_reader.c','qd_channel_reader.h','qd_channel_adapter.c'):
            (quadriga/name).write_text('QD '+name)
            (deployed/name).write_text('QD '+name)
        return repo

    def test_archive_stamp_and_overlay_tampering_rejected(self):
        for changed in ('archive','stamp','overlay'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);repo=self.archive_fixture(root)
                self.assertEqual(e.source_identity(root,repo)['kind'],'verified_archive')
                target={'archive':root/'vendor/oai-source.tar.gz','stamp':repo/'.archive-sha256',
                        'overlay':repo/'radio/rfsimulator/fixture.c'}[changed]
                target.write_text('tampered')
                with self.assertRaises(ValueError):e.source_identity(root,repo)

    def test_genuine_external_git_source_uses_own_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'source.c').write_text('external source fixture')
            subprocess.run(['git','-C',str(root),'add','source.c'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.email=test@example.invalid','-c','user.name=fixture','commit','-qm','fixture'],check=True)
            identity=e.source_identity(ROOT,root)
            self.assertEqual(identity['kind'],'git')
            self.assertEqual(identity['commit'],e.commit_at(root))

if __name__=='__main__':unittest.main()
