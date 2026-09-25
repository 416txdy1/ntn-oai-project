"""Audit STKTRACE2 + QDCHANNEL1 composition for duplicated impairments."""

from __future__ import annotations

import argparse
import cmath
import csv
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Sequence

from quadriga.tools.validate_bundle import ValidationError, validate_bundle


LIGHT_SPEED_M_S = 299_792_458.0


class LinkBudgetAuditError(ValueError):
    """The STK/QuaDRiGa composition violates the non-duplication contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LinkBudgetAuditError(message)


def _read_stktrace2(path: Path) -> tuple[list[str], list[dict[str, float]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        _require(stream.readline().strip() == "STKTRACE2", "输入不是 STKTRACE2")
        header = stream.readline().strip()
        _require(header.startswith("#"), "STKTRACE2 缺少字段头")
        names = [name.strip() for name in header[1:].split(",")]
        required = {
            "time", "x", "y", "z", "vx", "vy", "vz",
            "ue_x", "ue_y", "ue_z", "dl_power_dbw", "ul_power_dbw",
            "dl_valid", "ul_valid",
        }
        _require(required <= set(names), "STKTRACE2 缺少审计字段")
        rows = []
        for line_number, values in enumerate(csv.reader(stream), 3):
            _require(len(values) == len(names), f"STKTRACE2 第 {line_number} 行字段数错误")
            row = dict(zip(names, (float(value) for value in values)))
            _require(all(math.isfinite(value) for value in row.values()), "STKTRACE2 包含非有限值")
            rows.append(row)
    _require(len(rows) >= 2, "STKTRACE2 至少需要两个快照")
    return names, rows


def _read_scalars(path: Path, code: str) -> list[float]:
    payload = path.read_bytes()
    item_size = struct.calcsize("<" + code)
    _require(len(payload) % item_size == 0, f"{path.name} 字节数与类型不匹配")
    return [value[0] for value in struct.iter_unpack("<" + code, payload)]


def _center(values: Sequence[float]) -> list[float]:
    mean = math.fsum(values) / len(values)
    return [value - mean for value in values]


def _slope(y_values: Sequence[float], x_values: Sequence[float]) -> float:
    x = _center(x_values)
    y = _center(y_values)
    denominator = math.fsum(value * value for value in x)
    _require(denominator > 0.0, "审计自变量没有变化")
    return math.fsum(a * b for a, b in zip(x, y)) / denominator


def _correlation(a_values: Sequence[float], b_values: Sequence[float]) -> float:
    a = _center(a_values)
    b = _center(b_values)
    denominator = math.sqrt(
        math.fsum(value * value for value in a)
        * math.fsum(value * value for value in b)
    )
    if denominator == 0.0:
        return 0.0
    return math.fsum(x * y for x, y in zip(a, b)) / denominator


def audit_link_budget(bundle_dir: Path, trace_path: Path) -> dict[str, float | int | str]:
    bundle_dir = Path(bundle_dir)
    trace_path = Path(trace_path)
    summary = validate_bundle(bundle_dir)
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    dimensions = manifest["dimensions"]
    _require(
        dimensions["rx_antennas"] == 1 and dimensions["tx_antennas"] == 1,
        "当前链路预算审计仅支持卫星—UE SISO bundle",
    )

    trace_sha256 = hashlib.sha256(trace_path.read_bytes()).hexdigest()
    _require(
        trace_sha256 == manifest["provenance"]["stk_trace_sha256"],
        "bundle 与 STKTRACE2 provenance 不一致",
    )
    _, rows = _read_stktrace2(trace_path)
    snapshots = dimensions["snapshots"]
    paths = dimensions["paths"]
    _require(len(rows) == snapshots, "STKTRACE2 与 bundle 快照数量不一致")

    files = manifest["files"]
    times = _read_scalars(bundle_dir / files["times"]["path"], "d")
    delays = _read_scalars(bundle_dir / files["delays"]["path"], "d")
    interleaved = _read_scalars(bundle_dir / files["coefficients"]["path"], "f")
    gains = _read_scalars(bundle_dir / files["residual_gain_db"]["path"], "f")
    coefficients = [
        complex(interleaved[index], interleaved[index + 1])
        for index in range(0, len(interleaved), 2)
    ]

    max_time_error_s = max(abs(time - row["time"]) for time, row in zip(times, rows))
    _require(max_time_error_s <= 1e-9, "bundle 时间轴与 STKTRACE2 不对齐")

    max_power_error = 0.0
    max_zero_delay_error_s = 0.0
    max_reference_phase_error_rad = 0.0
    reference_phase: complex | None = None
    for snapshot in range(snapshots):
        start = snapshot * paths
        group = coefficients[start : start + paths]
        group_delays = delays[start : start + paths]
        powers = [abs(value) ** 2 for value in group]
        max_power_error = max(max_power_error, abs(math.fsum(powers) - 1.0))
        active = [index for index, power in enumerate(powers) if power > 1e-12]
        _require(bool(active), f"快照 {snapshot} 没有激活路径")
        earliest = min(group_delays[index] for index in active)
        max_zero_delay_error_s = max(max_zero_delay_error_s, abs(earliest))
        candidates = [
            index
            for index in active
            if math.isclose(group_delays[index], earliest, abs_tol=1e-12)
        ]
        reference_index = max(candidates, key=powers.__getitem__)
        current_phase = group[reference_index] / abs(group[reference_index])
        if reference_phase is None:
            reference_phase = current_phase
        max_reference_phase_error_rad = max(
            max_reference_phase_error_rad,
            abs(cmath.phase(current_phase / reference_phase)),
        )

    _require(max_power_error <= 2e-5, "QuaDRiGa 路径功率未逐快照归一化")
    _require(max_zero_delay_error_s <= 1e-12, "QuaDRiGa 时延未转换为零参考超额时延")
    _require(
        max_reference_phase_error_rad <= 2e-4,
        "QuaDRiGa 公共相位未稳定，可能重复主体 Doppler",
    )

    direction = manifest["radio"]["link_direction"]
    power_name = "dl_power_dbw" if direction == "downlink" else "ul_power_dbw"
    valid_name = "dl_valid" if direction == "downlink" else "ul_valid"
    frequency_hz = float(manifest["radio"]["center_frequency_hz"])
    ranges_m = []
    stk_power_dbw = []
    residual_gain_db = []
    radial_velocity_m_s = []
    for row, residual in zip(rows, gains):
        if int(row[valid_name]) != 1:
            continue
        displacement = (
            row["x"] - row["ue_x"],
            row["y"] - row["ue_y"],
            row["z"] - row["ue_z"],
        )
        distance = math.sqrt(math.fsum(value * value for value in displacement))
        _require(distance > 0.0, "卫星—UE 距离必须大于零")
        unit_los = tuple(value / distance for value in displacement)
        radial_velocity = math.fsum(
            row[name] * unit for name, unit in zip(("vx", "vy", "vz"), unit_los)
        )
        ranges_m.append(distance)
        stk_power_dbw.append(row[power_name])
        residual_gain_db.append(residual)
        radial_velocity_m_s.append(radial_velocity)
    _require(len(ranges_m) >= 2, "所选方向没有足够的有效 STK 快照")

    free_space_gain_db = [
        -20.0 * math.log10(4.0 * math.pi * distance * frequency_hz / LIGHT_SPEED_M_S)
        for distance in ranges_m
    ]
    combined_power_dbw = [
        stk + residual for stk, residual in zip(stk_power_dbw, residual_gain_db)
    ]
    stk_fspl_slope = _slope(stk_power_dbw, free_space_gain_db)
    residual_fspl_slope = _slope(residual_gain_db, free_space_gain_db)
    combined_fspl_slope = _slope(combined_power_dbw, free_space_gain_db)
    residual_fspl_correlation = _correlation(residual_gain_db, free_space_gain_db)
    max_residual_abs_db = max(abs(value) for value in residual_gain_db)

    _require(max_residual_abs_db <= 1e-6, "residual_gain_db 非零，可能重复 STK 大尺度增益")
    _require(abs(residual_fspl_slope) <= 1e-3, "residual_gain_db 仍包含距离路径损耗")
    _require(
        abs(combined_fspl_slope - stk_fspl_slope) <= 1e-3,
        "组合信道改变了 STK 路径损耗斜率",
    )

    doppler_hz = [
        -velocity / LIGHT_SPEED_M_S * frequency_hz for velocity in radial_velocity_m_s
    ]
    delays_s = [distance / LIGHT_SPEED_M_S for distance in ranges_m]
    return {
        "format": summary["format"],
        "link_direction": direction,
        "snapshots": snapshots,
        "paths": paths,
        "max_time_error_s": max_time_error_s,
        "max_tap_power_error": max_power_error,
        "max_zero_delay_error_s": max_zero_delay_error_s,
        "max_reference_phase_error_rad": max_reference_phase_error_rad,
        "max_residual_gain_abs_db": max_residual_abs_db,
        "stk_fspl_slope": stk_fspl_slope,
        "residual_fspl_slope": residual_fspl_slope,
        "residual_fspl_correlation": residual_fspl_correlation,
        "combined_fspl_slope": combined_fspl_slope,
        "bulk_delay_min_s": min(delays_s),
        "bulk_delay_max_s": max(delays_s),
        "bulk_doppler_min_hz": min(doppler_hz),
        "bulk_doppler_max_hz": max(doppler_hz),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    try:
        report = audit_link_budget(args.bundle, args.trace)
    except (LinkBudgetAuditError, ValidationError) as error:
        print(f"LINK_BUDGET_AUDIT_FAILED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
