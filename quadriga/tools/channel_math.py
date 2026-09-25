"""QDCHANNEL1 导出阶段的运行时无关参考数学实现。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class NormalizedChannel:
    """按磁盘轴顺序 `[snapshot, rx, tx, path]` 排列的导出结果。"""

    coefficients: tuple[complex, ...]
    excess_delays_s: tuple[float, ...]
    residual_gain_db: tuple[float, ...]


def normalize_channel(
    coefficients: Sequence[complex],
    delays_s: Sequence[float],
    *,
    snapshots: int,
    rx_antennas: int,
    tx_antennas: int,
    paths: int,
    active_power_epsilon: float = 1e-15,
) -> NormalizedChannel:
    """去除公共相位、归一化路径功率并提取零均值残余增益。

    QuaDRiGa 的每个快照包含绝对路径功率和公共传播相位。STKTRACE2 已经
    提供绝对增益与主体 Doppler，因此这里用每个天线链路的最早激活路径
    作为公共相位参考，并保留路径之间的相对相位。
    """

    dimensions = (snapshots, rx_antennas, tx_antennas, paths)
    if any(not isinstance(value, int) or value < 1 for value in dimensions):
        raise ValueError("所有维度必须是正整数")
    expected = math.prod(dimensions)
    if len(coefficients) != expected or len(delays_s) != expected:
        raise ValueError(f"输入长度必须为 {expected}")

    normalized = [0j] * expected
    excess_delays = [0.0] * expected
    gain_db = [0.0] * (snapshots * rx_antennas * tx_antennas)
    phase_reference: list[complex | None] = [None] * (rx_antennas * tx_antennas)

    for snapshot in range(snapshots):
        for rx in range(rx_antennas):
            for tx in range(tx_antennas):
                link = (snapshot * rx_antennas + rx) * tx_antennas + tx
                antenna_link = rx * tx_antennas + tx
                start = link * paths
                group = [complex(value) for value in coefficients[start : start + paths]]
                group_delays = [float(value) for value in delays_s[start : start + paths]]
                if not all(math.isfinite(value.real) and math.isfinite(value.imag) for value in group):
                    raise ValueError("系数包含非有限值")
                if not all(math.isfinite(value) and value >= 0.0 for value in group_delays):
                    raise ValueError("时延必须有限且非负")

                powers = [abs(value) ** 2 for value in group]
                total_power = sum(powers)
                if not math.isfinite(total_power) or total_power <= active_power_epsilon:
                    raise ValueError(f"link {link} 没有激活路径")
                active = [index for index, power in enumerate(powers) if power > active_power_epsilon]
                earliest_delay = min(group_delays[index] for index in active)
                candidates = [
                    index
                    for index in active
                    if math.isclose(group_delays[index], earliest_delay, abs_tol=1e-15)
                ]
                reference_index = max(candidates, key=powers.__getitem__)
                current_reference = group[reference_index] / abs(group[reference_index])
                if phase_reference[antenna_link] is None:
                    phase_reference[antenna_link] = current_reference
                rotation = phase_reference[antenna_link] / current_reference
                scale = math.sqrt(total_power)

                for path, value in enumerate(group):
                    normalized[start + path] = value * rotation / scale
                    excess_delays[start + path] = max(0.0, group_delays[path] - earliest_delay)
                gain_db[link] = 10.0 * math.log10(total_power)

    for rx in range(rx_antennas):
        for tx in range(tx_antennas):
            indices = [
                (snapshot * rx_antennas + rx) * tx_antennas + tx
                for snapshot in range(snapshots)
            ]
            mean_gain = sum(gain_db[index] for index in indices) / snapshots
            for index in indices:
                gain_db[index] -= mean_gain

    return NormalizedChannel(tuple(normalized), tuple(excess_delays), tuple(gain_db))


def ecef_to_enu(
    point_ecef_m: Sequence[float], reference_ecef_m: Sequence[float]
) -> tuple[float, float, float]:
    """将 WGS84 ECEF 点变换到参考点的局部 ENU 坐标。"""

    if len(point_ecef_m) != 3 or len(reference_ecef_m) != 3:
        raise ValueError("ECEF 坐标必须包含三个分量")
    x, y, z = (float(value) for value in reference_ecef_m)
    semi_major = 6_378_137.0
    eccentricity_squared = 6.69437999014e-3
    longitude = math.atan2(y, x)
    horizontal = math.hypot(x, y)
    latitude = math.atan2(z, horizontal * (1.0 - eccentricity_squared))
    for _ in range(10):
        prime_vertical = semi_major / math.sqrt(
            1.0 - eccentricity_squared * math.sin(latitude) ** 2
        )
        height = horizontal / math.cos(latitude) - prime_vertical
        latitude = math.atan2(
            z,
            horizontal
            * (1.0 - eccentricity_squared * prime_vertical / (prime_vertical + height)),
        )

    dx, dy, dz = (
        float(point_ecef_m[index]) - float(reference_ecef_m[index]) for index in range(3)
    )
    sin_lon, cos_lon = math.sin(longitude), math.cos(longitude)
    sin_lat, cos_lat = math.sin(latitude), math.cos(latitude)
    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up
