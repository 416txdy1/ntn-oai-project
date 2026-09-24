"""Read-only local subscriber audit; never print authentication secrets."""
import json
import re
import subprocess
import sys
from pathlib import Path
from paths import OAI_REPO

def run(args):
    p=subprocess.run(args,text=True,capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-1000:])
    return p.stdout

def sql(q):
    return run(['docker','exec','mysql','sh','-c',
                'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot -N -B "$MYSQL_DATABASE" -e "$1"',
                'audit',q])

conf=Path(sys.argv[1] if len(sys.argv)>1 else OAI_REPO/'ci-scripts/conf_files/nrue.uicc.ntn-leo.conf').read_text()
conf=re.sub(r'#[^\n]*','',conf)
fields={k.lower():v for k,v in re.findall(r'([A-Za-z0-9_]+)\s*=\s*"([^"\n]*)"',conf)}
safe={k:v for k,v in fields.items() if k in ('imsi','dnn','nssai_sst','nssai_sd')}
print('UE_IDENTITY',json.dumps(safe))
print('AUTH_FIELD_NAMES',[k for k in fields if any(x in k for x in ('key','opc','imsi'))])
print('TABLES',sql('SHOW TABLES'))
print('AUTH_SCHEMA',sql('SHOW COLUMNS FROM AuthenticationSubscription'))
imsi=fields.get('imsi','')
assert imsi.isdigit()
rows=sql("SELECT JSON_OBJECT('ueid',ueid,'key',encPermanentKey,'opc',encOpcKey,'method',authenticationMethod) FROM AuthenticationSubscription WHERE ueid='"+imsi+"'").splitlines()
for line in rows:
    row=json.loads(line)
    key=fields.get('key',fields.get('uicc_key',''))
    opc=fields.get('opc',fields.get('uicc_opc',''))
    print('AUTH_MATCH',json.dumps({'ueid':row['ueid'],'method':row['method'],
        'key_matches':bool(key) and key.lower()==row['key'].lower(),
        'opc_matches':bool(opc) and opc.lower()==row['opc'].lower()}))
print('SUBSCRIBER_ROWS',len(rows))
print('AUTH_IDS',sql('SELECT ueid FROM AuthenticationSubscription LIMIT 12'))
print('SESSION_SCHEMA',sql('SHOW COLUMNS FROM SessionManagementSubscriptionData'))
print('SESSION_EXAMPLES',sql('SELECT ueid,servingPlmnid,singleNssai,dnnConfigurations FROM SessionManagementSubscriptionData LIMIT 2'))
