"""验证新连接 profile 的空间模式选择，不启动 modem。"""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from runtime_config import resolve_runtime
from spatial_config import configure_miso
import handover_acceptance


class HandoverSpatialTests(unittest.TestCase):
    def test_profile_selects_new_trace_and_four_port_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = resolve_runtime(root, 'integrated-handover', 'miso-test',
                                     {'OAI_SPATIAL_MODE': 'miso4-subarray'})
            self.assertEqual(config.trace, root / 'local_ntn/stk_trace_seamless.csv')
            self.assertEqual(config.dl_bundle, root / 'examples/handover-miso4/downlink')
            self.assertEqual(config.ul_bundle, root / 'examples/handover-miso4/uplink')
            self.assertEqual(config.interpolation, 'legacy-linear')
            self.assertEqual(config.rf_port, 4044)

    def test_old_trace_bundle_cannot_enter_isolated_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, 'scope'):
                resolve_runtime(root, 'integrated-handover', 'miso-test', {
                    'OAI_SPATIAL_MODE': 'miso4-subarray',
                    'OAI_QD_DL_CHANNEL': str(root / 'examples/fdd-miso4-subarray/downlink')})

    def test_no_qd_legacy_cannot_claim_miso(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'no spatial'):
                resolve_runtime(Path(directory), 'legacy-handover', 'miso-test',
                                {'OAI_SPATIAL_MODE': 'miso4-subarray'})

    def test_short_case_retains_four_port_selection(self) -> None:
        config, env = handover_acceptance.selected_runtime(
            'firsthandover', 'integrated-handover', 'miso-test',
            {'OAI_SPATIAL_MODE': 'miso4-subarray'})
        self.assertEqual(config.dl_bundle.parts[-4:],
                         ('examples', 'handover-miso4', 'firsthandover', 'downlink'))
        self.assertEqual(env['OAI_SPATIAL_MODE'], 'miso4-subarray')

    def test_four_ports_still_one_layer(self) -> None:
        config = configure_miso('gNBs = ({\n});\nnb_tx = 1;\nnb_rx = 1;\n', 4)
        self.assertIn('nb_tx = 4;', config)
        self.assertIn('nb_rx = 4;', config)
        self.assertIn('maxMIMO_layers = 1;', config)


if __name__ == '__main__':
    unittest.main()
