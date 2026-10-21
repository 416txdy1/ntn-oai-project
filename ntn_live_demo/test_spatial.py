"""Reject false MISO claims and keep derived antenna provenance consistent."""
import json
from pathlib import Path
import tempfile
import unittest
from live_config import radio_environment, child_arguments
from spatial_evidence import audit_spatial
from causal import derive_inputs, sha


class SpatialTests(unittest.TestCase):
    def fixture(self, root):
        config=root/'gnb.conf';config.write_text('nb_tx = 4;\nnb_rx = 4;\nmaxMIMO_layers = 1;\n')
        logs={}
        for side,dimensions in [('gnb','1 Tx x 4 Rx'),('ue','4 Tx x 1 Rx')]:
            path=root/(side+'.txt');text='QDCHANNEL1 spatial ports: '+dimensions+'\nQDCHANNEL1 compute workers: 8\n'
            if side=='gnb':
                text+=''.join(f'QDCHANNEL1 Tx port {p} IQ={i} mean_energy=3.0\n' for p in range(4) for i in range(2))
            path.write_text(text);logs[side]=str(path)
        return dict(spatial_mode_requested='miso4-subarray',qd_workers_requested='8',gnb_config=str(config),logs=logs)

    def test_real_four_ports_pass(self):
        with tempfile.TemporaryDirectory() as d:
            proof=audit_spatial(self.fixture(Path(d)),'miso4-subarray',8)
            self.assertEqual(proof['active_tx_ports'],[0,1,2,3])

    def test_missing_actual_port_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.fixture(Path(d));p=Path(m['logs']['gnb'])
            p.write_text(p.read_text().replace('mean_energy=3.0','mean_energy=0.0'))
            with self.assertRaisesRegex(ValueError,'nonzero IQ'):audit_spatial(m,'miso4-subarray',8)

    def test_missing_or_wrong_dimensions_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.fixture(Path(d));p=Path(m['logs']['ue']);p.write_text(p.read_text().replace('4 Tx x 1 Rx','1 Tx x 1 Rx'))
            with self.assertRaisesRegex(ValueError,'dimensions'):audit_spatial(m,'miso4-subarray',8)

    def test_missing_workers_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.fixture(Path(d));p=Path(m['logs']['ue']);p.write_text(p.read_text().replace('compute workers: 8','compute workers: 1'))
            with self.assertRaisesRegex(ValueError,'worker'):audit_spatial(m,'miso4-subarray',8)

    def test_explicit_paths_for_modes_and_cases(self):
        for mode,folder in [('siso','handover'),('miso4-subarray','handover-miso4')]:
            for case in ('static','firsthandover','full'):
                env=radio_environment(Path('/new'),case,mode,8)
                self.assertIn('/examples/'+folder+'/',env['OAI_QD_DL_CHANNEL'])
                self.assertEqual(env['OAI_QD_WORKERS'],'1' if mode=='siso' else '8')
                self.assertEqual('/firsthandover/' in env['OAI_QD_DL_CHANNEL'],case=='firsthandover')

    def test_intervention_updates_sidecar_hashes_without_changing_taps(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'local_ntn').mkdir();suite=root/'suite';suite.mkdir()
            rows=[]
            for i in range(5):
                row=[str(8200+i)]+['0']*18;row[18]='20';rows.append(','.join(row))
            (root/'local_ntn/stk_trace_seamless.csv').write_text('STKTRACE2\ncolumns\n'+'\n'.join(rows)+'\n')
            (root/'local_ntn/satellite_schedule_seamless.csv').write_text('schedule')
            original=root/'examples/handover-miso4';original.mkdir(parents=True)
            provenance={'inputs':{'trace':{}},'bundles':{}}
            for direction in ('downlink','uplink'):
                p=original/direction;p.mkdir();(p/'manifest.json').write_text(json.dumps({'provenance':{}}))
                (p/'antenna.json').write_text(json.dumps({'profile':'satellite_16x16_4port_ground_omni','manifest_sha256':'old','stk_trace_sha256':'old'}))
                (p/'coefficients.cf32').write_bytes(b'unchanged coefficients')
                provenance['bundles'][direction]={}
            (original/'provenance.json').write_text(json.dumps(provenance))
            old_hash=sha(original/'downlink/coefficients.cf32')
            env,_=derive_inputs(root,suite,True,1,3,16,'miso4-subarray')
            p=Path(env['OAI_QD_DL_CHANNEL']);antenna=json.loads((p/'antenna.json').read_text())
            self.assertEqual(antenna['manifest_sha256'],sha(p/'manifest.json'))
            self.assertEqual(antenna['stk_trace_sha256'],sha(env['OAI_STK_TRACE']))
            self.assertEqual(sha(p/'coefficients.cf32'),old_hash)
            completion=json.loads((p.parent/'provenance.json').read_text())
            self.assertEqual(completion['bundles']['downlink']['antenna_sha256'],sha(p/'antenna.json'))


if __name__=='__main__':unittest.main()
