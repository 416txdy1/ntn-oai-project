"""Operate only the selected workspace's isolated Compose project."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'local_ntn'))
from runtime_config import resolve_runtime


def command(argv):
    return subprocess.run(argv,check=True,capture_output=True,text=True).stdout


class CoreLab:
    def __init__(self,config,runner=command):
        self.config=config;self.run=runner
        self.core=config.private_dir/'core';self.compose=self.core/'compose.yaml'
        self.marker=self.core/'owner.json'
    def identity(self):
        if self.config.profile=='zky' or self.config.core_project!='ntn-qd-integrated':
            raise ValueError('Core controller requires dedicated profile/project')
        if not self.core.resolve().is_relative_to(self.config.private_dir.resolve()):
            raise ValueError('Core directory escapes private directory')
        digest=hashlib.sha256()
        for relative in ['compose.yaml','conf/config.yaml','database/oai_db.sql','healthscripts/mysql-healthcheck.sh']:
            path=self.core/relative
            if path.is_symlink() or not path.resolve().is_relative_to(self.core.resolve()):
                raise ValueError('Core input symlink refused')
            digest.update(relative.encode());digest.update(path.read_bytes())
        return {'schema':1,'workspace':str(self.config.root),'project':self.config.core_project,
                'config_hash':digest.hexdigest(),'run_id':self.config.run_id}
    def validate(self,marker):
        expected=self.identity()
        if any(marker.get(k)!=expected[k] for k in ('schema','workspace','project','config_hash')):
            raise ValueError('Core ownership workspace/project/config hash differs')
    def read_owner(self):
        info=self.marker.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid not in (0,os.geteuid()):
            raise ValueError('Core owner must be an owned regular file')
        fd=os.open(self.marker,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:return json.load(stream)
    def inventory(self):
        # Batch CLI calls, retaining a complete, exact inventory for every check.
        def inspect(ids, prefix):
            if len(ids) != len(set(ids)):
                raise ValueError('Duplicate inventory query IDs')
            if not ids:
                return []
            items = json.loads(self.run(prefix + ids))
            if not isinstance(items, list) or any(
                    not isinstance(item, dict) or not isinstance(item.get('Id'), str)
                    for item in items):
                raise ValueError('Invalid inventory response')
            returned = [item['Id'] for item in items]
            if len(returned) != len(ids) or set(returned) != set(ids):
                raise ValueError('Incomplete or unexpected inventory response')
            return items
        container_ids = self.run(['docker','ps','-aq','--no-trunc']).split()
        containers = inspect(container_ids, ['docker','inspect'])
        network_ids = self.run(['docker','network','ls','-q','--no-trunc']).split()
        networks = inspect(network_ids, ['docker','network','inspect'])
        return containers, networks
    def names(self):
        return set(re.findall(r'^\s*container_name:\s*"?([a-z0-9-]+)',self.compose.read_text(),re.M))
    def own_container(self,item):
        labels=item.get('Config',{}).get('Labels') or {}
        return (labels.get('com.docker.compose.project')==self.config.core_project
                and labels.get('com.docker.compose.project.working_dir')==str(self.core)
                and labels.get('com.docker.compose.project.config_files')==str(self.compose)
                and item.get('Name','').lstrip('/') in self.names())
    def own_network(self,item):
        labels=item.get('Labels') or {}
        return (labels.get('com.docker.compose.project')==self.config.core_project
                and labels.get('com.docker.compose.network')=='public_net'
                and labels.get('ntn.workspace')==str(self.config.root)
                and item.get('Name')==self.config.core_project+'-net')
    def resources(self,inventory):
        containers,networks=inventory
        return {'containers':sorted(i['Id'] for i in containers if self.own_container(i)),
                'networks':sorted(i['Id'] for i in networks if self.own_network(i))}
    def preflight(self):
        expected=self.identity();inventory=self.inventory();containers,networks=inventory
        owner=self.read_owner() if self.marker.exists() or self.marker.is_symlink() else None
        if owner:self.validate(owner)
        names=self.names();project=self.config.core_project
        for item in containers:
            labels=item.get('Config',{}).get('Labels') or {}
            if item.get('Name','').lstrip('/') in names or labels.get('com.docker.compose.project')==project:
                if not owner or not self.own_container(item) or item['Id'] not in owner.get('containers',[]):
                    raise ValueError('Container name/project belongs to another workspace or deployment')
        pool=ipaddress.ip_network(self.config.gnb_ip_cidr,strict=False)
        for item in networks:
            ipam=item.get('IPAM',{}).get('Config',[])
            if ipam is None:ipam=[]
            options=item.get('Options',{})
            if options is None:options={}
            if not isinstance(ipam,list) or not isinstance(options,dict):raise ValueError('Invalid network metadata')
            overlaps=any(pool.overlaps(ipaddress.ip_network(e['Subnet'],strict=False))
                         for e in ipam if e.get('Subnet') and ':' not in e['Subnet'])
            labels=item.get('Labels') or {}
            relevant=(item.get('Name')==project+'-net' or labels.get('com.docker.compose.project')==project
                      or options.get('com.docker.network.bridge.name')=='ntn71' or overlaps)
            if relevant and (not owner or not self.own_network(item) or item['Id'] not in owner.get('networks',[])):
                raise ValueError('Dedicated core network/subnet conflict')
        if owner and self.resources(inventory)!={k:owner.get(k,[]) for k in ('containers','networks')}:
            raise ValueError('Core resource IDs differ from owner record')
        return inventory
    def compose_command(self,*args):
        return ['docker','compose','--project-name',self.config.core_project,'--file',str(self.compose),*args]
    def save_owner(self,inventory):
        marker=dict(self.identity(),**self.resources(inventory))
        temp=self.marker.with_suffix('.json.tmp')
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(marker,stream)
        os.replace(temp,self.marker)
        return marker
    def up(self):
        before=self.preflight();before_ids={i['Id'] for group in before for i in group}
        starting_identity=self.identity()
        previous_owner=self.read_owner() if self.marker.exists() else None
        saved_owner=None
        try:
            self.run(self.compose_command('up','-d'))
            after=self.inventory()
            # Only correctly labelled resources may be recorded as ours.
            for item in after[0]:
                if item.get('Name','').lstrip('/') in self.names() and not self.own_container(item):
                    raise ValueError('Foreign container appeared during startup')
            if self.identity()!=starting_identity:raise ValueError('Core configuration changed during startup')
            saved_owner=self.save_owner(after)
            self.preflight()
        except Exception:
            # Never compose-down on partial failure: it could remove preexisting resources.
            after=self.inventory()
            for item in after[0]:
                if item['Id'] not in before_ids and self.own_container(item):self.run(['docker','rm','-f',item['Id']])
            for item in after[1]:
                if item['Id'] not in before_ids and self.own_network(item):self.run(['docker','network','rm',item['Id']])
            if saved_owner is not None and self.read_owner()==saved_owner:
                self.marker.unlink()
                if previous_owner is not None:
                    fd=os.open(self.marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'w') as stream:json.dump(previous_owner,stream)
            raise
    def down(self):
        owner=self.read_owner();self.validate(owner);self.preflight()
        self.run(self.compose_command('down'))
        if self.read_owner()!=owner:raise ValueError('Core owner changed during shutdown')
        self.marker.unlink()
    def status(self):
        self.preflight()
        return self.run(self.compose_command('ps','--format','json'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('preflight','up','down','status'))
    parser.add_argument('--profile',required=True)
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args(argv)
    try:
        c=resolve_runtime(Path(__file__).resolve().parents[1],args.profile,args.run_id,os.environ)
        lab=CoreLab(c)
        if args.action=='status':print(lab.status())
        else:getattr(lab,args.action)();print(f'Core {args.action}: {c.core_project}')
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as error:
        # subprocess output may contain credentials; never relay it.
        parser.exit(1,f'Core operation refused ({type(error).__name__})\n')

if __name__=='__main__':main()
