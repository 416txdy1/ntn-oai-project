#!/usr/bin/env python3
"""Receive forwarded OAI/STK text logs over a selectable TCP port."""

import argparse
import socket


HOST = "0.0.0.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Receive forwarded OAI/STK logs")
    parser.add_argument("--host", default=HOST, help="listen address")
    parser.add_argument("--port", type=int, required=True, help="9000=STK, 9001=ping/iperf")
    parser.add_argument("--name", default="LOG", help="short name shown in connection messages")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen(5)
        print(f"[{args.name}] Waiting on TCP {args.host}:{args.port} ...", flush=True)

        # Keep accepting after the sender restarts or temporarily disconnects.
        while True:
            conn, addr = server.accept()
            print(f"[{args.name}] Connected: {addr}", flush=True)
            try:
                with conn, conn.makefile("r", encoding="utf-8", errors="replace", newline="") as stream:
                    # TextIOWrapper handles both split UTF-8 characters and
                    # TCP packets containing multiple log lines.
                    for line in stream:
                        print(line, end="", flush=True)
            except (ConnectionError, OSError) as exc:
                print(f"[{args.name}] Connection lost: {exc}", flush=True)
            print(f"[{args.name}] Sender disconnected; waiting for reconnection...", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nReceiver stopped.")
