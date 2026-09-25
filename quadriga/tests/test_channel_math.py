from __future__ import annotations

import cmath
import math
import unittest

from quadriga.tools.channel_math import ecef_to_enu, normalize_channel


class ChannelMathTest(unittest.TestCase):
    def test_common_phase_is_removed_but_relative_phase_is_preserved(self) -> None:
        common = cmath.exp(1j * 0.8)
        coefficients = [1 + 0j, 0.5j, common, 0.5j * common]
        result = normalize_channel(
            coefficients,
            [1.0, 1.2, 2.0, 2.2],
            snapshots=2,
            rx_antennas=1,
            tx_antennas=1,
            paths=2,
        )
        self.assertAlmostEqual(
            cmath.phase(result.coefficients[0]), cmath.phase(result.coefficients[2]), places=12
        )
        first_ratio = result.coefficients[1] / result.coefficients[0]
        second_ratio = result.coefficients[3] / result.coefficients[2]
        self.assertAlmostEqual(first_ratio.real, second_ratio.real, places=12)
        self.assertAlmostEqual(first_ratio.imag, second_ratio.imag, places=12)

    def test_power_delay_and_residual_gain_contract(self) -> None:
        result = normalize_channel(
            [2 + 0j, 1 + 0j, 4 + 0j, 2 + 0j],
            [3.0, 3.25, 8.0, 8.25],
            snapshots=2,
            rx_antennas=1,
            tx_antennas=1,
            paths=2,
        )
        for start in (0, 2):
            self.assertAlmostEqual(
                sum(abs(value) ** 2 for value in result.coefficients[start : start + 2]), 1.0
            )
        self.assertEqual(result.excess_delays_s, (0.0, 0.25, 0.0, 0.25))
        self.assertAlmostEqual(sum(result.residual_gain_db) / 2, 0.0, places=12)
        self.assertAlmostEqual(
            result.residual_gain_db[1] - result.residual_gain_db[0],
            10 * math.log10(4),
            places=12,
        )

    def test_zero_power_link_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "没有激活路径"):
            normalize_channel(
                [0j, 0j],
                [0.0, 1.0],
                snapshots=1,
                rx_antennas=1,
                tx_antennas=1,
                paths=2,
            )

    def test_ecef_to_enu_axes_at_equator(self) -> None:
        reference = (6_378_137.0, 0.0, 0.0)
        east, north, up = ecef_to_enu((6_378_139.0, 1.0, 3.0), reference)
        self.assertAlmostEqual(east, 1.0, places=9)
        self.assertAlmostEqual(north, 3.0, places=9)
        self.assertAlmostEqual(up, 2.0, places=9)


if __name__ == "__main__":
    unittest.main()
