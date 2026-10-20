"""使用 Python 标准库校验 QDCHANNEL1 bundle。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """Bundle 不符合 QDCHANNEL1 契约。"""


FILE_LAYOUT = {
    "times": ("float64", 8),
    "delays": ("float64", 8),
    "coefficients": ("complex64_interleaved", 8),
    "residual_gain_db": ("float32", 4),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bundle_file(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    _require(not candidate.is_absolute(), f"文件路径必须是相对路径: {relative}")
    _require(".." not in candidate.parts, f"文件路径不能越出 bundle: {relative}")
    resolved = (root / candidate).resolve()
    _require(root.resolve() in resolved.parents, f"文件路径不能越出 bundle: {relative}")
    return resolved


def _positive_int(value: Any, name: str, minimum: int = 1) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{name} 必须是整数")
    _require(value >= minimum, f"{name} 必须 >= {minimum}")
    return value


def _read_exact(stream: Any, size: int, label: str) -> bytes:
    data = stream.read(size)
    _require(len(data) == size, f"{label} 提前结束")
    return data


def is_snapshot_count(value: Any) -> bool:
    """MATLAB 大计数可能采用科学计数法；只接受可精确表示的非负整数。"""
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and 0 <= value <= 2**53 - 1 and value == int(value))


def _validate_fidelity(report: dict, antenna: dict, times: tuple[float, ...]) -> None:
    """声明精度时检查数值预算；没有报告的旧数据不视为 1% 合格。"""
    _require(isinstance(report, dict), "fidelity 必须为对象")
    for key in ("tolerance", "bandwidth_hz", "temporal_worst_nrmse", "temporal_global_nrmse",
                "spatial_continuous_band_bound", "combined_bound_at_reference_times",
                "minimum_interval_s", "maximum_interval_s"):
        value = report.get(key)
        _require(isinstance(value, (int, float)) and not isinstance(value, bool)
                 and math.isfinite(value) and value >= 0, f"fidelity.{key} 非法")
    _require(report["tolerance"] == 0.01 and report["bandwidth_hz"] == 4.5e6,
             "fidelity 必须使用 4.5 MHz 和 1% 门限")
    temporal = report["temporal_worst_nrmse"]
    spatial = report["spatial_continuous_band_bound"]
    _require(report["temporal_global_nrmse"] <= temporal, "fidelity 全局误差大于最差误差")
    combined = temporal*(1+spatial)+spatial
    _require(math.isclose(report["combined_bound_at_reference_times"], combined, rel_tol=1e-9, abs_tol=1e-12)
             and combined <= 0.01, "fidelity 组合误差超标或计算不一致")
    _require(antenna.get("wideband_error_bound") == spatial
             and antenna.get("validated_bandwidth_hz") == report["bandwidth_hz"], "fidelity 子阵误差记录不一致")
    output = report.get("output_snapshots")
    references = report.get("reference_snapshots")
    _require(is_snapshot_count(output) and output == len(times) and is_snapshot_count(references)
             and references > output, "fidelity 必须包含独立于输出节点的参考点")
    intervals = [b-a for a, b in zip(times, times[1:])]
    _require(math.isclose(report["minimum_interval_s"], min(intervals), rel_tol=1e-9, abs_tol=1e-12)
             and math.isclose(report["maximum_interval_s"], max(intervals), rel_tol=1e-9, abs_tol=1e-12),
             "fidelity 时间间隔与 bundle 不一致")
    if "scope" in report:
        _require(report["scope"] == "prefix_before_unchanged_legacy_tail", "fidelity 认证范围非法")
        start, end = report.get("validated_time_start_s"), report.get("validated_time_end_s")
        _require(start == times[0] and end in times and end > start, "fidelity 认证时间范围不一致")
        _require(report.get("unchanged_tail_snapshots") == sum(t > end for t in times),
                 "fidelity 未认证尾部数量不一致")


def validate_bundle(root: Path) -> dict[str, Any]:
    root = Path(root)
    manifest_path = root / "manifest.json"
    _require(manifest_path.is_file(), "缺少 manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    _require(manifest.get("format") == "QDCHANNEL1", "format 必须是 QDCHANNEL1")
    _require(manifest.get("schema_version") == 1, "schema_version 必须是 1")
    _require(manifest.get("byte_order") == "little", "v1 只支持 little endian")
    _require(manifest.get("axes") == ["snapshot", "rx", "tx", "path"], "axes 顺序错误")

    dimensions = manifest.get("dimensions", {})
    snapshots = _positive_int(dimensions.get("snapshots"), "snapshots", 2)
    rx_antennas = _positive_int(dimensions.get("rx_antennas"), "rx_antennas")
    tx_antennas = _positive_int(dimensions.get("tx_antennas"), "tx_antennas")
    paths = _positive_int(dimensions.get("paths"), "paths")
    links = snapshots * rx_antennas * tx_antennas
    taps = links * paths

    radio = manifest.get("radio", {})
    center_frequency = radio.get("center_frequency_hz")
    _require(isinstance(center_frequency, (int, float)) and math.isfinite(center_frequency), "中心频率必须是有限数")
    _require(center_frequency > 0, "中心频率必须大于 0")
    _require(radio.get("link_direction") in {"downlink", "uplink"}, "link_direction 必须是 downlink 或 uplink")

    time_contract = manifest.get("time", {})
    _require(time_contract.get("coordinate") == "stk_trace_seconds", "时间坐标必须是 stk_trace_seconds")
    _require(time_contract.get("interpolation") == "linear_complex_and_delay", "插值策略不受支持")
    _require(time_contract.get("out_of_range") == "mute", "越界策略必须是 mute")

    composition = manifest.get("composition", {})
    expected_composition = {
        "bulk_delay_source": "STKTRACE2",
        "bulk_doppler_source": "STKTRACE2",
        "absolute_gain_source": "STKTRACE2",
        "quadriga_delay": "relative_excess_seconds",
        "quadriga_coefficients": "unit_snapshot_link_power",
        "quadriga_large_scale_gain": "zero_mean_residual_db",
    }
    spatial = composition.get("quadriga_coefficients") == "unit_snapshot_mean_link_power"
    if spatial:
        expected_composition["quadriga_coefficients"] = "unit_snapshot_mean_link_power"
    _require(composition == expected_composition, "composition 与 QDCHANNEL1 v1 约定不一致")

    provenance = manifest.get("provenance", {})
    _require(isinstance(provenance.get("quadriga_version"), str) and provenance["quadriga_version"], "缺少 QuaDRiGa 版本")
    _require(isinstance(provenance.get("scenario"), str) and provenance["scenario"], "缺少场景名")
    _positive_int(provenance.get("random_seed"), "random_seed", 0)
    trace_hash = provenance.get("stk_trace_sha256", "")
    _require(isinstance(trace_hash, str) and len(trace_hash) == 64 and all(c in "0123456789abcdef" for c in trace_hash), "STK trace SHA256 非法")

    # 天线信息使用可选 sidecar，保持严格的 QDCHANNEL1 v1 manifest 不变。
    antenna_path = root / "antenna.json"
    if antenna_path.exists():
        antenna = json.loads(antenna_path.read_text(encoding="utf-8"))
        _require(antenna.get("format") == "NTN_ANTENNA1", "antenna.format 非法")
        _require(antenna.get("manifest_sha256") == _sha256(manifest_path), "antenna manifest SHA256 不匹配")
        _require(antenna.get("stk_trace_sha256") == trace_hash, "antenna STK trace SHA256 不匹配")
        _require(antenna.get("link_direction") == radio["link_direction"], "antenna 方向不匹配")
        _require(antenna.get("center_frequency_hz") == center_frequency, "antenna 频率不匹配")
        _require(antenna.get("profile") in {"omni", "satellite_16x16_ground_omni", "satellite_2port_ground_omni", "satellite_4port_ground_omni", "satellite_16x16_4port_ground_omni"}, "antenna profile 非法")
        satellite = _positive_int(antenna.get("satellite_rf_ports"), "antenna satellite_rf_ports")
        ground = _positive_int(antenna.get("ground_rf_ports"), "antenna ground_rf_ports")
        expected = (ground, satellite) if radio["link_direction"] == "downlink" else (satellite, ground)
        _require((rx_antennas, tx_antennas) == expected, "antenna RF 端口维度不一致")
        if antenna["profile"] in {"satellite_2port_ground_omni", "satellite_4port_ground_omni"}:
            ports = 2 if "2port" in antenna["profile"] else 4
            _require(satellite == ports and ground == 1 and spatial, "多端口需要匹配维度与空间归一化")
        elif antenna["profile"] == "satellite_16x16_4port_ground_omni":
            _require(satellite == 4 and ground == 1 and spatial, "四子阵需要匹配维度与空间归一化")
            _require(antenna.get("satellite_rows") == antenna.get("satellite_columns") == 16
                     and antenna.get("subarray_rows") == antenna.get("subarray_columns") == 8
                     and antenna.get("spacing_wavelengths") == 0.5, "子阵几何错误")
            reference = antenna.get("array_reference_frequency_hz")
            _require(isinstance(reference, (int, float)) and math.isfinite(reference) and reference > 0,
                     "子阵参考频率非法")
            _require(math.isclose(antenna.get("element_spacing_m", -1), 299792458 / reference / 2, rel_tol=1e-10)
                     and math.isclose(antenna.get("spacing_wavelengths_at_carrier", -1), center_frequency / reference / 2, rel_tol=1e-10),
                     "子阵物理间距与载频不一致")
            expected_map = [1 + int(i % 16 >= 8) + 2 * int(i // 16 >= 8) for i in range(256)]
            _require(antenna.get("element_port_map") == expected_map and antenna.get("element_index_base") == 1,
                     "子阵映射必须覆盖 256 阵元且每端口 64 个")
            _require(antenna.get("subarray_weight_norm2") == 1, "子阵权重必须单位功率")
            span = antenna.get("max_subarray_delay_span_s")
            _require(isinstance(span, (int, float)) and math.isfinite(span) and span >= 0, "子阵时延跨度非法")
            _require(antenna.get("delay_reduction") == "uniform_subarray_mean_narrowband", "子阵时延近似未声明")
            _require(antenna.get("absolute_array_gain_source") == "not_calibrated_STK_reference", "子阵绝对增益尚未校准")
        else:
            _require(satellite == ground == 1, "原有 profile 仅支持单波束端口")
        if antenna["profile"] == "satellite_16x16_ground_omni":
            _require(antenna.get("satellite_rows") == 16 and antenna.get("satellite_columns") == 16
                     and antenna.get("spacing_wavelengths") == 0.5, "antenna 必须是 16x16、0.5λ 阵列")
            _require(antenna.get("absolute_array_gain_source") == "STKTRACE2", "antenna 绝对增益来源错误")

    expected_counts = {
        "times": snapshots,
        "delays": taps,
        "coefficients": taps,
        "residual_gain_db": links,
    }
    files = manifest.get("files", {})
    _require(set(files) == set(FILE_LAYOUT), "files 必须且只能包含四个标准数组")
    resolved_files: dict[str, Path] = {}
    for name, (dtype, item_size) in FILE_LAYOUT.items():
        spec = files.get(name, {})
        _require(spec.get("dtype") == dtype, f"{name}.dtype 应为 {dtype}")
        _require(spec.get("count") == expected_counts[name], f"{name}.count 与维度不一致")
        expected_bytes = expected_counts[name] * item_size
        _require(spec.get("bytes") == expected_bytes, f"{name}.bytes 与维度不一致")
        path = _bundle_file(root, spec.get("path", ""))
        _require(path.is_file(), f"缺少数据文件: {path.name}")
        _require(path.stat().st_size == expected_bytes, f"{name} 文件大小错误")
        _require(_sha256(path) == spec.get("sha256"), f"{name} SHA256 不匹配")
        resolved_files[name] = path

    with resolved_files["times"].open("rb") as stream:
        times = struct.unpack(f"<{snapshots}d", _read_exact(stream, snapshots * 8, "times"))
    _require(all(math.isfinite(value) for value in times), "times 包含非有限值")
    _require(all(left < right for left, right in zip(times, times[1:])), "times 必须严格递增")

    if antenna_path.exists() and "fidelity" in antenna:
        _validate_fidelity(antenna["fidelity"], antenna, times)

    group_links = rx_antennas * tx_antennas if spatial else 1
    group_paths = paths * group_links
    coefficient_format = struct.Struct(f"<{group_paths * 2}f")
    delay_format = struct.Struct(f"<{group_paths}d")
    with resolved_files["coefficients"].open("rb") as coefficients, resolved_files["delays"].open("rb") as delays:
        for link_index in range(0, links, group_links):
            coefficient_values = coefficient_format.unpack(
                _read_exact(coefficients, coefficient_format.size, f"coefficients link {link_index}")
            )
            delay_values = delay_format.unpack(
                _read_exact(delays, delay_format.size, f"delays link {link_index}")
            )
            _require(all(math.isfinite(value) for value in coefficient_values), "coefficients 包含非有限值")
            _require(all(math.isfinite(value) and value >= 0 for value in delay_values), "delays 必须有限且非负")
            powers = [
                coefficient_values[2 * path] ** 2 + coefficient_values[2 * path + 1] ** 2
                for path in range(group_paths)
            ]
            total_power = sum(powers)
            _require(math.isclose(total_power / group_links, 1.0, rel_tol=1e-5, abs_tol=1e-6), f"link {link_index} 路径功率未归一化")
            active_delays = [delay_values[index] for index, power in enumerate(powers) if power > 1e-12]
            _require(active_delays and min(active_delays) <= 1e-12, f"link {link_index} 缺少零参考时延")

    gain_format = struct.Struct("<f")
    gain_sums = [0.0] * (rx_antennas * tx_antennas)
    with resolved_files["residual_gain_db"].open("rb") as gains:
        for link_index in range(links):
            (gain,) = gain_format.unpack(_read_exact(gains, gain_format.size, f"gain link {link_index}"))
            _require(math.isfinite(gain), "residual_gain_db 包含非有限值")
            gain_sums[link_index % len(gain_sums)] += gain
    for antenna_link, gain_sum in enumerate(gain_sums):
        _require(abs(gain_sum / snapshots) <= 1e-3, f"antenna link {antenna_link} 残余增益均值不为零")

    return {
        "format": "QDCHANNEL1",
        "snapshots": snapshots,
        "rx_antennas": rx_antennas,
        "tx_antennas": tx_antennas,
        "paths": paths,
        "link_direction": radio["link_direction"],
        "start_time_s": times[0],
        "end_time_s": times[-1],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 QDCHANNEL1 bundle")
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        summary = validate_bundle(args.bundle)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        print(f"QDCHANNEL1 validation failed: {error}")
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
