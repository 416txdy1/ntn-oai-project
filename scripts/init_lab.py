"""生成仅保存在 .private 的新实验凭据和核心网配置；不覆盖已有环境。"""
import argparse,json,os,re,secrets,ipaddress
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--subnet-octet',type=int,default=70)
    p.add_argument('--prefix',default='ntn-local')
    p.add_argument('--profile',choices=('zky','integrated-handover','legacy-handover'),default='zky')
    p.add_argument('--private-dir',type=Path)
    p.add_argument('--pdu-subnet')
    a=p.parse_args(argv)
    isolated=a.profile!='zky'
    if isolated:
        a.prefix='ntn-qd-integrated'
        a.subnet_octet=71
    pdu=str(ipaddress.IPv4Network(a.pdu_subnet or ('12.2.1.0/24' if isolated else '10.0.0.0/24')))
    if isolated and pdu!='12.2.1.0/24':p.error('isolated PDU pool conflicts')
    if not 1<=a.subnet_octet<=254 or not re.fullmatch('[a-z][a-z0-9-]{0,62}',a.prefix):p.error('invalid network/prefix')
    root=ROOT;private=a.private_dir or root/('.private/profiles/integrated-handover' if isolated else '.private')
    private=private.expanduser().absolute()
    if isolated and not private.resolve().is_relative_to(root.resolve()/'.private/profiles/integrated-handover'):p.error('private-dir escapes isolated profile')
    if private.exists():raise SystemExit('.private 已存在，拒绝覆盖凭据；沿用现有配置')
    os.umask(0o077)
    private.mkdir(mode=0o700,parents=True);core=private/'core'
    for name in ('conf','database','healthscripts'):(core/name).mkdir(parents=True)
    password=secrets.token_hex(24);key=secrets.token_hex(16);opc=secrets.token_hex(16);imsi='001010000000001'
    template=root/'configs/core'
    ue=(template/'ue.conf.in').read_text().replace('@KEY@',key).replace('@OPC@',opc).replace('@IMSI@',imsi)
    (private/'ue.conf').write_text(ue)
    compose=(template/'compose.yaml.in').read_text().replace('@DB_PASSWORD@',password)
    compose=re.sub(r'(?ms)^    ims:.*?(?=^    oai-udr:)', '',compose)
    compose=re.sub(r'(?m)^(\s*container_name:)\s*"?([a-z0-9-]+)"?\s*$',lambda m:m[1]+' "'+a.prefix+'-'+m[2]+'"',compose)
    compose=compose.replace('oai-cn5g-public-net',a.prefix+'-net').replace('"oai-cn5g"','"ntn'+str(a.subnet_octet)+'"')
    compose=compose.replace('192.168.70.',f'192.168.{a.subnet_octet}.')
    if isolated or a.pdu_subnet:
        compose=compose.replace('10.0.0.0/16',pdu).replace('grep 10.0.0','grep '+pdu)
    if isolated:
        compose=compose.replace('        driver: bridge','        labels:\n            ntn.workspace: '+json.dumps(str(root.resolve()))+'\n        driver: bridge')
    (core/'compose.yaml').write_text(compose)
    config=(template/'config.yaml.in').read_text().replace('@DB_PASSWORD@',password).replace('192.168.70.',f'192.168.{a.subnet_octet}.')
    if isolated or a.pdu_subnet:
        config=re.sub(r'(?m)(  - dnn: "oai"\n    pdu_session_type: "IPV4"\n    ipv4_subnet: )"[^"]+"',lambda m:m[1]+'"'+pdu+'"',config)
    if isolated:
        config=re.sub(r'(?m)^          - dnn: "(?:openairinterface|ims|default)"\n','',config)
        config=re.sub(r'(?m)^    - single_nssai: \*embb_slice\n      dnn: "(?:openairinterface|ims|default)"\n(?:        .*\n|      qos_profile:\n)*','',config)
        config=re.sub(r'(?m)^  - dnn: "(?:openairinterface|ims|default)"\n(?:    .*\n)*','',config)
    (core/'conf/config.yaml').write_text(config)
    sequence=json.dumps({'sqn':'000000000000','sqnScheme':'NON_TIME_BASED','lastIndexes':{'ausf':0}})
    profile=json.dumps({'oai':{'pduSessionTypes':{'defaultSessionType':'IPV4'},'sscModes':{'defaultSscMode':'SSC_MODE_1'},'sessionAmbr':{'uplink':'100Mbps','downlink':'100Mbps'},'5gQosProfile':{'5qi':9,'arp':{'priorityLevel':1,'preemptCap':'NOT_PREEMPT','preemptVuln':'NOT_PREEMPTABLE'}}}})
    sql=(template/'schema.sql').read_text()+f"\nINSERT INTO AuthenticationSubscription (ueid,authenticationMethod,encPermanentKey,sequenceNumber,authenticationManagementField,algorithmId,encOpcKey,supi) VALUES ('{imsi}','5G_AKA','{key}','{sequence}','8000','milenage','{opc}','{imsi}');\nINSERT INTO SessionManagementSubscriptionData (ueid,servingPlmnid,singleNssai,dnnConfigurations) VALUES ('{imsi}','00101','{{\"sst\":1,\"sd\":\"ffffff\"}}','{profile}');\n"
    (core/'database/oai_db.sql').write_text(sql)
    (core/'healthscripts/mysql-healthcheck.sh').write_text('#!/bin/bash\nexport MYSQL_PWD="$MYSQL_ROOT_PASSWORD"\nexec mysql -h127.0.0.1 -uroot -Doai_db -e "SELECT COUNT(*) FROM AuthenticationSubscription" >/dev/null 2>&1\n')
    # Docker 挂载文件需由容器内非 root 用户读取；宿主 .private 目录仍为 0700。
    (core/'healthscripts/mysql-healthcheck.sh').chmod(0o755)
    for mounted in (core/'database/oai_db.sql', core/'conf/config.yaml'):
        mounted.chmod(0o644)
    settings={'amf_ip':f'192.168.{a.subnet_octet}.132','gnb_ip_cidr':f'192.168.{a.subnet_octet}.129/26','ext_dn_ip':f'192.168.{a.subnet_octet}.135','ext_dn_container':a.prefix+'-oai-ext-dn','compose_project':a.prefix}
    if isolated:settings['ue_pdu_subnet']=pdu
    (private/'settings.json').write_text(json.dumps(settings,indent=2))
    print('已生成私有实验配置；密钥不会输出。请重新 source scripts/env.sh')

if __name__=='__main__':main()
