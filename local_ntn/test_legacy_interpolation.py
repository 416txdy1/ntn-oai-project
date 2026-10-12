"""Compile the actual current parser and verify local mirror equality."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'oai_patch/current/radio/rfsimulator'
for name in ('stk_trace.h', 'stk_trace.c'):
    assert (ROOT / 'local_ntn' / name).read_bytes() == (source / name).read_bytes(), name + ' mirror differs'
with tempfile.TemporaryDirectory(prefix='ntn-legacy-test-') as directory:
    executable = Path(directory) / 'legacy'
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-I', str(source), str(ROOT / 'local_ntn/test_legacy_interpolation.c'), str(source / 'stk_trace.c'), '-lm', '-o', str(executable)], check=True)
    subprocess.run([str(executable), str(ROOT / 'examples/fdd-pass/trace.csv')], check=True)
