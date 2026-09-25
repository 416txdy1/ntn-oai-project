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

## Resources
- .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100
- https://github.com/fraunhoferhhi/QuaDRiGa
- https://quadriga-channel-model.de/download/534245
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/quadriga_src/%40qd_channel/combine_tx_rx.m
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/tutorials/t14_dual_mobility.m
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/tutorials/calib_3GPP_38821_ntn.m
