#!/usr/bin/env python3
"""Forward the exported STK CSV to the LAN receiver.

The CSV is a snapshot. It is sent once at startup; use --watch if the
exporter may replace the file during a long-running display session.
"""
from __future__ import annotations
import argparse, socket, time
from pathlib import Path

TARGET = ("10.29.132.223", 9002)

def send_file(path: Path) -> None:
    with socket.create_connection(TARGET, timeout=5) as sock:
        with path.open("rb") as src:
            while True:
                block = src.read(65536)
                if not block:
                    break
                sock.sendall(block)
    print(f"sent {path} to {TARGET[0]}:{TARGET[1]}", flush=True)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file", type=Path, default=Path("local_ntn/stk_trace.csv"))
    p.add_argument("--watch", action="store_true")
    p.add_argument("--interval", type=float, default=1.0)
    a = p.parse_args()
    last = None
    while True:
        stat = a.file.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if stamp != last:
            send_file(a.file)
            last = stamp
        if not a.watch:
            return
        time.sleep(a.interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("CSV forwarding stopped.")
