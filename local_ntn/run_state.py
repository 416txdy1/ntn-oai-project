"""Bounded shutdown using PID start time and executable identity."""
import json
import os
from pathlib import Path
import signal
import time


def process_identity(pid: int) -> tuple[str, str] | None:
    try:
        # comm may include spaces and parentheses. The final ')' ends field 2.
        stat = Path(f'/proc/{pid}/stat').read_text()
        fields = stat[stat.rindex(')') + 2:].split()
        if fields[0] == 'Z':
            return None
        return fields[19], os.readlink(f'/proc/{pid}/exe')
    except (OSError, ValueError, IndexError):
        return None


def read_state(path, run_id):
    state = json.loads(Path(path).read_text())
    if 'schema' in state:
        if state.get('schema') != 2 or state.get('run_id') != run_id:
            raise ValueError('Process state belongs to another run or schema')
        return state, state['processes']
    if run_id != 'default':
        raise ValueError('Legacy process state has no matching run identity')
    return state, state


def matches(record):
    identity = process_identity(record['pid'])
    if not identity or record.get('start') is None or identity[0] != record['start']:
        return False
    # Old zky state predates executable recording; preserve its starttime guard.
    executable = record.get('executable')
    if executable is None:
        return True
    allowed = {executable}
    if record.get('phase') == 'launching':
        allowed.add(record.get('expected_executable'))
    return identity[1] in allowed


def save_state(path, state):
    path = Path(path)
    # Replace within the same run directory; raw state remains private.
    temporary = path.with_name(path.name + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
    os.replace(temporary, path)


def stop_owned(state_file: Path, run_id: str) -> None:
    if not Path(state_file).exists():
        return
    state, records = read_state(state_file, run_id)
    for sig, timeout in ((signal.SIGTERM, 10), (signal.SIGKILL, 5)):
        for record in records.values():
            if matches(record):
                try:
                    os.killpg(record['pid'], sig)
                except ProcessLookupError:
                    pass
        deadline = time.monotonic() + timeout
        while any(matches(record) for record in records.values()) and time.monotonic() < deadline:
            time.sleep(.1)
        if not any(matches(record) for record in records.values()):
            for record in records.values():
                current=process_identity(record['pid'])
                if current and current[0]==record.get('start'):
                    raise RuntimeError('Owned PID executable changed; state retained for inspection')
            if 'schema' in state:
                state['stopped_processes'] = records
                state['processes'] = {}
                state['status'] = 'stopped'
            else:
                state = {}
            save_state(state_file, state)
            return
    raise RuntimeError('Owned modem shutdown timed out; state retained for inspection')
