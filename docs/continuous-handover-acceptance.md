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
and missing observations.

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
Send-stop reserves at least five IQ seconds or eight wall seconds mapped with
recent observed real-time factor, whichever needs more IQ coverage. It cannot
cut a required switch window. Insufficient room for bounded draining fails
explicitly rather than reducing coverage.
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

