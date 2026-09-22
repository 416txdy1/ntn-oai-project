"""Bridge an active STK 12 scenario to OAI RFsim and print link metrics.

The UDP wire format intentionally remains compatible with OAI's existing
``stk_channel_model.c`` receiver::

  STK1,seq,time,x,y,z,vx,vy,vz,ax,ay,az,gnb_x,gnb_y,gnb_z,ue_x,ue_y,ue_z,simulation_rate

Rich STK Communications metrics are queried only at ``--status-interval`` and
printed in the bridge terminal.  They are not added to the STK1 packet.
If ``--log-target`` is specified, the JSON metrics are also sent via UDP.
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import threading
import time
from dataclasses import dataclass

from agi.stk12.stkdesktop import STKDesktop


def iter_children(obj):
    children = getattr(obj, "Children", None)
    if children is None:
        return
    for index in range(children.Count):
        child = children.Item(index)
        yield child
        yield from iter_children(child)


def configure_units(root):
    for dimension, unit in (
        ("DateFormat", "EpSec"),
        ("DistanceUnit", "m"),
        ("TimeUnit", "sec"),
        ("FrequencyUnit", "Hz"),
        ("PowerUnit", "dBW"),
        ("RatioUnit", "dB"),
        ("AngleUnit", "deg"),
    ):
        try:
            root.UnitPreferences.SetCurrentUnit(dimension, unit)
        except Exception:
            pass


def current_epsec(root) -> float:
    value = root.CurrentTime
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(root.ConversionUtility.ConvertDate("UTCG", str(value), "EpSec"))


def object_by_path_or_auto(root, scenario, path, class_name, preferred_names):
    if path:
        return root.GetObjectFromPath(path)
    matches = [obj for obj in iter_children(scenario) if str(obj.ClassName) == class_name]
    for preferred in preferred_names:
        for obj in matches:
            if str(obj.InstanceName).lower() == preferred.lower():
                return obj
    if len(matches) == 1:
        return matches[0]
    paths = [str(obj.Path) for obj in matches]
    raise RuntimeError(
        f"cannot choose {class_name} automatically; provide its path explicitly. "
        f"Candidates: {paths}"
    )


def ground_object(root, scenario, path, preferred_names):
    if path:
        return root.GetObjectFromPath(path)
    candidates = [
        obj
        for obj in iter_children(scenario)
        if str(obj.ClassName) in ("Facility", "Place", "Target")
    ]
    for preferred in preferred_names:
        for obj in candidates:
            if str(obj.InstanceName).lower() == preferred.lower():
                return obj
    paths = [str(obj.Path) for obj in candidates]
    raise RuntimeError(f"cannot choose a ground object automatically; candidates: {paths}")


def time_provider(obj, paths):
    errors = []
    for path in paths:
        try:
            return obj.DataProviders.GetDataPrvTimeVarFromPath(path)
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    raise RuntimeError("no compatible STK data provider: " + "; ".join(errors))


def values(provider, epoch_s, names):
    result = provider.ExecSingleElements(epoch_s, list(names))
    return tuple(
        float(result.DataSets.GetDataSetByName(name).GetValues()[0]) for name in names
    )


def scalar(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def provider_elements(provider):
    return [str(provider.Elements.Item(i).Name) for i in range(provider.Elements.Count)]


def query_elements(provider, epoch_s, requested):
    available = set(provider_elements(provider))
    selected = [name for name in requested if name in available]
    if not selected:
        return {}
    result = provider.ExecSingleElements(epoch_s, selected)
    output = {}
    for name in selected:
        try:
            raw = result.DataSets.GetDataSetByName(name).GetValues()[0]
            output[name] = scalar(raw)
        except Exception:
            pass
    return output


def fixed_position(obj):
    try:
        return tuple(float(v) for v in obj.Position.QueryCartesianArray())
    except Exception:
        provider = time_provider(obj, ("Cartesian Position//Fixed", "Cartesian Position/Fixed"))
        return provider


def position_at(position_or_provider, epoch_s):
    if isinstance(position_or_provider, tuple):
        return position_or_provider
    return values(position_or_provider, epoch_s, ("x", "y", "z"))


def make_aer(site, satellite):
    access = site.GetAccessToObject(satellite)
    access.ComputeAccess()
    provider = access.DataProviders.GetDataPrvTimeVarFromPath("AER Data//Default")
    return provider


def aer_at(provider, epoch_s):
    try:
        az, el, distance, rate, delay = values(
            provider, epoch_s, ("Azimuth", "Elevation", "Range", "RangeRate", "Path Delay")
        )
        return {
            "available": True,
            "azimuth_deg": az,
            "elevation_deg": el,
            "range_m": distance,
            "range_rate_mps": rate,
            "propagation_delay_ms": delay * 1000.0,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


CHAIN_FIELDS = tuple(
    ["Time"]
    + [
        f"{base}{hop}"
        for hop in (1, 2)
        for base in (
            "Xmtr Azimuth",
            "Xmtr Elevation",
            "Range",
            "Free Space Loss",
            "Prop Loss",
            "Rcvd. Frequency",
            "Freq. Doppler Shift",
            "Carrier Power at Rcvr Input",
            "C/No",
            "C/No Tot.",
            "C/N",
            "C/N Tot.",
            "Eb/No",
            "Eb/No Tot.",
            "BER",
            "BER Tot.",
            "Propagation Delay",
            "Propagation Distance",
        )
    ]
)


def chain_provider(chain):
    try:
        chain.ComputeAccess()
    except Exception:
        pass
    return chain.DataProviders.GetDataPrvTimeVarFromPath("Link Information")


def sum_fields(raw, stem):
    fields = [raw.get(f"{stem}1"), raw.get(f"{stem}2")]
    if all(isinstance(item, (int, float)) for item in fields):
        return sum(fields)
    return None


def predicted_bler(ber, block_bits):
    """Independent-bit approximation: BLER = 1 - (1 - BER)^N."""
    if not isinstance(ber, (int, float)) or not 0.0 <= ber <= 1.0:
        return None
    if ber == 1.0:
        return 1.0
    return -math.expm1(block_bits * math.log1p(-ber))


def hop_metrics(raw, hop):
    return {
        "azimuth_deg": raw.get(f"Xmtr Azimuth{hop}"),
        "elevation_deg": raw.get(f"Xmtr Elevation{hop}"),
        "range_m": raw.get(f"Range{hop}"),
        "propagation_delay_s": raw.get(f"Propagation Delay{hop}"),
        "doppler_hz": raw.get(f"Freq. Doppler Shift{hop}"),
        "free_space_loss_db": raw.get(f"Free Space Loss{hop}"),
        "propagation_loss_db": raw.get(f"Prop Loss{hop}"),
        "received_power_dbw": raw.get(f"Carrier Power at Rcvr Input{hop}"),
        "c_no_dbhz": raw.get(f"C/No{hop}"),
        "snr_c_n_db": raw.get(f"C/N{hop}"),
        "eb_no_db": raw.get(f"Eb/No{hop}"),
        "ber_predicted": raw.get(f"BER{hop}"),
    }


def chain_metrics(provider, epoch_s, block_bits, include_raw=False):
    if provider is None:
        return {"available": False, "error": "chain was not configured/found"}
    try:
        raw = query_elements(provider, epoch_s, CHAIN_FIELDS)
        if not raw:
            return {"available": False, "error": "no Link Information at this STK time"}
        final_hop = 2 if "Range2" in raw else 1
        ber_total = raw.get(f"BER Tot.{final_hop}", raw.get(f"BER{final_hop}"))
        result = {
            "available": True,
            "first_hop": hop_metrics(raw, 1),
            "second_hop": hop_metrics(raw, 2) if final_hop == 2 else None,
            "end_to_end": {
                "range_m": sum_fields(raw, "Range"),
                "propagation_delay_s": sum_fields(raw, "Propagation Delay"),
                "propagation_loss_db": sum_fields(raw, "Prop Loss"),
                "doppler_sum_hz": sum_fields(raw, "Freq. Doppler Shift"),
                "received_power_dbw": raw.get(f"Carrier Power at Rcvr Input{final_hop}"),
                "c_no_dbhz": raw.get(f"C/No Tot.{final_hop}", raw.get(f"C/No{final_hop}")),
                "snr_c_n_db": raw.get(f"C/N Tot.{final_hop}", raw.get(f"C/N{final_hop}")),
                "eb_no_db": raw.get(f"Eb/No Tot.{final_hop}", raw.get(f"Eb/No{final_hop}")),
                "ber_predicted": ber_total,
                "bler_independent_bit_predicted": predicted_bler(ber_total, block_bits),
                "bler_assumed_block_bits": block_bits,
            },
        }
        if include_raw:
            result["stk_raw"] = raw
        return result
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def resolve_chain(root, scenario, path, preferred_name):
    if path:
        return root.GetObjectFromPath(path)
    matches = [obj for obj in iter_children(scenario) if str(obj.ClassName) == "Chain"]
    for obj in matches:
        if str(obj.InstanceName).lower() == preferred_name.lower():
            return obj
    return None


def parse_target(text):
    try:
        host, port_text = text.rsplit(":", 1)
        port = int(port_text)
    except Exception as exc:
        raise argparse.ArgumentTypeError("target must be HOST:PORT") from exc
    if not host or not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("target must contain a host and port 1..65535")
    return host, port


@dataclass
class Ephemeris:
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    acceleration: tuple[float, float, float]


@dataclass
class SendSample:
    epoch_s: float
    sampled_real_s: float
    wallclock_rate: float
    rfsim_rate: float
    ephemeris: Ephemeris
    gnb_position: tuple[float, float, float]
    ue_position: tuple[float, float, float]


def propagate(sample, now_s):
    dt = (now_s - sample.sampled_real_s) * sample.wallclock_rate
    position = tuple(
        sample.ephemeris.position[i]
        + sample.ephemeris.velocity[i] * dt
        + 0.5 * sample.ephemeris.acceleration[i] * dt * dt
        for i in range(3)
    )
    physical_velocity = tuple(
        sample.ephemeris.velocity[i] + sample.ephemeris.acceleration[i] * dt
        for i in range(3)
    )
    # Keep the wire velocity and acceleration in physical STK units.  Each OAI
    # endpoint maps STK time to its own RFsim sample clock from consecutive
    # packet timestamps.  Scaling here by wall-clock animation rate would mix
    # three different clocks (STK, wall clock and RFsim) and make gNB/UE drift.
    return sample.epoch_s + dt, position, physical_velocity, sample.ephemeris.acceleration


def packet_sender(args, sample_lock, shared, stop_event):
    """Send at a stable wall-clock rate even while STK link queries are slow."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    period = 1.0 / args.rate_hz
    next_send = time.monotonic()
    try:
        while not stop_event.is_set():
            with sample_lock:
                sample = shared["sample"]
                sent = shared["sent"]
            if sample is None:
                stop_event.wait(0.01)
                continue
            if args.count and sent >= args.count:
                stop_event.set()
                break

            now_s = time.monotonic()
            epoch_s, position, velocity, acceleration = propagate(sample, now_s)
            sequence = shared["sequence_start"] + sent
            fields = [
                "STK1", str(sequence), f"{epoch_s:.9f}",
                *(f"{v:.9f}" for v in position),
                *(f"{v:.9f}" for v in velocity),
                *(f"{v:.9f}" for v in acceleration),
                *(f"{v:.9f}" for v in sample.gnb_position),
                *(f"{v:.9f}" for v in sample.ue_position),
                f"{sample.rfsim_rate:.9f}",
            ]
            payload = ",".join(fields).encode("ascii")
            for target in args.target:
                sock.sendto(payload, target)
            with sample_lock:
                shared["sent"] += 1
                shared["last_sequence"] = sequence

            next_send += period
            delay = next_send - time.monotonic()
            if delay > 0:
                stop_event.wait(delay)
            else:
                # Do not emit a burst after an unusually long scheduler pause.
                next_send = time.monotonic()
    except Exception as exc:
        with sample_lock:
            shared["error"] = exc
        stop_event.set()
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send STK satellite state to OAI and periodically print RF metrics"
    )
    parser.add_argument("--target", action="append", type=parse_target, required=True,
                        help="OAI UDP receiver HOST:PORT; repeat for gNB and UE")
    parser.add_argument("--log-target", action="append", type=parse_target,
                        help="UDP target for sending JSON logs (HOST:PORT); repeat for multiple targets")
    parser.add_argument("--satellite", help="STK satellite object path")
    parser.add_argument("--gnb", help="STK Place/Facility path used as gNB")
    parser.add_argument("--ue", help="STK Place/Facility path used as UE")
    parser.add_argument("--ul-chain", help="STK uplink Chain path; auto-detects OAI_UL")
    parser.add_argument("--dl-chain", help="STK downlink Chain path; auto-detects OAI_DL")
    parser.add_argument("--rate-hz", type=float, default=20.0)
    parser.add_argument("--status-interval", type=float, default=10.0,
                        help="terminal metrics interval in real seconds; 0 disables it")
    parser.add_argument("--time-mode", choices=("animation", "wallclock"), default="animation")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="STK seconds per real second in wallclock mode")
    parser.add_argument(
        "--rfsim-speed",
        type=float,
        help=(
            "STK seconds per RFsim second written to OAI; defaults to the sampled "
            "animation/wallclock rate. Set this separately when RFsim runs slower than real time"
        ),
    )
    parser.add_argument("--count", type=int, default=0, help="packet count; 0 runs until Ctrl-C")
    parser.add_argument(
        "--sequence-start",
        type=int,
        help="first STK1 sequence; defaults to Unix time in milliseconds so bridge restarts are newer",
    )
    parser.add_argument("--bler-block-bits", type=int, default=1000,
                        help="block length used only for independent-bit BLER prediction")
    parser.add_argument("--verbose-metrics", action="store_true",
                        help="include all selected STK Link Information fields in each log")
    args = parser.parse_args()
    if (args.rate_hz <= 0 or args.status_interval < 0 or args.speed <= 0
            or (args.rfsim_speed is not None and args.rfsim_speed < 0)
            or args.count < 0 or args.bler_block_bits <= 0
            or (args.sequence_start is not None and args.sequence_start < 0)):
        parser.error("rate and speed must be positive; interval/count must be non-negative")

    # Prepare log targets
    log_targets = args.log_target if args.log_target else []
    log_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if log_targets else None

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
    ul_chain = resolve_chain(root, scenario, args.ul_chain, "OAI_UL")
    dl_chain = resolve_chain(root, scenario, args.dl_chain, "OAI_DL")

    print(
        "[STK-BRIDGE] preparing ephemeris and access providers; "
        "the first access calculation can take several seconds",
        flush=True,
    )

    position_provider = time_provider(
        satellite, ("Cartesian Position//Fixed", "Cartesian Position/Fixed")
    )
    velocity_provider = time_provider(
        satellite, ("Cartesian Velocity//Fixed", "Cartesian Velocity/Fixed")
    )
    acceleration_provider = time_provider(
        satellite, ("Cartesian Acceleration//Fixed", "Cartesian Acceleration/Fixed")
    )
    lla_provider = time_provider(satellite, ("LLA State//Fixed", "LLA State/Fixed"))
    gnb_position = fixed_position(gnb)
    ue_position = fixed_position(ue)
    gnb_aer = make_aer(gnb, satellite)
    ue_aer = make_aer(ue, satellite)
    ul_provider = chain_provider(ul_chain) if ul_chain is not None else None
    dl_provider = chain_provider(dl_chain) if dl_chain is not None else None

    start_real = time.monotonic()
    start_stk = current_epsec(root)
    sequence_start = (
        args.sequence_start if args.sequence_start is not None else time.time_ns() // 1_000_000
    )
    next_status = start_real + args.status_interval
    sample_period = 1.0 / args.rate_hz
    animation_epoch = None
    animation_change_real = None
    animation_rate = 0.0
    sample_lock = threading.Lock()
    stop_event = threading.Event()
    shared = {
        "sample": None,
        "sent": 0,
        "last_sequence": None,
        "sequence_start": sequence_start,
        "error": None,
    }

    startup = {
        "event": "bridge_started",
        "scenario": str(scenario.InstanceName),
        "satellite": str(satellite.Path),
        "gnb": str(gnb.Path),
        "ue": str(ue.Path),
        "uplink_chain": str(ul_chain.Path) if ul_chain is not None else None,
        "downlink_chain": str(dl_chain.Path) if dl_chain is not None else None,
        "targets": [f"{host}:{port}" for host, port in args.target],
        "packet_rate_hz": args.rate_hz,
        "status_interval_s": args.status_interval,
        "time_mode": args.time_mode,
        "rfsim_speed_override": args.rfsim_speed,
        "sequence_start": sequence_start,
        "packet_frame": "Fixed/ECEF Cartesian; m, m/s, m/s^2; explicit STK animation rate",
        "bler_note": (
            f"predicted as 1-(1-BER)^{args.bler_block_bits}; "
            "this is not OAI measured HARQ BLER"
        ),
    }
    print("[STK-BRIDGE] " + json.dumps(startup, ensure_ascii=False), flush=True)

    sender = threading.Thread(
        target=packet_sender,
        args=(args, sample_lock, shared, stop_event),
        name="stk-oai-udp-sender",
        daemon=True,
    )
    sender.start()

    try:
        while not stop_event.is_set():
            loop_start = time.monotonic()
            if args.time_mode == "animation":
                epoch_s = current_epsec(root)
            else:
                epoch_s = start_stk + (loop_start - start_real) * args.speed

            ephemeris = Ephemeris(
                position=values(position_provider, epoch_s, ("x", "y", "z")),
                velocity=values(velocity_provider, epoch_s, ("x", "y", "z")),
                acceleration=values(acceleration_provider, epoch_s, ("x", "y", "z")),
            )
            gnb_xyz = position_at(gnb_position, epoch_s)
            ue_xyz = position_at(ue_position, epoch_s)

            if args.time_mode == "wallclock":
                simulation_rate = args.speed
            else:
                # STK GUI animation advances CurrentTime in discrete frames.  Estimating
                # its rate from every 20 Hz bridge sample used to alternate between zero
                # (no new animation frame) and a large spike (the next frame), which
                # produced discontinuous Doppler and delay-rate updates in RFsim.
                if animation_epoch is None:
                    animation_epoch = epoch_s
                    animation_change_real = loop_start
                elif epoch_s != animation_epoch:
                    real_delta = loop_start - animation_change_real
                    raw_rate = (epoch_s - animation_epoch) / real_delta if real_delta > 0 else 0.0
                    # A manual seek is a discontinuity, not an animation rate.
                    if math.isfinite(raw_rate) and abs(raw_rate) <= 100.0:
                        if animation_rate == 0.0:
                            animation_rate = raw_rate
                        else:
                            # Smooth scheduler and COM sampling jitter while preserving
                            # deliberate animation-rate changes.
                            animation_rate = 0.75 * animation_rate + 0.25 * raw_rate
                    else:
                        animation_rate = 0.0
                    animation_epoch = epoch_s
                    animation_change_real = loop_start
                elif loop_start - animation_change_real > 0.25:
                    # No STK animation frame for long enough: treat it as paused.  Keep
                    # the baseline recent so the first frame after resume is not divided
                    # by the entire pause duration.
                    animation_rate = 0.0
                    animation_change_real = loop_start
                simulation_rate = animation_rate
            rfsim_rate = simulation_rate if args.rfsim_speed is None else args.rfsim_speed
            with sample_lock:
                shared["sample"] = SendSample(
                    epoch_s=epoch_s,
                    sampled_real_s=loop_start,
                    wallclock_rate=simulation_rate,
                    rfsim_rate=rfsim_rate,
                    ephemeris=ephemeris,
                    gnb_position=gnb_xyz,
                    ue_position=ue_xyz,
                )

            if args.status_interval > 0 and loop_start >= next_status:
                altitude_m = values(lla_provider, epoch_s, ("Lat", "Lon", "Alt"))[2]
                report = {
                    "seq": shared["last_sequence"],
                    "udp_packets_sent": shared["sent"],
                    "estimated_stk_seconds_per_real_second": simulation_rate,
                    "configured_stk_seconds_per_rfsim_second": rfsim_rate,
                    "stk_time_s": epoch_s,
                    "satellite": {
                        "position_ecef_m": ephemeris.position,
                        "stk_physical_velocity_ecef_mps": ephemeris.velocity,
                        "stk_physical_speed_mps": math.sqrt(sum(v * v for v in ephemeris.velocity)),
                        "oai_effective_velocity_ecef_mps": tuple(
                            v * rfsim_rate for v in ephemeris.velocity
                        ),
                        "oai_effective_speed_mps": abs(rfsim_rate)
                        * math.sqrt(sum(v * v for v in ephemeris.velocity)),
                        "altitude_m": altitude_m,
                    },
                    "gnb_to_satellite_geometry": aer_at(gnb_aer, epoch_s),
                    "ue_to_satellite_geometry": aer_at(ue_aer, epoch_s),
                    "uplink": chain_metrics(
                        ul_provider, epoch_s, args.bler_block_bits, args.verbose_metrics
                    ),
                    "downlink": chain_metrics(
                        dl_provider, epoch_s, args.bler_block_bits, args.verbose_metrics
                    ),
                }
                log_json = json.dumps(report, ensure_ascii=False)
                print("[STK-METRICS] " + log_json, flush=True)

                # Send log to all log-targets if specified
                if log_sock and log_targets:
                    for host, port in log_targets:
                        try:
                            log_sock.sendto(log_json.encode("utf-8"), (host, port))
                        except Exception as e:
                            print(f"[STK-BRIDGE] WARNING: failed to send log to {host}:{port} - {e}", flush=True)

                next_status = time.monotonic() + args.status_interval

            remaining = sample_period - (time.monotonic() - loop_start)
            if remaining > 0:
                stop_event.wait(remaining)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        stop_event.set()
        sender.join(timeout=2.0)
        if log_sock:
            log_sock.close()
    with sample_lock:
        sent = shared["sent"]
        sender_error = shared["error"]
    if sender_error is not None:
        raise RuntimeError(f"UDP sender failed: {sender_error}") from sender_error
    print(f"[STK-BRIDGE] stopped after {sent} packets", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())