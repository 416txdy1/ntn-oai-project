"""使用当前 env.sh 配置做有界链路验收；不启动/停止核心网。"""
import argparse,json,os,re,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--rate',type=float,choices=(0,1),default=1);a=p.parse_args()
root=Path(__file__).resolve().parents[1];base=root/'local_ntn'
reports=root/'.runtime/reports';reports.mkdir(parents=True,exist_ok=True)
os.umask(0o077)
label=f'smoke-{int(a.rate)}-{time.time_ns()}'
report={'label':label,'rate':a.rate,'pdu_ready':False}
def command(*args,**kwargs):return subprocess.run(['python3',str(base/'experiment.py'),*args],**kwargs)
try:
 with (reports/(label+'-start.log')).open('w') as f:
  result=command('start','--rate',str(a.rate),'--label',label,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 report['start_exit']=result.returncode
 if result.returncode:raise RuntimeError('start failed; inspect private start log')
 for _ in range(90):
  r=subprocess.run(['ip','-n','oai-stk-ue','-j','-4','addr','show','dev','oaitun_ue1'],capture_output=True,text=True)
  if r.returncode==0 and any(x.get('addr_info') for x in json.loads(r.stdout)):
   report['pdu_ready']=True;break
  time.sleep(1)
 if not report['pdu_ready']:raise RuntimeError('PDU timeout')
 for mode,flags in [('ping',[]),('uplink',['iperf']),('downlink',['iperf','--reverse'])]:
  args=['ping'] if mode=='ping' else flags
  with (reports/(label+'-'+mode+'.log')).open('w') as f:
   result=command(*args,stdout=f,stderr=subprocess.STDOUT,timeout=90)
  text=(reports/(label+'-'+mode+'.log')).read_text()
  report[mode]={'exit':result.returncode,'summary':[s for s in text.splitlines() if any(k in s for k in ['packet loss','rtt ','receiver','time of day goes back'])]}
  if result.returncode:raise RuntimeError(mode+' failed')
  if mode=='ping':
   if '10 received, 0% packet loss' not in text or 'time of day goes back' in text:raise RuntimeError('ping packet/clock check failed')
  elif not any('receiver' in s and '(0%)' in s for s in text.splitlines()):raise RuntimeError(mode+' loss check failed')
 for kind in ('gnb','ue'):
  text=(base/f'{kind}-{label}.log').read_text(errors='replace')
  report[kind]={'qd_loaded':text.count('QDCHANNEL1 loaded'),'trace_loaded':text.count('STKTRACE2 loaded'),'pbch_failures':text.count('Error decoding PBCH')}
  if report[kind]['qd_loaded']!=1 or report[kind]['trace_loaded']!=1:raise RuntimeError('channel not loaded')
 report['passed']=True
except Exception as error:
 report['passed']=False;report['error']=str(error)
finally:
 r=command('stop',capture_output=True,text=True,timeout=25)
 report['stop_exit']=r.returncode
 if r.returncode:report['passed']=False
 (reports/(label+'.json')).write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report.get('passed') else 1)