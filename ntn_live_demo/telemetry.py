"""Numerical RFsim log observations; never forward arbitrary modem log text."""
import time


class RadioTelemetry:
    def __init__(self, helpers, run):
        self.helpers=helpers
        self.readers={side:helpers.Lines(run/(side+'-live-demo.log')) for side in ('gnb','ue')}
        self.channels={}

    def poll(self):
        for reader in self.readers.values():
            for line in reader.read():
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
