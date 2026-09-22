"""Print geometry and first-order RF metrics from the active STK scenario.

This script is read-only: it does not create or modify STK objects.  Values
labelled ``stk`` come directly from STK data providers.  Values labelled
``pred`` are calculated from the STK range/range-rate and configured carrier
frequencies.
"""

from __future__ import annotations

import argparse
import json
import math
import time

from agi.stk12.stkdesktop import STKDesktop


C_MPS = 299_792_458.0


def configure_units(root) -> None:
    for dimension, unit in (
        ("DateFormat", "EpSec"),
        ("DistanceUnit", "m"),
        ("TimeUnit", "sec"),
        ("AngleUnit", "deg"),
    ):
        try:
            root.UnitPreferences.SetCurrentUnit(dimension, unit)
        except Exception:
            # Some STK installations keep the angle dimension under a
            # different preference name.  AER normally defaults to degrees.
            if dimension != "AngleUnit":
                raise


def current_epsec(root) -> float:
    value = root.CurrentTime
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(root.ConversionUtility.ConvertDate("UTCG", str(value), "EpSec"))


def time_provider(obj, paths):
    errors = []
    for path in paths:
        try:
            return obj.DataProviders.GetDataPrvTimeVarFromPath(path)
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    raise RuntimeError("no compatible STK provider: " + "; ".join(errors))


def values(provider, epoch_s: float, names):
    result = provider.ExecSingleElements(epoch_s, list(names))
    return tuple(float(result.DataSets.GetDataSetByName(name).GetValues()[0]) for name in names)


def aer_provider(site, satellite):
    access = site.GetAccessToObject(satellite)
    access.ComputeAccess()
    provider = access.DataProviders.GetDataPrvTimeVarFromPath("AER Data//Default")
    return access, provider


def aer_at(provider, epoch_s: float):
    azimuth_deg, elevation_deg, range_m, range_rate_mps, path_delay_s = values(
        provider,
        epoch_s,
        ("Azimuth", "Elevation", "Range", "RangeRate", "Path Delay"),
    )
    return {
        "azimuth_deg_stk": azimuth_deg,
        "elevation_deg_stk": elevation_deg,
        "range_m_stk": range_m,
        "range_rate_mps_stk": range_rate_mps,
        "path_delay_ms_stk": path_delay_s * 1000.0,
    }


def fspl_db(range_m: float, frequency_hz: float) -> float:
    return 20.0 * math.log10(4.0 * math.pi * range_m * frequency_hz / C_MPS)


def doppler_hz(range_rate_mps: float, frequency_hz: float) -> float:
    # Positive range rate means increasing separation and therefore a lower
    # received frequency.
    return -range_rate_mps / C_MPS * frequency_hz


def main() -> int:
    parser = argparse.ArgumentParser(description="Print STK API geometry/link metrics")
    parser.add_argument("--satellite", default="*/Satellite/Satellite1")
    parser.add_argument("--gnb", default="*/Facility/gNB")
    parser.add_argument("--ue", default="*/Facility/UE")
    parser.add_argument("--dl-frequency-hz", type=float, default=2_488_400_000.0)
    parser.add_argument("--ul-frequency-hz", type=float, default=1_614_900_000.0)
    parser.add_argument("--rate-hz", type=float, default=1.0)
    parser.add_argument("--count", type=int, default=0, help="0 means run until Ctrl-C")
    args = parser.parse_args()
    if args.rate_hz <= 0.0 or args.count < 0:
        parser.error("--rate-hz must be positive and --count non-negative")

    desktop = STKDesktop.AttachToApplication()
    root = desktop.Root
    configure_units(root)
    satellite = root.GetObjectFromPath(args.satellite)
    gnb = root.GetObjectFromPath(args.gnb)
    ue = root.GetObjectFromPath(args.ue)

    position_provider = time_provider(
        satellite, ("Cartesian Position//Fixed", "Cartesian Position/Fixed")
    )
    velocity_provider = time_provider(
        satellite, ("Cartesian Velocity//Fixed", "Cartesian Velocity/Fixed")
    )
    lla_provider = time_provider(satellite, ("LLA State//Fixed", "LLA State/Fixed"))
    _, gnb_aer_provider = aer_provider(gnb, satellite)
    _, ue_aer_provider = aer_provider(ue, satellite)

    period = 1.0 / args.rate_hz
    emitted = 0
    try:
        while args.count == 0 or emitted < args.count:
            started = time.monotonic()
            epoch_s = current_epsec(root)
            sat_position = values(position_provider, epoch_s, ("x", "y", "z"))
            sat_velocity = values(velocity_provider, epoch_s, ("x", "y", "z"))
            _, _, altitude_m = values(lla_provider, epoch_s, ("Lat", "Lon", "Alt"))
            gnb_link = aer_at(gnb_aer_provider, epoch_s)
            ue_link = aer_at(ue_aer_provider, epoch_s)

            for link in (gnb_link, ue_link):
                link["fspl_dl_db_pred"] = fspl_db(link["range_m_stk"], args.dl_frequency_hz)
                link["fspl_ul_db_pred"] = fspl_db(link["range_m_stk"], args.ul_frequency_hz)
                link["doppler_dl_hz_pred"] = doppler_hz(link["range_rate_mps_stk"], args.dl_frequency_hz)
                link["doppler_ul_hz_pred"] = doppler_hz(link["range_rate_mps_stk"], args.ul_frequency_hz)

            output = {
                "source": "STK_API",
                "stk_time_s": epoch_s,
                "satellite": {
                    "position_ecef_m": sat_position,
                    "velocity_ecef_mps": sat_velocity,
                    "speed_mps": math.sqrt(sum(component * component for component in sat_velocity)),
                    "altitude_m_stk": altitude_m,
                },
                "ue_to_satellite": ue_link,
                "gnb_to_satellite": gnb_link,
                "transparent_total": {
                    "range_m_stk": ue_link["range_m_stk"] + gnb_link["range_m_stk"],
                    "path_delay_ms_stk": ue_link["path_delay_ms_stk"] + gnb_link["path_delay_ms_stk"],
                    "fspl_dl_db_pred": ue_link["fspl_dl_db_pred"] + gnb_link["fspl_dl_db_pred"],
                    "fspl_ul_db_pred": ue_link["fspl_ul_db_pred"] + gnb_link["fspl_ul_db_pred"],
                    "doppler_dl_hz_pred": ue_link["doppler_dl_hz_pred"] + gnb_link["doppler_dl_hz_pred"],
                    "doppler_ul_hz_pred": ue_link["doppler_ul_hz_pred"] + gnb_link["doppler_ul_hz_pred"],
                },
            }
            print(json.dumps(output, ensure_ascii=False), flush=True)
            emitted += 1
            remaining = period - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
