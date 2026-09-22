#!/usr/bin/env python3
"""Display Satellite1 state from the active STK 12 scenario."""

import argparse
import math
import time

from agi.stk12.stkdesktop import STKDesktop


def time_provider(obj, quantity):
    for path in (f"{quantity}//Fixed", f"{quantity}/Fixed"):
        try:
            return obj.DataProviders.GetDataPrvTimeVarFromPath(path)
        except Exception:
            pass
    raise RuntimeError(f"Cannot find STK data provider: {quantity}/Fixed")


def values(provider, epoch, names):
    result = provider.ExecSingleElements(epoch, list(names))
    return tuple(
        float(result.DataSets.GetDataSetByName(name).GetValues()[0])
        for name in names
    )


def current_epsec(root):
    try:
        return float(root.CurrentTime)
    except (TypeError, ValueError):
        return float(
            root.ConversionUtility.ConvertDate("UTCG", str(root.CurrentTime), "EpSec")
        )


parser = argparse.ArgumentParser()
parser.add_argument("--satellite", default="*/Satellite/Satellite1")
parser.add_argument(
    "--interval",
    type=float,
    default=0.0,
    help="refresh interval in seconds; 0 prints once",
)
parser.add_argument(
    "--wallclock",
    action="store_true",
    help="advance from STK CurrentTime using wall-clock time, like the bridge",
)
args = parser.parse_args()

desktop = STKDesktop.AttachToApplication()
root = desktop.Root
root.UnitPreferences.SetCurrentUnit("DateFormat", "EpSec")
root.UnitPreferences.SetCurrentUnit("DistanceUnit", "m")
root.UnitPreferences.SetCurrentUnit("TimeUnit", "sec")

satellite = root.GetObjectFromPath(args.satellite)
position_provider = time_provider(satellite, "Cartesian Position")
velocity_provider = time_provider(satellite, "Cartesian Velocity")
lla_provider = time_provider(satellite, "LLA State")

start_epoch = current_epsec(root)
start_wall = time.monotonic()

print("time_s,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps,speed_mps,altitude_m")
while True:
    if args.wallclock:
        epoch = start_epoch + time.monotonic() - start_wall
    else:
        epoch = current_epsec(root)

    x, y, z = values(position_provider, epoch, ("x", "y", "z"))
    vx, vy, vz = values(velocity_provider, epoch, ("x", "y", "z"))
    (altitude,) = values(lla_provider, epoch, ("Alt",))
    speed = math.sqrt(vx * vx + vy * vy + vz * vz)

    print(
        f"{epoch:.6f},{x:.3f},{y:.3f},{z:.3f},"
        f"{vx:.6f},{vy:.6f},{vz:.6f},{speed:.6f},{altitude:.3f}",
        flush=True,
    )

    if args.interval <= 0.0:
        break
    time.sleep(args.interval)
