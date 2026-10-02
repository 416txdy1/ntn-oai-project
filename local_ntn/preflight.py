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

from paths import OAI_REPO, BUILD_DIR, UE_CONFIG, STK_TRACE, DL_FREQUENCY_HZ, UL_FREQUENCY_HZ
from network_config import addresses


def channel_environments(environment: dict[str, str]) -> dict[str, dict[str, str]]:
    """gNB 接收 UL，UE 接收 DL；两个子进程使用独立字典。"""
    dl = environment.get('OAI_QD_DL_CHANNEL', '')
    ul = environment.get('OAI_QD_UL_CHANNEL', '')
    if environment.get('OAI_QD_CHANNEL'):
        raise ValueError('联合启动不能共用 OAI_QD_CHANNEL；请改用 OAI_QD_DL_CHANNEL 和 OAI_QD_UL_CHANNEL')
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


def preflight(rate: float, environment: dict[str, str] | None = None) -> dict:
    env = dict(os.environ if environment is None else environment)
    if not math.isfinite(rate) or not 0 <= rate <= 1:
        raise ValueError('rate 必须在 [0,1] 内')
    children = channel_environments(env)
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
