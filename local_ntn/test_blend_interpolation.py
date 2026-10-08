"""编译实际 STK 插值源文件，对完整示例做 1ms A/B 检查。"""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'oai_patch/current/radio/rfsimulator'
for name in ('stk_trace.h','stk_trace.c'):
    assert (ROOT/'local_ntn'/name).read_text()==(source/name).read_text(), 'local parser copy differs: '+name
with tempfile.TemporaryDirectory(prefix='ntn-blend-test-') as folder:
    executable=Path(folder)/'test'
    subprocess.run(['cc','-Wall','-Wextra','-Werror','-I',str(source),str(ROOT/'local_ntn/test_blend_interpolation.c'),str(source/'stk_trace.c'),'-lm','-o',str(executable)],check=True)
    subprocess.run([str(executable),str(ROOT/'examples/fdd-pass/trace.csv')],check=True)
