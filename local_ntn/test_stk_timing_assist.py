"""编译并验证实际 UE 时延前馈辅助函数。"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='ntn-timing-test-') as folder:
    executable = Path(folder) / 'test'
    subprocess.run([
        'cc', '-Wall', '-Wextra', '-Werror', '-I',
        str(ROOT / 'oai_patch/current/executables'),
        str(ROOT / 'local_ntn/test_stk_timing_assist.c'),
        '-lm', '-o', str(executable),
    ], check=True)
    subprocess.run([str(executable)], check=True)
