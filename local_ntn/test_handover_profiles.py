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
