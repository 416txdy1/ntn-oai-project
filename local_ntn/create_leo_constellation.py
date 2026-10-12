"""Create an isolated STK LEO constellation from the verified OAI scene.

The source scene is never overwritten.  Each imported satellite keeps the
same endpoint models as the source satellite, while its embedded TLE is
phase-shifted by plane and in-plane anomaly.  The resulting scenario is
intended for the STK exporter, which performs visibility-based satellite
selection later.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

from agi.stk12.stkdesktop import STKDesktop


BASE_NAME = "QIANFAN-166_69383"
BASE_RAAN_DEG = 357.8383
DEFAULT_BASE = Path(
    r"C:/Users/WSZ/.codex/visualizations/2026/07/24/"
    r"019f9209-937f-7c50-8691-be0521d4eebc/STK_PhasedArray_20260910/modified/"
    r"Scenario1.sc"
)
DEFAULT_OUT = Path(
    r"C:/Users/WSZ/.codex/visualizations/2026/07/24/"
    r"019f9209-937f-7c50-8691-be0521d4eebc/STK_LEO_Constellation_20260923_train_v2"
)


def tle_checksum(line: str) -> str:
    """Return a TLE line with a recomputed final checksum digit."""
    body = line.rstrip()[:68].ljust(68)
    total = sum(int(ch) for ch in body if ch.isdigit())
    total += body.count("-")
    return body + str(total % 10)


def replace_tle_fields(line: str, raan_deg: float, mean_anomaly_deg: float) -> str:
    """Change RAAN and mean anomaly in a canonical, stripped line-2 TLE."""
    raw = line.strip()
    if not raw.startswith("2 ") or len(raw) < 69:
        raise ValueError(f"unexpected TLE line 2: {line!r}")
    # Keep the full line while replacing the two fixed-width TLE fields.
    raw = (raw[:17] + f"{raan_deg % 360:8.4f}" + raw[25:43]
           + f"{mean_anomaly_deg % 360:8.4f}" + raw[51:])
    return tle_checksum(raw)


def satellite_text(source: Path, name: str, raan_deg: float, mean_anomaly_deg: float) -> str:
    lines = source.read_text(encoding="utf-8").splitlines()
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == f"Name\t\t {BASE_NAME}":
            line = line.replace(BASE_NAME, name)
        elif stripped == "CommonName\t\t QIANFAN-166":
            line = line.replace("QIANFAN-166", name)
        elif stripped.startswith("2 ") and len(stripped) >= 69:
            line = replace_tle_fields(stripped, raan_deg, mean_anomaly_deg)
        result.append(line)
    return "\n".join(result) + "\n"


def find_satellite_file(base_scenario: Path) -> Path:
    candidate = base_scenario.parent / f"{BASE_NAME}.sa"
    if not candidate.exists():
        raise FileNotFoundError(f"base satellite file not found: {candidate}")
    return candidate


def build(args: argparse.Namespace) -> dict:
    if args.count != args.planes * args.per_plane:
        raise ValueError("count must equal planes * per_plane")
    if args.count < 2 or args.planes < 1 or args.per_plane < 1:
        raise ValueError("count, planes and per_plane must be positive")
    base_scenario = args.base_scenario.resolve()
    source_sat = find_satellite_file(base_scenario)
    names = [
        f"OAI_LEO_P{plane:02d}_S{slot:02d}"
        for plane in range(1, args.planes + 1)
        for slot in range(1, args.per_plane + 1)
    ]
    offsets = []
    for plane in range(args.planes):
        raan = args.raan_offset_deg + plane * (360.0 / args.planes)
        for slot in range(args.per_plane):
            anomaly = args.phase_offset_deg + slot * args.in_plane_spacing_deg + plane * args.plane_phase_deg
            offsets.append((raan, anomaly))

    if args.dry_run:
        return {
            "base_scenario": str(base_scenario),
            "output_dir": str(args.output_dir.resolve()),
            "satellites": [
                {"name": n, "plane": i // args.per_plane + 1, "slot": i % args.per_plane + 1,
                 "raan_deg": r, "mean_anomaly_deg": m}
                for i, (n, (r, m)) in enumerate(zip(names, offsets))
            ],
        }

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_scenario = out_dir / args.scenario_name
    if out_scenario.exists():
        raise FileExistsError(f"refusing to overwrite existing scenario: {out_scenario}")

    # The active STK instance may be empty or may hold a prior unsaved copy.
    # Load the supplied source explicitly, then SaveAs into the new directory.
    desktop = STKDesktop.AttachToApplication()
    root = desktop.Root
    if root.CurrentScenario is not None:
        root.CloseScenario()
    root.LoadScenario(str(base_scenario))
    root.SaveAs(str(out_scenario))

    scenario = root.CurrentScenario
    imported = []
    for idx, (name, (raan, anomaly)) in enumerate(zip(names, offsets)):
        sat_file = out_dir / f"{name}.sa"
        sat_file.write_text(satellite_text(source_sat, name, raan, anomaly), encoding="utf-8")
        obj = scenario.Children.ImportObject(str(sat_file))
        imported.append({
            "name": name,
            "path": obj.Path,
            "plane": idx // args.per_plane + 1,
            "slot": idx % args.per_plane + 1,
            "raan_deg": raan % 360.0,
            "mean_anomaly_deg": anomaly % 360.0,
        })

    # A ground phased-array beam can point at only one satellite at a time.
    # The constellation baseline therefore uses isotropic endpoint models so
    # STK can evaluate every candidate link consistently; the original
    # phased-array scene remains untouched for directional experiments.
    endpoint_paths = [
        "Place/Beijing/Transmitter/OAI_gNB_DL_Tx",
        "Place/Beijing/Receiver/OAI_gNB_UL_Rx",
        "Place/OAI_UE/Transmitter/OAI_UE_UL_Tx",
        "Place/OAI_UE/Receiver/OAI_UE_DL_Rx",
    ]
    for name in names:
        endpoint_paths.extend([
            f"Satellite/{name}/Receiver/OAI_SAT_DL_Rx",
            f"Satellite/{name}/Transmitter/OAI_SAT_UL_Tx",
            f"Satellite/{name}/Receiver/OAI_SAT_UL_Rx",
            f"Satellite/{name}/Transmitter/OAI_SAT_DL_Tx",
        ])
    for path in endpoint_paths:
        root.GetObjectFromPath(path).Model.AntennaControl.SetEmbeddedModel(args.antenna_model)

    # The original source satellite remains in the copied scenario so the
    # user can compare against it; it is not part of the generated manifest.
    manifest = {
        "scenario": str(out_scenario),
        "source_scenario": str(base_scenario),
        "source_satellite": BASE_NAME,
        "count": len(imported),
        "planes": args.planes,
        "per_plane": args.per_plane,
        "acquire_elevation_deg": args.acquire_elevation_deg,
        "release_elevation_deg": args.release_elevation_deg,
        "antenna_model": args.antenna_model,
        "satellites": imported,
        "selection_policy": "highest elevation; retain current above release mask",
    }
    (out_dir / "constellation_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    root.SaveAs(str(out_scenario))
    return manifest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-scenario", type=Path, default=DEFAULT_BASE)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--scenario-name", default="OAI_LEO_Constellation.sc")
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--planes", type=int, default=1)
    p.add_argument("--per-plane", type=int, default=6)
    p.add_argument("--raan-offset-deg", type=float, default=BASE_RAAN_DEG)
    p.add_argument("--phase-offset-deg", type=float, default=0.0)
    p.add_argument("--in-plane-spacing-deg", type=float, default=30.0)
    p.add_argument("--plane-phase-deg", type=float, default=10.0)
    p.add_argument("--acquire-elevation-deg", type=float, default=10.0)
    p.add_argument("--release-elevation-deg", type=float, default=5.0)
    p.add_argument("--antenna-model", choices=["Isotropic", "Phased Array"], default="Isotropic")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    result = build(args)
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
