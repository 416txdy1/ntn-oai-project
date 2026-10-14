# 迁移配置与实验验证（2026-10-14）

## 配置

D 盘主源码：`D:\synching_study\jingwenpeng\2026autumn\ntn-oai-project`。
WSL 运行副本：`/home/duyaya/OAI/self-contained-test`。
基线：`hermite`、`OAI_STK_BLEND_TIMING_ASSIST=0`、原始 trace/QD；未更改实验方法或验收标准。
复用已有 ntn-verify 核心网及私有凭据，网络为 `192.168.78.128/26`；未安装新依赖。

## 已完成验证

以下 PowerShell 命令均从 D 盘项目根目录执行：

| 命令 | 结果 |
|---|---|
| `pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action build` | 0，385 个增量构建步骤 |
| `pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action test` | 0，完整 scripts/test.sh 通过 |
| `pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action up` | 0，9 个容器健康，iperf 3.9 就绪 |
| `pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action preflight` | 0，STK+QuaDRiGa，上下行方向、频率、trace 哈希匹配 |
| `pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action smoke-static` | 0，静态业务通过 |
| `pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action smoke-dynamic` | 0，动态短程业务通过 |

完整回归实际在 WSL 运行副本执行 `bash scripts/test.sh`，其中强制要求的 `python3 local_ntn/test_trace_validation.py`、`python3 local_ntn/test_real_iq.py` 均 PASS。真实 IQ 10 dB 损耗对应能量比 0.1；不可见时为零；双向 QD 各 723 快照/中点检查及 ASan/UBSan 通过。

| 模式与 label | ping | UL / DL 接收速率 | UDP 丢包 | UE PBCH 失败 |
|---|---|---|---|---|
| 静态 smoke-0-1791939112724910740 | 10/10 | 99.3 / 100 Kbit/s | 各 0/130 | 0 |
| 动态 smoke-1-1791939183242366607 | 10/10 | 97.3 / 100 Kbit/s | 各 0/130 | 0 |

在 WSL 运行副本执行：

```bash
python3 local_ntn/audit_runtime_numbers.py --run-dir "$PWD" --labels smoke-0-1791939112724910740 smoke-1-1791939183242366607
```

退出 0，共验算 120 条双端数值记录。动态短测日志覆盖 IQ 1.999 至约 29.999 秒。

新增入口的 PowerShell/Bash 语法检查通过；完整实验运行期间额外调用 smoke-static 和 sync 均按预期拒绝（退出 2），没有停止或修改正在运行的 modem。

## 完整轨迹

完整运行 `fullpass-1791939259978679986` 已结束，墙钟耗时 721.59 秒，退出码 **1**，全程业务验收 **未通过**。

命令：`pwsh -NoProfile -File scripts/wsl_lab.ps1 -Action full-pass -MaxWallSeconds 1800`，实际调用 WSL 的 `python3 scripts/full_pass.py --max-wall-seconds 1800`。

- PDU 成功；业务从双端约 IQ 3.999 秒开始。
- 两端达到 IQ 360.999 秒（目标 >=360.9 秒），完整覆盖轨迹末端；没有因墙钟上限或 IQ 停滞退出。
- ping：682 发 / 674 收，缺少序号 675–682，共 8 个；使用 CLOCK_MONOTONIC，无时钟回退。
- UE PBCH 解码失败 200 次，gNB 0 次。首次失败之前最近一条 UE IQ 日志为 356.999550 秒；由于日志每秒记录一次，此值是故障前采样点，不是精确失步时刻。与约 IQ 357 秒进入异常混合段相符。
- UL：接收 5950 包，发送 6020 包，差额 70；DL：接收 5955 包，发送 6120 包，差额 165。接收端内部 lost_packets 虽为 0，收发计数并不相等，不能据此宣称全程零丢包；收发结束时间不同，差额也不能直接当等窗口丢包率。
- 两端 trace/QD 各加载一次；原基线插值和辅助关闭状态已在日志中核对。
- 本轮 modem 自动停止成功；随后入口 `-Action stop` 成功停止 9 个 ntn-verify 容器，保留原配置、数据库卷和日志。

对静态、动态和全程三轮执行：

```bash
python3 local_ntn/audit_runtime_numbers.py --run-dir "$PWD" --labels smoke-0-1791939112724910740 smoke-1-1791939183242366607 fullpass-1791939259978679986
```

退出 0，共验算 **840 条**双端记录，时延、多普勒、增益、C/N 与所选公式在打印误差容差内一致。这证明实现按当前输入计算，不能证明输入物理连续，也不能替代业务验收。

本次已恢复新主目录下的配置、构建、核心网和完整实验执行链路。剩余问题是原示例尾段的切星/位置混合建模与同步，而不是目录找不到、构建缺失或凭据不匹配。要消除该失败，应单独设计连续单星对照或真实切星处理；重新导出 trace 时必须同时重新生成匹配的双向 QD bundle，属于实验输入/方法变更。本次没有截短轨迹、修改数据、降低验收阈值或开启额外辅助来掩盖失败。

独立执行 `python3 scripts/audit_trace_continuity.py --trace examples/fdd-pass/trace.csv` 返回 1：IQ 357–358、358–359、359–360、360–361 秒异常。最大相邻位置步长 1020.145 km，Hermite 采样速度峰值 1533.727 km/s。该筛查结果与历史已知输入问题一致；未修改输入使其通过。

## 记录与影响

命令和完整输出：`.planning/2026-10-14-migration-full-experiment/terminal.log`。
数值审计和入口保护验证：同目录 `diagnostics.log`。
原始 UE 日志和凭据仅保留在 WSL 本机，不复制进报告。

修改集中于迁移入口、debug_console 的相对路径及文档；OAI/QD 信号处理代码、公共 API、数据和实验参数未修改。没有 Git 提交、推送或重置。同步之前的运行副本差异保存在 `.runtime/source-backups/`。
脱敏原始结果 JSON：.planning/2026-10-14-migration-full-experiment/ 下三轮 label 对应 JSON、fullpass-diagnosis.json、trace-continuity.json、runtime-audit.json。
