"""Behavioral checks for isolated pseudo-handover wrappers and paired slices."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'local_ntn'


def clean_env():
    return {k: v for k, v in os.environ.items() if not k.startswith('OAI_')}


@pytest.mark.parametrize('wrapper', ['run_constellation_validation.sh', 'run_seamless_validation.sh'])
@pytest.mark.parametrize('profile', ['integrated-handover', 'legacy-handover'])
def test_wrappers_use_selected_profile(wrapper, profile):
    result = subprocess.run(['bash', str(BASE / wrapper), '--profile', profile,
                             '--run-id', 'wrapper-test', '--dry-run'],
                            env=clean_env(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan['profile'] == profile and plan['run_id'] == 'wrapper-test'
    assert plan['namespace'] == 'ntn-qd-ue'
    assert plan['run_dir'] == str(ROOT / '.runtime/runs' / profile / 'wrapper-test')
    assert plan['trace']['rows'] == 621
    assert plan['trace']['start'] == 8200 and plan['trace']['stop'] == 8820
    assert plan['schedule']['complete_stk_s'] == [8244, 8799]
    assert plan['commands']['core'][1] == str(ROOT / 'scripts/core_lab.py')
    for name in ('core', 'start', 'stop', 'ping', 'uplink', 'downlink'):
        cmd = plan['commands'][name]
        assert cmd[cmd.index('--profile') + 1] == profile
        assert cmd[cmd.index('--run-id') + 1] == 'wrapper-test'
    assert plan['commands']['namespace_probe'][2] == 'ntn-qd-ue'
    assert all(Path(log).is_relative_to(Path(plan['run_dir'])) for log in plan['logs'].values())
    assert plan['environment']['OAI_STK_TRACE_INTERPOLATION'] == 'legacy-linear'
    assert plan['environment']['OAI_STK_BLEND_TIMING_ASSIST'] == '0'
    assert (plan['environment']['OAI_QD_REQUIRED'] == '1') == (profile == 'integrated-handover')


def test_no_original_core_start():
    for name in ('run_constellation_validation.sh', 'run_seamless_validation.sh', 'test_seamless.py'):
        text = (BASE / name).read_text()
        assert '/home/kayoko/oai-cn5g-fed' not in text
        assert 'sudo -v' not in text
        assert 'oai-stk-ue' not in text


def slice_command(tmp_path, start, stop, schedule=None):
    return [sys.executable, str(BASE / 'slice_trace.py'), '--trace', str(BASE / 'stk_trace_seamless.csv'),
            '--schedule', str(schedule or BASE / 'satellite_schedule_seamless.csv'),
            '--start', str(start), '--stop', str(stop),
            '--trace-out', str(tmp_path / 'trace.csv'), '--schedule-out', str(tmp_path / 'schedule.csv')]


def test_slice_preserves_common_absolute_interval(tmp_path):
    result = subprocess.run(slice_command(tmp_path, 8200, 8270), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    times = [float(line.split(',')[0]) for line in (tmp_path / 'trace.csv').read_text().splitlines()[2:]]
    with (tmp_path / 'schedule.csv').open() as stream:
        schedule_times = [float(row['time']) for row in csv.DictReader(stream)]
    assert times == schedule_times == list(range(8200, 8271))


@pytest.mark.parametrize('start,stop', [(8199, 8270), (8200, 8821), (float('nan'), 8820)])
def test_slice_rejects_out_of_bounds(tmp_path, start, stop):
    result = subprocess.run(slice_command(tmp_path, start, stop), capture_output=True, text=True)
    assert result.returncode != 0
    assert not (tmp_path / 'trace.csv').exists() and not (tmp_path / 'schedule.csv').exists()


def test_slice_rejects_equal_count_different_timestamps(tmp_path):
    schedule = tmp_path / 'bad.csv'
    lines = (BASE / 'satellite_schedule_seamless.csv').read_text().splitlines()
    lines[2] = '8201.5,' + lines[2].split(',', 1)[1]
    schedule.write_text('\n'.join(lines) + '\n')
    result = subprocess.run(slice_command(tmp_path, 8200, 8270, schedule), capture_output=True, text=True)
    assert result.returncode != 0
    assert not (tmp_path / 'trace.csv').exists()


def test_slice_refuses_source_overwrite(tmp_path):
    trace = tmp_path / 'source.csv'
    trace.write_bytes((BASE / 'stk_trace_seamless.csv').read_bytes())
    original = trace.read_bytes()
    cmd = slice_command(tmp_path, 8200, 8270)
    cmd[cmd.index('--trace') + 1] = str(trace)
    cmd[cmd.index('--trace-out') + 1] = str(trace)
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert trace.read_bytes() == original


def helper(monkeypatch):
    monkeypatch.syspath_prepend(str(BASE))
    import handover_profiles
    return handover_profiles


def local_plan(tmp_path, monkeypatch):
    from dataclasses import replace
    module = helper(monkeypatch)
    config = module.resolve_runtime(ROOT, 'legacy-handover', 'test-runtime', {})
    config = replace(config, run_dir=tmp_path / 'run')
    return module, config, module.build_plan(config, 'mock', 7, 1, 0)


def test_unprivileged_wrapper_refuses_before_system_operation(tmp_path, monkeypatch):
    module, config, plan = local_plan(tmp_path, monkeypatch)
    monkeypatch.setattr(module.os, 'geteuid', lambda: 1000)
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **k: pytest.fail('must not execute'))
    with pytest.raises(ValueError, match='sudo -E python3'):
        module.execute_plan(config, plan, 7, {})
    assert not config.run_dir.exists()


def test_failed_start_does_not_stop_an_existing_run(tmp_path, monkeypatch):
    module, config, plan = local_plan(tmp_path, monkeypatch)
    monkeypatch.setattr(module.os, 'geteuid', lambda: 0)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        if command == plan['commands']['start']:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(module.subprocess, 'run', run)
    with pytest.raises(subprocess.CalledProcessError):
        module.execute_plan(config, plan, 7, {})
    assert calls == [plan['commands']['core'], plan['commands']['start']]
    for path in plan['logs'].values():
        assert Path(path).stat().st_mode & 0o777 == 0o600


def test_probe_failure_cleans_owned_probes_and_modems(tmp_path, monkeypatch):
    module, config, plan = local_plan(tmp_path, monkeypatch)
    monkeypatch.setattr(module.os, 'geteuid', lambda: 0)
    calls, signals = [], []
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='inet 12.2.1.2')
    monkeypatch.setattr(module.subprocess, 'run', run)
    monkeypatch.setattr(module, 'process_identity', lambda pid: ('123', '/usr/bin/python3'))
    children = []
    class Process:
        def __init__(self, command, **kwargs):
            assert kwargs['start_new_session'] is True
            assert kwargs['env']['OAI_NTN_NAMESPACE'] == 'ntn-qd-ue'
            self.command, self.pid, self.done = command, 100 + len(children), False
            children.append(self)
        def poll(self):
            return 0 if self.done else None
        def wait(self, timeout):
            if self.command == plan['commands']['uplink'] and not self.done:
                raise subprocess.TimeoutExpired(self.command, timeout)
            self.done = True
            return 0
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    def killpg(pid, sig):
        signals.append((pid, sig))
        next(p for p in children if p.pid == pid).done = True
    monkeypatch.setattr(module.os, 'killpg', killpg)
    with pytest.raises(subprocess.TimeoutExpired):
        module.execute_plan(config, plan, 7, {})
    assert calls[-1] == plan['commands']['stop']
    assert [pid for pid, _ in signals] == [100, 101]
    assert all(p.done for p in children)


def test_reused_probe_pid_is_never_signalled(tmp_path, monkeypatch):
    module = helper(monkeypatch)
    monkeypatch.setattr(module, 'process_identity', lambda pid: ('456', '/unrelated'))
    monkeypatch.setattr(module.os, 'killpg', lambda *a: pytest.fail('reused PID must not be signalled'))
    class Process:
        pid = 321
        def poll(self): return None
        def wait(self, timeout): raise subprocess.TimeoutExpired('foreign', timeout)
    with pytest.raises(RuntimeError, match='shutdown timed out'):
        module.stop_probe(Process(), ('123', '/usr/bin/python3'))


def test_inherited_original_environment_is_rejected_without_writes(tmp_path):
    env = clean_env()
    env['OAI_NTN_RUN_DIR'] = str(tmp_path / 'foreign')
    result = subprocess.run(['bash', str(BASE / 'run_seamless_validation.sh'),
                             '--profile', 'integrated-handover', '--run-id', 'contaminated', '--dry-run'],
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert not (tmp_path / 'foreign').exists()


@pytest.mark.parametrize('name', ['satellite_schedule.csv', 'satellite_schedule_firsthandover.csv',
                                  'satellite_schedule_seamless.csv', 'stk_trace_firsthandover.csv',
                                  'stk_trace_seamless.csv'])
def test_restored_input_bytes_match_frozen_source(name):
    source = subprocess.check_output(['git', '-C', str(ROOT), 'show', 'f30bc90:local_ntn/' + name])
    assert (BASE / name).read_bytes() == source
