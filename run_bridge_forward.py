#!/usr/bin/env python3
"""Start one STK bridge and forward only its text log over TCP port 9000."""

from __future__ import annotations

import ipaddress
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time

import psutil


PYTHON_EXE = sys.executable
BRIDGE_SCRIPT = Path(r"D:\实验室学习工作\杂活\雄安\OAI调研\stk_oai_bridge_generic.py")
WSL_DISTRO = "Ubuntu-22.04"

LOG_RECEIVER = ("10.29.132.223", 9000)
GNB_TARGET = "192.168.114.16:49000"
LAN_STK_TARGET = "10.29.132.223:49000"
UE_STK_PORT = 49001
# The current STK scene contains a constellation, so the bridge must be
# explicit about which satellite supplies the RFsim state.  Change this path
# when selecting another member of the constellation.
SATELLITE_PATH = (
    "/Application/STK/Scenario/OAI_LEO_Constellation/"
    "Satellite/OAI_LEO_P01_S01"
)

RATE_HZ = 20
STATUS_INTERVAL = 1               # one terminal/TCP status log per real second
TIME_MODE = "wallclock"
SPEED = 0.0008
RFSIM_SPEED = 0.1

STOP = False
BRIDGE_PROCESS: subprocess.Popen | None = None


def stop_signal(signum, frame) -> None:
    del signum, frame
    global STOP
    STOP = True
    raise KeyboardInterrupt


def wsl_capture(command: str) -> str:
    result = subprocess.run(
        ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", "--noprofile", "--norc", "-lc", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    return result.stdout


def detect_wsl_ip() -> str:
    output = wsl_capture(f"ip -4 route get {LOG_RECEIVER[0]}")
    match = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", output)
    if match:
        return match.group(1)

    output = wsl_capture("hostname -I")
    for token in output.split():
        try:
            address = ipaddress.ip_address(token)
        except ValueError:
            continue
        if address.version == 4 and address.is_private and not token.startswith(("10.", "172.17.")):
            return token
    raise RuntimeError(f"Cannot detect the WSL IPv4 address: {output!r}")


def clear_old_bridges() -> None:
    """Remove duplicate STK bridge children without touching gNB or UE."""
    needle = BRIDGE_SCRIPT.name.lower()
    for proc in psutil.process_iter(["pid", "cmdline"]):
        if proc.pid == psutil.Process().pid:
            continue
        try:
            command = " ".join(proc.info.get("cmdline") or []).lower()
            if needle in command:
                print(f"Stopping old STK bridge PID {proc.pid}", flush=True)
                proc.terminate()
                try:
                    proc.wait(5)
                except psutil.TimeoutExpired:
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def connect_log_receiver() -> socket.socket | None:
    try:
        connection = socket.create_connection(LOG_RECEIVER, timeout=3)
        connection.settimeout(5)
        print(f"STK log receiver connected: {LOG_RECEIVER[0]}:{LOG_RECEIVER[1]}", flush=True)
        return connection
    except OSError as exc:
        print(f"STK log receiver unavailable ({exc}); will retry", flush=True)
        return None


def terminate_bridge() -> None:
    global BRIDGE_PROCESS
    if BRIDGE_PROCESS is None or BRIDGE_PROCESS.poll() is not None:
        return
    BRIDGE_PROCESS.terminate()
    try:
        BRIDGE_PROCESS.wait(timeout=5)
    except subprocess.TimeoutExpired:
        BRIDGE_PROCESS.kill()


def main() -> int:
    global BRIDGE_PROCESS
    signal.signal(signal.SIGINT, stop_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, stop_signal)

    clear_old_bridges()
    wsl_ip = detect_wsl_ip()
    print(f"Detected WSL IP: {wsl_ip}", flush=True)
    print(f"STK targets: {GNB_TARGET}, {wsl_ip}:{UE_STK_PORT}, {LAN_STK_TARGET}", flush=True)

    command = [
        PYTHON_EXE,
        str(BRIDGE_SCRIPT),
        "--target", GNB_TARGET,
        "--target", f"{wsl_ip}:{UE_STK_PORT}",
        "--target", LAN_STK_TARGET,
        "--satellite", SATELLITE_PATH,
        "--rate-hz", str(RATE_HZ),
        "--status-interval", str(STATUS_INTERVAL),
        "--time-mode", TIME_MODE,
        "--speed", str(SPEED),
        "--rfsim-speed", str(RFSIM_SPEED),
    ]
    BRIDGE_PROCESS = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    connection: socket.socket | None = None
    try:
        assert BRIDGE_PROCESS.stdout is not None
        for line in BRIDGE_PROCESS.stdout:
            print(line, end="", flush=True)
            payload = line.encode("utf-8", errors="replace")
            while not STOP:
                try:
                    if connection is None:
                        connection = connect_log_receiver()
                        if connection is None:
                            time.sleep(2)
                            continue
                    connection.sendall(payload)
                    break
                except OSError:
                    if connection is not None:
                        connection.close()
                    connection = None
        return BRIDGE_PROCESS.wait()
    except KeyboardInterrupt:
        print("\nStopping STK bridge...", flush=True)
        return 0
    finally:
        terminate_bridge()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
