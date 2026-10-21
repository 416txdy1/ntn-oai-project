# handover 连接修复与四端口信道集成验证

## 最新验收结论（2026-10-20）

四端口 MISO 已在原 handover 口径下通过短切换和完整620IQ秒验收：100 Kbit/墙钟秒、5秒期限、全程及两个切换窗口失败比例≤1%。STK trace/切换表/生成脚本沿用65bc517；未放宽业务指标或简化信道。原始STK工程仅作参考。

完整运行 `miso-full-20261020-batch-rx`：1272.828770821墙钟秒，passed=true，numeric_audit_ok=true，空间审计true，stop_exit=0，专属核心网已关闭。

| 业务 | 收到/发出 | 期限失败比例 | 已收包最大延迟 |
| --- | --- | --- | --- |
| Ping | 1213/1213 | 0% | RTT 3.690221秒 |
| UL UDP | 15500/15500 | 0% | 1.803087秒 |
| DL UDP | 15492/15497 | 0.032264% | 2.037207秒 |

两个切换窗口内三种业务的期限失败均0；PBCH错误、RRC IDLE、重新接入均0。DL缺5包，已计入期限失败，不能宣称零丢包。该结论限定于记录的输入、配置、8线程及本机执行环境。620IQ秒完整运行覆盖尾段，不再仅依赖70IQ秒短测。

安全聚合证据：[全程](validation/handover-miso-20261020/full.json)、[短测](validation/handover-miso-20261020/short.json)。运行清单的35个覆盖源码哈希已与候选逐一匹配。规定trace解析、实际IQ及ASan/UBSan、四组独立信道数值、完整scripts/test.sh通过；此前TSan受环境映射错误限制，未称其通过。下面保留诊断过程与失败运行，最终结论以本节为准。


## 版本与范围

- 连接基底：`origin/codex/ntn-quadriga-handover`，`65bc517a0ec5bfb4e9e2f665876ea5d188cac1a5`。
- MISO 来源：`zky-miso`，`9a65bc7`。保留新连接分支的 RX tracker、TX predictor、CRC-good quarter-gain MAC TA 反馈、独立运行配置和 handover 验收。
- 工作分支：`codex/handover-miso-integration`。验证期间不改主工作区已有文档，不推送远端。
- OAI / QuaDRiGa / asn1c 归档版本保持 `vendor/checksums.json`、`vendor/source-manifest.json`、`sources.lock` 的锁定值；新增覆盖是原生四端口收发、QD 空间 FIR 和配置适配。

## STK 天线与 MISO 含义

检查仓库保存的 `STK_LEO_Constellation_20260923_train_v2` 场景：卫星四个收发端点均为 16×16 Phased Array、0.5 波长间距、MVDR、无极化；地面 gNB 和 UE 为 Isotropic。此次没有修改 STK 场景。

沿用 zky-miso 的实现，将 16×16 阵列拆成四个 8×8 子阵 RF 端口：下行信道为 4Tx×1Rx，上行为 1Tx×4Rx，PDSCH 最多一层。子阵使用均匀幅度、LOS 相位跟踪，并非完整复现 STK 的自适应 MVDR。FDD 两方向保持同一物理阵列几何，参考频率 2.4884 GHz；实际 DL/UL 频率分别为 2.4884/1.6149 GHz。

新数据位于 `examples/handover-miso4`，短场景位于其 `firsthandover` 子目录，均由对应 handover trace/schedule 重新生成。随机种子 20260925、QuaDRiGa NTN Rural LOS。`provenance.json` 绑定生成代码、轨迹、调度、二进制信道和天线 sidecar 的 SHA256。

保留新连接分支的 1 秒信道快照间隔。MATLAB 报过采样定理警告；本验收检验连接与实际多端口收发，不代表新数据取得旧版高密度数据的 1% 信道保真认证。业务负载使用新 handover 验收的墙钟 100 Kbit/s，与旧 MISO 的 IQ 时间 100 Kbit/s 指标不可直接比较。

## SISO 基底实测

独立 Linux 副本 `/home/duyaya/OAI/handover-review-20261018`，原始 65bc517，运行 `review-full-20261018`：

```bash
bash scripts/build.sh
cmake --build .runtime/oai/cmake_targets/ran_build/build --target nr_pbchsim nr_prachsim -j 6
source scripts/env.sh
bash local_ntn/run_regressions.sh
bash scripts/test.sh
sudo python3 scripts/core_lab.py up --profile integrated-handover --run-id review-full-20261018
sudo env OAI_NTN_TIMING_DIAG=1 OAI_NTN_TIMING_DIAG_START_IQ_S=0 \
  OAI_NTN_PUSCH_FAILURE_THRES=100 OAI_NTN_PDCP_REORDERING_MS=500 \
  OAI_NTN_CELL_KOFFSET_MS=80 OAI_RNGSEED=20260925 \
  python3 scripts/handover_acceptance.py --case full --profile integrated-handover \
  --run-id review-full-20261018 --max-wall-seconds 3600
```

构建、trace parser、实际 IQ sanitizer、完整回归通过。完整 620 秒 IQ 场景验收 `passed=true`，墙钟 1171.80173886 秒，数值审计通过，清理返回 0。

| 项目 | 收到 / 发出 |
| --- | --- |
| Ping | 1119 / 1119 |
| UL UDP | 14317 / 14317 |
| DL UDP | 14311 / 14315 |

PBCH 解码失败、RRC IDLE、重新接入均为 0，两个切换窗口均覆盖。DL 全程丢 4 包，报告 `service_degraded=true`；不能称全程零丢包。该结果支持“指定配置下尾段业务连接已修复”。

## MISO 集成与验证状态

独立 Linux 副本 `/home/duyaya/OAI/handover-miso-integration`。完整构建及 `bash local_ntn/run_regressions.sh`、`bash scripts/test.sh` 均返回 0；覆盖 trace parser、实际 IQ、前后向 FIR 样本边界、多端口以及 TA 回归。新增 `local_ntn/test_handover_spatial.py` 的 5 个测试通过。

集成中修复了两个实际问题：QD 测试夹具缺少对称 FIR 的前看样本；MATLAB 在规范化 manifest 换行后没有同步 antenna sidecar 的绑定哈希。前者通过 ASan 重测；后者完整重导出后 preflight 通过。失败运行 `miso-first-20261018` 保留，未用于成功统计。

短切换运行 `miso-first-20261018b` 已完成 70 IQ 秒（664.043380274 墙钟秒），严格验收失败，保留原始报告。Ping 收到 570/570、UL 7237/7237、DL 7213/7236；PBCH、RRC IDLE、重新接入均为 0。数值审计与四个真实发送端口检查通过。

失败项为 5 秒墙钟及时性：Ping 279/570（48.95%）、UL 2422/7237（33.47%）、DL 3318/7236（45.85%）未按时交付。切换窗口中分别有约 100%、97.58%、97.08% 未按时交付。最终丢包少不能替代及时性验收。粗分段诊断中，UL CRC 失败集中在 30–50 IQ 秒，不能把全部延迟简单归因于 CPU。

用户再次明确：最终必须采用 handover 的墙钟 100 Kbit/s、5 秒及时性和 1% 门限，不改为旧 IQ 负载。完整 MISO 尾段暂未启动，也未完成最终合并。

2026-10-19 正在检查可关闭的 FIR 样本分段并行模式 `OAI_QD_WORKERS=1..8`（默认 1）。它保留逐样本时钟、12 点 FIR、tap 求和顺序及四端口系数，线程只写各自输出区间，并拥有独立缓存。此前几种没有有效收益的单线程改写已撤回。并行版本仍需真实短场景和完整场景验证，不能仅凭微基准宣布通过。

推荐运行入口为 `source scripts/env_handover_miso4.sh`。`scripts/audit_handover_spatial.py` 使用本次 `run.json` 与业务 `report.json` 校验四端口加载、单层配置以及四路实际非零发送 IQ，只输出聚合统计，不发布原始 UE 日志。

## 2026-10-19 计算加速复测

四线程运行 miso-first-20261019-w4 完成 70 IQ 秒，墙钟 394.746862879 秒，严格验收失败。Ping、UL、DL 超过 5 秒的比例分别为 25.816%、18.635%、23.649%；PBCH/RRC/reaccess 均为 0。切换时段存在 CRC 重传和 MCS 降低，不能把原因全部归于计算速度。

最新快路径在连续整数延迟时批量载入四个复数样本，并用前后缀乘积计算同一 12 点 Lagrange 系数；非连续延迟仍走原路径。未修改信道采样、负载、期限或 MCS 策略。八线程增量构建、trace/IQ 回归及四组生成信道的 ASan/UBSan 校验通过，最大数值误差 2.25e-11。TSan 在 main 前报 unexpected memory mapping（exit 66），不能算通过。

复现命令：在候选 Linux 副本 source scripts/env_handover_miso4.sh 后设置 OAI_QD_WORKERS=8，运行 bash local_ntn/run_regressions.sh；四组数据校验脚本保存在主工作区 .planning/handover-tail-review-20261018/check_generated_miso.sh。八线程业务短测已结束，最终结果见下文。

八线程短测最终结果（miso-first-20261019-w8fast）：70 IQ 秒，238.296132128 墙钟秒，passed=false。Ping 21/196（10.714%）、UL 183/2498（7.326%）、DL 188/2497（7.529%）未按 5 秒期限送达；切换窗口失败上界为60%、42.166%、41.705%。最终收包分别196/196、2498/2498、2490/2497。数值审计通过，PBCH/RRC/reaccess为0，stop_exit=0，专属核心网已关闭。空间审计确认DL4Tx1Rx/UL1Tx4Rx及8线程，因业务不通过总结果仍为false（exit1）。

实际命令（Windows项目根目录）：
```powershell
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/run_miso_workers8_short.sh
```
脚本返回1（六项全程/窗口及时性失败），没有驱动或摘要错误。相比四线程，墙钟时间减少39.6%，仍不足以通过严格业务验收。40–50 IQ秒存在MCS降至0及CRC重传，随后恢复。后续需定位切换期间的有效吞吐与计算耗时，不能直接提高MCS或放宽信道模型。未启动完整MISO620秒验收，未完成合并提交，也未推送。
## 2026-10-19 数值对照与精确计算优化

用户要求保留 handover 时钟：轨迹/信道由 IQ 推进，业务100 Kbit/墙钟秒、期限5墙钟秒。新增计划目录 diagnose_window.py 独立读取磁盘系数和时延，在窗口内按0、1/4、1/2、3/4、1位置插值，计算平均链路路径功率 sum(|h|²)/links、直流响应功率及功率加权RMS超额时延。直流响应不代表全带宽吞吐，RMS时延不等同于最大超额时延。

MISO窗口平均路径功率最低DL0.99322/UL0.99250；RMS时延最大DL3.922us/UL2.419us。SISO同场景亦有DL2.816us/UL2.659us，并且同样观察到tracker delta=-320样本。使用(卫星-gNB距离+卫星-UE距离)/299792458独立计算，总时延在39到44 IQ秒由21.4783ms变为15.5445ms，每秒约-8787到-9441采样；平稳时段仅约+242/-164采样。这说明大幅定时变化与输入切换几何相符，尚不能据此判为MISO移植错误。摘要按最近RF日志对齐，存在分段精度限制；完整运行数字审计另行按实际采样时间核验。

代码改动：qd_channel_adapter.c 的四样本全部整数时延时直接取原采样，跳过原来计算后会丢弃的12点FIR；混合整数/分数批次保持通用路径。apply_channelmod.c 增加 OAI_QD_PROFILE=1 可开启的线程本地阶段计时，默认关闭，不修改采样时间或随机噪声序列。

独立参考使用通用Lagrange基函数，而非复用优化权重公式。四组MISO数据在8线程下ASan/UBSan通过：完整DL/UL各1241个快照/中点、短场景各141个，最大误差分别2.24996563e-11、1.53876720e-11、2.21289612e-11、1.32424427e-11，含0/.5/1/1e6速率及非整批边界。

复现脚本：主工作区 .planning/handover-tail-review-20261018/check_integer_profile.sh。首次误在integrated环境运行默认profile配置夹具导致断言失败，改回标准zky/siso测试环境；不修改测试断言。完整回归仍待最终退出码，真实业务复测尚未开始。

## 2026-10-19 注册启动修复与直接旋转验算

integer-profile、integer-repeat、integer-noprof三轮在业务建立前退出，均不得计作有效业务通过。进一步诊断确认UE收到Registration Reject / Illegal_UE，并主动退出；关闭耗时观测仍复现。没有修改UE身份或数据库密钥。原CoreLab.up仅等待Compose启动命令返回，不等待NF健康。等待本工作区全部服务健康后，integer-ready正常注册并完成70 IQ秒，支持启动竞态解释。

CoreLab.up现调用有界120秒wait_ready：验证完整自有服务集合、Running和已配置Health状态；每轮仍执行所有权预检，不放宽资源清理边界。新增测试覆盖starting到healthy、缺失、停止、不健康、外部容器及非法期限，共10项通过，已接入scripts/test.sh。handover_acceptance仅增加退出时的进程身份诊断，24项驱动测试通过。

integer-ready完成耗时240.28665891秒，数值审计通过，PBCH/RRC/reaccess均0，但全程及窗口的Ping/UL/DL及时性六项仍失败。阶段计时显示gNB FIR57.6%/后处理40.7%，UE FIR75.9%/后处理20.9%。本轮整数快速分支无确认端到端收益，已撤回至此前通过的8线程FIR实现。

后处理改为显式实数复数旋转：r'=r*cos(phi)-i*sin(phi)，i'=i*cos(phi)+r*sin(phi)。保留原逐样本相位累加，不用递推振荡器、不改噪声序列。200万相位点微基准最大double误差4.54747350886e-13；本机耗时从0.054944降至0.040002秒。实际rxAddInput新增15组、每组67个复数样本（正负/零频偏、大相位）；与原复指数参考的float32输出最大差0，相位末值也一致。

新增测试曾漏complex.h，已补；随后发现参考误按double常量累加，而OAI Doppler_phase_inc为float32，已改为实际字段值而未放宽误差阈值。这是测试参考修正，不是生产时钟或精度改变。

check_direct_rotation.sh最终exit0：增量构建、trace parser、实际IQ ASan/UBSan（含上述1005样本）、核心网与驱动测试全部通过。完整scripts/test.sh在此前整数版本通过；恢复的FIR为先前已通过四组数据独立验算的版本。最新真实短测miso-first-20261019-direct-rotation运行中，尚未完成完整MISO620秒验收或合并提交。
## 2026-10-20：STK 输入来源核验

按用户要求，当前合并以 origin/codex/ntn-quadriga-handover 的 STK 导出数据、切换表及场景生成脚本为准。git ls-remote origin refs/heads/codex/ntn-quadriga-handover 确认远端仍为 65bc517a0ec5bfb4e9e2f665876ea5d188cac1a5。

- 合并候选与 Linux 运行目录中，local_ntn/stk_trace_seamless.csv、stk_trace_firsthandover.csv 及三个 satellite_schedule CSV 均与该提交逐字节一致。
- configure_stk_phased_array.py、stk_build_oai_ntn_scene.py、local_ntn/export_constellation_trace.py、export_stk_trace.py 均逐字节一致。
- STK_LEO_Constellation_20260923_train_v2 中的两个 blend CSV 及 examples/fdd-pass/trace.csv 只有 CRLF/LF 差异，逐行数据一致；未为统一换行改动已有文件或信道包绑定。
- handover 分支没有 .sc/.sa 原始场景工程。合并保留的这些工程来自 zky-miso，仅作为参考，不能视为 handover 最新场景，也不是当前回放的数据来源。后续生成应以 handover 场景生成/导出脚本为基准，不能从旧工程覆盖当前 trace。
- 最近实际运行 miso-first-20261019-direct-rotation 的 run.json 确认使用 local_ntn/stk_trace_firsthandover.csv，SHA256 b29c32916d4adbaadbc24d1bc91d5ec84110461a97ceea083898ef705de92c03；切换表为 satellite_schedule_firsthandover.csv，SHA256 acebf870a47941451ab4936d5ac56cfc31f0d4a53d6e06483c5b0d124837ba71。
- 全程 trace SHA256 b73fa3dba8eee242f5125d307ed614310ea21ccb6d32f803d8cd36c06c8db366。四个 MISO 信道包 manifest 均绑定正确 trace；DL 4Tx×1Rx，UL 1Tx×4Rx。
- 数值核验：全程 621 点，8200–8820 秒；短测 71 点，8200–8270 秒；均为 1 秒步长，所有数值有限，信道包 times.f64 与对应 trace 时间列逐点完全相同。

验证命令：
```text
python .planning/handover-tail-review-20261018/audit_stk_sources.py
python .planning/handover-tail-review-20261018/verify_stk_content.py
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_run_trace.py
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_stk_sources.sh
```
最后一条在 Linux 候选内执行 bash local_ntn/run_regressions.sh，trace 解析、切换表、IQ ASan/UBSan 等回归通过，整体退出码 0。首次外层日志显示命令因末行 CRLF 失败，已修正验证脚本换行并重跑通过。证据见 .planning/handover-tail-review-20261018/stk-source-audit.json 及 Linux .runtime/stk-source-regressions-20261020.log。

本次未替换业务输入、未改变天线模型或验收标准；仅补充审计脚本和来源说明。输入来源核验通过不代表业务验收通过：最新短测 wall=228.137782151 秒、numeric_audit_ok=true，仍未达到 5 秒及时性标准，尚未完成合并提交。
## 2026-10-20：八样本 SIMD 性能与数值验证

修改 quadriga/oai/qd_channel_adapter.c：已有构建启用 AVX-512 时一次处理八个相邻样本，AVX2 构建保持四个。逐样本时间、线性复系数/时延插值、12 点 Lagrange、浮点系数转换、路径累加顺序不变。未改变 STK 输入、功率、信道抽头、MISO 端口、墙钟业务负载或 5 秒期限。

修改 quadriga/tests/qd_rfsim_adapter_test.c：35 样本增至67，确保8线程分片也能运行8样本向量；补充8/9/63/64/65边界。原阈值不变。Windows候选与Linux源码/运行overlay同步。

四轮交错微基准（wide-benchmark.json）：8线程 DL 中位数0.225535→0.2036945秒（减少9.68%）；UL0.4181265→0.3934065秒（减少5.91%）。1线程减少约22–23%。这是固定输入卷积微基准，不代表端到端业务收益。

独立等相位诊断（equal-phase-audit.json）：25–55IQ秒、五个频点，单位范数等相位波束的功率/最优波束功率最低0.9999224247，未发现明显四子阵相消。此检查不声称测量了实际 OAI PMI。

命令 `wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_wide_simd.sh` 退出0：增量构建、规定trace/IQ回归、四组实际MISO数据独立ASan/UBSan数值验证、完整scripts/test.sh均通过。随后使用 run_miso_wide_simd.sh 启动 miso-first-20261020-wide-simd；最终业务结果另行记录。
## 2026-10-20：多接收端口精确旋转缓存

修改 oai_patch/current/radio/rfsimulator/apply_channelmod.c：对多Rx调用缓存同一块的sin/cos结果。仅当样本数、归一化起始double相位和频偏增量精确相等时复用；容量16384样本，超限回退。保留原逐样本double累加、float相位写回、信号旋转和随机噪声调用顺序，不使用递推近似。缓存为线程局部，每个调用线程约256KiB；不改变公共API、信道或验收口径。

修改 local_ntn/test_real_iq.c：增加四端口命中、初相变化、频偏变化和67/7680/16384/16385样本边界。486192个新增样本对照原cexp参考，连同原1005个样本最大float输出误差0，最终相位精确相等。Windows候选、Linux源码和运行overlay均同步。

验证命令（项目根目录）：
```text
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_phase_cache.sh
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/run_miso_phase_cache.sh
```
首条退出0：增量构建、trace/IQ与ASan/UBSan、core10项和driver24项通过。本轮未重复完整scripts/test.sh，前一轮八样本实现完整套件已通过。本次没有修改FIR。

真实短测 miso-first-20261020-phase-cache：70IQ秒用179.179317552墙钟秒，较wide-simd的204.025110544秒减少12.18%。gNB相同2088960000样本后处理由63.1869秒降至41.1911秒，FIR约99.12秒；支持收益来自消除重复三角函数。单次对照，不宣称统计显著。

- Ping 145/145收到，6包超5秒（4.1379%），最大7.0832秒；切换窗口失败24%。
- UL 1845/1845收到，0超时，最大4.1032秒。
- DL 1836/1843收到，7包缺失计入期限失败（0.3798%），已收到包最大3.6514秒。
- UL/DL切换窗口期限失败均0；两方向UDP本次通过，但有DL丢包，不是零丢包。
- numeric_audit_ok=true，PBCH/RRC IDLE/reaccess均0，stop_exit=0，专属核心网已关闭。
- 总passed=false，仅全程/窗口Ping及时性两项失败；脚本exit1是验收失败而非驱动异常。
- 独立空间审计确认DL4Tx1Rx/UL1Tx4Rx、八线程与四个有效Tx；总状态随业务false，exit1。

摘要：.planning/handover-tail-review-20261018/phase-cache-summary.json、phase-cache-profile.json。未启动620秒MISO全程，未完成合并提交或推送。

后续方案（尚未实施）：
1. 优先定位Ping请求/回复在UL、DL、RLC/PDCP和主机调度的排队贡献，结合切换CRC重传再决定修复位置；保留5秒RTT口径，不能拿UDP单向通过替代。
2. 多Rx批量卷积与任务分发：共享可证明相同的时间轴和快照索引，合并四次线程唤醒；每端口独立系数、时延、输出与噪声仍保留。涉及更广的RFsim接口改造，需先设计评审和单独数值对照。
3. 同代码同数据在更充足的CPU资源/原生Linux执行环境做对照，测量每IQ秒墙钟耗时与尾延迟；不预先保证通过，不自动改变部署环境。
不建议将降低墙钟负载、延长期限或修改STK切换轨迹当作本次修复；这些会改变用户指定的实验口径。
## 2026-10-20：四接收端口批量卷积

用户授权按既定顺序持续优化，保持原实验口径。对迟到Ping的已有事件分析显示：最大RTT=7.083秒，邻近UDP上行3.679秒、随后下行3.408秒，和为7.087秒。其余5个迟到包也与队列叠加吻合。该分析是时间关联，并非ICMP逐跳时间戳，证据为ping-queue-correlation.json。

实现：
- quadriga/oai/qd_channel_adapter.c：新增内部qd_channel_convolve_all，展平Rx×样本一次分派线程，跨端口分片仍调用同一逐样本滤波函数；旧单Rx入口保留。整数溢出/零长度边界检查保留。
- oai_patch/current/radio/rfsimulator/{rfsimulator.h,apply_channelmod.c,simulator.cpp}：新增内部rxAddInputs，RFsim四Rx一次卷积后按原Rx顺序进行增益、旋转及随机噪声处理。SISO与非QD保留旧路径。QDBATCH独立记录批量FIR时间，不能将移出QDPROFILE的时间误当作收益。
- quadriga/tests/qd_rfsim_adapter_test.c：批量输出与独立逐点参考比较，覆盖非整批长度、跨端口边界、越界静音及输出尾部哨兵。
- local_ntn/test_real_iq.c：真实入口原/批量输出对比，并添加非零确定性噪声序列与调用数检查。
- quadriga/tests/test_rfsim_history.py：补齐抽取式历史测试的批量入口桩，原历史/前看断言不变。

验证命令：
```text
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_batch_rx.sh
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/check_batch_rx_resume.sh
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/synching_study/jingwenpeng/2026autumn/ntn-oai-project/.planning/handover-tail-review-20261018/run_miso_batch_rx.sh
```
首轮构建、trace/IQ和四组实际数据ASan/UBSan通过，全套因history夹具缺入口桩失败；补桩后第二条退出0，trace/IQ及完整scripts/test.sh通过。全程DL/UL各1241节点/中点、短程各141节点/中点全覆盖，最大误差2.55e-11；未放宽阈值。批量微基准上行0.206518秒，checksum1111207.14208与原实现相同；仅单次微基准，真实业务另行验证。

短测 miso-first-20261020-batch-rx：70IQ秒，138.1815834墙钟秒，passed=true，所有全程/切换窗口的原及时性验收通过，空间审计true，stop0，核心网已关闭。
- Ping110/110，超时0，最大RTT2.3288秒。
- UL1398/1398，超时0，最大1.6713秒。
- DL1393/1397，4个缺包计入期限失败0.2863%，已收包最大0.9913秒。
- 三种业务切换窗口期限失败均0；numeric_audit_ok=true，PBCH/RRC IDLE/reaccess均0。

当前已通过短测门禁启动run_miso_batch_full.sh，运行miso-full-20261020-batch-rx，全程620IQ秒；结果尚待完成。未完成合并提交或推送。
## 复现实验命令（Linux）

将以下命令保存为脚本，在项目根目录用具有实验所需网络命名空间及 Docker 权限的 bash 执行。每次使用新的 run_id；当前通过的短测使用8线程，默认1线程不能视为同一性能配置。保持日志观测开关与本次验收一致。

```bash
set -euo pipefail
source scripts/env_handover_miso4.sh
export OAI_QD_WORKERS=8 OAI_QD_PROFILE=1
export OAI_NTN_TIMING_DIAG=1 OAI_NTN_TIMING_DIAG_START_IQ_S=0
export OAI_NTN_PUSCH_FAILURE_THRES=100 OAI_NTN_PDCP_REORDERING_MS=500
export OAI_NTN_CELL_KOFFSET_MS=80 OAI_RNGSEED=20260925
run_id=miso-full-reproduce-001
python3 scripts/core_lab.py up --profile integrated-handover --run-id "$run_id"
trap 'python3 scripts/core_lab.py down --profile integrated-handover --run-id "$run_id"' EXIT
python3 scripts/handover_acceptance.py --case full --profile integrated-handover \
  --run-id "$run_id" --max-wall-seconds 10800
python3 scripts/audit_handover_spatial.py \
  ".runtime/runs/integrated-handover/$run_id/run.json" \
  ".runtime/runs/integrated-handover/$run_id/acceptance/report.json" \
  --output ".runtime/runs/integrated-handover/$run_id/acceptance/spatial-audit.json"
```

先做短测时将 case 改为 firsthandover 并使用另一个run_id。max-wall-seconds只是驱动等待上限，不修改5秒业务期限。最终必须同时检查业务passed、numeric_audit_ok、空间审计及清理退出状态。

合并前一致性核验：35个覆盖源码在工作区与运行清单哈希一致；暂存后33个逐字节一致，两个CMakeLists.txt仅被Git按文本属性将CRLF规范化为LF，内容无其他差异。273个暂存路径不含.private/.runtime，候选无未跟踪文件，工作区无冲突标记；git diff --cached --check通过。主工作区原有三份文档改动未触碰。
