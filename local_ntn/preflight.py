"""只读联调预检查：不生成配置、不启动进程、不修改网络。"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

# Radio constants are invariant; runtime paths are resolved only after CLI selection.
DL_FREQUENCY_HZ = 2488400000
UL_FREQUENCY_HZ = 1614900000
from network_config import addresses


def channel_environments(environment: dict[str, str], *, qd_required: bool = False) -> dict[str, dict[str, str]]:
    """gNB 接收 UL，UE 接收 DL；两个子进程使用独立字典。"""
    dl = environment.get('OAI_QD_DL_CHANNEL', '')
    ul = environment.get('OAI_QD_UL_CHANNEL', '')
    if environment.get('OAI_QD_CHANNEL'):
        raise ValueError('联合启动不能共用 OAI_QD_CHANNEL；请改用 OAI_QD_DL_CHANNEL 和 OAI_QD_UL_CHANNEL')
    if qd_required and not (dl and ul):
        raise ValueError('integrated profile requires both DL and UL bundles')
    if bool(dl) != bool(ul):
        raise ValueError('必须同时指定 OAI_QD_DL_CHANNEL 和 OAI_QD_UL_CHANNEL')
    result = {kind: dict(environment) for kind in ('gnb', 'ue')}
    if dl:
        result['gnb']['OAI_QD_CHANNEL'] = str(Path(ul).expanduser().resolve())
        result['ue']['OAI_QD_CHANNEL'] = str(Path(dl).expanduser().resolve())
    return result


def read_trace(path: Path) -> list[list[float]]:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not lines or lines[0] not in ('STKTRACE2', '# STKTRACE2'):
        raise ValueError('trace 必须是 STKTRACE2')
    rows = [list(map(float, row)) for row in csv.reader(line for line in lines[1:] if not line.startswith('#'))]
    if len(rows) < 2 or any(len(row) != 22 or not all(map(math.isfinite, row)) for row in rows):
        raise ValueError('trace 必须包含至少两行、每行 22 个有限数值')
    if any(a[0] >= b[0] for a, b in zip(rows, rows[1:])):
        raise ValueError('trace 时间必须严格递增')
    if any(value not in (0, 1) for row in rows for value in row[20:22]):
        raise ValueError('trace visibility 必须为 0/1')
    if rows[0][20:22] != [1, 1]:
        raise ValueError('启动历元必须具有上下行覆盖')
    return rows


def check_template(path: Path) -> None:
    text = re.sub(r'#[^\n]*|//[^\n]*', '', path.read_text())
    def number(name):
        values = re.findall(r'\b' + re.escape(name) + r'\s*=\s*(\d+)\s*;', text)
        if len(values) != 1:
            raise ValueError(f'gNB 模板 {name} 必须恰好出现一次')
        return int(values[0])
    for direction, expected in (('dl', DL_FREQUENCY_HZ), ('ul', UL_FREQUENCY_HZ)):
        point = number(direction + '_absoluteFrequencyPointA')
        # 当前启动器限定低于 3 GHz 的 NR-ARFCN 5 kHz 栅格。
        scs = number(direction + '_subcarrierSpacing')
        bandwidth = number(direction + '_carrierBandwidth')
        offset = number(direction + '_offstToCarrier')
        if scs != 0 or bandwidth != 25 or offset != 0 or point >= 600000:
            raise ValueError('启动器仅支持当前 band254 / 25 PRB / 15 kHz / offset=0 模板')
        center = point * 5000 + bandwidth * 12 * 15000 / 2
        if center != expected:
            raise ValueError(f'gNB {direction} 载频 {center} 与启动器 {expected} 不一致')


def check_bundle(bundle: Path, trace: Path, direction: str, frequency: int) -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from quadriga.tools.audit_link_budget import audit_link_budget
    # 先读元数据给出明确诊断，再执行完整哈希/数据/非重复损耗审计。
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['radio']['link_direction'] != direction:
        raise ValueError(f'{direction} bundle 方向错误：{bundle}')
    actual = manifest['radio']['center_frequency_hz']
    if not isinstance(actual, (int, float)) or not math.isfinite(actual) or abs(actual - frequency) > 1:
        raise ValueError(f'{direction} bundle 载频 {actual} != OAI {frequency} Hz；必须重新导出')
    return audit_link_budget(bundle, trace)


HANDOVER_SOURCE_FILES = (
    'quadriga/matlab/export_handover_fdd.m',
    'quadriga/matlab/export_stk_to_qdchannel.m',
    'quadriga/matlab/normalize_qd_channel.m',
    'quadriga/matlab/write_qdchannel1.m',
    'quadriga/matlab/read_stktrace2.m',
    'quadriga/matlab/ecef_to_enu_track.m',
    'quadriga/matlab/sha256_file.m',
)


def check_handover_bundles(dl: Path, ul: Path, trace: Path, schedule: Path) -> dict:
    """Require one complete export, tied to the exact trace and identity schedule."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    dl, ul, trace = (Path(value).resolve() for value in (dl, ul, trace))
    require(schedule is not None, 'handover requires a schedule')
    schedule = Path(schedule).resolve()
    require(dl.parent == ul.parent and dl.name == 'downlink' and ul.name == 'uplink',
            'handover DL and UL must belong to the same export')
    sidecar = dl.parent / 'provenance.json'
    require(sidecar.is_file(), 'handover completion provenance.json is missing')
    metadata = json.loads(sidecar.read_text(encoding='utf-8'))
    require(metadata.get('format') == 'NTN_HANDOVER_FDD1' and metadata.get('schema_version') == 1
            and metadata.get('state') == 'complete', 'handover export is not complete')
    inputs = metadata.get('inputs', {})
    for name, path in (('trace', trace), ('schedule', schedule)):
        require(inputs.get(name, {}).get('sha256') == sha(path), f'handover {name} SHA256 mismatch')
    rows = read_trace(trace)
    times = [row[0] for row in rows]
    with schedule.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        require({'time', 'satellite_id', 'elevation_deg', 'visible', 'switched'} <= set(reader.fieldnames or []),
                'handover schedule missing required columns')
        schedule_rows = list(reader)
    require(len(schedule_rows) == len(rows), 'handover schedule time row count mismatch')
    for expected, row in zip(times, schedule_rows):
        instant = float(row['time'])
        require(math.isfinite(instant) and abs(instant - expected) <= 1e-9,
                'handover schedule time axis mismatch')
        elevation = float(row['elevation_deg'])
        require(row.get('satellite_id') and math.isfinite(elevation) and -90 <= elevation <= 90
                and row['visible'] in ('0', '1') and row['switched'] in ('0', '1'),
                'handover schedule contains an invalid identity or visibility')
        if 'handover_phase' in row:
            require(row['handover_phase'] in ('steady', 'blend', 'complete'),
                    'handover schedule contains an invalid phase')
    for name in ('trace', 'schedule'):
        spec = inputs[name]
        require(spec.get('rows') == len(rows) and spec.get('start_time_s') == times[0]
                and spec.get('end_time_s') == times[-1], f'handover {name} interval metadata mismatch')
    tools = metadata.get('tools', {})
    require(isinstance(tools.get('matlab_version'), str) and bool(tools['matlab_version'])
            and tools.get('quadriga_version') == '2.8.1-0'
            and tools.get('scenario') == 'QuaDRiGa_NTN_Rural_LOS'
            and tools.get('random_seed') == 20260925, 'handover export tool provenance mismatch')
    source = metadata.get('source', {})
    require(isinstance(source.get('commit'), str) and re.fullmatch(r'[0-9a-f]{40}', source['commit']),
            'handover source commit is missing or invalid')
    root = Path(__file__).resolve().parents[1]
    checksums = json.loads((root / 'vendor/checksums.json').read_text(encoding='utf-8'))
    require(source.get('quadriga_archive_sha256') == checksums['quadriga-source.tar.gz'],
            'handover QuaDRiGa archive provenance mismatch')
    source_files = source.get('files', {})
    require(set(source_files) == set(HANDOVER_SOURCE_FILES), 'handover exporter source files missing')
    for name in HANDOVER_SOURCE_FILES:
        require(source_files[name] == sha(root / name), f'handover exporter source SHA256 mismatch: {name}')
    recorded_bundles = metadata.get('bundles', {})
    require(set(recorded_bundles) == {'downlink', 'uplink'}, 'handover completion requires both directions')
    audits = {}
    for direction, bundle, frequency in (('downlink', dl, DL_FREQUENCY_HZ), ('uplink', ul, UL_FREQUENCY_HZ)):
        record = recorded_bundles[direction]
        require(record.get('path') == direction, 'handover bundle path is not its standard direction')
        manifest_path = bundle / 'manifest.json'
        require(record.get('manifest_sha256') == sha(manifest_path),
                f'handover {direction} manifest SHA256 mismatch')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        recorded_data = record.get('data_sha256', {})
        require(set(recorded_data) == set(manifest['files']), 'handover bundle data SHA256 fields mismatch')
        for name, spec in manifest['files'].items():
            require(recorded_data[name] == spec['sha256'], f'handover {direction} data SHA256 mismatch')
        provenance = manifest['provenance']
        require(provenance.get('quadriga_version') == tools['quadriga_version']
                and provenance.get('scenario') == tools['scenario']
                and provenance.get('random_seed') == tools['random_seed'],
                f'handover {direction} tool provenance differs from completion record')
        audits[direction] = check_bundle(bundle, trace, direction, frequency)
    return {'path': str(sidecar), 'trace_sha256': inputs['trace']['sha256'],
            'schedule_sha256': inputs['schedule']['sha256'], 'audits': audits}

def preflight(rate: float, environment: dict[str, str] | None = None, runtime=None) -> dict:
    env = dict(os.environ if environment is None else environment)
    if not math.isfinite(rate) or not 0 <= rate <= 1:
        raise ValueError('rate 必须在 [0,1] 内')
    if runtime is None:
        from paths import OAI_REPO, BUILD_DIR, UE_CONFIG, STK_TRACE
        qd_required = False  # Preserve direct zky calls with optional QD.
    else:
        OAI_REPO, BUILD_DIR, UE_CONFIG, STK_TRACE = runtime.oai_repo, runtime.build_dir, runtime.ue_config, runtime.trace
        original=dict(env)
        env.update(runtime.to_env())
        if runtime.profile == 'zky':
            for key in ('OAI_QD_DL_CHANNEL','OAI_QD_UL_CHANNEL'):
                if not original.get(key):env.pop(key,None)
        qd_required = runtime.profile == 'integrated-handover'
        if runtime.profile == 'legacy-handover':
            for key in ('OAI_QD_CHANNEL','OAI_QD_DL_CHANNEL','OAI_QD_UL_CHANNEL'):
                env.pop(key, None)
    children = channel_environments(env, qd_required=qd_required)
    amf_ip, gnb_ip_cidr = addresses(env)
    required = [STK_TRACE, UE_CONFIG] + [BUILD_DIR / name for name in ('nr-softmodem', 'nr-uesoftmodem', 'librfsimulator.so', 'libparams_libconfig.so', 'libldpc.so', 'libdfts.so')]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError('缺少运行文件：\n  ' + '\n  '.join(missing))
    for name in ('nr-softmodem', 'nr-uesoftmodem'):
        if not os.access(BUILD_DIR / name, os.X_OK):
            raise ValueError(f'二进制不可执行：{BUILD_DIR / name}')
    rows = read_trace(STK_TRACE)
    if env.get('OAI_STK_TRACE_EPOCH') and float(env['OAI_STK_TRACE_EPOCH']) != rows[0][0]:
        raise ValueError('当前启动器从 trace 首行生成 TA/SIB19，不支持其他 OAI_STK_TRACE_EPOCH')
    check_template(OAI_REPO / 'ci-scripts/conf_files/gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf')
    # 只检查位置，不输出身份、密钥或整个私有配置。
    private = re.sub(r'#[^\n]*', '', UE_CONFIG.read_text())
    position = re.search(r'\bposition0\s*=\s*\{(.*?)\}', private, re.S)
    if position is None:
        raise ValueError('UE 配置缺少 position0')
    xyz = []
    for axis in 'xyz':
        value = re.search(r'\b' + axis + r'\s*=\s*([^;]+);', position[1])
        if value is None:
            raise ValueError('UE position0 坐标不完整')
        xyz.append(float(value[1]))
    if not all(map(math.isfinite, xyz)) or math.dist(xyz, rows[0][13:16]) > 1:
        raise ValueError('UE position0 与所选 trace 首行位置不一致')
    result = {'source_repo': str(OAI_REPO), 'build_dir': str(BUILD_DIR),
              'rfsimulator_library': str(BUILD_DIR / 'librfsimulator.so'),
              'trace': str(STK_TRACE), 'trace_sha256': hashlib.sha256(STK_TRACE.read_bytes()).hexdigest(),
              'rate': rate, 'trace_interval_s': [rows[0][0], rows[-1][0]],
              'dl_frequency_hz': DL_FREQUENCY_HZ, 'ul_frequency_hz': UL_FREQUENCY_HZ,
              'mode': 'STK-only', 'bundles': {}, 'amf_ip': amf_ip, 'gnb_ip_cidr': gnb_ip_cidr}
    if qd_required:
        result['handover_provenance'] = check_handover_bundles(
            runtime.dl_bundle, runtime.ul_bundle, STK_TRACE, runtime.schedule)
    if 'OAI_QD_CHANNEL' in children['gnb']:
        if b'QDCHANNEL1' not in (BUILD_DIR / 'librfsimulator.so').read_bytes():
            raise ValueError('选定 RFsim 库未发现 QDCHANNEL1 支持，请构建正确源码')
        result['mode'] = 'STK+QuaDRiGa'
        for kind, direction, frequency in (('gnb', 'uplink', UL_FREQUENCY_HZ), ('ue', 'downlink', DL_FREQUENCY_HZ)):
            bundle = Path(children[kind]['OAI_QD_CHANNEL'])
            result['bundles'][kind] = {'path': str(bundle), 'audit': check_bundle(bundle, STK_TRACE, direction, frequency)}
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rate', type=float, default=0)
    try:
        print(json.dumps(preflight(parser.parse_args().rate), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, ImportError) as error:
        raise SystemExit(f'Preflight failed: {error}') from None
