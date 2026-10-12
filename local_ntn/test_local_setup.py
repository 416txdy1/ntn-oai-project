"""Regression checks in temporary directories; no modem, database or real SIM writes."""
import contextlib
import csv
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from paths import OAI_REPO

BASE = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='ntn-local-setup-') as directory:
    work = Path(directory)
    for name in ('prepare_local.py', 'paths.py', 'network_config.py', 'runtime_config.py'):
        shutil.copy2(BASE / name, work / name)
    private = work / 'identity.conf'
    private.write_text('imsi = "001010000000001"; nssai_sst = 1; dnn = "oai";\n'
                       'position0 = { x = 6377900; y = 0; z = 0; };\n')
    env = dict(os.environ, OAI_REPO=str(OAI_REPO), OAI_UE_CONFIG=str(private),
               OAI_AMF_IP='192.168.70.132', OAI_GNB_IP_CIDR='192.168.70.129/26')
    env['OAI_STK_TRACE'] = str(work / 'stk_trace.csv')  # 测试只使用临时输入。
    template = OAI_REPO / 'ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf'
    original = template.read_bytes()
    def run(rate):
        return subprocess.run([sys.executable, str(work/'prepare_local.py'), '--rate', str(rate)],
                              env=env, text=True, capture_output=True)
    assert run(0).returncode != 0
    row = [0, 7000000, 0, 0, 100, 0, 0, 0, 0, 0, 6377900, 0, 0, 6377900, 0, 0, -100, -100, 20, 20, 1, 1]
    with (work/'stk_trace.csv').open('w', newline='') as stream:
        stream.write('STKTRACE2\n')
        writer = csv.writer(stream)
        writer.writerow(row)
        writer.writerow([1, *row[1:]])
    private.write_text('imsi = "001010000000001"; nssai_sst = 1; dnn = "oai";\n'
                       'position0 = { x = 0; y = 0; z = 6377900; };\n')
    mismatch=run(0)
    assert mismatch.returncode != 0 and 'position0 differs' in mismatch.stderr
    private.write_text('imsi = "001010000000001"; nssai_sst = 1; dnn = "oai";\n'
                       'position0 = { x = 6377900; y = 0; z = 0; };\n')
    for rate, expected_velocity in [(0, 0), (1, 1667)]:
        result = run(rate)
        assert result.returncode == 0, result.stderr
        conf = (work/'gnb.local.conf').read_text()
        assert re.search(r'mcc\s*=\s*1;', conf)
        assert re.search(r'mnc\s*=\s*1;', conf)
        assert 'sd = 0xffffff' in conf
        assert re.search(r'amf_ip_address\s*=\s*\(\s*\{\s*ipv4\s*=\s*\"192.168.70.132\"', conf)
        for field in ('GNB_IPV4_ADDRESS_FOR_NG_AMF', 'GNB_IPV4_ADDRESS_FOR_NGU'):
            assert re.search(field + r'\s*=\s*\"192.168.70.129/26\"', conf)
        assert re.search(r'velocityVX-r17\s*=\s*'+str(expected_velocity)+r';', conf)
    for rate in ('nan', '-0.1', '1.1'):
        assert run(rate).returncode != 0
    private.write_text('imsi = "208950000009901"; nssai_sst = 1; nssai_sd = 1;\n'
                       'position0 = { x = 6377900; y = 0; z = 0; };\n')
    assert run(0).returncode == 0
    conf = (work/'gnb.local.conf').read_text()
    assert 'mcc = 208' in conf and 'mnc = 95' in conf and 'sd = 0x000001' in conf
    assert template.read_bytes() == original, 'Original gNB template changed'
    print('PASS: config generation, UE position guard, static/dynamic velocity, both lab PLMNs, missing trace and invalid rates; template unchanged')

    # 默认文件不存在时，显式 trace 仍须同时用于配置生成和启动。
    selected = work / 'selected trace.csv'
    (work / 'stk_trace.csv').rename(selected)
    env['OAI_STK_TRACE'] = str(selected)
    assert run(0).returncode == 0
    selected.write_text(selected.read_text().replace('STKTRACE2', '# STKTRACE2', 1))
    assert run(0).returncode == 0
    print('PASS: explicit trace override and comment magic with missing default trace')
    # Exercise the validator's exit status without starting processes or real traffic.
    source = (BASE/'validate_dynamic.py').read_text()
    def fake_run(command, **kwargs):
        if command[0] == 'ip':
            return subprocess.CompletedProcess(command, 0, 'inet 10.0.0.2/24')
        return subprocess.CompletedProcess(command, 1 if 'ping' in command else 0)
    with patch.object(sys, 'argv', ['validate_dynamic.py', '--tag', 'fixture']), \
         patch('subprocess.run', side_effect=fake_run), patch('time.sleep'), \
         contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(compile(source, str(BASE/'validate_dynamic.py'), 'exec'),
                 {'__file__': str(work/'validate_dynamic.py'), '__name__': '__main__'})
        except SystemExit as exc:
            assert str(exc) == 'Dynamic validation failed: ping', str(exc)
        else:
            raise AssertionError('A failed ping was incorrectly accepted')
    print('PASS: dynamic validator returns failure when ping fails')
