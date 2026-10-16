# Receiver-derived transmit compensation (candidate)

This change is isolated to integrated-handover and legacy-handover RFsim profiles with receiver tracking, continuous FO mode 2, and autonomous TA enabled. `OAI_NTN_TX_PREDICTOR=0` disables it. Other profiles and RF hardware retain the existing compensation path.

The main thread records only accepted, serving-PCI, complete-span PSS measurements. Their raw sample coordinates plus the RF device first timestamp share the simulator IQ clock. Seven recent observations estimate local delay slope and curvature. The initial decoded serving SIB TA anchors the offset between UE nominal scheduling and the RF clock; later serving SIB updates retain that anchor. Loss of history or resynchronization clears the appropriate state without resetting the device clock. No STK propagation truth is read by this predictor.

Current payload and next stream boundary are distinct. With X=NTA+totalTA and I the already executed frame-tail read shift, original OAI writes a stream block using previous X and prepends excess samples when the block grows. The selected next value is max(predicted next X, predicted current X-I). Original block-size, koffset difference, and prefix-write behavior are retained. After final integer block-size and NTA decisions, the main thread solves the current payload's actual propagation epoch including its prefix. Total UL FO is derived from measured DL FO at that epoch using the two carrier frequencies. Each TX job owns an immutable FO/TA/epoch snapshot.

`python3 scripts/test_tx_predictor_contract.py` compiles extracted main scheduling code and the actual RU_write prefix loop, then runs 3,000 continuous synthetic scheduling jobs and the 704-assertion math suite. The scheduling fixture covers both numerologies, positive/negative delay slope, curvature reversal, frame-tail shifts, NTA changes, nonzero first timestamps, and wide clocks. `--mutant-lifecycle` deliberately restores the old unconditional reset and must fail. These are numeric scheduling tests; they do not decode actual UL IQ or establish a live acceptance result.

Private candidate 15c additionally passed three actual OAI translation units, trace/parser/IQ regressions, and 28 existing receiver IQ cases. The largest modeled scheduling error in its curve-reversal fixture was -4.247 samples; this is not proof of gNB FFT-window margin. Serving SIB koffset transitions, startup anchoring through the complete main loop, and the final active UL OFDM symbol require additional verification. Actual continuous Ping and bidirectional UDP across the first and second satellite switches, final original-platform business checks, and whole-branch review remain release requirements. No remote push is established by these candidate tests.


The explicit diagnostic environment setting `OAI_NTN_PUSCH_FAILURE_THRES` accepts 1..1000 only in the isolated profiles and records its value in run.json. When unset, OAI's default 10-event threshold is preserved. Zky ignores it. This count is not a wall/IQ duration or a HARQ round count. It is intended for a controlled comparison of transient PHY failures against the scheduler's sticky UL-failure state; increasing it does not constitute a PHY fix or acceptance result. Ping/UDP loss and delivery deadlines remain unchanged.


`OAI_NTN_PDCP_REORDERING_MS=100|200|500` is another explicit isolated comparison setting, unset by default. Only gNB receives the native `--pdcp.drb.t_reordering msXXX` option; its native RRC builder encodes the same timer for UE. The manifest records this override and the requested OAI RNG seed. Actual seeds still require numeric startup verification. Default DRBs use AM and the existing DL/UL MCS limit is already9; neither was assumed to be UM or high-MCS. Actual late old-COUNT PDCP discards during the observed switch motivate testing the finite reordering timer, without claiming packet-level attribution or changing any business loss/deadline gate.


With OAI_NTN_TIMING_DIAG=1, the optional OAI_NTN_TIMING_DIAG_START_IQ_S=580
selects a later bounded observation window using actual RF sample coordinates.
Default is0; isolated valid values are0..620; zky ignores the setting.
Only numeric logging is gated. Pilot acceptance, feedback and compensation
continue throughout the run. Native TX records include job-owned TA/NTA/clock
values, while raw modem logs remain private. This option is not a PHY fix.


## gNB TA numerical observation

New isolated profiles with `OAI_NTN_TIMING_DIAG=1` emit `STKGNB_TA_MEAS`
(native command index/previous index/CRC-SDU availability/SNRx10) and
`STKGNB_TA_SCHEDULE` (MAC CE scheduling point). Native command index31 is
zero relative correction; it is not a sample count. Frame/slot are native
modulo-SFN clocks; align with actual STKCLOCK anchors when analysing.
No native assignment, timer or compensator is changed by these records.
Bounds are20000 measurements/2000 schedules per translation unit. These
initial gNB logs are independent of the UE-only diagnostic-start IQ window.
Log I/O can affect wall runtime. Raw records remain private; no RNTI,
subscriber credentials or packet payload is emitted by the new logger.

## Isolated residual MAC TA controller

With both receiver tracker and TX predictor enabled in integrated-handover or legacy-handover, ordinary PUSCH TA uses `crc-good-quarter-gain-v1`. CRC-failed measurements retain the last accepted command; CRC-good residual offsets from neutral31 are rounded to one quarter, nearest with ties away from zero. Random-access assignments remain native. Zky, unknown profiles, or either disabled tracker retain native ordinary feedback. Invalid accepted commands are not clamped. The manifest records the policy; diagnostics append retained/feedbackUsed to the raw measurement. This is an experimental controller change, separate from diagnostic logging. See the final validation table for the finite observed results; the earlier native-loop failures remain recorded.
