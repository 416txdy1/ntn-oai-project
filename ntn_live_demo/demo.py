"""Isolated WebRTC live demo on the existing validated NTN runtime."""
import argparse
import datetime
import errno
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import signal
import subprocess
import sys
import time
import uuid
import urllib.request
from telemetry import RadioTelemetry
from live_config import DEFAULT_ROOT, add_runtime_arguments, radio_environment
from spatial_evidence import audit_live_run

HERE=Path(__file__).resolve().parent
TOOLS=Path('/home/kayoko/ntn-live-demo-tools')
ROOT=DEFAULT_ROOT
WINDOWS_NODE='/mnt/c/Users/WSZ/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'


def ensure_windows_runtime():
    """Validate before deployment; recover only a missing WSL PE handler."""
    def probe():
        subprocess.run([WINDOWS_NODE,'--version'],check=True,capture_output=True,text=True)
    try:
        probe()
    except OSError as error:
        if error.errno != errno.ENOEXEC:
            raise
        handler=Path('/proc/sys/fs/binfmt_misc/WSLInterop')
        register=Path('/proc/sys/fs/binfmt_misc/register')
        if ('microsoft' not in Path('/proc/sys/kernel/osrelease').read_text().lower()
                or not Path('/init').is_file() or handler.exists() or not register.exists()):
            raise
        print('WSL: restoring missing Windows interoperability handler for this session only.',flush=True)
        register.write_text(':WSLInterop:M::MZ::/init:PF\n')
        probe()


def load_helpers():
    spec=importlib.util.spec_from_file_location('ntn_suite_helpers',HERE.parent/'ntn_test_launcher/full_test.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def digest_runtime(root):
    paths=list((root/'oai_patch/current').rglob('*'))+list((root/'quadriga/oai').glob('*.c'))
    build=root/'.runtime/oai/cmake_targets/ran_build/build'
    paths += [build/n for n in ('nr-softmodem','nr-uesoftmodem','librfsimulator.so','libparams_libconfig.so','libldpc.so','libdfts.so')]
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def atomic_json(path,data):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data));temporary.chmod(0o644);os.replace(temporary,path)


def publisher_arguments(ffmpeg,source=None):
    command=[str(ffmpeg),'-hide_banner','-loglevel','warning']
    if source:
        command+=['-re','-stream_loop','-1','-i',str(source),'-map','0:v:0','-map','0:a:0',
                  '-vf','scale=640:-2,setsar=1,fps=15']
    else:
        command+=['-re','-f','lavfi','-i','testsrc=size=426x240:rate=15','-an']
    command+=['-c:v','libvpx','-pix_fmt','yuv420p','-deadline','realtime','-cpu-used','8',
              '-b:v','250k','-maxrate','250k','-bufsize','125k','-g','15','-threads','1']
    if source:
        command+=['-c:a','libopus','-b:a','64k','-ar','48000','-ac','2','-application','lowdelay']
    return command+['-rtsp_transport','tcp','-f','rtsp','rtsp://127.0.0.1:8554/live']


def audio_quality(rows,windows):
    active=[r for r in rows if r.get('audio_samples_received',0)>48000 and r.get('audio_total_energy',0)>0 and r.get('audio_track_live')]
    elapsed=(active[-1]['browser_ms']-active[0]['browser_ms'])/1000 if len(active)>1 else 0
    ratio=(active[-1]['audio_samples_received']-active[0]['audio_samples_received'])/(48000*elapsed) if elapsed>0 else 0
    unmuted=bool(active) and not active[-1].get('audio_muted',True) and active[-1].get('audio_volume',0)>0
    growth=len(active)>=15 and active[-1].get('audio_bytes_received',0)>active[-5].get('audio_bytes_received',0)
    playout=bool(active) and (active[-1].get('audio_playout_samples') is None or active[-1]['audio_playout_samples']>48000)
    window_ok=all(w.get('audio_progress_ratio',0)>=.8 and w['audio_byte_delta']>0 for w in windows)
    return {'passed':bool(growth and unmuted and playout and .8<=ratio<=1.2 and window_ok),
            'decoded_sample_progress_ratio':ratio,'measured_wall_seconds':elapsed,'final_player_unmuted':unmuted,
            'scope':'Samples received include concealment; ratio checks audio pull clock, not acoustic audibility'}


def analyze(output,run,root,case,audio_required=False,windows_renderer=False):
    sys.path.insert(0,str(root/'scripts'))
    from handover_metrics import CLOCK,ClockMap
    manifest=json.loads((run/'run.json').read_text())
    anchors=[]
    for line in (run/'ue-live-demo.log').read_text(errors='replace').splitlines():
        match=CLOCK.search(line)
        if match:
            d,ns,samples,fs,iq,stk=match.groups()
            anchors.append(dict(monotonic_ns=int(ns),samples=int(samples),sampling_rate=float(fs),iq_s=float(iq),stk_s=float(stk)))
    clock=ClockMap(anchors,manifest['epoch'],manifest['rate'],anchors[0]['sampling_rate'])
    events=[json.loads(line) for line in (output/'browser-events.jsonl').read_text().splitlines()]
    pairs=[e for e in events if e.get('event')=='clock_pair']
    rows=[]
    for event in events:
        if event.get('event')!='stats' or not pairs:continue
        pair=min(pairs,key=lambda p:abs(p['browser_ms']-event['browser_ms']))
        center=(pair['browser_begin_ms']+pair['browser_end_ms'])/2
        ns=int(pair['server_monotonic_ns']+(event['browser_ms']-center)*1e6)
        if not anchors[0]['monotonic_ns']<=ns<=anchors[-1]['monotonic_ns']:continue
        row=dict(event,**clock.map(ns))
        diagnosis=event.get('diagnostic_snapshot',{})
        row.update(diagnostic_code=diagnosis.get('code'),display_dl_cn_db=diagnosis.get('dl_cn_db'),
                   display_ue_ingress_kbps=diagnosis.get('ue_ingress_kbps'),
                   display_physical_iq_s=diagnosis.get('physical_iq_s'),display_channel_age_ms=diagnosis.get('channel_age_ms'))
        row['local_clock_pair_half_width_ms']=(pair['browser_end_ms']-pair['browser_begin_ms'])/2
        rows.append(row)
    (output/'video-timeline.json').write_text(json.dumps(rows,indent=2))
    import csv
    keys=['iq_s','stk_s','connection_state','bitrate_kbps','decoded_fps','buffer_ms','frame_gap_ms',
          'frames_decoded','frames_dropped','packets_lost','freeze_count','total_freeze_duration_s','local_clock_pair_half_width_ms',
          'audio_bitrate_kbps','audio_samples_received','audio_concealed_samples','audio_concealment_events',
          'audio_total_energy','audio_buffer_ms','audio_playout_samples','audio_muted','estimated_av_offset_ms']
    keys+=['diagnostic_code','display_dl_cn_db','display_ue_ingress_kbps','display_physical_iq_s','display_channel_age_ms']
    with (output/'video-timeline.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,keys,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    connected=[r for r in rows if r.get('connection_state')=='connected' and r.get('frames_decoded',0)>0]
    selected=[r['candidate_pair'] for r in connected if r.get('candidate_pair')]
    proof=bool(selected) and all(p.get('remote_address')==('127.0.0.1' if windows_renderer else '192.168.71.135') and p.get('remote_port')==(8190 if windows_renderer else 8189) and p.get('protocol')==('tcp' if windows_renderer else 'udp') for p in selected)
    relay_ingress=None
    if windows_renderer:
        ingress=[json.loads(s) for s in (output/'ue-relay-ingress.jsonl').read_text().splitlines()]
        ready=[p for e in ingress for p in e.get('items',[]) if p.get('name')=='live' and p.get('ready')]
        relay_ingress=bool(ready) and ready[-1].get('bytesReceived',0)>ready[0].get('bytesReceived',0)
        proof=proof and relay_ingress
    captures=(output/'ue-media-packets.private.log').read_text(errors='replace')
    packet_proof='192.168.71.135.8189' in captures and '12.2.1.' in captures
    windows=[]
    for completion in ([] if case=='static' else [8244] if case=='firsthandover' else [8244,8799]):
        window=[r for r in connected if completion-5<=r['stk_s']<=completion+5]
        windows.append({'completion_stk_s':completion,'samples':len(window),
                        'decoded_frame_delta':window[-1]['frames_decoded']-window[0]['frames_decoded'] if len(window)>1 else 0,
                        'audio_sample_delta':window[-1].get('audio_samples_received',0)-window[0].get('audio_samples_received',0) if len(window)>1 else 0,
                        'audio_byte_delta':window[-1].get('audio_bytes_received',0)-window[0].get('audio_bytes_received',0) if len(window)>1 else 0,
                        'audio_progress_ratio':(window[-1].get('audio_samples_received',0)-window[0].get('audio_samples_received',0))/(48000*((window[-1]['browser_ms']-window[0]['browser_ms'])/1000)) if len(window)>1 else 0,
                        'max_sampled_frame_gap_ms':max((r.get('frame_gap_ms') or 0 for r in window),default=None),
                        'max_native_freeze_count':max((r.get('freeze_count') or 0 for r in window),default=None)})
    passed=(len(connected)>=15 and connected[-1]['frames_decoded']>100 and proof and packet_proof
            and not any(e.get('event')=='fatal' for e in events)
            and all(w['samples']>=4 and w['decoded_frame_delta']>0 for w in windows))
    audio_check=audio_quality(connected,windows)
    audio_passed=audio_check['passed']
    if audio_required:passed=passed and audio_passed
    return {'demo_passed':passed,'case':case,'video_stats_samples':len(rows),'connected_samples':len(connected),
            'first_connected_iq_s':connected[0]['iq_s'] if connected else None,
            'last_connected_iq_s':connected[-1]['iq_s'] if connected else None,
            'decoded_frames':connected[-1]['frames_decoded'] if connected else 0,
            'native_freeze_count':connected[-1].get('freeze_count') if connected else None,
            'native_freeze_duration_wall_s':connected[-1].get('total_freeze_duration_s') if connected else None,
            'media_candidate_path_verified':proof,'ue_tunnel_capture_verified':packet_proof,'switch_windows':windows,
            'audio_required':audio_required,'audio_received_and_unmuted':audio_passed,
            'audio_quality':audio_check,
            'render_location':'windows' if windows_renderer else 'ue-linux','ue_relay_ingress_verified':relay_ingress,
            'audio_samples_received':connected[-1].get('audio_samples_received') if connected else None,
            'audio_concealed_samples':connected[-1].get('audio_concealed_samples') if connected else None,
            'audio_playout_samples':connected[-1].get('audio_playout_samples') if connected else None,
            'scope':'Demo playback/path/coverage gates only; not the existing Ping/UDP acceptance or a zero-freeze guarantee',
            'time_units':'Events mapped to IQ/STK using paired browser/host monotonic clocks; rate, buffer and freeze units remain wall time'}


def main(argv=None):
    global ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    add_runtime_arguments(parser)
    parser.add_argument('--case',choices=['static','firsthandover','full'],default='firsthandover')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--skip-regressions',action='store_true',help='for repeat demo after recorded offline regressions')
    parser.add_argument('--source',type=Path,help='read-only local video with mandatory audio; live-loop as VP8+Opus')
    parser.add_argument('--experiment',type=Path,help='isolated causal-suite configuration; defaults remain unchanged')
    args=parser.parse_args(argv)
    ROOT=args.root.expanduser().resolve()
    if os.geteuid()!=0:raise RuntimeError('Run orchestration via sudo; media/browser themselves drop privileges')
    source=args.source.expanduser().resolve() if args.source else None
    if source is not None and not source.is_file():raise RuntimeError('Source video must be an existing regular file')
    source_before=hashlib.sha256(source.read_bytes()).hexdigest() if source else None
    windows_renderer=bool(source)
    if windows_renderer:ensure_windows_runtime()
    helpers=load_helpers();helpers.validate(ROOT)
    for name in ('nr-softmodem','nr-uesoftmodem'):
        if subprocess.run(['pgrep','-x',name],stdout=subprocess.DEVNULL).returncode==0:
            raise RuntimeError('Another modem experiment is running; refusing to interfere')
    if subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project=ntn-qd-integrated'],text=True).strip():
        raise RuntimeError('Existing isolated core deployment found; refusing to borrow/remove it')
    lock=(ROOT/'.private/full-test-launcher.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    user=pwd.getpwnam('kayoko')
    tag='live-'+args.case+'-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    output=ROOT/'.private'/tag;output.mkdir(mode=0o700)
    visible=TOOLS/'runs'/tag;visible.mkdir(parents=True,mode=0o700);os.chown(visible,user.pw_uid,user.pw_gid)
    env={k:v for k,v in os.environ.items() if not k.startswith('OAI_') and not k.lower().endswith('_proxy')}
    env.update(helpers.PARAMETERS,PLAYWRIGHT_BROWSERS_PATH=str(TOOLS/'browsers'),PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1')
    env.update(radio_environment(ROOT,args.case,args.spatial_mode,args.qd_workers))
    env.update(HOME=user.pw_dir,USER=user.pw_name,LOGNAME=user.pw_name,XDG_RUNTIME_DIR=f'/run/user/{user.pw_uid}')
    if Path('/mnt/wslg/PulseServer').exists():env['PULSE_SERVER']='unix:/mnt/wslg/PulseServer'
    env['PULSE_LATENCY_MSEC']='60'
    experiment_config=None
    if args.experiment:
        experiment_config=json.loads(args.experiment.read_text())
        if not source:raise ValueError('Causal experiments require an audio/video source')
        for key,value in experiment_config['environment'].items():
            if key not in ('OAI_STK_TRACE','OAI_STK_SCHEDULE','OAI_QD_DL_CHANNEL','OAI_QD_UL_CHANNEL'):
                raise ValueError('Unsupported experimental override: '+key)
            path=Path(value).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.exists():raise ValueError('Experimental input outside isolated root')
            env[key]=str(path)
        if not 60<=float(experiment_config['target_iq_s'])<=615:raise ValueError('Invalid experimental duration')
        if 'replay_round' in experiment_config:
            index=experiment_config['replay_round'];total=experiment_config['replay_total']
            if type(index) is not int or type(total) is not int or not 1<=index<=total<=8:raise ValueError('Invalid replay round')
    runner=helpers.Runner(ROOT,output,env)
    selector=['--profile','integrated-handover','--run-id',tag]
    core=[sys.executable,'scripts/core_lab.py'];experiment=[sys.executable,'local_ntn/experiment.py']
    checker=[sys.executable,'scripts/original_platform_check.py'];snapshot=output/'original-before.json'
    run=ROOT/'.runtime/runs/integrated-handover'/tag
    result={'tag':tag,'case':args.case,'passed':False,'stages':runner.records,'cleanup':{},'ui_directory':str(visible)}
    result.update(spatial_mode_requested=args.spatial_mode,qd_workers_requested=int(env['OAI_QD_WORKERS']),runtime_root=str(ROOT))
    if experiment_config:result['experiment']=experiment_config
    result['source_media']={'path':str(source),'sha256':source_before,'output_video_codec':'VP8','output_audio_codec':'Opus','live_wall_paced':True,'loop':True} if source else {'synthetic':True,'audio':False}
    processes={};core_started=False;before=digest_runtime(ROOT)
    def start(name,argv):
        stream=(output/(name+'.private.log')).open('xb')
        p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        stream.close();processes[name]=(p,helpers.process_start(p.pid))
        return p
    def stop(name):
        if name not in processes:return
        p,identity=processes[name]
        if p.poll() is not None:return
        if name=='browser' and windows_renderer:
            try:state=json.loads((visible/'state.json').read_text())
            except (FileNotFoundError,ValueError):state={}
            atomic_json(visible/'state.json',dict(state,stop_requested=True))
            try:p.wait(timeout=20);return
            except subprocess.TimeoutExpired:raise RuntimeError('Windows player has not confirmed graceful exit; lease timeout will close it')
        for sig,timeout in [(signal.SIGINT,15),(signal.SIGTERM,5),(signal.SIGKILL,5)]:
            if p.poll() is not None:return
            if identity is None or helpers.process_start(p.pid)!=identity:raise RuntimeError('Process identity changed: '+name)
            # Let the browser worker close Chromium itself before escalating its session.
            if name=='browser' and sig==signal.SIGINT:os.kill(p.pid,sig)
            else:os.killpg(p.pid,sig)
            try:p.wait(timeout=timeout);return
            except subprocess.TimeoutExpired:pass
        raise RuntimeError('Cannot confirm owned process exit: '+name)
    drop=['setpriv','--reuid',str(user.pw_uid),'--regid',str(user.pw_gid),'--init-groups']
    def original_compare():runner.stage('original-after',checker+['compare','--snapshot',str(snapshot)],timeout=120)
    helpers.say('LIVE DEMO '+tag);helpers.say('PRIVATE EVIDENCE '+str(output));helpers.say('PLAYER SHOTS '+str(visible))
    def interrupt(*_):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupt)
    try:
        runner.stage('original-before',checker+['snapshot','--snapshot',str(snapshot)],timeout=120)
        if not args.skip_regressions:
            runner.stage('trace-iq-regressions',['bash','local_ntn/run_regressions.sh'])
            runner.stage('scripts-regressions',['bash','scripts/test.sh'])
        runner.stage('core-up',core+['up']+selector,timeout=180);core_started=True
        for _ in range(120):
            ids=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project=ntn-qd-integrated'],text=True).split()
            inventory=json.loads(subprocess.check_output(['docker','inspect',*ids])) if ids else []
            if len(inventory)==9 and all(i['State']['Running'] and i['State'].get('Health',{}).get('Status')=='healthy' for i in inventory):break
            time.sleep(1)
        else:raise RuntimeError('Core readiness timeout')
        ext=next(i for i in inventory if i['Name']=='/ntn-qd-integrated-oai-ext-dn')
        ext_pid=ext['State']['Pid'];ext_identity=helpers.process_start(ext_pid)
        media_ns=['nsenter','-t',str(ext_pid),'-n']+drop
        config=visible/'mediamtx.yml'
        config.write_text('logLevel: info\nrtsp: yes\nrtspAddress: 127.0.0.1:8554\nrtspTransports: [tcp]\nrtmp: no\nhls: no\nsrt: no\nmoq: no\nwebrtc: yes\nwebrtcAddress: 192.168.71.135:8889\nwebrtcLocalUDPAddress: 192.168.71.135:8189\nwebrtcLocalTCPAddress: ""\nwebrtcIPsFromInterfaces: no\nwebrtcAdditionalHosts: [192.168.71.135]\nwebrtcICEServers2: []\npaths:\n  live:\n    source: publisher\n')
        config.chmod(0o644)
        if helpers.process_start(ext_pid)!=ext_identity:raise RuntimeError('ext-DN process identity changed')
        start('media-server',media_ns+[str(TOOLS/'mediamtx/mediamtx'),str(config)])
        time.sleep(2)
        py=str(TOOLS/'user-venv/bin/python')
        encoders=list(TOOLS.glob('user-venv/lib/python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-*'))
        if len(encoders)!=1:raise RuntimeError('Expected exactly one isolated FFmpeg binary')
        ffmpeg=str(encoders[0])
        publisher_command=publisher_arguments(ffmpeg,source)
        if experiment_config:publisher_command[1:1]=['-progress',str(visible/'publisher-progress.txt'),'-stats_period','1']
        start('publisher',media_ns+publisher_command)
        time.sleep(2)
        for name in ('media-server','publisher'):
            if processes[name][0].poll() is not None:raise RuntimeError(name+' exited; see private log')
        runner.stage('modems-start',experiment+['start']+selector+['--rate','0' if args.case=='static' else '1','--label','live-demo'],timeout=90)
        for _ in range(120):
            p=subprocess.run(['ip','-n','ntn-qd-ue','-j','-4','addr','show','dev','oaitun_ue1'],capture_output=True,text=True)
            addresses=[a['local'] for i in (json.loads(p.stdout) if p.returncode==0 else []) for a in i.get('addr_info',[]) if a.get('family')=='inet']
            if addresses:break
            time.sleep(.5)
        else:raise RuntimeError('PDU readiness timeout')
        runner.stage('video-route',['ip','-n','ntn-qd-ue','route','replace','192.168.71.135/32','dev','oaitun_ue1','src',addresses[0]])
        route=json.loads(subprocess.check_output(['ip','-n','ntn-qd-ue','-j','route','get','192.168.71.135']))[0]
        result['ue_route']=route
        if route.get('dev')!='oaitun_ue1' or route.get('prefsrc')!=addresses[0]:raise RuntimeError('Video route bypasses UE PDU')
        ue_ns=['ip','netns','exec','ntn-qd-ue']
        # Capture headers only, no payload or unrelated UE traffic.
        start('ue-media-packets',ue_ns+['tcpdump','-i','oaitun_ue1','-nn','-l','-s','96']+([] if experiment_config else ['-c','40'])+['udp and host 192.168.71.135 and port 8189'])
        state_base={'audio_required':bool(source),'render_location':'windows' if windows_renderer else 'ue-linux',
                    'spatial_mode_requested':args.spatial_mode,'qd_workers_requested':int(env['OAI_QD_WORKERS'])}
        if experiment_config:state_base['experiment_condition']=experiment_config['condition']
        if experiment_config and 'replay_round' in experiment_config:
            state_base.update(replay_round=experiment_config['replay_round'],replay_total=experiment_config['replay_total'],
                              replay_note='每轮重新接入，重复同一段真实切换；不是一条连续轨迹')
        if windows_renderer:
            relay_config=visible/'ue-relay.yml'
            relay_config.write_text('logLevel: info\nrtsp: no\nrtmp: no\nhls: no\nsrt: no\nmoq: no\napi: yes\napiAddress: 10.202.0.2:9997\nauthInternalUsers:\n- user: any\n  pass: ""\n  ips: [127.0.0.1, 10.202.0.1]\n  permissions:\n  - action: read\n    path: live\n  - action: api\nwebrtc: yes\nwebrtcAddress: 10.202.0.2:8890\nwebrtcLocalUDPAddress: ""\nwebrtcLocalTCPAddress: 10.202.0.2:8190\nwebrtcIPsFromInterfaces: no\nwebrtcAdditionalHosts: [127.0.0.1]\nwebrtcICEServers2: []\npaths:\n  live:\n    source: whep://192.168.71.135:8889/live/whep\n')
            relay_config.chmod(0o644)
            start('ue-relay',ue_ns+drop+[str(TOOLS/'mediamtx/mediamtx'),str(relay_config)])
            start('display-bridge',[sys.executable,str(HERE/'bridge.py')])
            state_base['media_url']='http://127.0.0.1:8889/live/whep'
        start('telemetry-server',([] if windows_renderer else ue_ns)+[sys.executable,str(HERE/'worker.py'),'serve','--run',str(visible),'--output',str(output)])
        atomic_json(visible/'state.json',state_base)
        time.sleep(.5)
        if windows_renderer:
            script=subprocess.check_output(['wslpath','-w',str(HERE/'windows_player.cjs')],text=True).strip()
            start('browser',[WINDOWS_NODE,script,tag])
        else:start('browser',ue_ns+drop+[py,str(HERE/'worker.py'),'browser','--run',str(visible)]+(['--headless'] if args.headless else []))
        live=helpers.Live(run)
        # The helper expects acceptance log names; point only its readers at this run's real logs.
        live.modems={s:helpers.Lines(run/(s+'-live-demo.log')) for s in ('gnb','ue')}
        radio=RadioTelemetry(helpers,run)
        events=helpers.Lines(output/'browser-events.jsonl')
        first_video=None;last_stats=None;deadline=time.monotonic()+1800;next_note=0;next_ingress=0
        ingress_previous=None;ingress_kbps=None;ingress_observed_ns=None
        replay_switched=False
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        target={'static':60,'firsthandover':65,'full':615}[args.case]
        if experiment_config:target=float(experiment_config['target_iq_s'])
        while time.monotonic()<deadline:
            live.poll()
            radio.poll()
            state=dict(state_base)
            if 'ue' in live.clock:
                iq,stk=live.clock['ue'];state.update(iq_s=iq,stk_s=stk)
            if 'ue' in live.phases:state.update(satellite=live.phases['ue'][0],phase=live.phases['ue'][1])
            if state_base.get('replay_round'):
                replay_switched=replay_switched or state.get('phase')=='complete'
                state['replay_completed']=state_base['replay_round']-1+int(replay_switched)
            state['sampled_host_monotonic_ns']=time.monotonic_ns()
            state['channels']=radio.snapshot(state.get('iq_s'))
            state['spatial']=radio.spatial_snapshot()
            state['input_dl_cn_db']=state['channels'].get('dl',{}).get('cn_db')
            state['ue_ingress_kbps']=ingress_kbps
            state['ue_ingress_observed_monotonic_ns']=ingress_observed_ns
            state['publisher_alive']=processes['publisher'][0].poll() is None
            if experiment_config:
                state.update(input_dl_cn_db=live.physical.get('ue',(None,None,None))[2],ue_ingress_kbps=ingress_kbps)
            atomic_json(visible/'state.json',state)
            if windows_renderer and time.monotonic()>=next_ingress:
                ingress_kbps=None
                try:
                    with opener.open('http://10.202.0.2:9997/v3/paths/list',timeout=1) as response:ingress=json.load(response)
                    ingress['host_monotonic_ns']=time.monotonic_ns()
                    ingress['iq_s']=live.clock.get('ue',(None,None))[0]
                    ingress['stk_s']=live.clock.get('ue',(None,None))[1]
                    paths=[p for p in ingress.get('items',[]) if p.get('name')=='live']
                    if paths:
                        current=(ingress['host_monotonic_ns'],paths[0].get('bytesReceived',0),paths[0].get('readyTime'))
                        if ingress_previous and current[2]==ingress_previous[2] and current[1]>=ingress_previous[1] and current[0]>ingress_previous[0]:
                            ingress_kbps=(current[1]-ingress_previous[1])*8e6/(current[0]-ingress_previous[0])
                        else:ingress_kbps=None
                        ingress_previous=current
                        ingress_observed_ns=current[0]
                    else:
                        ingress_previous=None;ingress_observed_ns=None
                    with (output/'ue-relay-ingress.jsonl').open('a') as stream:stream.write(json.dumps(ingress)+'\n')
                except (OSError,ValueError):pass
                next_ingress=time.monotonic()+1
                if experiment_config:
                    sample={'host_monotonic_ns':time.monotonic_ns(),'clock':live.clock,'physical':live.physical,
                            'phases':live.phases,'processes_alive':{name:p.poll() is None for name,(p,_) in processes.items() if name!='ue-media-packets'}}
                    manifest=json.loads((run/'run.json').read_text())
                    owned=json.loads(Path(manifest['state_file']).read_text())['processes']
                    for name,record in owned.items():
                        sample['processes_alive']['modem-'+name]=str(helpers.process_start(record['pid']))==str(record['start'])
                    link=subprocess.run(['ip','-n','ntn-qd-ue','-j','-s','link','show','dev','oaitun_ue1'],capture_output=True,text=True)
                    try:sample['ue_tunnel']=json.loads(link.stdout)[0].get('stats64',{})
                    except (ValueError,IndexError):sample['ue_tunnel']=None
                    sample['host_loadavg']=Path('/proc/loadavg').read_text().split()[:3]
                    progress_file=visible/'publisher-progress.txt'
                    if progress_file.exists():
                        fields=dict(line.split('=',1) for line in progress_file.read_text().splitlines() if '=' in line)
                        sample['publisher_progress']={k:fields.get(k) for k in ('frame','out_time_us','speed')}
                    with (output/'causal-samples.jsonl').open('a') as stream:stream.write(json.dumps(sample)+'\n')
                    if not all(sample['processes_alive'].values()):raise RuntimeError('Owned worker/modem exited during causal experiment')
            for line in events.read():
                event=json.loads(line)
                if event.get('event')=='fatal':raise RuntimeError('Player reported fatal error; see private telemetry')
                if event.get('event')=='stats':
                    last_stats=event
                    if event.get('frames_decoded',0)>0 and first_video is None:first_video=time.monotonic();helpers.say('VIDEO first decoded frames through UE')
            for name in (('browser','media-server','publisher','telemetry-server','ue-relay','display-bridge') if windows_renderer else ('browser','media-server','publisher','telemetry-server')):
                if processes[name][0].poll() is not None:raise RuntimeError(name+' exited unexpectedly')
            if time.monotonic()>=next_note:
                if last_stats:helpers.say('AV '+json.dumps({k:last_stats.get(k) for k in ('bitrate_kbps','decoded_fps','buffer_ms','frame_gap_ms','frames_decoded','freeze_count','audio_bitrate_kbps','audio_decode_rate_hz','audio_samples_received','audio_playout_samples','audio_muted')},ensure_ascii=True))
                if experiment_config:helpers.say('UE_MEDIA '+json.dumps({'condition':experiment_config['condition'],'iq_s':state.get('iq_s'),'input_dl_cn_db':state.get('input_dl_cn_db'),'ingress_kbps':ingress_kbps}))
                next_note=time.monotonic()+5
            progress=min((v[0] for v in live.clock.values()),default=0)
            if first_video is None and progress>30:raise RuntimeError('No decoded video before IQ30; fail without masking startup')
            if progress>=target:break
            time.sleep(.2)
        else:raise RuntimeError('Demo wall timeout')
        stop('browser');time.sleep(.3);stop('telemetry-server');stop('ue-media-packets')
        result.update(analyze(output,run,ROOT,args.case,bool(source),windows_renderer))
        evidence=audit_live_run(ROOT,run,args.spatial_mode,int(env['OAI_QD_WORKERS']))
        atomic_json(output/'physical-spatial-audit.json',evidence)
        result.update(numeric_audit_ok=evidence['numeric_audit_ok'],spatial_audit=evidence['spatial'])
        result['passed']=result['demo_passed']
    except (Exception,KeyboardInterrupt) as error:
        result['error']=str(error) or type(error).__name__;helpers.say('DEMO FAILED: '+result['error'])
    finally:
        for name in ('browser','telemetry-server','display-bridge','ue-relay','ue-media-packets','publisher','media-server'):
            try:stop(name)
            except Exception as error:result['cleanup'][name]=str(error);result['passed']=False
        if experiment_config and 'video_stats_samples' not in result and (output/'browser-events.jsonl').exists():
            try:result.update(analyze(output,run,ROOT,args.case,bool(source),windows_renderer))
            except Exception as error:result['partial_analysis_error']=str(error)
        if (run/'run.json').exists():
            try:runner.stage('modems-stop',experiment+['stop']+selector,timeout=60)
            except Exception as error:result['cleanup']['modems']=str(error);result['passed']=False
        if core_started:
            try:runner.stage('core-down',core+['down']+selector,timeout=120)
            except Exception as error:result['cleanup']['core']=str(error);result['passed']=False
        result['runtime_sources_and_binaries_unchanged']=before==digest_runtime(ROOT)
        if not result['runtime_sources_and_binaries_unchanged']:result['passed']=False
        if source:
            result['source_file_unchanged']=source_before==hashlib.sha256(source.read_bytes()).hexdigest()
            if not result['source_file_unchanged']:result['passed']=False
        if snapshot.exists():
            try:original_compare();result['original_protection_passed']=True
            except Exception as error:result['original_protection_passed']=False;result['passed']=False
        (output/'report.json').write_text(json.dumps(result,indent=2))
        helpers.say(('DEMO PASS' if result['passed'] else 'DEMO FAIL')+' '+str(output/'report.json'))
        lock.close()
    return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
