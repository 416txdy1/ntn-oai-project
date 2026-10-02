"""Local experiment controller, run in WSL as root. Only stops its own recorded PIDs."""
import argparse,ipaddress,json,math,os,re,shutil,signal,socket,subprocess,sys,time
from pathlib import Path
from paths import OAI_REPO, UE_CONFIG, BUILD_DIR, STK_TRACE
from preflight import preflight, channel_environments
from network_config import check_network
BASE=Path(__file__).resolve().parent
STATE=BASE/'processes.json'
EXT_DN_IP=str(ipaddress.IPv4Address(os.environ.get('OAI_EXT_DN_IP','192.168.70.135')))
EXT_DN_CONTAINER=os.environ.get('OAI_EXT_DN_CONTAINER','oai-ext-dn')
p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','start','stop','status','ping','iperf'])
p.add_argument('--rate',type=float,default=0);p.add_argument('--label',default='static-final')
p.add_argument('--reverse',action='store_true')
a=p.parse_args()
def call(cmd,**kw):return subprocess.run(cmd,check=True,**kw)
def identity(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().split()
        return None if fields[2] == 'Z' else fields[21]
    except FileNotFoundError:return None
def safe_tail(path):
    lines=Path(path).read_text(errors='replace').splitlines()
    pattern='STKTRACE2|successful|succeeded|Reject|REJECT|PDU|oaitun|Assertion|Write queue|RRC_CONNECTED|Authentication|SECURITY|Error decoding PBCH'
    selected=[s for s in lines if re.search(pattern,s) and 'STKTRACE2' not in s][-10:]
    selected += [s for s in lines if 'STKTRACE2' in s][-5:]
    for line in selected:
        print(re.sub(r'\b(Ki|OPc|K|key)=[^, ]+',r'\1=[REDACTED]',line))
def checked_preflight():
    try:
        return preflight(a.rate)
    except (ValueError, OSError, KeyError, ImportError) as error:
        raise SystemExit(f'Preflight failed: {error}') from None

if a.action=='preflight':
    print(json.dumps(checked_preflight(),ensure_ascii=False,indent=2))
elif a.action=='stop':
    if STATE.exists():
        owned = json.loads(STATE.read_text())
        def alive(value):
            return value['start'] is not None and identity(value['pid']) == value['start']
        # TERM 只是请求退出；必须等待结束，才能安全启动下一轮实验。
        for sig, timeout in ((signal.SIGTERM, 10), (signal.SIGKILL, 5)):
            for value in owned.values():
                if alive(value):
                    try: os.killpg(value['pid'], sig)
                    except ProcessLookupError: pass
            deadline = time.monotonic() + timeout
            while any(alive(value) for value in owned.values()) and time.monotonic() < deadline:
                time.sleep(.1)
            if not any(alive(value) for value in owned.values()):
                STATE.write_text('{}\n')
                print('Owned modem processes stopped')
                break
        else:
            raise SystemExit('Owned modem shutdown timed out; state retained for inspection')
elif a.action=='start':
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.label):p.error('invalid label')
    if not math.isfinite(a.rate) or not 0 <= a.rate <= 1:p.error('--rate must be between 0 and 1')
    report=checked_preflight()
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    if os.geteuid()!=0:raise SystemExit('start requires root: use sudo python3 local_ntn/experiment.py start')
    if subprocess.run(['pgrep','-x','nr-softmodem'],stdout=subprocess.DEVNULL).returncode==0:
        raise SystemExit('gNB already running; use stop for this controller or stop your manual process')
    if subprocess.run(['pgrep','-x','nr-uesoftmodem'],stdout=subprocess.DEVNULL).returncode==0:
        raise SystemExit('UE already running; refusing duplicate')
    try:
        print(json.dumps(check_network()), flush=True)
    except (ValueError, OSError) as error:
        raise SystemExit(f'Network preflight failed: {error}') from None
    call(['python3',str(BASE/'prepare_local.py'),'--rate',str(a.rate)])
    call(['bash',str(BASE/'local_network.sh')])
    env=os.environ.copy()
    env.update(OAI_STK_TRACE_RATE=str(a.rate), OAI_STK_TRACE=str(STK_TRACE),
               OAI_REPO=str(OAI_REPO), OAI_BUILD_DIR=str(BUILD_DIR), OAI_UE_CONFIG=str(UE_CONFIG))
    environments=channel_environments(env)
    state={}
    started=[]
    try:
        for kind in ('gnb','ue'):
            log=BASE/f'{kind}-{a.label}.log'
            with log.open('w') as f:
                process=subprocess.Popen(['bash',str(BASE/'run_local.sh'),kind],stdout=f,stderr=subprocess.STDOUT,
                    env=environments[kind],start_new_session=True)
            started.append(process)
            state[kind]={'pid':process.pid,'start':identity(process.pid),'log':str(log),'rate':a.rate}
            STATE.write_text(json.dumps(state,indent=2))
            print('Started',kind,process.pid,flush=True)
            if kind=='gnb':
                deadline=time.monotonic()+30
                # RFsim 会把 TCP 探测当成 UE；只查看日志就绪标记。
                while time.monotonic()<deadline:
                    if process.poll() is not None: raise SystemExit('gNB exited; inspect private log')
                    if 'No connected device' in log.read_text(errors='replace'):break
                    time.sleep(.2)
                else:raise SystemExit('gNB readiness timeout')
            else:
                time.sleep(1)
                if process.poll() is not None: raise SystemExit('UE exited; inspect private log')
    except BaseException:
        # 只清理本次已创建且身份仍匹配的进程组，不影响手动启动的实例。
        for owned in state.values():
            if owned['start'] is not None and identity(owned['pid'])==owned['start']:
                try: os.killpg(owned['pid'],signal.SIGTERM)
                except ProcessLookupError: pass
        for process in started:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                owned=next(value for value in state.values() if value['pid']==process.pid)
                if owned['start'] is not None and identity(process.pid)==owned['start']:
                    try: os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError: pass
                process.wait(timeout=5)
        STATE.write_text('{}\n')
        raise
elif a.action=='status':
    if STATE.exists():
        for kind,v in json.loads(STATE.read_text()).items():
            print(kind,'alive=',v['start'] is not None and identity(v['pid'])==v['start']);safe_tail(v['log'])
    if Path('/run/netns/oai-stk-ue').exists():
        call(['ip','-n','oai-stk-ue','-br','addr'])
    else:
        print('UE namespace is not present. Keep a WSL terminal open, then start the experiment to create it.')
else:
    call(['python3',str(BASE/'verify_network.py')])
    ns=['ip','netns','exec','oai-stk-ue']
    info=json.loads(subprocess.check_output(['ip','-n','oai-stk-ue','-j','-4','addr','show','dev','oaitun_ue1']))
    addr=info[0]['addr_info'][0]['local']
    call(['ip','-n','oai-stk-ue','route','replace',EXT_DN_IP+'/32','dev','oaitun_ue1','src',addr])
    print('UE source',addr,'destination ext-DN',EXT_DN_IP,'through oaitun_ue1',flush=True)
    if a.action=='ping':call(ns+['ping','-n','-I','oaitun_ue1','-c','10','-W','5',EXT_DN_IP])
    else:
        # nsenter -n only changes the network namespace, not the container rootfs.
        # Resolve one host-visible binary and use it at both ends so versions match.
        iperf_bin=os.environ.get('OAI_IPERF3_BIN') or shutil.which('iperf3')
        if not iperf_bin:
            raise SystemExit('iperf3 not found; install it or export OAI_IPERF3_BIN to a host-visible executable')
        iperf_prefix=[]
        if library_path:=os.environ.get('OAI_IPERF3_LIBRARY_PATH'):
            iperf_prefix=['env','LD_LIBRARY_PATH='+library_path]
        iperf=iperf_prefix+[iperf_bin]
        container=json.loads(subprocess.check_output(['docker','inspect',EXT_DN_CONTAINER]))[0]
        pid=container['State']['Pid']
        server=subprocess.Popen(['nsenter','-t',str(pid),'-n']+iperf+['-s','-1','-p','5203'],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            time.sleep(.3)
            if server.poll() is not None:raise RuntimeError(server.stderr.read().decode())
            call(ns+iperf+['-c',EXT_DN_IP,'-p','5203','-B',addr,'-u','-b','100K','-t','15','-i','5']
                 +(['-R'] if a.reverse else []))
        finally:
            if server.poll() is None:server.terminate()
            server.wait(timeout=5)
