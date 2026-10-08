"""使用 monotonic_ns 测量本地实验 ICMP，SIGINT 后停止发送并等待在途回复。"""
import argparse
import json
import os
import select
import signal
import socket
import struct
import time

MAGIC = b'NTNMONO1'


def checksum(data):
    if len(data) % 2:
        data += b'\0'
    total = sum(struct.unpack('!' + 'H' * (len(data)//2), data))
    while total >> 16:
        total = (total & 65535) + (total >> 16)
    return ~total & 65535


def make_request(sequence, timestamp, nonce):
    payload = MAGIC + nonce + struct.pack('!IQ', sequence, timestamp) + bytes(28)
    header = struct.pack('!BBHHH', 8, 0, 0, 0, sequence & 65535)
    return struct.pack('!BBHHH', 8, 0, checksum(header + payload), 0, sequence & 65535) + payload


def parse_reply(data, nonce):
    # SOCK_RAW 带 IPv4 首部，SOCK_DGRAM 直接返回 ICMP。
    if data and data[0] >> 4 == 4:
        ihl = (data[0] & 15) * 4
        if ihl < 20 or len(data) < ihl + 8:
            return None
        data = data[ihl:]
    if len(data) < 36 or data[0] != 0 or data[1] != 0:
        return None
    if data[8:16] != MAGIC or data[16:24] != nonce:
        return None
    return struct.unpack('!IQ', data[24:36])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--interface', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--interval', type=float, default=1)
    parser.add_argument('--count', type=int, default=0)
    parser.add_argument('--timeout', type=float, default=5)
    args = parser.parse_args()
    if args.interval <= 0 or args.timeout <= 0 or args.count < 0:
        parser.error('invalid count/interval/timeout')
    socket.inet_aton(args.destination)
    sending = True
    stop_time = None
    def stop(_signal, _frame):
        nonlocal sending, stop_time
        if sending:
            sending = False
            stop_time = time.monotonic()
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    nonce = os.urandom(8)
    sent, received = {}, {}
    started = time.monotonic()
    next_send = started
    try:
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP)
    except PermissionError:
        # 新 netns 的 ping_group_range 可能禁用 datagram ping；root 用 CAP_NET_RAW。
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    with icmp_socket as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, args.interface.encode() + b'\0')
        sock.setblocking(False)
        while True:
            now = time.monotonic()
            if sending and now >= next_send:
                sequence = len(sent) + 1
                timestamp = time.monotonic_ns()
                sock.sendto(make_request(sequence, timestamp, nonce), (args.destination, 0))
                sent[sequence] = timestamp
                next_send = now + args.interval
                if args.count and sequence >= args.count:
                    stop(None, None)
            if not sending and (len(received) == len(sent) or now - stop_time >= args.timeout):
                break
            ready, _, _ = select.select([sock], [], [], .05)
            if ready:
                data, address = sock.recvfrom(4096)
                parsed = parse_reply(data, nonce)
                if not parsed or address[0] != args.destination:
                    continue
                sequence, timestamp = parsed
                if sent.get(sequence) != timestamp or sequence in received:
                    continue
                rtt = (time.monotonic_ns() - timestamp)/1e6
                received[sequence] = rtt
                print(f'64 bytes from {args.destination}: icmp_seq={sequence} time={rtt:.3f} ms (monotonic)', flush=True)
    missing = sorted(set(sent) - set(received))
    values = list(received.values())
    report = {'clock': 'CLOCK_MONOTONIC', 'sent': len(sent), 'received': len(received),
              'missing_sequences': missing, 'drain_timeout_s': args.timeout,
              'wall_monotonic_seconds': time.monotonic()-started,
              'rtt_ms': {'min': min(values), 'mean': sum(values)/len(values), 'max': max(values)} if values else None}
    with open(args.report, 'w') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report), flush=True)
    return 0 if sent and not missing else 1


if __name__ == '__main__':
    raise SystemExit(main())
