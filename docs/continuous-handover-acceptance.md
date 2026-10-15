# Continuous physical and business acceptance

These commands operate only the isolated integration worktree. Provision/start its
core with the run-scoped core controller first; the acceptance driver does not
start a core or take over existing modems.

Use a fresh run ID. Start from an environment without stale OAI variables, or
export the matching profile/run ID **before** sourcing scripts/env.sh. A sourced
zky/default or another run's paths remain an error; the driver does not clear
conflicting variables silently.

~~~bash
sudo -E python3 scripts/handover_acceptance.py \
  --case full --profile integrated-handover --run-id integrated-full-001 \
  --max-wall-seconds 3600
~~~

Auxiliary cases have separate reports and cannot substitute for the full case:

~~~bash
sudo -E python3 scripts/handover_acceptance.py \
  --case firsthandover --profile integrated-handover --run-id integrated-first-001
sudo -E python3 scripts/handover_acceptance.py \
  --case static --profile integrated-handover --run-id integrated-static-001
sudo -E python3 scripts/handover_acceptance.py \
  --case legacy --profile legacy-handover --run-id integrated-legacy-001
~~~

Full and legacy require the complete 8200–8820 STK / 620 IQ-second interval and
both complete nonempty 8239–8249 and 8794–8804 business windows.
Firsthandover selects the dedicated short trace, schedule and DL/UL bundles,
requires all 70 IQ seconds and the 8239–8249 window.
Static uses rate zero and 90 cumulative IQ seconds, with at least 30 IQ seconds of
observed continuous business. Its STK epoch remains constant and it has no
satellite-switch expectation. The longer interval permits initial registration
and the bounded tail drain.

The original zky 361-second scripts/full_pass.py entry remains available,
including its original ping/iperf flow. The legacy local_ntn/test_seamless.py
entry remains compatible; --acceptance explicitly delegates its remaining
arguments to the new driver.

## Evidence and time units

The driver starts continuous ICMP and two independent UDP flows as soon as the
PDU address is observed and clock/receiver readiness permits. UE workers run in
the selected UE network namespace and bind the real PDU address. External-DN
workers run host Python through nsenter -n into the verified container's network
namespace; they retain host PID/time namespaces and CLOCK_MONOTONIC.
Both directions traverse the UE tunnel and external DN. A receiver report is
mandatory; sender-only counts cannot pass.

Each UDP datagram carries a run token, direction, sequence and monotonic send
timestamp. Successful sends and receives have separate private JSONL records,
heartbeats and final counters. Records preserve unknown IDs, duplicate and
out-of-order datagrams, timeouts, late receipts and eventual missing packets.
At the bounded drain deadline, only observed receipts count as delivered.
A late receipt retains its timeout and late status but is not falsely counted
as permanently lost. Global cohorts retain early packets sent before the first
successful receipt.

The configured offered rate is **100000 payload bit/s paced by wall time**.
Reports also calculate actual offered wall rate from successful sent bytes,
measured receive throughput per wall second, receive throughput per IQ second and
real-time factor (deltaIQ / deltaWall). These quantities are separate.
ICMP RTT is wall_rtt_ms. UDP one-way latency is observed application endpoint
wall time, including receiver scheduling. Neither is relabeled as IQ propagation
time.

Physical STKCLOCK anchors come from the real RFsim channel callback and retain
direction, monotonic_ns, samples, actual sampling_rate, iq_s and stk_s.
gNB UL and UE DL have separate mappings. Actual startup rates, manifest Fs,
anchor Fs, epoch and rate must agree. Physical log arrival times are never
clock anchors. Incremental tails reject rotation, truncation, clock regression
and missing observations. Numerical/schedule records must also cover the run
at their one-IQ-second cadence without gaps over 1.15 IQ seconds, including
both observed satellite-completion markers.

Each business event needs bracketing anchors. Interpolation gives an estimate
while the interval remains explicit uncertainty evidence. Intended cadence is
0.1 IQ seconds plus actual sample-block spacing; the report states observed
maximum spacing (the collector rejects gaps over 0.15 IQ seconds).
Unbracketed events cannot silently be extrapolated.

Let D be definitely-inside window senders, M missing among D and A_m
possibly-inside missing senders. Conservative loss upper bound is
(M+A_m)/(D+A_m). Possibly-inside received packets cannot reduce this bound.
A window without definite senders fails. Boundary packets all received can pass
with zero loss; uncertain missing packets remain visible and can fail the
unchanged 1% loss / 99% ping-success thresholds.
Deadline timeouts are separate; final loss uses observed bounded-drain delivery.

Reports require PDU and actual successful ICMP/UL/DL delivery before STK 8239,
complete physical IQ coverage, both expected nonempty windows, no post-PDU
RRC IDLE/reaccess, no PBCH errors/PDU address changes, and a passing independent
numerical audit. Missing fields, worker failures and gaps fail closed.
SIGINT/SIGTERM trigger bounded cleanup of this run's process identities/resources.

## Outputs

Outputs are private by default under
.runtime/runs/<profile>/<run-id>/acceptance/:

- report.json: case, failures, conservative cohorts, clocks, workload rates,
  process identities and drain facts.
- Worker JSONL and matched JSON: complete timestamp/packet-matching evidence.
  Raw modem logs stay in the run directory and may contain credentials.
- numeric-audit.json: independent geometry audit using manifest trace,
  actual Fs and Hermite, blend-aware or legacy-linear interpolation.
- timeline.csv, timeline.svg, timeline.png: physical delay, Doppler, C/N,
  satellite identity/phase, ICMP RTT, loss bounds, arrival throughput and
  real-time factor on one axis. Static plots use IQ elapsed seconds.
- switch-comparison.json: before/during/after cohorts for each completion.

Startup is unavailable instead of zero latency/loss. Final send-stop/drain is
marked intentional and is not presented as continuous offered traffic.
Send-stop prefers at least five IQ seconds or eight wall seconds mapped with
recent observed real-time factor. It remains after the complete final switch
window, targeting at least five IQ seconds before the case end. The actual stop
brackets and remaining IQ bounds are separately reported; polling overrun is not
presented as verified target margin. Faster replay can make
these preferences conflict: retain the complete window and observe the fixed
six-wall-second drain with actual channel clocks, even if those clocks extend
beyond the case. The report records each channel's drain endpoint and overrun.
No traffic is added after send-stop, no trace states are extrapolated, and the
original five-wall-second delivery deadline and one-percent gates still apply.
Missing clocks, unresolved deadlines or late/missing packets still fail.
Throughput bins use receive-time estimates and expose clock precision;
loss bins use matched sender cohorts. Stable business through a transition is
valid evidence; no synthetic degradation is introduced.

Only reviewed nonsecret timeline/aggregate artifacts should be published.
Never publish raw UE/modem logs or subscriber/private core files.

~~~bash
python3 local_ntn/audit_runtime_numbers.py \
  --manifest .runtime/runs/integrated-handover/integrated-full-001/run.json
sudo -E python3 local_ntn/experiment.py stop \
  --profile integrated-handover --run-id integrated-full-001
~~~

Manifest identity distinguishes a standalone OAI Git checkout from the verified
vendor archive. Parent integration HEAD is never recorded as OAI source commit.
Archive identity contains the pinned commit, verified archive checksum/stamp and
deployed current/QuaDRiGa overlay hashes. Git trusted-directory exceptions are
scoped to exact commands, never global configuration.


The 100K wall workload is independently verified in each UDP direction. Sender
sequences, end.sent, payload sizes and end.sent_bytes must exactly agree. Actual
offered rate uses the first-to-last real send_ns span and excludes the first
packet's payload from the numerator (N-1 packet intervals); startup and the other
direction's ready time do not dilute it. At least 21 packets are required so the
sample contains at least 20 packet intervals. The observed payload bit rate must
be within +/-5% of 100000 wall bit/s, an explicit measurement/pacing tolerance.
This validates that the requested workload ran; it does not alter the existing
ping success or UDP loss thresholds. Heartbeat observation gaps still fail.
The report records packet/byte totals, exact first/last times, endpoint rule,
tolerance, actual wall rate, and actual IQ time reserved for bounded draining.


The continuous driver verifies the owned UPF and ext-DN container IDs, core workspace/configuration ownership, live process and network namespace identities, UPF address and both routes before starting business workers. For the inherited exact UE-pool SNAT rule, the uplink receiver expects the verified UPF address while preserving the original PDU address in `business_path` in the manifest and report. Without source translation it expects the PDU address. Unexpected source translation, changed identities or routes fail verification. UDP token, direction, sequence and exact source checks remain active.


实际物理观测的起点由生产信道回调一次性输出 `STKCHANNELSTART`，并与该方向首条 `STKCLOCK`、数值状态和卫星日程的原始样本计数严格匹配。RFsim 在对端尚未连接时可能推进样本计数；这段 `[0, first_actual_callback]` 记为 `startup_unobserved`，不声称已有信道观测，不补历史样本、不重置 IQ 或 STK epoch。总验收仍使用原始 RF IQ 的 `[0, duration]`，全部业务事件和 PDU 就绪均须处于双侧真实物理起点之后并具有双侧时钟括号；所有早期发送保留在全局统计中。后续时钟间隙 0.15 IQ 秒、数值/日程间隙 1.15 IQ 秒、620 IQ 秒结束点和两次切换窗口要求不变。曲线对完全或部分未观测的启动 bin 显式标记覆盖状态，物理数值留空。

## RF 错误归属与及时交付

新 profile 的每次 PBCH 解码失败在原错误行附带 `STKUE_PBCH_FAILURE`，字段包含
实际 RF 输入样本区间、采样率、原生作业身份、FFT 校正及设备 firstTS。
实际接收 API 减去的 firstTS 在记录时加回，因此区间与物理信道时钟同域；
不通过 SFN、墙钟打印时间或 STK 插值猜测错误时间。四个 SSB FFT 的输入采用
半开跨度 `[native_begin,native_end)`，支持实际每时隙 12/14 个符号并校验作业身份。

停止本次拥有的 modem 后，观察器读完剩余日志。报告保留全部错误，并区分
`in_case`、`terminal_outside`、`boundary_ambiguous` 和 `unattributed`。
测试区间仍为原 RF `[0,duration]`：只有整个输入跨度起点严格大于末界才能归为
终止后事件；跨界、末界接触、缺失/矛盾元数据或截断错误均计入失败。
未知截断日志也使观测失败。停止后错误不会被删除，也不能缩短测试覆盖来通过。

最终丢包上限仍为 1%。在此之外增加独立的及时交付条件：沿用现有
`CLOCK_MONOTONIC` 五秒期限，各全程及切换窗口的保守及时交付失败率上界
须不超过 1%。包晚到仍记为最终收到，同时记为未及时交付；尚未等待完整期限
的证据不能通过。窗口边界可能归属的未及时包纳入最坏情况上界，所有早期
发送记录和真实工作负载保留。

延迟报告给出实际收到包的 p50、p95、max，分位数采用经验 nearest rank；
未收到包属于右删失，不伪造其延迟。`service_degraded` 表示观测到迟到、缺失或
期限未决，不替代数值验收门槛。最长接收中断按唯一包的首次实际到达计算，
包含业务起点和结束点间隙；重复包不能填平中断。窗口边界保留物理时钟括号，
分别报告中断下界与上界。主动停止发送后的排空阶段不计为业务中断。
