from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from quadriga.tools.create_example_bundle import write_example_bundle
from quadriga.tools.validate_bundle import ValidationError, validate_bundle


class ValidateBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        write_example_bundle(self.root)

    def _manifest(self) -> dict:
        return json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict) -> None:
        (self.root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_valid_example(self) -> None:
        summary = validate_bundle(self.root)
        self.assertEqual(summary["snapshots"], 3)
        self.assertEqual(summary["paths"], 2)
        self.assertEqual(summary["link_direction"], "downlink")

    def _write_antenna(self, **changes: object) -> None:
        manifest = self._manifest()
        antenna = {
            "format": "NTN_ANTENNA1", "profile": "satellite_16x16_ground_omni",
            "manifest_sha256": hashlib.sha256((self.root / "manifest.json").read_bytes()).hexdigest(),
            "stk_trace_sha256": manifest["provenance"]["stk_trace_sha256"],
            "link_direction": manifest["radio"]["link_direction"],
            "center_frequency_hz": manifest["radio"]["center_frequency_hz"],
            "satellite_rows": 16, "satellite_columns": 16, "spacing_wavelengths": 0.5,
            "satellite_rf_ports": 1, "ground_rf_ports": 1, "absolute_array_gain_source": "STKTRACE2",
        }
        antenna.update(changes)
        (self.root / "antenna.json").write_text(json.dumps(antenna), encoding="utf-8")

    def test_array_sidecar_keeps_v1_manifest_compatible(self) -> None:
        self._write_antenna()
        self.assertEqual(validate_bundle(self.root)["tx_antennas"], 1)

    def test_sidecar_from_other_bundle_is_rejected(self) -> None:
        self._write_antenna(manifest_sha256="0" * 64)
        with self.assertRaisesRegex(ValidationError, "antenna manifest SHA256"):
            validate_bundle(self.root)

    def test_sidecar_cannot_turn_array_elements_into_rf_ports(self) -> None:
        self._write_antenna(satellite_rf_ports=256)
        with self.assertRaisesRegex(ValidationError, "RF 端口"):
            validate_bundle(self.root)

    def test_invalid_link_direction_is_rejected(self) -> None:
        manifest = self._manifest()
        manifest["radio"]["link_direction"] = "sideways"
        self._write_manifest(manifest)
        with self.assertRaisesRegex(ValidationError, "link_direction"):
            validate_bundle(self.root)

    def test_checksum_mismatch_is_rejected(self) -> None:
        path = self.root / "coefficients.cf32"
        path.write_bytes(path.read_bytes()[:-1] + b"\x00")
        with self.assertRaisesRegex(ValidationError, "SHA256"):
            validate_bundle(self.root)

    def test_non_monotonic_time_is_rejected(self) -> None:
        payload = struct.pack("<3d", 0.0, 0.002, 0.001)
        path = self.root / "times.f64"
        path.write_bytes(payload)
        manifest = self._manifest()
        manifest["files"]["times"]["sha256"] = hashlib.sha256(payload).hexdigest()
        self._write_manifest(manifest)
        with self.assertRaisesRegex(ValidationError, "严格递增"):
            validate_bundle(self.root)

    def test_parent_path_is_rejected(self) -> None:
        manifest = self._manifest()
        manifest["files"]["times"]["path"] = "../times.f64"
        self._write_manifest(manifest)
        with self.assertRaisesRegex(ValidationError, "越出 bundle"):
            validate_bundle(self.root)

    def test_nonzero_mean_residual_gain_is_rejected(self) -> None:
        payload = struct.pack("<3f", 1.0, 1.0, 1.0)
        path = self.root / "residual_gain_db.f32"
        path.write_bytes(payload)
        manifest = self._manifest()
        manifest["files"]["residual_gain_db"]["sha256"] = hashlib.sha256(payload).hexdigest()
        self._write_manifest(manifest)
        with self.assertRaisesRegex(ValidationError, "均值不为零"):
            validate_bundle(self.root)


if __name__ == "__main__":
    unittest.main()
