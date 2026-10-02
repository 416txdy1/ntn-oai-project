"""只输出聚合误差：以独立 Python 几何计算验算实际 RFsim 日志。"""
import argparse
import bisect
import csv
import json
import math
from pathlib import Path
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--run-dir', type=Path, required=True)
p.add_argument('--labels', nargs='+', required=True)
p.add_argument('--trace', type=Path)
a=p.parse_args()
trace = a.trace or (a.run_dir/'examples/fdd-pass/trace.csv')
if not trace.is_file(): trace = a.run_dir/'local_ntn/stk_trace.csv'
rows=[list(map(float,row)) for row in csv.reader(line for line in trace.read_text().splitlines()[1:] if line and not line.startswith('#'))]
times=[r[0] for r in rows]
c=299792458.0
fs=7680000.0

def interpolate(t):
    assert times[0] <= t <= times[-1]
    i=max(0,min(len(rows)-2,bisect.bisect_right(times,t)-1))
    x,y=rows[i:i+2]
    h=y[0]-x[0]; u=(t-x[0])/h
    r=[left+u*(right-left) for left,right in zip(x,y)]
    # Hermite 多项式的 Horner 形式；速度由多项式导数独立计算。
    for k in range(3):
        d=x[1+k]; v=h*x[4+k]
        b=3*(y[1+k]-d)-h*(2*x[4+k]+y[4+k])
        aa=2*(d-y[1+k])+h*(x[4+k]+y[4+k])
        r[1+k]=((aa*u+b)*u+v)*u+d
        r[4+k]=(3*aa*u*u+2*b*u+v)/h
    return r

def geometry(r,rate):
    rg=math.dist(r[1:4],r[10:13]); ru=math.dist(r[1:4],r[13:16])
    vr=sum((r[1+k]-r[13+k])*r[4+k] for k in range(3))/ru*rate
    return (rg+ru)/c*1000,vr,ru/c*1000

pattern=re.compile(r'STKTRACE2 (UL|DL) IQ=([\d.]+) STK=([\d.]+) delay=([\d.]+)ms Doppler=([-\d.]+)Hz gain=([-\d.]+)dB C/N=([-\d.]+)dB valid=(\d+) samples=(\d+)')
report={'sampling_rate_hz':fs,'trace_rows':len(rows),'trace_interval_s':[times[0],times[-1]],'runs':{}}
limits={'iq_s':5.1e-7,'stk_s':5.1e-7,'delay_ms':5.1e-7,'doppler_hz':5.1e-4,'gain_db':5.1e-4,'cn_db':5.1e-4}
for label in a.labels:
    result_path = a.run_dir/(label+'-result.json')
    if not result_path.is_file(): result_path = a.run_dir/'.runtime/reports'/(label+'.json')
    result=json.loads(result_path.read_text())
    rate=result['rate']; run={}
    for kind,direction in [('gnb','UL'),('ue','DL')]:
        text=(a.run_dir/'local_ntn'/f'{kind}-{label}.log').read_text(errors='replace')
        matches=list(pattern.finditer(text))
        assert matches, (label,kind,'no numeric log')
        maxima=dict.fromkeys(limits,0.0)
        iq_times=[]; stk_times=[]
        for m in matches:
            side,iq,stk,delay,doppler,gain,cn,valid,samples=m.groups()
            assert side==direction and valid=='1'
            iq_exact=int(samples)/fs; t=times[0]+rate*iq_exact
            r=interpolate(t); expected_delay,vr,_=geometry(r,rate)
            frequency=1614900000 if side=='UL' else 2488400000
            expected_doppler=-vr/(c if side=='UL' else c+vr)*frequency
            power_index,cn_index=(17,19) if side=='UL' else (16,18)
            expected_gain=r[power_index]-rows[0][power_index]
            errors={'iq_s':abs(float(iq)-iq_exact),'stk_s':abs(float(stk)-t),'delay_ms':abs(float(delay)-expected_delay),'doppler_hz':abs(float(doppler)-expected_doppler),'gain_db':abs(float(gain)-expected_gain),'cn_db':abs(float(cn)-r[cn_index])}
            for key,value in errors.items():
                maxima[key]=max(maxima[key],value)
                assert value<=limits[key],(label,kind,key,value,limits[key])
            iq_times.append(iq_exact); stk_times.append(t)
        assert rate==0 or max(stk_times)-min(stk_times)>1, 'dynamic trace did not advance'
        run[kind]={'checked_rows':len(matches),'iq_interval_s':[min(iq_times),max(iq_times)],'stk_interval_s':[min(stk_times),max(stk_times)],'max_abs_errors':maxima}
    report['runs'][label]=run
values=[geometry(row,1) for row in rows]
report['whole_trace_geometry']={'total_feeder_plus_service_delay_ms':[min(v[0] for v in values),max(v[0] for v in values)],'service_delay_ms':[min(v[2] for v in values),max(v[2] for v in values)],'service_radial_velocity_m_s':[min(v[1] for v in values),max(v[1] for v in values)]}
rg=math.dist(rows[0][1:4],rows[0][10:13])
expected_ta=round(2*rg/c/4.072e-9)
config=(a.run_dir/'local_ntn/gnb.local.conf').read_text()
actual_ta=int(re.search(r'\bta-Common-r17\s*=\s*(\d+)',config)[1])
assert actual_ta==expected_ta
initial=float((a.run_dir/'local_ntn/initial_delay_ms.txt').read_text())
assert abs(initial-values[0][0])<=5.1e-10
report['initial_config']={'total_delay_ms':initial,'ta_common_units':actual_ta,'ta_quantization_error_ns':abs(actual_ta*4.072e-9-2*rg/c)*1e9}
report['tolerances_log_rounding']=limits
print(json.dumps(report,indent=2))