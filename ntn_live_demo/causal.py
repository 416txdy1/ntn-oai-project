"""Paired, run-owned IQ-channel intervention and long audiovisual observations.

Never changes OAI sources/binaries or existing traces. A result may be inconclusive.
"""
import argparse
import csv
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import time
import uuid

from demo import ROOT, HERE, load_helpers
from live_config import add_runtime_arguments, child_arguments, bundle_root, radio_environment


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def derive_inputs(root, suite, smoke, onset, duration, drop, spatial_mode='siso'):
    """Reuse identical QD taps; explicitly document the modified absolute C/N input."""
    original = bundle_root(root,spatial_mode)
    trace = root/'local_ntn/stk_trace_seamless.csv'
    schedule = root/'local_ntn/satellite_schedule_seamless.csv'
    destination = original/suite.name
    destination.mkdir(mode=0o700)
    source_hash = sha(trace)
    lines = trace.read_text().splitlines()
    rows = list(csv.reader(lines[2:]))
    epoch = float(rows[0][0])
    changes = []
    for row in rows:
        iq = float(row[0])-epoch
        # One-second linear ramps, identical positions/velocities/power/taps/schedule.
        weight = max(0., min(1., iq-onset, onset+duration-iq))
        if weight:
            previous = float(row[18])
            row[18] = format(previous-drop*weight, '.17g')
            changes.append({'iq_s':iq, 'before_cn_db':previous, 'after_cn_db':float(row[18])})
    if not changes:raise ValueError('Intervention interval outside trace')
    derived_trace = suite/'intervention-trace.csv'
    with derived_trace.open('w', newline='') as stream:
        stream.write(lines[0]+'\n'+lines[1]+'\n')
        csv.writer(stream,lineterminator='\n').writerows(rows)
    derivation = {'kind':'controlled_absolute_downlink_cn_intervention',
                  'original_trace':str(trace), 'original_trace_sha256':source_hash,
                  'derived_trace_sha256':sha(derived_trace),
                  'onset_iq_s':onset, 'duration_iq_s':duration, 'drop_db':drop,
                  'changed_column':'dl_cn_db', 'changes':changes,
                  'qd_tap_data_unchanged':True,
                  'note':'Not a new MATLAB export. Original normalized relative taps reused; only absolute STK DL C/N changed.'}
    provenance = json.loads((original/'provenance.json').read_text())
    provenance['experimental_derivation'] = derivation
    provenance['inputs']['trace'].update(path=str(derived_trace),sha256=sha(derived_trace))
    for direction in ('downlink','uplink'):
        shutil.copytree(original/direction,destination/direction)
        manifest_path = destination/direction/'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['provenance']['stk_trace_sha256'] = sha(derived_trace)
        write_json(manifest_path,manifest)
        provenance['bundles'][direction]['manifest_sha256'] = sha(manifest_path)
        antenna_path=destination/direction/'antenna.json'
        if antenna_path.exists():
            antenna=json.loads(antenna_path.read_text())
            antenna.update(manifest_sha256=sha(manifest_path),stk_trace_sha256=sha(derived_trace))
            write_json(antenna_path,antenna)
            provenance['bundles'][direction]['antenna_sha256']=sha(antenna_path)
    write_json(destination/'provenance.json',provenance)
    write_json(destination/'experimental-derivation.json',derivation)
    write_json(suite/'input-derivation.json',derivation)
    return {'OAI_STK_TRACE':str(derived_trace), 'OAI_STK_SCHEDULE':str(schedule),
            'OAI_QD_DL_CHANNEL':str(destination/'downlink'), 'OAI_QD_UL_CHANNEL':str(destination/'uplink')}, derivation


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def interval(rows, left, right):
    return [r for r in rows if r.get('iq_s') is not None and left<=r['iq_s']<=right]


def rate(rows, field, clock):
    pairs = [(a,b) for a,b in zip(rows,rows[1:]) if field in a and field in b and b[field]>=a[field] and b[clock]>a[clock]]
    seconds = sum((b[clock]-a[clock]) for a,b in pairs)
    return sum(b[field]-a[field] for a,b in pairs)/seconds if seconds>0 else None


def window_metrics(directory, left, right):
    ingress = []
    for event in read_rows(directory/'ue-relay-ingress.jsonl'):
        if event.get('iq_s') is None:continue
        paths=[p for p in event.get('items',[]) if p.get('name')=='live']
        if paths:
            path=paths[0]
            ingress.append({'iq_s':event['iq_s'],'wall_s':event['host_monotonic_ns']/1e9,
                            'bytes':path.get('bytesReceived',0),'ready':bool(path.get('ready')),
                            'ready_time':path.get('readyTime')})
    ingress=interval(ingress,left,right)
    video=interval(json.loads((directory/'video-timeline.json').read_text()),left,right) if (directory/'video-timeline.json').exists() else []
    samples=read_rows(directory/'causal-samples.jsonl')
    samples=[dict(s,iq_s=s.get('clock',{}).get('ue',[None,None])[0]) for s in samples]
    samples=interval(samples,left,right)
    cn=[s['physical']['ue'][2] for s in samples if 'ue' in s.get('physical',{})]
    for s in video:s['wall_s']=s['browser_ms']/1000
    resets=sum(b['bytes']<a['bytes'] or b['ready_time']!=a['ready_time'] for a,b in zip(ingress,ingress[1:]))
    freeze=(max(r.get('total_freeze_duration_s') or 0 for r in video)-min(r.get('total_freeze_duration_s') or 0 for r in video)) if video else None
    healthy=bool(samples) and all(all(s['processes_alive'].values()) for s in samples)
    publisher=[s for s in samples if s.get('publisher_progress',{}).get('out_time_us') not in (None,'N/A')]
    publisher_ratio=None
    if len(publisher)>1:
        seconds=(publisher[-1]['host_monotonic_ns']-publisher[0]['host_monotonic_ns'])/1e9
        publisher_ratio=(float(publisher[-1]['publisher_progress']['out_time_us'])-float(publisher[0]['publisher_progress']['out_time_us']))/1e6/seconds if seconds>0 else None
    return {'iq_interval':[left,right],'ingress_samples':len(ingress),'player_samples':len(video),
            'ingress_bytes_per_wall_s':rate(ingress,'bytes','wall_s'),
            'decoded_frames_per_wall_s':rate(video,'frames_decoded','wall_s'),
            'max_frame_gap_ms':max((r.get('frame_gap_ms') or 0 for r in video),default=None),
            'freeze_wall_s':freeze,'median_input_dl_cn_db':statistics.median(cn) if cn else None,
            'ingress_resets':resets,'workers_alive':healthy,
            'publisher_realtime_progress_ratio':publisher_ratio,
            'audio_concealed_samples_delta':(video[-1].get('audio_concealed_samples',0)-video[0].get('audio_concealed_samples',0)) if len(video)>1 else None,
            'scope':'Input C/N is not measured SINR. Ingress is before Windows forwarding; playback is after forwarding.'}


def assess_pair(normal, intervention, pre_normal, pre_intervention, coverage, protection):
    enough=all(w['ingress_samples']>=5 and w['player_samples']>=5 for w in (normal,intervention,pre_normal,pre_intervention))
    producer_ok=all(w.get('publisher_realtime_progress_ratio') is not None and .8<=w['publisher_realtime_progress_ratio']<=1.2 for w in (normal,intervention,pre_normal,pre_intervention))
    valid=enough and coverage and protection and producer_ok and all(w['workers_alive'] for w in (normal,intervention,pre_normal,pre_intervention))
    cn_effect=(normal['median_input_dl_cn_db'] is not None and intervention['median_input_dl_cn_db'] is not None
               and normal['median_input_dl_cn_db']-intervention['median_input_dl_cn_db']>=8)
    def reduced(key):
        n,d,pn,pd=(w.get(key) for w in (normal,intervention,pre_normal,pre_intervention))
        return all(v is not None for v in (n,d,pn,pd)) and min(n,pn,pd)>0 and .5<=pn/pd<=2 and d<.5*n and d<.5*pd
    ingress_effect=reduced('ingress_bytes_per_wall_s')
    playback_effect=reduced('decoded_frames_per_wall_s') or (
        normal.get('freeze_wall_s') is not None and intervention.get('freeze_wall_s') is not None
        and intervention['freeze_wall_s']>normal['freeze_wall_s']+2)
    stable_ingress=all(w['ingress_resets']==0 for w in (normal,intervention,pre_normal,pre_intervention))
    supported=valid and stable_ingress and cn_effect and ingress_effect and playback_effect
    return {'status':'SUPPORTED' if supported else 'INCONCLUSIVE' if valid else 'INVALID',
            'adequate_data_and_coverage':valid,'physical_cn_difference_observed':cn_effect,
            'publisher_kept_realtime':producer_ok,
            'ue_media_ingress_reduction':ingress_effect,'playback_deterioration':playback_effect,
            'no_ingress_counter_reset':stable_ingress,
            'meaning':'Evidence of this injected IQ-channel effect; does not attribute every normal-handover freeze to switching.'}


def structured_radio(directory, runtime, helpers):
    """Export only matched numeric/schedule fields, never arbitrary UE log lines."""
    destination=directory/'radio-numeric.jsonl'
    with destination.open('w') as output:
        for side in ('gnb','ue'):
            iq=None
            for line in (runtime/(side+'-live-demo.log')).read_text(errors='replace').splitlines():
                clock=helpers.CLOCK.search(line)
                if clock:iq=float(clock[2])
                physical=helpers.PHYSICAL.search(line)
                schedule=helpers.SCHEDULE.search(line)
                if physical:
                    output.write(json.dumps({'side':side,'kind':'physical','fields':physical.groups()})+'\n')
                if schedule:
                    output.write(json.dumps({'side':side,'kind':'schedule','fields':schedule.groups()})+'\n')
                if 'received all 0 pdu' in line:
                    output.write(json.dumps({'side':side,'iq_s':iq,'kind':'all_zero_pdu_rejection'})+'\n')


def export_timeline(directory, destination):
    """Join numeric observations on IQ; preserve the pairing distance explicitly."""
    video=json.loads((directory/'video-timeline.json').read_text()) if (directory/'video-timeline.json').exists() else []
    ingress=read_rows(directory/'ue-relay-ingress.jsonl')
    keys=['host_monotonic_ns','iq_s','stk_s','input_dl_cn_db','ue_tunnel_rx_bytes',
          'relay_received_bytes','publisher_out_time_us','player_pair_distance_iq_s',
          'decoded_fps','frame_gap_ms','freeze_count','total_freeze_duration_s',
          'audio_samples_received','audio_concealed_samples','audio_muted']
    with destination.open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,keys);writer.writeheader()
        for sample in read_rows(directory/'causal-samples.jsonl'):
            iq,stk=sample.get('clock',{}).get('ue',(None,None))
            if iq is None:continue
            row={'host_monotonic_ns':sample['host_monotonic_ns'],'iq_s':iq,'stk_s':stk,
                 'input_dl_cn_db':sample.get('physical',{}).get('ue',[None,None,None])[2],
                 'ue_tunnel_rx_bytes':(sample.get('ue_tunnel') or {}).get('rx',{}).get('bytes'),
                 'publisher_out_time_us':sample.get('publisher_progress',{}).get('out_time_us')}
            matched=min(video,key=lambda v:abs(v['iq_s']-iq)) if video else None
            if matched:
                distance=abs(matched['iq_s']-iq);row['player_pair_distance_iq_s']=distance
                if distance<=1:
                    row.update({k:matched.get(k) for k in keys[8:]})
            incoming=min(ingress,key=lambda v:abs(v['host_monotonic_ns']-sample['host_monotonic_ns'])) if ingress else None
            if incoming and abs(incoming['host_monotonic_ns']-sample['host_monotonic_ns'])<=2e9:
                paths=[p for p in incoming.get('items',[]) if p.get('name')=='live']
                if paths:row['relay_received_bytes']=paths[0].get('bytesReceived')
            writer.writerow(row)


def main(argv=None):
    global ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    add_runtime_arguments(parser)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--repeats',type=int,choices=range(1,5),default=2)
    parser.add_argument('--smoke',action='store_true',help='100 IQ seconds, first switch only; never long-run acceptance')
    parser.add_argument('--prepare-only',action='store_true',help='derive inputs, run regressions/preflight; no modems')
    args=parser.parse_args(argv)
    args.root=args.root.expanduser().resolve();ROOT=args.root
    if os.geteuid()!=0:raise RuntimeError('Use launcher/sudo for isolated orchestration')
    if not args.source.is_file():raise ValueError('Source does not exist')
    helpers=load_helpers();helpers.validate(ROOT)
    lock=(ROOT/'.private/causal-suite.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    tag='causal-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    suite=ROOT/'.private'/tag;suite.mkdir(mode=0o700)
    # Windows-accessible, sanitized summary. No UE logs or credentials copied here.
    public=HERE/'causal-results'/tag;public.mkdir(parents=True)
    target,onset,duration=(100.,70.,12.) if args.smoke else (615.,300.,12.)
    environment,derivation=derive_inputs(ROOT,suite,args.smoke,onset,duration,16.,args.spatial_mode)
    report={'suite':tag,'mode':'SMOKE_FIRST_SWITCH_ONLY' if args.smoke else 'LONG_TWO_SWITCHES',
            'spatial_mode':args.spatial_mode,'qd_workers':args.qd_workers,
            'target_iq_s_per_case':target,'repeats':args.repeats,'cases':[],'pairs':[],
            'intervention':derivation,'status':'INCOMPLETE',
            'limitations':['Finite paired observations, not a universal causal guarantee.',
                            'Source is wall-paced; IQ/wall speed and content phase can differ between runs.',
                            'Windows output follows an extra media relay; host load and buffers remain confounders.',
                            'No measured SINR/BLER claim: current logs expose applied input C/N and only limited decoder events.']}
    runner=helpers.Runner(ROOT,suite,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    child=None
    def interrupted(*_):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupted)
    def save():
        write_json(suite/'suite-report.json',report);write_json(public/'suite-report.json',report)
        lines=['# NTN 音视频信道对照实验', '', '状态：'+report['status'], '',
               '模式：'+report['mode'], '',
               '|重复|组别|覆盖|原平台保护|干预窗UE入流 kbit/s|干预窗显示 fps|响应窗冻结秒|',
               '|---|---|---|---|---|---|---|']
        for entry in report['cases']:
            during=entry.get('during',{});response=entry.get('response',{})
            ingress=during.get('ingress_bytes_per_wall_s');fps=during.get('decoded_frames_per_wall_s')
            lines.append('|'+ '|'.join(str(v) for v in (entry['repeat'],entry['condition'],entry.get('coverage'),entry.get('protected'),
                round(ingress*8/1000,2) if ingress is not None else '缺失',round(fps,2) if fps is not None else '缺失',response.get('freeze_wall_s')))+'|')
        lines+=['','## 配对判定','']+[f"- 重复{p['repeat']}：{p['status']}；物理变化={p['physical_cn_difference_observed']}，UE入流下降={p['ue_media_ingress_reduction']}，播放恶化={p['playback_deterioration']}" for p in report['pairs']]
        lines+=['','SUPPORTED 表示本次受控IQ信道干预的配对证据成立；INCONCLUSIVE 表示未证明，不能当作通过。正常切换可能平滑，冻结不能全部归因于切换。',
                '只读源片、相同编码/种子；固定组冻结整个轨迹时钟，正常/干预组只在DL载噪比输入上不同。短模式不代表双切换长测。',
                '数据单位：IQ/STK用于事件位置，速率、缓冲、冻结使用墙钟。Windows指标位于UE中继之后。',
                '详情及证据路径见同目录 suite-report.json；原始UE日志保留私有，不随摘要发布。']
        (public/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def run_case(condition,repeat):
        nonlocal child
        case='static' if condition=='fixed' else 'firsthandover' if args.smoke else 'full'
        controls=radio_environment(ROOT,'full',args.spatial_mode,args.qd_workers)
        control_environment={k:v for k,v in controls.items() if k not in ('OAI_SPATIAL_MODE','OAI_QD_WORKERS')}
        config={'condition':condition,'repeat':repeat,'target_iq_s':target,
                'environment':environment if condition=='intervention' else control_environment,
                'expected_perturbation':{'onset_iq_s':onset,'duration_iq_s':duration,'drop_db':16} if condition=='intervention' else None}
        config_path=suite/f'{repeat}-{condition}.json';write_json(config_path,config)
        command=[sys.executable,'-u',str(HERE/'demo.py'),'--case',case,'--source',str(args.source),
                 '--skip-regressions','--experiment',str(config_path)]+child_arguments(args)
        helpers.say(f'CASE repeat={repeat} condition={condition} target={target} IQ seconds')
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        directory=None
        with (suite/f'{repeat}-{condition}.console.log').open('w') as log:
            for line in child.stdout:
                print(line,end='',flush=True);log.write(line);log.flush()
                marker='PRIVATE EVIDENCE '
                if marker in line:directory=Path(line.split(marker,1)[1].strip())
        code=child.wait();child=None
        entry={'condition':condition,'repeat':repeat,'exit_code':code,'directory':str(directory) if directory else None}
        if directory and (directory/'report.json').exists():
            outcome=json.loads((directory/'report.json').read_text())
            entry['report']=outcome
            runtime=ROOT/'.runtime/runs/integrated-handover'/outcome['tag']
            structured_radio(directory,runtime,helpers)
            entry['before']=window_metrics(directory,onset-25,onset-5)
            # During window sits wholly inside the deep-C/N plateau; response adds buffer drain time.
            entry['during']=window_metrics(directory,onset+3,onset+duration-1)
            entry['response']=window_metrics(directory,onset+3,onset+duration+8)
            entry['recovery']=window_metrics(directory,onset+duration+10,min(target-1,onset+duration+30))
            entry['handover_observations']=[{'completion_iq_s':t,
                'before':window_metrics(directory,t-29,t-9),
                'event':window_metrics(directory,t-5,t+10)} for t in ([44] if args.smoke else [44,599])]
            timelines=json.loads((directory/'video-timeline.json').read_text()) if (directory/'video-timeline.json').exists() else []
            entry['coverage']=bool(timelines) and max(r['iq_s'] for r in timelines)>=target-1 and not outcome.get('error')
            schedules=[row for row in read_rows(directory/'radio-numeric.jsonl') if row['side']=='ue' and row['kind']=='schedule' and row['fields'][7]=='complete']
            completion_by_satellite={}
            for row in schedules:completion_by_satellite.setdefault(row['fields'][3],float(row['fields'][2]))
            entry['switch_completions']=completion_by_satellite
            expected=0 if condition=='fixed' else 1 if args.smoke else 2
            expected_times=[8244,8799][:expected]
            entry['coverage']=entry['coverage'] and all(any(abs(actual-t)<=2 for actual in completion_by_satellite.values()) for t in expected_times)
            if condition=='fixed':entry['coverage']=entry['coverage'] and not completion_by_satellite
            entry['protected']=all(outcome.get(k) for k in ('original_protection_passed','runtime_sources_and_binaries_unchanged','source_file_unchanged')) and not outcome.get('cleanup')
            manifest=json.loads((runtime/'run.json').read_text())
            expected_trace=Path(config['environment']['OAI_STK_TRACE'])
            entry['recorded_input_matches']=manifest['trace_sha256']==sha(expected_trace) and manifest['rate']==(0 if condition=='fixed' else 1)
            entry['coverage']=entry['coverage'] and entry['recorded_input_matches']
            export_timeline(directory,public/f'{repeat}-{condition}-timeline.csv')
        report['cases'].append(entry);save()
        if not entry.get('protected'):raise RuntimeError('Run incomplete or protection/cleanup check failed; stop suite')
        return entry
    try:
        helpers.say('CAUSAL SUITE '+tag);helpers.say('RESULTS '+str(public))
        helpers.say('Long mode: 6 runs by default, 615 IQ seconds each; allow roughly 1-3 hours depending on host. No forced visible stalls.')
        runner.stage('trace-iq-regressions',['bash','local_ntn/run_regressions.sh'])
        runner.stage('scripts-regressions',['bash','scripts/test.sh'])
        # Preflight both directions, with unchanged tap payload hashes and explicit derived provenance.
        preflight_env={k:v for k,v in os.environ.items() if not k.startswith('OAI_')}
        preflight_env.update(helpers.PARAMETERS)
        preflight_env.update(radio_environment(ROOT,'full',args.spatial_mode,args.qd_workers))
        preflight_env.update(environment)
        preflight_runner=helpers.Runner(ROOT,suite,preflight_env)
        preflight_runner.stage('derived-preflight',[sys.executable,'local_ntn/experiment.py','preflight','--profile','integrated-handover','--run-id',tag,'--rate','1'],timeout=120)
        for direction in ('downlink','uplink'):
            preflight_runner.stage('derived-native-'+direction,[sys.executable,'quadriga/tests/run_qd_channel_reader_tests.py',
                '--real-bundle',environment['OAI_QD_DL_CHANNEL' if direction=='downlink' else 'OAI_QD_UL_CHANNEL'],
                '--real-trace',environment['OAI_STK_TRACE']],timeout=180)
        if args.prepare_only:
            report['status']='PREPARED_ONLY_NOT_RUNTIME_TESTED';save();return 0
        for repeat in range(1,args.repeats+1):
            conditions=['fixed','normal','intervention'] if repeat%2 else ['intervention','normal','fixed']
            entries={condition:run_case(condition,repeat) for condition in conditions}
            normal,changed=entries['normal'],entries['intervention']
            pair=assess_pair(normal['during'],changed['during'],normal['before'],changed['before'],
                             all(e['coverage'] for e in entries.values()),all(e['protected'] for e in entries.values()))
            # Playback may lag behind the physical window; check a separately declared response interval.
            response=assess_pair(normal['response'],changed['response'],normal['before'],changed['before'],
                                 all(e['coverage'] for e in entries.values()),all(e['protected'] for e in entries.values()))
            if pair['adequate_data_and_coverage'] and pair['physical_cn_difference_observed'] and pair['ue_media_ingress_reduction'] and response['playback_deterioration'] and response['adequate_data_and_coverage'] and pair['no_ingress_counter_reset']:
                pair['status']='SUPPORTED';pair['playback_deterioration']=True
            pair.update(repeat=repeat,response_interval_assessment=response)
            pair['normal_vs_fixed_handover_observations']=[{'completion_iq_s':n['completion_iq_s'],
                 'fixed':f,'normal':n,
                 'interpretation':'Descriptive comparison; fixed freezes the whole channel, so this alone does not isolate handover causality.'}
                 for n,f in zip(normal['handover_observations'],entries['fixed']['handover_observations'])]
            if not entries['fixed']['report'].get('demo_passed') or not entries['normal']['report'].get('demo_passed'):
                pair['status']='INVALID';pair['reason']='Control playback gate did not pass'
            report['pairs'].append(pair);save();helpers.say('PAIR '+json.dumps(pair))
        report['status']='SUPPORTED' if all(p['status']=='SUPPORTED' for p in report['pairs']) else 'INCONCLUSIVE'
        save();return 0 if report['status']=='SUPPORTED' else 2
    except (Exception,KeyboardInterrupt) as error:
        report['error']=str(error) or type(error).__name__;report['status']='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAILED'
        if child and child.poll() is None:
            child.send_signal(signal.SIGINT)
            try:child.wait(timeout=180)
            except subprocess.TimeoutExpired:report['cleanup_attention']='Child cleanup did not confirm; no broad kill attempted'
        save();helpers.say('SUITE '+report['status']+' '+report['error']);return 1
    finally:
        helpers.say('CAUSAL RESULT '+str(public/'suite-report.json'));lock.close()


if __name__=='__main__':sys.exit(main())
