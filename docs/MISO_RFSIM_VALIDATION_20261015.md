# MISO 步骤二：原生双端口 RFsim 与数值回归（2026-10-15）

## 实现与运行入口

OAI 仍基于 vendor/source-manifest.json 记录的 `1e0c78bfbb80424f275e73a3103f582e0f903413`，未更换 vendor 版本；当前修改维护于 `oai_patch/current/radio/rfsimulator/simulator.cpp` 和 `quadriga/oai/`。

- QD adapter 对所有 Rx/Tx 链路插值、缓存，再对每个接收端口计算 `sum_tx sum_path h[rx,tx,path] * x[tx](t-delay)`，保留分数采样延迟。
- RFsim 从接收方向 bundle 读取远端发射数量，使用本地实际接收数量；检查线上 IQ 包的天线数与信道维度匹配。原来的本地 Tx 数不能用于推断远端 Tx 数。
- gNB 使用原生 2 Tx / 2 Rx，UE 使用 1 Tx / 1 Rx。PDSCH 设置 N1=1、N2=1、XP=2、最多一层，并启用 CSI-RS。实际权重由 OAI 的原生预编码流程控制，不复制单路 IQ 来伪造双输入。
- 每个 IQ 秒统计两个发射端口的平均能量，避免只采空闲子帧导致误判。
- `prepare_local.py` 生成独立 `gnb.miso.conf`，不改原 OAI 模板、原 SISO 生成文件或私有 UE 配置；该生成文件不入库。
- 多端口预检查必须同时验证上下行维度，拒绝混用 SISO bundle。

在已配置的 Linux 实验副本中执行：

```bash
source scripts/env_miso.sh
python3 local_ntn/experiment.py preflight --rate 0
# 以 root 运行实验启动器；若使用 sudo，必须显式保留所需 OAI 环境变量。
python3 local_ntn/experiment.py start --rate 0 --label miso-static
python3 local_ntn/experiment.py stop
```

`source scripts/env.sh` 明确切回原 SISO 模式。不要给 gNB 和 UE 共用一个 OAI_QD_CHANNEL。双向文件分别由启动器传入。

## 已执行验证与验算

Linux 运行副本：`/home/duyaya/OAI/self-contained-test`。系统 Python 3.10.12、现有 GCC/Ninja/OpenSSL，未新增依赖。

```bash
JOBS=4 bash scripts/build.sh
OAI_SPATIAL_MODE=miso2 bash scripts/test.sh
OAI_SPATIAL_MODE=siso bash scripts/test.sh
source scripts/env_miso.sh
python3 local_ntn/test_real_iq.py
python3 local_ntn/experiment.py preflight --rate 0
```

以上命令退出码均为 0。`scripts/test.sh` 包含 trace parser、真实 IQ、接收队列长历史、Python 信道工具、C reader 与 ASan/UBSan sparse adapter 回归。

- 真实 IQ 路径：10 dB 功率损耗得到能量比 0.100000000；不可见区间为零；噪声比为 0.038400000，等于 `10^(-20/10) × 7.68 MHz / 2 MHz`。
- 新增实际 `rxAddInput` 测试：2 Tx × 1 Rx 与 1 Tx × 2 Rx 均匹配 STK 增益乘以 QD 卷积，防止集成层误回退到旧单 tap。
- 独立 Lagrange 插值参考对不同天线使用不同宽带 IQ；真实上下行每方向覆盖 362 快照及 361 中点，共 723 点，并检查越界静音。误差为 1e-12 量级，低于断言容限，ASan/UBSan 未报告问题。上行最大误差 4.06738396e-12。
- 上行最大历史长度 1586 个采样点（测试采样率 30.72 MHz）。它由全空间、全快照最大时延计算，不仅取第一条天线链路。
- 原 SISO 数据每方向的同类 723 点回归继续通过；上行最大误差 1.8189894e-12。
- 配置生成测试检查原模板不变、2 Tx/2 Rx、最多一层、模式错误拒绝和重复生成一致性。

隔离配置测试一度缺少新模块副本，已修正；审计错误消息一度与旧测试不兼容，已恢复旧诊断约定。没有删除或跳过失败测试。

## 端到端状态：尚未通过

两次静态 smoke（smoke-0-1792031549691692162、smoke-0-1792031853797549185）均为 `start_exit=0, pdu_ready=false, error=PDU timeout, stop_exit=0`。无线侧已同步并完成 RRCSetup，双端实际加载 2x1 / 1x2 信道；gNB 报告 No AMF is associated。

第二次记录的端口整窗平均能量：port 0 有 29 个非零时间窗，范围 3029.646—4259.908；port 1 有 26 个非零时间窗，范围 0—23.4。这证明第二路传输了实际 IQ；由于尚未建立业务，不能将端口能量差解释为业务预编码增益或吞吐量收益。

后续只读检查发现实验 AMF/MySQL 已停止，Docker 网络 endpoint 数为零。继续排查本地核心网生命周期与连通性；没有发布原始 UE 日志，也未修改用户凭据。

## 结果边界

本步骤验证空间维度、数字卷积、配置和构建，不等于完整业务验收。未宣称完整 361 秒过境通过，也不宣称已经实现 256 个 OAI 发射通道。双阵元布局、1 秒快照及绝对功率标定限制见 MISO_CHANNEL_VALIDATION_20261015.md。
