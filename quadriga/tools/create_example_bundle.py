"""生成确定性的 QDCHANNEL1 双径 SISO 示例。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


def _write(path: Path, payload: bytes, dtype: str, count: int) -> dict[str, object]:
    path.write_bytes(payload)
    return {
        "path": path.name,
        "dtype": dtype,
        "count": count,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def write_example_bundle(root: Path) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    times = [0.0, 0.001, 0.002]
    delays = []
    coefficients = []
    residual_gain_db = [-0.25, 0.0, 0.25]
    for snapshot in range(len(times)):
        phase = snapshot * 0.2
        first = math.sqrt(0.8) * complex(math.cos(phase), math.sin(phase))
        second = math.sqrt(0.2) * complex(math.cos(-phase), math.sin(-phase))
        delays.extend([0.0, 250e-9 + snapshot * 5e-9])
        coefficients.extend([first.real, first.imag, second.real, second.imag])

    files = {
        "times": _write(root / "times.f64", struct.pack("<3d", *times), "float64", 3),
        "delays": _write(root / "delays.f64", struct.pack("<6d", *delays), "float64", 6),
        "coefficients": _write(
            root / "coefficients.cf32",
            struct.pack("<12f", *coefficients),
            "complex64_interleaved",
            6,
        ),
        "residual_gain_db": _write(
            root / "residual_gain_db.f32",
            struct.pack("<3f", *residual_gain_db),
            "float32",
            3,
        ),
    }
    manifest = {
        "format": "QDCHANNEL1",
        "schema_version": 1,
        "byte_order": "little",
        "axes": ["snapshot", "rx", "tx", "path"],
        "dimensions": {"snapshots": 3, "rx_antennas": 1, "tx_antennas": 1, "paths": 2},
        "radio": {"center_frequency_hz": 2_000_000_000.0, "link_direction": "downlink"},
        "time": {
            "coordinate": "stk_trace_seconds",
            "interpolation": "linear_complex_and_delay",
            "out_of_range": "mute",
        },
        "composition": {
            "bulk_delay_source": "STKTRACE2",
            "bulk_doppler_source": "STKTRACE2",
            "absolute_gain_source": "STKTRACE2",
            "quadriga_delay": "relative_excess_seconds",
            "quadriga_coefficients": "unit_snapshot_link_power",
            "quadriga_large_scale_gain": "zero_mean_residual_db",
        },
        "provenance": {
            "quadriga_version": "2.8.1",
            "scenario": "deterministic_siso_two_path_example",
            "random_seed": 20260924,
            "stk_trace_sha256": "0" * 64,
        },
        "files": files,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 QDCHANNEL1 示例 bundle")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(write_example_bundle(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
