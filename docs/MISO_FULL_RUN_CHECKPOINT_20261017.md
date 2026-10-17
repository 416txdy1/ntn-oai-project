# 4×1 完整业务续检记录（2026-10-17）

## 当前轮入口（后续修改后已更新）

先读 `.runtime/fidelity-checkpoints/active.json`，再读取其中指定的 `checkpoint_path`；以下旧轮标识仅保留为历史，不应作为当前活动进程依据。

当前实现 `6b2167c`；业务 `fullpass-1792221840958142385`，工具会话42430，PID2334，启动ticks44460；记录器会话40792。控制台输出保存在 `.runtime/fidelity-four-sample-business.log`，检查点每15秒写入对应的新目录。已建立PDU，截至IQ28秒ping1–216连续，最近RTT约0.93秒，PBCH失败0；完整验收尚未完成。

新实现完整7.68Msps IQ回归：DL最大误差2.57243948e-11，UL1.6512793e-11。原百万QD参考及1%精度报告未重新生成，继续使用已经通过的结果。

## 旧轮续检说明（历史记录）

**不要重新运行生成、构建、IQ回归或启动新的 full_pass。先读取当前检查点，确认现有进程或最终报告。** 用户明确要求保留已运行结果，避免因会话 token 用尽而重头测试。

- 分支：zky-miso；运行实现提交：a4bea87，解析与完整精度记录提交：c074194；均未 push。
- 正在运行：fullpass-1792204181467086862。
- WSL：Ubuntu-22.04；运行副本：/home/duyaya/OAI/self-contained-test。
- 完整业务工具会话：34050；full_pass PID：2354，进程启动 ticks：122547。后续必须核对启动标识，不能只凭旧PID操作进程。
- 检查点记录器工具会话：74850；脚本：.runtime/checkpoint_full_business.py。仅观察本轮已存在的业务，每15秒保存，结束后自动收尾；不会启动或重启实验。
- 当前完整业务未完成，不能宣称只剩原尾部失败。

PowerShell 中先执行：

```powershell
Get-Content .runtime/fidelity-checkpoints/fullpass-1792204181467086862/latest.json
```

若 state=running，再查看原会话34050的输出，或执行以下只读命令核对实际进度：

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.runtime/inspect_current_full.py
```

若 state=finished，直接读取同目录 full_pass_final.json 和 failure_locations.json，并检查运行副本的最终报告及公式审计，不要从头跑。若进程已消失但没有最终报告，保留检查点并诊断中断原因；OAI协议栈目前不支持从任意IQ位置恢复内存状态，不能把分段重启拼接成完整业务通过。

## 已完成，无需无故重跑

- 完整密集信道已生成：DL162049快照、UL153559快照，含双向原尾部4快照。
- IQ0–357秒，4.5MHz频带，1%门限：DL组合界0.949024%，UL0.944053%，通过。
- 实际QD参考：DL1299767点，其中1137722个非输出节点；UL1231839点，其中1078284个非输出节点。
- 完整IQ回归：双向4097分层点、四种时间速率、静音边界、ASan/UBSan通过。实际7.68Msps下DL最大误差2.93303228e-11、UL1.6512793e-11。
- 标准构建、4端口原轨迹 scripts/test.sh、完整密集信道 scripts/test_fidelity.sh 均已通过。
- 双向尾部4快照的times、delays、coefficients、gain已与原 examples/fdd-miso4-subarray 逐字节比较一致。
- 测试精确命令、前次失败及修改原因见 MISO_FIDELITY_20261016.md。

## 本轮已运行部分（记录时点，后续以latest.json为准）

2026-10-17 10:46北京时间：gNB最后IQ69.999秒，UE69.999110秒；业务约IQ4秒建立。ping已连续收到1–887，中间无缺号；最近10次RTT约1.3–1.7秒，累计最大5.527秒；双方PBCH失败0。当前统计只包含已收到回复，不能替代最终发送/接收与UDP结算。

完整轨迹目标为最后日志IQ至少360.9秒，双向各100Kbit/s，保持原严格 full_pass 判定。只有原IQ357–361秒末尾连接失败可作为用户允许的已知问题；不能豁免更早的失步、PDU失败或持续积压。

## 已落盘证据

目录：.runtime/fidelity-checkpoints/fullpass-1792204181467086862/

- latest.json：原子更新的最新业务状态、IQ范围、连续序号、RTT及PBCH统计。
- history.jsonl：每15秒追加的去敏历史记录。
- identity.json：运行标签、PID启动标识、实现提交、运行源码SHA256。
- fidelity-vector-regression.log：已通过的原轨迹回归日志。
- fidelity-vector-full-regression.log：已通过的完整信道回归日志。
- downlink/uplink的manifest、fidelity_report、runtime_fidelity_report：已通过精度验收的绑定证据。
- full_pass_final.json、failure_locations.json：业务结束后由记录器收集；运行中尚不存在属正常。

原始modem日志仍只留在运行副本 local_ntn/，不得提交或发布。检查点与大数据留在忽略目录.runtime/。仓库其他人的三个文档改动继续保护。

当前业务进程保持运行；请保留机器、WSL和测试进程。会话换轮本身不要求重跑，但机器/WSL停止会丢失协议栈内存状态；已有数值回归、生成缓存和已落盘观测仍然有效。

## 2026-10-17 后续检查：原进程已中断

实时核对发现原PID2354不存在，WSL为新启动状态；没有最终full_pass报告。实际modem日志停在IQ约188.999秒，ping连续收到1–2376，最后RTT约340.5秒，PBCH失败0。检查点最后更新时间为北京时间15:13:41，原latest中的running是历史状态，不能作为当前进程存活证明。

已保存的history显示：IQ111秒RTT约1.32秒，IQ131秒约60.35秒，IQ147秒约168.96秒，IQ164秒约280.21秒。北京时间11:12至15:08存在约14214秒记录间隔，但积压在该间隔之前已经出现。不能只归因中断，也不能将本轮视为仅末尾失败。原生成与精度验证继续有效，不重做百万QD参考。

已实施同一快照区间内4个相邻IQ样本并行计算，每个样本保留独立时延、插值系数与12点核；跨区间和不足4样本沿用原处理。实际完整信道0/120/240秒位置，每方向每次处理1024000个样本，旧DL耗时1.406/1.366/1.414秒，新DL0.906/0.912/0.930秒；旧UL1.497/1.424/1.430秒，新UL0.981/0.933/0.931秒。输出校验值一致，速度提升约1.5倍；该局部基准不等于完整业务已通过。

执行标准scripts/wsl_lab.sh build（内部scripts/build.sh）、source scripts/env_subarray4.sh后bash scripts/test.sh、bash scripts/test_fidelity.sh均退出0。完整7.68Msps回归双向4097时刻、四种时钟速率、静音边界通过ASan/UBSan。日志为运行副本.runtime/fidelity-four-sample-regression.log和fidelity-four-sample-full-regression.log；对照基准保存在源仓库.runtime/fidelity-four-sample-benchmark.log。

2026-10-17：fullpass-1792221840958142385 已到361秒，strict passed=false。ping3248/2750，末498个未收，最大RTT459005.848ms；UL98596/DL84909bit/s。PBCH200次首次前置IQ356.99955符合旧尾部位置，但IQ300开始MCS降到0、DL约0.2Mbps并持续积压，故不能按仅尾部失败验收。检查点已包含最终报告，无需重跑收集。代码检查确认配置缺失pusch_AntennaPorts（上游默认1），PUCCH硬编码numSpatialStreamIndices=1，PHY确实仅使用该数目的接收IQ。正补齐NO_BEAM_MODE下PUCCH接收端口及生成配置的PUSCH端口；尚未证明这是全部业务故障根因。未改尾部、负载、MCS或物理信道。WSL无rg，已用Windows rg读取UNC源码。首次build尚未纳入未跟踪overlay，暂存新文件后重新执行标准build。
