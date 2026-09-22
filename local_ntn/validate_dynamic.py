"""Bounded end-to-end dynamic test, outputs separate logs; only owns experiment.py PIDs."""
import subprocess,time,argparse,re
from pathlib import Path
b=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--tag',default='v2');args=p.parse_args()
if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.tag):p.error('invalid tag')
def cmd(*args,**kwargs):return subprocess.run(['python3',str(b/'experiment.py'),*args],**kwargs)
cmd('stop',check=True);time.sleep(2)
cmd('start','--rate','1','--label','dynamic-'+args.tag,check=True)
deadline=time.monotonic()+35
while time.monotonic()<deadline:
    p=subprocess.run(['ip','-n','oai-stk-ue','-4','addr','show','dev','oaitun_ue1'],capture_output=True,text=True)
    if p.returncode==0 and 'inet ' in p.stdout:
        print('DYNAMIC_PDU_READY',p.stdout,flush=True);break
    time.sleep(.25)
else:
    cmd('status');raise SystemExit('No dynamic PDU within 35 wall seconds')
for action,extra_args in [('ping',[]),('iperf',[]),('iperf-dl',['--reverse'])]:
    with (b/f'{action}-dynamic-{args.tag}.txt').open('w') as f:
        p=cmd('ping' if action=='ping' else 'iperf',*extra_args,stdout=f,stderr=subprocess.STDOUT,timeout=50)
    print(action,'exit',p.returncode,flush=True)
cmd('status')
