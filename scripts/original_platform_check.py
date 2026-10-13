"""Original platform fingerprints and bounded private business re-verification.
A Task8 snapshot cannot reconstruct the missing Task1 dirty-source baseline.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,os,re,secrets,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local_ntn'))
from network_owner import NetworkManager
from run_state import process_identity,stop_owned
ORIGINAL=Path('/mnt/d/实验室学习工作/杂活/雄安/OAI调研')
OAI=Path('/home/kayoko/OAI/openairinterface5g')
CORE=Path('/home/kayoko/oai-cn5g-fed')
BUILD=OAI/'cmake_targets/ran_build/build'
PROTECTED=[ORIGINAL/'local_ntn/stk_trace.csv',OAI/'ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf',
CORE/'docker-compose-v220/docker-compose-basic-nrf.yaml',CORE/'docker-compose-v220/docker-compose-extdn-ubuntu.yaml',
BUILD/'nr-softmodem',BUILD/'nr-uesoftmodem',BUILD/'librfsimulator.so']
CORE_ORDER=('mysql','oai-nrf','oai-udr','oai-udm','oai-ausf','oai-amf','oai-smf','oai-upf','oai-ext-dn')
NETWORK_CONFIG=SimpleNamespace(profile='zky',namespace='oai-stk-ue',host_veth='oai-stk-host',ue_veth='oai-stk-peer',
rf_host_ip='10.201.0.1',rf_ue_ip='10.201.0.2',owner_file=Path('/run/oai-stk-ue.owner.json'))

def command(argv):
    return subprocess.run(argv,check=True,capture_output=True,text=True,timeout=120).stdout

def fingerprint(path):
    path=Path(path)
    try:info=path.lstat()
    except FileNotFoundError:return {'type':'missing'}
    if stat.S_ISLNK(info.st_mode):
        return {'type':'symlink','sha256':hashlib.sha256(os.readlink(path).encode()).hexdigest(),'mtime_ns':info.st_mtime_ns}
    if not stat.S_ISREG(info.st_mode):raise ValueError('Nonregular fingerprint input')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):digest.update(data)
    return {'type':'file','sha256':digest.hexdigest(),'mtime_ns':info.st_mtime_ns}

def process_cwd(pid):
    return Path(os.readlink(f'/proc/{pid}/cwd')).resolve()

def ip_executable():
    value=shutil.which('ip')
    if not value:raise ValueError('Local ip executable missing')
    return str(Path(value).resolve())

def original_initial_delay():
    value=(ORIGINAL/'local_ntn/initial_delay_ms.txt').read_text().strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+',value):raise ValueError('Invalid original delay')
    return value


def source_snapshot(root,runner=command):
    root=Path(root).resolve();argv=['git','-c','safe.directory='+str(root),'-C',str(root)]
    if Path(runner(argv+['rev-parse','--show-toplevel']).strip()).resolve()!=root:raise ValueError('Git root differs')
    head=runner(argv+['rev-parse','HEAD']).strip()
    if not re.fullmatch('[0-9a-f]{40}',head):raise ValueError('Invalid HEAD')
    status_text=runner(argv+['status','--porcelain=v1','-z'])
    names=(runner(argv+['diff','--name-only','--no-renames','HEAD','-z'])+runner(argv+['ls-files','--others','--exclude-standard','-z'])).split('\0');hashes={}
    index_sha256=hashlib.sha256(runner(argv+['ls-files','--stage','-z']).encode()).hexdigest()
    for relative in sorted(set(names)-{''}):
        if Path(relative).is_absolute() or '..' in Path(relative).parts:raise ValueError('Invalid source path')
        hashes[relative]=fingerprint(root/relative)
    return {'head':head,'status':status_text,'dirty_files':hashes,'index_sha256':index_sha256}

def container_info(item):
    labels=item.get('Config',{}).get('Labels') or {}
    return {'id':item['Id'],'name':item['Name'].lstrip('/'),'running':bool(item['State']['Running']),
      'health':item['State'].get('Health',{}).get('Status'),'started_at':item['State'].get('StartedAt'),
      'labels':{k:labels.get(k) for k in ('com.docker.compose.project','com.docker.compose.service',
      'com.docker.compose.project.working_dir','com.docker.compose.project.config_files')}}

def containers(runner=command):
    return {i['name']:i for identifier in runner(['docker','ps','-aq']).split()
      for i in [container_info(json.loads(runner(['docker','inspect',identifier]))[0])]}

def network_snapshot(runner=command):
    return {'namespaces':sorted(n['name'] for n in json.loads(runner(['ip','-j','netns','list']))),
      'rf_links':{n['ifname']:n['ifindex'] for n in json.loads(runner(['ip','-d','-j','link','show']))
      if n['ifname'] in ('oai-stk-host','oai-stk-peer','ntn-qd-host','ntn-qd-peer')},
      'markers':{str(p):fingerprint(p) for p in (Path('/run/oai-stk-ue.owner.json'),Path('/run/ntn-qd-ue.owner.json'))}}

def snapshot(runner=command):
    return {'schema':1,'captured_at_utc':datetime.now(timezone.utc).isoformat(),
      'purpose':'Task8 pre-live protection; not Task1 pre-change dirty baseline',
      'sources':{str(p):source_snapshot(p,runner) for p in (ORIGINAL,OAI,CORE)},
      'files':{str(p):fingerprint(p) for p in PROTECTED},'containers':containers(runner),'network':network_snapshot(runner)}

def validate_snapshot(data):
    if data.get('schema')!=1 or set(data.get('sources',{}))!={str(p) for p in (ORIGINAL,OAI,CORE)}:
        raise ValueError('Incomplete original source snapshot')
    if set(data.get('files',{}))!={str(p) for p in PROTECTED}:raise ValueError('Incomplete protected files')
    for item in data['files'].values():
        if item.get('type')!='file' or not re.fullmatch('[0-9a-f]{64}',item.get('sha256','')):
            raise ValueError('Protected regular file missing')
    expected={str(ORIGINAL):'f30bc90a626214d227a7991d7429cf7723233f96',
       str(OAI):'c4125d1c740181ab1f7da0e7dd1d04ed07c37670',str(CORE):'212f92fc6a2fb82b5df1e8f4ef20075e75acefb3'}
    if any(data['sources'][p]['head']!=head for p,head in expected.items()):
        raise ValueError('Original source revision changed')
    return data


def compare_snapshots(before,after):
    if before.get('schema')!=1 or after.get('schema')!=1:raise ValueError('Snapshot schema differs')
    differences=[k for k in ('sources','files','network') if before[k]!=after[k]]
    def stable(items):
        return {n:{k:v for k,v in i.items() if k not in ('health','started_at')} for n,i in items.items()}
    if stable(before['containers'])!=stable(after['containers']):differences.append('containers')
    return differences

def compare_early(early,current):
    files=early.get('files',{})
    if not files or any(not re.fullmatch('[0-9a-f]{64}',v.get('sha256','')) or not isinstance(v.get('mtime_ns'),int) for v in files.values()):
        raise ValueError('Early file fingerprints invalid')
    match=all(current.get('files',{}).get(p,{}).get('sha256')==v['sha256'] and
      current.get('files',{}).get(p,{}).get('mtime_ns')==v['mtime_ns'] for p,v in files.items())
    valid=bool(early.get('sources')) and all(re.fullmatch('[0-9a-f]{40}',v.get('head','')) and
      'dirty_files' in v for v in early.get('sources',{}).values())
    return {'protected_files_match':match,'early_source_state_verified':bool(valid),
      'limitation':'No valid Task1 pre-change complete dirty-source hash snapshot; earlier Git fields contained errors'}

def require_container_identity(before,current):
    if any(before[k]!=current[k] for k in ('id','name','labels')):raise ValueError('Container identity changed')
    if 'owned_started_at' in before and before['owned_started_at']!=current.get('started_at'):
        raise ValueError('Container was restarted by another operation')

def started_container_ids(before,current,selected):
    return sorted(k for k in selected if not before[k] and current[k])

def release_network(manager,owner):
    if manager.verify()!=owner:raise ValueError('Network identity changed')
    manager.down()

def signal_record(record,sig):
    if not record or process_identity(record['pid'])!=(record['start'],record['executable']):
        raise ValueError('Process identity changed')
    if os.getpgid(record['pid'])!=record['pid']:raise ValueError('Process group differs')
    os.killpg(record['pid'],sig)

def parse_ping(text):
    found=re.findall(r'(\d+) packets transmitted,\s*(\d+) received,',text)
    if len(found)!=1:raise ValueError('Ping summary missing or ambiguous')
    return dict(zip(('sent','received'),map(int,found[0])))

def parse_udp(text):
    found=re.findall(r'(\d+)/(\d+)\s*\([\d.]+%\)\s+receiver\b',text)
    if len(found)!=1:raise ValueError('Receiver summary missing or ambiguous')
    return dict(zip(('lost','total'),map(int,found[0])))

def run_short(ops):
    result={'passed':False}
    try:
        ops.preflight();ops.core_up();ops.network_up();ops.start();values=ops.business();result.update(values)
        result['passed']=(values['ping']==dict(sent=30,received=30) and
          all(values[k]['total']>0 and values[k]['lost']==0 for k in ('uplink','downlink')))
    except (Exception,KeyboardInterrupt) as error:result['error']=type(error).__name__
    finally:
        previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        for sig in previous:signal.signal(sig,signal.SIG_IGN)
        try:ops.cleanup()
        except Exception as error:result['cleanup_error']=type(error).__name__;result['passed']=False
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)
    return result

def private_destination(path):
    path=Path(path).absolute()
    if not any(path.resolve().is_relative_to((ROOT/p).resolve()) for p in ('.private','.runtime')):
        raise ValueError('Output escapes independent private/runtime scope')
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('Output symlink refused')
    return path

def save_new(path,data):
    path=private_destination(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(data,stream,indent=2);stream.write('\n')


def process_argv(pid):
    return [v.decode() for v in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if v]

def launch_identity(process,executable):
    identity=process_identity(process.pid)
    if identity is None:
        if process.poll() is None:raise RuntimeError('Child identity unavailable')
        return None
    return {'pid':process.pid,'start':identity[0],'executable':identity[1],
       'phase':'launching','expected_executable':str(Path(shutil.which(executable) or executable).resolve())}

def stop_child(process,record,destination,run_id):
    if process.poll() is None:
        save_new(destination,{'schema':2,'run_id':run_id,'processes':{'child':record}})
        stop_owned(destination,run_id)
    process.wait(timeout=5)

class OriginalShortRun:
    def __init__(self,tag,before,output):
        self.tag=tag;self.before=before;self.output=private_destination(output)
        self.output.mkdir(parents=True,exist_ok=False)
        self.manager=NetworkManager(NETWORK_CONFIG)
        self.owner=None;self.started={};self.records={};self.controller=None;self.controller_record=None
        self.state=ORIGINAL/'local_ntn/processes.json';self.old_state=None;self.state_owned=False;self.logs_claimed=False
        self.token=secrets.token_hex(32);self.counter=0
        self.environment={k:v for k,v in os.environ.items() if not k.startswith('OAI_')}
        self.environment['OAI_ORIGINAL_CHECK_TOKEN']=self.token
        self.log_paths=[ORIGINAL/'local_ntn'/f'{kind}-{tag}.log' for kind in ('gnb','ue')]
        self.expected={str((BUILD/'nr-softmodem').resolve()),str((BUILD/'nr-uesoftmodem').resolve())}
    def capture(self,name,argv,timeout=120):
        path=self.output/(name+'.log')
        with path.open('xb') as stream:
            process=subprocess.Popen(argv,env=self.environment,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            record=launch_identity(process,argv[0])
            try:
                code=process.wait(timeout=timeout)
                if code:raise subprocess.CalledProcessError(code,argv)
            finally:
                self.counter+=1
                stop_child(process,record,self.output/f'capture-{self.counter}-owned.json',self.tag)
        return path.read_text(errors='replace')
    def preflight(self):
        if compare_snapshots(self.before,snapshot()):raise ValueError('Original changed since pre-live snapshot')
        for name in ('nr-softmodem','nr-uesoftmodem'):
            result=subprocess.run(['pgrep','-x',name],capture_output=True)
            if result.returncode!=1:raise ValueError('Existing modem or process probe failure')
        self.manager.preflight()
        if any(p.exists() or p.is_symlink() for p in self.log_paths):raise ValueError('Run logs already exist')
        if self.state.is_symlink():raise ValueError('Original state symlink refused')
        self.old_state=self.state.read_bytes() if self.state.exists() else None
        if self.old_state:
            for record in json.loads(self.old_state).values():
                if process_identity(record['pid']) is not None:raise ValueError('Existing state PID refused')
        existing=self.before['containers']
        if any(name not in existing for name in CORE_ORDER):raise ValueError('Required original container missing')
        projects={existing[name]['labels']['com.docker.compose.project'] for name in CORE_ORDER}
        if len(projects)!=1 or None in projects:raise ValueError('Original Compose project mismatch')
        for name in CORE_ORDER:
            item=existing[name]
            if item['running'] or not item['labels']['com.docker.compose.service']:
                raise ValueError('Original containers must be stopped and Compose-owned')
        self.logs_claimed=True
    def core_up(self):
        for name in CORE_ORDER:
            expected=self.before['containers'][name]
            current=container_info(json.loads(command(['docker','inspect',expected['id']]))[0])
            require_container_identity(expected,current)
            if current['running']:raise ValueError('Container running state changed')
            begin_ns=time.time_ns()
            result=self.capture('start-'+name,['docker','start',expected['id']])
            end_ns=time.time_ns()
            if result.strip()!=expected['id']:raise ValueError('Start command did not confirm exact ID')
            current=container_info(json.loads(command(['docker','inspect',expected['id']]))[0])
            require_container_identity(expected,current)
            stamp=current.get('started_at') or ''
            normalized=re.sub(r'(\.\d{6})\d+',r'\1',stamp).replace('Z','+00:00')
            started_ns=int(datetime.fromisoformat(normalized).timestamp()*1e9)
            if not begin_ns<=started_ns<=end_ns:raise ValueError('Container start is not attributable to this command')
            self.started[name]=dict(expected,owned_started_at=stamp)
            deadline=time.monotonic()+120
            while True:
                current=container_info(json.loads(command(['docker','inspect',expected['id']]))[0])
                require_container_identity(expected,current)
                if current['running'] and current['health'] in (None,'healthy'):
                    if started_container_ids({expected['id']:expected['running']},{expected['id']:current['running']},{expected['id']})!=[expected['id']]:
                        raise ValueError('No verified stopped-to-running transition')
                    break
                if time.monotonic()>deadline or current['health']=='unhealthy':raise RuntimeError('Core health failed')
                time.sleep(.25)
    def network_up(self):self.owner=self.manager.up()
    def has_token(self,pid):
        try:return ('OAI_ORIGINAL_CHECK_TOKEN='+self.token).encode() in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):return False
    def approved_process(self,pid,identity,kind=None):
        if os.getpgid(pid)!=pid or os.getsid(pid)!=pid:
            raise ValueError('Unapproved launch session/group')
        expected={k:str((BUILD/('nr-softmodem' if k=='gnb' else 'nr-uesoftmodem')).resolve()) for k in ('gnb','ue')}
        if identity[1] in expected.values():
            if kind and identity[1]!=expected[kind]:raise ValueError('Wrong modem kind')
            record={'pid':pid,'start':identity[0],'executable':identity[1]}
        elif identity[1] in ('/usr/bin/bash','/bin/bash'):
            argv=process_argv(pid)
            if len(argv)!=3 or Path(argv[0]).name!='bash' or argv[1]!=str(ORIGINAL/'local_ntn/run_local.sh') or argv[2] not in expected:
                raise ValueError('Unknown token launch shell')
            if kind and argv[2]!=kind:raise ValueError('Wrong launch kind')
            record={'pid':pid,'start':identity[0],'executable':identity[1],'phase':'launching','expected_executable':expected[argv[2]]}
        elif identity[1]==ip_executable():
            if kind not in (None,'ue'):raise ValueError('Wrong namespace launch kind')
            argv=['ip','netns','exec','oai-stk-ue','./nr-uesoftmodem',
              '-O','/home/kayoko/.local/share/oai-stk/ue.local.conf',
              '--rfsimulator.[0].serveraddr','10.201.0.1',
              '--rfsimulator.[0].prop_delay',original_initial_delay(),
              '--band','254','-C','2488400000','--CO','-873500000','-r','25',
              '--numerology','0','--ssb','60','--rfsim',
              '--rfsimulator.[0].options','chanmod','--time-sync-I','0.1',
              '--autonomous-ta','--cont-fo-comp','2','--num-ul-actors','1']
            actual=process_argv(pid)
            if not actual or Path(actual[0]).name!='ip' or actual[1:]!=argv[1:] or Path(process_cwd(pid)).resolve()!=BUILD.resolve():
                raise ValueError('Unknown namespace launch arguments')
            record={'pid':pid,'start':identity[0],'executable':identity[1],'phase':'launching',
              'expected_executable':expected['ue'],'intermediate':'original-ue-ip'}
        else:raise ValueError('Unknown token executable')
        current=process_identity(pid)
        if current is None:return None
        allowed={record['executable'],record.get('expected_executable')}
        if current[0]!=identity[0]:raise ValueError('Launch PID reused while checking')
        if current[1] not in allowed:
            if record.get('phase')=='launching' and record['executable'] in ('/usr/bin/bash','/bin/bash') and record['expected_executable']==expected['ue'] and current[1]==ip_executable():
                return self.approved_process(pid,current,'ue')
            raise ValueError('Launch identity changed while checking')
        return record
    def remember(self,pid,identity,launch_record=None):
        previous=self.records.get(str(pid))
        if previous:
            if previous['start']!=identity[0]:raise ValueError('PID reused')
            allowed={previous['executable']}
            if previous.get('phase')=='launching':allowed.add(previous['expected_executable'])
            if launch_record and launch_record.get('intermediate')=='original-ue-ip' and previous.get('phase')=='launching' and previous['executable'] in ('/usr/bin/bash','/bin/bash') and previous.get('expected_executable')==launch_record.get('expected_executable'):
                allowed.add(launch_record['executable'])
            if identity[1] not in allowed:raise ValueError('Unknown executable transition')
        elif identity[1] not in self.expected and launch_record is None:
            raise ValueError('Unknown first executable')
        self.records[str(pid)]=launch_record or {'pid':pid,'start':identity[0],'executable':identity[1]}
    def claim_state(self,raw,state):
        if not state or not set(state).issubset({'gnb','ue'}):return False
        for kind,value in state.items():
            if value.get('log') not in {str(p) for p in self.log_paths} or value.get('rate')!=1:return False
            identity=process_identity(value['pid'])
            if identity:
                if identity[0]!=value.get('start') or not self.has_token(value['pid']):raise ValueError('Foreign live state refused')
                record=self.approved_process(value['pid'],identity,kind)
                if record:self.remember(value['pid'],identity,record)
        self.state_owned=True;self.claimed_state=raw
        return True
    def collect(self):
        if self.logs_claimed and self.state.exists():
            raw=self.state.read_bytes();self.claim_state(raw,json.loads(raw))
        for path in Path('/proc').iterdir():
            if not path.name.isdigit():continue
            pid=int(path.name);identity=process_identity(pid)
            if not identity or not self.has_token(pid):continue
            # The live, exact controller session owns transient prepare/network children.
            if self.controller and self.controller_record:
                parent=process_identity(self.controller.pid)
                allowed={self.controller_record['executable'],self.controller_record.get('expected_executable')}
                if parent and parent[0]==self.controller_record['start'] and parent[1] in allowed:
                    if os.getpgid(pid)==self.controller.pid and os.getsid(pid)==self.controller.pid:continue
            record=self.approved_process(pid,identity)
            if record:self.remember(pid,identity,record)

    def start(self):
        with (self.output/'start.log').open('xb') as log:
            argv=[sys.executable,str(ORIGINAL/'local_ntn/experiment.py'),'start','--rate','1','--label',self.tag]
            self.controller=subprocess.Popen(argv,env=self.environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            self.controller_record=launch_identity(self.controller,argv[0])
            deadline=time.monotonic()+75
            while time.monotonic()<deadline:
                self.collect()
                if self.controller.poll() is not None and self.controller.returncode!=0:raise RuntimeError('Original start failed')
                address=subprocess.run(['ip','-n','oai-stk-ue','-j','-4','addr','show','dev','oaitun_ue1'],capture_output=True,text=True)
                if address.returncode==0:
                    rows=json.loads(address.stdout)
                    if rows and any(x.get('local') for x in rows[0].get('addr_info',[])):
                        if self.controller.wait(timeout=5)!=0:raise RuntimeError('Original launch failed')
                        self.collect();return
                time.sleep(.1)
            raise RuntimeError('PDU readiness timeout')
    def business(self):
        argv=[sys.executable,str(ORIGINAL/'local_ntn/experiment.py')]
        return {'ping':parse_ping(self.capture('ping',argv+['ping','--ping-count','30'],55)),
          'uplink':parse_udp(self.capture('udp-uplink',argv+['iperf','--iperf-seconds','15'],35)),
          'downlink':parse_udp(self.capture('udp-downlink',argv+['iperf','--iperf-seconds','15','--reverse'],35))}
    def restore_state(self):
        if not self.state_owned or not hasattr(self,'claimed_state'):
            raise ValueError('State was not associated with this invocation')
        fd=os.open(self.state,os.O_RDWR|os.O_NOFOLLOW)
        try:
            opened=os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):raise ValueError('Nonregular state')
            current=os.read(fd,max(opened.st_size+1,1))
            if current!=self.claimed_state:raise ValueError('Foreign state replacement refused')
            named=self.state.lstat()
            if (named.st_dev,named.st_ino)!=(opened.st_dev,opened.st_ino):
                raise ValueError('State pathname replaced')
            if os.fstat(fd).st_mtime_ns!=opened.st_mtime_ns:raise ValueError('State mutated during check')
            if self.old_state is None:
                self.state.unlink()
            else:
                os.lseek(fd,0,os.SEEK_SET)
                with os.fdopen(os.dup(fd),'wb') as stream:
                    stream.write(self.old_state);stream.truncate();stream.flush();os.fsync(stream.fileno())
                named=self.state.lstat()
                if (named.st_dev,named.st_ino)!=(opened.st_dev,opened.st_ino):
                    raise ValueError('State pathname changed during restore')
        finally:os.close(fd)

    def cleanup(self):
        errors=[]
        if self.controller:
            try:stop_child(self.controller,self.controller_record,self.output/'controller-owned.json',self.tag)
            except Exception as error:errors.append(type(error).__name__)
        try:
            self.collect()
            if self.records:
                state_file=self.output/'owned-processes.json'
                save_new(state_file,{'schema':2,'run_id':self.tag,'processes':self.records})
                stop_owned(state_file,self.tag)
            if any(process_identity(r['pid']) is not None and self.has_token(r['pid']) for r in self.records.values()):
                raise RuntimeError('Owned process retained')
        except Exception as error:errors.append(type(error).__name__)
        if not errors and self.owner is not None:
            try:release_network(self.manager,self.owner)
            except Exception as error:errors.append(type(error).__name__)
        if self.state_owned and not errors:
            try:self.restore_state()
            except Exception as error:errors.append(type(error).__name__)
        if self.logs_claimed:
            for path in self.log_paths:
                if path.is_file() and not path.is_symlink():
                    try:shutil.move(str(path),str(self.output/path.name))
                    except Exception as error:errors.append(type(error).__name__)
        for name,expected in reversed(list(self.started.items())):
            try:
                current=container_info(json.loads(command(['docker','inspect',expected['id']]))[0])
                require_container_identity(expected,current)
                if current['running']:self.capture('stop-'+name,['docker','stop','--time','10',expected['id']],25)
            except Exception as error:errors.append(type(error).__name__)
        if errors:raise RuntimeError('Owned cleanup failed')

class SignalGuard:
    def __enter__(self):
        self.previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        for sig in self.previous:signal.signal(sig,self.handle)
    def handle(self,_sig,_frame):raise KeyboardInterrupt()
    def __exit__(self,*_args):
        for sig,handler in self.previous.items():signal.signal(sig,handler)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('snapshot','compare','short-run'))
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--early-snapshot',type=Path)
    parser.add_argument('--tag',default='integration-after')
    args=parser.parse_args(argv)
    if os.geteuid()!=0:parser.error('Requires root')
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}',args.tag):parser.error('Invalid tag')
    os.umask(0o077)
    try:
        target=private_destination(args.snapshot)
        if args.action=='snapshot':
            data=validate_snapshot(snapshot());save_new(target,data)
            result={'passed':True,'captured_at_utc':data['captured_at_utc'],'purpose':data['purpose']}
        elif args.action=='compare':
            before=validate_snapshot(json.loads(target.read_text()));current=validate_snapshot(snapshot())
            differences=compare_snapshots(before,current)
            result={'passed':not differences,'differences':differences}
            if args.early_snapshot:
                result['early']=compare_early(json.loads(args.early_snapshot.read_text()),current)
                result['passed']=result['passed'] and result['early']['protected_files_match']
        else:
            before=validate_snapshot(json.loads(target.read_text()));output=target.parent/('original-short-'+args.tag)
            with SignalGuard():result=run_short(OriginalShortRun(args.tag,before,output))
            result['differences']=compare_snapshots(before,snapshot())
            if result['differences']:result['passed']=False
            save_new(output/'report.json',result)
        print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
    except (Exception,KeyboardInterrupt) as error:
        print(json.dumps({'passed':False,'error':type(error).__name__}));return 1

if __name__=='__main__':raise SystemExit(main())
