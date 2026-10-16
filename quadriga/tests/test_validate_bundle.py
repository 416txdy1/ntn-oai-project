from __future__ import annotations

import hashlib
import json
import struct
import shutil
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

    def test_runtime_fidelity_rejects_stale_or_false_reports(self) -> None:
        from quadriga.tools.validate_runtime_fidelity import validate_runtime_fidelity
        summary = validate_bundle(self.root)
        report = dict(bandwidth_hz=4.5e6, sample_rate_hz=7680000, tolerance=0.01,
                      temporal_global_nrmse=0.001, temporal_worst_nrmse=0.003,
                      fir_worst_bound=0.002, joint_temporal_fir_bound=0.004,
                      spatial_continuous_band_bound=0.0001, combined_bound=0.0041004,
                      checked_reference_snapshots=11, non_output_reference_snapshots=8,
                      validated_time_start_s=summary['start_time_s'], validated_time_end_s=summary['end_time_s'],
                      scope='prefix_before_unchanged_legacy_tail', passed=True,
                      bundle_manifest_sha256=hashlib.sha256((self.root/'manifest.json').read_bytes()).hexdigest())
        original = dict(report, reference_snapshots=11)
        (self.root/'fidelity_report.json').write_text(json.dumps(original))
        path = self.root/'runtime_fidelity_report.json'
        path.write_text(json.dumps(report))
        self.assertTrue(validate_runtime_fidelity(self.root)['passed'])
        for key, value in (('bundle_manifest_sha256', '0'*64), ('combined_bound', 0.001),
                           ('fir_worst_bound', float('nan')), ('non_output_reference_snapshots', 0),
                           ('checked_reference_snapshots', 10), ('sample_rate_hz', 30720000),
                           ('validated_time_end_s', summary['end_time_s']+1), ('passed', False)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                path.write_text(json.dumps(dict(report, **{key:value})))
                validate_runtime_fidelity(self.root)

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

    def test_subarray_mapping_and_power_guards(self) -> None:
        source = Path(__file__).resolve().parents[2] / 'examples/fdd-miso4-subarray/downlink'
        target = self.root / 'subarrays'
        shutil.copytree(source, target)
        self.assertEqual(validate_bundle(target)['tx_antennas'], 4)
        path = target / 'antenna.json'
        original = json.loads(path.read_text())
        uplink = json.loads((source.parent/'uplink/antenna.json').read_text())
        self.assertEqual(original['element_spacing_m'], uplink['element_spacing_m'])
        self.assertEqual(original['array_reference_frequency_hz'], uplink['array_reference_frequency_hz'])
        self.assertNotEqual(original['spacing_wavelengths_at_carrier'], uplink['spacing_wavelengths_at_carrier'])
        bad_map = original['element_port_map'].copy()
        bad_map[0] = 2
        for field, value, error in (
            ('element_port_map', bad_map, '子阵映射'),
            ('subarray_weight_norm2', 4, '单位功率'),
            ('max_subarray_delay_span_s', -1, '时延跨度'),
            ('subarray_rows', 16, '子阵几何'),
            ('element_spacing_m', 1, '物理间距'),
        ):
            with self.subTest(field=field):
                path.write_text(json.dumps(dict(original, **{field:value})))
                with self.assertRaisesRegex(ValidationError, error):
                    validate_bundle(target)

    def test_false_fidelity_claims_are_rejected(self) -> None:
        from quadriga.tools.validate_bundle import _validate_fidelity
        report = dict(tolerance=0.01, bandwidth_hz=4.5e6, temporal_worst_nrmse=0.003,
                      temporal_global_nrmse=0.001, spatial_continuous_band_bound=0.0001,
                      combined_bound_at_reference_times=0.0031003,
                      minimum_interval_s=0.001, maximum_interval_s=0.002,
                      output_snapshots=3, reference_snapshots=11)
        antenna = dict(wideband_error_bound=0.0001, validated_bandwidth_hz=4.5e6)
        times = (0.0, 0.001, 0.003)
        _validate_fidelity(report, antenna, times)
        prefix = dict(report, scope="prefix_before_unchanged_legacy_tail", validated_time_start_s=0.0,
                      validated_time_end_s=0.001, unchanged_tail_snapshots=1)
        _validate_fidelity(prefix, antenna, times)
        with self.assertRaisesRegex(ValidationError, "尾部"):
            _validate_fidelity(dict(prefix, unchanged_tail_snapshots=0), antenna, times)
        for key, value in (("temporal_worst_nrmse", 0.1), ("tolerance", 0.02),
                           ("reference_snapshots", 3), ("maximum_interval_s", 1),
                           ("combined_bound_at_reference_times", float("nan"))):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                _validate_fidelity(dict(report, **{key: value}), antenna, times)

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
