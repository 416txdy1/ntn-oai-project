"""只输出数值摘要：独立验算空间链路运行日志，不发布原始 UE 日志。"""
from __future__ import annotations
import argparse
import bisect
import csv
import json
import math
from pathlib import Path
import re

FS = 7_680_000.0
C = 299_792_458.0
LINE = re.compile(r"STKTRACE2 (UL|DL) IQ=([\d.]+) STK=([\d.]+) delay=([\d.]+)ms Doppler=([-\d.]+)Hz gain=([-\d.]+)dB C/N=([-\d.]+)dB valid=(\d) samples=(\d+)")


def expected_state(rows: list[list[float]], time_s: float, rate: float, uplink: bool) -> dict[str, float]:
    if not rows[0][0] <= time_s <= rows[-1][0]:
        raise ValueError("验算时间越出 trace")
    index = min(len(rows)-2, max(0, bisect.bisect_right([row[0] for row in rows], time_s)-1))
    left, right = rows[index:index+2]
    dt = right[0] - left[0]
    u = (time_s - left[0]) / dt
    position, velocity = [], []
    # 由端点位置、端点速度求三次多项式系数，独立于 C 的 Hermite 基函数实现。
    for axis in range(3):
        p0, p1, v0, v1 = left[1+axis], right[1+axis], left[4+axis], right[4+axis]
        a1 = dt*v0
        a2 = 3*(p1-p0)-dt*(2*v0+v1)
        a3 = -2*(p1-p0)+dt*(v0+v1)
        position.append(p0+u*(a1+u*(a2+u*a3)))
        velocity.append((a1+u*(2*a2+3*u*a3))/dt)
    sites = [[left[start+i]+u*(right[start+i]-left[start+i]) for i in range(3)] for start in (10,13)]
    ranges = [math.dist(position, site) for site in sites]
    radial = sum((p-s)*v for p,s,v in zip(position,sites[1],velocity)) / ranges[1] * rate
    frequency = 1_614_900_000 if uplink else 2_488_400_000
    power_col, cn_col, valid_col = (17,19,21) if uplink else (16,18,20)
    reference = next(row[power_col] for row in rows if row[valid_col])
    return {"delay_ms": sum(ranges)/C*1000,
            "doppler_hz": -radial/(C if uplink else C+radial)*frequency,
            "gain_db": left[power_col]+u*(right[power_col]-left[power_col])-reference,
            "cn_db": left[cn_col]+u*(right[cn_col]-left[cn_col]),
            "valid": int(bool(left[valid_col] and right[valid_col]))}


def audit_run(root: Path, label: str, ports: int) -> dict:
    # label 只允许文件名字符，避免从日志参数读取工作区外任意文件。
    if not re.fullmatch(r"smoke-[01]-[0-9]+", label):
        raise ValueError("非法 smoke label")
    result = json.loads((root/'.runtime/reports'/f'{label}.json').read_text())
    rows = list(csv.reader(line for line in (root/'examples/fdd-pass/trace.csv').read_text().splitlines()[1:] if line and not line.startswith('#')))
    trace = [list(map(float,row)) for row in rows]
    report = {"label": label, "ports": ports, "business_passed": result.get('passed',False), "rate": result['rate'], "directions": {}}
    for kind, uplink in (('gnb',True),('ue',False)):
        text = (root/'local_ntn'/f'{kind}-{label}.log').read_text(errors='replace')
        expected_ports = f"1 Tx x {ports} Rx" if uplink else f"{ports} Tx x 1 Rx"
        if text.count('QDCHANNEL1 spatial ports: '+expected_ports) != 1:
            raise ValueError(f"{kind} 空间维度未正确加载")
        errors = dict.fromkeys(('iq_seconds','stk_seconds','delay_ms','doppler_hz','gain_db','cn_db'),0.0)
        count = 0
        for match in LINE.finditer(text):
            if (match[1]=='UL') != uplink:
                raise ValueError("方向错误")
            iq = int(match[9])/FS
            trace_time = trace[0][0]+iq*result['rate']
            expected = expected_state(trace,trace_time,result['rate'],uplink)
            errors['iq_seconds'] = max(errors['iq_seconds'], abs(float(match[2])-iq))
            errors['stk_seconds'] = max(errors['stk_seconds'], abs(float(match[3])-trace_time))
            for index,key in enumerate(('delay_ms','doppler_hz','gain_db','cn_db'),4):
                errors[key] = max(errors[key], abs(float(match[index])-expected[key]))
            if int(match[8]) != expected['valid'] or not expected['valid']:
                raise ValueError("有业务验收记录落入不可见区间")
            count += 1
        if count < 3:
            raise ValueError("运行样本不足以验算")
        tolerances = {'iq_seconds':1e-6,'stk_seconds':1e-6,'delay_ms':1e-6,'doppler_hz':1e-3,'gain_db':1e-3,'cn_db':1e-3}
        if any(not math.isfinite(value) or value > tolerances[key] for key,value in errors.items()):
            raise ValueError(f"{kind} 公式验算失败: {errors}")
        direction = {'rows':count,'max_errors':errors,'pbch_failures':text.count('Error decoding PBCH')}
        if kind == 'gnb':
            energies = {str(port):[] for port in range(ports)}
            for port, value in re.findall(r'QDCHANNEL1 Tx port (\d+) IQ=\d+ mean_energy=([\d.]+)',text):
                if port not in energies: raise ValueError('额外发射端口')
                energies[port].append(float(value))
            if any(sum(value>0 for value in values)<2 for values in energies.values()):
                raise ValueError('存在未实际发送有效 IQ 的端口')
            direction['tx_energy'] = {port:{'nonzero_windows':sum(v>0 for v in values),'min':min(values),'max':max(values)} for port,values in energies.items()}
        report['directions'][kind] = direction
    report['passed'] = report['business_passed'] and all(v['pbch_failures']==0 for v in report['directions'].values())
    return report


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--ports',type=int,choices=(2,4),required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    report=audit_run(root,args.label,args.ports)
    (root/'.runtime/reports'/f'{args.label}-spatial-audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__ == '__main__': raise SystemExit(main())
