"""Bounded, explicitly recorded NTN diagnostic setting; no live resources."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'local_ntn'))
from runtime_config import pusch_failure_threshold, pdcp_reordering_ms, resolve_runtime

from ntn_timing_budget import cell_koffset_ms, timing_budget

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

 def test_pdcp_native_finite_values(self):
  for value in ['100','200','500']:
   self.assertEqual(pdcp_reordering_ms('integrated-handover',{'OAI_NTN_PDCP_REORDERING_MS':value}),int(value))
  for value in ['0','501','infinity','ms500','500;echo x',' 500']:
   with self.assertRaises(ValueError):pdcp_reordering_ms('legacy-handover',{'OAI_NTN_PDCP_REORDERING_MS':value})
 def test_pdcp_old_profile_and_default_unchanged(self):
  self.assertIsNone(pdcp_reordering_ms('zky',{'OAI_NTN_PDCP_REORDERING_MS':'infinity'}))
  self.assertIsNone(pdcp_reordering_ms('integrated-handover',{}))
 def test_pdcp_manifest_and_requested_seed(self):
  from unittest.mock import patch
  import experiment
  root=Path(__file__).resolve().parents[1]
  raw={'OAI_NTN_PDCP_REORDERING_MS':'500','OAI_RNGSEED':'20260925'}
  config=resolve_runtime(root,'legacy-handover','pdcp-test',raw)
  with patch.object(experiment,'read_trace',return_value=[[8200]]), patch.object(experiment,'sha256',return_value='a'*64), patch.object(experiment,'commit_at',return_value='b'*40), patch.object(experiment,'source_identity',return_value={'kind':'test'}):
   env=experiment.environments(config,raw,1)
   self.assertEqual(experiment.launcher_environments(env,qd_required=False)['gnb']['OAI_NTN_PDCP_REORDERING_MS'],'500')
   manifest=experiment.build_manifest(config,1,env)
   self.assertEqual(manifest['pdcp_reordering_ms_override'],500)
   self.assertEqual(manifest['oai_rngseed_requested'],'20260925')

 def test_koffset_validation_and_budget(self):
  from preflight import read_trace
  root=Path(__file__).resolve().parents[1]
  self.assertIsNone(cell_koffset_ms('zky',{'OAI_NTN_CELL_KOFFSET_MS':'bad'}))
  self.assertIsNone(cell_koffset_ms('legacy-handover',{}))
  for value in ['0','1024','-1','48;echo x','48.0']:
   with self.assertRaises(ValueError):resolve_runtime(root,'integrated-handover','k-test',{'OAI_NTN_CELL_KOFFSET_MS':value})
  rows=read_trace(root/'local_ntn/stk_trace_seamless.csv')
  with self.assertRaises(ValueError):timing_budget(rows,40,'legacy-linear')
  with self.assertRaises(ValueError):timing_budget(rows,48,'hermite')
  b=timing_budget(rows,48,'legacy-linear')
  self.assertEqual(b['minimum_integer_koffset_ms'],45)
  self.assertAlmostEqual(b['max_geometric_roundtrip_ms'],42.95659299863363)
  self.assertAlmostEqual(b['nominal_write_lead_ms'],8.043407001366369)
  self.assertGreater(timing_budget(rows,80,'legacy-linear')['nominal_write_lead_ms'],40)

 def test_diag_window_input(self):
  from runtime_config import timing_diag_start_iq_s
  self.assertIsNone(timing_diag_start_iq_s('zky',{'OAI_NTN_TIMING_DIAG_START_IQ_S':'bad'}))
  self.assertEqual(timing_diag_start_iq_s('integrated-handover',{}),0)
  for value in ['0','580','620']:
   self.assertEqual(timing_diag_start_iq_s('legacy-handover',{'OAI_NTN_TIMING_DIAG_START_IQ_S':value}),int(value))
  for value in ['-1','621','580.0','580;echo x','0000']:
   with self.assertRaises(ValueError):timing_diag_start_iq_s('legacy-handover',{'OAI_NTN_TIMING_DIAG_START_IQ_S':value})

if __name__=='__main__':unittest.main()
