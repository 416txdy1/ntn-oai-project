"""Bounded, explicitly recorded NTN diagnostic setting; no live resources."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'local_ntn'))
from runtime_config import pusch_failure_threshold, resolve_runtime

class DtxSetting(unittest.TestCase):
 def test_old_profile_ignores_override(self):
  for value in ['100','0','1001','$(unsafe)',None]:
   self.assertIsNone(pusch_failure_threshold('zky',{} if value is None else {'OAI_NTN_PUSCH_FAILURE_THRES':value}))
 def test_unset_preserves_oai_default(self):
  for profile in ['integrated-handover','legacy-handover']:
   for env in [{},{'OAI_NTN_PUSCH_FAILURE_THRES':''}]:self.assertIsNone(pusch_failure_threshold(profile,env))
 def test_bounded_explicit_values(self):
  for value in ['1','10','100','1000','0010']:
   self.assertEqual(pusch_failure_threshold('integrated-handover',{'OAI_NTN_PUSCH_FAILURE_THRES':value}),int(value))
 def test_invalid_rejected_before_launch(self):
  root=Path(__file__).resolve().parents[1]
  for value in ['0','1001','-1','1.0','1;echo x','1 2','99999999999999999999']:
   with self.assertRaises(ValueError):resolve_runtime(root,'integrated-handover','dtx-test',{'OAI_NTN_PUSCH_FAILURE_THRES':value})

 def test_launch_environment_and_manifest_agree(self):
  from unittest.mock import patch
  import experiment
  root=Path(__file__).resolve().parents[1]
  for profile in ['legacy-handover','zky']:
   raw={'OAI_NTN_PUSCH_FAILURE_THRES':'100'}
   config=resolve_runtime(root,profile,'dtx-test',raw)
   with patch.object(experiment,'read_trace',return_value=[[8200]]), patch.object(experiment,'sha256',return_value='a'*64), patch.object(experiment,'commit_at',return_value='b'*40), patch.object(experiment,'source_identity',return_value={'kind':'test'}):
    env=experiment.environments(config,raw,1)
    children=experiment.launcher_environments(env,qd_required=False)
    self.assertEqual(children['gnb']['OAI_NTN_PUSCH_FAILURE_THRES'],'100')
    manifest=experiment.build_manifest(config,1,env)
    self.assertEqual(manifest['pusch_failure_threshold_override'],100 if profile!='zky' else None)

if __name__=='__main__':unittest.main()
