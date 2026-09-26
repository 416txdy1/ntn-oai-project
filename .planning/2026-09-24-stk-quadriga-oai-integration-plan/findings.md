# Findings & Decisions

## Requirements
- Execute and report exactly one implementation step at a time.
- Every step needs a reversible backup or Git version.
- Terminal commands and results must be visible to the user and saved for later inspection.
- Preserve existing dirty worktrees and do not expose credentials or raw UE logs.

## Research Findings
- Step 0 project commit: 33c13d687e266d69a9246e84b88eeebc0fa2301d.
- Step 0 OAI commit: c4125d1c740181ab1f7da0e7dd1d04ed07c37670.
- The selected integration sources were copied to the Step 0 backup with SHA256 values.
- Existing baseline regressions pass; current warnings are unused parameters in test doubles and CRLF conversion notices.
- OAI branch `zky` now preserves the verified 14-file STK/RFsim source baseline at commit `219576f68c`.
- Existing STKTRACE2 rows contain time, satellite/ground geometry, DL/UL power, C/N and validity; RFsim derives bulk delay and Doppler from the IQ sample clock.
- QuaDRiGa `qd_channel` stores coefficients and delays with native dimensions `[Rx antenna, Tx antenna, path, snapshot]` and requires matching snapshot counts when channels are combined.
- QuaDRiGa documentation supports interpolation of channel coefficients/delays and describes time-evolving path powers, delays, angles and phases.
- QDCHANNEL1 therefore transposes the persisted layout to `[snapshot, rx, tx, path]` for streaming and keeps STK bulk terms separate from normalized QuaDRiGa multipath terms.
- Step 2 environment discovery found no MATLAB/Octave executable and no `QUADRIGA_PATH` on Windows or WSL.
- QuaDRiGa v2.8 advertises Octave 8 compatibility; v2.4 introduced satellite modelling and v2.2 introduced dual mobility.
- The official channel object exposes complex `coeff` and `delay` tensors; the exporter can keep API-specific generation separate from deterministic tensor normalization and QDCHANNEL1 serialization.
- Official dual-mobility tutorial uses `qd_layout.tx_track`, `qd_layout.rx_track`, identical snapshot counts, `layout.update_rate`, and `layout.get_channels`; transmitter and receiver tracks must be aligned on the same time grid.
- Official NTN calibration uses `qd_satellite`, `init_tracks`, satellite antenna orientation and 3GPP TR 38.821 scenarios, confirming that arbitrary STK ECEF samples should enter through explicit tracks rather than a terrestrial fixed-BS shortcut.
- QuaDRiGa dual-mobility output contains both bulk motion Doppler and multipath Doppler. Because STK remains authoritative for satellite bulk Doppler, the Step 2 adapter must document and isolate residual phase handling instead of blindly stacking both frequency shifts.
- Runtime-continuation discovery did not find the newly supplied MATLAB/QuaDRiGa files under the Windows project root or on the Windows PATH; the external WSL/OAI root and standard installation locations still need inspection.
- The user-supplied shortcut resolves to MATLAB R2023b at C:\Program Files\MATLAB\R2023b\bin\matlab.exe; the executable exists.
- The supplied QuaDRiGa 2.8.1-0 root contains the qd_layout and qd_simulation_parameters class sources.
- Real STKTRACE2 files use a bare STKTRACE2 magic line and columns 21/22 are dl_valid,ul_valid; the first exporter parser version expected a commented magic line and reversed those flags.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Do not create a Git commit for Step 0 | Existing user changes and generated scenario data should not be staged or bundled into an agent-created commit |
| Do not back up UE credentials, databases, raw logs, or build output | Protect secrets and keep rollback scope limited to integration source files |
| Commit through an isolated OAI worktree | Preserve all existing uncommitted changes in the `develop` worktree while creating a clean, reviewable `zky` commit |
| Use JSON manifest plus little-endian binary arrays | A later RFsim C/C++ reader can stream the files without MATLAB, HDF5 or NumPy runtime dependencies |
| Keep STK bulk delay/Doppler/absolute gain authoritative | Avoid applying free-space loss, propagation time or satellite Doppler twice |
| Store normalized coefficients and zero-mean residual gain from QuaDRiGa | Preserve multipath fading and shadowing variation while retaining the existing STK link budget reference |
| Require an explicit QuaDRiGa source path and fail fast when unavailable | Avoid silently using a different library version or synthetic data in a real export command |
| Test the converter with deterministic qd_channel-shaped fixtures | Validate dimensions, normalization, relative delays, provenance and bytes on this machine without claiming a real QuaDRiGa execution |
| Stabilize the earliest active path phase per antenna link | Remove common propagation phase and bulk Doppler already supplied by STK while preserving relative multipath phase |
| Add an explicit link direction to QDCHANNEL1 v1 | The exporter must assign satellite/UE transmitter and receiver roles unambiguously for separate uplink and downlink bundles |
| Start with SISO service-link export | Validate the offline pipeline before adding antenna-array and feeder-link complexity |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| git diff --check opened an interactive pager | Exact pager PID was validated and terminated; verification rerun used GIT_PAGER=cat |
| A stale Step 1 marker referenced `local_ntn/test_stk_trace.c` | Actual trace tests are `test_trace.c` and `test_trace_validation.c`; current discovery uses a unique result marker |
| Windows PowerShell argument passing did not execute the updated discovery script reliably | PowerShell 7 with explicit `-NoExit -Command` produced the expected unique marker and transcript |
| The WSL instance returned `Bad file descriptor` for `/mnt/e` | Ran the unchanged regression suite from an isolated `/tmp` copy and checked the main project diff separately |
| The first direction/hash assertion addressed `link_direction` at the manifest root | QDCHANNEL1 stores it at `radio.link_direction`; correcting the field path proved all downlink-repeat/uplink binary hashes are identical |

- Runtime issue resolved: the MATLAB parser now accepts the real magic line and maps downlink/uplink validity to columns 21/22 respectively.
- MATLAB R2023b reports version 23.2.0.2365128 and parses stk_constellation_trace_blend.csv into 1387 snapshots from t=7614 s through t=9000 s.
- QuaDRiGa 2.8.1 accepts the configured NTN scenario and starts channel generation, but get_channels rejects tracks that have positions without a movement profile.
- QuaDRiGa 2.8.1 defines movement_profile as a 2-by-N time-versus-distance matrix; dual-mobility Tx/Rx tracks must share the same end time, and layout.update_rate controls the output time grid.
- Full QuaDRiGa generation now completes, but an absolute coefficient-power epsilon is invalid for NTN path loss because valid satellite coefficients can have total power below 1e-15.
- A relative-to-peak path activation threshold preserves valid low-power NTN coefficients while still excluding numerically zero paths.
- The full 1387-snapshot export succeeds. QuaDRiGa emits a sampling-theorem warning because the STK geometry grid is 1 second at 2 GHz; STK bulk Doppler remains separate, but fast residual multipath Doppler is under-sampled.
- Cross-language JSON requires MATLAB manifest integer fields to use an integer MATLAB type; a numerically integral double may be encoded with an exponent and parsed as a JSON float.
- QuaDRiGa NTN scenarios use the canonical satellite-Tx/ground-Rx orientation. For the current SISO exporter, uplink uses channel reciprocity and changes only the manifest direction plus STK uplink validity/link-budget inputs; a later MIMO implementation must transpose Rx/Tx antenna dimensions explicitly.
- Step 2A baseline confirms STKTRACE2 columns 17/18 are absolute downlink/uplink received power in dBW, while columns 19/20 are C/N and 21/22 are validity flags.
- Exported complex taps are normalized independently at every snapshot, so their summed power is one and they cannot carry absolute path loss into RFsim.
- The current residual_gain_db is raw QuaDRiGa total coefficient power minus its time mean. Zero mean alone does not prove independence from satellite-range free-space loss; the real bundle spans -3.308 to +3.828 dB with 1.362 dB standard deviation and requires correlation/decomposition auditing.
- The real-data audit confirms duplication: QuaDRiGa residual gain versus relative free-space gain has correlation 0.899117 and regression slope 0.995961. STK downlink power already has slope 1.203847 versus the same free-space term, while STK plus the current residual has slope 2.199808.
- Subtracting the relative free-space term from the current QuaDRiGa residual reduces its standard deviation from 1.361673 dB to 0.596035 dB and its free-space correlation to -0.008330, confirming that most of the previous residual trend was deterministic range loss.
- QuaDRiGa 2.8.1 internally distinguishes the large-scale shadow-fading parameter sf from scenario path gain. The next audit action is to inspect the generated qd_channel.par fields and use an explicit stochastic component if it is preserved at channel output.
- Runtime inspection shows channel.par.pg is a 1-by-1387 per-snapshot path-gain series, while sf_parset is only one scalar (-0.478372 dB) for the current single segment. The channel object does not provide an independent per-snapshot shadow-fading series that can safely replace total path gain.
- Step 2A correction policy: keep the QDCHANNEL1 v1 residual_gain_db file for compatibility but write 0 dB from the production exporter. This preserves normalized QuaDRiGa multipath while ensuring STK remains the sole large-scale absolute-gain source.
- A dedicated audit tool will enforce time alignment, trace provenance, per-snapshot unit tap power, zero-reference excess delay, common-phase stabilization, zero production residual, and unchanged STK-to-FSPL slope after composition.
- The new audit negative control rejects the pre-fix real downlink bundle because its residual_gain_db is non-zero and range-correlated.
- MATLAB R2023b/QuaDRiGa 2.8.1 regenerated both real downlink and reciprocal uplink with the corrected normalization; both pass the existing bundle validator and the new link-budget audit.
- Corrected real bundles have zero time misalignment, maximum tap-power error 6.08131e-08, zero excess-delay reference error, and maximum common-phase error 1.87766e-08 rad.
- The corrected residual gain is exactly 0 dB; its FSPL slope/correlation are zero, and composition leaves the STK FSPL slope unchanged at 1.203847 for both directions.
- Audited STK geometry gives 6.219-10.739 ms one-way service-link delay and approximately -33.77 to +26.98 kHz bulk Doppler at 2 GHz.

## Resources
- .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100
- https://github.com/fraunhoferhhi/QuaDRiGa
- https://quadriga-channel-model.de/download/534245
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/quadriga_src/%40qd_channel/combine_tx_rx.m
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/tutorials/t14_dual_mobility.m
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/tutorials/calib_3GPP_38821_ntn.m
# Step 3A re-verification findings (2026-09-26)

- The tracked planning text had not yet been advanced from Step 2A even though the Step 3 reader exists in commit `8b1bb1d`; this is a documentation-state omission, not a code-state mismatch.
- Re-verification will use the existing C reader driver, real retained DL/UL bundles, the link-budget auditor, and the full STK/RFsim regression suite.
- No new channel-model behavior will be implemented during this audit; any numerical failure will stop the phase for diagnosis rather than being hidden or weakened.
- Real audit bundles are available under `runtime-output/audit-downlink` and `runtime-output/audit-uplink`; the previously retained WSL Step 3 temporary directory is no longer present, so a fresh isolated copy is required.
- PowerShell must not interpolate Bash command substitutions while constructing the visible WSL test script; use a single-quoted outer template plus explicit path placeholder replacement.
- The first real-data rerun passed all 13 schema/math/audit unit tests and real DL/UL bundle validation, but the real DL link-budget audit returned nonzero. The full pipeline correctly stopped before C-reader and STK/RFsim stages; the exact provenance/error is being diagnosed without relaxing any threshold.
- The real DL audit failure is an input-selection error: the bundle provenance is `680632212ffdbfa95a8e45a537acbfcad3c6dfaccfca1bc50283f0384c6e3e73`, while the initially selected blend trace hashes to `b0a911d2e31449ef6f57f1bb2a7b47e430634c40ec74b4df70cebfc45e3f3ba1`. The auditor correctly rejected the mismatch before performing composition metrics.
- The matching input is `stk_constellation_trace_blend.csv`. With it, all 13 Python tests, real DL/UL schema checks, real DL/UL link-budget audits, and all four cross-direction payload SHA256 comparisons pass. The remaining nonzero status occurred later in the combined WSL stage and is being isolated.
- The focused strict C-reader run passes for the real downlink (1387 snapshots, SISO, 11 paths) and all malformed-input controls. Passing a literal multiline Bash command through a double-quoted PowerShell template is unsafe because Bash variable names are expanded by PowerShell; transport the script as Base64 instead.
- With Base64 transport, the real uplink reader, GCC `-fanalyzer`, ASan/UBSan/leak checks for example/DL/UL, and every functional STK/RFsim regression pass. The combined script returned 129 only because its last `git diff --check` ran in an intentionally non-Git `/tmp` copy; the main-worktree check is handled separately.
- Final real DL/UL metrics match: time error 0, maximum tap-power error `6.081311076933105e-08`, zero-delay error 0, reference-phase error `1.8776618900713638e-08` rad, residual gain max/slope/correlation all 0, and combined FSPL slope equals the STK-only slope (`1.2038472634976762` DL, `1.2038472634976765` UL). This numerically excludes duplicate large-scale path loss and bulk Doppler phase.
# Step 4 RFsim integration findings (2026-09-26)

- The project checkpoint is `3109dc6` on branch `zky`; generated STK artifacts remain untracked and must not be staged.
- Step 4 is limited to the existing satellite-UE SISO service link and must preserve STK ownership of absolute gain, bulk delay, bulk Doppler, visibility, and noise.
- The first WSL call-chain discovery produced no transcript output, so a second inspection was launched with explicit stdout/stderr capture.
- The isolated OAI worktree `/home/duyaya/OAI/oai-zky-preserve` is clean on branch `zky` at `219576f68c`; the dirty main `develop` worktree will not be modified.
- This OAI revision stores RFsim under `radio/rfsimulator`, not the older `targets/ARCH/rfsimulator` path. A corrected call-chain inspection completed successfully.
- RFsim calls `update_channel_model(channel, nsamps, nextRxTstamp)` before `rxAddInput(...)` for the same receive block. Existing STK trace handling already owns bulk channel offset, Doppler phase increment, gain/noise, visibility, and UE synchronization.
- The intended Step 4 boundary is therefore: load/sample QDCHANNEL1 during the update stage and change only relative multipath taps/delays consumed by `rxAddInput`; never add another absolute gain, bulk delay, or bulk Doppler term.
- The real bundle's maximum relative excess delay is `0.00110293139355125 s` (about `33882.05` samples at 30.72 Msps). Since `channel_desc_t::channel_length` is `uint8_t`, the existing short FIR cannot represent it safely.
- Step 4 keeps `channel_desc_t` unchanged and introduces per-block sparse convolution with explicit RFsim input history. The tested history is `ceil(max_delay * sample_rate) + 3 = 33886` samples.
- The real-bundle adapter test passes for 11 paths and verifies that a QD time outside the bundle produces zero signal. STK remains responsible for later absolute gain/noise and bulk Doppler stages.
