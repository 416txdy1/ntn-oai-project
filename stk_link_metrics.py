"""Export STK Communications Link Information for the active scenario."""

from __future__ import annotations

import argparse
import json

from agi.stk12.stkdesktop import STKDesktop


ELEMENTS = (
    "Time",
    "Xmtr Power",
    "Xmtr Azimuth",
    "Xmtr Elevation",
    "Xmtr Gain",
    "EIRP",
    "Range",
    "Free Space Loss",
    "Atmos Loss",
    "Rain Loss",
    "Prop Loss",
    "Rcvd. Frequency",
    "Freq. Doppler Shift",
    "Rcvd. Iso. Power",
    "Carrier Power at Rcvr Input",
    "Rcvr Azimuth",
    "Rcvr Elevation",
    "Rcvr Gain",
    "g/T",
    "C/No",
    "C/No Tot.",
    "Bandwidth",
    "C/N",
    "C/N Tot.",
    "Eb/No",
    "Eb/No Tot.",
    "BER",
    "BER Tot.",
    "Propagation Delay",
    "Propagation Distance",
)


def iter_children(obj):
    children = getattr(obj, "Children", None)
    if children is None:
        return
    for index in range(children.Count):
        child = children.Item(index)
        yield child
        yield from iter_children(child)


def current_epsec(root) -> float:
    value = root.CurrentTime
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(root.ConversionUtility.ConvertDate("UTCG", str(value), "EpSec"))


def configure_units(root):
    preferences = (
        ("DateFormat", "EpSec"),
        ("DistanceUnit", "m"),
        ("TimeUnit", "sec"),
        ("FrequencyUnit", "Hz"),
        ("PowerUnit", "dBW"),
        ("RatioUnit", "dB"),
        ("AngleUnit", "deg"),
    )
    applied = {}
    for dimension, unit in preferences:
        try:
            root.UnitPreferences.SetCurrentUnit(dimension, unit)
            applied[dimension] = unit
        except Exception:
            pass
    return applied


def resolve(root, scenario, path, class_name):
    if path:
        return root.GetObjectFromPath(path)
    matches = [obj for obj in iter_children(scenario) if str(obj.ClassName) == class_name]
    if len(matches) != 1:
        paths = [str(obj.Path) for obj in matches]
        raise RuntimeError(
            f"expected exactly one {class_name}, found {len(matches)}; "
            f"use --{class_name.lower()} with one of {paths}"
        )
    return matches[0]


def choose_epoch(access, requested_epoch, use_first_access):
    access.ComputeAccess()
    intervals = access.ComputedAccessIntervalTimes
    values = [tuple(map(float, intervals.GetInterval(i))) for i in range(intervals.Count)]
    for start, stop in values:
        if start <= requested_epoch <= stop:
            return requested_epoch, values
    if use_first_access and values:
        start, stop = values[0]
        return (start + stop) / 2.0, values
    raise RuntimeError(
        f"requested STK time {requested_epoch:.6f} is outside link access intervals: {values}"
    )


def scalar(dataset):
    values = dataset.GetValues()
    value = values[0]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export STK Link Information as JSON")
    parser.add_argument("--transmitter", help="STK transmitter object path")
    parser.add_argument("--receiver", help="STK receiver object path")
    parser.add_argument("--time", type=float, help="STK EpSec; defaults to CurrentTime")
    parser.add_argument(
        "--use-first-access",
        action="store_true",
        help="if the requested time is not visible, sample the midpoint of the first access",
    )
    args = parser.parse_args()

    desktop = STKDesktop.AttachToApplication()
    root = desktop.Root
    scenario = root.CurrentScenario
    units = configure_units(root)
    transmitter = resolve(root, scenario, args.transmitter, "Transmitter")
    receiver = resolve(root, scenario, args.receiver, "Receiver")
    access = transmitter.GetAccessToObject(receiver)
    requested_epoch = current_epsec(root) if args.time is None else args.time
    epoch, intervals = choose_epoch(access, requested_epoch, args.use_first_access)

    provider = access.DataProviders.GetDataPrvTimeVarFromPath("Link Information")
    result = provider.ExecSingleElements(epoch, list(ELEMENTS))
    metrics = {}
    unavailable = []
    for name in ELEMENTS:
        try:
            metrics[name] = scalar(result.DataSets.GetDataSetByName(name))
        except Exception:
            unavailable.append(name)
    output = {
        "source": "STK_Link_Information",
        "scenario": str(scenario.InstanceName),
        "transmitter": str(transmitter.Path),
        "receiver": str(receiver.Path),
        "requested_time_s": requested_epoch,
        "sample_time_s": epoch,
        "access_intervals_s": intervals,
        "units_requested": units,
        "metrics": metrics,
        "unavailable_metrics": unavailable,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
