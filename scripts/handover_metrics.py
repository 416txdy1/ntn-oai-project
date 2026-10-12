"""Shared IQ timeline and conservative evidence-based handover acceptance."""
import bisect
import math
from pathlib import Path
import re

CLOCK = re.compile(r'STKCLOCK (UL|DL) monotonic_ns=(\d+) samples=(\d+) sampling_rate=([\d.]+) iq_s=([\d.]+) stk_s=([\d.]+)')
NUMERIC = re.compile(r'STKTRACE2 (UL|DL) IQ=([\d.]+) STK=([\d.]+) delay=([\d.]+)ms Doppler=([-\d.]+)Hz gain=([-\d.]+)dB C/N=([-\d.]+)dB valid=(\d+) samples=(\d+)')
SCHEDULE = re.compile(r'STKSCHEDULE (UL|DL) IQ=([\d.]+) STK=([\d.]+) satellite_id=(\S+) elevation_deg=([-\d.]+) visible=(\d+) switched=(\d+) phase=(\S+) previous=(.*?) next=(.*?) samples=(\d+)')


def case_spec(case):
    if case not in ('full','firsthandover','static','legacy'):
        raise ValueError('unknown acceptance case')
    return dict(duration_iq_s=70 if case=='firsthandover' else 90 if case=='static' else 620,
                rate=0 if case=='static' else 1,
                trace_interval_s=[8200,8270 if case=='firsthandover' else 8820],
                completions=[] if case=='static' else [8244] if case=='firsthandover' else [8244,8799])


class IncrementalTail:
    """Read appended complete lines once; reject rotation/truncation."""
    def __init__(self,path):
        self.path=Path(path);self.identity=None;self.offset=0;self.partial=b''

    def read_lines(self):
        if not self.path.exists():
            if self.identity is not None:raise ValueError('log disappeared')
            return []
        stat=self.path.stat()
        identity=(stat.st_dev,stat.st_ino)
        if self.identity is not None and (identity!=self.identity or stat.st_size<self.offset):
            raise ValueError('log rotated or truncated')
        self.identity=identity
        with self.path.open('rb') as stream:
            stream.seek(self.offset)
            data=stream.read();self.offset=stream.tell()
        pieces=(self.partial+data).split(b'\n')
        self.partial=pieces.pop()
        return [line.decode('utf-8',errors='replace') for line in pieces]


def parse_clock(line):
    match=CLOCK.search(line)
    if not match:return None
    direction,ns,samples,fs,iq,stk=match.groups()
    return dict(direction=direction,monotonic_ns=int(ns),samples=int(samples),
                sampling_rate=float(fs),iq_s=float(iq),stk_s=float(stk))


class ClockMap:
    """Piecewise estimate plus observed bracketing range, never extrapolation."""
    def __init__(self,anchors,epoch,rate,fs,max_iq_gap=.15):
        if len(anchors)<2:raise ValueError('need bracketing clock anchors')
        self.anchors=anchors;self.ns=[a['monotonic_ns'] for a in anchors]
        self.epoch=epoch;self.rate=rate;self.fs=fs
        for index,a in enumerate(anchors):
            if not math.isfinite(a['sampling_rate']) or a['sampling_rate']!=fs:
                raise ValueError('clock sample rate disagreement')
            iq=a['samples']/fs
            if abs(a['iq_s']-iq)>1e-8 or abs(a['stk_s']-(epoch+rate*iq))>1e-8:
                raise ValueError('clock timestamp mapping disagreement')
            if index:
                previous=anchors[index-1]
                if a['monotonic_ns']<=previous['monotonic_ns'] or a['samples']<=previous['samples']:
                    raise ValueError('clock regression or repeated anchor')
                if (a['samples']-previous['samples'])/fs>max_iq_gap:
                    raise ValueError('IQ clock observation gap')
        self.max_iq_gap=max((b['samples']-a['samples'])/fs for a,b in zip(anchors,anchors[1:]))

    def map(self,ns):
        if ns<self.ns[0] or ns>self.ns[-1]:
            raise ValueError('event has no bracketing physical clock observations')
        index=min(len(self.anchors)-2,max(0,bisect.bisect_right(self.ns,ns)-1))
        a,b=self.anchors[index:index+2]
        lo,hi=a['samples']/self.fs,b['samples']/self.fs
        fraction=(ns-a['monotonic_ns'])/(b['monotonic_ns']-a['monotonic_ns'])
        iq=lo+fraction*(hi-lo)
        return dict(monotonic_ns=ns,iq_s=iq,stk_s=self.epoch+self.rate*iq,
                    iq_bounds_s=[lo,hi],stk_bounds_s=[self.epoch+self.rate*lo,self.epoch+self.rate*hi],
                    anchor_ns=[a['monotonic_ns'],b['monotonic_ns']],
                    anchor_samples=[a['samples'],b['samples']],
                    uncertainty_iq_s=hi-lo,
                    real_time_factor=(hi-lo)/((b['monotonic_ns']-a['monotonic_ns'])/1e9))


def cohort_summary(packets,start,end,axis='iq',wall_interval_s=None):
    if end<=start:raise ValueError('empty cohort interval')
    definite=[];ambiguous=[]
    for packet in packets:
        lo,hi=packet['send'][axis+'_bounds_s']
        if lo>=start and hi<=end: definite.append(packet)
        elif hi>=start and lo<=end:ambiguous.append(packet)
    missing=[p for p in definite if not p['received']]
    ambiguous_missing=[p for p in ambiguous if not p['received']]
    denominator=len(definite)+len(ambiguous_missing)
    upper=(len(missing)+len(ambiguous_missing))/denominator if denominator else None
    lower=len(missing)/(len(definite)+len(ambiguous)) if definite or ambiguous else None
    received=[p for p in definite if p['received']]
    received_bytes=sum(p['bytes'] for p in received)
    latency=[(p['receive_ns']-p['send_ns'])/1e6 for p in received]
    return dict(sent=len(definite),received=len(received),packets=len(definite),
                lost_packets=len(missing),eventual_missing=len(missing),
                definite_sent=len(definite),boundary_ambiguous_sent=len(ambiguous),
                boundary_ambiguous_missing=len(ambiguous_missing),
                loss_lower_bound=lower,loss_upper_bound=upper,
                success_lower_bound=1-upper if upper is not None else None,
                deadline_timeouts=sum(bool(p.get('deadline_timeout')) for p in definite),
                late_received=sum(bool(p.get('late_received')) for p in definite),
                received_bytes=received_bytes,
                observed_iq_bits_per_second=received_bytes*8/(end-start) if axis=='iq' else None,
                measured_wall_bits_per_second=received_bytes*8/wall_interval_s if wall_interval_s and wall_interval_s>0 else None,
                wall_latency_ms_mean=sum(latency)/len(latency) if latency else None,
                wall_jitter_ms_mean=sum(abs(b-a) for a,b in zip(latency,latency[1:]))/(len(latency)-1) if len(latency)>1 else None,
                observation_ok=bool(definite))


def evaluate_handover(report):
    """Fail closed on missing/invalid evidence, with unchanged full thresholds."""
    reasons=[]
    def require(condition,message):
        if not condition:reasons.append(message)
    try:
        spec=case_spec(report['case'])
        require(report['qd_enabled']==(report['case']!='legacy'),'unexpected QD state')
        require(report['profile']==('legacy-handover' if report['case']=='legacy' else 'integrated-handover'),'unexpected profile')
        require(report['rate']==spec['rate'],'unexpected replay rate')
        require(report['trace_interval_s']==spec['trace_interval_s'],'unexpected trace interval')
        fs=report['sample_rate_hz']
        require(isinstance(fs,(int,float)) and math.isfinite(fs) and fs>0,'invalid actual Fs')
        for side in ('gnb','ue'):
            require(report['clock_sample_rates'][side]==fs,'actual Fs mismatch: '+side)
            begin,end=report['iq_interval_s'][side]
            require(begin<=.15 and end>=spec['duration_iq_s'],'incomplete IQ coverage: '+side)
            require(report['iq_end_stk_s'][side]>=spec['trace_interval_s'][0]+spec['rate']*spec['duration_iq_s'],'incomplete STK coverage: '+side)
        if report['case']=='static':
            require(report['pdu_ready_iq_s']<spec['duration_iq_s']-30,'late static PDU')
            require(report['traffic_ready_iq_s']<spec['duration_iq_s']-30,'late static business')
            require(report['business_iq_interval_s'][1]-report['business_iq_interval_s'][0]>=30,'static business duration below30 IQ seconds')
        else:
            require(report['pdu_ready_stk_s']<8239,'PDU not ready before first window')
            require(report['traffic_ready_stk_s']<8239,'business not ready before first window')
        for field in ('pdu_address_changes','pbch_errors','rrc_idle','reaccess_count'):
            require(report[field]==0,field+' is nonzero')
        for field in ('numeric_audit_ok','clock_observation_ok','worker_observation_ok'):
            require(report[field] is True,field+' failed')
        require(report['stop_exit']==0,'owned stop failed')
        windows=report['windows']
        require(len(windows)==len(spec['completions']),'wrong number of switch windows')
        checks=[('global ping',report['ping'])]
        checks.extend(('global '+d,report['udp'][d]) for d in ('uplink','downlink'))
        for window,complete in zip(windows,spec['completions']):
            require(window['complete_stk_s']==complete and window['start_stk_s']==complete-5 and window['end_stk_s']==complete+5,'wrong switch window')
            require(window['coverage_ok'] is True,'incomplete switch window')
            checks.append(('window ping',window['ping']))
            checks.extend(('window '+d,window['udp'][d]) for d in ('uplink','downlink'))
        for label,value in checks:
            require(value['observation_ok'] is True and value['definite_sent']>0 and value['sent']>0,label+' has no certain matched senders')
            require(0<=value['received']<=value['sent'],label+' invalid counters')
            loss=value['loss_upper_bound']
            require(isinstance(loss,(int,float)) and math.isfinite(loss) and 0<=loss<=.01,label+' conservative loss exceeds1%')
            require(value['lost_packets']==value['sent']-value['received'],label+' inconsistent final loss')
            ambiguous_missing=value.get('boundary_ambiguous_missing',0)
            require(isinstance(ambiguous_missing,int) and ambiguous_missing>=0,label+' invalid ambiguous missing count')
            certain=value['definite_sent']
            require(certain==value['sent'],label+' inconsistent definite senders')
            computed=(value['lost_packets']+ambiguous_missing)/(certain+ambiguous_missing) if certain+ambiguous_missing else None
            require(computed is not None and loss is not None and abs(loss-computed)<1e-12,label+' unsubstantiated loss bound')
    except (KeyError,TypeError,ValueError,IndexError) as error:
        reasons.append('missing or invalid evidence: '+str(error))
    return reasons
