"""Generate a separate local gNB config from a trace state.

The optional RFsim lead selects the state expected when the UE finishes its
initial cell search.  It is deliberately opt-in: zero preserves the original
first-row behaviour and makes A/B comparisons reproducible.
"""
import argparse,csv,math,os,re
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--rate',type=float,default=0)
p.add_argument('--initial-lead-rfsim',type=float,
               default=float(os.environ.get('OAI_STK_INITIAL_LEAD_RFSIM','0')),
               help='RFsim seconds between trace start and expected initial sync')
a=p.parse_args()
if a.rate < 0 or a.rate > 1:
    p.error('--rate must be in [0,1]')
if a.initial_lead_rfsim < 0:
    p.error('--initial-lead-rfsim must be non-negative')
base=Path(__file__).resolve().parent
repo=Path('/home/kayoko/OAI/openairinterface5g')
trace_path=Path(os.environ.get('OAI_STK_TRACE', str(base/'stk_trace.csv')))
lines=[s for s in trace_path.read_text().splitlines() if s and not s.startswith('#')]
if not lines or lines[0] != 'STKTRACE2':
    raise RuntimeError(f'Unsupported STK trace header: {trace_path}')
rows=[list(map(float,row)) for row in csv.reader(lines[1:])]
if len(rows) < 2 or any(len(row) != 22 for row in rows):
    raise RuntimeError(f'Expected at least two 22-column STKTRACE2 rows: {trace_path}')
target_stk=rows[0][0]+a.rate*a.initial_lead_rfsim
target_stk=min(max(target_stk,rows[0][0]),rows[-1][0])
hi=next((i for i,row in enumerate(rows) if row[0] >= target_stk),len(rows)-1)
lo=max(0,hi-1)
if rows[hi][0] == rows[lo][0]:
    u=0.0
else:
    u=(target_stk-rows[lo][0])/(rows[hi][0]-rows[lo][0])
v=[x+u*(y-x) for x,y in zip(rows[lo],rows[hi])]
pos=v[1:4];vel=v[4:7];gnb=v[10:13];ue=v[13:16]
def rng(site):
    d=[x-y for x,y in zip(pos,site)];r=math.sqrt(sum(x*x for x in d))
    return r,sum(x*y for x,y in zip(d,vel))/r*a.rate
rf,vf=rng(gnb);rs,vs=rng(ue);c=299792458.
conf=(repo/'ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf').read_text()
conf=conf.replace('sd = 0xffffff','sd = 0x000001')
values={'cellSpecificKoffset_r17':80,'ta-Common-r17':round(2*rf/c/4.072e-9),
        'ta-CommonDrift-r17':round(2*vf/c/.2e-9)}
values.update({f'position{k}-r17':round(x/1.3) for k,x in zip('XYZ',pos)})
values.update({f'velocityV{k}-r17':round(x*a.rate/.06) for k,x in zip('XYZ',vel)})
for name,value in values.items():
    conf,n=re.subn(r'(?m)^(\s*'+re.escape(name)+r'\s*=)[^;]+;',r'\g<1> '+str(value)+';',conf)
    if n!=1:raise RuntimeError(f'{name}: {n} occurrences')
# Keep 20ms static history guard (greater than maximum delay in selected pass).
out=base/'gnb.local.conf';out.write_text(conf)
(base/'initial_delay_ms.txt').write_text(f'{(rf+rs)/c*1000:.9f}\n')
print('Generated',out,'trace',trace_path,'rate',a.rate,
      'initial lead RFsim s',a.initial_lead_rfsim,
      'initial STK s',target_stk,'initial delay ms',(rf+rs)/c*1000)
