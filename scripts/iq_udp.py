"""由共享 IQ 样本时钟驱动的双向 UDP 探针；只依赖 Python 标准库。"""
import argparse
import json
import math
from pathlib import Path
import select
import signal
import socket
import struct
import time

HEADER = struct.Struct('!16sQd')
PAYLOAD_BYTES = 1200
RATE = 100000


def packet_budget(start: float, current: float) -> int:
    """按 UDP payload 计费，量化误差小于一个报文，不含 IP/UDP 头。"""
    if not math.isfinite(start) or not math.isfinite(current) or current < start:
        raise ValueError('invalid IQ clock')
    return math.floor((current - start) * RATE / (8 * PAYLOAD_BYTES))


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(path)


def summarize(sender: dict, receiver: dict) -> dict:
    sent = sender['sent']
    received = {int(row[0]) for row in receiver['received']}
    expected = set(range(len(sent)))
    missing = sorted(expected - received)
    iq_duration = sender['last_iq'] - sender['start_iq']
    wall_duration = sender['sending_wall_seconds']
    return {'clock': 'iq', 'payload_bytes': PAYLOAD_BYTES, 'target_bits_per_iq_second': RATE,
            'iq_seconds': iq_duration, 'seconds': wall_duration,
            'sent_packets': len(sent), 'packets': len(expected & received),
            'lost_packets': len(missing), 'missing_sequences': missing,
            'sent_minus_received_packets': len(missing),
            'unexpected_sequences': sorted(received - expected),
            'duplicate_packets': receiver.get('duplicates', 0),
            'invalid_packets': receiver.get('invalid', 0),
            'sent_bits_per_iq_second': len(sent) * PAYLOAD_BYTES * 8 / iq_duration if iq_duration else 0,
            'received_bits_per_iq_second': len(expected & received) * PAYLOAD_BYTES * 8 / iq_duration if iq_duration else 0,
            'bits_per_second': len(expected & received) * PAYLOAD_BYTES * 8 / wall_duration if wall_duration else 0,
            'missing_send_iq_s': [sent[index][1] for index in missing],
            'sender_error': sender.get('error'), 'receiver_error': receiver.get('error')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', required=True)
    parser.add_argument('--peer', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--clock', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--token', required=True)
    args = parser.parse_args()
    token = bytes.fromhex(args.token)
    if len(token) != 16:
        parser.error('token must contain 16 bytes')
    state = {'sent': [], 'received': [], 'duplicates': 0, 'invalid': 0,
             'start_iq': 0., 'last_iq': 0., 'sending_wall_seconds': 0.}
    stop_at = None

    def stop(signum: int, frame: object) -> None:
        nonlocal stop_at
        if stop_at is None:
            stop_at = time.monotonic()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))
    sock.setblocking(False)
    seen = set()
    started = None
    last_save = 0.
    previous = None
    write_json(args.report, {**state, 'ready': True, 'complete': False})
    try:
        while stop_at is None or time.monotonic() - stop_at < 5:
            now = time.monotonic()
            clock = json.loads(args.clock.read_text())
            current = float(clock['current'])
            start = float(clock['start'])
            budget = packet_budget(start, current)
            if previous is not None and current < previous:
                raise ValueError('IQ clock moved backwards')
            previous = current
            if clock.get('running') and stop_at is None:
                if started is None:
                    started = now
                    state['start_iq'] = start
                if state['start_iq'] != start:
                    raise ValueError('IQ clock origin changed')
                state['last_iq'] = current
                state['sending_wall_seconds'] = now - started
                while len(state['sent']) < budget:
                    seq = len(state['sent'])
                    packet = HEADER.pack(token, seq, current) + bytes(PAYLOAD_BYTES - HEADER.size)
                    # 成功发送后才计数；短暂队列拥堵留待下一轮，不丢弃预算。
                    try:
                        sock.sendto(packet, (args.peer, args.port))
                    except BlockingIOError:
                        break
                    state['sent'].append([seq, current, time.monotonic()])
            if select.select([sock], [], [], .01)[0]:
                while True:
                    try:
                        packet, source = sock.recvfrom(65535)
                    except BlockingIOError:
                        break
                    if len(packet) != PAYLOAD_BYTES or source != (args.peer, args.port):
                        state['invalid'] += 1
                        continue
                    identity, seq, send_iq = HEADER.unpack_from(packet)
                    if identity != token or not math.isfinite(send_iq):
                        state['invalid'] += 1
                    elif seq in seen:
                        state['duplicates'] += 1
                    else:
                        seen.add(seq)
                        state['received'].append([seq, send_iq, current, time.monotonic()])
            if now - last_save >= 1:
                write_json(args.report, {**state, 'ready': True, 'complete': False})
                last_save = now
    except Exception as error:
        state['error'] = str(error)
    finally:
        sock.close()
        write_json(args.report, {**state, 'ready': True, 'complete': True})
    return int('error' in state)


if __name__ == '__main__':
    raise SystemExit(main())
