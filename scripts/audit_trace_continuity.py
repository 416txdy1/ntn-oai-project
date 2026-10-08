"""检查 LEO 轨迹位置/速度连续性；不修改输入，不把切星位置混合当成连续轨道。"""
import argparse
import csv
import json
import math
from pathlib import Path


def hermite_state(a, b, u):
    dt = b[0] - a[0]
    position, velocity = [], []
    for k in range(3):
        p = a[1+k]
        v = dt * a[4+k]
        q = 3 * (b[1+k]-p) - dt * (2*a[4+k]+b[4+k])
        c = 2 * (p-b[1+k]) + dt * (a[4+k]+b[4+k])
        position.append(((c*u+q)*u+v)*u+p)
        velocity.append((3*c*u*u+2*q*u+v)/dt)
    return position, velocity


def audit(rows, speed_limit):
    issues = []
    for a, b in zip(rows, rows[1:]):
        dt = b[0] - a[0]
        if dt <= 0:
            raise ValueError('trace time must be strictly increasing')
        secant_speed = math.dist(a[1:4], b[1:4]) / dt
        probes = [math.hypot(*hermite_state(a, b, u)[1]) for u in (0, .25, .5, .75, 1)]
        if max(secant_speed, *probes) <= speed_limit:
            continue
        speeds, dopplers = [], []
        for index in range(1001):
            position, velocity = hermite_state(a, b, index/1000)
            distance = math.dist(position, a[13:16])
            if distance <= 0:
                raise ValueError('zero service range')
            radial = sum((position[k]-a[13+k])*velocity[k] for k in range(3))/distance
            speeds.append(math.hypot(*velocity))
            dopplers.append(-radial/(299792458.0+radial)*2488400000.0)
        issues.append({'stk_interval_s': [a[0], b[0]], 'iq_interval_s_at_rate1': [a[0]-rows[0][0], b[0]-rows[0][0]],
                       'position_step_km': secant_speed*dt/1000,
                       'reported_endpoint_speed_km_s': [math.hypot(*a[4:7])/1000, math.hypot(*b[4:7])/1000],
                       'sampled_hermite_max_speed_km_s': max(speeds)/1000,
                       'sampled_dl_doppler_hz': [min(dopplers), max(dopplers)],
                       'sampling_step_s': dt/1000})
    return {'passed': not issues, 'rows': len(rows), 'leo_speed_limit_m_s': speed_limit,
            'dl_frequency_hz': 2488400000, 'issues': issues,
            'scope': 'LEO kinematic screening; sampled peaks, not a proof of continuous extrema'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--max-speed-m-s', type=float, default=20000)
    args = parser.parse_args()
    if not math.isfinite(args.max_speed_m_s) or args.max_speed_m_s <= 0:
        parser.error('speed limit must be finite and positive')
    rows = [list(map(float, row)) for row in csv.reader(line for line in args.trace.read_text().splitlines()[1:] if line and not line.startswith('#'))]
    if len(rows) < 2 or any(len(row) != 22 or not all(math.isfinite(x) for x in row) for row in rows):
        parser.error('expected at least two finite STKTRACE2 rows with 22 fields')
    report = audit(rows, args.max_speed_m_s)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
