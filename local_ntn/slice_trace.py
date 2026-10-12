"""Create a paired absolute-time trace/schedule slice without overwriting inputs."""
from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path


def read_pair(trace: Path, schedule: Path):
    lines = trace.read_text(encoding='ascii').splitlines()
    if len(lines) < 4 or lines[0] != 'STKTRACE2':
        raise ValueError('trace must start with STKTRACE2 and contain two samples')
    rows = [line for line in lines[2:] if line and not line.startswith('#')]
    times = [float(line.split(',', 1)[0]) for line in rows]
    with schedule.open(newline='', encoding='ascii') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        schedule_rows = [row for row in reader if row]
    if not header or header[0] != 'time':
        raise ValueError('schedule must have a time column')
    schedule_times = [float(row[0]) for row in schedule_rows]
    if (len(times) < 2 or not all(math.isfinite(t) for t in times)
            or any(a >= b for a, b in zip(times, times[1:]))):
        raise ValueError('trace timestamps must be finite and strictly increasing')
    if times != schedule_times:
        raise ValueError('trace/schedule must use the same absolute timestamps')
    return lines[1], rows, header, schedule_rows, times


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('trace', 'schedule', 'trace-out', 'schedule-out'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--stop', type=float, required=True)
    a = p.parse_args(argv)
    try:
        if not math.isfinite(a.start) or not math.isfinite(a.stop) or a.stop <= a.start:
            raise ValueError('finite stop must be greater than finite start')
        outputs = [a.trace_out, a.schedule_out]
        resolved = [path.resolve() for path in outputs]
        inputs = {a.trace.resolve(), a.schedule.resolve()}
        if len(set(resolved)) != 2 or any(path in inputs for path in resolved):
            raise ValueError('outputs must be distinct from both source inputs')
        if any(path.exists() or path.is_symlink() for path in outputs):
            raise ValueError('refusing to overwrite existing slice outputs')
        trace_header, trace_rows, header, schedule_rows, times = read_pair(a.trace, a.schedule)
        if a.start < times[0] or a.stop > times[-1]:
            raise ValueError('requested slice is outside the common absolute input interval')
        indices = [i for i, t in enumerate(times) if a.start <= t <= a.stop]
        if len(indices) < 2:
            raise ValueError('trace slice contains fewer than two samples')
        selected_trace = [trace_rows[i] for i in indices]
        selected_schedule = [schedule_rows[i] for i in indices]
        for path in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation keeps a concurrent caller from overwriting either input/output.
        with a.trace_out.open('x', encoding='ascii', newline='\n') as stream:
            stream.write('STKTRACE2\n' + trace_header + '\n' + '\n'.join(selected_trace) + '\n')
        with a.schedule_out.open('x', encoding='ascii', newline='') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(header)
            writer.writerows(selected_schedule)
        print(f'wrote {len(indices)} rows [{times[indices[0]]}, {times[indices[-1]]}]')
    except (ValueError, OSError, StopIteration, IndexError) as error:
        p.exit(1, f'Slice refused: {error}\n')


if __name__ == '__main__':
    main()
