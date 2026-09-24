# NTN OAI 本地实验调试教程

> 适用仓库：`ntn-oai-project` 当前工作树
>
> 适用环境：Windows 11 + STK 12 + Ubuntu-22.04 WSL + OAI RFsim + OAI 5GC
>
> 当前机器路径：Windows `E:\jingwenpeng\2026autumn\ntn-oai-project`，WSL `/mnt/e/jingwenpeng/2026autumn/ntn-oai-project`

本文面向“从回归测试到真实 STK 动态链路”的本机调试。它以当前机器和当前代码为准，不把旧 `/home/kayoko` 环境的历史结果当作本机已验证结果。

## 1. 先理解系统在调试什么

本项目不是把 STK 当作实时 UDP 时钟源，而是先从 STK 导出确定性轨迹，再让 gNB 和 UE 按 RFsim 的 IQ 样本时钟重放同一份轨迹：

```text
Windows STK 场景
    │ export_stk_trace.py
    ▼
local_ntn/stk_trace.csv（STKTRACE2）
    │ 同一轨迹、同一 rate
    ├───────────────┐
    ▼               ▼
RFsim gNB         RFsim UE（oai-stk-ue namespace）
    │               │
    └────── 5G 空口 ┘
            │
            ▼
       OAI 5GC → oai-ext-dn（192.168.70.135）
```

时间映射为：

```text
STK 查询时刻 = trace 起始历元 + RFsim 绝对样本时间戳 / 采样率 × rate
```

- `rate=0`：冻结轨迹，速度、Doppler 和 TA drift 同时变为 0，适合作为静态基线。
- `rate=1`：每个 RFsim 仿真秒推进 1 个 STK 秒，是动态回归基线。
- `0<rate<1`：有意放慢轨迹；频移和漂移也同比缩小，不再代表原始卫星速度。
- gNB 和 UE 必须使用相同轨迹、相同 `rate`。
- 轨迹到末尾后信号会静音，不会循环，也不会冻结在最后一个有效状态。

STK 数据真正作用于 IQ 的位置如下：

| 输入 | OAI 中的作用 |
|---|---|
| 卫星、gNB、UE 的 ECEF 位置 | 计算馈电段和业务段距离，更新传播时延及 RFsim `channel_offset` |
| 卫星速度 | 计算径向速度和 Doppler，对 IQ 做相位旋转 |
| 接收功率 dBW | 相对首个有效功率参考转换为 IQ 幅度比例 |
| 两跳 C/N | 合成后按测量带宽换算噪声比例，向 IQ 注入高斯噪声 |
| `dl_valid` / `ul_valid` | 无覆盖时把对应信号幅度置零 |
| 馈电段距离、速度、加速度 | 更新 SIB19 的 common TA、drift、variant、卫星位置和速度 |

因此，调试时不能只看“STK 几何可见”。还要同时检查轨迹有效标志、RFsim 时延/Doppler、RRC/鉴权、PDU Session 和用户面流量。

## 2. 安全边界

1. 不要公开 `/home/duyaya/.local/share/oai-stk/ue.local.conf`，其中包含测试 SIM 凭据。
2. 不要直接上传原始 UE 日志；启动日志可能打印 K/OPc。优先使用 `experiment.py status` 的过滤、脱敏输出。
3. 不要使用 `pkill -f`。`experiment.py stop` 只停止它自己记录且 PID 启动时间匹配的进程组。
4. 不要覆盖 OAI 原始配置模板。`prepare_local.py` 只生成 `local_ntn/gnb.local.conf`。
5. 不要在 modem 运行时覆盖 `stk_trace.csv`；先停止、重新导出，再重启。
6. 不要直接运行 `oai_patch/deploy_stk_auto.sh`。它仍指向旧 `/home/kayoko` 路径，也不包含当前 STKTRACE2 的全部文件，只能作为旧版本参考。
7. 实验期间保留一个持续打开的 WSL 终端，不要执行 `wsl --shutdown`。本机曾因短 WSL 会话结束而停止容器并丢失 `/run/netns`。

## 3. 当前机器的基线状态

本文编写时的只读检查结果是：

- OAI 路径：`/home/duyaya/OAI/openairinterface5g`。
- `nr-softmodem`、`nr-uesoftmodem` 构建产物存在。
- 私有 UE 配置存在，权限为 `600`。
- `local_ntn/stk_trace.csv` 尚不存在。
- 主要 5GC 和 ext-DN 容器存在，但当前为 `Exited`。
- 当前没有 gNB/UE 进程，也没有 `oai-stk-ue` network namespace。

这意味着可以先做代码回归，但真实注册、PDU、ping 和 iperf 必须等 STK 场景打开并成功导出轨迹后再做。

## 4. 目录与关键文件

| 文件 | 用途 |
|---|---|
| `local_ntn/export_stk_trace.py` | 在 Windows 附加到已打开的 STK 12，导出 STKTRACE2 |
| `local_ntn/stk_trace.csv` | 生成的轨迹，gNB/UE 共用，不提交 |
| `local_ntn/stk_trace.json` | 导出元数据：场景、区间、行数、对象路径、有效点数 |
| `local_ntn/prepare_local.py` | 从轨迹首行和私有 UE 身份生成本地 gNB 配置 |
| `local_ntn/local_network.sh` | 创建并校验 UE 专用 network namespace 和 veth |
| `local_ntn/run_local.sh` | 进入 OAI 构建目录启动 gNB 或 UE |
| `local_ntn/experiment.py` | 推荐的一键启动、状态、流量测试和安全停止入口 |
| `local_ntn/validate_dynamic.py` | 动态自动验证：注册/PDU、ping、上下行 iperf |
| `local_ntn/run_regressions.sh` | trace、IQ、配置及语法的统一回归入口 |
| `local_ntn/provision_subscriber.py` | 创建私有 UE 配置；必要时插入缺失的实验订阅 |
| `local_ntn/audit_auth.py` | 只读核对 UE 配置与数据库认证是否匹配，不输出秘密 |
| `sources.lock` | 外部 OAI/5GC 路径、commit 与当前运行版本记录 |

仓库顶层还有一组早期或辅助工具，需要与当前主线区分：

- `stk_show_state.py`、`stk_link_metrics.py`、`stk_inspect_comm.py`、`stk_dump_comm_models.py`：用于检查 STK 状态、链路和 Data Provider，适合场景诊断。
- `stk_build_oai_ntn_scene.py`、`configure_stk_phased_array.py`：会创建或修改 STK 通信对象；后者还包含旧机器输出目录保护条件。除非正在专门配置场景，否则不要在日常链路调试中运行。
- `stk_oai_bridge_generic.py`、`stk_oai_bridge_generic_detailed.py`、`run_bridge_forward.py`：属于 STK→UDP 在线桥接实验路径，时间模型与本文的确定性 STKTRACE2 重放不同。
- `receive_*`、`run_ping_iperf_forward.py`、`forward_stk_csv.py`：属于跨 Windows/WSL 日志或文件转发辅助链，不是当前本机控制器模式的必要组件。
- `stop_oai_stk_tools.py`：旧工具链的清理脚本。当前流程优先使用具备 PID 所有权检查的 `experiment.py stop`。

本教程不删除这些工具，但也不以它们作为当前成功路径。若研究在线交互，应建立独立实验记录，不能与 STKTRACE2 的确定性结果混用。

默认路径由 `local_ntn/paths.py` 解析：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
python3 local_ntn/paths.py repo
python3 local_ntn/paths.py ue
```

默认分别是当前用户下的 `~/OAI/openairinterface5g` 和 `~/.local/share/oai-stk/ue.local.conf`。如需覆盖，使用 `OAI_REPO`、`OAI_UE_CONFIG`；通过 `sudo` 时要显式保留环境变量，例如：

```bash
sudo --preserve-env=OAI_REPO,OAI_UE_CONFIG python3 local_ntn/experiment.py status
```

## 5. 第一次调试前的准备

### 5.1 保持 WSL 会话并恢复现有核心网

先打开一个持续保留的 Ubuntu-22.04 WSL 窗口。在该窗口中：

```bash
docker start mysql oai-nrf oai-udr oai-udm oai-ausf oai-amf oai-smf oai-upf oai-ext-dn
docker ps
```

这里复用本机已有的 v2.2.1 容器，不是从空白机器安装 5GC。应等待 `mysql` 和各网络功能容器进入 healthy/running，再做认证审计或启动 modem。

如果容器不存在，不要用旧 `oai-cn5g-fed` compose 盲目重建。先核对 `sources.lock` 和 `/home/duyaya/OAI/openairinterface5g/doc/tutorial_resources/oai-cn5g/docker-compose.yaml`。

### 5.2 只读审计认证信息

使用私有启动配置进行只读核对：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
python3 local_ntn/audit_auth.py /home/duyaya/.local/share/oai-stk/ue.local.conf
```

重点看：

- `SUBSCRIBER_ROWS` 应为预期数量，通常是 1。
- `AUTH_MATCH` 中 `key_matches`、`opc_matches` 应为 `true`。
- IMSI 的 PLMN、gNB 配置和 AMF 支持的 PLMN 必须一致。本机当前使用 `001/01`、DNN `oai`、SST `1`、SD `ffffff`。

如果私有配置还未创建，或确认数据库确实缺少当前实验订阅，才运行：

```bash
python3 local_ntn/provision_subscriber.py --local-current
stat -c '%a %U %n' /home/duyaya/.local/share/oai-stk/ue.local.conf
```

该命令的保护逻辑是：

- 已有订阅且 K/OPc 匹配：保留 SQN 和 session 记录，不覆盖。
- 已有订阅但密钥不匹配：直接拒绝，不覆盖数据库。
- 订阅不存在：插入一个实验订阅和对应 session profile。
- 私有配置在写入凭据前设置为 `600`。

#### 核对 `position0` 与 trace 的 UE 坐标

启用 `--autonomous-ta` 时，OAI UE 会从私有配置的 `position0` 计算服务链路往返定时提前量（Timing Advance, TA）；它不会自动使用 STKTRACE2 中的 `ue_x/ue_y/ue_z`。因此两处必须使用同一组 ECEF 米制坐标。

`prepare_local.py` 会在生成 gNB 配置前比较两者，误差超过 1 米就拒绝启动。例如本次场景首行坐标为：

```text
x = -2176831.540396419
y =  4387441.716136720
z =  4071933.940179984
```

原私有配置的旧坐标 `(0, 0, 6377900)` 会把 7882 秒处的服务链路 RTT 从真实的 `14.717410 ms` 算成 `38.433797 ms`，使 UE 的 PRACH 多提前约 `23.716388 ms`，最终表现为“下行同步和 SIB19 正常，但 gNB 完全检测不到 PRACH”。修正时请复制出权限为 `600` 的场景专用私有配置，不要覆盖 OAI 原始模板，也不要把包含 K/OPc 的文件提交到仓库：

```bash
export OAI_UE_CONFIG=/home/duyaya/.local/share/oai-stk/ue.stk-20260923.conf
stat -c '%a %U %n' "$OAI_UE_CONFIG"
python3 local_ntn/prepare_local.py --rate 0
```

成功标准是 `prepare_local.py` 不报告 `position0 differs from trace first-row UE ECEF`。坐标相同只保证初始 TA 几何一致；移动 UE 场景还需要额外设计位置随时间更新机制。

### 5.3 编译 OAI

```bash
cmake --build /home/duyaya/OAI/openairinterface5g/cmake_targets/ran_build/build \
  --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
```

成功标准是三个目标成功构建或显示无需更新。不要把本仓库当作完整 OAI 源码树；真正的 OAI 修改位于外部仓库 `/home/duyaya/OAI/openairinterface5g`，基准 commit 记录在 `sources.lock`。

### 5.4 先跑代码回归

统一入口：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
bash local_ntn/run_regressions.sh
```

它依次验证：

1. trace 插值、样本时钟、功率转 IQ、无覆盖语义；
2. trace 的有限数、物理范围、有效标志和时间步；
3. 编译并调用外部 OAI 仓库实际 `apply_channelmod.c` 的 IQ 路径；
4. 10 dB 功率下降、噪声、时延、Doppler、无覆盖和旧 SAT_LEO_STK 可见性；
5. 配置生成、`001/01` 与 `208/95`、静态/动态速度、非法 rate、模板不变；
6. 动态验证能否正确传播 ping 失败退出码；
7. Python 编译、Bash 语法及 `git diff --check`。

若只需满足最小的 trace parser 与 IQ 回归：

```bash
cc -Wall -Wextra -Werror -I local_ntn \
  local_ntn/test_trace.c local_ntn/stk_trace.c -lm \
  -o /tmp/oai-stk-trace-test
/tmp/oai-stk-trace-test
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py
```

注意：这些测试使用临时 fixture，不等价于真实 STK 端到端实验。

## 6. 从 STK 导出真实轨迹

### 6.1 检查 STK 场景对象

当前导出器要求场景中存在：

- `Satellite/QIANFAN-166_69383`
- `Place/Beijing`
- `Place/OAI_UE`
- gNB、UE、卫星上的 8 个 OAI transmitter/receiver 对象

完整对象路径定义在 `configure_stk_phased_array.py` 的 `ENDPOINTS`，四段链路定义在 `LINKS`。

默认 `12080--12350` 是原场景的 EpSec 区间，不保证适用于新场景。换场景时先在 STK 中确认对象路径、Access 区间和相控阵扫描范围；仅有几何视线并不保证 `dl_valid/ul_valid=1`。

### 6.2 在 Windows PowerShell 导出

1. 打开目标 STK 12 场景。
2. 确保 STK 和 PowerShell/Python 的权限级别相同；若 STK 以管理员运行，PowerShell 也要以管理员运行。
3. 执行：

```powershell
cd E:\jingwenpeng\2026autumn\ntn-oai-project
& D:\miniconda\python.exe .\local_ntn\export_stk_trace.py `
  --start 12080 --stop 12350 --step 1
```

成功后应生成：

```powershell
Get-Item .\local_ntn\stk_trace.csv
Get-Content .\local_ntn\stk_trace.csv -TotalCount 4
Get-Content .\local_ntn\stk_trace.json
```

检查点：

- 第一行必须是 `STKTRACE2`。
- 每个数据行必须有 22 个数值字段。
- `stk_trace.json` 中 `rows`、`valid_dl_ul`、`endpoint_paths` 和时间范围符合场景预期。
- `time_before` 与 `time_after` 应一致，说明导出没有移动动画时间。
- 第一条数据必须上下行有效，否则 `prepare_local.py` 会拒绝生成初始配置。

常见失败：

- `Cannot attach to STK 12`：没有打开目标场景，或 STK 与 Python 权限级别不同。
- `GetObjectFromPath` 相关错误：场景对象路径与代码中的常量不一致。
- 有效点过少：检查 Access、波束指向、±60° 扫描范围和导出区间。

## 7. 推荐调试路径：先静态，再动态

### 7.1 静态基线（rate=0）

在 WSL 项目目录：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
sudo python3 local_ntn/experiment.py start --rate 0 --label manual-static
sudo python3 local_ntn/experiment.py status
```

`start` 内部会依次执行：

```text
检查轨迹/私有配置/OAI 二进制/root/重复进程
→ prepare_local.py --rate 0
→ local_network.sh
→ 启动 gNB，等待日志出现 No connected device
→ 启动 UE
→ 将 PID、启动时间、日志路径写入 processes.json
```

反复查看状态，直到 `oaitun_ue1` 获得 IPv4：

```bash
sudo python3 local_ntn/experiment.py status
```

状态判断顺序：

1. `gnb alive=True`、`ue alive=True`：进程仍在。
2. 日志出现 `STKTRACE2 loaded`：轨迹已载入，rate/epoch/噪声设置可见。
3. UE 完成同步与 `RRC_CONNECTED`。
4. 鉴权与安全模式成功，没有 `PLMN_not_allowed` 或认证拒绝。
5. PDU Session 建立，namespace 中出现 `oaitun_ue1` IPv4。

PDU 就绪后测试：

```bash
sudo python3 local_ntn/experiment.py ping
sudo python3 local_ntn/experiment.py iperf
sudo python3 local_ntn/experiment.py iperf --reverse
```

数据路径是：

```text
UE namespace / oaitun_ue1
→ RFsim 空口
→ gNB
→ UPF
→ oai-ext-dn 192.168.70.135
```

不要 ping UE 自己的地址。控制器会动态读取 `oaitun_ue1` 地址，将到 `192.168.70.135/32` 的路由绑定到该接口。iperf 默认是 UDP 100 Kbit/s、15 秒；无 `--reverse` 为上行，有 `--reverse` 为下行。

完成静态基线后：

```bash
sudo python3 local_ntn/experiment.py stop
```

### 7.2 动态自动验证（rate=1）

确认静态链路正常后执行：

```bash
sudo python3 local_ntn/validate_dynamic.py --tag local-debug
```

该脚本会：

1. 停止控制器此前拥有的进程；
2. 以 `rate=1` 启动 `dynamic-local-debug`；
3. 最多等待 35 秒，让 `oaitun_ue1` 获得地址；
4. 依次执行 ping、上行 iperf、下行 iperf；
5. 输出到：
   - `local_ntn/ping-dynamic-local-debug.txt`
   - `local_ntn/iperf-dynamic-local-debug.txt`
   - `local_ntn/iperf-dl-dynamic-local-debug.txt`
6. 任一流量测试失败都会以非零状态退出。

动态脚本结束后不会自动停止 modem。无论成功或失败，检查状态并收尾：

```bash
sudo python3 local_ntn/experiment.py status
sudo python3 local_ntn/experiment.py stop
```

## 8. 高级调试：分窗口手动启动

只有在需要直接观察两个 modem 的完整输出时使用。先确认没有控制器或其他手动 modem 在运行：

```bash
pgrep -a -x nr-softmodem
pgrep -a -x nr-uesoftmodem
```

准备配置和网络：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
python3 local_ntn/prepare_local.py --rate 1
sudo bash local_ntn/local_network.sh
```

gNB 窗口：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
sudo OAI_STK_TRACE_RATE=1 bash local_ntn/run_local.sh gnb
```

UE 窗口：

```bash
cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project
sudo OAI_STK_TRACE_RATE=1 bash local_ntn/run_local.sh ue
```

静态调试时，把上述三个 `rate` 都改成 0。手动启动的进程不归 `experiment.py stop` 管理，应在各自终端用 `Ctrl+C` 停止，再用精确进程名确认退出。不要使用宽泛的 `pkill -f`。

## 9. 日志怎么看

### 9.1 控制器日志

`experiment.py start --label NAME` 生成：

- `local_ntn/gnb-NAME.log`
- `local_ntn/ue-NAME.log`
- `local_ntn/processes.json`

原始日志可能含测试凭据，不应直接公开。日常先用：

```bash
sudo python3 local_ntn/experiment.py status
```

它只筛选同步、RRC、鉴权、PDU、队列、PBCH 和 STKTRACE2 等关键行，并尝试对 K/OPc 字段脱敏。

### 9.2 Windows 实时日志窗口

打开已有调试日志：

```powershell
powershell -NoExit -File .\local_ntn\debug_console.ps1
powershell -NoExit -File .\local_ntn\debug_console.ps1 -LogName debug-checks.log
```

将新命令和退出码写入可见检查日志：

```powershell
.\local_ntn\debug_run.ps1 -Command 'wsl.exe -d Ubuntu-22.04 -- bash /mnt/e/jingwenpeng/2026autumn/ntn-oai-project/local_ntn/run_regressions.sh'
```

同一个日志只保留一个写入者；并行执行编译和测试时使用不同 `LogName`。

### 9.3 关键 STKTRACE2 日志

典型日志类似：

```text
STKTRACE2 DL IQ=... STK=... delay=...ms Doppler=...Hz gain=...dB C/N=...dB valid=1 samples=...
```

字段含义：

- `IQ`：RFsim 样本时钟换算的仿真秒。
- `STK`：当前查询到的 STK EpSec。
- `delay`：馈电段加业务段总传播时延。
- `Doppler`：业务段 Doppler。
- `gain`：相对首个有效功率参考的 IQ 幅度变化。
- `C/N`：STK 两跳 C/N 的合成值，加上可选偏移后用于噪声。
- `valid=0`：该方向无覆盖，信号被静音。

## 10. 分层排障

不要一看到 UE 失败就改 Prompt、改 STK 或改核心网。按数据流从前到后定位。

### 10.1 前置文件或路径失败

现象：

```text
Missing prerequisites
Missing STK trace
```

检查：

```bash
python3 local_ntn/paths.py repo
python3 local_ntn/paths.py ue
ls -l local_ntn/stk_trace.csv
ls -l /home/duyaya/OAI/openairinterface5g/cmake_targets/ran_build/build/nr-softmodem
ls -l /home/duyaya/OAI/openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem
```

修复原则：缺轨迹就回到 STK 导出；缺二进制就重新构建；不要创建空文件绕过检查。

### 10.2 轨迹格式或物理范围失败

现象：`Expected STKTRACE2`、`invalid STKTRACE2 at line ...`、首行 coverage 无效。

检查：

```bash
head -n 4 local_ntn/stk_trace.csv
python3 local_ntn/test_trace_validation.py
python3 local_ntn/prepare_local.py --rate 0
```

旧 channel CSV 与 STKTRACE2 不兼容。每行要求 22 个有限数值，时间严格递增，位置/速度/加速度在物理边界内，最后两个有效标志只能是 0 或 1。

### 10.3 核心网未就绪

现象：数据库连接失败、NG Setup 失败、注册无响应。

检查：

```bash
docker ps -a
docker logs --tail 100 mysql
docker logs --tail 100 oai-amf
docker logs --tail 100 oai-smf
docker logs --tail 100 oai-upf
```

先恢复容器并等数据库 healthy，再重跑只读认证审计。不要因为一次 MySQL 尚未 ready 就删除数据库或重新创建所有订阅。

### 10.4 namespace 或 veth 冲突

现象：`Network name/address conflict`、`Namespace is not owned by this experiment`、owner marker mismatch。

检查：

```bash
sudo ip netns list
ip -d link show oai-stk-host
sudo python3 local_ntn/verify_network.py
```

脚本会核对 veth 类型、互为 peer 的 interface index、`10.201.0.1/30 ↔ 10.201.0.2/30`、namespace inode 和 root-owned marker。不要直接修改或复用来历不明的同名 namespace。

### 10.5 gNB 就绪超时

现象：`gNB readiness timeout` 或 `gNB exited; inspect log`。

检查：

```bash
sudo python3 local_ntn/experiment.py status
```

重点看 `gnb-<label>.log` 中配置解析、N2 地址、AMF 连接、RFsim 初始化和 `STKTRACE2 loaded`。控制器通过日志中的 `No connected device` 判断 RFsim gNB 就绪，不用 TCP 探测，因为探测连接会被 RFsim 当成 UE。

### 10.6 PBCH/同步失败

现象：`Error decoding PBCH`、UE 一直无法同步。

依次检查：

1. gNB/UE 的 `OAI_STK_TRACE_RATE` 是否相同；
2. 起始轨迹是否 `dl_valid=1`；
3. 初始时延文件是否由当前轨迹重新生成；
4. `delay` 和 `Doppler` 是否为有限且合理值；
5. 是否意外设置了遗留 `OAI_STK_PORT` 或 `OAI_STK_TRACE_EPOCH`。

`run_local.sh` 会主动取消旧 UDP 端口和遗留 epoch，确保初始 SIB19/TA 与轨迹第一行一致。一次 PBCH 失败后成功接入不等于所有 PBCH 问题已消失，应记录但不要夸大结论。

### 10.7 下行同步成功但 PRACH/RAR 失败

典型现象：UE 能解码 SIB1/SIB2/SIB19，反复打印 `RAR reception failed`，同时 gNB 日志没有 PRACH 检测记录。

按以下顺序排查：

1. 先比较 UE `position0` 与 trace 首行 `ue_x/ue_y/ue_z`；这是自主 TA 的输入，不是普通展示字段。
2. 用 trace 距离计算服务链路 RTT，并与 UE 日志中的 `timing_advance_ntn` 对照。
3. 再检查 `prop_delay`、SIB19 common TA、RFsim `channel_offset` 是否来自同一首行。
4. 仅在上述几何和时序一致后，再用 `OAI_STK_TRACE_NOISE=0` 做单变量噪声诊断。

不要看到 RAR 失败就首先提高功率或关闭噪声。本次实测在两个真实仰角窗口以及无噪声条件下都稳定复现失败；修正 `position0` 后未改链路预算即一次完成 4-Step RA、RRC 和 PDU Session，证明根因是 TA 几何输入错位。

### 10.8 注册被拒绝

现象：`PLMN_not_allowed`、Authentication Reject、Security Mode 失败。

检查链：

```text
私有 UE 配置 IMSI/K/OPc/DNN/S-NSSAI
→ prepare_local 生成的 gNB PLMN/SD
→ AMF 支持的 PLMN/S-NSSAI
→ MySQL AuthenticationSubscription
→ SessionManagementSubscriptionData
```

先执行只读 `audit_auth.py`。本机当前基线是 `001/01 + oai + SST 1 + SD ffffff`；不要照搬旧报告中的 `208/95 + oai.ipv4 + SD 000001`，否则会产生跨层不一致。

### 10.9 RRC 成功但没有 PDU/tun

现象：有 `RRC_CONNECTED`，但 35 秒内没有 `oaitun_ue1`。

检查：

- UE 请求的 DNN 与 SMF/订阅配置是否一致；
- S-NSSAI 是否一致；
- SMF、UPF、ext-DN 是否运行；
- UE 日志中的 PDU Session Reject；
- AMF/SMF 日志中的拒绝原因。

不要硬编码 UE 地址；地址由核心网动态分配。

### 10.10 ping/iperf 失败

先确认：

```bash
sudo ip -n oai-stk-ue -br addr
sudo ip -n oai-stk-ue route
docker inspect oai-ext-dn --format '{{.State.Status}} {{.State.Pid}}'
```

测试目标必须是 `192.168.70.135`，源接口必须是 `oaitun_ue1`。`nsenter -n` 只进入 ext-DN 的网络 namespace，并不会切换到容器根文件系统，因此服务端二进制也必须能从 WSL 宿主机路径访问。`experiment.py` 默认使用 `PATH` 中的 `iperf3`，也支持显式指定同一个二进制及其动态库目录：

```bash
export OAI_IPERF3_BIN=/path/to/iperf3
export OAI_IPERF3_LIBRARY_PATH=/path/to/libs   # 静态链接或系统库齐全时可省略
sudo --preserve-env=OAI_IPERF3_BIN,OAI_IPERF3_LIBRARY_PATH \
  python3 local_ntn/experiment.py iperf
```

客户端和服务端始终使用同一路径，避免混用不同版本导致不可信的抖动结果。如果 `apt` 本身存在未满足依赖，不要为安装 iperf3 盲目执行 `apt --fix-broken install`；先处理系统包问题，或使用一个宿主机可见的已验证二进制。

### 10.11 动态中途断链

检查 `valid`、轨迹时间和是否出现：

```text
STKTRACE2 exhausted ... signal muted (no looping or stale freeze)
```

可能原因：

- 卫星离开几何可见区；
- 相控阵超过 ±60° 扫描范围；
- RFsim 样本时间走到 trace 末尾；
- rate 设置不一致；
- 当前区间本身有效点不足。

不要通过偷偷循环轨迹来“修好”断链，因为跳回起点会造成不真实的位置、时延和 Doppler 突变。

### 10.12 发送队列满

当前 UE 启动基线使用 `--num-ul-actors 1`。如果日志出现 `Write queue` 或时间戳偏差，先记录期望/实际时间戳、CPU 负载、rate 和流量负载。现有代码只增强了诊断，不能宣称已彻底修复所有多 actor 并发问题。

## 11. 可选信道调试变量

当前 STKTRACE2 C 模块支持：

| 环境变量 | 默认值 | 含义 |
|---|---:|---|
| `OAI_STK_TRACE` | 由 `run_local.sh` 设置 | 轨迹文件路径 |
| `OAI_STK_TRACE_RATE` | `0`（启动脚本默认） | 轨迹时间倍率，允许 0 到 1 |
| `OAI_STK_TRACE_EPOCH` | 轨迹首行 | 起始 STK EpSec；启动脚本会取消外部遗留值 |
| `OAI_STK_TRACE_BW_HZ` | `2000000` | STK C/N 对应的测量带宽 |
| `OAI_STK_TRACE_EXTRA_LOSS_DB` | `0` | 额外链路损耗，同时降低信号和 C/N |
| `OAI_STK_TRACE_CN_OFFSET_DB` | `0` | 用于灵敏度实验的 C/N 偏移 |
| `OAI_STK_TRACE_NOISE` | `1` | 是否按 C/N 注入噪声 |

这些变量适合受控敏感性实验。修改它们会改变实验方法和结果，记录时必须写明，不能与默认基线直接混为一组。

## 12. 正确收尾

控制器模式：

```bash
sudo python3 local_ntn/experiment.py stop
pgrep -a -x nr-softmodem || true
pgrep -a -x nr-uesoftmodem || true
```

`stop` 不会停止核心网容器或 STK，也不会删除 namespace。保留这些状态便于下一轮调试。如果确实要关闭核心网，应明确逐个停止本实验容器，不要使用宽泛的清理命令。

## 13. 每次实验建议记录

为保证科研可复现性，至少记录：

- 项目 Git commit 与未提交 diff 摘要；
- `sources.lock` 中 OAI/5GC commit 和镜像版本；
- STK 场景路径、对象路径、导出 start/stop/step；
- `stk_trace.json` 的行数、有效 DL/UL 点数；
- `rate` 及所有非默认 `OAI_STK_TRACE_*` 变量；
- gNB/UE 配置中的 PLMN、DNN、S-NSSAI，但不记录 K/OPc；
- 构建和 `run_regressions.sh` 的准确命令、退出码；
- 静态/动态标签、PDU 地址、ping/iperf 输出文件；
- PBCH 失败、队列告警、断链时刻和对应 STKTRACE2 状态；
- 最终是否执行了安全停止，以及是否存在残留 modem。

## 14. 本项目结果的解释边界

- 历史环境曾验证单 UE、低负载、有限过境区间内的注册、PDU、ping 和 100 Kbit/s UDP；它不是最大吞吐率或长期稳定性认证。
- 操作系统测得的 RTT、抖动和吞吐会受到 RFsim 处理速度、协议调度和 CPU 负载影响，不等于纯卫星几何传播时延。
- 当前噪声是按每个输入块 RMS 和 STK C/N 标定的链路级近似，不是完整射频前端或绝对接收机灵敏度模型。
- 目前是单颗卫星轨迹重放，不包含跨卫星切换和无缝循环。
- 原 UDP 在线桥接模式仍保留，但当前成功路径不证明在线 STK 播放/暂停同步已修复。

## 15. 最短执行清单

```text
1. 保持 WSL 终端 → 恢复并等待 5GC 容器 healthy
2. audit_auth.py 只读核对认证
3. 构建 nr-softmodem、nr-uesoftmodem、rfsimulator
4. run_regressions.sh
5. Windows 打开 STK 场景并导出 STKTRACE2
6. rate=0 启动 → status → PDU → ping → 上/下行 iperf → stop
7. validate_dynamic.py --tag <tag>
8. status、保存结果、stop、确认无残留 modem
```

如果第 4 步通过而第 6 步失败，优先排查真实场景、核心网、认证和运行环境；如果第 4 步已经失败，先修代码或构建，不要进入端到端实验。
