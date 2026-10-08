# blend 段信道解释修正（2026-10-03，全程复测仍未通过）

用户明确允许修正信道插值语义，要求卫星选择、切换时机和 5 秒 blend 窗口保持不变。原始 trace 和 DL/UL QD bundle 未改变。

## 可选模式

保持原基线：

```bash
export OAI_STK_TRACE_INTERPOLATION=hermite
```

实验性修正版：

```bash
export OAI_STK_TRACE_INTERPOLATION=blend-aware
```

未设置时仍使用 hermite。配置会传给两个 modem，并在 STKTRACE2 日志中打印模式。还没有把实验性模式设为默认，更不能把离线通过当成全程业务已通过。

## 数学语义

原实现把混合位置曲线的导数同时用作真实载波速度与时延变化率。切星位置混合造成的数百公里每秒位移，会被误解释成 MHz 级多普勒。

新模式保留原 Hermite 位置曲线、功率、C/N 和可见性。当相邻点位置差分速度超过本 LEO 场景的 20000 m/s 筛查上限时，将该区间标为合成过渡：载波多普勒使用输入物理速度的线性插值；时延漂移仍使用原位置曲线的导数。它不把混合坐标宣称为物理单星轨道，而是区分合成过渡与物理速度。

这是经过用户授权的信道模型语义调整，不是声称旧数据已经符合单星动力学。阈值识别是当前无切换事件字段输入的兼容办法，不等于通用卫星切换算法。

## 已完成检查

实际 C 插值源文件对 361000 个点做 A/B（1 ms 间隔）：4000 个混合点；位置、路径速度、功率和可见性逐点完全相同，非混合段物理速度也完全相同。最大载波速度从 1533726.767 降到 7349.372 m/s；下行多普勒绝对峰值从 2971044.832 降到 39356.152 Hz。

```bash
python3 local_ntn/test_blend_interpolation.py
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py
```

修正版 OAI 已重新编译；parser 和实际 IQ 回归通过。

验收 ICMP 改用 CLOCK_MONOTONIC，不再用可能回退的墙钟计算 RTT。新 netns 的 datagram ICMP 可能受 ping_group_range 限制，工具在 root 下回退到 RAW ICMP；独立 netns 回环 3/3 和 3 项编解码测试通过。未修改系统时间或放宽网络权限。

## 完整复测

```bash
source scripts/env.sh
export OAI_STK_TRACE_INTERPOLATION=blend-aware
bash scripts/core.sh up
bash scripts/prepare_iperf.sh
python3 scripts/full_pass.py --max-wall-seconds 1800
bash scripts/core.sh stop
```

第一次复测 fullpass-1790956771094496411 因 ICMP 工具权限问题在约 IQ 5 秒提前退出，不能评价切换段。修复工具后，fullpass-1790956961261766917 跑完整条轨迹，但未通过：ping 708 发 / 700 收，UE PBCH 失败 198 次；仅纠正载波速度不足以恢复末段业务。720 条运行日志的公式验算通过，不能据此宣称业务通过。

## 第二步：可选时延前馈（已复测，业务未通过）

```bash
export OAI_STK_TRACE_INTERPOLATION=blend-aware
export OAI_STK_BLEND_TIMING_ASSIST=1
```

位置曲线保持不变，也保留了合成段很快的时延变化。原 UE 仅在 PBCH 成功后反馈调整帧时序，可能在快速漂移时失锁。因此增加仅针对合成段的帧级时延前馈，通过现有 STK 同步接口预测下一帧边界的传播时延。逐帧采样修正保留小数余量，避免量化偏差累积；超出读块安全界限时明确失败，不静默截断。

这是接收机增加已知信道辅助信息的实验选项，默认关闭；不能把其结果与无辅助接收机的旧结果直接等同。卫星选择、切换时机、5 秒 blend 窗口和原 trace/QD 数据保持不变。common_lib.h 内部状态增加合成段标记，因此需要重新构建配套的 gNB、UE 和 RFsim。

2026-10-03：恢复被中断的构建后，385/385 完成。执行 `bash build-blend-timing.sh`，返回 0；其中时延前馈 C 测试、`python3 local_ntn/test_trace_validation.py` 和 `python3 local_ntn/test_real_iq.py` 全部通过。完整业务验收已结束，结果未通过，见下表。

补充验证：bash scripts/test.sh 返回 0，包含双向 QD reader/adapter ASan+UBSan 检查。独立几何计算显示末段 1 ms 内最大时延变化为 2.385068683 μs，10 ms 内为 23.848907370 μs；帧级前馈是否足够仍以业务结果为准。

## 本次完整复测结果

标签：`fullpass-1790996094370730643`，`blend-aware` + `OAI_STK_BLEND_TIMING_ASSIST=1`。轨迹 361 秒，业务自 IQ 约 4.999 秒 PDU 就绪后开始；两端日志到达 IQ 360.999 秒，墙钟约 692.566 秒。控制器停止返回 0。

| 项目 | 结果 |
|---|---|
| ping（单调时钟） | 654 发、646 收；末尾 647–654 缺失 |
| ping RTT | min/mean/max 156.871 / 235.631 / 451.937 ms |
| UL UDP | 发送 5765、接收 5699，差额 66；接收平均 97.658 Kbit/s |
| DL UDP | 发送 5864、接收 5704，差额 160；接收平均 98.959 Kbit/s |
| UE PBCH | 220 次失败；37 次出现在首次耗尽日志之后 |
| 首次 PBCH 失败前的最近 IQ 日志 | 356.999550 秒 |
| 时延前馈 | 37 条限频日志，最大记录修正 183 samples |
| gNB/UE 加载 | trace 与 QD 各加载一次 |
| 全程结论 | **未通过，不能作为已修复版本推荐** |

UDP 的 `lost_packets=0` 只表示接收序号内部未观察到缺口；结束时间不同，收发差额也不能直接换算成严格同窗口丢包率。尾部 ping 丢失和耗尽前 PBCH 错误已经足以否定全程业务通过。PBCH 用最近的每秒 IQ 日志分组，不能把它当成逐条错误的精确采样时间。

独立运行数值验算：

```bash
python3 local_ntn/audit_runtime_numbers.py \
  --run-dir /home/duyaya/OAI/self-contained-test \
  --labels fullpass-1790996094370730643
```

返回 0，共检查 gNB/UE 各 360 条记录。时延最大绝对误差 < 5e-7 ms，多普勒 < 0.0005 Hz，增益与 C/N < 0.0005 dB，均在日志舍入误差内。初始 TA 量化误差约 0.351 ns。这只说明运行输出符合当前公式，不证明当前合成信道或接收机业务表现正确。

本次未继续盲目把修正改成每 slot 应用：现有 UE 读取包含下一 slot 的首符号，仅改变读块长度会影响缓冲区布局；更细粒度补偿需要同时验证 IQ 拼接、频偏相位连续性和 UL 定时。帧级前馈保持显式可选且默认关闭，原始数据和切换流程未改。后续应先建立末段的独立同步诊断，再对改进方案运行完整轨迹验收。

未执行新的 Git 提交或 push；原始 modem 日志保留在隔离测试目录，没有加入仓库报告。