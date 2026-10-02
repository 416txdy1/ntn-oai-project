"""启动器共享配置；sudo 时通过 --preserve-env 显式保留项目配置。"""
import os
import pwd
from pathlib import Path

USER_HOME = Path(pwd.getpwnam(os.environ['SUDO_USER']).pw_dir) if os.environ.get('SUDO_USER') else Path.home()
BASE = Path(__file__).resolve().parent
OAI_REPO = Path(os.environ.get('OAI_REPO', BASE.parent / '.runtime/oai')).expanduser().resolve()
BUILD_DIR = Path(os.environ.get('OAI_BUILD_DIR', OAI_REPO / 'cmake_targets/ran_build/build')).expanduser().resolve()
UE_CONFIG = Path(os.environ.get('OAI_UE_CONFIG', USER_HOME / '.local/share/oai-stk/ue.local.conf')).expanduser().resolve()
STK_TRACE = Path(os.environ.get('OAI_STK_TRACE', BASE.parent / 'examples/fdd-pass/trace.csv')).expanduser().resolve()
# 本启动器支持的 band 254、25 PRB、15 kHz SCS 配置；预检查核对 gNB 模板。
DL_FREQUENCY_HZ = 2488400000
UL_FREQUENCY_HZ = 1614900000

if __name__ == '__main__':
    import argparse
    values = {'repo': OAI_REPO, 'build': BUILD_DIR, 'ue': UE_CONFIG, 'trace': STK_TRACE,
              'dl-frequency': DL_FREQUENCY_HZ, 'ul-offset': UL_FREQUENCY_HZ - DL_FREQUENCY_HZ}
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=values)
    print(values[parser.parse_args().name])
