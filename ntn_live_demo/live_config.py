"""Explicit spatial selection for the separate audiovisual integration runtime."""
from pathlib import Path

DEFAULT_ROOT = Path('/home/kayoko/ntn-workspaces/ntn-live-miso')
SPATIAL_MODES = ('siso', 'miso4-subarray')


def add_runtime_arguments(parser):
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--spatial-mode', choices=SPATIAL_MODES, default='siso')
    parser.add_argument('--qd-workers', type=int, choices=range(1, 9), default=8)


def child_arguments(args):
    return ['--root', str(args.root), '--spatial-mode', args.spatial_mode,
            '--qd-workers', str(args.qd_workers)]


def bundle_root(root, mode):
    if mode not in SPATIAL_MODES:
        raise ValueError('Unsupported live spatial mode')
    return root/'examples'/('handover-miso4' if mode == 'miso4-subarray' else 'handover')


def radio_environment(root, case, mode, workers):
    if case not in ('static', 'firsthandover', 'full') or workers not in range(1, 9):
        raise ValueError('Unsupported case or compute worker count')
    directory = bundle_root(root, mode)
    name = 'firsthandover' if case == 'firsthandover' else 'seamless'
    if case == 'firsthandover':
        directory /= 'firsthandover'
    return {'OAI_SPATIAL_MODE': mode,
            'OAI_QD_WORKERS': str(workers if mode != 'siso' else 1),
            'OAI_STK_TRACE': str(root/'local_ntn'/f'stk_trace_{name}.csv'),
            'OAI_STK_SCHEDULE': str(root/'local_ntn'/f'satellite_schedule_{name}.csv'),
            'OAI_QD_DL_CHANNEL': str(directory/'downlink'),
            'OAI_QD_UL_CHANNEL': str(directory/'uplink')}
