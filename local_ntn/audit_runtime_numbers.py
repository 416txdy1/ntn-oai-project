"""Independent numerical audit of three STK interpolation modes and observed IQ Fs."""
import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
import re

C=299792458.0
PATTERN=re.compile(r'STKTRACE2 (UL|DL) IQ=([\d.]+) STK=([\d.]+) delay=([\d.]+)ms Doppler=([-\d.]+)Hz gain=([-\d.]+)dB C/N=([-\d.]+)dB valid=(\d+) samples=(\d+)')
LIMITS={'iq_s':5.1e-7,'stk_s':5.1e-7,'delay_ms':5.1e-7,'doppler_hz':5.1e-4,'gain_db':5.1e-4,'cn_db':5.1e-4}


def read_rows(path):
    return [list(map(float,row)) for row in csv.reader(line for line in Path(path).read_text().splitlines()[1:] if line and not line.startswith('#'))]


def interpolate(rows,t,mode='hermite'):
    if mode not in ('hermite','blend-aware','legacy-linear'):raise ValueError('unknown interpolation')
    times=[r[0] for r in rows]
    if not times[0]<=t<=times[-1]:raise ValueError('numeric trace out of range')
    index=max(0,min(len(rows)-2,bisect.bisect_right(times,t)-1))
    x,y=rows[index:index+2];h=y[0]-x[0];u=(t-x[0])/h
    r=[left+u*(right-left) for left,right in zip(x,y)]
    if mode=='legacy-linear':return r
    for k in range(3):
        d=x[1+k];v=h*x[4+k]
        b=3*(y[1+k]-d)-h*(2*x[4+k]+y[4+k])
        aa=2*(d-y[1+k])+h*(x[4+k]+y[4+k])
        r[1+k]=((aa*u+b)*u+v)*u+d
        r[4+k]=(3*aa*u*u+2*b*u+v)/h
    if mode=='blend-aware' and math.dist(x[1:4],y[1:4])/h>20000:
        r[4:7]=[left+u*(right-left) for left,right in zip(x[4:7],y[4:7])]
    return r


def geometry(row,rate):
    rg=math.dist(row[1:4],row[10:13]);ru=math.dist(row[1:4],row[13:16])
    vr=sum((row[1+k]-row[13+k])*row[4+k] for k in range(3))/ru*rate
    return (rg+ru)/C*1000,vr,ru/C*1000


def audit_log(rows,text,direction,fs,epoch,rate,mode):
    if not math.isfinite(fs) or fs<=0:raise ValueError('invalid observed sampling rate')
    if 'STKTRACE2 interpolation=' in text and 'STKTRACE2 interpolation='+mode not in text:
        raise ValueError('recorded interpolation mismatch')
    matches=list(PATTERN.finditer(text))
    if not matches:raise ValueError('no numeric channel log')
    maxima=dict.fromkeys(LIMITS,0.0);iq_times=[];stk_times=[]
    for match in matches:
        side,iq,stk,delay,doppler,gain,cn,valid,samples=match.groups()
        if side!=direction or valid!='1':raise ValueError('wrong direction or invalid channel inside trace')
        iq_exact=int(samples)/fs;t=epoch+rate*iq_exact
        row=interpolate(rows,t,mode);expected_delay,vr,_=geometry(row,rate)
        frequency=1614900000 if side=='UL' else 2488400000
        expected_doppler=-vr/(C if side=='UL' else C+vr)*frequency
        power_index,cn_index=(17,19) if side=='UL' else (16,18)
        errors=dict(iq_s=abs(float(iq)-iq_exact),stk_s=abs(float(stk)-t),
                    delay_ms=abs(float(delay)-expected_delay),doppler_hz=abs(float(doppler)-expected_doppler),
                    gain_db=abs(float(gain)-(row[power_index]-rows[0][power_index])),
                    cn_db=abs(float(cn)-row[cn_index]))
        for key,value in errors.items():
            maxima[key]=max(maxima[key],value)
            if value>LIMITS[key]:raise ValueError('numeric '+key+' error exceeds rounding tolerance')
        iq_times.append(iq_exact);stk_times.append(t)
    return dict(checked_rows=len(matches),iq_interval_s=[min(iq_times),max(iq_times)],
                stk_interval_s=[min(stk_times),max(stk_times)],max_abs_errors=maxima)


def audit_manifest(path):
    from experiment import observed_sample_rate
    manifest=json.loads(Path(path).read_text())
    trace=Path(manifest['trace'])
    if hashlib.sha256(trace.read_bytes()).hexdigest()!=manifest['trace_sha256']:
        raise ValueError('runtime trace hash mismatch')
    if manifest.get('schedule'):
        if hashlib.sha256(Path(manifest['schedule']).read_bytes()).hexdigest()!=manifest['schedule_sha256']:
            raise ValueError('runtime schedule hash mismatch')
    for bundle in manifest.get('bundles',{}).values():
        for relative,expected in bundle['files'].items():
            if hashlib.sha256((Path(bundle['path'])/relative).read_bytes()).hexdigest()!=expected:
                raise ValueError('runtime bundle hash mismatch')
    rows=read_rows(trace);fs=manifest['sample_rate_hz']
    if manifest['epoch']!=rows[0][0]:raise ValueError('manifest epoch mismatch')
    logs={side:Path(manifest['logs'][side]).read_text(errors='replace') for side in ('gnb','ue')}
    if observed_sample_rate(logs)!=fs:raise ValueError('manifest/startup sampling rate disagreement')
    result=dict(sampling_rate_hz=fs,trace_rows=len(rows),trace_interval_s=[rows[0][0],rows[-1][0]],runs={})
    result['runs'][manifest['run_id']]={side:audit_log(rows,logs[side],direction,fs,manifest['epoch'],manifest['rate'],manifest['interpolation'])
                                      for side,direction in [('gnb','UL'),('ue','DL')]}
    result['initial_config']=audit_initial(rows,manifest['gnb_config'],manifest['initial_delay_file'],
                                          manifest.get('initial_lead_rfsim',0),manifest['rate'],manifest['interpolation'])
    result['tolerances_log_rounding']=LIMITS
    return result


def audit_initial(rows,config_path,delay_path,lead=0,rate=0,mode='hermite'):
    row=interpolate(rows,rows[0][0]+lead*rate,mode)
    rg=math.dist(row[1:4],row[10:13]);delay=geometry(row,rate)[0]
    expected_ta=round(2*rg/C/4.072e-9)
    actual_ta=int(re.search(r'\bta-Common-r17\s*=\s*(\d+)',Path(config_path).read_text())[1])
    initial=float(Path(delay_path).read_text())
    if actual_ta!=expected_ta or abs(initial-delay)>5.1e-10:
        raise ValueError('initial geometry/config mismatch')
    return dict(total_delay_ms=initial,ta_common_units=actual_ta,ta_quantization_error_ns=abs(actual_ta*4.072e-9-2*rg/C)*1e9)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path);p.add_argument('--run-dir',type=Path)
    p.add_argument('--labels',nargs='+');p.add_argument('--trace',type=Path)
    a=p.parse_args(argv)
    if a.manifest:
        if a.run_dir or a.labels or a.trace:p.error('--manifest cannot be mixed with old run selectors')
        report=audit_manifest(a.manifest)
    else:
        if not a.run_dir or not a.labels:p.error('--run-dir and --labels required without manifest')
        from experiment import observed_sample_rate
        trace=a.trace or a.run_dir/'examples/fdd-pass/trace.csv'
        if not trace.is_file():trace=a.run_dir/'local_ntn/stk_trace.csv'
        rows=read_rows(trace);report=dict(trace_rows=len(rows),trace_interval_s=[rows[0][0],rows[-1][0]],runs={})
        all_rates=set()
        for label in a.labels:
            result_path=a.run_dir/(label+'-result.json')
            if not result_path.is_file():result_path=a.run_dir/'.runtime/reports'/(label+'.json')
            result=json.loads(result_path.read_text())
            logs={side:(a.run_dir/'local_ntn'/f'{side}-{label}.log').read_text(errors='replace') for side in ('gnb','ue')}
            fs=observed_sample_rate(logs)
            if fs is None:raise ValueError('both startup sampling rates required')
            if result.get('sample_rate_hz',fs)!=fs:raise ValueError('result Fs mismatch')
            all_rates.add(fs)
            # Result-aware run evidence belongs in the CLI, not the reusable
            # one-point arithmetic audit used by independent numerical fixtures.
            run={}
            for side,direction in [('gnb','UL'),('ue','DL')]:
                mode=result.get('interpolation','hermite')
                if 'interpolation' in result:
                    declared=re.findall(r'\bSTKTRACE2 interpolation=([a-z-]+)\b',logs[side])
                    if not declared or any(value!=mode for value in declared):
                        raise ValueError('recorded interpolation mode mismatch')
                value=audit_log(rows,logs[side],direction,fs,rows[0][0],result['rate'],mode)
                begin,end=value['stk_interval_s']
                if result['rate']!=0 and end-begin<=1:
                    raise ValueError('dynamic trace did not advance')
                run[side]=value
            report['runs'][label]=run
        if len(all_rates)!=1:raise ValueError('runs have inconsistent sampling rates')
        report['sampling_rate_hz']=all_rates.pop()
        report['initial_config']=audit_initial(rows,a.run_dir/'local_ntn/gnb.local.conf',a.run_dir/'local_ntn/initial_delay_ms.txt')
        report['tolerances_log_rounding']=LIMITS
    print(json.dumps(report,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
