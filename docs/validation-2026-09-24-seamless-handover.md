# 单小区连续卫星切换验证记录

## 本次实现范围

- 地面 gNB 和 UE 固定不动；不引入多小区、Xn 或 RRC 小区切换。
- STK 仍负责卫星轨道与链路预算；导出器在卫星选择变化前生成 5 s 的 `prepare/blend/complete` 过渡区。
- gNB 和 UE 继续使用同一条 `STKTRACE2` 和同一 IQ 时间倍率；RFsim 在 IQ 时间戳上读取连续的时延、多普勒、功率和 C/N。
- schedule CSV 只用于日志标记当前卫星和切换阶段，不改变 RNTI、PDU Session 或 `oaitun_ue1`。

## 已完成的离线/编译验证

### 轨迹

输入为 STK 导出的 `stk_constellation_trace_blend.csv`，通过：

```text
python local_ntn/slice_trace.py --trace <STK目录>/stk_constellation_trace_blend.csv --schedule <STK目录>/satellite_schedule_blend.csv --start 8200 --stop 8820 --trace-out local_ntn/stk_trace_seamless.csv --schedule-out local_ntn/satellite_schedule_seamless.csv
```

生成 621 个 1 Hz 样本，包含两次切换：

```text
8239 s: S06 -> S05, prepare
8240–8243 s: S06 -> S05, blend
8244 s: S06 -> S05, complete
8794 s: S05 -> S04, prepare
8795–8798 s: S05 -> S04, blend
8799 s: S05 -> S04, complete
```

按 RFsim 的同一距离/径向速度公式重算得到：

- 全片段最大相邻时延变化：`1.509 ms`；
- 第一次切换窗口最大相邻时延变化：`1.229 ms`；
- 第二次切换窗口最大相邻时延变化：`1.509 ms`；
- 直接切换会产生约 `65 kHz` 的多普勒跳变，渐变轨迹将其分摊到 5 s 过渡区。

### 测试命令

```text
wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_trace_validation.py
wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/实验室学习工作/杂活/雄安/OAI调研/local_ntn/test_real_iq.py
wsl.exe -d Ubuntu-22.04 -- cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
```

结果：轨迹物理边界测试通过；真实 `rxAddInput` IQ 回归通过（10 dB 功率变化、静默、噪声、时延/多普勒变化）；三个 OAI 目标均编译成功。

## 端到端长时验证（实测结果）

本次测试在已授权的 WSL 终端中完成，未代填密码。进程由
`local_ntn/experiment.py` 的自有 PID 记录控制，测试结束后已停止 gNB、UE
及本次测试创建的探测进程；核心网容器保持运行。

```bash
cd /mnt/d/实验室学习工作/杂活/雄安/OAI调研
sudo -E env OAI_STK_TRACE="$PWD/local_ntn/stk_trace_seamless.csv" \
  OAI_STK_SCHEDULE="$PWD/local_ntn/satellite_schedule_seamless.csv" \
  OAI_STK_TRACE_RATE=1 bash local_ntn/run_seamless_validation.sh
```

曾按以下命令启动 5GC、gNB、UE，并覆盖两次切换：

```bash
grep -E 'satellite handover|STKTRACE2' local_ntn/gnb-seamless-20260924.log
cat local_ntn/ping-seamless-seamless-20260924.txt
cat local_ntn/iperf-seamless-seamless-20260924.txt
```


```bash
sudo python3 local_ntn/experiment.py stop
```

结果：

- `STKTRACE2` 和 schedule 均在 gNB/UE 两端加载，第一次切换记录为
  `OAI_LEO_P01_S06 -> OAI_LEO_P01_S05`，第二次为
  `OAI_LEO_P01_S05 -> OAI_LEO_P01_S04`；两端切换时间戳相差约 1 ms。
- 倍率 `1.0` 的实测中，UE 在第一次切换之前反复收到与自身发送值不一致的
  RAR RAPID，未能在切换前建立 PDU；把 `--cont-fo-comp` 改为 1 或 3
  也未消除该现象。
- 倍率 `0.1` 的同轨迹对照中，初始同步和 PDU 建立成功，说明静态/慢速动态
  链路本身可用。
- 倍率 `0.5` 的对照中，UE 最终建立了 `oaitun_ue1`，但轨迹在业务探测完成
  前耗尽，RFsim 按设计将信号静音；这不能作为无缝业务连续性的通过证据。

因此，截至本次测试，结论是：**卫星切换日志和动态参数注入链路已验证，
但 1.0 倍率下的接入/业务无缝性尚未通过**。后续应先解决高速动态时延、
多普勒与 PRACH/RAR 定时的一致性，再进行长时 ping/iperf 统计。

停止本次脚本创建的进程：

## 2026-09-24 后续修复（待 WSL 端到端复测）

- `local_ntn/test_seamless.py` 新增 `--rate`，默认 `0.1`，避免 RFsim
  加速重放在业务探测完成前耗尽轨迹；仍可显式使用 `--rate 1` 做高速 A/B。
- `run_seamless_validation.sh` 不再硬编码倍率，读取
  `OAI_STK_TRACE_RATE`，并把实际倍率记录到验证日志。
- `prepare_local.py` 新增可选 `--initial-lead-rfsim`（或环境变量
  `OAI_STK_INITIAL_LEAD_RFSIM`）。它按 `trace_start + rate × lead` 线性选择
  初始 STK 状态，生成对应的 gNB 初始 SIB19 和 UE `prop_delay`；默认 0，
  不改变既有行为。
- Windows 侧已完成：`python -m py_compile local_ntn/prepare_local.py
  local_ntn/experiment.py local_ntn/test_seamless.py` 通过，`git diff --check`
  无空白错误。WSL 自动执行通道随后返回 `Wsl/EnumerateDistros/Service/
  E_ACCESSDENIED`，因此本段修改尚未声称通过 OAI 编译或端到端测试。

建议在已授权的 WSL 终端按顺序复测：

```bash
cd '/mnt/d/实验室学习工作/杂活/雄安/OAI调研'
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py
sudo -E env OAI_STK_TRACE="$PWD/local_ntn/stk_trace_firsthandover.csv" \
  OAI_STK_SCHEDULE="$PWD/local_ntn/satellite_schedule_firsthandover.csv" \
  OAI_STK_INITIAL_LEAD_RFSIM=2.5 \
  python3 local_ntn/test_seamless.py --tag lead25-rate1 --rate 1 --duration 60
```

对照组只需将 `OAI_STK_INITIAL_LEAD_RFSIM=0`，其余参数不变；两组均执行
`sudo python3 local_ntn/experiment.py stop` 收尾，并比较 UE 日志中的 PRACH/RAR
匹配、PDU 建立时间及 gNB/UE 的 `STKTRACE2` 时间戳。

## 2026-09-28 本机完整复测

预检命令及结果：

```bash
python3 local_ntn/test_trace_validation.py
# PASS: trace physical bounds, finite fields, flags and valid input

python3 local_ntn/test_real_iq.py
# PASS actual rxAddInput: 10dB loss energy ratio=0.100000000; outage=0;
# noise ratio=0.038400000; delay and Doppler changed

cmake --build /home/kayoko/OAI/openairinterface5g/cmake_targets/ran_build/build \
  --target nr-softmodem nr-uesoftmodem rfsimulator -j 6
# 成功构建三个目标
```

短时动态业务测试使用默认动态时延和动态多普勒：

```bash
sudo -E env OAI_STK_TRACE="$PWD/local_ntn/stk_trace_seamless.csv" \
  OAI_STK_SCHEDULE="$PWD/local_ntn/satellite_schedule_seamless.csv" \
  OAI_STK_DYNAMIC_DELAY=1 OAI_STK_DYNAMIC_DOPPLER=1 \
  python3 local_ntn/test_seamless.py --tag codex-full-rate1 --rate 1 --duration 30
sudo python3 local_ntn/experiment.py stop
```

结果：UE 获得 `12.1.1.68`，gNB/UE 均记录 `OAI_LEO_P01_S06 -> OAI_LEO_P01_S05`；Ping 为
30/30、0% 丢包、平均 RTT 107.797 ms；上行 UDP 约 100 kbit/s，接收 99.6 kbit/s，
0/259 丢包。日志文件为 `local_ntn/gnb-codex-full-rate1.log`、
`local_ntn/ue-codex-full-rate1.log`、`local_ntn/ping-seamless-codex-full-rate1.txt` 和
`local_ntn/iperf-seamless-codex-full-rate1.txt`。

覆盖两次切换的长测命令：

```bash
sudo -E env OAI_STK_TRACE="$PWD/local_ntn/stk_trace_seamless.csv" \
  OAI_STK_SCHEDULE="$PWD/local_ntn/satellite_schedule_seamless.csv" \
  OAI_STK_DYNAMIC_DELAY=1 OAI_STK_DYNAMIC_DOPPLER=1 \
  python3 local_ntn/test_seamless.py --tag codex-handover-520 --rate 1 --duration 520
sudo python3 local_ntn/experiment.py stop
```

结果：日志确认 `S06 -> S05` 和 `S05 -> S04` 两次切换的 prepare、blend、complete 阶段。
第一次接入后的 UE 地址为 `12.1.1.69`，第二次重新接入后的地址为 `12.1.1.70`。
Ping 为 350/520，丢包 32.6923%，平均 RTT 98.527 ms；iperf 在约 375 s 报
`Network is unreachable` 并退出。UE 在切换窗口出现 PBCH 解码失败和 RRC 回到 IDLE，之后重新
完成初始同步和 PDU 建立；轨迹耗尽后按设计进入 `STKTRACE2 exhausted` 静音状态。

因此，本次复测证明动态轨迹、参数注入、两次卫星选择日志、重新接入和核心网业务路径均可运行，
但当前单小区实现还不能证明无缝业务连续性。详细日志保存在：
`local_ntn/gnb-codex-handover-520.log`、`local_ntn/ue-codex-handover-520.log`、
`local_ntn/ping-seamless-codex-handover-520.txt` 和
`local_ntn/iperf-seamless-codex-handover-520.txt`。
