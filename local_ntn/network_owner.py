"""RFsim topology ownership and precise, identity-checked lifecycle."""
import ipaddress
import json
import os
from pathlib import Path
import stat
import subprocess


def create_owner(config, topology):
    host, peer = topology['host'], topology['peer']
    if (host.get('ifname') != config.host_veth or peer.get('ifname') != config.ue_veth
            or host.get('linkinfo', {}).get('info_kind') != 'veth'
            or peer.get('linkinfo', {}).get('info_kind') != 'veth'
            or host.get('link_index') != peer.get('ifindex')
            or peer.get('link_index') != host.get('ifindex')):
        raise ValueError('RFsim veth identity differs')
    for field, address in [('host_addresses',config.rf_host_ip),('peer_addresses',config.rf_ue_ip)]:
        entries = topology[field]
        if len(entries) != 1 or entries[0].get('local') != address or entries[0].get('prefixlen') != 30:
            raise ValueError('RFsim address differs')
    if not set(topology['interfaces']).issubset({'lo', config.ue_veth, 'oaitun_ue1'}):
        raise ValueError('Unrecognized namespace interfaces')
    if config.profile=='zky':
        return {'schema':1,'host_ifindex':host['ifindex'],'peer_ifindex':peer['ifindex'],'netns_inode':topology['netns_inode']}
    return {'schema':2, 'profile':config.profile, 'run_id':config.run_id,
            'namespace':config.namespace, 'host_veth':config.host_veth,'ue_veth':config.ue_veth,
            'host_ifindex':host['ifindex'],'peer_ifindex':peer['ifindex'],
            'netns_inode':topology['netns_inode'], 'workspace':str(config.root)}


def validate_owner(config, topology, marker):
    if marker != create_owner(config, topology):
        raise ValueError('Network owner marker mismatch')


def marker_identity(path):
    info=os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0:raise ValueError('Owner marker must be a root-owned regular file')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        opened=os.fstat(fd);named=os.lstat(path)
        identity=(opened.st_dev,opened.st_ino)
        if not stat.S_ISREG(opened.st_mode) or opened.st_uid!=0 or identity!=(info.st_dev,info.st_ino) or identity!=(named.st_dev,named.st_ino):
            raise ValueError('Marker pathname/opened identity differs')
        return identity
    finally:os.close(fd)

def read_marker_capture(path,expected=None):
    info=os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0:raise ValueError('Owner marker must be a root-owned regular file')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        opened=os.fstat(stream.fileno());identity=(opened.st_dev,opened.st_ino)
        if not stat.S_ISREG(opened.st_mode) or opened.st_uid!=0 or identity!=(info.st_dev,info.st_ino) or (expected is not None and identity!=expected):
            raise ValueError('Marker opened identity differs')
        value=json.load(stream);named=os.lstat(path)
        if not stat.S_ISREG(named.st_mode) or named.st_uid!=0 or (named.st_dev,named.st_ino)!=identity:
            raise ValueError('Marker pathname replaced during read')
        return value,identity

def read_marker(path):
    return read_marker_capture(path)[0]

def write_marker(path,marker,on_created=None):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        opened=os.fstat(stream.fileno());identity=(opened.st_dev,opened.st_ino)
        if on_created:on_created(identity)
        json.dump(marker,stream);stream.flush()
        if marker_identity(path)!=identity:raise ValueError('Created marker was replaced')
        return identity


def command(argv):
    result=subprocess.run(argv,check=True,capture_output=True,text=True)
    return result.stdout


def namespace_inventory(output):
    # iproute2 emits no bytes for a successful empty namespace inventory.
    rows=json.loads(output) if output.strip() else []
    if not isinstance(rows,list) or any(not isinstance(row,dict) or not isinstance(row.get('name'),str) or not row['name'] for row in rows):
        raise ValueError('Invalid namespace inventory')
    return rows


class NetworkManager:
    def __init__(self, config, runner=command):
        self.config=config; self.run=runner; self.marker_identity=None; self.created_marker_identity=None
    def ip(self,*args):
        output=self.run(['ip',*args])
        return namespace_inventory(output) if args==('-j','netns','list') else json.loads(output)
    def inode(self):
        path=Path('/run/netns')/self.config.namespace
        info=path.lstat()
        if stat.S_ISLNK(info.st_mode):raise ValueError('Symlink namespace refused')
        return info.st_ino
    def link(self,name):
        return self.ip('-d','-j','link','show','dev',name)[0]
    def topology(self):
        c=self.config
        return {'host':self.link(c.host_veth),
                'peer':self.ip('-n',c.namespace,'-d','-j','link','show','dev',c.ue_veth)[0],
                'netns_inode':self.inode(),
                'host_addresses':self.ip('-j','-4','addr','show','dev',c.host_veth)[0]['addr_info'],
                'peer_addresses':self.ip('-n',c.namespace,'-j','-4','addr','show','dev',c.ue_veth)[0]['addr_info'],
                'interfaces':[d['ifname'] for d in self.ip('-n',c.namespace,'-j','link','show')]}
    def marker_created(self,identity):
        self.created_marker_identity=identity
        self.marker_identity=identity
    def checked_marker(self):
        value,identity=read_marker_capture(self.config.owner_file,self.marker_identity)
        if self.marker_identity is None:self.marker_identity=identity
        return value
    def verify(self,claim=False):
        c=self.config;t=self.topology();owner=create_owner(c,t)
        if c.owner_file.exists() or c.owner_file.is_symlink():
            validate_owner(c,t,self.checked_marker())
        elif claim:
            write_marker(c.owner_file,owner,self.marker_created)
            validate_owner(c,t,self.checked_marker())
        else:raise ValueError('Namespace has no owner marker')
        return owner

    def preflight(self):
        c=self.config
        if c.owner_file.exists() or c.owner_file.is_symlink():raise ValueError('Existing owner marker refused')
        if any(n['name']==c.namespace for n in self.ip('-j','netns','list')):
            raise ValueError('Namespace already exists')
        if any(n['ifname'] in (c.host_veth,c.ue_veth) for n in self.ip('-j','link','show')):
            raise ValueError('Veth name conflict')
        network=ipaddress.ip_network(c.rf_host_ip+'/30',strict=False)
        for route in self.ip('-j','-4','route','show','table','all'):
            destination=route.get('dst','default')
            if destination != 'default' and network.overlaps(ipaddress.ip_network(destination,strict=False)):
                raise ValueError('RFsim address route conflict')
    def up(self):
        c=self.config
        if any(n['name']==c.namespace for n in self.ip('-j','netns','list')):
            return self.verify()
        self.preflight();created_inode=None;created_host=None
        try:
            self.run(['ip','netns','add',c.namespace]);created_inode=self.inode()
            self.run(['ip','link','add',c.host_veth,'type','veth','peer','name',c.ue_veth])
            created_host=self.link(c.host_veth)['ifindex']
            self.run(['ip','link','set',c.ue_veth,'netns',c.namespace])
            self.run(['ip','addr','add',c.rf_host_ip+'/30','dev',c.host_veth])
            self.run(['ip','link','set',c.host_veth,'up'])
            self.run(['ip','-n',c.namespace,'addr','add',c.rf_ue_ip+'/30','dev',c.ue_veth])
            self.run(['ip','-n',c.namespace,'link','set',c.ue_veth,'up'])
            self.run(['ip','-n',c.namespace,'link','set','lo','up'])
            return self.verify(claim=True)
        except Exception:
            # Successful creates are recorded before any subsequent mutation.
            # Missing/replaced objects are left alone; names alone never authorize deletion.
            if created_host is not None:
                try:
                    current=self.link(c.host_veth)
                    if current['ifindex']==created_host and current.get('linkinfo',{}).get('info_kind')=='veth':
                        self.run(['ip','link','delete',c.host_veth])
                except (OSError,ValueError,subprocess.CalledProcessError):pass
            if created_inode is not None:
                try:
                    if self.inode()==created_inode:self.run(['ip','netns','delete',c.namespace])
                except (OSError,ValueError,subprocess.CalledProcessError):pass
            if self.created_marker_identity is not None:
                try:
                    if marker_identity(c.owner_file)==self.created_marker_identity:c.owner_file.unlink()
                except (OSError,ValueError):pass
            raise
    def down(self):
        c=self.config;owner=self.verify()
        # Recheck at the command boundary before deleting either object.
        validate_owner(c,self.topology(),owner)
        if self.checked_marker()!=owner:raise ValueError('Marker changed before link deletion')
        self.run(['ip','link','delete',c.host_veth])
        if self.inode()!=owner['netns_inode']:raise ValueError('Namespace changed during down')
        if self.checked_marker()!=owner:raise ValueError('Marker changed before namespace deletion')
        self.run(['ip','netns','delete',c.namespace])
        if self.checked_marker()!=owner:raise ValueError('Owner marker changed during down')
        c.owner_file.unlink()
