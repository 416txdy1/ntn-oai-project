"""Legacy --tag/--duration/--rate entry for isolated pseudo handover probes.

Probe exit codes describe compatibility only. Complete IQ interval/window
acceptance is performed by the dedicated handover acceptance driver.
"""
import subprocess
import sys
from pathlib import Path
from handover_profiles import main

BASE = Path(__file__).resolve().parent


def experiment(*args: str, **kwargs):
    """Retain the original helper API; CLI profile/run selection is passed in args."""
    return subprocess.run([sys.executable, str(BASE / 'experiment.py'), *args], **kwargs)


if __name__ == '__main__':
    sys.exit(main())
