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

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Do not create a Git commit for Step 0 | Existing user changes and generated scenario data should not be staged or bundled into an agent-created commit |
| Do not back up UE credentials, databases, raw logs, or build output | Protect secrets and keep rollback scope limited to integration source files |
| Commit through an isolated OAI worktree | Preserve all existing uncommitted changes in the `develop` worktree while creating a clean, reviewable `zky` commit |
| Use JSON manifest plus little-endian binary arrays | A later RFsim C/C++ reader can stream the files without MATLAB, HDF5 or NumPy runtime dependencies |
| Keep STK bulk delay/Doppler/absolute gain authoritative | Avoid applying free-space loss, propagation time or satellite Doppler twice |
| Store normalized coefficients and zero-mean residual gain from QuaDRiGa | Preserve multipath fading and shadowing variation while retaining the existing STK link budget reference |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| git diff --check opened an interactive pager | Exact pager PID was validated and terminated; verification rerun used GIT_PAGER=cat |
| A stale Step 1 marker referenced `local_ntn/test_stk_trace.c` | Actual trace tests are `test_trace.c` and `test_trace_validation.c`; current discovery uses a unique result marker |
| Windows PowerShell argument passing did not execute the updated discovery script reliably | PowerShell 7 with explicit `-NoExit -Command` produced the expected unique marker and transcript |

## Resources
- .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100
- https://github.com/fraunhoferhhi/QuaDRiGa
- https://quadriga-channel-model.de/download/534245
- https://github.com/fraunhoferhhi/QuaDRiGa/blob/main/quadriga_src/%40qd_channel/combine_tx_rx.m
