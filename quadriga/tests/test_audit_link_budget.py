from __future__ import annotations

import hashlib
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

from quadriga.tools.audit_link_budget import LinkBudgetAuditError, audit_link_budget, _sample_trace
from quadriga.tools.create_example_bundle import write_example_bundle


class LinkBudgetAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"
        write_example_bundle(self.bundle)
        self.trace = self.root / "trace.csv"
        distances = (1_000_000.0, 1_200_000.0, 1_500_000.0)
        lines = [
            "STKTRACE2",
            "# time,x,y,z,vx,vy,vz,ax,ay,az,gnb_x,gnb_y,gnb_z,"
            "ue_x,ue_y,ue_z,dl_power_dbw,ul_power_dbw,dl_cn_db,"
            "ul_cn_db,dl_valid,ul_valid",
        ]
        for index, distance in enumerate(distances):
            power = -20.0 * math.log10(distance)
            fields = [
                index * 0.001,
                distance, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0,
                power, power, 10, 10, 1, 1,
            ]
            lines.append(",".join(str(value) for value in fields))
        self.trace.write_text("\n".join(lines) + "\n", encoding="utf-8")

        coefficients = []
        delays = []
        for _ in distances:
            coefficients.extend((math.sqrt(0.8), 0.0, 0.0, math.sqrt(0.2)))
            delays.extend((0.0, 250e-9))
        (self.bundle / "coefficients.cf32").write_bytes(struct.pack("<12f", *coefficients))
        (self.bundle / "delays.f64").write_bytes(struct.pack("<6d", *delays))
        self._write_residual((0.0, 0.0, 0.0))

        manifest_path = self.bundle / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["provenance"]["stk_trace_sha256"] = hashlib.sha256(
            self.trace.read_bytes()
        ).hexdigest()
        for name in ("coefficients", "delays"):
            path = self.bundle / manifest["files"][name]["path"]
            manifest["files"][name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_residual(self, values: tuple[float, float, float]) -> None:
        path = self.bundle / "residual_gain_db.f32"
        path.write_bytes(struct.pack("<3f", *values))
        manifest_path = self.bundle / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["residual_gain_db"]["sha256"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_nonduplicating_bundle_passes(self) -> None:
        report = audit_link_budget(self.bundle, self.trace)
        self.assertEqual(report["max_residual_gain_abs_db"], 0.0)
        self.assertAlmostEqual(report["combined_fspl_slope"], report["stk_fspl_slope"])

    def test_independent_nonuniform_geometry(self) -> None:
        rows = []
        for t in (0, 2):
            rows.append(dict(time=t, x=t**3, y=1, z=2, vx=3*t*t, vy=0, vz=0,
                             dl_valid=float(t == 0), ul_valid=1))
        values = _sample_trace(rows, [0, 0.13, 1.7, 2])
        for row in values:
            self.assertAlmostEqual(row["x"], row["time"]**3)
            self.assertAlmostEqual(row["vx"], 3*row["time"]**2)
        self.assertEqual([row["dl_valid"] for row in values], [1, 0, 0, 0])
        with self.assertRaisesRegex(LinkBudgetAuditError, "超出"):
            _sample_trace(rows, [-0.01, 2])

    def test_range_dependent_residual_is_rejected(self) -> None:
        distances = (1_000_000.0, 1_200_000.0, 1_500_000.0)
        gains = [-20.0 * math.log10(distance) for distance in distances]
        mean = sum(gains) / len(gains)
        self._write_residual(tuple(value - mean for value in gains))
        with self.assertRaisesRegex(LinkBudgetAuditError, "residual_gain_db 非零"):
            audit_link_budget(self.bundle, self.trace)


if __name__ == "__main__":
    unittest.main()
