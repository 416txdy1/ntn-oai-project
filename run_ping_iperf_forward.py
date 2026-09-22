#!/usr/bin/env python3
"""Forward ping and iperf3 logs after dynamically detecting oaitun_ue1."""

from __future__ import annotations

import queue
import re
import signal
import socket
import subprocess
import threading
import time


WSL_DISTRO = "Ubuntu-22.04"
TUN_INTERFACE = "oaitun_ue1"
LOG_RECEIVER = ("10.129.137.101", 9001)

PING_TARGET = "10.0.0.1"
PING_INTERVAL_SECONDS = 1

IPERF_SERVER = "192.168.70.135"
IPERF_MODE = "udp"                # "udp" or "tcp"
IPERF_BANDWIDTH = "100K"          # UDP only
IPERF_DURATION_SECONDS = 30
IPERF_REPORT_INTERVAL = 5
IPERF_REPEAT_SECONDS = 0           # 0 = once; e.g. 60 = repeat every 60 s

STOP = threading.Event()
INTERRUPTS = 0
CHILDREN: list[subprocess.Popen] = []


def stop_signal(signum, frame) -> None:
    del signum, frame
    global INTERRUPTS
    INTERRUPTS += 1
    STOP.set()
    if INTERRUPTS == 1:
        raise KeyboardInterrupt
    raise SystemExit(130)


def wsl_base() -> list[str]:
    return ["wsl.exe", "-d", WSL_DISTRO, "--"]


def wsl_capture(command: str) -> str:
    result = subprocess.run(
        wsl_base() + ["bash", "--noprofile", "--norc", "-lc", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    return result.stdout


def clear_old_measurements() -> None:
    subprocess.run(
        ["wsl.exe", "-d", WSL_DISTRO, "-u", "root", "--", "bash", "-lc",
         "pkill -INT -x ping 2>/dev/null || true; pkill -INT -x iperf3 2>/dev/null || true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )


def wait_for_ue_ip() -> str:
    pattern = re.compile(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/")
    last_notice = 0.0
    while not STOP.is_set():
        output = wsl_capture(f"ip -4 -o addr show dev {TUN_INTERFACE} 2>/dev/null || true")
        match = pattern.search(output)
        if match:
            return match.group(1)
        if time.monotonic() - last_notice >= 10:
            print(f"Waiting for {TUN_INTERFACE}; start gNB and UE manually...", flush=True)
            last_notice = time.monotonic()
        STOP.wait(1)
    raise KeyboardInterrupt


class Forwarder:
    def __init__(self) -> None:
        self.q: queue.Queue[str | None] = queue.Queue(maxsize=10000)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def write(self, tag: str, text: str) -> None:
        text = text.rstrip("\r\n")
        if not text:
            return
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{tag}] {text}"
        print(line, flush=True)
        try:
            self.q.put_nowait(line + "\n")
        except queue.Full:
            print("Measurement log queue full", flush=True)

    def _run(self) -> None:
        connection: socket.socket | None = None
        while not STOP.is_set():
            try:
                item = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                break
            payload = item.encode("utf-8", errors="replace")
            while not STOP.is_set():
                try:
                    if connection is None:
                        connection = socket.create_connection(LOG_RECEIVER, timeout=3)
                        connection.settimeout(5)
                    connection.sendall(payload)
                    break
                except OSError:
                    if connection is not None:
                        connection.close()
                    connection = None
                    time.sleep(2)
        if connection is not None:
            connection.close()

    def close(self) -> None:
        try:
            self.q.put_nowait(None)
        except queue.Full:
            pass
        self.thread.join(timeout=2)


def is_wsl_launcher_noise(line: str) -> bool:
    """Hide WSL's Windows-PATH conversion warnings, not tool errors."""
    return (
        "Failed to translate" in line
        or line.lstrip().startswith("wsl:")
        or "\ufffd" in line
        or "\x00" in line
    )


def read_output(stream, tag: str, forwarder: Forwarder, filter_wsl_noise: bool = False) -> None:
    for line in stream:
        if filter_wsl_noise and is_wsl_launcher_noise(line):
            continue
        forwarder.write(tag, line)


def start_child(command: list[str], tag: str, forwarder: Forwarder) -> subprocess.Popen:
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None and proc.stderr is not None
    CHILDREN.append(proc)
    threading.Thread(target=read_output, args=(proc.stdout, tag, forwarder), daemon=True).start()
    threading.Thread(
        target=read_output,
        args=(proc.stderr, tag, forwarder, True),
        daemon=True,
    ).start()
    return proc


def wait_for_data_plane(forwarder: Forwarder) -> bool:
    """Do not start iperf until the UE gateway responds through the tunnel."""
    while not STOP.is_set():
        probe = subprocess.run(
            wsl_base() + ["ping", "-I", TUN_INTERFACE, "-c", "1", "-W", "5", PING_TARGET],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
        if probe.returncode == 0:
            forwarder.write("SYSTEM", f"Data plane reachable at {PING_TARGET}; starting iperf3")
            return True
        forwarder.write("SYSTEM", f"Data plane cannot reach {PING_TARGET}; iperf3 delayed")
        if STOP.wait(5):
            return False
    return False


def run_iperf(ue_ip: str, forwarder: Forwarder) -> None:
    while not STOP.is_set():
        if not wait_for_data_plane(forwarder):
            return
        command = wsl_base() + [
            "iperf3", "-c", IPERF_SERVER, "-B", ue_ip,
            "-t", str(IPERF_DURATION_SECONDS),
            "-i", str(IPERF_REPORT_INTERVAL),
            "--connect-timeout", "10000",
        ]
        if IPERF_MODE.lower() == "udp":
            command += ["-u", "-b", IPERF_BANDWIDTH]
        proc = start_child(command, "IPERF", forwarder)
        while proc.poll() is None and not STOP.wait(0.5):
            pass
        forwarder.write("SYSTEM", f"iperf3 exited with code {proc.poll()}")
        if IPERF_REPEAT_SECONDS <= 0 or STOP.wait(IPERF_REPEAT_SECONDS):
            return


def terminate_children() -> None:
    for proc in reversed(CHILDREN):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    clear_old_measurements()


def main() -> int:
    signal.signal(signal.SIGINT, stop_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, stop_signal)

    clear_old_measurements()
    forwarder = Forwarder()
    try:
        forwarder.write("SYSTEM", f"Waiting for dynamic IP on {TUN_INTERFACE}")
        ue_ip = wait_for_ue_ip()
        forwarder.write("SYSTEM", f"Detected UE IP {ue_ip}")

        start_child(
            wsl_base() + ["ping", "-I", TUN_INTERFACE, "-i", str(PING_INTERVAL_SECONDS), PING_TARGET],
            "PING",
            forwarder,
        )
        threading.Thread(target=run_iperf, args=(ue_ip, forwarder), daemon=True).start()
        forwarder.write("SYSTEM", "Ping/iperf forwarding active; press Ctrl-C to stop")
        while not STOP.wait(1):
            pass
        return 0
    except KeyboardInterrupt:
        forwarder.write("SYSTEM", "Stopping ping and iperf forwarding")
        return 0
    finally:
        STOP.set()
        terminate_children()
        forwarder.close()


if __name__ == "__main__":
    raise SystemExit(main())
