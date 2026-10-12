"""Resolve non-secret runtime settings without touching modems or input files."""
import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import shlex
from typing import Mapping, Optional


@dataclass(frozen=True)
class RuntimeConfig:
    root: Path
    oai_repo: Path
    build_dir: Path
    private_dir: Path
    run_dir: Path
    state_file: Path
    gnb_config: Path
    initial_delay_file: Path
    ue_config: Path
    trace: Path
    schedule: Optional[Path]
    dl_bundle: Optional[Path]
    ul_bundle: Optional[Path]
    profile: str
    run_id: str
    namespace: str
    host_veth: str
    ue_veth: str
    rf_host_ip: str
    rf_ue_ip: str
    core_project: str
    ext_dn_container: str
    amf_ip: str
    gnb_ip_cidr: str
    ext_dn_ip: str
    ue_pdu_subnet: str
    interpolation: str
    rf_port: int
    owner_file: Path
    qd_required: bool
    timing_assist: bool

    def to_env(self) -> dict[str, str]:
        names = {
            'OAI_REPO': self.oai_repo, 'OAI_BUILD_DIR': self.build_dir,
            'OAI_BUILD_REPO': self.oai_repo, 'OAI_UE_CONFIG': self.ue_config,
            'OAI_STK_TRACE': self.trace, 'OAI_STK_SCHEDULE': self.schedule,
            'OAI_QD_DL_CHANNEL': self.dl_bundle, 'OAI_QD_UL_CHANNEL': self.ul_bundle,
            'OAI_NTN_PROFILE': self.profile, 'OAI_NTN_RUN_ID': self.run_id,
            'OAI_NTN_PRIVATE_DIR': self.private_dir, 'OAI_NTN_RUN_DIR': self.run_dir,
            'OAI_NTN_STATE_FILE': self.state_file, 'OAI_GNB_CONFIG': self.gnb_config,
            'OAI_INITIAL_DELAY_FILE': self.initial_delay_file,
            'OAI_NTN_NAMESPACE': self.namespace, 'OAI_NTN_HOST_VETH': self.host_veth,
            'OAI_NTN_UE_VETH': self.ue_veth, 'OAI_RF_HOST_IP': self.rf_host_ip,
            'OAI_RF_UE_IP': self.rf_ue_ip, 'OAI_RF_PORT': self.rf_port,
            'OAI_CORE_PROJECT': self.core_project, 'OAI_EXT_DN_CONTAINER': self.ext_dn_container,
            'OAI_AMF_IP': self.amf_ip, 'OAI_GNB_IP_CIDR': self.gnb_ip_cidr,
            'OAI_EXT_DN_IP': self.ext_dn_ip, 'OAI_UE_PDU_SUBNET': self.ue_pdu_subnet,
            'OAI_STK_TRACE_INTERPOLATION': self.interpolation,
            'OAI_STK_BLEND_TIMING_ASSIST': int(self.timing_assist),
            'OAI_NTN_OWNER_FILE': self.owner_file, 'OAI_QD_REQUIRED': int(self.qd_required),
            'OAI_IPERF3_BIN': self.root / '.runtime/iperf3/iperf3',
            'OAI_IPERF3_LIBRARY_PATH': self.root / '.runtime/iperf3/lib',
        }
        return {key: '' if value is None else str(value) for key, value in names.items()}


def _user_home(environ):
    if environ.get('SUDO_USER'):
        import pwd
        return Path(pwd.getpwnam(environ['SUDO_USER']).pw_dir)
    return Path.home()


def resolve_runtime(root: Path, profile: str, run_id: str,
                    environ: Mapping[str, str]) -> RuntimeConfig:
    root = Path(root).expanduser().resolve()
    profile = profile or environ.get('OAI_NTN_PROFILE') or 'zky'
    run_id = run_id or environ.get('OAI_NTN_RUN_ID') or 'default'
    if profile not in ('zky', 'integrated-handover', 'legacy-handover'):
        raise ValueError(f'Unknown NTN profile: {profile}')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', run_id):
        raise ValueError('Invalid run_id: use 1 to 64 letters, digits, underscores or hyphens, starting with a letter or digit')
    isolated = profile != 'zky'

    def path(key, default, scope=None):
        value = Path(environ.get(key) or default).expanduser().resolve()
        if isolated and not value.is_relative_to(Path(scope or root)):
            raise ValueError(f'{key} escapes the isolated runtime scope')
        # The scope itself must not escape via an existing symlink.
        if isolated and not value.is_relative_to(root):
            raise ValueError(f'{key} escapes the independent root')
        return value

    private_default = root / ('.private/profiles/integrated-handover' if isolated else '.private')
    private = path('OAI_NTN_PRIVATE_DIR', private_default, private_default)
    run_default = root / '.runtime/runs' / profile / run_id if isolated else root / 'local_ntn'
    run = path('OAI_NTN_RUN_DIR', run_default, run_default)
    repo = path('OAI_REPO', root / '.runtime/oai', root / '.runtime')
    build = path('OAI_BUILD_DIR', repo / 'cmake_targets/ran_build/build', root / '.runtime')
    if isolated:
        path('OAI_BUILD_REPO', repo, root / '.runtime')
    ue = path('OAI_UE_CONFIG', private / 'ue.conf' if isolated else _user_home(environ) / '.local/share/oai-stk/ue.local.conf', private)
    trace_default = root / ('local_ntn/stk_trace_seamless.csv' if isolated else 'examples/fdd-pass/trace.csv')
    trace = path('OAI_STK_TRACE', trace_default)
    if isolated and trace.is_relative_to((root / 'examples/fdd-pass').resolve()):
        raise ValueError('OAI_STK_TRACE reuses the original profile inputs')
    schedule = path('OAI_STK_SCHEDULE', root / 'local_ntn/satellite_schedule_seamless.csv') if isolated else (path('OAI_STK_SCHEDULE', environ['OAI_STK_SCHEDULE']) if environ.get('OAI_STK_SCHEDULE') else None)
    bundle_root = root / ('examples/handover' if isolated else 'examples/fdd-pass')
    dl = path('OAI_QD_DL_CHANNEL', bundle_root / 'downlink', bundle_root)
    ul = path('OAI_QD_UL_CHANNEL', bundle_root / 'uplink', bundle_root)
    qd_required = profile != 'legacy-handover'
    if not qd_required:
        dl = ul = None

    defaults = {
        'namespace': ('OAI_NTN_NAMESPACE', 'ntn-qd-ue' if isolated else 'oai-stk-ue'),
        'host_veth': ('OAI_NTN_HOST_VETH', 'ntn-qd-host' if isolated else 'oai-stk-host'),
        'ue_veth': ('OAI_NTN_UE_VETH', 'ntn-qd-peer' if isolated else 'oai-stk-peer'),
        'rf_host_ip': ('OAI_RF_HOST_IP', '10.202.0.1' if isolated else '10.201.0.1'),
        'rf_ue_ip': ('OAI_RF_UE_IP', '10.202.0.2' if isolated else '10.201.0.2'),
        'core_project': ('OAI_CORE_PROJECT', 'ntn-qd-integrated' if isolated else 'oai'),
        'ext_dn_container': ('OAI_EXT_DN_CONTAINER', 'ntn-qd-integrated-oai-ext-dn' if isolated else 'oai-ext-dn'),
        'amf_ip': ('OAI_AMF_IP', '192.168.71.132' if isolated else '192.168.70.132'),
        'gnb_ip_cidr': ('OAI_GNB_IP_CIDR', '192.168.71.129/26' if isolated else '192.168.70.129/26'),
        'ext_dn_ip': ('OAI_EXT_DN_IP', '192.168.71.135' if isolated else '192.168.70.135'),
        'ue_pdu_subnet': ('OAI_UE_PDU_SUBNET', '12.2.1.0/24' if isolated else '12.1.1.0/24'),
        'interpolation': ('OAI_STK_TRACE_INTERPOLATION', 'legacy-linear' if isolated else 'hermite'),
    }
    settings_path = private / 'settings.json'
    if isolated and not settings_path.resolve().is_relative_to(private):
        raise ValueError('Private settings escape isolated private directory')
    settings = json.loads(settings_path.read_text()) if settings_path.is_file() else {}
    if not isinstance(settings, dict):
        raise ValueError('Private settings must be a JSON object')
    values = {}
    for field, (key, default) in defaults.items():
        value = environ.get(key) or default
        if isolated and value != default:
            raise ValueError(f'{key} conflicts with isolated profile resources')
        settings_key = 'compose_project' if field == 'core_project' else field
        if settings_key in settings:
            if isolated and str(settings[settings_key]) != default:
                raise ValueError(f'Private settings contain a conflicting {settings_key}')
            # Legacy shell settings previously override its exported network defaults.
            value = str(settings[settings_key])
        if isolated and value != default:
            raise ValueError(f'{key} conflicts with isolated profile resources')
        values[field] = value
    try:
        rf_port = int(environ.get('OAI_RF_PORT') or (4044 if isolated else 4043))
    except ValueError:
        raise ValueError('OAI_RF_PORT must be an integer') from None
    if not 1 <= rf_port <= 65535 or isolated and rf_port != 4044:
        raise ValueError('OAI_RF_PORT conflicts with the profile port')
    owner_default = Path('/run/ntn-qd-ue.owner.json' if isolated else '/run/oai-stk-ue.owner.json')
    owner = Path(environ.get('OAI_NTN_OWNER_FILE') or owner_default).expanduser().resolve()
    if isolated and owner != owner_default:
        raise ValueError('OAI_NTN_OWNER_FILE conflicts with isolated ownership')
    timing_value = environ.get('OAI_STK_BLEND_TIMING_ASSIST', '0')
    if timing_value not in ('0', '1') or isolated and timing_value != '0':
        raise ValueError('OAI_STK_BLEND_TIMING_ASSIST must be 0 for isolated profiles')
    if isolated and environ.get('OAI_QD_CHANNEL'):
        raise ValueError('Use separate isolated DL/UL bundles, not OAI_QD_CHANNEL')
    return RuntimeConfig(
        root=root, oai_repo=repo, build_dir=build, private_dir=private, run_dir=run,
        state_file=path('OAI_NTN_STATE_FILE', run / 'processes.json', run),
        gnb_config=path('OAI_GNB_CONFIG', run / 'gnb.local.conf', run),
        initial_delay_file=path('OAI_INITIAL_DELAY_FILE', run / 'initial_delay_ms.txt', run),
        ue_config=ue, trace=trace, schedule=schedule, dl_bundle=dl, ul_bundle=ul,
        profile=profile, run_id=run_id, rf_port=rf_port, owner_file=owner,
        qd_required=qd_required, timing_assist=timing_value == '1', **values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='')
    parser.add_argument('--run-id', default='')
    parser.add_argument('--format', choices=('json', 'env'), default='json')
    args = parser.parse_args()
    try:
        config = resolve_runtime(Path(__file__).resolve().parents[1], args.profile, args.run_id, os.environ)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Runtime configuration failed: {error}\n')
    if args.format == 'json':
        print(json.dumps(asdict(config), default=str, indent=2))
    else:
        for key, value in config.to_env().items():
            print(f'export {key}={shlex.quote(value)}')


if __name__ == '__main__':
    main()
