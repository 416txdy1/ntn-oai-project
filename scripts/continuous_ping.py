"""Continuous ICMP evidence with persistent deadlines and bounded final draining."""
import argparse
import select
import signal
import socket
import time
from continuous_udp import EventWriter
from monotonic_ping import make_request,parse_reply
from pathlib import Path
import os


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',required=True);p.add_argument('--interface',required=True)
    p.add_argument('--events',type=Path,required=True)
    p.add_argument('--interval',type=float,default=1);p.add_argument('--timeout',type=float,default=5)
    a=p.parse_args(argv)
    if a.interval<=0 or a.timeout<=0:p.error('positive interval/timeout required')
    nonce=os.urandom(8);sent={};received=set();expired=set()
    sending=True;stop_ns=None
    def stop(_signal,_frame):
        nonlocal sending,stop_ns
        if sending:sending=False;stop_ns=time.monotonic_ns()
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    writer=EventWriter(a.events,'ping');failed=False;next_send=0;next_heartbeat=0
    try:
        try:sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_ICMP)
        except PermissionError:sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_ICMP)
        with sock:
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,a.interface.encode()+b'\0')
            sock.setblocking(False);writer.emit('ready',destination=a.destination,interface=a.interface)
            while True:
                now=time.monotonic_ns()
                if now>=next_heartbeat:writer.emit('heartbeat');next_heartbeat=now+1_000_000_000
                if sending and now>=next_send:
                    seq=len(sent)+1;send_ns=time.monotonic_ns()
                    wire=make_request(seq,send_ns,nonce)
                    if sock.sendto(wire,(a.destination,0))!=len(wire):raise RuntimeError('partial ICMP send')
                    sent[seq]=send_ns
                    writer.emit('send',sequence=seq,send_ns=send_ns,bytes=len(wire),deadline_ns=send_ns+int(a.timeout*1e9))
                    next_send=now+int(a.interval*1e9)
                for seq,timestamp in sent.items():
                    if seq not in received and seq not in expired and now>=timestamp+int(a.timeout*1e9):
                        expired.add(seq);writer.emit('timeout',sequence=seq,send_ns=timestamp,deadline_ns=timestamp+int(a.timeout*1e9))
                if not sending and (len(received)==len(sent) or now>=stop_ns+int(a.timeout*1e9)):break
                ready,_,_=select.select([sock],[],[],.05)
                if ready:
                    data,address=sock.recvfrom(4096);receive_ns=time.monotonic_ns()
                    decoded=parse_reply(data,nonce)
                    if not decoded or address[0]!=a.destination:continue
                    seq,timestamp=decoded
                    if sent.get(seq)!=timestamp:writer.emit('rejected');continue
                    writer.emit('receive',sequence=seq,send_ns=timestamp,receive_ns=receive_ns,
                                bytes=64,wall_rtt_ms=(receive_ns-timestamp)/1e6,duplicate=seq in received,
                                late=receive_ns>timestamp+int(a.timeout*1e9))
                    received.add(seq)
    except Exception as error:
        failed=True;writer.emit('error',reason=str(error))
    finally:
        writer.emit('end',sent=len(sent),received=len(received),failed=failed,deadline_timeouts=len(expired))
        writer.close()
    return int(failed)

if __name__=='__main__':raise SystemExit(main())
