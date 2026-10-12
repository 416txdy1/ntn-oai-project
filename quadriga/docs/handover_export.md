# 伪切换双向 QuaDRiGa 数据

整合 profile 的两组输入各自导出，不能用完整轨迹的 bundle 替代片段：

| 输入 | STK 时间范围 | 快照 | Bundle 根目录 |
|---|---:|---:|---|
| seamless | 8200–8820 s | 621 | examples/handover |
| firsthandover | 8200–8270 s | 71 | examples/handover/firsthandover |

每组包含 downlink（2488400000 Hz）、uplink（1614900000 Hz）和共同的 provenance.json。
生成时使用 MATLAB 9.13.0.2049777 (R2022b)、QuaDRiGa 2.8.1-0、
seed 20260925、QuaDRiGa_NTN_Rural_LOS。UL 继续使用原 zky 的 SISO 互易信道表示。

export_handover_fdd(trace_path, schedule_path, output_dir) 原样复用
export_stk_to_qdchannel、normalize_qd_channel 和 QDCHANNEL1 二进制格式。
公共相位稳定、逐快照路径功率归一化、零残余大尺度增益和相对 excess delay 均未修改。
快照间保持原复数线性插值，中点相消不会再被强制归一化。
只有新生成的 JSON 文本统一为 LF，以便 manifest 哈希跨 Windows/Linux 保持一致。

provenance.json 最后写入，记录输入原始 SHA256、行数与时间范围、生成时 Git 提交、
七个 MATLAB 源文件哈希、vendor 归档哈希、工具版本、两向 manifest 与数据哈希。
已有输出文件或目录一律拒绝覆盖。部分失败留下的目录没有完成记录，也拒绝原地重写。

integrated-handover 的 preflight 要求同一导出根目录下完整的 DL、UL 和共同完成记录，
并重新验证精确 trace/schedule 哈希、逐行时间轴、方向、频率、数组尺寸、数据哈希、
归一化、公共相位、零参考 excess delay 和无重复绝对增益。
zky 原入口仍允许无此 sidecar 的原 FDD 示例；legacy-handover 明确关闭 QD。

短运行需同时选择以下四个输入，不能只切换 trace：

```bash
export OAI_STK_TRACE="$PWD/local_ntn/stk_trace_firsthandover.csv"
export OAI_STK_SCHEDULE="$PWD/local_ntn/satellite_schedule_firsthandover.csv"
export OAI_QD_DL_CHANNEL="$PWD/examples/handover/firsthandover/downlink"
export OAI_QD_UL_CHANNEL="$PWD/examples/handover/firsthandover/uplink"
```

## 模型适用性

四次真实生成都出现 QuaDRiGa 警告：
`QuaDRiGa:layout:get_channels:sampling_ok`，
`Sample density in tracks does not fulfill the sampling theoreme.`
provenance.warnings 保存每个方向实际 lastwarn、1 s 轨迹间隔、频率和最大位置差分速度；
完整生成控制台记录另行保存在本地测试记录中。

最大位置差分速度约为长轨迹 1048909.918 m/s、短轨迹 1020145.192 m/s。
这是伪切换时混合卫星位置形成的合成轨迹差分，**不是实际卫星轨道速度**；
它与 STKTRACE2 的物理 velocity 列是不同量。本次保留原轨迹与 zky 导出数学，
验收证明数据契约、数值组合和仿真整合。它不能证明高速小尺度信道已经充分满足
空间采样要求，也不能把这份合成轨迹直接视为一颗真实卫星的连续运动。

## 2026-10-12 验证记录

在独立 Linux 副本 /home/kayoko/ntn-workspaces/ntn-quadriga-handover，
所有 C/IQ 测试使用其 .runtime/oai 源码及实际构建参数：

```bash
.runtime/test-venv/bin/python -m pytest -q quadriga/tests/test_handover_bundle.py
bash scripts/test.sh
source scripts/env.sh
PYTHONPATH=local_ntn python3 -m unittest test_runtime_config test_preflight
```

结果分别为 19 passed（无跳过）、exit 0、20 tests OK。
scripts/test.sh 包含 trace parser/physical bounds、真实 rxAddInput ASan/UBSan IQ 回归、
原 zky FDD 双向审计，以及长短四向 link budget、C reader、实际 QD RFsim adapter 审计。
长数据每方向检查 1241 个快照/中点，短数据每方向检查 141 个；
最大复数 IQ 误差不超过 1.875e-12，时间轴误差为 0，残余绝对增益为 0。
新 DL/UL history 分别为 22447/15236 samples，均通过边界和尾部验证。

已安装 MATLAB 真实执行 quadriga/tests/matlab_test_export_handover_fdd.m，exit 0：
原有文件/目录不被覆盖、错 schedule 时间轴在创建输出前拒绝、非均匀 trace
在原导出器触发 TraceRate 后没有完成记录、失败目录再次运行被 OutputExists 拒绝。
原 vendor 和 examples/fdd-pass 共 20 个文件逐一 SHA256 前后相等。

这些数值测试不替代后续全程业务验收。切换期间的业务变化必须以实际 IQ 时钟
对应的持续 ping 与上下行流量记录观测，不能根据输入曲线推测业务测试结果。