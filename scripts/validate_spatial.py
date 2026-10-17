"""在一个持续会话内完成空间链路静态/动态业务与数值验收。"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from audit_spatial_run import audit_run


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ports',type=int,choices=(2,4),required=True)
    args=parser.parse_args()
    if os.geteuid()!=0:
        parser.error('请在已 source 对应环境的 root shell 运行')
    if os.environ.get('OAI_SPATIAL_MODE') not in ({'miso4', 'miso4-subarray'} if args.ports == 4 else {'miso2'}):
        parser.error('端口数量与已加载的空间模式不匹配')
    # 验算器使用原始 Hermite/STK 基线，拒绝未经记录的实验修正。
    for name, default in (('OAI_STK_TRACE_INTERPOLATION','hermite'), ('OAI_STK_BLEND_TIMING_ASSIST','0')):
        if os.environ.get(name,default) != default:
            parser.error(f'{name} 偏离验收基线')
    for name in ('OAI_STK_TRACE_EPOCH','OAI_STK_TRACE_EXTRA_LOSS_DB','OAI_STK_TRACE_CN_OFFSET_DB','OAI_STK_TRACE_BW_HZ','OAI_STK_TRACE_NOISE'):
        if name in os.environ:
            parser.error(f'验收前请清除 {name}')
    root=Path(__file__).resolve().parents[1]
    for name in ('nr-softmodem','nr-uesoftmodem'):
        if subprocess.run(['pgrep','-x',name],capture_output=True).returncode==0:
            raise SystemExit('已有 modem 运行，拒绝接管或停止')
    settings=json.loads((root/'.private/settings.json').read_text())
    compose=['docker','compose','-p',settings['compose_project'],'-f',str(root/'.private/core/compose.yaml')]
    running=subprocess.check_output([*compose,'ps','--status','running','-q'],text=True).split()
    services=subprocess.check_output([*compose,'config','--services'],text=True).split()
    if running and len(running)!=len(services):
        raise SystemExit('核心网部分运行，拒绝改变已有服务状态')
    own_core=not running
    success=False
    try:
        if own_core:
            subprocess.run(['bash',str(root/'scripts/core.sh'),'up'],check=True)
        for rate in (0,1):
            process=subprocess.run([sys.executable,str(root/'scripts/smoke.py'),'--rate',str(rate)],capture_output=True,text=True)
            # smoke stdout 是去敏结果 JSON；原始 modem 日志保留在 .runtime/local_ntn。
            result=json.loads(process.stdout)
            print(json.dumps(result,indent=2),flush=True)
            report=audit_run(root,result['label'],args.ports,Path(os.environ['OAI_STK_TRACE']))
            (root/'.runtime/reports'/f"{result['label']}-spatial-audit.json").write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2),flush=True)
            if process.returncode or not report['passed']:
                raise RuntimeError('业务或物理公式验算失败')
        success=True
    finally:
        stopped=subprocess.run([sys.executable,str(root/'local_ntn/experiment.py'),'stop'],capture_output=True)
        if stopped.returncode: success=False
        if own_core:
            stopped=subprocess.run(['bash',str(root/'scripts/core.sh'),'stop'])
            if stopped.returncode: success=False
    return 0 if success else 1

if __name__ == '__main__': raise SystemExit(main())
