# 新入口验证记录：2026-10-21

新增 `run_ntn_channel_comparison.cmd` → `launch_causal.ps1` → `causal.py`。旧CMD默认行为保持。未执行新的Git提交或推送；不包含用户原片。

## 已执行

- Windows PowerShell解析检查通过；CMD为ASCII/CRLF。
- `python3 -B /mnt/d/实验室学习工作/杂活/雄安/OAI调研/ntn_live_demo/test_causal.py`：9项通过，覆盖无业务变化、本地冻结、源编码停滞、计数重置、覆盖不足不得判SUPPORTED及墙钟速率计算。
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ntn_live_demo\launch_causal.ps1 -PrepareOnly -Repeats 1`：exit=0，suite `causal-20261021-090940-e18de2`。当轮 trace/IQ回归8.5秒、脚本回归81.3秒、Python派生预检查0.5秒，均exit=0。该早期检查未包含后加的原生C检查。
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ntn_live_demo\launch_causal.ps1 -Smoke -Repeats 1`：两轮真实运行，详情如下。

## 保留的首轮失败

Suite `causal-20261021-091356-6234b1`。trace/IQ回归9.0秒、脚本回归82.6秒、派生预检查0.5秒，均exit=0。固定组及正常组完成100 IQ秒并通过原Demo门限。干预组在接入前失败，真实C读取器拒绝manifest新增字段；配对INVALID、suite INCONCLUSIVE，未将其误判为信道效果。

修复方式：保留QDCHANNEL1严格字段集合，只更新trace摘要；派生说明移到独立旁证文件和完成来源记录。未修改C读取器、未放松其检查、未重编译OAI。新增真实C读取器对派生DL/UL的预检查。

## 修复后短时三组联调

Suite `causal-20261021-092620-854fd7`。trace/IQ回归8.0秒、脚本回归80.8秒、派生预检查0.5秒、原生C的DL/UL检查各0.5秒，全部exit=0。

对应Linux工作目录为 `/home/kayoko/ntn-workspaces/ntn-quadriga-handover`，实际离线命令：

```bash
bash local_ntn/run_regressions.sh
bash scripts/test.sh
python3 local_ntn/experiment.py preflight --profile integrated-handover --run-id causal-20261021-092620-854fd7 --rate 1
python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "$DERIVED_DL" --real-trace "$DERIVED_TRACE"
python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "$DERIVED_UL" --real-trace "$DERIVED_TRACE"
```

三个DERIVED变量对应当轮 `input-derivation.json` 和组别配置中记录的绝对路径，preflight使用派生环境变量。详情在Linux `.private/<suite-id>/`。

|项目|正常组|干预组|
|---|---:|---:|
|目标覆盖|100 IQ秒及首次切换|100 IQ秒及首次切换|
|干预窗IQ73–81的输入DL C/N中位数|19.887dB|3.887dB|
|UE中继入流（干预窗，墙钟平均）|352.79kbit/s|74.76kbit/s|
|解码帧率（干预窗，墙钟平均）|15.01fps|4.42fps|
|编码输出时间/墙钟进度|1.066|0.999|
|响应窗IQ73–90新增冻结|0秒|9.173秒|
|干预窗音频补偿样本增量|0|427,965|
|保护和清理|通过|通过|

干预窗入流约下降78.8%，解码帧率约下降70.6%。恢复窗口IQ92–99的干预组入流约223.76kbit/s、解码13.23fps；正常组分别约221.38kbit/s、13.23fps。观测到物理输入、UE入流、解码/补偿的关联，源仍实时推进，未暂停本地转发。

但本轮播放器均在运行中变为静音，固定和正常控制组原有有声门限未通过。严格配对最终为INVALID，suite INCONCLUSIVE，不能宣称正式证据验收通过。保留真实结果及原因；没有取消静音、重写原报告或放宽门限。

固定组 `live-static-20261021-092750-5cdbad`；正常组 `live-firsthandover-20261021-093059-208a0d`；干预组 `live-firsthandover-20261021-093423-373675`。三组原平台、运行源码及二进制、源片校验均未变，清理无错误。结束后只读检查无网络命名空间、运行容器或调制解调器进程。

短模式只用于流程验证。默认六轮、每轮615 IQ秒和第二次有声切换尚未在此次新入口下跑完；必须以用户实际长测报告判定，不能用本记录替代。
