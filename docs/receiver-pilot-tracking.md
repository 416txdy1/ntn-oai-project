# Receiver pilot tracking for isolated handover profiles

`integrated-handover` and `legacy-handover` enable the receiver tracker. `OAI_NTN_RX_TRACKER=0` disables it. Missing, zky and foreign profile names retain the previous receiver path. This changes receiver processing only: the physical channel, trace interpolation, QuaDRiGa, timing advance formulas, IQ clock, timing-assist setting and acceptance gates are unchanged.

The main receiver thread copies chronological **actually read** samples into bounded history. Every downlink job owns a separate original-IQ snapshot, signed FFT offset, total frequency compensation and 64-bit sample epoch. PDSCH workers use the immutable job values; they do not read a later controller offset or frequency. Jobs release their samples after PDSCH processing. PBCH processing and the existing timing/frequency feedback execute synchronously in main preprocessing before the PDSCH job is queued. Trusted tracker jobs exclude those old feedback loops, preventing double integration. The original `nr_slot_fep` API and body remain intact; the new `nr_slot_fep_tracked` uses copied scratch samples and applies the job compensation once.

Serving-cell PSS scheduling uses the existing PBCH configuration: the PSS is one symbol before PBCH1. A fixed ±512-sample search uses production PSS/SSS routines, the current receiver total FO as a prior, the original correlation/SSS quality thresholds and a strict decoded PCI check. Every PSS candidate FFT tail and all four SSB FFT intervals must lie in true observed data. Search-edge, short data, wrong-cell and noise observations cannot update history. Timing resolution is the existing four-sample PSS grid; this implementation does not claim fractional-sample refinement.

For observed PSS sample `A`, nominal serving-cell PSS sample `Q`, consumed read correction `C` and measured FFT correction `delta`, the first trusted error is `e_ref=C_ref+delta`. Subsequent errors are `e=e_ref+(A-A_ref)-(Q-Q_ref)`. Timing rate is `delta_e*Fs/delta_Q` in samples/second. Frequency rate uses the actual observed interval `delta_A/Fs`. Main predicts the next frame read correction and each job's FFT offset/FO. Predictions expire after one configured SSB period. A discontinuous read clears the observation history; it never resets RF sample time. Rejects retain prior history without inventing measurements, and expiration returns to the old receiver feedback. Signed differences are checked before conversion; the FO primitive receives only bounded snapshot-local indices, never narrowed absolute timestamps.

## Actual IQ regression

Run after formal source preparation/build:

```bash
python3 scripts/test_rx_tracker_iq.py --root "$PWD"
```

The script copies the pinned OAI PBCH simulator into a fresh ignored `.private` directory, reuses actual Ninja compiler/link flags and production generator/PSS/SSS/FEP/DMRS/Polar objects, and explicitly verifies each `OAI_RNGSEED` marker. It asserts CRC truth rather than treating simulator exit zero as success. The simulator uses R25 because its bandwidth helper rejects R24; Fs=7.68 MHz, FFT512, CP36, FDD and SSB type match this test, but it is not a complete copy of the live configuration. Logs and IQ files stay private.

The input delay holds constant over the RFsim read block containing SSB symbols 2–5, evaluated at that block's real first-symbol read epoch. This matches RFsim's one channel-offset update per read. An earlier per-sample time-warp stress fixture compressed the SSB waveform and rejected at the unchanged SSS threshold at 2725 us/s; those failures are retained and are not reported as platform failures or hidden by threshold changes. Continuous CFO chirp remains an additional input stress.

Private candidate verification passed 28 cases, including controlled zero/non-grid time RED→GREEN, five distinct fixed noise seeds, absent SSB, same-Nid2 wrong PCI, short/edge/capture rejection, default/zky/foreign/off compatibility, six-observation 2725 us/s +13.25 kHz/s loops at 30/20/16 dB, and epochs crossing 2^31 and 2^32. Each case also exercises actual concurrent FFT jobs with separate snapshot values, history replacement/discontinuity, first nonzero offset preservation, dimensional rate checks and bounded prediction expiry. Same-IQ measurements remain identical across the wide epoch controls.

These are receiver unit/integration IQ results. They do not replace the pending continuous live static/first-handover/legacy620/full620 business acceptance, original-platform after-test, source protection comparison or independent review.