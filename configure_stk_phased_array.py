"""Configure the eight OAI link endpoints in the prepared STK scenario copy.

Engineering demonstration assumptions, not measured Qianfan payload parameters.
Original and modified scenes are kept separately. Run --verify for read-only checks.
"""
from pathlib import Path
import json
import sys
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkobjects import (
    AgEElementConfigurationType, AgELatticeType, AgESpacingUnit,
    AgEDirectionProviderType, AgELimitsExceededBehaviorType,
)

BASE = Path('C:/Users/WSZ/.codex/visualizations/2026/07/24/019f9209-937f-7c50-8691-be0521d4eebc/STK_PhasedArray_20260910')
SAT = 'Satellite/QIANFAN-166_69383'
GNB = 'Place/Beijing'
UE = 'Place/OAI_UE'
ENDPOINTS = [
    (GNB+'/Transmitter/OAI_gNB_DL_Tx', SAT, 16, 30),
    (GNB+'/Receiver/OAI_gNB_UL_Rx', SAT, 16, None),
    (UE+'/Transmitter/OAI_UE_UL_Tx', SAT, 4, 10),
    (UE+'/Receiver/OAI_UE_DL_Rx', SAT, 4, None),
    (SAT+'/Receiver/OAI_SAT_DL_Rx', GNB, 16, None),
    (SAT+'/Transmitter/OAI_SAT_UL_Tx', GNB, 16, 20),
    (SAT+'/Receiver/OAI_SAT_UL_Rx', UE, 16, None),
    (SAT+'/Transmitter/OAI_SAT_DL_Tx', UE, 16, 20),
]
LINKS = [('DL feeder',0,4),('DL service',7,3),('UL service',2,6),('UL feeder',5,1)]

def connect(r, obj, attr, value):
    p = obj.Path.split('/Scenario/')[1].split('/',1)[1]
    cmd = f'{obj.ClassName} */{p} SetValue {attr} {value}'
    r.ExecuteCommand(cmd)

def configure(r, obj, target, n, power):
    m = obj.Model
    ctrl = m.AntennaControl
    ctrl.SetEmbeddedModel('Phased Array')
    ant = ctrl.EmbeddedModel
    ant.DesignFrequency = m.Frequency
    ant.ElementConfigurationType = AgEElementConfigurationType.eElementConfigurationTypePolygon
    cfg = ant.ElementConfiguration
    cfg.NumSides = 4
    cfg.LatticeType = AgELatticeType.eLatticeTypeRectangular
    cfg.Equilateral = True
    cfg.NumElementsX = n
    cfg.NumElementsY = n
    cfg.SpacingUnit = AgESpacingUnit.eSpacingUnitWavelengthRatio
    cfg.SpacingX = 0.5
    ant.IncludeElementFactor = True
    ant.ElementFactorExponent = 1.0
    ant.BacklobeSuppression = 30.0
    ant.BeamDirectionProviderType = AgEDirectionProviderType.eDirectionProviderTypeObject
    beam = ant.BeamDirectionProvider
    beam.Enabled = True
    beam.Directions.RemoveAll()
    beam.Directions.Add(target)
    beam.UseDefaultDirection = False
    beam.LimitsExceededBehaviorType = AgELimitsExceededBehaviorType.eLimitsExceededBehaviorTypeIgnoreObject
    prefix = 'Model.AntennaControl.Antenna.BeamDirectionProvider.'
    for name, val in [('AzimuthSteeringLimitA',-60),('AzimuthSteeringLimitB',60),
                      ('ElevationSteeringLimitA',-60),('ElevationSteeringLimitB',60)]:
        connect(r,obj,prefix+name,f'{val} deg')
    # STK VVLH satellite +Z is nadir; ground parent +Z is local zenith.
    connect(r,obj,'Model.AntennaControl.Orientation','"Azimuth Elevation"')
    connect(r,obj,'Model.AntennaControl.Orientation.AzimuthAngle','0 deg')
    connect(r,obj,'Model.AntennaControl.Orientation.ElevationAngle','90 deg')
    if power is not None:
        m.Power = power
        m.DataRate = 1_000_000
    else:
        m.AutoScaleBandwidth = False
        m.Bandwidth = 2_000_000
    ant.UserComment = 'OAI engineering reference: half-wave array, target steering, +/-60 deg limits; not actual spacecraft hardware.'

def describe(r,obj):
    m=obj.Model
    a=m.AntennaControl.EmbeddedModel
    out={'path':obj.Path,'frequency_GHz':m.Frequency,'antenna':a.Name,
         'design_frequency_GHz':a.DesignFrequency}
    if a.Name=='Phased Array':
        b=a.BeamDirectionProvider
        out.update(elements=a.NumberOfElements,width_m=a.Width,height_m=a.Height,
                   spacing_x_lambda=a.ElementConfiguration.SpacingX,
                   spacing_y_lambda=a.ElementConfiguration.SpacingY,
                   steering_enabled=b.Enabled,targets=[b.Directions.Item(i).Path for i in range(b.Directions.Count)],
                   include_element_factor=a.IncludeElementFactor,backlobe_suppression_dB=a.BacklobeSuppression)
    if obj.ClassName=='Transmitter':
        out.update(power_dBW=m.Power,data_rate_bps=m.DataRate)
    else:
        out.update(bandwidth_Hz=m.Bandwidth)
    return out

def verify_links(r,objects):
    results=[]
    elements=['Time','Xmtr Gain','Rcvr Gain','EIRP','C/N','Eb/No','BER','Propagation Delay']
    for name,tx,rx in LINKS:
        access=objects[tx].GetAccessToObject(objects[rx])
        access.ComputeAccess()
        ints=access.ComputedAccessIntervalTimes
        intervals=[tuple(map(float,ints.GetInterval(i))) for i in range(ints.Count)]
        if not intervals:
            results.append({'link':name,'error':'no access'})
            continue
        # Use the pass nearest the current scene epoch, without moving animation.
        now=float(r.CurrentTime)
        start,stop=min(intervals,key=lambda ab:abs((ab[0]+ab[1])/2-now))
        samples=[]
        provider=access.DataProviders.GetDataPrvTimeVarFromPath('Link Information')
        for f in (0.15,0.35,0.5,0.65,0.85):
            t=start+(stop-start)*f
            try:
                ds=provider.ExecSingleElements(t,elements).DataSets
                row={k:ds.GetDataSetByName(k).GetValues()[0] for k in elements}
            except Exception as exc:
                row={'time_s':t,'error':str(exc)}
            samples.append(row)
        results.append({'link':name,'selected_access_s':[start,stop],'samples':samples})
    return results

def main():
    d=STKDesktop.AttachToApplication()
    r=d.Root
    r.Isolate()
    for dim,unit in [('FrequencyUnit','GHz'),('PowerUnit','dBW'),('BitsUnit','b'),
                     ('TimeUnit','sec'),('BandwidthUnit','Hz'),('DistanceUnit','m'),
                     ('DateFormat','EpSec'),('AngleUnit','deg'),('RatioUnit','dB')]:
        r.UnitPreferences.SetCurrentUnit(dim,unit)
    directory=list(r.ExecuteCommand('GetDirectory / Scenario'))[0]
    if 'STK_PhasedArray_20260910' not in directory or 'modified' not in directory:
        raise RuntimeError('Not the prepared modified scene; refusing mutation')
    objects=[r.GetObjectFromPath(p) for p,_,_,_ in ENDPOINTS]
    if '--verify' not in sys.argv:
        for obj,(_,target,n,power) in zip(objects,ENDPOINTS):
            configure(r,obj,target,n,power)
            print('CONFIGURED',json.dumps(describe(r,obj)),flush=True)
        r.Save()
    report={'scenario_directory':directory,'endpoints':[describe(r,o) for o in objects],
            'links':verify_links(r,objects)}
    out=BASE/'phased_array_validation.json'
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
