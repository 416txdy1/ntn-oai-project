"""Repeat the verified first-handover window, with an explicit new session each round."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid

from demo import HERE, ROOT, load_helpers
from live_config import add_runtime_arguments, child_arguments


def confirmed_handover(root, outcome, helpers):
    path=root/'.runtime/runs/integrated-handover'/outcome['tag']/'ue-live-demo.log'
    phases=[];completions=[]
    for line in path.read_text(errors='replace').splitlines():
        match=helpers.SCHEDULE.search(line)
        if not match:continue
        d,iq,stk,satellite,elevation,visible,switched,phase,previous,following,samples=match.groups()
        if phase in ('prepare','blend','complete') and phase not in phases:phases.append(phase)
        if phase=='complete' and switched=='1':
            event={'iq_s':float(iq),'stk_s':float(stk),'previous':previous,'satellite':satellite,'following':following}
            if not completions or event['previous']!=completions[-1]['previous'] or event['satellite']!=completions[-1]['satellite']:
                completions.append(event)
    expected=['prepare','blend','complete']
    return {'phases':phases,'completions':completions,
            'verified':phases==expected and len(completions)==1 and completions[0]['previous']!=completions[0]['satellite']}


def main(argv=None):
    global ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    add_runtime_arguments(parser)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--rounds',type=int,choices=range(1,9),default=4)
    parser.add_argument('--skip-regressions',action='store_true')
    args=parser.parse_args(argv)
    args.root=args.root.expanduser().resolve();ROOT=args.root
    if os.geteuid()!=0:raise RuntimeError('Run the Windows launcher or sudo')
    if not args.source.is_file():raise ValueError('Source video does not exist')
    helpers=load_helpers();helpers.validate(ROOT)
    lock=(ROOT/'.private/causal-suite.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # Do not start regressions or borrow an existing core/modem experiment.
    if subprocess.run(['pgrep','-x','nr-softmodem|nr-uesoftmodem'],stdout=subprocess.DEVNULL).returncode==0:
        raise RuntimeError('Another modem experiment is running; stop it normally first')
    if subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project=ntn-qd-integrated'],text=True).strip():
        raise RuntimeError('Isolated core exists; refusing to take over existing experiment')
    tag='handover-replay-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    private=ROOT/'.private'/tag;private.mkdir(mode=0o700)
    public=HERE/'replay-results'/tag;public.mkdir(parents=True)
    report={'series':tag,'requested_rounds':args.rounds,'completed_rounds':0,'rounds':[],
            'spatial_mode':args.spatial_mode,'qd_workers':args.qd_workers,
            'status':'RUNNING','mode':'independent_first_handover_replays',
            'scope':'Each round has a fresh PDU/media session and IQ restarts. Not continuous multi-satellite handover or a causal control suite.'}
    runner=helpers.Runner(ROOT,private,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    child=None
    def save():
        body=json.dumps(report,ensure_ascii=False,indent=2)
        (private/'report.json').write_text(body);(public/'report.json').write_text(body,encoding='utf-8')
        lines=['# 多轮卫星切换重放','','状态：'+report['status'],f"已完整通过 {report['completed_rounds']}/{args.rounds} 轮。",'',
               '每轮重新接入，使用同一已验证的S06→S05片段；轮间重连不是卫星切换。',
               '默认每轮65 IQ秒，准备约40秒、混合约41–44秒、完成约45秒，实际墙钟依电脑运行速度。','',
               '|轮次|通过|阶段完整|实际切换完成IQ|报告|','|---|---|---|---|---|']
        for entry in report['rounds']:
            event=entry.get('handover',{});complete=', '.join(str(c['iq_s']) for c in event.get('completions',[]))
            lines.append(f"|{entry['round']}|{entry['passed']}|{event.get('verified',False)}|{complete}|{entry.get('directory','')}|")
        lines+=['','这是演示重放，未替代正常双切换或因果对照验收。不保证零卡顿。']
        (public/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def interrupted(*_):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupted)
    helpers.say('HANDOVER REPLAY '+tag);helpers.say('SUMMARY '+str(public/'RESULTS.md'))
    helpers.say('Keep player and console OPEN. Closing the player stops the series; do not close it to advance rounds.')
    try:
        save()
        if not args.skip_regressions:
            runner.stage('trace-iq-regressions',['bash','local_ntn/run_regressions.sh'])
            runner.stage('scripts-regressions',['bash','scripts/test.sh'])
        for index in range(1,args.rounds+1):
            helpers.say(f'ROUND {index}/{args.rounds}: real S06 -> S05, fresh session, target=65 IQ seconds')
            config={'condition':'normal','replay_round':index,'replay_total':args.rounds,'target_iq_s':65,'environment':{}}
            config_path=private/f'round-{index}.json';config_path.write_text(json.dumps(config))
            command=[sys.executable,'-B','-u',str(HERE/'demo.py'),'--case','firsthandover','--source',str(args.source),
                     '--skip-regressions','--experiment',str(config_path)]+child_arguments(args)
            child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            directory=None
            with (private/f'round-{index}.console.log').open('w') as stream:
                for line in child.stdout:
                    print(line,end='',flush=True);stream.write(line);stream.flush()
                    if 'PRIVATE EVIDENCE ' in line:directory=Path(line.split('PRIVATE EVIDENCE ',1)[1].strip())
            code=child.wait();child=None
            entry={'round':index,'exit_code':code,'directory':str(directory) if directory else None,'passed':False}
            if directory and directory.is_relative_to(ROOT/'.private') and (directory/'report.json').exists():
                outcome=json.loads((directory/'report.json').read_text());entry['report']=outcome
                entry['handover']=confirmed_handover(ROOT,outcome,helpers)
                entry['passed']=code==0 and outcome.get('passed') is True and entry['handover']['verified']
            report['rounds'].append(entry)
            if entry['passed']:report['completed_rounds']+=1
            save()
            if not entry['passed']:raise RuntimeError('Round failed/incomplete; series stopped without counting a false switch. See round report; keep player open and unmuted.')
            helpers.say(f'CONFIRMED {report["completed_rounds"]}/{args.rounds}: prepare/blend/complete + audio/video + protection passed')
        report['status']='PASS';save();return 0
    except (Exception,KeyboardInterrupt) as error:
        report.update(status='INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAIL',error=str(error) or type(error).__name__)
        if child and child.poll() is None:
            child.send_signal(signal.SIGINT)
            try:child.wait(timeout=180)
            except subprocess.TimeoutExpired:report['cleanup_attention']='Child cleanup not confirmed; no broad kill attempted'
        save();helpers.say('REPLAY '+report['status']+' '+report['error']);return 1
    finally:
        helpers.say('REPLAY SUMMARY '+str(public/'RESULTS.md'));lock.close()


if __name__=='__main__':sys.exit(main())
