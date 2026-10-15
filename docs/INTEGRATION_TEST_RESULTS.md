# 整合测试结果（验收进行中）

候选保护代码 7f40221（最终pre-live补充验证）；Task7审阅通过基点49a353f26e2304dca8acde9e1da1a875860c6a96。
此文档保留初期离线检查点，并追加真实运行结果；最终验收与原平台业务后测尚未完成，不代表发布完成。

| 测试 | 实际结果 |
| --- | --- |
| Task8缺checker接口，RED5ed95c8 | exit1，模块不存在 |
| 初版保护边界06f5be2 | 17 tests PASS；range diffcheck exit1，EOF空白 |
| 真实staged-only同status内容改动，RED72114cf | 19 collected，1 FAIL；缺dirty内容指纹 |
| staged/unstaged/index修复fdd0f42 | 19 tests PASS、compile/range diffcheck exit0 |
| 原launcher早退state归属，RED76a58ef | 21 collected，2 ERROR；缺claim_state |
| 精确state恢复3f8e96c | 21 tests PASS，含真实SIGTERM私有Python会话清理/无关会话保留 |
| 既有run_state/network_owner/core_lab | 12 /10 /6 tests PASS |
| static / firsthandover / legacy / full | 后续实际结果见下；尚未全部通过 |
| 原平台最终parser/IQ与短跑 | parser/IQ 已通过；最终业务短跑待执行 |
| 最终全分支独立审阅/远程push | 未完成 |

实际GREEN命令，在独立Linux克隆中set-e串行执行，aggregate exit0：

~~~bash
python3 scripts/test_original_platform_check.py
python3 local_ntn/test_run_state.py
python3 local_ntn/test_network_owner.py
python3 scripts/test_core_lab.py
python3 -m py_compile scripts/original_platform_check.py
git diff --check 49a353f26e2304dca8acde9e1da1a875860c6a96 HEAD
~~~

## 整合前原短跑与保护证据范围

2026-10-12实际前测：rate1、原1387行7614–9000 trace；ping30/30，
UL/DL UDP各0/130丢失，各命令exit0。七项trace、模板、原binary的真实before/after SHA256与mtime相同。
原ignored gnb.local.conf和initial_delay_ms.txt由既有launcher再生成，其旧字节恢复没有被证明。

纠正原baseline报告：private before.json的Git HEAD/status字段实际包含dubious ownership错误文本。
这些文本相等不能证明完整源码HEAD/dirty集合未变；原始before.json保留不修改。
原sources.lock在2026-09-22提交cb60f035c3968077d0c8a4b505ea9640bf99d279已记录
OAI c4125d1c74和5GC212f92f，当前成功checked Git查询与之相符。
当前32/13个dirty/untracked普通文件mtime均早于前测只能作为辅助证据，
没有可靠Task1前完整dirty集合及内容hash快照。

Task8新的成功快照将明确标时点，覆盖随后live阶段源码status、dirty文件hash、index摘要、
七项文件、容器ID/labels/running和网络身份；它不补造此前缺失证据。
真实四case结果、命令/退出码、time precision/workload/two windows及原最终复验应在执行后追加；
所有失败记录保留，只有验收与保护审阅全部通过才允许新分支push。
最终pre-live checkpoint：7f40221。23项阶段又观察到容器归属RED d23a5b9 exit1：
失败start后同ID被外部启动，旧实现错误调用stop。5b0b09f只在精确start成功ID确认且
StartedAt处于本次命令区间时登记，未知partial保留失败；cleanup还匹配owned StartedAt，
外部同ID重启拒绝停止。7f40221补充成功/区间外启动/外部重启三场景验证。
最终24保护tests、run_state12、network_owner10、core_lab6、compile及全范围diffcheck aggregate exit0。
真实private Python子会话SIGTERM停止与无关会话保留通过；这不是任何modem或业务live测试。

## 2026-10-13 实际运行与当前失败

物理时钟启动修复候选 `96a5aea` 的 static 90 IQ 秒实测通过：ping 104/104，
UL UDP 1323/1323，DL UDP 1318/1322（0.30% 丢失）；业务区间为 IQ
19.6223–85.016 秒，PBCH 错误和重接入为 0，QD 双侧各加载一次，停止与清理成功。
这是该候选的实测结果，不能替代后续接收端修改的重新验收。

PRACH 中心搜索候选 `a438f5c9b2f44dee14772ae0dd93783f18e00eb9`：实际生产
波形生成、提取与解码 200 场景通过，其中 66 项明确正确前导真值检查、24 项正时延
TA 单位检查。测试范围和边界详见 `prach-centered-search.md`；不是任意时延的保证。
五目标实际构建、parser/IQ 回归、完整离线回归及独立范围审查通过。

同一候选运行命令：

~~~bash
python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover --run-id task8-first-20261013c --max-wall-seconds 3600
~~~

**实际退出码 1，验收失败，保留记录。** 初始 PDU 已建立，持续业务覆盖 IQ
18.932923–64.425199 秒；物理观测完整覆盖 70 IQ 秒。首次切换 STK
8239–8249 秒窗口完整，但 ping 0/14，UL UDP 5/172，DL UDP 5/173：
窗口丢失率分别为 100%、97.11%、97.13%。全程 ping 50/64，UL 636/806，
DL 633/805；验收观测内 PBCH 错误 314、PHY 重接入 5。双侧 QD 各加载一次，
停止退出码 0、清理无错误。不得把完整覆盖或成功接入解释为切换验收通过。

接收跟踪诊断仍是待验证假说：真实时延在切换阶段每秒下降约 1144–1229 微秒，
每 10 ms 移动约 88–94 个采样，现有定时搜索约 ±36 个采样。首次 PBCH 错误
位于实际时钟括号 IQ [38.93355, 39.03355]，不是精确的错误时间戳。
候选修复必须从接收信号测量，不能通过模型真值补偿、重置时钟或放宽验收阈值通过。

`cacc0eb` 仅修正 RTT 图显示：收到的 ICMP 样本画为独立点，丢包空缺不连接曲线；
原失败数据、统计和验收结果不变。

原平台实际回归从原工作目录执行，所有命令退出码 0；编译产物和日志只存新平台
私有目录，不写原构建树：

~~~bash
cc -Wall -Wextra -Werror -I local_ntn local_ntn/test_trace.c local_ntn/stk_trace.c -lm -o /home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/task8-20261013/original-parser-iq-current/test_trace
/home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/task8-20261013/original-parser-iq-current/test_trace
PYTHONDONTWRITEBYTECODE=1 python3 local_ntn/test_trace_validation.py
PYTHONDONTWRITEBYTECODE=1 python3 local_ntn/test_real_iq.py
~~~

最终原平台业务后测、完整保护对比、四组新平台验收和全分支独立审查仍待完成。
## 2026-10-14 接收端候选实测（整合验收尚未完成）

`acb576ab0b40931fc3cc2ee3f43051a5b01b165e` 的独立源树正式构建六个目标
`nr-softmodem nr-uesoftmodem rfsimulator params_libconfig nr_prachsim nr_pbchsim`
（`cmake --build .runtime/oai/cmake_targets/ran_build/build --target ... -j 6`）
完成 391/391 步，退出码 0。`bash local_ntn/run_regressions.sh` 与
`bash scripts/test.sh` 均退出 0；实际接收 IQ 28 场景独立重跑及范围审查通过。
部署源树是经过归档校验与覆盖文件校验的 `verified_archive`，固定 OAI commit
`1e0c78bfbb80424f275e73a3103f582e0f903413`；没有声称它存在自身 Git HEAD。
实际验证了 27 项覆盖文件与六个二进制的 SHA256，私有证明保留。

~~~bash
python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover --run-id task8-first-20261014a --max-wall-seconds 3600
python3 scripts/handover_acceptance.py --case static --profile integrated-handover --run-id task8-static-20261014b --max-wall-seconds 3600
~~~

首次切换命令实际退出 1。业务覆盖 IQ 18.976925–65.009187 秒；物理观测双侧
覆盖 70 秒，QD 双侧各加载一次，idle/reaccess 为 0，停止与清理成功。全程
Ping 78/78，UL 983/983，DL 979/983（0.407% 最终丢失）。切换窗口 Ping
16/16、UL 209/209、DL 210/210 是**最终交付**，不是及时交付：窗口平均
Ping RTT 13.235 秒，上行约 9 IQ 秒无包到达，随后出现积压包集中到达。
窗口 Ping、UL、DL 延迟 p95 分别约 19.877、16.135、6.274 秒（墙钟）。
这些持续业务数据明确显示物理切换的业务影响，不能宣称运行正常或切换验收通过。

脚本报告 PBCH 错误 10，停止后的完整私有日志实际共有 29；所有错误都集中在
短轨迹末界附近，首次错误的现有时钟括号 [69.954093,70.055021] 跨越 IQ70。
现有脚本未按错误的原生输入样本归属测试区间，且停止后未读完日志，不能据此
直接删掉错误。新增诊断将记录真实输入样本跨度；跨边界或时间未知仍判失败，
原失败报告保留。业务验收还将保留最终丢包事实，独立检查现有五秒墙钟期限的
及时交付，并报告延迟分位数和接收中断，防止长时间排队被最终交付掩盖。

静态命令实际退出 0：90 IQ 秒完整覆盖，业务 IQ 20.211348–84.205 秒；Ping
89/89，平均 RTT 186.705 ms，UL 1139/1139，DL 1134/1138（0.351% 最终
丢失），PBCH/idle/reaccess 为 0。Ping 与 UL 五秒超时均为 0，DL 四个缺失
包计超时；QD 双侧各加载一次，停止与资源清理成功。这是冻结候选的静态结果，
仍不能替代最终候选的完整矩阵及原平台后测。

实际 UE 运行使用 `--cont-fo-comp 2`。源码净 residualULFo 为
`+freq_offset * fUL/fDL`（先取负，模式 2 再反转）；模式 1 净值为负，模式 3
为零。此前只依据后一条反转语句解释符号的诊断口述已撤回。上行排队归因须结合
实际频偏、时间提前和发射样本诊断，当前没有以改符号或物理模型宣称修复。

## 2026-10-14: first-switch diagnostic 14d (FAILED, preserved)

Project/source/build: 032277b9d33fdcf4cf5fb8abbe44cc7236dd6f2a; verified-archive OAI pin 1e0c78bfbb80424f275e73a3103f582e0f903413; formal-diag-harness-032 recorded six-target build, trace/parser/IQ regression and scripts/test.sh exit 0. Receiver and harness were unchanged for this case.

Command: OAI_NTN_TIMING_DIAG=1 python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover --run-id task8-firstdiag-20261014d --max-wall-seconds 3600. Exit 1, controller wall 139.115 s. All nine dedicated core containers were healthy before and after. The earlier 14c readiness failure is retained as an environment failure; it is not receiver/business evidence.

Actual RF sample rate 7.68 MHz; physical start verified on both sides; continuous business IQ interval 17.572881380208333--65.0031875 s. Global Ping 41/89 received (48 missing), UL UDP 518/1125 (607 missing), DL UDP 931/1124 (193 missing). First-switch conservative window: Ping 0/19, UL UDP 0/237, DL UDP 237/237. Timely gates also failed. No RRC idle or reaccess. No in-case PBCH failure: all 51 raw failure events were attributed beyond the closed 70-second RF case from their actual input sample spans. The first span begins at native sample 537716488, greater than the case endpoint 537600000. All events remain counted in the terminal-outside category.

Numeric diagnostics: 3426 serving-pilot events, 3375 accepted (51 terminal events rejected); 6852 actual UL-write records. All in-window pilots accepted. UL compensation is mode 2 with autonomous TA. At IQ 39--44 s, applied UL FO minus independently reconstructed physical FO at write time has one-second medians about -356, -384, -400, -421, -436 Hz. Autonomous NTN TA minus two geometric delays at write time has medians about 99, 107, 183, 196, 204 us. These are diagnostic comparisons, not the complete desired transmit-timing equation. Native arrival/frame comparisons additionally identify time misalignment during the business interruption. Physical equations were evaluated separately from controller observations; no STK truth was fed back into a receiver.

Causal offline forecast experiments are retained privately. Initial SIB TA plus only preceding accepted pilot coordinates/FO can reduce the steady lag, but linear delay extrapolation retains curvature error and naive quadratic fits produce overshoot around piecewise trace boundaries. These experiments are NOT a live PASS and are not production changes. Further receiver-derived transmit-time and boundary handling must pass actual IQ checks and fresh live acceptance before release.

Stop exit 0, cleanup error null; modem processes and isolated UE network resources absent. Read-only original-platform protection comparison against post-restart-pre-receiver.json passed with differences=[] after this run. Final original business revalidation and the four-case passing integration matrix remain outstanding. New integration branch has NOT been pushed.


### 2026-10-15 receiver-derived TX candidate, actual first-switch case

Commit 498f1ebec5d335ededbdb216af3b066ddcb63f1f was formally deployed only into the independent Linux clone. Six build targets, `bash local_ntn/run_regressions.sh`, and `bash scripts/test.sh` exited 0; proof records 28 overlay files and 6 binary hashes. The portable extracted main/prefix scheduling test and 704 math assertions passed. Existing receiver IQ cases were 28/28. Independent candidate source review found no new substantive defect; startup SIB lifecycle and final active UL-symbol IQ coverage remain incomplete.

Actual command: `OAI_NTN_TIMING_DIAG=1 python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover --run-id task8-firstdiag-20261015c --max-wall-seconds 3600`. Actual result: **FAIL**, command exit 1, report wall 106.305371s (wrapper108.367331s). Fs7680000; observed physical IQ gNB1.234..71.034, UE1.239999870..71.018117188; business19.940882682..64.670194271. Ping32/65 received (33 lost,50.7692%); uplink406/817 (411 lost,50.3060%); downlink405/816 (411 lost,50.3676%), offered~99.82kbit/s each. Window at STK8244 covered: ping4/14, UL52/178, DL53/178; conservative and timely loss gates failed. PBCH case errors0, RRC idle/reaccess0, QD loaded once on each side, numeric audit valid. Stop0, no cleanup error; owned modems/namespace/veth/owner absent afterwards.

Continuous records show business mostly delivered through IQ41s, then both directions had zero receipts from IQ42 through the send stop. gNB explicitly declared UL failure at IQ~42.034 after10 PUSCH DTX (then queued reports11..17). Its UL statistics progressed from IQ38.334:2106/2/0/0 HARQ rounds, errors0/DTX0, to IQ40.934:2459/13/7/6/errors5/DTX4, then froze at IQ42.234:2726/45/18/16/errors13/DTX21. Code marks UL failure before handling that HARQ result; this sticky state stops subsequent scheduling. The count is events, not milliseconds, and these observations do not establish the individual DTX time span or prove that RTT alone makes10 inappropriate.

Actual immutable TX diagnostics were active (first valid call321); receiver pilot FO median errors remained near0Hz. Compared with independent physical geometry at estimated future arrival, UL FO median errors were near0..-9Hz across the switch, substantially different from the older hundreds-Hz bias; extrema and TA/arrival outliers still occur near interpolation knots. These diagnostics are not a PHY PASS and no frozen report was rewritten.

New WSL boot78c6ccda required a fresh bounded keeper. The old full snapshot comparison initially failed only for containers: all10 original/foreign container records remained exactly equal, while the same9 owned integrated core IDs/labels had stopped across the restart. This was documented rather than changing the protection checker. A fresh snapshot after restarting only the owned core was used. Core9/9 healthy before and after; post-case original snapshot comparison exited0 with differences=[]; the original source/configuration/state was not modified. No remote push occurred.


### 2026-10-15 explicit DTX-count100 comparison (still FAIL)

Commit d978758a35b6f3ad16114707ef1878d265dd2be5 adds only an explicit, bounded diagnostic override, source/default behavior unchanged. The deployed OAI overlay hashes (28) and all six binary hashes are exactly equal to the formally built 498f1eb candidate. `bash local_ntn/run_regressions.sh` and `bash scripts/test.sh` both exited0 after deployment. Parameter tests (5), Bash syntax, and Windows Git diff check passed. An attempted Git check from WSL against the Windows managed worktree failed because its .git pointer contains a Windows drive path; its failure was retained, and the actual Windows Git check passed.

Actual command: `OAI_NTN_TIMING_DIAG=1 OAI_NTN_PUSCH_FAILURE_THRES=100 python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover --run-id task8-firstdiag-20261015d --max-wall-seconds 3600`. Actual result: **FAIL**, only two failure reasons: window downlink conservative loss and timely delivery exceed1%. Report wall105.194190s; wrapper107.000230s. Business IQ18.703..64.437198307. Ping65/65, uplink832/832, downlink827/832 (5 missing,0.600962%). WindowSTK8244 covered: Ping14/14, UL179/179, DL178/180 (2 missing,1.111111%). Ping mean wallRTT205.537ms; window238.692ms. Both UDP actual offered loads~99.81kbit/s. All original loss/deadline gates remained unchanged; do not label this comparison PASS or erase the default10 failure. Manifest records override100; actual gNB startup value and scheduler recovery statistics require separate verification.

This comparison supports a failure-state latch amplifying transient PHY impairment; it does not prove the PHY is fixed, nor that10 is invalid for every NTN RTT. Post-case original snapshot compare exited0/differences=[]; core9healthy before/after, stop0/no cleanup error, owned modems/network absent. PBCH case0, idle/reaccess0, QD once per side. The actual shared-axis figure was exported and visually inspected as ntn-first15d-observed-timeline.png (304877B), showing physical delay/Doppler/CN, wallRTT, cohort loss, actual arrival throughput and real-time factor on absolute STK time. Failed-case data remains private.

Additional private actual-OAI waveform diagnostic: `ntn_ul_tail_checks.py` compiled/linked actual nr_normal_prefix_mod and nr_symbol_fep_ul plus extracted original RU_write prefix/final write, all exit0. With FFT512/CP36/divisor8/NTA100 and every symbol active, stream block deltas0,-1,-4,+20 preserved all FFT inputs. Delta-20 left16 required samples missing from symbol13's FFT and normalized last-symbol error0.035663655, while symbols0..12 stayed identical. This is a diagnostic exposing truncation, NOT a validation that the candidate's actual variable-length stream is always safe. Only mu0/one isolated slot is covered so far; adjacent-slot RF ring, actual main-generated block sequences and RFsim read-held delay still need extension. No OAI source/binary or runtime policy changed for this test.


### 2026-10-15 fixed-noise-seed pair and PDCP evidence

The earlier15c/15d comparison did NOT fix actual OAI noise seeds; it is observational evidence, not a fully controlled noise comparison.15d actual gNB/UE seeds were9461786867769420245/12840016405660019649, despite offline QuaDRiGa's fixed seed. gNB startup confirmed PUSCH Failure100/PUCCH Failure10. After damage, cumulative DTX stopped at84 while successful UL LCID4 bytes rose543907->619270; this confirms recovery without equating the cumulative DTX count to a live consecutive counter.

Before further outcomes were known, OAI_RNGSEED20260925 was chosen from the existing documented QD seed for a new pair. Both physical modems in each run actually printed20260925. Runs use identical28 OAI overlays and6 binary hashes, d978758 project/scripts, same trace/rate/QD and business gates; host scheduling/startup and wall-time traffic phases are still observed variables, not bitwise-replay guarantees.

| Run | Explicit DTX | Ping received/sent | UL received/sent | DL received/sent | Result |
| --- | --- | --- | --- | --- | --- |
| task8-firstdiag-20261015e | 10 | 35/78 | 441/988 | 460/987 | **FAIL** |

task8-firstdiag-20261015e: wall124.523117s; businessIQ[19.0499265625, 65.043]; failures: global ping conservative loss exceeds1%, global ping timely delivery exceeds1%, global uplink conservative loss exceeds1%, global uplink timely delivery exceeds1%, global downlink conservative loss exceeds1%, global downlink timely delivery exceeds1%, window ping conservative loss exceeds1%, window ping timely delivery exceeds1%, window uplink conservative loss exceeds1%, window uplink timely delivery exceeds1%, window downlink conservative loss exceeds1%, window downlink timely delivery exceeds1%.
Window8244: ping0/17, UL0/207, DL21/208. Mean wallRTT global/window 213.5412610285714/Nonems. Stop0, PBCHcase0, idle0, reaccess0; original compare passed/differences=[] and core9healthy.
| task8-firstdiag-20261015f | 100 | 87/88 | 1113/1118 | 1110/1117 | **FAIL** |

task8-firstdiag-20261015f: wall138.442030s; businessIQ[19.397937630208332, 65.03018671875]; failures: global ping conservative loss exceeds1%, global ping timely delivery exceeds1%, global uplink timely delivery exceeds1%, window ping conservative loss exceeds1%, window ping timely delivery exceeds1%, window uplink conservative loss exceeds1%, window uplink timely delivery exceeds1%.
Window8244: ping20/21, UL262/267, DL267/268. Mean wallRTT global/window 1113.1902941839082/4018.6781231500004ms. Stop0, PBCHcase0, idle0, reaccess0; original compare passed/differences=[] and core9healthy.

Neither count100 nor the fixed seed is a complete PHY fix. Source+configuration show DL/UL MCS already limited to9, DRB AM, RLC maxRetx32/poll45ms/reassembly15ms/statusProhibit15ms, PDCP discard infinity and reordering100ms.15d UE showed old-COUNT discards423<427 and442<444 with list0 near observed DL IQ40.120/41.129; these are direct late-count discards, not proven mappings to the two UDP losses. No observed max-retrans/integrity-discard warnings. Default INFO does not expose reorder-expiry or actual timer values.

Native finite PDCP timer comparison was added explicitly, default unchanged. Only gNB receives --pdcp.drb.t_reordering ms500; source mapping config_pdcp -> DRB.pdcp_config -> ASN encode -> UE decode/new entity establishes both-end configuration. It must not be added to UE CLI, where support was not established. The pending trial is not a claim that500ms improves business or PHY.
