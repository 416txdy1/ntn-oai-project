# 节点一：2 发 1 收端到端验收（2026-10-15）

## 范围与实现

下行真实 2 Tx × 1 Rx、上行 1 Tx × 2 Rx，单数据层。前置提交 640939d、cd8c833 完成空间信道、RFsim 和 OAI 接入；本节点补齐实际业务与独立数据验算。

新增 scripts/validate_spatial.py 在一个持续 WSL 会话内检查核心网状态、执行静态和动态 smoke、验算并清理自己启动的服务。拒绝接管已有 modem 或部分运行的核心网。scripts/audit_spatial_run.py 只输出数值摘要，不发布原始 UE 日志。新增回归用可手算的匀速运动检查时延和 Doppler 公式；必需的双端口 IQ 数据不再允许缺失时静默跳过。

## 已执行实验

运行目录 /home/duyaya/OAI/self-contained-test，root shell，沿用现有 Python/OAI/QuaDRiGa 环境。保持活动 WSL 会话，启动 bash scripts/core.sh up，source scripts/env_miso.sh 后分别运行：

```bash
python3 scripts/smoke.py --rate 0
python3 scripts/smoke.py --rate 1
python3 scripts/audit_spatial_run.py smoke-0-1792032399276106617 --ports 2
python3 scripts/audit_spatial_run.py smoke-1-1792033075203349834 --ports 2
python3 scripts/test_spatial_audit.py
python3 -m py_compile scripts/validate_spatial.py scripts/audit_spatial_run.py local_ntn/test_real_iq.py
```

以上记录退出码均为 0。

| 模式/label | PDU | ping | UL UDP | DL UDP | PBCH 失败 |
|---|---|---|---|---|---|
| static / smoke-0-1792032399276106617 | 成功 | 10/10 | 0/130 丢包 | 0/131 丢包 | 0 |
| dynamic / smoke-1-1792033075203349834 | 成功 | 10/10 | 0/130 丢包 | 0/130 丢包 | 0 |

动态接收吞吐 UL 98.1 Kbit/s、DL 100 Kbit/s，与 100 Kbit/s UDP 负载相符；不是容量测试。静态 RTT 平均 717.425 ms、动态 646.839 ms 是非实时仿真的墙钟结果，不可当作卫星几何传播时延。

验算器直接从 IQ 样本计数求仿真时间，以独立的三次多项式实现 Hermite 位置/速度，计算服务链路加馈电链路的几何时延、服务链路径向速度与双向频率的 Doppler，并对照 STK 相对增益和 C/N。动态最大误差：delay 4.976e-7 ms、Doppler 4.837e-4 Hz、gain 4.439e-4 dB、C/N 4.475e-4 dB，均符合日志舍入精度。动态 port 0/1 分别有 19/16 个非零能量窗，峰值 25990.640/20927.236，证明第二路实际承载 IQ。

## 失败记录与限制

早期两次静态 PDU 超时来自核心网未运行，详见前置验证记录。smoke-1-1792032465789866748 动态启动曾未完成初始同步；没有删除失败记录、改变噪声/功率或降低动态速率。SISO 动态对照 smoke-1-1792032951983802481 完整业务通过，同参数 2×1 动态复测如上通过；该次同步失败尚无确定根因，不能声称启动成功率为 100%。

本节点仅验收有界静态/动态业务，未覆盖完整 361 秒过境。现有 STK 绝对功率参考、1 秒 QD 快照采样及馈电链路空间简化限制保持，见 MISO_CHANNEL_VALIDATION_20261015.md。

## 连续运行复验

在 root shell 执行 source scripts/env_miso.sh 后，python3 scripts/validate_spatial.py --ports 2 退出 0。static smoke-0-1792033235136912236 和 dynamic smoke-1-1792033303806179908 均完成 PDU、ping 10/10、双向 UDP 0/130 丢包、PBCH 失败 0，独立数值审计均通过。动态第二路有 16 个非零窗，峰值 21282.665；物理量误差仍在上述范围。

提交前执行 OAI_SPATIAL_MODE=miso2 bash scripts/test.sh，退出 0；覆盖 trace parser、真实 IQ、队列历史、Python、C reader 和双向 ASan/UBSan 回归。
