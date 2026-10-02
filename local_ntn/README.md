# 当前入口

单仓库源码交付请使用 [MANUAL_RUN.md](MANUAL_RUN.md) 和仓库根目录 scripts/。以下保留历史实验记录，其中的外部绝对路径不是当前默认值。

> STK + QuaDRiGa 联合启动的新配置与只读预检查见 [联合仿真说明](JOINT_SIMULATION.md)。启动成功不等于 PDU/通信通过；当前验证结果见该说明与本次联调记录。

# 本机 STK–OAI–5GC 实验（2026-09-10）

> 当前机器（2026-09-23）的路径、修复、命令及实际验证结果见 [本地调试记录](DEBUG-2026-09-23.md)。以下结果和 `/home/kayoko` 路径属于原实验环境；当前使用 `/home/duyaya/OAI`、现有 v2.2.1 核心网和 `001/01 + oai`，尚缺已打开的 STK 场景与 STKTRACE2 轨迹。

## 已验证的结果

所有通信组件在本机 Ubuntu-22.04 WSL 内：gNB、UE、OAI 5GC v2.2.0。Windows STK 通过官方 API 导出当前相控阵场景。UE 使用独立网络命名空间 `oai-stk-ue`，防止同机路由绕过空口和核心网。

| 测试 | 结果 |
|---|---|
| 编译 | `nr-softmodem`、`nr-uesoftmodem`、`rfsimulator` 均成功 |
| 静态 STK，注册/PDU | 成功；本次分配 `12.1.1.66` |
| 静态 ping | 10/10，0% 丢包，平均 RTT 68.209 ms |
| 动态 STK，注册/PDU（最终回归） | 成功；本次分配 `12.1.1.70` |
| 动态 ping（最终回归） | 10/10，0% 丢包，平均 RTT 121.457 ms |
| 动态上行 UDP | 设定 100 kbit/s，接收 99.5 kbit/s，接收端报告 0/130 丢包，抖动 32.413 ms |
| 动态下行 UDP | 设定 100 kbit/s，接收约 100 kbit/s，接收端报告 0/130 丢包，抖动 1.092 ms |
| 真实 IQ 函数受控测试 | 10 dB 接收功率降低 → 输出信号能量比 0.100000000；无覆盖 → 信号分量为 0 |

这是低负载、单 UE、有限过境区间的验证，不是最大吞吐率或长期稳定性认证。RTT/吞吐/抖动由操作系统墙钟测量，受 RFsim 处理快慢、协议调度、CPU 负载影响，不等于卫星几何传播时延。初始接入时仍见到一次 PBCH 解码失败，随后成功同步和建链；不能宣称消除了所有 PBCH 错误。

## 时间机制：本次解决的核心问题

原有 UDP 路径同时使用了两种时间：Windows/STK 墙钟的新位置，以及按 RFsim 样本时间积分出来的传播时延。SIB19 又取当前 UDP 几何状态，位置、时延和广播参考历元可能逐渐不一致。

新增的 `STKTRACE2` 模式统一为：

```
STK查询时刻 = trace起始历元 + RFsim绝对样本时间戳 / 实际采样率 × rate
```

两端读取同一份文件，以相同规则查询。实际本次采样率为 7.68 Msamples/s。插值采用三次 Hermite，位置与速度的一阶导数一致；不根据 UDP 包到达间隔推断速度。SIB19 使用其宣布的下一帧历元对应状态，而不是把当前帧位置标记成下一帧。

`rate=1`：每个 RFsim 仿真秒推进 1 个 STK 秒；不保证等于 1 个现实秒。
`rate=0`：冻结测试，速度、Doppler、TA drift 也变为 0。
`0<rate<1`：有意降低轨迹速度，频移和漂移也相应缩放；不再代表卫星原始实际速度。

**重要边界：这是“真实 STK 场景数据导出 + 按采样时间重放”，不是跟随 STK 播放/暂停键的在线模式。** 原 `OAI_STK_PORT` UDP 模式保留，但此次成功结果不证明原实时桥接模式已修复。启动脚本主动取消旧 UDP 环境变量，避免混用。后续若要求在线交互，建议让 RFsim 时间成为 STK 查询请求的主时钟，而不是再次独立播放两个时钟。

## STK 参数确实如何改变 IQ

| STK/派生数据 | OAI 实際作用 |
|---|---|
| 卫星与地面 ECEF 位置 | 计算业务段+馈电段距离，设置 `channel_offset`，实际改变取样位置 |
| 速度/径向速度 | 设置 `Doppler_phase_inc`，在 IQ 上做连续相位旋转 |
| 最后一跳接收功率 dBW | 相对有效参考功率转换为 `10^(ΔP/20)`，乘到 IQ 幅度 |
| 两跳 C/N | 逆线性比相加，换算到采样带宽后实际注入高斯噪声 |
| 无访问/扫描越界 | 信号幅度归零，不再保持最后有效增益 |
| 馈电段距离、速度、加速度 | 动态更新 SIB19 common TA、drift、variant、位置、速度 |

这里保留 OAI 透明卫星模型“馈电段载波频移已补偿”的约定：RF 载波频移施加业务段，传播时延包含两段。common TA = `2 × 馈电段距离 / c`。当前场景的 gNB 参考点与 UE 恰好同址，但概念上是两个角色。

幅度不是将 dBW 直接当作整数 IQ。默认以文件第一个有效接收功率作为 0 dB 数字参考；STK 的绝对功率改变仍会通过 C/N 影响噪声。噪声按每块输入 RMS 标定，默认 STK 接收带宽 2 MHz；这是可控的链路级近似，不是绝对接收机灵敏度/完整射频前端模型。星上发射功率固定，两段不能简单相加发射功率。没有把 STK 的预测 BER/BLER 冒充 OAI 的实测 BER/BLER。

`test_real_iq.py` 编译仓库实际 `apply_channelmod.c`；为单独测量信号能量，测试桩将随机噪声取零，同时独立验证非零噪声系数。端到端实验使用真实高斯噪声函数。

## 本机配置与数据库

- 源码：`/home/kayoko/OAI/openairinterface5g`，基准提交 `c4125d1c74`，保留了原来的未提交修改。
- 核心网：`/home/kayoko/oai-cn5g-fed/docker-compose-v220`。
- AMF `192.168.70.132`，UPF `.134`，外部数据网 `.135`。
- gNB 的 N2/N3 本机地址 `192.168.70.129`。
- RFsim 专用 veth：gNB 一侧 `10.201.0.1`，UE 一侧 `10.201.0.2`。
- 实验 PLMN `208/95`；IMSI `208950000009901`；DNN `oai.ipv4`；SST `1`；SD `000001`。
- UE 私有配置：`/home/kayoko/.local/share/oai-stk/ue.local.conf`，权限 600，不在报告里显示 K/OPc。
- 原始 UE 配置、原有数据库测试用户均未覆盖。先前依据原 IMSI 补齐的 `001010000000001` 订阅也保留，但不是当前实验所用账号。
- SMF 当前启用 `use_local_subscription_info: yes`，实际 DNN/QoS 配置来自 `conf/basic_nrf_config.yaml`；数据库中也保存了本次用户的匹配会话资料。

已确认的一处原有问题：UE 的 `001/01` 与 gNB 的 `208/95` 不一致，AMF 明确返回 `PLMN_not_allowed`，并非 STK 引起。另一个问题是 UE 多上行 actor 下曾出现发送队列满；本次使用 `--num-ul-actors 1` 的保守基线未再复现。只新增了队列时间戳诊断，没有声称彻底修复所有并发队列情况。

## 按顺序运行

### 1. 保留一个 WSL 终端，启动核心网

在 Ubuntu-22.04 里：

```bash
cd /home/kayoko/oai-cn5g-fed/docker-compose-v220
docker compose -f docker-compose-basic-nrf.yaml -f docker-compose-extdn-ubuntu.yaml up -d --wait --wait-timeout 120
docker ps
```

不要执行旧的同时关闭 EPC/删除 orphan 的启动脚本。此环境曾在 WSL 外部短命令结束后停止容器；实验期间请保留 WSL 会话，不要 `wsl --shutdown`。

### 2. 需要变更场景时重新导出（Windows PowerShell）

STK 已打开目标场景，并且八个 OAI 收发对象路径与导出器匹配：

```powershell
cd "D:\实验室学习工作\杂活\雄安\OAI调研"
& D:\Anaconda\python.exe .\local_ntn\export_stk_trace.py --start 12080 --stop 12350 --step 1
```

本机 STK 的权限级别可能要求管理员 PowerShell 才能附加。导出不改变场景动画时间。不要在 gNB/UE 运行中覆盖轨迹期待热更新；先停止，再导出、重启。其他场景需要修改导出器的对象路径，不能直接宣称通用于所有命名/模型。

已导出文件共 271 个时刻，其中 252 个时刻上下行有效。超出相控阵扫描范围虽然可能仍有几何可视性，也会断链。到达文件末尾不会自动循环；跳回起点会造成不真实的位置/时延突变，所以未偷偷增加循环。

### 3. 本机一键启动/状态/测试（WSL）

```bash
cd '/mnt/d/实验室学习工作/杂活/雄安/OAI调研'

# 静态基线：可持续观察
sudo python3 local_ntn/experiment.py start --rate 0 --label manual-static
sudo python3 local_ntn/experiment.py status
sudo python3 local_ntn/experiment.py ping
sudo python3 local_ntn/experiment.py iperf
sudo python3 local_ntn/experiment.py iperf --reverse

# 停止本脚本启动的gNB/UE；不停止核心网或STK
sudo python3 local_ntn/experiment.py stop

# 动态自动验证：自动启动、等待PDU、ping、上/下行iperf
sudo python3 local_ntn/validate_dynamic.py
```

测试自动读取 `oaitun_ue1` 当前 IPv4，不固定最后一位。ping 目标是 **外部数据网 192.168.70.135**，不是 UE 自己的 IP。首次创建接口前运行 ping/iperf 会报错，先检查状态。

动态验证结束不会自动停止 gNB/UE，可继续观察直到扫描失效/轨迹结束；最后执行 `experiment.py stop`。再次启动前也先停止。`stop` 只向记录且启动时间匹配的进程组发送 SIGTERM，避免 `pkill -f` 误杀其他实验。

iperf 客户端和服务器使用同一个宿主机可见的 `iperf3`；服务器仅进入 ext-DN 容器的**网络**命名空间，仍走相同数据网路径，测试后退出。默认从 `PATH` 查找，也可用 `OAI_IPERF3_BIN` 和 `OAI_IPERF3_LIBRARY_PATH` 指定二进制及动态库。注意 `nsenter -n` 不会进入容器根文件系统，不能假设容器内的 `/usr/bin/iperf3` 在宿主机也存在。

### 4. 若想分窗口手动启动

先确保没有控制器启动的进程，然后在 WSL 工作目录准备一次：

```bash
python3 local_ntn/prepare_local.py --rate 1
sudo bash local_ntn/local_network.sh
```

gNB 窗口：

```bash
sudo OAI_STK_TRACE_RATE=1 bash local_ntn/run_local.sh gnb
```

UE 窗口：

```bash
sudo OAI_STK_TRACE_RATE=1 bash local_ntn/run_local.sh ue
```

两端 rate 必须一致；静态时上述三个 rate 都改为 0。手动启动的进程不归 `experiment.py stop` 管理，需在各自终端停止并确认 `pgrep -a -x nr-softmodem` / `pgrep -a -x nr-uesoftmodem`。

上述启动器固定使用轨迹第一行作为起点，会清除遗留 `OAI_STK_TRACE_EPOCH`，避免初始 SIB19/TA 与信道起点不一致。专用命名空间通过 `/run/oai-stk-ue.owner.json` 记录 inode/接口索引；若遇到同名但非本实验创建的网络会拒绝运行，不会直接修改它。

## 修改位置

实际 OAI 源码目录下：

- 新增 `radio/rfsimulator/stk_trace.h`、`stk_trace.c`：校验、读取、插值。
- 新增 `radio/rfsimulator/stk_trace_channel.c`：采样时钟、几何、Doppler、SIB19、功率/噪声、无覆盖。
- 修改 `radio/rfsimulator/apply_channelmod.c`：优先调用 trace 模式；将幅度和噪声真正接入 `rxAddInput`。
- 修改 `radio/rfsimulator/stk_channel_model.c`：初始同步优先使用 trace 的已应用状态；旧 UDP 模式保留。
- 修改 `radio/rfsimulator/rfsimulator.h`、`CMakeLists.txt`：接口和构建。
- 修改 `radio/COMMON/common_lib.c`：队列满时输出期望/实际时间戳，仅诊断。

本次修改前的文件在 `local_ntn/original/`。`local_ntn/staged/` 保存四个集成文件和队列诊断副本；新模块也在 `local_ntn/`。它们不是仓库最初版本，而是本次操作前已有用户改动的备份。

重编译：

```bash
cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build \
  --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
```

回归测试（WSL 工作目录）：

```bash
cc -Wall -Wextra -Werror -I local_ntn local_ntn/test_trace.c local_ntn/stk_trace.c -lm -o /tmp/oai-stk-trace-test
/tmp/oai-stk-trace-test
python3 local_ntn/test_real_iq.py
python3 local_ntn/test_trace_validation.py
```

最终实验结果见 `ping-static.txt`、`ping-dynamic-final2.txt`、`iperf-dynamic-final2.txt`、`iperf-dl-dynamic-final2.txt`、`iq-verification-final.txt`。原始 UE 启动日志会打印测试 SIM 的 K/OPc，**不要直接公开上传原始日志**；`experiment.py status` 只显示过滤后的状态。

交付时已停止本次控制器启动的 gNB/UE，确认没有残留的 `nr-softmodem` / `nr-uesoftmodem`；9 个核心网及配套容器仍为 healthy，STK 场景保留。

## 后续研究边界

1. 实时 STK API 模式应改为按 RFsim 请求历元查询，或带足够缓冲的统一时间服务；不能只调整播放倍率和 timeout。
2. 当前是单颗卫星有效过境区间；跨卫星接力、无缝循环需要连续星历与切换策略。
3. 绝对射频功率、天线扫描损失、多径、接收机噪声系数及带宽需进一步标定，才能用于工程级预算结论。
4. 当前只验证 100 kbit/s 负载；高负载、长时间运行和多 actor 并发队列仍需单独压测。

独立代码审查后增加了严格轨迹数值范围/时间步校验、延迟转换溢出检查、命名空间归属校验及进程退出竞争处理。原轨迹数值溢出用例先复现失败，再通过修复后的回归测试。

接口参考：[STK Cartesian Position（含 Fixed 坐标系）](https://help.agi.com/stkEngineOnUNIX/Subsystems/dataProviders/Content/html/dataProviders/Cartesian_Position~Vehicle.htm)、[STK Link Information](https://help.agi.com/stk/12.10.0/Subsystems/dataProviders/Content/html/dataProviders/Link_Information~Chain.htm)。
