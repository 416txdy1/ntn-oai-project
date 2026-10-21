"""检查与 bundle 绑定的时间插值、FIR、子阵组合精度报告。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from quadriga.tools.validate_bundle import is_snapshot_count, validate_bundle


def validate_runtime_fidelity(bundle: Path) -> dict:
    summary = validate_bundle(bundle)
    report = json.loads((bundle / 'runtime_fidelity_report.json').read_text())
    digest = hashlib.sha256((bundle / 'manifest.json').read_bytes()).hexdigest()
    if report.get('bundle_manifest_sha256') != digest:
        raise ValueError('运行时精度报告与当前 bundle 不匹配')
    for key in ('temporal_global_nrmse', 'temporal_worst_nrmse', 'fir_worst_bound',
                'joint_temporal_fir_bound', 'spatial_continuous_band_bound', 'combined_bound'):
        value = report.get(key)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'非法精度字段: {key}')
    joint = report['joint_temporal_fir_bound']
    temporal = report['temporal_worst_nrmse']
    fir = report['fir_worst_bound']
    space = report['spatial_continuous_band_bound']
    expected = joint * (1 + space) + space
    if not (max(temporal, fir) <= joint <= temporal + fir + 1e-12
            and report['temporal_global_nrmse'] <= temporal
            and math.isclose(expected, report['combined_bound'], rel_tol=1e-9, abs_tol=1e-12)
            and expected <= 0.01 and report.get('passed') is True
            and report.get('tolerance') == 0.01 and report.get('bandwidth_hz') == 4.5e6
            and report.get('sample_rate_hz') == 7680000):
        raise ValueError('运行时组合精度预算超标或不一致')
    original = json.loads((bundle / 'fidelity_report.json').read_text())
    if not (report.get('scope') == original.get('scope') == 'prefix_before_unchanged_legacy_tail'
            and report.get('validated_time_start_s') == summary['start_time_s']
            and report.get('validated_time_end_s') == original.get('validated_time_end_s')
            and space == original.get('spatial_continuous_band_bound')):
        raise ValueError('运行时精度认证范围不一致')
    count = report.get('checked_reference_snapshots')
    holdout = report.get('non_output_reference_snapshots')
    if not (is_snapshot_count(count) and is_snapshot_count(holdout) and 0 < holdout <= count
            and count == original.get('reference_snapshots')):
        raise ValueError('真实参考数量不足或缺少非输出节点')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_runtime_fidelity(args.bundle), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
