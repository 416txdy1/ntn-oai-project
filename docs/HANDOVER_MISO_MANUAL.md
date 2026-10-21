# 合并版 handover + MISO 手动配置与运行指南

适用分支：`codex/handover-miso-integration`。连接逻辑来自 `origin/codex/ntn-quadriga-handover`（65bc517），四端口模型来自 `zky-miso`（9a65bc7），合并提交14f782b。本文描述已通过620 IQ秒验收的配置，不沿用旧zky的361秒/IQ负载验收。

## 1. 模型和验收口径

- STK trace驱动RFsim IQ采样时钟，epoch=8200秒，rate=1；full覆盖8200–8820秒，共620 IQ秒；firsthandover覆盖8200–8270秒，共70 IQ秒。
- 卫星16×16阵列分为四个8×8子阵；DL4Tx×1Rx，UL1Tx×4Rx，PDSCH单层。子阵采用均匀幅度、LOS相位对齐，不是完整STK MVDR实现。
- 共同物理阵元间距0.06023799590098055m：DL2.4884GHz对应0.5波长，UL1.6149GHz对应0.32448561324545894波长。
- 轨迹、切换表及导出/场景生成脚本沿用handover更新版本。仓库旧STK工程用于参考；本次运行不连接STK桌面、不现场导出trace。
- 双向UDP分别100000 bit/墙钟秒，1000字节包；Ping为RTT，UDP为单向延迟，期限均5墙钟秒。全程及切换窗口期限失败比例和最终丢包比例上限1%；实际发包速率测量容限5%。
- full两次切换完成时刻为8244、8799 STK秒（44、599 IQ秒），各前后5秒为验收窗口。这里是单小区连续物理信道/卫星身份变化，不是多小区Xn/RRC切换。

## 2. 工作副本与依赖

使用Ubuntu 22.04/WSL2的Linux文件系统工作副本，避免在/mnt/c或/mnt/d编译大量OAI源码。当前已验证副本为 `/home/duyaya/OAI/handover-miso-integration`；其他机器替换为实际路径。Windows `.runtime/handover-review-20261018` 是Git集成工作树，Linux副本才是执行位置。

运行下面命令前先确认工作副本包含本文及合并版覆盖源码；不要覆盖已有修改或拷贝他人的.private。依赖安装仅用于尚未配置的新环境，已有环境先检查，不重复安装：

```bash
cd /home/duyaya/OAI/handover-miso-integration
python3 --version
docker --version
docker compose version
# 新环境才执行：bash scripts/install_deps.sh
bash scripts/build.sh
python3 scripts/check_delivery.py
```

`vendor/`、`sources.lock`保留锁定版本；修改OAI覆盖应在`oai_patch/current/`，QD C模块在`quadriga/oai/`，再执行build。不要手改.runtime/oai当作持久修改。八样本AVX-512快路径在支持的CPU上使用，其他路径按编译支持回退；不同硬件的墙钟验收需要重新验证。

## 3. 初始化独立核心网配置

仅首次执行：

```bash
python3 scripts/init_lab.py --profile integrated-handover
```

生成`.private/profiles/integrated-handover/`中的UE凭据、核心网配置及settings.json。该目录已存在时脚本拒绝覆盖，应沿用匹配配置，不能为绕过错误删除现有凭据。UE与5GC必须使用同一初始化产生的凭据；不手工复制K/OPc到文档或终端。

固定隔离资源：Docker项目`ntn-qd-integrated`，核心网网段192.168.71.128/26，UE PDU池12.2.1.0/24，UE namespace `ntn-qd-ue`，RFsim端口4044。多个实验不能同时占用这些资源。使用本机已配置的Docker及网络命名空间权限，运行脚本需要root。

### 3.1 UPF 首包 QFI 修复镜像

当前官方 v2.2.1 镜像在首个 IPv4 上行包到达前使用默认 QFI=5，导致配置为 QFI=1 的 UE 拒绝首批下行包。合并版增加本地 UPF 补丁，首包 QFI 直接来自 PFCP 控制面规则。连接、IQ 时钟、MISO 数据和墙钟验收门限保持不变。

在 Linux 副本内执行；编译依赖安装在 Docker 构建镜像中，首次构建需要网络并可能耗时较长。不要与墙钟验收同时编译：

```bash
python3 scripts/build_upf_qfi.py --jobs 6
bash scripts/test_upf_qfi.sh
# 先用 core_lab.py down 停止本 profile（若已运行），再选择修复镜像：
sudo python3 scripts/configure_upf_qfi.py
```

选择器只更改本工作区私有 Compose 中的 UPF image 行，并保存一次性备份；拒绝在核心网运行中切换。原始镜像及配置模板保留，新初始化的私有配置也需要执行选择器。生成镜像为 `ntn-local/oai-upf:2.2.1-qfi-v1`，源码、补丁和程序哈希记录在 `.runtime/upf-qfi/manifest.json`。不要只同步无线覆盖文件而遗漏此镜像步骤。

回退：先停止本 profile，再执行 `sudo python3 scripts/configure_upf_qfi.py --rollback`，将恢复固定摘要的原 UPF 镜像。回退后原首包 QFI 问题也会恢复。构建来源与限制见 [UPF 补丁说明](../upf_patch/README.md)。

## 4. 检查输入与环境

|输入|full|firsthandover|
|---|---|---|
|trace|local_ntn/stk_trace_seamless.csv|local_ntn/stk_trace_firsthandover.csv|
|切换表|local_ntn/satellite_schedule_seamless.csv|local_ntn/satellite_schedule_firsthandover.csv|
|DL bundle|examples/handover-miso4/downlink|examples/handover-miso4/firsthandover/downlink|
|UL bundle|examples/handover-miso4/uplink|examples/handover-miso4/firsthandover/uplink|

full trace SHA256为`b73fa3dba8eee242f5125d307ed614310ea21ccb6d32f803d8cd36c06c8db366`。bundle内manifest/antenna的哈希绑定必须通过校验。已有四组导出数据可直接运行，无需MATLAB重新生成；不要将旧fdd-pass数据替换进这套验收。

运行用新的bash环境，不继承旧zky或其他run的OAI变量。下方脚本会清除其子shell中的OAI配置变量再显式设置本次参数；不会更改父shell或磁盘文件。不要先source全程env再调用短测，否则短测会拒绝继承的全程路径。

## 5. 手动启动短测与全程验收

在项目根目录保存以下脚本为`.runtime/manual_handover_miso.sh`，每次从项目根目录运行。先执行`mkdir -p .runtime`。脚本参数为case及唯一run_id，已有run_id不能复用。

```bash
#!/usr/bin/env bash
set -euo pipefail
case_name=${1:?usage: script firsthandover-or-full unique-run-id}
run_id=${2:?unique run_id required}
case "$case_name" in firsthandover|full) ;; *) exit 2 ;; esac
for variable in ${!OAI_@}; do unset "$variable"; done
export OAI_NTN_PROFILE=integrated-handover
export OAI_SPATIAL_MODE=miso4-subarray OAI_QD_WORKERS=8 OAI_QD_PROFILE=1
export OAI_NTN_TIMING_DIAG=1 OAI_NTN_TIMING_DIAG_START_IQ_S=0
export OAI_NTN_PUSCH_FAILURE_THRES=100 OAI_NTN_PDCP_REORDERING_MS=500
export OAI_NTN_CELL_KOFFSET_MS=80 OAI_RNGSEED=20260925
python3 scripts/core_lab.py up --profile integrated-handover --run-id "$run_id"
trap 'python3 scripts/core_lab.py down --profile integrated-handover --run-id "$run_id"' EXIT
python3 scripts/handover_acceptance.py --case "$case_name"   --profile integrated-handover --run-id "$run_id" --max-wall-seconds 10800
python3 scripts/audit_handover_spatial.py   ".runtime/runs/integrated-handover/$run_id/run.json"   ".runtime/runs/integrated-handover/$run_id/acceptance/report.json"   --output ".runtime/runs/integrated-handover/$run_id/acceptance/spatial-audit.json"
```

```bash
sudo bash .runtime/manual_handover_miso.sh firsthandover manual-miso-short-001
# 短测业务与空间审计通过后，再运行：
sudo bash .runtime/manual_handover_miso.sh full manual-miso-full-001
```

core_lab up等待自有核心网容器健康；acceptance负责启动gNB/UE、业务发送、观测、排空和停止，外层trap停止专属核心网。不要在另一个终端重复启动gNB/UE。若up失败且未到trap，应检查同一run的core状态，必要时用下节命令清理。

参数含义：8为QD计算工作线程数；SIMD八样本是另一层优化。PUSCH failure threshold=100、PDCP重排序=500ms、cell k-offset=80ms、随机种子20260925均属于本次验收配置，不应省略后声称等价复现。10800只是整体运行超时保护，不改变5秒业务期限。

## 6. 查看结果与安全停止

结果目录：`.runtime/runs/integrated-handover/<run_id>/`。

- `run.json`：实际输入、构建/覆盖哈希、线程、采样率和配置。
- `acceptance/report.json`：passed、failure_reasons、numeric_audit_ok、stop_exit、全程与窗口业务统计。
- `acceptance/spatial-audit.json`：四端口和实际非零Tx能量检查。
- `acceptance/numeric-audit.json`：时延、多普勒、功率等独立数值对照。
- 原始日志和逐包文件保留在本机；不要直接公开UE日志或私有网络/身份信息。

通过必须检查报告、空间审计和退出码；仅看到PDU地址、ping偶尔成功或“core healthy”不等于全程通过。诊断日志中gNB的QD接收方向显示1Tx×4Rx、UE方向显示4Tx×1Rx，需按信道方向解释，不能把这行当作端点自身RF端口配置。

手动中断时先Ctrl+C让驱动清理；必要时从新的shell指定原run_id停止：

```bash
sudo python3 local_ntn/experiment.py stop --profile integrated-handover --run-id manual-miso-full-001
sudo python3 scripts/core_lab.py down --profile integrated-handover --run-id manual-miso-full-001
```

不要使用全局pkill、docker compose down其他项目或WSL shutdown来替代按所有权清理。

## 7. 数值与回归检查

在独立shell运行，勿与墙钟业务验收并行竞争CPU：

```bash
export OAI_NTN_PROFILE=zky OAI_SPATIAL_MODE=siso OAI_QD_WORKERS=8
source scripts/env.sh
bash local_ntn/run_regressions.sh
bash scripts/test.sh
```

这里zky/siso是通用回归夹具的环境，不改变上面MISO业务配置。若pytest不在当前解释器，沿用项目已配置环境设置PYTEST_PYTHON，不在不明环境安装依赖。四组真实MISO数据另外显式检查：

```bash
for dataset in seamless firsthandover; do
  bundle_root=examples/handover-miso4
  if [ "$dataset" = firsthandover ]; then bundle_root+=/firsthandover; fi
  for direction in downlink uplink; do
    bundle="$bundle_root/$direction"
    trace="local_ntn/stk_trace_${dataset}.csv"
    python3 -m quadriga.tools.audit_link_budget "$bundle" "$trace"
    python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "$bundle" --real-trace "$trace"
    python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --sample-rate 7680000       --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle "$bundle" --trace "$trace"
  done
done
```

## 8. 已知现象和结果边界

修复前两次MISO full均通过但有首批DL1–5丢失；根因现已确定为UPF初始QFI错误。完成第3.1节的镜像步骤后，本次620 IQ秒全程为Ping1174/1174、UL15009/15009、DL15006/15006，均无丢包和5秒超期。短测下行1437/1437，但有2个切换期上行包缺失，仍满足原门限；该短测不能称双向零丢包。完整证据见[UPF QFI修复验收](UPF_QFI_FIX_VALIDATION_20261021.md)。

当前保留1秒信道快照和四子阵窄带等效；数值回归通过不等于取得高密度信道保真或完整MVDR认证。已有详细证据见[合并验证](HANDOVER_MISO_INTEGRATION_20261018.md)、[再次复测](HANDOVER_MISO_REPEAT_20261020.md)。

输出文件格式、旧脚本兼容性与时间单位见 [合并版输出格式说明](MERGED_OUTPUT_FORMAT_20261021.md)。
