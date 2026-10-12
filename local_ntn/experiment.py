"""Run-scoped experiment controller; no system operations during import."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from network_config import check_network
from network_owner import NetworkManager
from preflight import preflight, channel_environments, read_trace
from run_state import process_identity, read_state, matches, save_state, stop_owned
from runtime_config import resolve_runtime

BASE = Path(__file__).resolve().parent


def call(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def commit_at(path):
    return subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()


def build_manifest(config, rate, environment):
    rows=read_trace(config.trace)
    bundles={}
    if config.profile!='legacy-handover':
        for direction,bundle in (('downlink',config.dl_bundle),('uplink',config.ul_bundle)):
            if bundle and bundle.is_dir():
                bundles[direction]={'path':str(bundle),'files':{str(p.relative_to(bundle)):sha256(p) for p in sorted(bundle.rglob('*')) if p.is_file()}}
    return {'schema':1,'profile':config.profile,'run_id':config.run_id,'workspace':str(config.root),
            'source_commit':commit_at(config.root),'oai_source':{'commit':commit_at(config.oai_repo),'path':str(config.oai_repo)},
            'source_repo':str(config.oai_repo),'build_dir':str(config.build_dir),
            'binaries':{name:sha256(config.build_dir/name) for name in ('nr-softmodem','nr-uesoftmodem','librfsimulator.so','libparams_libconfig.so','libldpc.so','libdfts.so')},
            'trace':str(config.trace),'trace_sha256':sha256(config.trace),
            'schedule':str(config.schedule) if config.schedule else None,
            'schedule_sha256':sha256(config.schedule) if config.schedule else None,
            'bundles':bundles,'epoch':rows[0][0],'rate':rate,'interpolation':config.interpolation,
            'timing_assist':environment.get('OAI_STK_BLEND_TIMING_ASSIST','0')=='1',
            'gnb_config':str(config.gnb_config),'initial_delay_file':str(config.initial_delay_file),
            'state_file':str(config.state_file),'logs':{},'sample_rate_hz':None,
            'network':{'namespace':config.namespace,'host_veth':config.host_veth,'ue_veth':config.ue_veth,
                       'rf_host_ip':config.rf_host_ip,'rf_ue_ip':config.rf_ue_ip,'rf_port':config.rf_port,
                       'core_project':config.core_project,'owner_file':str(config.owner_file)}}


def observed_sample_rate(logs):
    values=[]
    for kind in ('gnb','ue'):
        text=logs.get(kind,'')
        # Only explicit modem/RFsim rate diagnostics qualify; no inferred PRB constant.
        number=r'([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)'
        patterns=(r'\bSTKRUNTIME\b[^\n]*?\bsample_rate_hz='+number+r'\b',
                  r'\btune_offset [+-]?[0-9.]+ Hz, sample_rate '+number+r' Hz\b',
                  r'\bHW: Configuring ru_id \d+, sample_rate '+number+r', tx/rx num_channels')
        found=[value for pattern in patterns for value in re.findall(pattern,text)]
        rates={float(value) for value in found if math.isfinite(float(value)) and float(value)>0}
        if len(rates)>1:raise ValueError('Conflicting sample rate in '+kind+' startup log')
        if not rates:return None
        values.append(rates.pop())
    if values[0]!=values[1]:raise ValueError('gNB/UE sample rate mismatch')
    return values[0]


def environments(config, environment, rate):
    env=dict(environment)
    env.update(config.to_env())
    if config.profile=='zky':
        for key in ('OAI_QD_DL_CHANNEL','OAI_QD_UL_CHANNEL'):
            if not environment.get(key):env.pop(key,None)
    elif config.profile=='legacy-handover':
        for key in ('OAI_QD_CHANNEL','OAI_QD_DL_CHANNEL','OAI_QD_UL_CHANNEL'):env.pop(key,None)
    env['OAI_STK_TRACE_RATE']=str(rate)
    env['OAI_STK_TRACE_EPOCH']=str(read_trace(config.trace)[0][0])
    return env


def launcher_environments(environment, *, qd_required=False):
    """Validate role channels, then send only directional inputs across the resolver boundary."""
    children=channel_environments(environment,qd_required=qd_required)
    if environment.get('OAI_NTN_PROFILE','zky')!='zky':
        for child in children.values():
            child.pop('OAI_QD_CHANNEL',None)
    return children


def write_manifest(path, manifest, exclusive=False):
    if exclusive:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(manifest,stream,indent=2)
    else:save_state(path,manifest)


def refresh_manifest(config):
    path=config.run_dir/'run.json'
    if not path.is_file():return
    manifest=json.loads(path.read_text())
    if manifest.get('run_id')!=config.run_id:raise ValueError('Manifest belongs to another run')
    logs={kind:Path(log).read_text(errors='replace') for kind,log in manifest['logs'].items()}
    manifest['sample_rate_hz']=observed_sample_rate(logs)
    write_manifest(path,manifest)


def record_modem(record):
    current=process_identity(record['pid'])
    if current and current[0]==record['start'] and current[1]==record['expected_executable']:
        record['executable']=current[1]
        record['phase']='running'
        return True
    return False


def start(config,args,environment):
    manifest_path=config.run_dir/'run.json'
    if config.profile!='zky' and (manifest_path.exists() or manifest_path.is_symlink()):
        raise ValueError('Run manifest already exists; choose a new run-id')
    if os.geteuid()!=0:raise SystemExit('start requires root: use sudo -E python3 local_ntn/experiment.py start')
    for name in ('nr-softmodem','nr-uesoftmodem'):
        if subprocess.run(['pgrep','-x',name],stdout=subprocess.DEVNULL).returncode==0:
            raise SystemExit(name+' already running; refusing duplicate')
    report=preflight(args.rate,environment,runtime=config)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    env=environments(config,environment,args.rate)
    print(json.dumps(check_network(env)),flush=True)
    children=launcher_environments(env,qd_required=config.profile=='integrated-handover')
    config.run_dir.mkdir(parents=True,exist_ok=True)
    manifest=build_manifest(config,args.rate,env)
    manifest['initial_lead_rfsim']=args.initial_lead_rfsim
    write_manifest(manifest_path,manifest,exclusive=config.profile!='zky')
    state={'schema':2,'run_id':config.run_id,'profile':config.profile,'status':'launching','processes':{}}
    manager=NetworkManager(config)
    network_up=False
    started=[]
    try:
        call(['python3',str(BASE/'prepare_local.py'),'--profile',config.profile,'--run-id',config.run_id,
              '--rate',str(args.rate),'--initial-lead-rfsim',str(args.initial_lead_rfsim)],env=env)
        manifest['network']['owner']=manager.up()
        network_up=True
        write_manifest(manifest_path,manifest)
        for kind in ('gnb','ue'):
            log=config.run_dir/f'{kind}-{args.label}.log'
            fd=os.open(log,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'w') as stream:
                process=subprocess.Popen(['bash',str(BASE/'run_local.sh'),kind],stdout=stream,
                    stderr=subprocess.STDOUT,env=children[kind],start_new_session=True)
            started.append(process)
            identity=process_identity(process.pid)
            record={'pid':process.pid,'start':identity[0] if identity else None,
                    'executable':identity[1] if identity else None,'phase':'launching',
                    'expected_executable':str(config.build_dir/('nr-softmodem' if kind=='gnb' else 'nr-uesoftmodem')),
                    'log':str(log),'rate':args.rate}
            state['processes'][kind]=record
            save_state(config.state_file,state)
            manifest['logs'][kind]=str(log)
            write_manifest(manifest_path,manifest)
            print('Started',kind,process.pid,flush=True)
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                if process.poll() is not None:raise SystemExit(kind+' exited; inspect private log')
                # A log marker alone is insufficient: wait for the shell to exec the selected binary.
                ready=kind=='ue' or 'No connected device' in log.read_text(errors='replace')
                if ready and record_modem(record):break
                time.sleep(.2)
            else:raise SystemExit(kind+' readiness timeout')
            save_state(config.state_file,state)
        state['status']='running'
        save_state(config.state_file,state)
        refresh_manifest(config)
    except BaseException:
        state['status']='launch_failed'
        save_state(config.state_file,state)
        # Shutdown handles shell→selected modem transitions only during launch, with unchanged starttime.
        # Timeout leaves state intact and intentionally prevents network teardown.
        stop_owned(config.state_file,config.run_id)
        for process in started:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                raise RuntimeError('Launched child exit unconfirmed; network retained for inspection') from None
        if network_up and config.profile!='zky':manager.down()
        raise


def safe_tail(path):
    # Only structured numerical trace records are safe to display from private modem logs.
    lines=Path(path).read_text(errors='replace').splitlines()
    for line in [line for line in lines if re.search(r'\b(STKTRACE2|STKSCHEDULE)\b',line)][-5:]:
        if re.search(r'\b(?:Ki|OPc|K|key|imsi|password)\b',line,re.I):continue
        print(line)


def traffic(config,args,env):
    call(['python3',str(BASE/'verify_network.py'),'--profile',config.profile,'--run-id',config.run_id],env=env)
    ns=['ip','netns','exec',config.namespace]
    info=json.loads(subprocess.check_output(['ip','-n',config.namespace,'-j','-4','addr','show','dev','oaitun_ue1']))
    addr=info[0]['addr_info'][0]['local']
    call(['ip','-n',config.namespace,'route','replace',config.ext_dn_ip+'/32','dev','oaitun_ue1','src',addr])
    print('UE source',addr,'destination ext-DN',config.ext_dn_ip,'through oaitun_ue1',flush=True)
    if args.action=='ping':
        call(ns+['ping','-n','-I','oaitun_ue1','-c',str(args.ping_count),'-W','5',config.ext_dn_ip])
        return
    iperf_bin=env.get('OAI_IPERF3_BIN') or shutil.which('iperf3')
    if not iperf_bin:raise ValueError('iperf3 not found; install it or export OAI_IPERF3_BIN')
    prefix=['env','LD_LIBRARY_PATH='+env['OAI_IPERF3_LIBRARY_PATH']] if env.get('OAI_IPERF3_LIBRARY_PATH') else []
    iperf=prefix+[iperf_bin]
    container=json.loads(subprocess.check_output(['docker','inspect',config.ext_dn_container]))[0]
    pid=container['State']['Pid']
    server=subprocess.Popen(['nsenter','-t',str(pid),'-n']+iperf+['-s','-1','-p','5203'],
                            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        time.sleep(.3)
        if server.poll() is not None:raise RuntimeError('iperf server exited')
        call(ns+iperf+['-c',config.ext_dn_ip,'-p','5203','-B',addr,'-u','-b','100K','-t',str(args.iperf_seconds),'-i','5']
             +(['-R'] if args.reverse else []))
    finally:
        if server.poll() is None:server.terminate()
        server.wait(timeout=5)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('preflight','start','stop','status','ping','iperf'))
    parser.add_argument('--profile',default='')
    parser.add_argument('--run-id',default='')
    parser.add_argument('--rate',type=float,default=0)
    parser.add_argument('--label',default='static-final')
    parser.add_argument('--reverse',action='store_true')
    parser.add_argument('--ping-count',type=int,default=10)
    parser.add_argument('--iperf-seconds',type=int,default=15)
    parser.add_argument('--initial-lead-rfsim',type=float,default=0)
    args=parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.label):parser.error('invalid label')
    if not math.isfinite(args.rate) or not 0<=args.rate<=1:parser.error('--rate must be finite and between 0 and 1')
    if not math.isfinite(args.initial_lead_rfsim) or args.initial_lead_rfsim<0:parser.error('--initial-lead-rfsim must be finite and nonnegative')
    if args.ping_count<1 or args.iperf_seconds<1:parser.error('traffic counts and duration must be positive')
    try:
        config=resolve_runtime(BASE.parent,args.profile,args.run_id,os.environ)
        if args.action=='preflight':print(json.dumps(preflight(args.rate,dict(os.environ),runtime=config),ensure_ascii=False,indent=2))
        elif args.action=='start':start(config,args,dict(os.environ))
        elif args.action=='stop':
            recorded=config.state_file.exists()
            stop_owned(config.state_file,config.run_id)
            if recorded and config.profile!='zky' and (config.owner_file.exists() or config.owner_file.is_symlink()):NetworkManager(config).down()
            print('Owned modem processes stopped')
        elif args.action=='status':
            refresh_manifest(config)
            if config.state_file.exists():
                _,records=read_state(config.state_file,config.run_id)
                for kind,record in records.items():
                    print(kind,'alive=',matches(record));safe_tail(record['log'])
            if Path('/run/netns',config.namespace).exists():call(['ip','-n',config.namespace,'-br','addr'])
            else:print('UE namespace is not present')
        else:
            env=dict(os.environ)
            runtime_env=config.to_env()
            if config.profile=='zky':
                for key in ('OAI_IPERF3_BIN','OAI_IPERF3_LIBRARY_PATH'):
                    runtime_env.pop(key,None)
            env.update(runtime_env)
            traffic(config,args,env)
    except (ValueError,OSError,KeyError,RuntimeError,subprocess.CalledProcessError) as error:
        parser.exit(1,f'Experiment failed: {error}\n')


if __name__=='__main__':main()
