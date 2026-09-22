"""Insert the missing local lab UE only; preserve all existing subscribers."""
import json
import re
import subprocess
import argparse
from pathlib import Path

def sql(q):
    p=subprocess.run(['docker','exec','-i','mysql','sh','-c',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot -N -B "$MYSQL_DATABASE"'],
        input=q,text=True,capture_output=True)
    if p.returncode:
        raise RuntimeError('Database operation failed (details withheld to avoid disclosing SIM keys)')
    return p.stdout

conf=Path('/home/kayoko/OAI/openairinterface5g/ci-scripts/conf_files/nrue.uicc.ntn-leo.conf').read_text()
conf=re.sub(r'#[^\n]*','',conf)
v={k.lower():val for k,val in re.findall(r'(\w+)\s*=\s*"([^"\n]*)"',conf)}
imsi=v['imsi']; key=v['key']; opc=v['opc']
p=argparse.ArgumentParser();p.add_argument('--local-20895',action='store_true');args=p.parse_args()
if args.local_20895:
    imsi='208950000009901'
    conf=re.sub(r'(imsi\s*=\s*)"\d+"',r'\g<1>"'+imsi+'"',conf)
    conf=re.sub(r'(nssai_sst\s*=\s*1\s*;)',r'\1 nssai_sd = 1;',conf)
    conf=conf.replace('dnn = "oai"','dnn = "oai.ipv4"')
    target=Path('/home/kayoko/.local/share/oai-stk/ue.local.conf')
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.read_text()!=conf:
        old=target.read_text()
        if '208950000000041' not in old:
            raise SystemExit('Existing local UE config differs; refusing overwrite')
        backup=target.with_suffix('.conf.initial-20895-backup')
        if not backup.exists(): backup.write_text(old);backup.chmod(0o600)
    target.write_text(conf);target.chmod(0o600)
assert re.fullmatch(r'\d{15}',imsi)
assert re.fullmatch(r'[0-9a-fA-F]{32}',key) and re.fullmatch(r'[0-9a-fA-F]{32}',opc)
sequence=json.dumps({'sqn':'000000000000','sqnScheme':'NON_TIME_BASED','lastIndexes':{'ausf':0}})
dnn='oai.ipv4' if args.local_20895 else 'oai'
slice_info=json.dumps({'sst':1,'sd':'000001' if args.local_20895 else '000000'})
profile={dnn:{'pduSessionTypes':{'defaultSessionType':'IPV4'},
    'sscModes':{'defaultSscMode':'SSC_MODE_1'},
    'sessionAmbr':{'uplink':'100Mbps','downlink':'100Mbps'},
    '5gQosProfile':{'5qi':9,'arp':{'priorityLevel':1,'preemptCap':'NOT_PREEMPT','preemptVuln':'NOT_PREEMPTABLE'}}}}
if sql(f"SELECT COUNT(*) FROM AuthenticationSubscription WHERE ueid='{imsi}';").strip()!='0':
    match=sql(f"SELECT COUNT(*) FROM AuthenticationSubscription WHERE ueid='{imsi}' AND LOWER(encPermanentKey)=LOWER('{key}') AND LOWER(encOpcKey)=LOWER('{opc}');").strip()=='1'
    if not match: raise SystemExit('Existing subscriber keys differ; no database overwrite performed')
    if args.local_20895:
        sql(f"UPDATE SessionManagementSubscriptionData SET singleNssai='{slice_info}',dnnConfigurations='{json.dumps(profile)}' WHERE ueid='{imsi}' AND servingPlmnid='20895';")
    print('Existing authentication matches; SQN preserved. Local session profile:',imsi,dnn,slice_info)
    raise SystemExit(0)
query=f"""START TRANSACTION;
INSERT INTO AuthenticationSubscription
(ueid,authenticationMethod,encPermanentKey,sequenceNumber,authenticationManagementField,algorithmId,encOpcKey,supi)
VALUES ('{imsi}','5G_AKA','{key}','{sequence}','8000','milenage','{opc}','{imsi}');
INSERT INTO SessionManagementSubscriptionData (ueid,servingPlmnid,singleNssai,dnnConfigurations)
VALUES ('{imsi}','20895','{slice_info}','{json.dumps(profile)}');
COMMIT;
"""
sql(query)
print('Inserted one lab subscriber and its oai/SST=1 session profile:',imsi)
