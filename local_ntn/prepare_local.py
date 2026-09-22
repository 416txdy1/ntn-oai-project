"""Generate a separate local gNB config from trace[0]; never rewrite user templates."""
import argparse,csv,math,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--rate',type=float,default=0)
a=p.parse_args()
base=Path(__file__).resolve().parent
repo=Path('/home/kayoko/OAI/openairinterface5g')
lines=[s for s in (base/'stk_trace.csv').read_text().splitlines() if s and not s.startswith('#')]
v=list(map(float,next(csv.reader(lines[1:]))))
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
print('Generated',out,'rate',a.rate,'initial delay ms',(rf+rs)/c*1000)
