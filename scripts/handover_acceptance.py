"""Bounded continuous business acceptance on the physical RFsim IQ timeline.

Raw modem and packet events stay private. This driver starts no core containers.
Only Task8 explicitly activates real runs; all four cases report their own scope.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local_ntn'))
from runtime_config import resolve_runtime
from run_state import process_identity,read_state,matches
from experiment import observed_sample_rate,write_manifest
from audit_runtime_numbers import audit_manifest
from handover_metrics import IncrementalTail,parse_clock,ClockMap,NUMERIC,SCHEDULE,case_spec,cohort_summary,evaluate_handover
from continuous_udp import match_events
from handover_plot import write_timeline


def command(args,**kwargs):
    return subprocess.run(args,check=True,**kwargs)


def selected_runtime(case,profile,run_id,environment):
    expected='legacy-handover' if case=='legacy' else 'integrated-handover'
    if profile!=expected:raise ValueError('case/profile mismatch')
    env=dict(environment)
    if case=='firsthandover':
        desired={'OAI_STK_TRACE':ROOT/'local_ntn/stk_trace_firsthandover.csv',
                 'OAI_STK_SCHEDULE':ROOT/'local_ntn/satellite_schedule_firsthandover.csv',
                 'OAI_QD_DL_CHANNEL':ROOT/'examples/handover/firsthandover/downlink',
                 'OAI_QD_UL_CHANNEL':ROOT/'examples/handover/firsthandover/uplink'}
        for key,path in desired.items():
            if env.get(key) and Path(env[key]).resolve()!=path.resolve():
                raise ValueError('inherited '+key+' conflicts with case')
            env[key]=str(path)
    config=resolve_runtime(ROOT,profile,run_id,env)
    spec=case_spec(case)
    from preflight import read_trace
    rows=read_trace(config.trace)
    if [rows[0][0],rows[-1][0]]!=spec['trace_interval_s']:
        raise ValueError('case requires its complete selected trace')
    # Resolver enforces existing inherited run/network scope; never silently clear it.
    env.update(config.to_env())
    return config,env


class OwnedChildren:
    def __init__(self,output):
        self.output=output;self.children={};self.handles=[]

    def spawn(self,name,argv,environment):
        path=self.output/(name+'.log')
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        stream=os.fdopen(fd,'w');self.handles.append(stream)
        process=subprocess.Popen(argv,env=environment,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        identity=process_identity(process.pid)
        if identity is None:raise RuntimeError('worker exited before identity was observed')
        self.children[name]=dict(process=process,identity=identity,argv=argv,start_ns=time.monotonic_ns())
        # ip/nsenter exec host Python without changing PID start time.
        expected=str(Path(sys.executable).resolve())
        deadline=time.monotonic()+5
        while identity[1]!=expected and time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('worker failed during exec')
            current=process_identity(process.pid)
            if current is None or current[0]!=identity[0]:raise RuntimeError('child identity changed during exec')
            identity=current;time.sleep(.01)
        if identity[1]!=expected:raise RuntimeError('child did not exec selected host Python')
        self.children[name]['identity']=identity
        return process

    def alive(self,name):
        child=self.children[name]
        return child['process'].poll() is None and process_identity(child['process'].pid)==child['identity']

    def signal(self,name,sig):
        child=self.children[name];process=child['process']
        if process.poll() is None:
            if process_identity(process.pid)!=child['identity']:
                raise RuntimeError('child PID/executable identity changed; refusing signal')
            os.killpg(process.pid,sig)

    def finish(self,name,timeout=8):
        child=self.children[name];process=child['process']
        if process.poll() is None:self.signal(name,signal.SIGTERM)
        try:process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.signal(name,signal.SIGKILL);process.wait(timeout=5)
        child['exit']=process.returncode;child['end_ns']=time.monotonic_ns()

    def close(self):
        errors=[]
        for name in self.children:
            try:self.finish(name)
            except Exception as error:errors.append(name+': '+str(error))
        for handle in self.handles:handle.close()
        if errors:raise RuntimeError('; '.join(errors))

    def evidence(self):
        return {name:{key:value for key,value in child.items() if key!='process'}
                | {'pid':child['process'].pid} for name,child in self.children.items()}


class Observer:
    def __init__(self,manifest):
        self.manifest=manifest
        self.tails={side:IncrementalTail(path) for side,path in manifest['logs'].items()}
        self.anchors={side:[] for side in ('gnb','ue')}
        self.numbers={side:[] for side in ('gnb','ue')}
        self.schedules={side:[] for side in ('gnb','ue')}
        self.startup={side:[] for side in ('gnb','ue')}
        self.pbch_errors=0;self.rrc_idle=0;self.reaccess_count=0;self.initial_access=False
        self.qd_loaded={side:0 for side in ('gnb','ue')}
        self.fs=manifest['sample_rate_hz']

    def update(self):
        for side,tail in self.tails.items():
            direction='UL' if side=='gnb' else 'DL'
            for line in tail.read_lines():
                clock=parse_clock(line)
                if clock:
                    if clock['direction']!=direction:raise ValueError('clock direction mismatch')
                    prior=self.anchors[side]
                    fs=clock['sampling_rate']
                    if prior and (clock['samples']<=prior[-1]['samples'] or clock['monotonic_ns']<=prior[-1]['monotonic_ns']):
                        raise ValueError('physical clock regression')
                    if prior and (clock['samples']-prior[-1]['samples'])/fs>.15:
                        raise ValueError('physical clock observation gap')
                    if self.fs is not None and fs!=self.fs:raise ValueError('startup/channel Fs mismatch')
                    iq=clock['samples']/fs
                    if abs(clock['iq_s']-iq)>1e-8 or abs(clock['stk_s']-(self.manifest['epoch']+self.manifest['rate']*iq))>1e-8:
                        raise ValueError('physical epoch/rate mismatch')
                    prior.append(clock)
                numeric=NUMERIC.search(line)
                if numeric:
                    values=numeric.groups()
                    self.numbers[side].append(dict(direction=values[0],iq_s=float(values[1]),stk_s=float(values[2]),
                        delay_ms=float(values[3]),doppler_hz=float(values[4]),gain_db=float(values[5]),
                        cn_db=float(values[6]),valid=int(values[7]),samples=int(values[8])))
                schedule=SCHEDULE.search(line)
                if schedule:
                    values=schedule.groups()
                    self.schedules[side].append(dict(iq_s=float(values[1]),stk_s=float(values[2]),
                        satellite_id=values[3],phase=values[7],switched=int(values[6]),samples=int(values[10])))
                self.qd_loaded[side]+=int('QDCHANNEL1 loaded' in line)
                self.pbch_errors+=int('Error decoding PBCH' in line)
                self.rrc_idle+=int(self.initial_access and any(marker in line for marker in ('RRC_IDLE','RRC IDLE','RRC moved into IDLE state','going to IDLE','Go to IDLE.')))
                if side=='ue':
                    if 'PDU Session Establishment Accept' in line:self.initial_access=True
                    if self.initial_access and any(marker in line for marker in ('Starting Initial synchronization','RA procedure started','Initialization of 4-Step','Initialization of 2-Step','Triggering new RA procedure','Generating RRCReestablishmentComplete','Received RRCReestablishment')):
                        self.reaccess_count+=1
                # Keep only recognized startup lines, not raw UE credentials.
                if 'sample_rate' in line or 'STKRUNTIME' in line:self.startup[side].append(line)
        seen=observed_sample_rate({side:'\n'.join(lines) for side,lines in self.startup.items()})
        if seen is not None:
            if self.fs is not None and seen!=self.fs:raise ValueError('startup Fs changed')
            self.fs=seen
            for rows in self.anchors.values():
                if any(a['sampling_rate']!=seen for a in rows):raise ValueError('anchor/startup Fs mismatch')

    def progress(self):
        return {side:rows[-1]['samples']/self.fs if rows and self.fs else 0 for side,rows in self.anchors.items()}

    def mapper(self,side):
        return ClockMap(self.anchors[side],self.manifest['epoch'],self.manifest['rate'],self.fs)


def validate_physical_observations(observer,spec):
    duration=spec['duration_iq_s']
    for side in ('gnb','ue'):
        for label,rows in [('numeric',observer.numbers[side]),('schedule',observer.schedules[side])]:
            if not rows:raise ValueError('missing '+side+' '+label+' physical observations')
            times=[row['samples']/observer.fs for row in rows]
            if times[0]>1.15 or times[-1]<duration-1.15:
                raise ValueError('incomplete '+side+' '+label+' physical coverage')
            if any(b<=a or b-a>1.15 for a,b in zip(times,times[1:])):
                raise ValueError(side+' '+label+' physical observation gap')
        if any(row['valid']!=1 for row in observer.numbers[side]):
            raise ValueError('invalid physical channel in required interval')
        for completion in spec['completions']:
            if not any(row['phase']=='complete' and completion<=row['stk_s']<completion+1.15
                       for row in observer.schedules[side]):
                raise ValueError('missing observed satellite completion: '+side)


def tail_stop_iq(spec,anchors,fs):
    factors=[]
    for rows in anchors.values():
        a,b=rows[max(0,len(rows)-31)],rows[-1]
        if b['monotonic_ns']<=a['monotonic_ns']:raise ValueError('no tail clock interval')
        factors.append(((b['samples']-a['samples'])/fs)/((b['monotonic_ns']-a['monotonic_ns'])/1e9))
    reserve=max(5.0,8.0*max(factors))
    minimum_stop=(spec['completions'][-1]+5-spec['trace_interval_s'][0]+.3) if spec['completions'] else 30.3
    if spec['duration_iq_s']-reserve<minimum_stop:
        raise ValueError('observed real-time factor leaves insufficient drain after required business coverage')
    return spec['duration_iq_s']-reserve


def pdu_address(namespace):
    result=subprocess.run(['ip','-n',namespace,'-j','-4','addr','show','dev','oaitun_ue1'],capture_output=True,text=True)
    if result.returncode:return None
    addresses=[address['local'] for link in json.loads(result.stdout) for address in link.get('addr_info',[]) if address.get('scope')=='global']
    if len(addresses)>1:raise ValueError('unexpected multiple PDU addresses')
    return addresses[0] if addresses else None


def private_events(path):
    if not path.is_file():raise ValueError('missing worker events: '+path.name)
    tail=IncrementalTail(path);lines=tail.read_lines()
    if tail.partial:raise ValueError('incomplete worker event record')
    return [json.loads(line) for line in lines]


def worker_observation(events,expected_role):
    if not events or events[0]['event']!='ready' or events[-1]['event']!='end' or events[-1].get('failed'):
        raise ValueError('worker did not complete')
    if any(e.get('role')!=expected_role or e.get('event')=='error' for e in events):
        raise ValueError('worker error/role mismatch')
    times=[e['monotonic_ns'] for e in events]
    if any(b<a for a,b in zip(times,times[1:])):raise ValueError('worker monotonic regression')
    heartbeats=[e['monotonic_ns'] for e in events if e['event'] in ('ready','heartbeat','end')]
    if any(b-a>2_000_000_000 for a,b in zip(heartbeats,heartbeats[1:])):
        raise ValueError('worker observation gap')
    if expected_role=='sender' and events[0].get('offered_wall_bits_per_second')!=100000:
        raise ValueError('wrong offered wall rate')
    sends=[event for event in events if event['event']=='send']
    receives=[event for event in events if event['event']=='receive']
    if expected_role in ('sender','ping'):
        if events[-1]['sent']!=len(sends) or [event['sequence'] for event in sends]!=list(range(1,len(sends)+1)):
            raise ValueError('sender event/sequence gap')
    if expected_role=='receiver' and events[-1]['received_datagrams']!=len(receives):
        raise ValueError('receiver event accounting gap')
    if expected_role=='ping' and events[-1]['received']!=len({event['sequence'] for event in receives}):
        raise ValueError('ping receiver accounting gap')
    return [times[0],times[-1]]


def mapped_packets(sender,receiver,mapper,drain_ns):
    result=match_events(sender,receiver,5_000_000_000,drain_ns)
    for packet in result['packets']:
        packet['send']=mapper.map(packet['send_ns'])
        if packet['received']:packet['receive']=mapper.map(packet['receive_ns'])
    return result


def build_report(report,observer,output,readiness,traffic_stop_ns,drain_ns,workers):
    fs=observer.fs
    if fs is None:raise ValueError('missing both actual startup sample rates')
    maps={side:observer.mapper(side) for side in ('gnb','ue')}
    events={name:private_events(output/(name+'.jsonl')) for name in ('ping','uplink-sender','uplink-receiver','downlink-sender','downlink-receiver')}
    for name,rows in events.items():worker_observation(rows,'ping' if name=='ping' else name.split('-')[1])
    ping=mapped_packets(events['ping'],events['ping'],maps['ue'],drain_ns)
    probes={'ping':ping}
    for direction,side in [('uplink','gnb'),('downlink','ue')]:
        probes[direction]=mapped_packets(events[direction+'-sender'],events[direction+'-receiver'],maps[side],drain_ns)
    if any(probe['unknown_receives'] for probe in probes.values()):
        raise ValueError('unmatched/foreign receiver evidence')
    # PDU readiness and traffic readiness require bracketing on both physical sides.
    pdu=[maps[side].map(readiness['pdu_ns']) for side in maps]
    first_receives=[]
    first_sends=[]
    for probe in probes.values():
        delivered=[packet for packet in probe['packets'] if packet['received']]
        if not delivered:raise ValueError('business direction never delivered a real packet')
        first_receives.append(min(packet['receive_ns'] for packet in delivered))
        if not probe['packets']:raise ValueError('business direction has no sender evidence')
        first_sends.append(min(packet['send_ns'] for packet in probe['packets']))
    readiness['confirmed_traffic_ns']=max(first_receives)
    traffic=[maps[side].map(readiness['confirmed_traffic_ns']) for side in maps]
    measurement=[maps[side].map(max(first_sends)) for side in maps]
    start=max(max(p['iq_bounds_s']) for p in measurement)
    stop=[maps[side].map(traffic_stop_ns) for side in maps]
    end=min(min(p['iq_bounds_s']) for p in stop)
    report.update(sample_rate_hz=fs,clock_sample_rates={side:rows[-1]['sampling_rate'] for side,rows in observer.anchors.items()},
                  iq_interval_s={side:[rows[0]['samples']/fs,rows[-1]['samples']/fs] for side,rows in observer.anchors.items()},
                  iq_end_stk_s={side:rows[-1]['stk_s'] for side,rows in observer.anchors.items()},
                  pdu_ready_stk_s=max(max(p['stk_bounds_s']) for p in pdu),
                  traffic_ready_stk_s=max(max(p['stk_bounds_s']) for p in traffic),
                  pdu_ready_iq_s=max(max(p['iq_bounds_s']) for p in pdu),
                  traffic_ready_iq_s=max(max(p['iq_bounds_s']) for p in traffic),business_iq_interval_s=[start,end],
                  pbch_errors=observer.pbch_errors,rrc_idle=observer.rrc_idle,reaccess_count=observer.reaccess_count,
                  clock_observation_ok=True,worker_observation_ok=True,
                  offered_wall_bits_per_second=100000,
                  measurement_clock='CLOCK_MONOTONIC',clock_max_iq_gap_s={side:mapper.max_iq_gap for side,mapper in maps.items()},
                  workers=workers,drain_end_monotonic_ns=drain_ns,
                  traffic_stop_monotonic_ns=traffic_stop_ns,
                  readiness=readiness,qd_loaded=observer.qd_loaded)
    elapsed_wall=(traffic_stop_ns-readiness['traffic_ns'])/1e9
    report['ping']=cohort_summary(probes['ping']['packets'],0,case_spec(report['case'])['duration_iq_s'],wall_interval_s=elapsed_wall)
    report['ping']['wall_rtt_ms_mean']=report['ping'].pop('wall_latency_ms_mean')
    report['udp']={}
    for direction in ('uplink','downlink'):
        report['udp'][direction]=cohort_summary(probes[direction]['packets'],0,case_spec(report['case'])['duration_iq_s'],wall_interval_s=elapsed_wall)
        send_events=[event for event in events[direction+'-sender'] if event['event']=='send']
        offered_span=(traffic_stop_ns-min(event['send_ns'] for event in send_events))/1e9
        report['udp'][direction]['actual_offered_wall_bits_per_second']=sum(event['bytes'] for event in send_events)*8/offered_span
        report['udp'][direction]['offered_wall_interval_s']=offered_span
    report['packet_accounting']={key:{name:value for name,value in probe.items() if name!='packets'} for key,probe in probes.items()}
    report['windows']=[]
    for complete in case_spec(report['case'])['completions']:
        lo,hi=complete-5,complete+5
        covered=(report['traffic_ready_stk_s']<lo and all(stop_map['stk_bounds_s'][0]>hi for stop_map in stop))
        window=dict(complete_stk_s=complete,start_stk_s=lo,end_stk_s=hi,coverage_ok=covered,
                    ping=cohort_summary(probes['ping']['packets'],lo,hi,'stk'),
                    udp={direction:cohort_summary(probes[direction]['packets'],lo,hi,'stk') for direction in ('uplink','downlink')})
        window['ping']['wall_rtt_ms_mean']=window['ping'].pop('wall_latency_ms_mean')
        report['windows'].append(window)
    # Private packet events retain raw anchors and every exact timestamp.
    for name,probe in probes.items():
        (output/(name+'-matched.json')).write_text(json.dumps(probe,indent=2))
    report['timeline']=write_timeline(output,observer,probes,start,end,report)
    return report


def run_acceptance(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=('full','firsthandover','static','legacy'),default='full')
    parser.add_argument('--profile',default='integrated-handover');parser.add_argument('--run-id',required=True)
    parser.add_argument('--max-wall-seconds',type=int,default=3600)
    args=parser.parse_args(argv)
    if os.geteuid()!=0:parser.error('run as root with matching profile/run environment')
    if args.max_wall_seconds<120:parser.error('max-wall-seconds must be at least120')
    spec=case_spec(args.case)
    config,environment=selected_runtime(args.case,args.profile,args.run_id,os.environ)
    manifest_path=config.run_dir/'run.json'
    if manifest_path.exists():parser.error('run already exists; choose a new run-id')
    os.umask(0o077)
    config.run_dir.mkdir(parents=True,exist_ok=True)
    output=config.run_dir/'acceptance';output.mkdir()
    children=OwnedChildren(output)
    report=dict(case=args.case,profile=config.profile,run_id=config.run_id,rate=spec['rate'],
                qd_enabled=args.case!='legacy',trace_interval_s=spec['trace_interval_s'],
                duration_iq_s=spec['duration_iq_s'],pdu_address_changes=0,numeric_audit_ok=False,
                clock_observation_ok=False,worker_observation_ok=False,passed=False)
    owned=False;observer=None;readiness={};traffic_stop_ns=drain_ns=None
    started=time.monotonic();last_progress=started;previous=-1;next_note=0;drain_deadline=None
    try:
        launch=children.spawn('launch',[sys.executable,str(ROOT/'local_ntn/experiment.py'),'start',
            '--profile',config.profile,'--run-id',config.run_id,'--label','acceptance','--rate',str(spec['rate'])],environment)
        # Poll readiness during launcher execution, rather than waiting for stable connection.
        address=None;traffic_started=False;container=None
        while True:
            now=time.monotonic()
            if now-started>args.max_wall_seconds:raise RuntimeError('bounded wall timeout')
            if observer is None and manifest_path.is_file():
                manifest=json.loads(manifest_path.read_text())
                owned=manifest.get('run_id')==config.run_id and manifest.get('profile')==config.profile
                if owned and set(manifest['logs'])=={'gnb','ue'}:observer=Observer(manifest)
            if observer:
                observer.update()
                progress=observer.progress()
                current=min(progress.values())
                if current>previous:previous=current;last_progress=now
                if now-last_progress>60:raise RuntimeError('IQ did not advance for60 wall seconds')
                if config.state_file.is_file():
                    _,records=read_state(config.state_file,config.run_id)
                    if records and not all(matches(record) for record in records.values()):
                        raise RuntimeError('owned modem process exited')
                current_address=pdu_address(config.namespace)
                if current_address:
                    if address is None:
                        address=current_address;readiness['pdu_ns']=time.monotonic_ns();observer.initial_access=True
                    elif current_address!=address:
                        report['pdu_address_changes']+=1;raise RuntimeError('PDU address changed')
                elif address is not None:
                    report['pdu_address_changes']+=1;raise RuntimeError('PDU address disappeared')
                if address and not traffic_started and observer.fs and all(len(rows)>=2 for rows in observer.anchors.values()):
                    command([sys.executable,str(ROOT/'local_ntn/verify_network.py'),'--profile',config.profile,'--run-id',config.run_id],env=environment,stdout=subprocess.DEVNULL)
                    container=json.loads(subprocess.check_output(['docker','inspect',config.ext_dn_container]))[0]
                    if not container['State']['Running']:raise RuntimeError('ext-DN not running')
                    labels=container['Config'].get('Labels') or {}
                    if labels.get('com.docker.compose.project')!=config.core_project:
                        raise RuntimeError('ext-DN does not belong to selected core project')
                    container_pid=container['State']['Pid'];container_identity=process_identity(container_pid)
                    if not container_identity:raise RuntimeError('ext-DN identity unavailable')
                    report['ext_dn_identity']={'pid':container_pid,'identity':container_identity}
                    command(['ip','-n',config.namespace,'route','replace',config.ext_dn_ip+'/32','dev','oaitun_ue1','src',address])
                    route=json.loads(subprocess.check_output(['ip','-n',config.namespace,'-j','route','get',config.ext_dn_ip]))
                    if not route or route[0].get('dev')!='oaitun_ue1':raise RuntimeError('UDP would bypass PDU tunnel')
                    token=os.urandom(8).hex()
                    prefix={'ue':['ip','netns','exec',config.namespace],
                            'dn':['nsenter','-t',str(container_pid),'-n']}
                    for direction,port,sender_side,receiver_side,source,dest in [
                        ('uplink',5203,'ue','dn',address,config.ext_dn_ip),
                        ('downlink',5204,'dn','ue',config.ext_dn_ip,address)]:
                        for role,side,bind,peer in [('receiver',receiver_side,dest,source),('sender',sender_side,source,dest)]:
                            name=direction+'-'+role
                            if role=='sender':
                                receiver_events=output/(direction+'-receiver.jsonl')
                                deadline=time.monotonic()+5
                                first=[]
                                while time.monotonic()<deadline:
                                    if receiver_events.is_file():
                                        with receiver_events.open() as stream:
                                            line=stream.readline()
                                        if line.endswith('\n'):
                                            first=[json.loads(line)];break
                                    time.sleep(.02)
                                if not first or first[0]['event']!='ready':raise RuntimeError('receiver readiness timeout')
                            if side=='dn' and process_identity(container_pid)!=container_identity:
                                raise RuntimeError('ext-DN PID identity changed')
                            children.spawn(name,prefix[side]+[sys.executable,str(ROOT/'scripts/continuous_udp.py'),role,
                                '--bind',bind,'--peer',peer,'--port',str(port),'--direction',direction,'--token',token,
                                '--events',str(output/(name+'.jsonl'))],environment)
                    children.spawn('ping',prefix['ue']+[sys.executable,str(ROOT/'scripts/continuous_ping.py'),
                        '--destination',config.ext_dn_ip,'--interface','oaitun_ue1','--events',str(output/'ping.jsonl')],environment)
                    readiness['traffic_ns']=time.monotonic_ns();traffic_started=True
                if traffic_started and traffic_stop_ns is None:
                    for name in ('ping','uplink-sender','uplink-receiver','downlink-sender','downlink-receiver'):
                        if not children.alive(name):raise RuntimeError('business worker exited: '+name)
                    tail_target=tail_stop_iq(spec,observer.anchors,observer.fs) if current>=spec['duration_iq_s']-30 else spec['duration_iq_s']-5
                    if current>=tail_target:
                        traffic_stop_ns=time.monotonic_ns()
                        report['tail_send_stop_target_iq_s']=tail_target
                        for name in ('uplink-sender','downlink-sender','ping'):children.signal(name,signal.SIGINT)
                        drain_deadline=now+6
                        report['tail_phase']='intentional_send_stop_and_bounded_wall_drain'
                if traffic_stop_ns is not None and drain_ns is None and now>=drain_deadline:
                    for name in ('uplink-sender','downlink-sender','ping'):
                        children.children[name]['process'].wait(timeout=2)
                    for name in ('uplink-receiver','downlink-receiver'):children.signal(name,signal.SIGINT)
                    for name in ('uplink-receiver','downlink-receiver'):children.children[name]['process'].wait(timeout=2)
                    drain_ns=time.monotonic_ns()
                if now>=next_note:
                    print(json.dumps({'case':args.case,'run_id':args.run_id,'wall_s':now-started,
                                      'iq_elapsed_s':progress,'business_available':traffic_started and traffic_stop_ns is None}),flush=True)
                    next_note=now+30
                if drain_ns is not None and current>=spec['duration_iq_s']:
                    if all(rows[-1]['monotonic_ns']>=drain_ns for rows in observer.anchors.values()):break
                if not traffic_started and current>=(60 if args.case=='static' else 39):raise RuntimeError('business readiness deadline exceeded')
            if launch.poll() is not None and launch.returncode!=0:raise RuntimeError('experiment launch failed; inspect private log')
            time.sleep(.1)
        observer.manifest['sample_rate_hz']=observer.fs
        write_manifest(manifest_path,observer.manifest)
        validate_physical_observations(observer,spec)
        numeric=audit_manifest(manifest_path)
        (output/'numeric-audit.json').write_text(json.dumps(numeric,indent=2))
        report['numeric_audit_ok']=True
    except Exception as error:
        report['error']=str(error)
    finally:
        # Complete bounded owned cleanup even if a second signal arrives.
        signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:children.close()
        except Exception as error:report['cleanup_error']=str(error)
        if manifest_path.is_file():
            try:
                final_manifest=json.loads(manifest_path.read_text())
                owned=(final_manifest.get('run_id')==config.run_id and final_manifest.get('profile')==config.profile
                       and final_manifest.get('workspace')==str(config.root))
            except (ValueError,OSError):owned=False
        if owned and config.state_file.is_file():
            try:
                result=subprocess.run([sys.executable,str(ROOT/'local_ntn/experiment.py'),'stop',
                    '--profile',config.profile,'--run-id',config.run_id],env=environment,capture_output=True,text=True,timeout=30)
                report['stop_exit']=result.returncode
                (output/'stop.log').write_text(result.stdout+result.stderr)
            except Exception as error:report['cleanup_error']=str(error)
        else:report['stop_exit']=1
        report['wall_seconds']=time.monotonic()-started
        if observer and traffic_stop_ns is not None and drain_ns is not None:
            try:build_report(report,observer,output,readiness,traffic_stop_ns,drain_ns,children.evidence())
            except Exception as error:report['summary_error']=str(error)
        report['failure_reasons']=evaluate_handover(report)
        if report.get('error') or report.get('summary_error') or report.get('cleanup_error'):
            report['failure_reasons'].append('driver or evidence collection failed')
        if observer and args.case!='legacy' and any(count!=1 for count in observer.qd_loaded.values()):
            report['failure_reasons'].append('expected one QD load per modem')
        report['passed']=not report['failure_reasons']
        (output/'report.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({key:report.get(key) for key in ('case','run_id','passed','failure_reasons','error','summary_error','wall_seconds')},indent=2),flush=True)
    return 0 if report['passed'] else 1


class InterruptGuard:
    def __enter__(self):
        self.previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        self.interrupted=False
        for sig in self.previous:signal.signal(sig,self.handle)
        return self

    def handle(self,sig,_frame):
        if not self.interrupted:
            self.interrupted=True
            raise RuntimeError('controlled interruption: '+str(sig))

    def __exit__(self,*_exception):
        for sig,handler in self.previous.items():signal.signal(sig,handler)


def main(argv=None):
    with InterruptGuard():
        return run_acceptance(argv)


if __name__=='__main__':raise SystemExit(main())

