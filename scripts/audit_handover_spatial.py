"""验证 handover 业务报告对应运行的真实四端口 IQ，仅输出聚合信息。"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re


def audit(manifest_path: Path, report_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    business = json.loads(report_path.read_text())
    if any(manifest[key] != business[key] for key in ('profile', 'run_id')):
        raise ValueError('业务报告和运行清单不属于同一次运行')
    config = Path(manifest['gnb_config']).read_text()
    for name, value in (('nb_tx', 4), ('nb_rx', 4), ('maxMIMO_layers', 1)):
        if re.findall(r'(?m)^\s*' + name + r'\s*=\s*(\d+)\s*;', config) != [str(value)]:
            raise ValueError('运行配置不符合四端口单层要求: ' + name)
    result = {'run_id': manifest['run_id'], 'business_passed': business['passed'], 'directions': {}}
    for role, dimensions in (('gnb', '1 Tx x 4 Rx'), ('ue', '4 Tx x 1 Rx')):
        log = Path(manifest['logs'][role]).read_text(errors='replace')
        if log.count('QDCHANNEL1 spatial ports: ' + dimensions) != 1:
            raise ValueError(role + ' 未唯一加载预期空间维度')
        result['directions'][role] = dimensions
        requested_workers = manifest.get('qd_workers_requested')
        if requested_workers is not None:
            observed = re.findall(r'QDCHANNEL1 compute workers: (\d+)', log)
            if observed != [str(requested_workers)]:
                raise ValueError(role + ' 的实际计算线程数与运行清单不符')
        if role == 'gnb':
            energies = {str(port): [] for port in range(4)}
            for port, value in re.findall(r'QDCHANNEL1 Tx port (\d+) IQ=\d+ mean_energy=([\d.]+)', log):
                if port not in energies:
                    raise ValueError('出现额外发射端口')
                energies[port].append(float(value))
            if any(sum(math.isfinite(v) and v > 0 for v in values) < 2 for values in energies.values()):
                raise ValueError('存在未实际发送有效 IQ 的端口')
            result['tx_energy'] = {port: {'nonzero_windows': sum(v > 0 for v in values),
                                         'min': min(values), 'max': max(values)}
                                   for port, values in energies.items()}
    result['passed'] = bool(business['passed'] and business.get('numeric_audit_ok'))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.manifest, args.report)
    text = json.dumps(result, indent=2) + '\n'
    args.output.write_text(text)
    print(text)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
