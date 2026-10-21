"""Aggregate actual RF ports separately from requested settings and playback."""
import json
import math
from pathlib import Path
import re
import sys


def audit_spatial(manifest, mode, workers):
    ports = 4 if mode == 'miso4-subarray' else 1
    if mode not in ('siso', 'miso4-subarray'):
        raise ValueError('Unsupported spatial mode')
    if manifest.get('spatial_mode_requested') != mode:
        raise ValueError('Run manifest spatial mode differs from requested mode')
    if manifest.get('qd_workers_requested') != str(workers):
        raise ValueError('Run manifest worker count differs from requested count')
    config = Path(manifest['gnb_config']).read_text()
    settings = [('nb_tx',ports),('nb_rx',ports)]
    if ports == 4:
        settings += [('maxMIMO_layers',1)]
    for name,value in settings:
        actual = re.findall(r'(?m)^\s*'+name+r'\s*=\s*(\d+)\s*;',config)
        if actual != [str(value)]:
            raise ValueError('Generated radio configuration differs: '+name)
    evidence = {'passed':True,'mode':mode,'directions':{},'compute_workers':{},'active_tx_ports':[]}
    for role,expected in [('gnb',(1,ports)),('ue',(ports,1))]:
        log = Path(manifest['logs'][role]).read_text(errors='replace')
        observed = re.findall(r'QDCHANNEL1 spatial ports: (\d+) Tx x (\d+) Rx',log)
        if observed != [tuple(str(v) for v in expected)]:
            raise ValueError(role+' actual spatial dimensions differ or are missing')
        compute = re.findall(r'QDCHANNEL1 compute workers: (\d+)',log)
        if compute != [str(workers)]:
            raise ValueError(role+' actual compute worker count differs or is missing')
        evidence['directions'][role] = dict(tx=expected[0],rx=expected[1])
        evidence['compute_workers'][role] = workers
        if role == 'gnb' and ports == 4:
            energy = {i:[] for i in range(ports)}
            for port,value in re.findall(r'QDCHANNEL1 Tx port (\d+) IQ=\d+ mean_energy=([\d.]+)',log):
                if int(port) not in energy:
                    raise ValueError('Unexpected transmit port')
                energy[int(port)].append(float(value))
            for port,values in energy.items():
                if sum(math.isfinite(v) and v > 0 for v in values) < 2:
                    raise ValueError('Transmit port has insufficient actual nonzero IQ: '+str(port))
            evidence['active_tx_ports'] = list(energy)
    return evidence


def audit_live_run(root, run, mode, workers):
    sys.path.insert(0,str(root/'local_ntn'))
    from experiment import observed_sample_rate, write_manifest
    from audit_runtime_numbers import audit_manifest
    path=run/'run.json'
    manifest=json.loads(path.read_text())
    logs={role:Path(manifest['logs'][role]).read_text(errors='replace') for role in ('gnb','ue')}
    manifest['sample_rate_hz']=observed_sample_rate(logs)
    write_manifest(path,manifest)
    numeric=audit_manifest(path)
    return {'numeric_audit_ok':True,'numeric':numeric,'spatial':audit_spatial(manifest,mode,workers)}
