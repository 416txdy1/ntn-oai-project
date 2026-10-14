# zky 分支协作调试指南（2026-10-08）

## 当前状态

这是可复现问题的调试版本，不是全程验收通过版本。短时 ping/双向 UDP 和离线回归已通过；361 秒示例末段仍失步。2026-10-03 历史完整实验：ping 654 发 / 646 收，UE PBCH 失败 220 次。详细原因及数值验算见 [修复报告](BLEND_REPAIR_20261003.md)。

> 2026-10-14 更新：本次补齐保存的 STK 场景、Windows/WSL 运行入口和迁移验证报告。当前基线完整 361 秒业务仍未通过；最新结果见 [迁移验证](MIGRATION_VALIDATION_20261014.md)。天线对齐前的配置见 [STK 场景](STK_SCENE.md)，Windows 入口见 [Windows/WSL 运行](WINDOWS_WSL_RUN.md)。本次交付审计与验证边界见 [本地交付检查](ZKY_DELIVERY_20261014.md)。

## 1. 获取源码

在 Ubuntu 22.04 或 WSL2 的 Linux 文件系统执行：

```bash
cd ~
git clone --branch zky --single-branch https://github.com/416txdy1/ntn-oai-project.git
cd ntn-oai-project
```

已有工作副本的成员先检查自己的未提交修改，再使用 `git pull --ff-only origin zky`；不要用强制重置覆盖自己的代码。

OAI、QuaDRiGa、ASN1C、SIMDe 源码快照均在 vendor/，不需要额外拉取源码仓库。系统依赖、Docker 镜像仍需安装/下载；示例回放不需要 MATLAB/STK。重新生成信道需要对应软件与许可。

## 2. 构建与回归

```bash
bash scripts/install_deps.sh
JOBS=4 bash scripts/build.sh
bash scripts/test.sh
```

构建将源码解包到 .runtime/。OAI 修改应写在 oai_patch/current/，QD C 代码在 quadriga/oai/；不要只修改生成目录。每次改源码后重新构建。回归包含 trace parser、实际 IQ、插值 A/B、时延辅助以及双向 QD 检查。回归通过不等于完整业务通过。

## 3. 首次生成本机配置

以下操作在 root 终端中进行，先把路径换成刚克隆的实际目录：

```bash
sudo -i
cd /home/你的用户名/ntn-oai-project
python3 scripts/init_lab.py
source scripts/env.sh
bash scripts/core.sh up
bash scripts/prepare_iperf.sh
```

init_lab.py 仅首次执行，生成本机随机凭据和匹配的 UE/5GC 配置；已有 .private/ 时拒绝覆盖。默认网络 192.168.70.128/26，前缀 ntn-local。如有冲突，在首次初始化时改用 `python3 scripts/init_lab.py --subnet-octet 78 --prefix ntn-lab`，两种初始化命令只选一种。不要上传 .private/ 或原始 modem 日志。

## 4. 基线手动调试

保持上述 root 终端打开，显式选择原基线：

```bash
source scripts/env.sh
export OAI_STK_TRACE_INTERPOLATION=hermite
export OAI_STK_BLEND_TIMING_ASSIST=0
python3 local_ntn/experiment.py preflight --rate 1
LABEL="manual-$(date +%Y%m%d-%H%M%S)"
python3 local_ntn/experiment.py start --rate 1 --label "$LABEL"
ip -n oai-stk-ue -4 addr show dev oaitun_ue1
```

等 oaitun_ue1 获得地址后运行；若尚无地址，等待后重试，不要重复 start：

```bash
python3 local_ntn/experiment.py ping
python3 local_ntn/experiment.py iperf
python3 local_ntn/experiment.py iperf --reverse
python3 local_ntn/experiment.py stop
```

短测目标为 ping 10/10 和双向 100 Kbit/s UDP 有效接收；它不能证明末段正常。完整 PDU 等待脚本和排错步骤见 [手动运行指南](../local_ntn/MANUAL_RUN.md)。

## 5. 复现完整失败与实验修正

先停止手动启动的 modem，保留核心网运行，然后选择以下一种模式：

| 模式 | OAI_STK_TRACE_INTERPOLATION | OAI_STK_BLEND_TIMING_ASSIST |
|---|---|---|
| 原基线 | hermite | 0 |
| 仅修正混合段载波速度 | blend-aware | 0 |
| 载波速度修正 + 帧级时延前馈 | blend-aware | 1 |

例如复现最近一次实验：

```bash
export OAI_STK_TRACE_INTERPOLATION=blend-aware
export OAI_STK_BLEND_TIMING_ASSIST=1
python3 scripts/full_pass.py --max-wall-seconds 1800
```

脚本自启动 modem、等待 PDU、持续 ping 和双向 UDP，并在两端 IQ 时钟到达约 360.999 秒后停止。本示例输入共 361 秒；IQ 时间不等于墙钟，给出 1800 秒墙钟上限。最近复测返回 1，表示未通过，这是当前已知状态，不能忽略为成功。

结果在 .runtime/reports/fullpass-*.json。终端会打印本次 label；用该 label 验算公式：

```bash
python3 local_ntn/audit_runtime_numbers.py --run-dir "$PWD" --labels fullpass-替换成本次编号
python3 scripts/audit_trace_continuity.py --trace examples/fdd-pass/trace.csv
```

连续性筛查对原示例末 4 段返回 1，表示其不是连续单星运动；这是已知输入语义问题。blend-aware 保留原位置、切换时机和窗口，只调整载波速度解释；前馈默认关闭，开启改变接收机辅助信息条件。两个实验选项均未解决全程失步。

## 6. 停止与协作反馈

```bash
python3 local_ntn/experiment.py stop
bash scripts/core.sh stop
```

不要使用宽泛 pkill。调试时保持电脑开机、避免休眠，WSL 和 Docker 需要运行。

提交问题时请提供 commit 编号、所选模式、失败命令、脱敏的结果摘要和 IQ 失败区间。不要上传 .private/、数据库凭据或原始 UE 日志。UDP 的内部序号丢包为 0 不代表尾部无丢包；收发停止时间不同也不能直接用差额计算等窗口丢包率。

## 发布前检查（2026-10-08）

本次待发布代码与此前构建的隔离 WSL 副本逐文件核对一致；重新执行 bash scripts/test.sh 返回 0，包含 trace parser 和实际 IQ 回归。本次发布检查未重跑 361 秒业务；上文全程失败数据来自 2026-10-03，仍作为当前已知限制。
