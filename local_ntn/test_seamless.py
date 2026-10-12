"""Run concurrent long ping/iperf probes across the exported satellite handovers."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


BASE = Path(__file__).resolve().parent


def experiment(*args: str, **kwargs):
    return subprocess.run(["python3", str(BASE / "experiment.py"), *args], **kwargs)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tag", default="seamless-20260924")
    p.add_argument("--duration", type=int, default=620)
    p.add_argument(
        "--rate",
        type=float,
        default=0.1,
        help="STK trace seconds per RFsim IQ second (default: 0.1; use 1 for accelerated replay)",
    )
    a = p.parse_args()
    if a.duration <= 0:
        p.error("--duration must be positive")
    if a.rate <= 0:
        p.error("--rate must be positive")

    experiment("stop", check=True)
    time.sleep(2)
    experiment("start", "--rate", str(a.rate), "--label", a.tag, check=True)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        probe = subprocess.run(
            ["ip", "-n", "oai-stk-ue", "-4", "addr", "show", "dev", "oaitun_ue1"],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0 and "inet " in probe.stdout:
            break
        time.sleep(0.5)
    else:
        experiment("status")
        raise SystemExit("No PDU session within 60 wall seconds")

    ping_log = (BASE / f"ping-seamless-{a.tag}.txt").open("w")
    iperf_log = (BASE / f"iperf-seamless-{a.tag}.txt").open("w")
    try:
        ping = subprocess.Popen(
            ["python3", str(BASE / "experiment.py"), "ping",
             "--ping-count", str(a.duration)],
            stdout=ping_log, stderr=subprocess.STDOUT,
        )
        iperf = subprocess.Popen(
            ["python3", str(BASE / "experiment.py"), "iperf",
             "--iperf-seconds", str(a.duration)],
            stdout=iperf_log, stderr=subprocess.STDOUT,
        )
        ping_rc = ping.wait(timeout=a.duration * 6 + 60)
        iperf_rc = iperf.wait(timeout=a.duration * 6 + 60)
    finally:
        ping_log.close()
        iperf_log.close()
    experiment("status")
    print(f"ping_exit={ping_rc} iperf_exit={iperf_rc}")
    return 0 if ping_rc == 0 and iperf_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
