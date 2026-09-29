"""Export an OAI STKTRACE2 trace with deterministic satellite handovers."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from bisect import bisect_right
from pathlib import Path

from agi.stk12.stkdesktop import STKDesktop

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configure_stk_phased_array import GNB, UE  # noqa: E402
from local_ntn.handover_blend import blend_alpha, interpolate_state  # noqa: E402
from local_ntn.satellite_schedule import select_satellite  # noqa: E402


LINKS = [("DL feeder", 0, 4), ("DL service", 7, 3),
         ("UL service", 2, 6), ("UL feeder", 5, 1)]
FIELDS = ["Time", "Carrier Power at Rcvr Input", "C/N", "Xmtr Gain", "Rcvr Gain"]


def values(dataset, name):
    return dataset.DataSets.GetDataSetByName(name).GetValues()


def columns(provider, start, stop, step, names):
    ds = provider.ExecElements(start, stop, step, names)
    return {name: list(map(float, values(ds, name))) for name in names}


def state_grid(sat, start, stop, step):
    states = []
    for name in ("Cartesian Position", "Cartesian Velocity", "Cartesian Acceleration"):
        provider = sat.DataProviders.GetDataPrvTimeVarFromPath(name + "//Fixed")
        states.append(columns(provider, start, stop, step, ["Time", "x", "y", "z"]))
    times = states[0]["Time"]
    if any(s["Time"] != times for s in states):
        raise RuntimeError("state time grids differ")
    return times, states


def intervals(access):
    access.ComputeAccess()
    raw = access.ComputedAccessIntervalTimes
    return [(float(raw.GetInterval(i)[0]), float(raw.GetInterval(i)[1]))
            for i in range(raw.Count)]


def visibility_map(ground, sat, start, stop, step):
    """Return epoch -> positive ground elevation for access epochs."""
    access = ground.GetAccessToObject(sat)
    ints = intervals(access)
    if not ints:
        return {}, []
    provider = access.DataProviders.Item("AER Data").Group.Item("Default")
    try:
        data = columns(provider, start, stop, step, ["Time", "Elevation"])
    except Exception:
        # The requested export window may not intersect this satellite's
        # access intervals even though it has access elsewhere in the day.
        return {}, ints
    return ({round(t, 6): e for t, e in zip(data["Time"], data["Elevation"])}, ints)


def in_intervals(t, ints):
    return any(a - 1e-6 <= t <= b + 1e-6 for a, b in ints)


def endpoints(gnb, ue, sat_name):
    sat = f"Satellite/{sat_name}"
    return [
        gnb + "/Transmitter/OAI_gNB_DL_Tx",
        gnb + "/Receiver/OAI_gNB_UL_Rx",
        ue + "/Transmitter/OAI_UE_UL_Tx",
        ue + "/Receiver/OAI_UE_DL_Rx",
        sat + "/Receiver/OAI_SAT_DL_Rx",
        sat + "/Transmitter/OAI_SAT_UL_Tx",
        sat + "/Receiver/OAI_SAT_UL_Rx",
        sat + "/Transmitter/OAI_SAT_DL_Tx",
    ]


def link_budgets(objects, start, stop, step):
    budgets = []
    for link_name, tx, rx in LINKS:
        access = objects[tx].GetAccessToObject(objects[rx])
        access.ComputeAccess()
        provider = access.DataProviders.GetDataPrvTimeVarFromPath("Link Information")
        try:
            data = columns(provider, start, stop, step, FIELDS)
        except Exception:
            data = {field: [] for field in FIELDS}
        by_time = {
            round(t, 6): {field: data[field][i] for field in FIELDS[1:]}
            for i, t in enumerate(data["Time"])
        }
        budgets.append((link_name, by_time))
    return budgets


def hop(budget, t):
    d = budget.get(round(t, 6))
    valid = d is not None and all(math.isfinite(v) and v > -900 for v in d.values())
    return (d if valid else {"Carrier Power at Rcvr Input": -300.0, "C/N": -100.0}), int(valid)


def combine_cn(first, second):
    return -10 * math.log10(10 ** (-first / 10) + 10 ** (-second / 10))


def read_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [str(row["name"]) for row in data["satellites"]]


def state_at(state_data, index):
    return {
        "position": [state_data[0][axis][index] for axis in ("x", "y", "z")],
        "velocity": [state_data[1][axis][index] for axis in ("x", "y", "z")],
        "acceleration": [state_data[2][axis][index] for axis in ("x", "y", "z")],
    }


def metric_at(budgets, time):
    hops = [hop(data, time) for _name, data in budgets]
    dl_valid = hops[0][1] * hops[1][1]
    ul_valid = hops[2][1] * hops[3][1]
    return {
        "dl_power": hops[1][0]["Carrier Power at Rcvr Input"],
        "ul_power": hops[3][0]["Carrier Power at Rcvr Input"],
        "dl_cn": combine_cn(hops[0][0]["C/N"], hops[1][0]["C/N"]),
        "ul_cn": combine_cn(hops[2][0]["C/N"], hops[3][0]["C/N"]),
        "dl_valid": dl_valid,
        "ul_valid": ul_valid,
    }


def trace_state(states, budgets, name, index, time):
    if not name:
        return {"position": [0.0, 0.0, 0.0], "velocity": [0.0, 0.0, 0.0],
                "acceleration": [0.0, 0.0, 0.0], "dl_power": -300.0,
                "ul_power": -300.0, "dl_cn": -100.0, "ul_cn": -100.0,
                "dl_valid": 0, "ul_valid": 0}
    row = state_at(states[name], index)
    row.update(metric_at(budgets[name], time))
    return row


def preserve_valid_old_metrics(old, new):
    """Keep the old valid path until a newly selected path is valid."""
    result = dict(new)
    for direction in ("dl", "ul"):
        if old[f"{direction}_valid"] and not new[f"{direction}_valid"]:
            result[f"{direction}_power"] = old[f"{direction}_power"]
            result[f"{direction}_cn"] = old[f"{direction}_cn"]
            result[f"{direction}_valid"] = 1
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--start", type=float, default=7400.0)
    p.add_argument("--stop", type=float, default=12000.0)
    p.add_argument("--step", type=float, default=1.0)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--schedule-out", type=Path, required=True)
    p.add_argument("--acquire-elev-deg", type=float, default=10.0)
    p.add_argument("--release-elev-deg", type=float, default=5.0)
    p.add_argument("--min-dwell-s", type=float, default=30.0)
    p.add_argument("--handover-blend-s", type=float, default=5.0)
    args = p.parse_args()
    if args.stop <= args.start or args.step <= 0 or args.handover_blend_s < 0:
        p.error("invalid interval")

    desktop = STKDesktop.AttachToApplication()
    root = desktop.Root
    root.CloseScenario() if root.CurrentScenario is not None else None
    root.LoadScenario(str(args.scenario.resolve()))
    for dim, unit in [("FrequencyUnit", "Hz"), ("PowerUnit", "dBW"),
                      ("BitsUnit", "b"), ("TimeUnit", "sec"),
                      ("BandwidthUnit", "Hz"), ("DistanceUnit", "m"),
                      ("DateFormat", "EpSec"), ("AngleUnit", "deg"),
                      ("RatioUnit", "dB")]:
        root.UnitPreferences.SetCurrentUnit(dim, unit)

    sat_names = read_manifest(args.manifest)
    ground = root.GetObjectFromPath(GNB)
    ue_obj = root.GetObjectFromPath(UE)
    gnb = list(map(float, ground.Position.QueryCartesianArray()))
    ue = list(map(float, ue_obj.Position.QueryCartesianArray()))
    sat_objects = {name: root.GetObjectFromPath("Satellite/" + name) for name in sat_names}
    first = sat_objects[sat_names[0]]
    times, state_data = state_grid(first, args.start, args.stop, args.step)
    states = {sat_names[0]: state_data}
    for name in sat_names[1:]:
        sat_times, sat_state = state_grid(sat_objects[name], args.start, args.stop, args.step)
        if sat_times != times:
            raise RuntimeError(f"state time grid differs for {name}")
        states[name] = sat_state

    visibility = {}
    budgets = {}
    for name, sat in sat_objects.items():
        visibility[name] = visibility_map(ground, sat, args.start, args.stop, args.step)
        budgets[name] = link_budgets(
            [root.GetObjectFromPath(path) for path in endpoints(GNB, UE, name)],
            args.start, args.stop, args.step,
        )
        print(f"PREPARED {name}: access_intervals={len(visibility[name][1])}", flush=True)

    current = None
    current_since = times[0]
    schedule_rows = []
    selected_rows = []
    switch_count = 0
    valid = [0, 0]
    for i, t in enumerate(times):
        candidates = []
        elevations = {}
        for name in sat_names:
            elev_map, ints = visibility[name]
            elev = elev_map.get(round(t, 6)) if in_intervals(t, ints) else None
            if elev is not None and math.isfinite(elev):
                elevations[name] = elev
                candidates.append({"id": name, "elevation_deg": elev})
        cur_elev = elevations.get(current) if current else None
        selected, switched = select_satellite(
            candidates, current, cur_elev, args.acquire_elev_deg,
            args.release_elev_deg, t - current_since, args.min_dwell_s,
        )
        if switched:
            switch_count += 1
            current_since = t
        current = selected
        elevation = elevations.get(current, float("nan")) if current else float("nan")
        schedule_rows.append([t, current or "", elevation, int(current is not None), int(switched)])
        if current is not None:
            pass
        selected_rows.append({"current": current, "elevation": elevation,
                              "switched": switched, "index": i, "time": t})

    # Build deterministic handover windows around each selector transition.
    events = []
    blend_rows = max(0, math.ceil(args.handover_blend_s / args.step))
    for i, row in enumerate(selected_rows):
        if not row["switched"] or i == 0:
            continue
        old_name = selected_rows[i - 1]["current"]
        new_name = row["current"]
        if not old_name or not new_name or old_name == new_name:
            continue
        start_i = max(0, i - blend_rows)
        events.append({"index": i, "start": start_i, "old": old_name, "new": new_name})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.schedule_out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="ascii") as f:
        f.write("STKTRACE2\n")
        f.write("# time,x,y,z,vx,vy,vz,ax,ay,az,gnb_x,gnb_y,gnb_z,ue_x,ue_y,ue_z,dl_power_dbw,ul_power_dbw,dl_cn_db,ul_cn_db,dl_valid,ul_valid\n")
        w = csv.writer(f)
        for selected in selected_rows:
            i = selected["index"]
            current = selected["current"]
            phase = "steady"
            previous_name = ""
            next_name = ""
            effective = trace_state(states, budgets, current, i, times[i])
            for event in events:
                if event["start"] <= i <= event["index"]:
                    old_name, new_name = event["old"], event["new"]
                    start_time = times[event["start"]]
                    duration = times[event["index"]] - start_time
                    old_state = trace_state(states, budgets, old_name, i, times[i])
                    new_state = preserve_valid_old_metrics(
                        old_state, trace_state(states, budgets, new_name, i, times[i]))
                    effective = interpolate_state(
                        old_state, new_state,
                        blend_alpha(times[i], start_time, duration),
                        reference_site=gnb,
                    )
                    previous_name, next_name = old_name, new_name
                    phase = "prepare" if i == event["start"] else "blend"
                    if i == event["index"]:
                        phase = "complete"
                        current = new_name
                    else:
                        current = old_name
                    break
            dl = int(effective["dl_valid"])
            ul = int(effective["ul_valid"])
            valid[0] += dl
            valid[1] += ul
            row = [times[i]] + effective["position"] + effective["velocity"] + effective["acceleration"]
            row += gnb + ue + [effective["dl_power"], effective["ul_power"],
                               effective["dl_cn"], effective["ul_cn"], dl, ul]
            if not all(math.isfinite(v) for v in row):
                raise RuntimeError("nonfinite export")
            w.writerow(row)
            schedule_rows[i] = [times[i], current or "", selected["elevation"],
                                int(current is not None), int(selected["switched"]),
                                phase, previous_name, next_name]

    with args.schedule_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "satellite_id", "elevation_deg", "visible", "switched",
                    "handover_phase", "previous_satellite_id", "next_satellite_id"])
        w.writerows(schedule_rows)

    metadata = {
        "scenario": str(args.scenario.resolve()), "manifest": str(args.manifest.resolve()),
        "start": times[0], "stop": times[-1], "step": args.step, "rows": len(times),
        "satellites": sat_names, "switch_count": switch_count,
        "valid_dl_ul": valid, "schedule": str(args.schedule_out.resolve()),
        "acquire_elevation_deg": args.acquire_elev_deg,
        "release_elevation_deg": args.release_elev_deg,
        "min_dwell_s": args.min_dwell_s, "gnb_ecef_m": gnb, "ue_ecef_m": ue,
        "handover_blend_s": args.handover_blend_s,
        "model": "selected in-view satellite; continuous STK link-state blend; RFsim IQ-clock replay",
    }
    args.out.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
