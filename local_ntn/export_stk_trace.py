"""Read the active STK scene; export deterministic RFsim trace, without moving animation.

Units: ECEF m, m/s, m/s^2, EpSec, dBW, dB. Fixed payload output power;
two independent hop C/N values combine as inverse linear ratios.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
from agi.stk12.stkdesktop import STKDesktop
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from configure_stk_phased_array import SAT, GNB, UE, ENDPOINTS, LINKS

def columns(provider,start,stop,step,names):
    ds=provider.ExecElements(start,stop,step,names).DataSets
    return {n:list(map(float,ds.GetDataSetByName(n).GetValues())) for n in names}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start',type=float,default=12080)
    p.add_argument('--stop',type=float,default=12350)
    p.add_argument('--step',type=float,default=1)
    p.add_argument('--out',type=Path,default=Path(__file__).with_name('stk_trace.csv'))
    a=p.parse_args()
    if a.stop<=a.start or a.step<=0: p.error('invalid interval')
    try:
        desktop=STKDesktop.AttachToApplication()
    except Exception as exc:
        raise SystemExit('Cannot attach to STK 12. Open the target scenario and run Python at the same permission level as STK. Details: '+str(exc)) from None
    r=desktop.Root; r.Isolate()
    for dim,unit in [('FrequencyUnit','Hz'),('PowerUnit','dBW'),('BitsUnit','b'),
                     ('TimeUnit','sec'),('BandwidthUnit','Hz'),('DistanceUnit','m'),
                     ('DateFormat','EpSec'),('AngleUnit','deg'),('RatioUnit','dB')]:
        r.UnitPreferences.SetCurrentUnit(dim,unit)
    old_time=float(r.CurrentTime)
    sat=r.GetObjectFromPath(SAT)
    states=[]
    for name in ('Cartesian Position','Cartesian Velocity','Cartesian Acceleration'):
        provider=sat.DataProviders.GetDataPrvTimeVarFromPath(name+'//Fixed')
        states.append(columns(provider,a.start,a.stop,a.step,['Time','x','y','z']))
    times=states[0]['Time']
    if any(s['Time']!=times for s in states): raise RuntimeError('state time grids differ')
    gnb=list(map(float,r.GetObjectFromPath(GNB).Position.QueryCartesianArray()))
    ue=list(map(float,r.GetObjectFromPath(UE).Position.QueryCartesianArray()))
    objects=[r.GetObjectFromPath(path) for path,_,_,_ in ENDPOINTS]
    fields=['Time','Carrier Power at Rcvr Input','C/N','Xmtr Gain','Rcvr Gain']
    budgets=[]
    for name,tx,rx in LINKS:
        access=objects[tx].GetAccessToObject(objects[rx]); access.ComputeAccess()
        provider=access.DataProviders.GetDataPrvTimeVarFromPath('Link Information')
        data=columns(provider,a.start,a.stop,a.step,fields)
        # Access boundaries may insert extra samples: match by epoch, never by row number.
        budgets.append({round(t,6):{k:data[k][i] for k in fields[1:]} for i,t in enumerate(data['Time'])})
        print('EXPORTED',name,len(data['Time']),flush=True)
    def hop(index,t):
        d=budgets[index].get(round(t,6))
        valid=d is not None and all(math.isfinite(v) and v>-900 for v in d.values())
        return (d if valid else {'Carrier Power at Rcvr Input':-300.,'C/N':-100.}), int(valid)
    def cn(c1,c2): return -10*math.log10(10**(-c1/10)+10**(-c2/10))
    good=[0,0]
    with a.out.open('w',newline='',encoding='ascii') as f:
        f.write('STKTRACE2\n')
        f.write('# time,x,y,z,vx,vy,vz,ax,ay,az,gnb_x,gnb_y,gnb_z,ue_x,ue_y,ue_z,dl_power_dbw,ul_power_dbw,dl_cn_db,ul_cn_db,dl_valid,ul_valid\n')
        w=csv.writer(f)
        for i,t in enumerate(times):
            hops=[hop(j,t) for j in range(4)]
            dl=hops[0][1]*hops[1][1]; ul=hops[2][1]*hops[3][1]
            good[0]+=dl; good[1]+=ul
            row=[t]+[s[axis][i] for s in states for axis in ('x','y','z')]+gnb+ue
            row += [hops[1][0]['Carrier Power at Rcvr Input'],hops[3][0]['Carrier Power at Rcvr Input'],
                    cn(hops[0][0]['C/N'],hops[1][0]['C/N']),cn(hops[2][0]['C/N'],hops[3][0]['C/N']),dl,ul]
            if not all(math.isfinite(v) for v in row): raise RuntimeError('nonfinite export')
            w.writerow(row)
    meta={'scenario':r.CurrentScenario.Path,'time_before':old_time,'time_after':float(r.CurrentTime),
          'start':times[0],'stop':times[-1],'step':a.step,'rows':len(times),'valid_dl_ul':good,
          'gnb_ecef_m':gnb,'ue_ecef_m':ue,'endpoint_paths':[o.Path for o in objects],
          'frequencies_Hz':[o.Model.Frequency for o in objects],
          'model':'STK fixed-payload-output power; inverse-sum hop C/N; actual ECEF trajectory'}
    a.out.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(json.dumps(meta,indent=2),flush=True)
if __name__=='__main__': main()
