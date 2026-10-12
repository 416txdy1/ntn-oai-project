"""Shared runtime configuration; preserve project settings explicitly with sudo."""
import os
from pathlib import Path
from runtime_config import resolve_runtime

BASE = Path(__file__).resolve().parent
RUNTIME = resolve_runtime(BASE.parent, '', '', os.environ)
OAI_REPO = RUNTIME.oai_repo
BUILD_DIR = RUNTIME.build_dir
UE_CONFIG = RUNTIME.ue_config
STK_TRACE = RUNTIME.trace
DL_FREQUENCY_HZ = 2488400000
UL_FREQUENCY_HZ = 1614900000

if __name__ == '__main__':
    import argparse
    values = {'repo': OAI_REPO, 'build': BUILD_DIR, 'ue': UE_CONFIG, 'trace': STK_TRACE,
              'dl-frequency': DL_FREQUENCY_HZ, 'ul-offset': UL_FREQUENCY_HZ - DL_FREQUENCY_HZ}
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=values)
    print(values[parser.parse_args().name])
