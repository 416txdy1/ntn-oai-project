"""Verify the exact owned RFsim veth/netns before starting UE or changing its routes."""
import argparse,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--claim',action='store_true');a=p.parse_args()
if os.geteuid()!=0:raise SystemExit('Network verification requires sudo')
def ip(*args):return json.loads(subprocess.check_output(['ip',*args],text=True))
host=ip('-d','-j','link','show','oai-stk-host')[0]
peer=ip('-n','oai-stk-ue','-d','-j','link','show','oai-stk-peer')[0]
def require(ok,message):
    if not ok:raise SystemExit('Refusing to use namespace: '+message)
require(host['linkinfo']['info_kind']==peer['linkinfo']['info_kind']=='veth','not a veth pair')
require(host['link_index']==peer['ifindex'] and peer['link_index']==host['ifindex'],'peer indexes differ')
for prefix,name,expected in [([], 'oai-stk-host','10.201.0.1'),(['-n','oai-stk-ue'],'oai-stk-peer','10.201.0.2')]:
    entries=ip(*prefix,'-j','-4','addr','show','dev',name)[0]['addr_info']
    require(len(entries)==1 and entries[0]['local']==expected and entries[0]['prefixlen']==30,'address differs')
names={d['ifname'] for d in ip('-n','oai-stk-ue','-j','link','show')}
require(names.issubset({'lo','oai-stk-peer','oaitun_ue1'}),'unrecognized interfaces present')
owner={'schema':1,'host_ifindex':host['ifindex'],'peer_ifindex':peer['ifindex'],
       'netns_inode':Path('/run/netns/oai-stk-ue').stat().st_ino}
marker=Path('/run/oai-stk-ue.owner.json')
if marker.exists():
    require(not marker.is_symlink() and marker.stat().st_uid==0,'invalid owner marker')
    require(json.loads(marker.read_text())==owner,'owner marker mismatch')
elif a.claim:
    fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(owner,f)
else:raise SystemExit('Namespace is not owned by this experiment; refusing to reuse it')
print('Verified owned oai-stk-ue veth topology')
