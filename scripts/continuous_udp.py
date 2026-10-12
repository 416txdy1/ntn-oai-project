"""Continuous real UDP sender/receiver; host CLOCK_MONOTONIC, private JSONL evidence."""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import time

MAGIC=b'NTNUDP01'
HEADER=struct.Struct('!8s8sBQQ')
DIRECTIONS={'uplink':1,'downlink':2}


def encode_packet(token,direction,sequence,send_ns,size):
    if len(token)!=8 or direction not in DIRECTIONS or sequence<1 or size<HEADER.size or size>1400:
        raise ValueError('invalid UDP packet arguments')
    return HEADER.pack(MAGIC,token,DIRECTIONS[direction],sequence,send_ns)+bytes(size-HEADER.size)


def decode_packet(data,token,direction):
    if len(data)<HEADER.size:raise ValueError('truncated probe packet')
    magic,run,side,sequence,ns=HEADER.unpack_from(data)
    if magic!=MAGIC or run!=token or side!=DIRECTIONS[direction] or sequence<1:
        raise ValueError('foreign probe packet')
    return sequence,ns,len(data)


def match_events(sends,receives,deadline_ns,drain_end_ns):
    if receives is None:raise ValueError('missing receiver evidence')
    sent={}
    for event in sends:
        if event.get('event')!='send':continue
        seq=event['sequence']
        if seq in sent:raise ValueError('duplicate sender sequence')
        sent[seq]=dict(sequence=seq,send_ns=event['send_ns'],bytes=event['bytes'],received=False,
                       receive_ns=None,deadline_timeout=True,late_received=False)
    seen=set();unknown=duplicates=out_of_order=0;maximum=0
    for event in receives:
        if event.get('event')!='receive' or event.get('receive_ns',event['monotonic_ns'])>drain_end_ns:continue
        seq=event['sequence'];packet=sent.get(seq)
        if packet is None or event['send_ns']!=packet['send_ns'] or event['bytes']!=packet['bytes']:
            unknown+=1;continue
        if event.get('receive_ns',event['monotonic_ns'])<packet['send_ns']:raise ValueError('negative packet transit time')
        if seq in seen:duplicates+=1;continue
        if seq<maximum:out_of_order+=1
        maximum=max(maximum,seq);seen.add(seq)
        receive_ns=event.get('receive_ns',event['monotonic_ns']);late=receive_ns>packet['send_ns']+deadline_ns
        packet.update(received=True,receive_ns=receive_ns,deadline_timeout=late,late_received=late)
    return dict(packets=[sent[x] for x in sorted(sent)],unknown_receives=unknown,
                duplicates=duplicates,out_of_order=out_of_order)


class EventWriter:
    def __init__(self,path,role):
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        self.stream=os.fdopen(fd,'w',buffering=1);self.role=role

    def emit(self,event,**values):
        row=dict(event=event,role=self.role,monotonic_ns=time.monotonic_ns(),**values)
        self.stream.write(json.dumps(row,separators=(',',':'))+'\n')
        return row

    def close(self):self.stream.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role',choices=('sender','receiver'))
    parser.add_argument('--bind',required=True)
    parser.add_argument('--peer',required=True)
    parser.add_argument('--port',type=int,required=True)
    parser.add_argument('--direction',choices=DIRECTIONS,required=True)
    parser.add_argument('--token',required=True)
    parser.add_argument('--events',type=Path,required=True)
    parser.add_argument('--payload-bytes',type=int,default=1000)
    parser.add_argument('--wall-bits-per-second',type=int,default=100000)
    args=parser.parse_args(argv)
    token=bytes.fromhex(args.token)
    encode_packet(token,args.direction,1,1,args.payload_bytes)
    if args.wall_bits_per_second!=100000:parser.error('new acceptance requires100000 offered wall bit/s')
    socket.inet_aton(args.bind);socket.inet_aton(args.peer)
    running=True
    def stop(_sig,_frame):
        nonlocal running
        running=False
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    writer=EventWriter(args.events,args.role)
    sequence=0;failed=False;next_heartbeat=0
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.bind((args.bind,args.port if args.role=='receiver' else 0))
            sock.setblocking(False)
            writer.emit('ready',bind=args.bind,peer=args.peer,port=args.port,direction=args.direction,
                        offered_wall_bits_per_second=args.wall_bits_per_second,payload_bytes=args.payload_bytes)
            interval=args.payload_bytes*8/args.wall_bits_per_second
            next_send=time.monotonic()
            while running:
                now=time.monotonic()
                if now>=next_heartbeat:
                    writer.emit('heartbeat');next_heartbeat=now+1
                if args.role=='sender':
                    if now>=next_send:
                        sequence+=1;send_ns=time.monotonic_ns()
                        wire=encode_packet(token,args.direction,sequence,send_ns,args.payload_bytes)
                        written=sock.sendto(wire,(args.peer,args.port))
                        if written!=len(wire):raise RuntimeError('partial UDP datagram')
                        writer.emit('send',sequence=sequence,send_ns=send_ns,bytes=len(wire))
                        # No catch-up burst: measure actual observed offered rate too.
                        next_send=now+interval
                    time.sleep(min(.01,max(0,next_send-time.monotonic())))
                else:
                    ready,_,_=select.select([sock],[],[],.05)
                    if ready:
                        data,peer=sock.recvfrom(65536)
                        receive_ns=time.monotonic_ns()
                        try:
                            seq,send_ns,size=decode_packet(data,token,args.direction)
                            if peer[0]!=args.peer:raise ValueError('foreign source IP')
                        except ValueError:
                            writer.emit('rejected');continue
                        # Source emission time remains explicit; writer time is separate.
                        writer.emit('receive',sequence=seq,send_ns=send_ns,receive_ns=receive_ns,bytes=size)
    except Exception as error:
        failed=True;writer.emit('error',reason=str(error))
    finally:
        writer.emit('end',sent=sequence,failed=failed);writer.close()
    return int(failed)


if __name__=='__main__':raise SystemExit(main())

