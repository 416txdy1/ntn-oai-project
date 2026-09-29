"""Create a deterministic trace/schedule slice without changing source exports."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trace", type=Path, required=True)
    p.add_argument("--schedule", type=Path, required=True)
    p.add_argument("--start", type=float, required=True)
    p.add_argument("--stop", type=float, required=True)
    p.add_argument("--trace-out", type=Path, required=True)
    p.add_argument("--schedule-out", type=Path, required=True)
    a = p.parse_args()
    if a.stop <= a.start:
        p.error("stop must be greater than start")

    trace_lines = a.trace.read_text(encoding="ascii").splitlines()
    if not trace_lines or trace_lines[0] != "STKTRACE2":
        raise SystemExit("trace must start with STKTRACE2")
    selected_trace = []
    for line in trace_lines[2:]:
        if not line or line.startswith("#"):
            continue
        value = float(line.split(",", 1)[0])
        if a.start <= value <= a.stop:
            selected_trace.append(line)
    if len(selected_trace) < 2:
        raise SystemExit("trace slice contains fewer than two samples")

    schedule_rows = []
    with a.schedule.open(newline="", encoding="ascii") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row and a.start <= float(row[0]) <= a.stop:
                schedule_rows.append(row)
    if len(schedule_rows) != len(selected_trace):
        raise SystemExit(
            f"trace/schedule row count mismatch: {len(selected_trace)} vs {len(schedule_rows)}"
        )

    a.trace_out.parent.mkdir(parents=True, exist_ok=True)
    a.trace_out.write_text(
        "STKTRACE2\n" + trace_lines[1] + "\n" + "\n".join(selected_trace) + "\n",
        encoding="ascii",
    )
    a.schedule_out.parent.mkdir(parents=True, exist_ok=True)
    with a.schedule_out.open("w", newline="", encoding="ascii") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(schedule_rows)
    print(
        f"wrote {len(selected_trace)} rows [{selected_trace[0].split(',')[0]}, "
        f"{selected_trace[-1].split(',')[0]}]"
    )


if __name__ == "__main__":
    main()
