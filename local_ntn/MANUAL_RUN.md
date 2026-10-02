# 单仓库手动运行配置与指令

本说明针对仓库内源码交付结构。只需拉取 ntn-oai-project 的 zky 分支；不需要额外 clone OAI、QuaDRiGa、ASN1C 或 SIMDe。Ubuntu 22.04/WSL2、Docker Engine/Compose v2、系统依赖仍须安装，核心网镜像首次可能需要联网下载。

## 1. 安装依赖、解包并编译

将仓库放在 Linux 文件系统，例如 `/home/你的用户名/ntn-oai-project`。以下第一条 cd 请使用你实际的目录；其余命令不需要修改用户名。

```bash
cd ~/ntn-oai-project
bash scripts/install_deps.sh
bash scripts/build.sh
```

构建默认使用 6 个并行任务，可用 `JOBS=4 bash scripts/build.sh` 调整。该步骤会校验 vendor/checksums.json，并解包本地源码归档至 `.runtime/`，先编译仓库内 ASN1C，再编译 nr-softmodem、nr-uesoftmodem 和 RFsim。没有 submodule update 或 git clone。

不要在 `.runtime/oai` 修改要保存的源码。OAI 改动维护入口是 `oai_patch/current/`；QD C 模块是 `quadriga/oai/`。重新构建会同步这些文件。原 `oai_patch/` 根目录和 `local_ntn/staged/` 是历史副本。

## 2. 生成新实验私有配置

在 root 终端执行初始化和网络实验（也可使用已有 Docker 权限及 sudo 保留环境变量）：

```bash
sudo -i
cd /home/你的用户名/ntn-oai-project
python3 scripts/init_lab.py
source scripts/env.sh
```

这会生成 `.private/ue.conf`、匹配的核心网订阅、随机 K/OPc 和数据库密码。不会输出密钥，也不会读取别人的私有配置。`.private/` 已被 Git 忽略，目录权限 0700；不要提交或复制其内容给他人。

默认核心网为 192.168.70.128/26、容器前缀 ntn-local。若本机已有该网段，**首次初始化时**改用：

```bash
python3 scripts/init_lab.py --subnet-octet 78 --prefix ntn-lab
source scripts/env.sh
```

两种初始化方式选一种；已有 `.private/` 时脚本会拒绝覆盖，正常后续运行只需 `source scripts/env.sh`。不同实验不要同时复用 RFsim 的 oai-stk-ue namespace。

## 3. 启动核心网与准备流量工具

保持 WSL 终端一直打开：

```bash
bash scripts/core.sh up
bash scripts/core.sh status
bash scripts/prepare_iperf.sh
```

`up` 会等待健康检查，失败时返回非零，不应继续启动 modem。核心网配置与订阅来自本次生成目录，无需拉取 5GC 源码。流量工具从本次 ext-DN 镜像复制到 `.runtime/iperf3/`，两端使用相同版本。

## 4. 预检查和动态启动

```bash
python3 local_ntn/experiment.py preflight --rate 1
LABEL="manual-dynamic-$(date +%Y%m%d-%H%M%S)"
python3 local_ntn/experiment.py start --rate 1 --label "$LABEL"
```

preflight 应报告 mode=STK+QuaDRiGa。gNB 加载上行 bundle，UE 加载下行 bundle；不要另外设置共享 OAI_QD_CHANNEL。已包含的输入为：

| 项目 | 值 |
|---|---|
| trace | examples/fdd-pass/trace.csv，362 快照，7882–8243 秒 |
| QD | examples/fdd-pass/downlink 和 uplink，每方向 11 路径 |
| DL / UL | 2488400000 / 1614900000 Hz |
| NR / 采样率 | 25 PRB、15 kHz SCS / 7.68 Msps |
| gNB / UE | 使用同一 trace、相同 rate |

rate=1 按 IQ 采样时钟推进轨道时间；rate=0 固定首行。不是墙钟实时速度。启动成功不代表 PDU 已完成。

## 5. 等待 PDU 并测试流量

```bash
python3 - <<'PY'
import json,subprocess,time
for _ in range(90):
    r=subprocess.run(['ip','-n','oai-stk-ue','-j','-4','addr','show','dev','oaitun_ue1'],capture_output=True,text=True)
    if r.returncode==0 and any(x.get('addr_info') for x in json.loads(r.stdout)):
        print('UE tunnel ready'); break
    time.sleep(1)
else:
    raise SystemExit('PDU timeout; stop and inspect local private logs')
PY
python3 local_ntn/experiment.py ping
python3 local_ntn/experiment.py iperf
python3 local_ntn/experiment.py iperf --reverse
```

ping 应 10 发 10 收。UDP 为 100 Kbit/s、15 秒，重点看 receiver 行的丢包率；上行 UE→ext-DN，下行使用 --reverse。脚本从 `.private/settings.json` 选择目标地址，不再固定本机旧容器名/网段。

如 ping 出现 time of day goes back，该次 RTT 作废，需要补测；不要用 RFsim 的墙钟 RTT 直接解释几何传播时延。收到旧隧道地址也不能替代业务验收。

## 6. 静态测试和自动验收

先停止上一轮：

```bash
python3 local_ntn/experiment.py stop
python3 local_ntn/experiment.py start --rate 0 --label manual-static
```

重复等待与业务测试。或让脚本自动执行启动、PDU、ping、双向 UDP、停止：

```bash
python3 local_ntn/experiment.py stop
python3 scripts/smoke.py --rate 0
python3 scripts/smoke.py --rate 1
```

结果保存在 `.runtime/reports/`，只在控制台输出摘要。原始 UE 日志可能含凭据，留在本地，不上传。

## 7. 数值回归和重新生成信道

modem 停止后执行：

```bash
bash scripts/test.sh
```

包含 trace parser、实际 IQ、长时延历史清理、双向 bundle 审计、逐快照/中点 C 卷积及 ASan/UBSan。所有编译引用均来自仓库解包目录。

示例回放不需要 STK/MATLAB。如需重新生成 QD，先 `python3 scripts/prepare_sources.py`，然后在 MATLAB 进入本仓库并执行：

```matlab
addpath(fullfile(pwd, 'quadriga', 'matlab'));
export_example_fdd;
```

它使用仓库内 QuaDRiGa 源码和示例 trace，输出至 `.runtime/generated-fdd/`，不会覆盖已验证 bundle。若修改 STK 几何，应重新导出 trace、更新 UE 位置并重新生成两个方向，不能只修改 manifest 哈希。

## 8. 完整停止

```bash
python3 local_ntn/experiment.py stop
bash scripts/core.sh stop
```

不会删除数据库卷、私有配置或别人的核心网容器；下次继续 source 环境后 up 即可。切勿用宽泛 pkill 或删除卷作为常规停止。

## 验证范围与许可证

当前示例总传播时延约 14.717–21.478 ms，业务单段约 7.359–10.739 ms；C adapter 回归覆盖全部 362 快照与 361 中点。低速流量测试不代表最大容量或整个过境在线稳定性。1 秒 QD 快照存在残余 Doppler 欠采样限制，复系数线性插值中点功率最低约 -0.093 dB，没有偷偷改成插值后归一化。

QuaDRiGa 随附非商业使用许可证；OAI、ASN1C、SIMDe 保留各自许可证，见 vendor/ 和源码归档。
## 9. 对自己的运行结果做数值验算

建议先执行第 6 节的两轮 smoke。它们会分别打印唯一 label，并生成 `.runtime/reports/<label>.json`。将下面两个 label 替换为本机实际值；保持原始日志在本机，验算器只输出汇总数值：

```bash
python3 local_ntn/audit_runtime_numbers.py \
  --run-dir "$PWD" \
  --labels smoke-0-你的编号 smoke-1-你的编号
```

该命令会核对 IQ 采样时间、STK 插值、上下行多普勒、传播时延、增益、C/N 和初始 TA；断言失败时退出码非零。若日志已被清理、当前生成配置换了轨迹，或使用了其他频率/采样率，不能直接套用这个针对当前示例的验算器。第 4 节单独执行 start 不会生成 smoke 结果 JSON，因此不能把手动 start 的 label 直接传给此命令。

本次示例的验算参考：总 feeder+service 几何时延 14.7174–21.4783 ms，初始 TA=3614295。日志时延差不超过 5.1e-7 ms、多普勒差不超过 5.1e-4 Hz 是打印舍入容差；不表示实际卫星测量达到这种精度。完整验证结果见 [SELF_CONTAINED_VALIDATION.md](../docs/SELF_CONTAINED_VALIDATION.md)。
