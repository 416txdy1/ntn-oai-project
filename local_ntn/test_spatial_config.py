"""验证原始模板保护与 MISO 配置约束。"""
import unittest
from spatial_config import configure_miso, spatial_mode, spatial_ports

class SpatialConfigTest(unittest.TestCase):
    def test_native_two_ports(self) -> None:
        original = 'gNBs = ({\n});\nRUs=({\n nb_tx = 1;\n nb_rx = 1;\n});'
        result = configure_miso(original)
        self.assertIn('nb_tx = 2;', result)
        self.assertIn('nb_rx = 2;', result)
        self.assertIn('pdsch_AntennaPorts_XP = 2;', result)
        self.assertIn('maxMIMO_layers = 1;', result)
        self.assertEqual(result, configure_miso(result))
        self.assertIn('nb_tx = 1;', original)

    def test_four_ports(self) -> None:
        original = 'gNBs = ({\n});\nRUs=({\n nb_tx = 1;\n nb_rx = 1;\n});'
        result = configure_miso(original, 4)
        for field in ('nb_tx = 4;', 'nb_rx = 4;', 'pdsch_AntennaPorts_N1 = 2;', 'maxMIMO_layers = 1;'):
            self.assertIn(field, result)
        self.assertEqual(result, configure_miso(result, 4))
        self.assertEqual(spatial_ports({'OAI_SPATIAL_MODE':'miso4'}), 4)
        self.assertEqual(spatial_ports({}), 1)
        self.assertEqual(spatial_ports({'OAI_SPATIAL_MODE':'miso4-subarray'}), 4)
        with self.assertRaises(ValueError): configure_miso(original, 3)

    def test_guards(self) -> None:
        self.assertFalse(spatial_mode({}))
        self.assertTrue(spatial_mode({'OAI_SPATIAL_MODE': 'miso2'}))
        with self.assertRaises(ValueError): spatial_mode({'OAI_SPATIAL_MODE': 'typo'})
        with self.assertRaises(ValueError): configure_miso('gNBs=({});')

if __name__ == '__main__': unittest.main()
