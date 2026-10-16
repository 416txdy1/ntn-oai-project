# 整合测试结果

候选保护代码 7f40221（最终pre-live补充验证）；Task7审阅通过基点49a353f26e2304dca8acde9e1da1a875860c6a96。
此文档先保留初期检查点，再按时间追加真实结果。2026-10-16最终五轮验收与原平台业务复验结果见文末；历史失败和保护证据范围继续保留。

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
| task8-firstdiag-20261015f | 100 | 87/88 | 1113/1118 | 1110/1117 | **FAIL** |

task8-firstdiag-20261015e: wall124.523117s; businessIQ[19.0499265625, 65.043]; failures: global ping conservative loss exceeds1%, global ping timely delivery exceeds1%, global uplink conservative loss exceeds1%, global uplink timely delivery exceeds1%, global downlink conservative loss exceeds1%, global downlink timely delivery exceeds1%, window ping conservative loss exceeds1%, window ping timely delivery exceeds1%, window uplink conservative loss exceeds1%, window uplink timely delivery exceeds1%, window downlink conservative loss exceeds1%, window downlink timely delivery exceeds1%.
Window8244: ping0/17, UL0/207, DL21/208. Mean wallRTT global/window 213.5412610285714/Nonems. Stop0, PBCHcase0, idle0, reaccess0; original compare passed/differences=[] and core9healthy.

task8-firstdiag-20261015f: wall138.442030s; businessIQ[19.397937630208332, 65.03018671875]; failures: global ping conservative loss exceeds1%, global ping timely delivery exceeds1%, global uplink timely delivery exceeds1%, window ping conservative loss exceeds1%, window ping timely delivery exceeds1%, window uplink conservative loss exceeds1%, window uplink timely delivery exceeds1%.
Window8244: ping20/21, UL262/267, DL267/268. Mean wallRTT global/window 1113.1902941839082/4018.6781231500004ms. Stop0, PBCHcase0, idle0, reaccess0; original compare passed/differences=[] and core9healthy.

Neither count100 nor the fixed seed is a complete PHY fix. Source+configuration show DL/UL MCS already limited to9, DRB AM, RLC maxRetx32/poll45ms/reassembly15ms/statusProhibit15ms, PDCP discard infinity and reordering100ms.15d UE showed old-COUNT discards423<427 and442<444 with list0 near observed DL IQ40.120/41.129; these are direct late-count discards, not proven mappings to the two UDP losses. No observed max-retrans/integrity-discard warnings. Default INFO does not expose reorder-expiry or actual timer values.

Native finite PDCP timer comparison was added explicitly, default unchanged. Only gNB receives --pdcp.drb.t_reordering ms500; source mapping config_pdcp -> DRB.pdcp_config -> ASN encode -> UE decode/new entity establishes both-end configuration. It must not be added to UE CLI, where support was not established. The pending trial is not a claim that500ms improves business or PHY.


### 2026-10-15 first handover diagnostic 15g (not accepted)

Commit cc8a34ab, unchanged 498f1eb OAI overlays/binaries; explicit PUSCH failure
threshold 100, PDCP reordering 500 ms, modem seed 20260925. Continuous Ping
71/72, UL 903/912, DL 907/911. Switch window Ping 15/16 (mean RTT 7274.607 ms),
UL 182/191, DL 194/194. Overall acceptance FAILED on Ping/UL loss and timely
delivery. Original protection comparison passed; nine dedicated core containers
healthy before/after, owned modem/network cleanup passed. Timer changes do not
establish a physical-channel fix.

Next explicit diagnostic: OAI_NTN_CELL_KOFFSET_MS=48, only isolated generated
gNB configuration. Unset remains 80; zky ignores the override. Current launcher
is mu=0. Full-trace max geometric RTT is 42.956593 ms; nominal lead 3+48-RTT
is at least 8.043407 ms (mathematical minimum K for a 5 ms nominal margin: 45).
This is an endpoint bound for legacy-linear geometry, not an actual write-lead
guarantee: ordinary TA, NTA, clipping and prediction errors also affect writes.
Physical and continuous business acceptance gates remain unchanged.


### 2026-10-15 matrix at 80fdbd9 and startup-coverage correction

Same 498f1eb OAI overlays/binaries, explicit PUSCH threshold100, PDCP500ms,
K80 and OAI seed20260925. Earlier same-configuration failures remain valid;
one short PASS is not a robustness guarantee.

| Case/run | Result | Ping received/sent | UL received/sent | DL received/sent |
| --- | --- | --- | --- | --- |
| first/task8-firstdiag-20261015k | PASS | 86/86 | 1093/1093 | 1089/1092 |
| static/task8-static-20261015l | PASS | 111/111 | 1415/1415 | 1409/1413 |
| full/task8-full-20261015m | FAIL | 1093/1093 | 13964/13964 | 13957/13962 |
| legacy/task8-legacy-20261015n | FAIL | 352/352 | 4485/4485 | 4484/4484 |


task8-firstdiag-20261015k: wall 143.748653s; business IQ [21.33199752604167, 65.025]; PDU observed IQ 4.731490, confirmed business IQ 21.632007. Failures: none.
Window 8244: ping 19/19, late/deadline failures 0 definite + 0 boundary, max observed wall latency 3731.39558ms; uplink 245/245, late/deadline failures 0 definite + 0 boundary, max observed wall latency 3135.364914ms; downlink 244/244, late/deadline failures 0 definite + 0 boundary, max observed wall latency 997.084143ms; 
Case PBCH0, idle/reaccess0, numeric audit passed, stop0/no cleanup error; core9healthy and original compare0/differences=[].

task8-static-20261015l: wall 159.558253s; business IQ [20.784348307291665, 85.078]; PDU observed IQ 4.578000, confirmed business IQ 20.984348. Failures: none.
Case PBCH0, idle/reaccess0, numeric audit passed, stop0/no cleanup error; core9healthy and original compare0/differences=[].

task8-full-20261015m: wall 1172.125881s; business IQ [19.0419265625, 615.035]; PDU observed IQ 4.441482, confirmed business IQ 19.241933. Failures: window ping timely delivery exceeds1%; window uplink timely delivery exceeds1%; window ping timely delivery exceeds1%.
Window 8244: ping 18/18, late/deadline failures 6 definite + 0 boundary, max observed wall latency 5717.276857ms; uplink 222/222, late/deadline failures 5 definite + 0 boundary, max observed wall latency 5091.280193ms; downlink 223/223, late/deadline failures 0 definite + 0 boundary, max observed wall latency 1003.824929ms; 
Window 8799: ping 19/19, late/deadline failures 2 definite + 0 boundary, max observed wall latency 5190.085797ms; uplink 235/235, late/deadline failures 0 definite + 0 boundary, max observed wall latency 3405.229012ms; downlink 235/235, late/deadline failures 0 definite + 0 boundary, max observed wall latency 2346.709328ms; 
Case PBCH0, idle/reaccess0, numeric audit passed, stop0/no cleanup error; core9healthy and original compare0/differences=[].

task8-legacy-20261015n: wall 420.839559s; business IQ [62.25624075520833, 607.530021875]; PDU observed IQ 4.547485, confirmed business IQ 62.441000. Failures: business not ready before first window; incomplete switch window; window ping has no certain matched senders; window ping conservative loss exceeds1%; window ping unresolved timely evidence; window ping unsubstantiated timely bound; window ping timely delivery exceeds1%; window ping unsubstantiated loss bound; window uplink has no certain matched senders; window uplink conservative loss exceeds1%; window uplink unresolved timely evidence; window uplink unsubstantiated timely bound; window uplink timely delivery exceeds1%; window uplink unsubstantiated loss bound; window downlink has no certain matched senders; window downlink conservative loss exceeds1%; window downlink unresolved timely evidence; window downlink unsubstantiated timely bound; window downlink timely delivery exceeds1%; window downlink unsubstantiated loss bound.
Window 8244: ping 0/0, late/deadline failures 0 definite + 0 boundary, max observed wall latency Nonems; uplink 0/0, late/deadline failures 0 definite + 0 boundary, max observed wall latency Nonems; downlink 0/0, late/deadline failures 0 definite + 0 boundary, max observed wall latency Nonems; 
Window 8799: ping 7/7, late/deadline failures 0 definite + 0 boundary, max observed wall latency 360.746495ms; uplink 83/83, late/deadline failures 0 definite + 0 boundary, max observed wall latency 342.669497ms; downlink 84/84, late/deadline failures 0 definite + 0 boundary, max observed wall latency 215.997861ms; 
Case PBCH0, idle/reaccess0, numeric audit passed, stop0/no cleanup error; core9healthy and original compare0/differences=[].

K48 diagnostics h/i both failed business readiness at39IQ before any PDU,
received SIB1 but no SIB2/SIB19/PRACH. Geometry budget passes, actual startup does
not. Readonly source review found no proven K-before-SIB cycle or UL ring OOB;
INFO evidence cannot distinguish missing other-SI TX/monitor/DCI. Do not promote48.
K80 configs g/k are byte-identical; h/i byte-identical and differ only by K.

Important whole-branch review finding: PDU-to-first-business coverage was absent
for about15-17IQ seconds in integrated cases, and longer in faster legacy replay.
The old reports expose the true business interval and do not fabricate packets,
but cannot support a claim of continuous business from earliest PDU availability.
CoreLab.inventory spawned one Docker inspect per container/network twice after
PDU. The correction batches each full inventory, requires exact unique query/
returned ID sets, preserves both complete preflights and all ownership/conflict/
namespace/route/SNAT checks, and adds per-direction PDU-to-first-send/first-receipt
wall durations plus both channels' actual IQ/STK bracketing bounds. New actual
runs must measure the improvement; no coverage or radio PASS is inferred.

The first70 actual shared-axis plot was visually checked. RTT peaked near3.5s
and UL arrival throughput dipped/recovered during the physical transition.
Full15m still FAILED the unchanged5s service deadline despite eventual receipt.
No remote push or completed integration release is established.


### 2026-10-15 startup fix actual result and fast-replay drain correction

bc8c831 passed full offline regressions with the same28 OAI overlays/6 binaries.
Fresh15o first70 PASS: Ping84/84, UL1075/1075, DL1071/1074; no case PBCH/idle/
reaccess, numeric audit good, stop0, core9healthy, original compare0/differences[].
PDU observed4.319478IQ; common business7.019560IQ and confirmed7.219565IQ.
PDU-to-firstSend wall seconds Ping3.830307/UL3.742226/DL3.805513; respective UE
IQ estimates2.633126/2.575431/2.616412, both channel bounds retained. This fixes
unnecessary serial Docker overhead, not a claim of zero startup unavailability.
Max received latency Ping1741.556ms/UL1964.377ms/DL409.151ms.

Independent actual archive-base audit:3740 base files checked, excluding28
recorded overlays; missing/mismatches/extra source files all empty. This
supplements runtime source_identity, which normally checks archive+overlays.

Fresh legacy15r failed before the second window at IQ590.8: measured replay
factor~2.3 made the former preferred8wall-second tail reserve conflict with
the620IQ case end. The driver rejected before measuring that window. It is
not a PHY/late-packet result or a successful full case. Owned cleanup0,
core9healthy and original compare0/differences[].

The bounded observation correction retains the complete final window, then
stops traffic at max(windowEnd+0.3IQ,caseEnd-preferredReserve), targeting at least
5IQ before case end. If the required window itself leaves no such target,
it still rejects. Actual stop brackets and remaining IQ ranges are reported;
loop overshoot is not disguised as guaranteed margin. The fixed6wall drain
starts from the actual stop timestamp and may be clock-observed beyond the
case620 boundary. No new trace states, extrapolation, additional post-stop
traffic, loss gate or5wall deadline changes are introduced. Late/missing/
unresolved evidence remains failing; extra-tail RRC observations still count
conservatively. A5.1s receipt remains late even when observed after case end.
These changes require fresh actual validation and do not alter old outcomes.


### 2026-10-15 clean-core legacy15z and second-switch diagnostics

71880c legacy15x failed when uplink sender returned Errno101 after361 successful
sends; repeated PDU establishment was observed. The dedicated nine core
containers were then stopped/started by exact IDs/labels/owner with persistent
volumes retained. All nine became healthy; original snapshot comparison passed.
This was an isolated diagnostic reset, not proof of a stale-session root cause.

Clean-core legacy15z completed full620IQ and both windows but FAILED original
business gates: Ping228/231, UL2934/2953, DL2952/2952. First window Ping3/3,
UL49/49, DL49/49. Second window Ping1/4, UL36/52, DL52/52. Case PBCH/idle/
reaccess0, one PDU acceptance, no worker crash; independent numeric audit good,
stop0, core9healthy and original compare0/differences[]. Thus the bounded tail
correction reaches both windows; it does not conceal real UL loss/late delivery.

gNB numeric stats show first-switch recovery by~46IQ (DTX48/errors11), whereas
second-switch cumulative CRC errors grow12 at595.181IQ to1332 at615.581IQ;
DTX only50->87 and stops increasing after600. SNR remains roughly14–17dB.
No PUSCH sticky-UL-failure warning was observed. This warrants late-run timing/
FO investigation rather than declaring QuaDRiGa or the five-second gate at fault.

Optional diagnostic OAI_NTN_TIMING_DIAG_START_IQ_S accepts0..620 in isolated
profiles (default0; zky ignores it). It delays ONLY bounded PSS/UL numeric logging
using actual RF sample clocks, allowing start580 to observe the second switch
without enlarging existing4000-PSS/70000-UL-call limits. Compensation main block
is byte-identical; accepted observations, prediction and writes remain ungated.
TX diagnostic records additionally retain immutable job ordinary TA, previous/
current NTA and clock offset, avoiding inference from later mutable UE values.
Actual C parser/window tests include boundary samples above2^32 and invalid
inputs. A new formal build/regression and actual late diagnostic remain required.


### 2026-10-15 late-window diagnostic at e3ed4b9

Source/binary proof: `.private/task8-20261013/late-diag16a-formal-20261015/source-and-binary-proof.json`.
`cmake --build ...` all six targets exit 0 (36.951 s),
`bash local_ntn/run_regressions.sh` exit 0 (9.786 s),
`bash scripts/test.sh` exit 0 (87.053 s). The diagnostic window changes logging
only; PHY compensation calculations remain unchanged. Scoped read-only review passed.

After exact-owned nine-container fresh restart (volumes preserved), ran
`python3 scripts/handover_acceptance.py --case legacy --profile legacy-handover
--run-id task8-legacydiag-20261015aa --max-wall-seconds 3600` with timing
diagnostics enabled from IQ 580 s, PUSCH threshold 100, PDCP reordering 500 ms,
Koffset 80 ms, RNG seed 20260925. This is a diagnostic FAIL, not release evidence.
Report wall time 266.240 s; business IQ interval 14.044..604.567 s; both complete
switch windows covered. Ping 239/244, UL 3054/3113, DL 3111/3112.
First window: Ping 1/4, UL 21/52, DL 52/52. Second window: Ping 4/4,
UL 53/53, DL 53/53. Loss/timely gates failed globally and at the first window.
No case PBCH failures, RRC idle or reaccess. Cleanup exit 0, all nine isolated
core containers healthy, original-platform comparison passed with no differences.

Late diagnostic has 2111 pilot and 4225 UL-write records. Every pilot in the
580..620 analysis bins was accepted. Offline continuous full-trace geometry
comparison shows transient arrival prediction discrepancies around integer-second
trace interpolation corners; this is not exact held-callback channel/FFT proof.
The analysis omits out-of-trace values rather than freezing the last row and
uses only valid TX predictions for immutable anchor/TA comparisons. The current
result does not establish a unique failure cause: the previous full legacy
run failed at the second window, whereas this one failed at the first.
Next investigation captures the first window with unchanged compensation.
The integrated full matrix and original final business recheck remain pending;
no remote branch has been pushed.


### 2026-10-15 first-window acceptance at e3ed4b9

`python3 scripts/handover_acceptance.py --case firsthandover --profile integrated-handover
--run-id task8-firstdiag-20261015ab --max-wall-seconds 3600`, with explicit
DTX threshold100 / PDCP500 ms / Koffset80 ms / RNG20260925 / timing diagnostics1,
diagnostic start IQ0. Same source and six binary hashes as the late-window run.
After a fresh exact-owned core restart: PASS, exit0, report102.322 s,
business IQ7.672..64.405. Ping79/79, UL1006/1006, DL1003/1005; complete first
window Ping13/13, UL175/175, DL175/175. Timely and loss gates passed. QD loaded
at both endpoints; numeric audit passed; case PBCH/idle/reaccess all0.
Cleanup0, isolated core9 healthy, original comparison0/no differences.

The actual seven-panel timeline was exported and visually checked. It preserves
the startup/tail gaps, actual wall RTT and IQ-mapped physical geometry without
substituting generated business results. Native gNB counters show transient
retransmissions/errors/DTX during the physical blend despite successful business
delivery. Large intermediate receiver prediction deviations also occur in this
passing window, so those deviations alone are not a sufficient failure diagnosis.
The current static/full/legacy acceptance matrix remains pending; prior FAILs
are retained and do not become PASS because of this short-case result.


### 2026-10-15 static PASS and startup monitor repair

Current-build static case `task8-static-20261015ac`: PASS, report118.329 wall s,
business IQ7.721..83.915, physical beyond90 IQ s. Ping96/96, UL1222/1222,
DL1218/1221, measured offered rates approximately99.875 kbit/s/direction.
QD loaded once at each endpoint; numeric audit passed; no case PBCH errors,
idle or reaccess. Stop0, core9 healthy at completion, original comparison0.

Full case `task8-full-20261015ad`: FAIL during startup at2.574 wall s, before
physical channel/traffic evidence. Error `owned modem process exited`;
preserved state has UE phase=launching, original shell executable recorded.
Cleanup0 and original comparison0, all isolated core9 healthy. This is startup
monitor failure evidence, not a PHY outcome or620-second test.

Source inspection identified an observation race: run_local.sh performs
shell -> ip netns exec -> selected UE executable, while concurrent acceptance
polling required shell or selected modem even during the intermediate ip exec.
The new helper allows observation of an unchanged live PID/start identity only
while its record is launching and the launcher subprocess remains active.
The launcher still requires the exact selected executable within30 seconds;
no-IQ-progress60-second and total wall deadlines remain. Running/post-launch
observation and stop_owned retain their existing strict executable checks.
No new cleanup permission for ip, no PHY/math or acceptance-gate change.
Scoped read-only review passed. Three new tests cover intermediate exec,
dead/reused/missing identity, strict running/post-launch checks and unchanged
cleanup matching. The complete driver test on Windows had21 successful tests,
one skip and2 Linux-platform-specific errors (owner path and missing os.geteuid);
Linux validation remains authoritative and is pending for this repair.


### 2026-10-15 f2a3d27 formal Linux validation

Commit f2a3d27413a9f99d85fd51afec33b8850a7112f9. Commands and results:

```bash
python3 scripts/prepare_sources.py
cmake --build /home/kayoko/ntn-workspaces/ntn-quadriga-handover/.runtime/oai/cmake_targets/ran_build/build --target nr-softmodem nr-uesoftmodem rfsimulator params_libconfig nr_prachsim nr_pbchsim -j 6
bash local_ntn/run_regressions.sh
bash scripts/test.sh
```

All exit0. Build15.379 s; trace/parser/IQ regression9.676 s;
complete script suite87.116 s. Linux driver boundary tests24/24 passed,
including the startup-race regression; the earlier Windows platform errors
do not occur on the supported Linux runtime. Private formal proof:
`.private/task8-20261013/startup-monitor16g-formal-20261015/source-and-binary-proof.json`.
All28 OAI overlay hashes and all6 binary hashes exactly equal the e3ed4b9
proof: the observation fix did not modify PHY compensation.
Current inventory has every zky path present, vendor and FDD blobs identical;
158 unchanged zky +32 compatible extensions +13 original restorations +80 new
files, excluding the inventory document. Full current live matrix still pending.


### 2026-10-16 confirmed complete two-switch integration PASS

`python3 scripts/handover_acceptance.py --case full --profile integrated-handover
--run-id task8-full-20261015af --max-wall-seconds 3600` at f2a3d27413a9f99d85fd51afec33b8850a7112f9,
with explicit DTX100 / PDCP500 ms / Koffset80 ms / RNG20260925 / diagnostic1,
diagnostic start0: PASS, exit0, report891.411 wall s (wrapper906.248 s).
Business IQ7.040..614.270; both endpoints observed beyond622 IQ s; complete
620 IQ s case and both required switch windows covered. Ping848/848,
UL10859/10859, DL10855/10859; loss and5-wall-second timely gates all passed.
Actual offered rates UL99872.854 and DL99874.419 bit/s.
STK8244 window: Ping13/13, UL173/173, DL173/173; mean wall RTT231.597 ms.
STK8799 window: Ping14/14, UL173/173, DL173/173; mean wall RTT235.418 ms.
Global mean wall RTT186.957 ms. QD loaded once per modem; independent numeric
audit passed. Case PBCH errors0, idle0, reaccess0. Stop0, cleanup confirmed,
isolated core9 healthy at completion and original comparison0/no differences.
The actual full seven-panel timeline was exported (PNG487448 bytes) and visually
checked. These are observed results; previous failed runs remain preserved,
and a single passing run does not imply seed-independent reliability/capacity.

On resuming October16, WSL had a new boot and the bounded previous keeper had
expired. Exact-owned recovery restarted only the same nine core container IDs.
The generic before/after guard reported containers changed because its initial
snapshot had owned containers stopped. Investigation proved the only changed
fields were running/health/started_at on those exact nine IDs; foreign containers,
original sources/protected files/RF network were equal. The earlier pre-live
protection baseline compared equal after recovery. This expected recovery
transition is separately audited; the generic failed assertion is not erased.
Remaining current-commit legacy/static/first cases and final original business
recheck are still pending. No remote push.


### 2026-10-16 K80 matrix outcomes and K64 prospective diagnostic

At the same f2a3d274 source and six binary hashes, K80 legacy run
task8-legacy-20261015ag PASSED complete620 IQ s: report325.950 wall s,
business IQ14.653..604.646; Ping297/297, UL3783/3783, DL3781/3782.
First window Ping4/4 UL56/56 DL55/55; second Ping5/5 UL68/68 DL68/68.
Global mean wall RTT77.691 ms; all loss and timely gates passed. QD loads0/0,
numeric audit passed, case PBCH/idle/reaccess0; stop0/core9healthy/originalcompare0.
Its observed timeline PNG567101 bytes was exported and visually checked.

K80 static run task8-static-20261015ah PASSED90 IQ s: report184.211 wall s,
business7.729..85.029IQ; Ping155/155, UL1973/1973, DL1968/1972.
Actual offered UL99741.455/DL99742.777 bit/s; all gates/audit passed,
case PBCH/idle/reaccess0, stop0/core9healthy/originalcompare0.

K80 first run task8-first-20261015ai FAILED the unchanged Ping timely gates:
report143.873 wall s, business7.184..65.014IQ. Ping114/114, UL1448/1448,
DL1440/1447. Window Ping19/19, UL235/235, DL236/236; no window eventual loss,
but5 Ping RTTs exceeded5 wall s (5.345..5.874 s). Window UL max one-way4.705 s,
DL max1.612 s: the round-trip excess is real end-to-end delay, not lost replies
or a probe timestamp error. Case PBCH/idle/reaccess0, numeric auditpassed,
stop0/core9healthy/originalcompare0. All failed evidence retained.
Private slow-ping16k numeric audit records true monotonic packet events,
IQ/STK brackets and ordinaryTA swing baseline~-16 to-92 samples duringblend;
anchor B=-9.622476198sample. This correlation is not a unique causal proof.

Prospective next diagnostic changes only explicit isolated Koffset80->64 ms,
keeping source/binaries/DTX100/PDCP500/RNG20260925/diag1(start0), trafficload,
5-wall-second deadline and1%loss/timely gates. Source default80 unchanged.
The full621-row legacy-linear nominal geometry budget atK64 is24.043407 ms,
maxroundtrip42.956593 ms, required nominal5 ms/minintegerK45. This excludes
ordinaryTA/NTA/prediction error, so it is not an actual FFT/write-lead guarantee.
K64 is intended to shorten RX-to-TX prediction83->67 ms and test its effect,
not to declare the observed K80 failure fixed. Before promoting K64, require
two consecutive fresh first-window PASS runs plus complete full/legacy/static
cases at the same configuration. No acceptance threshold is relaxed.
Original final recheck and remote push remain pending.


### 2026-10-16 K64 rejected; gNB native TA diagnostic added

K64 single-factor case task8-first-k64-20261016b FAILED. Report129.744 wall s,
business7.605..65.038IQ: Ping101/101, UL1282/1287, DL1281/1285.
First window Ping17/17, UL213/218, DL221/221. Ping timely failure4/101
global and4/17 window; window UL conservative loss5/218 and timely failure
upper14.679%. No driver error, numeric audit passed, case PBCH/idle/reaccess0,
stop0/core9healthy/originalcompare0. The K64 candidate did not satisfy the
prospectively declared first-run criterion and is rejected; no repeat-until-pass
or matrix promotion. Default/next diagnostic returns to explicit K80.

Added bounded numeric-only gNB observation, with no MAC TA decision changes:
STKGNB_TA_MEAS logs native timing-advance command index, previous retained
index, native frame/slot, SDU/CRC-success indicator and measured SNRx10;
STKGNB_TA_SCHEDULE logs the native MAC CE scheduling point before its timer
reset. Scheduling is not an acknowledgement of physical transmission/UE receipt.
Only integrated-handover/legacy-handover with timing diagnostics1 enable logs.
Measurement/schedule hard limits are20000/2000 per translation unit. Existing
UE diagnostic-start setting does not gate these bounded initial gNB records.
Log I/O may affect wall runtime; no compensator, MAC field assignment, timer,
service gate or original profile behavior is changed by this observation.

The two gNB source files were byte-verified against the pinned OAI archive
before adding only include/diagnostic calls. BaseSHA256:
gNB_scheduler_ulsch.c83150f599143a18d90ca6afb52728472c08f35e9648ffeb2e94e869a692172f1;
gNB_scheduler_dlsch.c4c471bb261284efad246852cd0a66594d1fa197d07ad470025ffa6b1f0ddd9fc.
The native PUSCH path updates TA when RSSI>0 even without an SDU/CRC success;
the new record exposes this distinction for causal investigation. It does not
yet filter that update or establish which measurements cause the delay.
Actual-header Linux regression command
`python3 /mnt/c/Users/WSZ/.codex/worktrees/ntn-quadriga-handover/OAI调研/scripts/test_gnb_ta_diag.py`
exit0: PASS bounded gNB TA numeric diagnostics (profile gates, CRC fields,
hard limits). Full deployment/build/trace/parser/IQ/script regression pending.

### 2026-10-16 gNB observation result and prospective residual-TA candidate

Diagnostic-only commit 475db674eadfda53b5c343b52389ef14d24fd8e6 passed the
formal six-target build (19.520s), `bash local_ntn/run_regressions.sh`
(10.556s), and `bash scripts/test.sh` (94.375s), all exit0. Source proof records
31 overlays and six binary hashes. The independent archive comparison found
3738 non-overlay base files with no missing, mismatched, or extra files.

`task8-first-gnbdiag-20261016d` passed firsthandover at explicit DTX100,
PDCP500ms, K80, seed20260925, diagnostics1/start0: 113.459 wall seconds,
business IQ7.027559375..64.961188411; Ping89/89, UL1135/1135, DL1129/1134.
Switch-window Ping16/16, UL197/197, DL198/198; all timely/loss gates passed.
Numeric audit and original comparison passed; owned resources cleaned up.
The numeric TA audit found all actually scheduled window commands had a
CRC-good latest measurement, despite substantial positive/negative command
oscillation. CRC-failed exclusion alone does not explain the earlier failure.
Scheduling timestamps are native frame/slot observations, not UE receipt times.

New, unproven candidate `crc-good-quarter-gain-v1`: in the two isolated
profiles, only while both receiver tracker and TX predictor are enabled,
ordinary PUSCH TA feedback accepts CRC-good measurements and rounds the
residual command offset from neutral31 to one quarter. Random access, invalid
command handling, zky and disabled-tracker behavior retain native semantics.
The run manifest records the policy; numeric diagnostics retain raw and
applied commands. This changes an experimental feedback controller, not the
STK trace or QuaDRiGa path generation, and is not yet a demonstrated fix.

Actual-production-block and actual-header regressions run via
`python3 /mnt/c/Users/WSZ/.codex/worktrees/ntn-quadriga-handover/OAI调研/scripts/test_ntn_ta_feedback.py`
and the adjacent `test_gnb_ta_diag.py`: both exit0. The former checks profile
isolation, CRC gating, bounded gain, invalid values, the separate native RAR
assignment, and manifest policy consistency. Its toy-loop convergence check
does not establish PHY or business performance.

Prospective validation: same K80/DTX100/PDCP500/seed/diagnostics configuration,
two consecutive fresh-core firsthandover passes before full620, legacy620,
and static90 tests. A failure remains a failure; no repeat-until-pass and no
relaxation of five-wall-second delivery or one-percent loss gates. Full build,
trace/IQ regressions, continuous business matrix, and original final platform
recheck remain required before publishing this candidate.

### 2026-10-16 runtime matrix passed; original verification harness correction

Runtime commit e066b99558be686aecff7d41d0ed9eadffb8ef74 passed its entire
prospectively declared matrix: two fresh firsthandover runs16e/16f, full620
run16g, legacy620 run16h and static90 run16i. All used the same six binary
hashes, DTX100/PDCP500/K80/seed20260925/diagnostics1-start0 and quarter-gain
policy. The unchanged global/window loss and timely-delivery gates all passed.
Full Ping923/923, UL11806/11806, DL11802/11805; both switch windows have zero
loss and no missed timely-delivery deadlines. Full wall RTT mean196.939ms,
first/second window means287.600/269.306ms. Legacy Ping259/259, UL3304/3304,
DL3302/3303; static Ping104/104, UL1328/1328, DL1323/1327. Earlier failures
remain failures. These results do not establish unset DTX/PDCP defaults.

Final original check integration-final-16j FAILED before UE startup, with
ValueError and cleanup RuntimeError; no Ping/UDP result was produced. The
original native gNB forks a same-binary direct child in its launch group.
The verification harness incorrectly demanded every token-bearing process
be its own session/group leader. It rejected the native child and then
rejected it again during cleanup, leaving this run's gNB group/network.
Read-only process evidence confirmed exact executable/start identity, common
private ownership token, direct parent, session and group. Recovery stopped
only that verified group and removed only matching ifindex216/215 and
namespace inode4026532897. After recovery no live/zombie modems remained and
original source/template/binary/container/network comparison had differences[].

The failed harness had kept prior inactive processes.json bytes only in
memory. Their exact restoration cannot be proved after that process exited.
Recovery archived then removed only this failed run's generated PID state;
the next launch starts without a stale PID record. This generated runtime
state exception is not a source/template/binary change and must remain
disclosed. Do not claim byte-exact restoration of that pre-failure PID file.

Verifier-only correction allows ignoring a native fork child only after
same expected binary, private token on both processes, direct-parent,
leader-session/group and stable identity checks. Child PIDs cannot satisfy
an explicit gNB/UE ownership-state claim. Unknown children remain errors.
Preflight now durably saves prior PID-state bytes and a private digest before
starting resources. Actual Linux fork/token/parent/reuse rejection and private
backup regressions pass in `python3 scripts/test_original_platform_check.py`
(32 tests). This changes verification tooling, not the accepted runtime code,
OAI overlays, binaries, channel generator or business gates. Full verifier
suite and a new original-platform business recheck remain required.

Original attempt integration-final-16p also FAILED before business counts,
with ValueError/cleanup RuntimeError during UE launch. Its archived startup
markers show both launchers started; later read-only collection of the same
four native processes passed. The original exception text was not retained,
so the precise transient cannot be uniquely identified from this evidence.
Both groups502053/502159 and their verified network236/235 were subsequently
cleaned by the identity-based checker; the missing prior PID state was restored
as missing and protected source/template/binary/container/network differences
were[]. This second failure is not a passing original-platform test.

Further verifier-only regressions reproduce legitimate temporary descendants
of a verified launch group and stale bash-to-ip executable snapshots. Helpers
are ignored only with a still-matching recorded leader, own token throughout
a bounded ancestry chain, matching session/group, and stable identities.
They never become independent process-state owners. Fresh executable identity
may be revalidated once under the same PID/start; PID reuse and unknown live
processes remain errors. Already-exited temporary processes claim no resources.
Private exception tracebacks are now saved inside the private run output;
the public result still contains only exception types. The actual Linux fork,
different-binary helper, foreign token/ancestry/reused PID rejection and state
backup regressions pass: `python3 scripts/test_original_platform_check.py`,
34 tests exit0. The simulator runtime files,32 OAI overlays and six binaries
remain unchanged; full auxiliary regressions and new original recheck pending.

### 2026-10-16 final residual-TA candidate validation

Validated runtime code commit: `e066b99558be686aecff7d41d0ed9eadffb8ef74`. The subsequent `ae3723e7caa8fa95fb47ede327582396c29dc498` changes only the original-platform verification tool, its regression tests and notes. Source and all six runtime binaries were reverified identical; its complete trace/IQ and script regressions passed again (10.754s/90.944s). Remaining release changes are documentation and numeric artifacts. All five prospectively declared live runs passed on the exact runtime source and six binary hashes. Parameters were explicit DTX100, PDCP500ms, K80, RNG seed20260925, timing diagnostics1/start0 and `crc-good-quarter-gain-v1`. This validates those parameters; it does not establish the full-run behavior of the unset DTX/PDCP defaults.

| Run | Case | Wall seconds | Ping received/sent | UL received/sent | DL received/sent |
| --- | --- | ---: | ---: | ---: | ---: |
| `task8-first-ta-20261016e` | firsthandover | 108.387 | 85/85 | 1081/1081 | 1076/1080 |
| `task8-first-ta-20261016f` | firsthandover-repeat | 131.247 | 107/107 | 1362/1362 | 1356/1359 |
| `task8-full-ta-20261016g` | full | 968.562 | 923/923 | 11806/11806 | 11802/11805 |
| `task8-legacy-ta-20261016h` | legacy | 284.468 | 259/259 | 3304/3304 | 3302/3303 |
| `task8-static-ta-20261016i` | static | 128.419 | 104/104 | 1328/1328 | 1323/1327 |

Each run passed the unchanged global and switch-window one-percent conservative loss and five-wall-second timely-delivery gates. Both firsthandover runs followed fresh core resets before the full test. Full and legacy each cover620 IQ seconds and both complete STK8239–8249 /8794–8804 windows; static covers90 IQ seconds. Only actual business observation intervals count as business coverage. Missing startup and drain coverage remains visible in the figures.

| Run | Switch STK second | Ping received/sent | UL received/sent | DL received/sent | Mean wall RTT ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| firsthandover | 8244 | 15/15 | 187/187 | 187/187 | 283.795 |
| firsthandover-repeat | 8244 | 15/15 | 190/190 | 191/191 | 290.341 |
| full | 8244 | 15/15 | 189/189 | 189/189 | 287.600 |
| full | 8799 | 15/15 | 192/192 | 193/193 | 269.306 |
| legacy | 8244 | 4/4 | 54/54 | 55/55 | 62.737 |
| legacy | 8799 | 4/4 | 57/57 | 57/57 | 76.898 |

Full-run mean wall RTT was 196.939ms. The window RTT values and joint plot show business timing changes aligned with the physical transitions; they include host scheduling and do not isolate propagation as the only cause.


The QD-on and QD-off runs have different observed real-time factors. Their wall RTT difference must not be attributed directly to propagation delay. Event times share the IQ/STK axis; RTT, offered rate and IQ/wall throughput retain their separately documented units.


Formal commands `cmake --build .runtime/oai/cmake_targets/ran_build/build --target nr-softmodem nr-uesoftmodem rfsimulator params_libconfig nr_prachsim nr_pbchsim -j 6`, `bash local_ntn/run_regressions.sh` and `bash scripts/test.sh` all exited0 (18.999s,10.586s,94.769s). The source proof records32 overlays/six binary hashes. The deployed archive audit compared3738 non-overlay base files with no missing, mismatched or extra source files.

Final original-platform business recheck passed: Ping30/30, UL130 datagrams and DL130 datagrams, zero loss in both15-second UDP tests. Original trace parser, trace validation, stock real-IQ regression and a separately compiled genuine address/undefined sanitizer run all exited0. Sanitizer compilation explicitly used `-UNDEBUG`, `-fsanitize=address,undefined`, `-fno-omit-frame-pointer` and `-fno-sanitize-recover=all`; it did not rely on the stock script's ignored command-line arguments.

Successful original recheck ID: `integration-final-16u`. Exact source commands
from `/mnt/d/实验室学习工作/杂活/雄安/OAI调研` were
`cc -Wall -Wextra -Werror -Ilocal_ntn local_ntn/test_trace.c local_ntn/stk_trace.c -lm -o /home/kayoko/ntn-workspaces/ntn-quadriga-handover/.private/task8-20261016/original-final16u/original-trace-test`,
that resulting parser binary, `python3 local_ntn/test_trace_validation.py` and
`python3 local_ntn/test_real_iq.py`: all exit0. The full sanitizer compile argv,
input hashes and its actual exit0 execution are retained in the private
`original-final16u` audit; no raw UE logs are published.

Before the original recheck, only the exact owned nine new core containers and one owned network were removed. Foreign Docker network configuration and endpoints and original source/template/binary/container/network fingerprints passed comparison. The successful final recheck starts and ends without a PID-state file. The earlier failed16j attempt did not durably save its prior inactive PID-record bytes; their restoration is not claimed, as disclosed above. Its exact generated state was archived then removed during verified recovery. No original configuration template or external source checkout was overwritten.

Reviewed numeric evidence and exact binary hashes are in [validation/2026-10-16/index.json](validation/2026-10-16/index.json); the [full joint timeline](validation/2026-10-16/full/timeline.png) aligns physical delay/Doppler/CN and satellite transitions with continuous RTT/loss/UDP throughput. CSVs retain distinct IQ and wall throughput/time units. Raw modem and packet-event logs remain private.

These are finite observed experimental runs at low offered load, not a seed-independent reliability/capacity guarantee. Earlier failed runs above remain failures. The pseudo satellite switches are physical-channel changes within one cell, not multi-cell RRC/Xn handovers. One-second QD snapshots and synthetic blended geometry retain the documented research limitations.
