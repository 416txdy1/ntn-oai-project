#!/usr/bin/env python3
"""Receive STK logs, ping/iperf logs, and the exported CSV on one host."""
from __future__ import annotations
import socket, threading
from pathlib import Path

HOST = "0.0.0.0"
STREAMS = {
    9000: ("STK", Path("received_stk.log")),
    9001: ("TEST", Path("received_ping_iperf.log")),
    9002: ("CSV", Path("received_stk_trace.csv")),
}

def serve(port: int, name: str, output: Path) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, port)); server.listen(5)
        print(f"[{name}] listening on {HOST}:{port}, saving {output}", flush=True)
        while True:
            conn, addr = server.accept()
            print(f"[{name}] connected from {addr}", flush=True)
            try:
                # CSV is binary-safe; text logs are UTF-8. Appending allows
                # the STK/test senders to reconnect without stopping display.
                mode = "ab" if name == "CSV" else "a"
                with conn, output.open(mode) as dst:
                    while True:
                        data = conn.recv(65536)
                        if not data: break
                        if name == "CSV":
                            dst.write(data); dst.flush()
                            print(data.decode("utf-8", "replace"), end="", flush=True)
                        else:
                            text = data.decode("utf-8", "replace")
                            dst.write(text); dst.flush()
                            print(text, end="", flush=True)
            except OSError as exc:
                print(f"[{name}] connection lost: {exc}", flush=True)
            print(f"[{name}] sender disconnected; waiting", flush=True)

def main() -> None:
    for port, (name, output) in STREAMS.items():
        threading.Thread(target=serve, args=(port, name, output), daemon=True).start()
    print("Receiving on TCP 9000/9001/9002; press Ctrl+C to stop.", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nReceiver stopped.")

if __name__ == "__main__":
    main()
