#!/usr/bin/env python3
"""Receive ping and iperf text logs from run_ping_iperf_forward.py."""

import socket


HOST = "0.0.0.0"
PORT = 9001
BUFFER_SIZE = 4096


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"Waiting for ping/iperf logs on TCP {HOST}:{PORT} ...", flush=True)

        # Keep listening after the sender is stopped or restarted.
        while True:
            conn, addr = server.accept()
            print(f"Connected: {addr}", flush=True)
            try:
                with conn, conn.makefile(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                    newline="",
                ) as stream:
                    # Reading as text lines avoids TCP packet splitting/sticking
                    # and handles UTF-8 characters split across recv() calls.
                    for line in stream:
                        print(line, end="", flush=True)
            except (ConnectionError, OSError) as exc:
                print(f"Connection lost: {exc}", flush=True)
            print("Sender disconnected; waiting for reconnection...", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPing/iperf log receiver stopped.")
