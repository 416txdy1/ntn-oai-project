import argparse
import math

from agi.stk12.stkdesktop import STKDesktop
from stk_oai_bridge_generic import (
    configure_units,
    ground_object,
    object_by_path_or_auto,
)


def intervals(access):
    access.ComputeAccess()
    collection = access.ComputedAccessIntervalTimes
    return [tuple(map(float, collection.GetInterval(i))) for i in range(collection.Count)]


def provider(obj, quantity):
    for path in (f"Cartesian {quantity}//Fixed", f"Cartesian {quantity}/Fixed"):
        try:
            return obj.DataProviders.GetDataPrvTimeVarFromPath(path)
        except Exception:
            pass
    raise RuntimeError(f"No Fixed Cartesian {quantity} provider")


def vector_at(data_provider, epoch):
    result = data_provider.ExecSingleElements(epoch, ["x", "y", "z"])
    return tuple(float(result.DataSets.GetDataSetByName(axis).GetValues()[0]) for axis in ("x", "y", "z"))


def site_position(site):
    xyz = site.Position.QueryCartesianArray()
    return tuple(float(value) for value in xyz)


def range_and_rate(sat_pos, sat_vel, site_pos):
    relative = tuple(sat_pos[i] - site_pos[i] for i in range(3))
    distance = math.sqrt(sum(value * value for value in relative))
    rate = sum(relative[i] * sat_vel[i] for i in range(3)) / distance
    return distance, rate


parser = argparse.ArgumentParser(
    description="Move the active STK scenario to a common gNB/UE visibility interval"
)
parser.add_argument("--satellite", help="STK satellite object path")
parser.add_argument("--gnb", help="STK Place/Facility path used as gNB")
parser.add_argument("--ue", help="STK Place/Facility path used as UE")
args = parser.parse_args()

desktop = STKDesktop.AttachToApplication()
root = desktop.Root
scenario = root.CurrentScenario
if scenario is None:
    raise RuntimeError("STK has no active scenario")
configure_units(root)

satellite = object_by_path_or_auto(
    root, scenario, args.satellite, "Satellite", ("Satellite1",)
)
gnb = ground_object(root, scenario, args.gnb, ("gNB", "Beijing"))
ue = ground_object(root, scenario, args.ue, ("OAI_UE", "UE"))

print("selected satellite:", satellite.Path)
print("selected gNB:", gnb.Path)
print("selected UE:", ue.Path)

gnb_intervals = intervals(satellite.GetAccessToObject(gnb))
ue_intervals = intervals(satellite.GetAccessToObject(ue))

overlaps = []
for gnb_start, gnb_stop in gnb_intervals:
    for ue_start, ue_stop in ue_intervals:
        start = max(gnb_start, ue_start)
        stop = min(gnb_stop, ue_stop)
        if stop > start:
            overlaps.append((start, stop))

if not overlaps:
    raise RuntimeError("No common satellite/gNB/UE visibility interval exists in the scenario time period")

# Use the longest common interval and stay away from rise/set boundaries.
start, stop = max(overlaps, key=lambda item: item[1] - item[0])
chosen = (start + stop) / 2.0
root.CurrentTime = chosen

sat_pos = vector_at(provider(satellite, "Position"), chosen)
sat_vel = vector_at(provider(satellite, "Velocity"), chosen)
gnb_pos = site_position(gnb)
ue_pos = site_position(ue)
feeder_range, feeder_rate = range_and_rate(sat_pos, sat_vel, gnb_pos)
service_range, service_rate = range_and_rate(sat_pos, sat_vel, ue_pos)
c = 299792458.0
delay_ms = (feeder_range + service_range) / c * 1000.0
drift_us_s = (feeder_rate + service_rate) / c * 1_000_000.0
sat_to_ue_speed = -service_rate
doppler_hz = sat_to_ue_speed / (c - sat_to_ue_speed) * 2_488_400_000.0
koffset_ms = math.ceil(2.0 * delay_ms + 5.0)

print("gNB access intervals:", gnb_intervals)
print("UE access intervals:", ue_intervals)
print("common interval:", (start, stop))
print("STK CurrentTime set to:", chosen)
print(f"OAI initial propagation delay: {delay_ms:.6f} ms")
print(f"OAI initial DL Doppler: {doppler_hz:.3f} Hz")
print(f"OAI initial DL time drift: {drift_us_s:.6f} us/s")
print(f"Minimum suggested k_offset with 5 ms guard: {koffset_ms} ms")
print("\nSuggested UE command:")
print(
    "sudo env OAI_STK_PORT=49001 OAI_STK_TIMEOUT_MS=5000 "
    "./nr-uesoftmodem "
    "--rfsimulator.[0].serveraddr 192.168.114.16 "
    "-O ~/OAI/openairinterface5g/ci-scripts/conf_files/nrue.uicc.ntn-leo.conf "
    "--band 254 -C 2488400000 --CO -873500000 -r 25 --numerology 0 --ssb 60 "
    f"--rfsim --rfsimulator.[0].prop_delay {delay_ms:.3f} "
    "--rfsimulator.[0].options chanmod --time-sync-I 0.1 "
    "--cont-fo-comp 2"
)
