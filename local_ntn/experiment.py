"""Local experiment controller, run in WSL as root. Only stops its own recorded PIDs."""
import argparse,json,os,re,signal,socket,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
STATE=BASE/'processes.json'
p=argparse.ArgumentParser();p.add_argument('action',choices=['start','stop','status','ping','iperf'])
p.add_argument('--rate',type=float,default=0);p.add_argument('--label',default='static-final')
p.add_argument('--reverse',action='store_true')
p.add_argument('--ping-count',type=int,default=10)
p.add_argument('--iperf-seconds',type=int,default=15)
a=p.parse_args()
def call(cmd,**kw):return subprocess.run(cmd,check=True,**kw)
def identity(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().split()[21]
    except FileNotFoundError:return None
def safe_tail(path):
    lines=Path(path).read_text(errors='replace').splitlines()
    pattern='STKTRACE2|successful|succeeded|Reject|REJECT|PDU|oaitun|Assertion|Write queue|RRC_CONNECTED|Authentication|SECURITY|Error decoding PBCH'
    selected=[s for s in lines if re.search(pattern,s) and 'STKTRACE2' not in s][-10:]
    selected += [s for s in lines if 'STKTRACE2' in s][-5:]
    for line in selected:
        print(re.sub(r'\b(Ki|OPc|K|key)=[^, ]+',r'\1=[REDACTED]',line))
if a.action=='stop':
    if STATE.exists():
        for v in json.loads(STATE.read_text()).values():
            if v['start'] is not None and identity(v['pid'])==v['start']:
                try:
                    os.killpg(v['pid'],signal.SIGTERM)
                    print('Stopped owned process group',v['pid'])
                except ProcessLookupError:pass
elif a.action=='start':
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.label):p.error('invalid label')
    if subprocess.run(['pgrep','-x','nr-softmodem'],stdout=subprocess.DEVNULL).returncode==0:
        raise SystemExit('gNB already running; use stop for this controller or stop your manual process')
    if subprocess.run(['pgrep','-x','nr-uesoftmodem'],stdout=subprocess.DEVNULL).returncode==0:
        raise SystemExit('UE already running; refusing duplicate')
    prepare_cmd=['python3',str(BASE/'prepare_local.py'),'--rate',str(a.rate)]
    initial_lead=os.environ.get('OAI_STK_INITIAL_LEAD_RFSIM')
    if initial_lead is not None:
        prepare_cmd += ['--initial-lead-rfsim', initial_lead]
    call(prepare_cmd)
    call(['bash',str(BASE/'local_network.sh')])
    env=os.environ.copy();env['OAI_STK_TRACE_RATE']=str(a.rate)
    state={}
    for kind in ('gnb','ue'):
        log=BASE/f'{kind}-{a.label}.log'
        with log.open('w') as f:
            process=subprocess.Popen(['bash',str(BASE/'run_local.sh'),kind],stdout=f,stderr=subprocess.STDOUT,
                env=env,start_new_session=True)
        state[kind]={'pid':process.pid,'start':identity(process.pid),'log':str(log),'rate':a.rate}
        STATE.write_text(json.dumps(state,indent=2))
        print('Started',kind,process.pid,flush=True)
        if kind=='gnb':
            deadline=time.monotonic()+30
            # Read log readiness instead of probing TCP: RFsim treats a probe as a UE.
            while time.monotonic()<deadline:
                if process.poll() is not None: raise SystemExit('gNB exited; inspect log')
                if 'No connected device' in log.read_text(errors='replace'):break
                time.sleep(.2)
            else:raise SystemExit('gNB readiness timeout')
elif a.action=='status':
    if STATE.exists():
        for kind,v in json.loads(STATE.read_text()).items():
            print(kind,'alive=',v['start'] is not None and identity(v['pid'])==v['start']);safe_tail(v['log'])
    call(['ip','-n','oai-stk-ue','-br','addr'])
else:
    call(['python3',str(BASE/'verify_network.py')])
    ns=['ip','netns','exec','oai-stk-ue']
    info=json.loads(subprocess.check_output(['ip','-n','oai-stk-ue','-j','-4','addr','show','dev','oaitun_ue1']))
    addr=info[0]['addr_info'][0]['local']
    call(['ip','-n','oai-stk-ue','route','replace','192.168.70.135/32','dev','oaitun_ue1','src',addr])
    print('UE source',addr,'destination ext-DN 192.168.70.135; through oaitun_ue1',flush=True)
    if a.action=='ping':
        if a.ping_count <= 0: p.error('--ping-count must be positive')
        call(ns+['ping','-n','-I','oaitun_ue1','-c',str(a.ping_count),'-W','5','192.168.70.135'])
    else:
        if a.iperf_seconds <= 0: p.error('--iperf-seconds must be positive')
        # Same binary/version at both ends; enter only ext-DN's network namespace.
        # This keeps the same data path without changing its old Ubuntu image.
        container=json.loads(subprocess.check_output(['docker','inspect','oai-ext-dn']))[0]
        pid=container['State']['Pid']
        server=subprocess.Popen(['nsenter','-t',str(pid),'-n','/usr/bin/iperf3','-s','-1','-p','5203'],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            time.sleep(.3)
            if server.poll() is not None:raise RuntimeError(server.stderr.read().decode())
            call(ns+['iperf3','-c','192.168.70.135','-p','5203','-B',addr,'-u','-b','100K','-t',str(a.iperf_seconds),'-i','5']
                 +(['-R'] if a.reverse else []))
        finally:
            if server.poll() is None:server.terminate()
            server.wait(timeout=5)
