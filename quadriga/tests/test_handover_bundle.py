"""Bidirectional handover completion and runtime launch boundaries; no live modems."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local_ntn"))
import preflight
from runtime_config import resolve_runtime

SOURCE_FILES = (
    "quadriga/matlab/export_handover_fdd.m",
    "quadriga/matlab/export_stk_to_qdchannel.m",
    "quadriga/matlab/normalize_qd_channel.m",
    "quadriga/matlab/write_qdchannel1.m",
    "quadriga/matlab/read_stktrace2.m",
    "quadriga/matlab/ecef_to_enu_track.m",
    "quadriga/matlab/sha256_file.m",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class HandoverBundleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="handover-bundle-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "examples/handover"
        self.output.mkdir(parents=True)
        (self.root / "local_ntn").mkdir()
        self.trace = self.root / "local_ntn/trace.csv"
        shutil.copyfile(ROOT / "examples/fdd-pass/trace.csv", self.trace)
        self.rows = preflight.read_trace(self.trace)
        self.schedule = self.root / "local_ntn/schedule.csv"
        with self.schedule.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(("time", "satellite_id", "elevation_deg", "visible", "switched",
                             "handover_phase", "previous_satellite_id", "next_satellite_id"))
            for row in self.rows:
                writer.writerow((row[0], "SAT_A", 20, 1, 0, "steady", "", ""))
        self.bundles = {}
        for direction in ("downlink", "uplink"):
            self.bundles[direction] = self.output / direction
            shutil.copytree(ROOT / "examples/fdd-pass" / direction, self.bundles[direction])
        descriptor = lambda path: {"sha256": sha(path), "rows": len(self.rows),
                                  "start_time_s": self.rows[0][0], "end_time_s": self.rows[-1][0]}
        self.provenance = {
            "format": "NTN_HANDOVER_FDD1", "schema_version": 1, "state": "complete",
            "inputs": {"trace": descriptor(self.trace), "schedule": descriptor(self.schedule)},
            "tools": {"matlab_version": "9.13.0.2049777 (R2022b)", "quadriga_version": "2.8.1-0",
                      "scenario": "QuaDRiGa_NTN_Rural_LOS", "random_seed": 20260925},
            "source": {"commit": "b5e6264a6c8a888a8bfcf5bfeca7c9fb22f691c0",
                       "quadriga_archive_sha256": json.loads((ROOT / "vendor/checksums.json").read_text())["quadriga-source.tar.gz"],
                       "files": {name: sha(ROOT / name) if (ROOT / name).is_file() else "0" * 64
                                 for name in SOURCE_FILES}},
            "warnings": {
                "events": [], "trace_time_step_s": self.rows[1][0] - self.rows[0][0],
                "max_satellite_track_speed_m_s": max(
                    math.dist(a[1:4], b[1:4]) / (b[0] - a[0]) for a, b in zip(self.rows, self.rows[1:])),
                "center_frequency_hz": {"downlink": 2488400000, "uplink": 1614900000},
            },
            "bundles": {},
        }
        for direction, bundle in self.bundles.items():
            manifest = json.loads((bundle / "manifest.json").read_text())
            self.provenance["bundles"][direction] = {
                "path": direction, "manifest_sha256": sha(bundle / "manifest.json"),
                "data_sha256": {name: spec["sha256"] for name, spec in manifest["files"].items()},
            }
        self.save()

    def save(self):
        (self.output / "provenance.json").write_text(json.dumps(self.provenance), encoding="utf-8")

    def check(self):
        guard = getattr(preflight, "check_handover_bundles", None)
        self.assertTrue(callable(guard), "missing integrated bidirectional completion guard")
        return guard(self.bundles["downlink"], self.bundles["uplink"], self.trace, self.schedule)

    def test_complete_bidirectional_export_passes_full_audit(self):
        result = self.check()
        self.assertEqual(result["trace_sha256"], sha(self.trace))
        self.assertEqual(result["schedule_sha256"], sha(self.schedule))
        for direction in self.bundles:
            self.assertEqual(result["audits"][direction]["snapshots"], len(self.rows))
            self.assertEqual(result["audits"][direction]["max_residual_gain_abs_db"], 0.0)

    def test_partial_export_rejected(self):
        (self.output / "provenance.json").unlink()
        with self.assertRaisesRegex(ValueError, "completion"):
            self.check()

    def test_only_downlink_export_rejected(self):
        shutil.rmtree(self.bundles["uplink"])
        with self.assertRaises((ValueError, OSError)):
            self.check()

    def test_incomplete_state_rejected(self):
        self.provenance["state"] = "exporting"
        self.save()
        with self.assertRaisesRegex(ValueError, "complete"):
            self.check()

    def test_slice_hash_mismatch(self):
        # A shorter trace with a copied long provenance must not be accepted.
        lines = self.trace.read_bytes().splitlines(keepends=True)
        self.trace.write_bytes(b"".join(lines[:73]))
        with self.assertRaisesRegex(ValueError, "trace.*SHA256"):
            self.check()

    def test_schedule_hash_mismatch(self):
        self.schedule.write_text(self.schedule.read_text().replace("SAT_A", "SAT_B"))
        with self.assertRaisesRegex(ValueError, "schedule.*SHA256"):
            self.check()

    def test_schedule_time_mismatch_even_with_updated_hash(self):
        lines = self.schedule.read_text().splitlines()
        fields = lines[2].split(",")
        fields[0] = str(float(fields[0]) + .25)
        lines[2] = ",".join(fields)
        self.schedule.write_text("\n".join(lines) + "\n")
        self.provenance["inputs"]["schedule"]["sha256"] = sha(self.schedule)
        self.save()
        with self.assertRaisesRegex(ValueError, "schedule.*time"):
            self.check()

    def test_prepare_phase_is_preserved_as_valid_schedule_input(self):
        self.schedule.write_text(self.schedule.read_text().replace(',steady,', ',prepare,', 1))
        self.provenance['inputs']['schedule']['sha256'] = sha(self.schedule)
        self.save()
        self.assertEqual(self.check()['schedule_sha256'], sha(self.schedule))
    def test_warning_provenance_is_required_without_weakening_audit(self):
        self.provenance.pop('warnings')
        self.save()
        with self.assertRaisesRegex(ValueError, 'warning provenance'):
            self.check()
    def test_manifest_hash_mismatch(self):
        path = self.bundles["uplink"] / "manifest.json"
        path.write_text(path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "manifest.*SHA256"):
            self.check()

    def test_binary_corruption_rejected(self):
        path = self.bundles["downlink"] / "coefficients.cf32"
        data = bytearray(path.read_bytes())
        data[0] ^= 1
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "SHA256"):
            self.check()

    def test_wrong_direction_rejected_after_rehashed_manifest(self):
        path = self.bundles["uplink"] / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["radio"]["link_direction"] = "downlink"
        path.write_text(json.dumps(manifest))
        self.provenance["bundles"]["uplink"]["manifest_sha256"] = sha(path)
        self.save()
        with self.assertRaisesRegex(ValueError, "方向"):
            self.check()

    def test_wrong_frequency_rejected_after_rehashed_manifest(self):
        path = self.bundles["uplink"] / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["radio"]["center_frequency_hz"] = 2488400000
        path.write_text(json.dumps(manifest))
        self.provenance["bundles"]["uplink"]["manifest_sha256"] = sha(path)
        self.save()
        with self.assertRaisesRegex(ValueError, "载频"):
            self.check()

    def test_bundles_from_different_exports_rejected(self):
        other = self.root / "examples/handover/firsthandover"
        other.mkdir()
        shutil.move(str(self.bundles["uplink"]), str(other / "uplink"))
        self.bundles["uplink"] = other / "uplink"
        with self.assertRaisesRegex(ValueError, "same export"):
            self.check()

    def test_sidecar_data_hash_mismatch(self):
        self.provenance["bundles"]["downlink"]["data_sha256"]["times"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "data.*SHA256"):
            self.check()

    def runtime(self, profile="integrated-handover"):
        config = resolve_runtime(self.root, profile, "fixture",
                                 {"OAI_STK_TRACE": str(self.trace), "OAI_STK_SCHEDULE": str(self.schedule)})
        config.build_dir.mkdir(parents=True, exist_ok=True)
        for name in ("nr-softmodem", "nr-uesoftmodem", "librfsimulator.so",
                     "libparams_libconfig.so", "libldpc.so", "libdfts.so"):
            path = config.build_dir / name
            path.write_bytes(b"QDCHANNEL1")
            path.chmod(0o755)
        config.private_dir.mkdir(parents=True, exist_ok=True)
        xyz = self.rows[0][13:16]
        config.ue_config.write_text("position0 = { " +
                                   " ".join(f"{axis} = {value};" for axis, value in zip("xyz", xyz)) + " };")
        return config

    def test_integrated_real_preflight_rejects_partial_completion(self):
        config = self.runtime()
        (self.output / "provenance.json").unlink()
        with patch.object(preflight, "check_template"), self.assertRaisesRegex(ValueError, "completion"):
            preflight.preflight(1, {}, config)

    def test_legacy_preflight_remains_stk_only_without_completion(self):
        config = self.runtime("legacy-handover")
        (self.output / "provenance.json").unlink()
        with patch.object(preflight, "check_template"):
            result = preflight.preflight(1, {}, config)
        self.assertEqual(result["mode"], "STK-only")

    def test_existing_zky_bundle_requires_no_sidecar(self):
        result = preflight.check_bundle(self.bundles["downlink"], self.trace, "downlink", 2488400000)
        self.assertEqual(result["snapshots"], len(self.rows))


class RealHandoverDataTest(unittest.TestCase):
    def test_committed_long_and_short_bidirectional_inputs(self):
        for subdir, suffix, count in (("", "seamless", 621), ("firsthandover", "firsthandover", 71)):
            with self.subTest(suffix=suffix):
                output = ROOT / "examples/handover" / subdir
                if not (output / "provenance.json").is_file():
                    self.skipTest("real exports are audited before being copied into examples/handover")
                trace = ROOT / f"local_ntn/stk_trace_{suffix}.csv"
                schedule = ROOT / f"local_ntn/satellite_schedule_{suffix}.csv"
                result = preflight.check_handover_bundles(output / "downlink", output / "uplink", trace, schedule)
                self.assertEqual(result["trace_sha256"], sha(trace))
                self.assertEqual(result["schedule_sha256"], sha(schedule))
                for direction, frequency in (("downlink", 2488400000), ("uplink", 1614900000)):
                    manifest = json.loads((output / direction / "manifest.json").read_text())
                    self.assertEqual(manifest["dimensions"]["snapshots"], count)
                    self.assertEqual(manifest["radio"], {"center_frequency_hz": frequency, "link_direction": direction})
                    self.assertEqual(manifest["provenance"]["stk_trace_sha256"], sha(trace))
                    self.assertLessEqual(result["audits"][direction]["max_tap_power_error"], 2e-5)


if __name__ == "__main__":
    unittest.main()