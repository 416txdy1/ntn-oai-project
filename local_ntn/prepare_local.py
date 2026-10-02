"""Generate a separate local gNB config from trace[0]; never rewrite user templates."""
import argparse,csv,math,re
from pathlib import Path
from paths import OAI_REPO, UE_CONFIG, STK_TRACE
from network_config import configure
p=argparse.ArgumentParser();p.add_argument('--rate',type=float,default=0)
a=p.parse_args()
if not math.isfinite(a.rate) or not 0 <= a.rate <= 1:
    p.error('--rate must be finite and between 0 and 1')
base=Path(__file__).resolve().parent
repo=OAI_REPO
trace=STK_TRACE
if not trace.is_file():
    raise SystemExit(f'Missing STK trace: {trace}. Open the STK scene and run local_ntn/export_stk_trace.py on Windows first.')
lines=[s.strip() for s in trace.read_text().splitlines() if s.strip() and (not s.strip().startswith('#') or s.strip()=='# STKTRACE2')]
if not lines or lines[0] not in ('STKTRACE2','# STKTRACE2') or len(lines)<3:
    raise SystemExit('Expected STKTRACE2 with at least two data rows; legacy channel CSV is not compatible.')
v=list(map(float,next(csv.reader(lines[1:]))))
if len(v)!=22 or not all(math.isfinite(x) for x in v) or v[20:]!=[1,1]:
    raise SystemExit('First trace row must contain 22 finite values and valid DL/UL coverage.')
pos=v[1:4];vel=v[4:7];gnb=v[10:13];ue=v[13:16]
def rng(site):
    d=[x-y for x,y in zip(pos,site)];r=math.sqrt(sum(x*x for x in d))
    return r,sum(x*y for x,y in zip(d,vel))/r*a.rate
rf,vf=rng(gnb);rs,vs=rng(ue);c=299792458.
conf=(repo/'ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf').read_text()
if not UE_CONFIG.is_file():
    raise SystemExit(f'Missing private UE config: {UE_CONFIG}; run provision_subscriber.py --local-current after checking the core network.')
ue_conf=re.sub(r'#[^\n]*','',UE_CONFIG.read_text())
imsi=re.search(r'\bimsi\s*=\s*"(\d{15})"',ue_conf)
if not imsi:
    raise SystemExit('Private UE configuration has no valid 15-digit IMSI')
position_block=re.search(r'\bposition0\s*=\s*\{(.*?)\}',ue_conf,re.S)
if not position_block:
    raise SystemExit('Private UE configuration has no position0 block; autonomous NTN TA requires the trace UE ECEF position.')
number=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
configured_ue=[]
for axis in 'xyz':
    match=re.search(r'\b'+axis+r'\s*=\s*('+number+r')\s*;',position_block[1])
    if not match:
        raise SystemExit(f'Private UE configuration position0 has no numeric {axis} coordinate')
    configured_ue.append(float(match[1]))
position_error=math.dist(configured_ue,ue)
if position_error>1.0:
    raise SystemExit(
        f'UE position0 differs from trace first-row UE ECEF by {position_error:.3f} m; '
        f'set position0 to x={ue[0]:.9f}, y={ue[1]:.9f}, z={ue[2]:.9f}. '
        'Otherwise autonomous NTN timing advance can move PRACH outside the gNB receive window.'
    )
# The supported lab PLMNs use a two-digit MNC. Keep all three components aligned.
conf=re.sub(r'\bmcc\s*=\s*\d+',f'mcc = {int(imsi[1][:3])}',conf)
conf=re.sub(r'\bmnc\s*=\s*\d+',f'mnc = {int(imsi[1][3:5])}',conf)
sd=re.search(r'\bnssai_sd\s*=\s*(0x[0-9a-fA-F]+|\d+)',ue_conf)
slice_sd=int(sd[1],16 if sd[1].startswith('0x') else 10) if sd else 0xffffff
conf=re.sub(r'\bsd\s*=\s*(?:0x[0-9a-fA-F]+|\d+)',f'sd = 0x{slice_sd:06x}',conf)
values={'cellSpecificKoffset_r17':80,'ta-Common-r17':round(2*rf/c/4.072e-9),
        'ta-CommonDrift-r17':round(2*vf/c/.2e-9)}
values.update({f'position{k}-r17':round(x/1.3) for k,x in zip('XYZ',pos)})
values.update({f'velocityV{k}-r17':round(x*a.rate/.06) for k,x in zip('XYZ',vel)})
for name,value in values.items():
    conf,n=re.subn(r'(?m)^(\s*'+re.escape(name)+r'\s*=)[^;]+;',r'\g<1> '+str(value)+';',conf)
    if n!=1:raise RuntimeError(f'{name}: {n} occurrences')
# 初始时延由双段几何计算；动态回放可超过 20 ms，由运行时更新偏移。
out=base/'gnb.local.conf';out.write_text(configure(conf))
(base/'initial_delay_ms.txt').write_text(f'{(rf+rs)/c*1000:.9f}\n')
print('Generated',out,'rate',a.rate,'initial delay ms',(rf+rs)/c*1000)
