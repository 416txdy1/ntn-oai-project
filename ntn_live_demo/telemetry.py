"""Numerical RFsim log observations; never forward arbitrary modem log text."""
import time
import re


class RadioTelemetry:
    def __init__(self, helpers, run):
        self.helpers=helpers
        self.readers={side:helpers.Lines(run/(side+'-live-demo.log')) for side in ('gnb','ue')}
        self.channels={}
        self.ports={};self.workers={};self.tx_ports=set()

    def poll(self):
        for side,reader in self.readers.items():
            for line in reader.read():
                ports=re.search(r'QDCHANNEL1 spatial ports: (\d+) Tx x (\d+) Rx',line)
                if ports:self.ports[side]={'tx':int(ports[1]),'rx':int(ports[2])}
                workers=re.search(r'QDCHANNEL1 compute workers: (\d+)',line)
                if workers:self.workers[side]=int(workers[1])
                energy=re.search(r'QDCHANNEL1 Tx port (\d+) IQ=\d+ mean_energy=([\d.]+)',line)
                if side=='gnb' and energy and float(energy[2])>0:self.tx_ports.add(int(energy[1]))
                match=self.helpers.PHYSICAL.search(line)
                if match:
                    direction,iq,stk,delay,doppler,gain,cn,valid=match.groups()
                    self.channels[direction.lower()]={
                        'iq_s':float(iq),'stk_s':float(stk),'delay_ms':float(delay),
                        'doppler_hz':float(doppler),'gain_db':float(gain),'cn_db':float(cn),
                        'valid':valid=='1','observed_host_monotonic_ns':time.monotonic_ns()}

    def snapshot(self, current_iq=None):
        now=time.monotonic_ns()
        return {direction:dict(value,age_ms=(now-value['observed_host_monotonic_ns'])/1e6,
                               lag_iq_s=None if current_iq is None else max(0,current_iq-value['iq_s']))
                for direction,value in self.channels.items()}

    def spatial_snapshot(self):
        return {'observed_ports':dict(self.ports),'observed_workers':dict(self.workers),
                'active_tx_ports':sorted(self.tx_ports)}
