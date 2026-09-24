"""Local paths shared by launchers; overrides survive sudo via --preserve-env."""
import os
import pwd
from pathlib import Path

USER_HOME = Path(pwd.getpwnam(os.environ['SUDO_USER']).pw_dir) if os.environ.get('SUDO_USER') else Path.home()
OAI_REPO = Path(os.environ.get('OAI_REPO', USER_HOME / 'OAI/openairinterface5g')).resolve()
UE_CONFIG = Path(os.environ.get('OAI_UE_CONFIG', USER_HOME / '.local/share/oai-stk/ue.local.conf')).resolve()
BASE = Path(__file__).resolve().parent

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=['repo', 'ue'])
    args = parser.parse_args()
    print(OAI_REPO if args.name == 'repo' else UE_CONFIG)
