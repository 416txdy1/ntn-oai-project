# Progress Log

## Session: 2026-09-24

### Current Status
- **Phase:** Step 0 complete; awaiting user review before Step 1
- **Started:** 2026-09-24

### Actions Taken
- Opened visible PowerShell 7 windows for baseline capture and regression output.
- Recorded project and OAI commits and displayed both worktree states.
- Backed up 19 project files and 14 OAI files relevant to STK/RFsim integration.
- Generated SHA256 manifest, rollback notes, command transcript, and full regression log.
- Did not copy credentials, databases, raw UE logs, keys, or build trees.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Trace parser and sample-clock regression | PASS | PASS | PASS |
| Trace physical validation | PASS | PASS | PASS |
| Actual rxAddInput IQ regression | PASS | PASS; 10 dB energy ratio 0.1, outage 0, noise ratio 0.0384 | PASS |
| Legacy SAT_LEO_STK visibility | PASS | PASS | PASS |
| Local config and failure-propagation regression | PASS | PASS | PASS |
| Python compile and Bash syntax | PASS | PASS | PASS |
| git diff --check | Exit 0 | Exit 0 with CRLF notices | PASS |

### Errors
| Error | Resolution |
|-------|------------|
| Missing C:\Program Files\PowerShell\7\pwsh.exe | Used the pwsh executable returned by Get-Command |
| Interactive pager blocked git diff --check | Terminated only validated pager PID 437869; reran with GIT_PAGER=cat and captured full output |

### Git Preservation
- User explicitly authorized committing the required baseline content to `zky` with `zky <1119045132@qq.com>`.
- Created an isolated OAI worktree at `/home/duyaya/OAI/oai-zky-preserve` so the dirty `develop` worktree remained untouched.
- Copied 14 verified STK/RFsim integration source files from the Step 0 backup and rechecked every SHA256 value.
- OAI `zky` commit: `219576f68c` (`rfsimulator: preserve STK trace integration baseline`).
- Excluded UE/core-network configuration, credentials, raw logs, build output, generated STK data, and complete backup source copies.

## Session: 2026-09-24 - Step 1

### Current Status
- **Phase:** Step 1 complete - awaiting user review before Step 2

### Actions Taken
- Started read-only discovery in a visible PowerShell window.
- Confirmed the project currently provides `test_trace.c`, `test_trace_validation.c`, and `test_real_iq.c`; there is no `test_stk_trace.c`.

### Errors
| Error | Resolution |
|-------|------------|
| An existing `STEP01_DISCOVERY_DONE.json` reported missing `local_ntn/test_stk_trace.c` | The marker belonged to an older script run; preserved it for audit and changed the current script to a unique completion marker before rerunning |
| The saved internal apply-patch executable path no longer existed after a desktop update | Located the current executable and did not retry the stale path |
| The first multi-file patch used a phase status line without its Markdown list marker | Re-read the current plan and applied a targeted patch matching the actual `- **Status:**` line |
| Windows PowerShell exited without writing the new discovery marker | Used the current PowerShell 7 runtime and explicit `-NoExit -Command`; the visible rerun succeeded |

### Files Added
- `quadriga/README.md`: STK/QuaDRiGa responsibility boundary, formula, binary layout and timing rules.
- `quadriga/schema/channel_bundle_v1.schema.json`: QDCHANNEL1 manifest schema.
- `quadriga/tools/create_example_bundle.py`: deterministic SISO two-path example generator.
- `quadriga/tools/validate_bundle.py`: dependency-free streaming validator.
- `quadriga/tests/test_validate_bundle.py`: valid bundle, checksum, time ordering, path traversal and residual-gain tests.
- `quadriga/examples/siso_two_path/`: generated reference manifest and four small binary arrays.

### Verification Results
| Command | Result |
|---------|--------|
| `python -m quadriga.tools.create_example_bundle quadriga/examples/siso_two_path` | PASS |
| `python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path` | PASS; 3 snapshots, SISO, 2 paths, 0-0.002 s |
| `python -m unittest -v quadriga.tests.test_validate_bundle` | PASS; 5 tests in 0.073 s |
| `python -m json.tool quadriga/schema/channel_bundle_v1.schema.json` | PASS |
| `python -m py_compile ...` | PASS |
| `wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project && GIT_PAGER=cat bash local_ntn/run_regressions.sh"` | PASS; exit 0 |
| `git diff --check` | PASS; exit 0 |

### Impact
- No OAI source, RFsim behavior, STKTRACE2 parser, runtime configuration or experiment result was changed.
- No new Python or system dependency was added.

## Session: 2026-09-25 - Step 2

### Current Status
- **Phase:** Step 2 complete - awaiting user review before Step 3

### Environment Discovery
- Restored the pinned plan and inspected the worktree in a visible PowerShell 7 window.
- Neither Windows nor WSL exposes `matlab`, `octave`, or `octave-cli` on PATH.
- `QUADRIGA_PATH` is not configured.
- No heavyweight runtime or QuaDRiGa source was installed; real channel generation cannot be claimed on this machine yet.

### Changes
- Added a MATLAB/Octave STKTRACE2 parser and WGS84 ECEF-to-ENU converter.
- Added a dual-mobility QuaDRiGa export entry point for separate downlink/uplink SISO service-link bundles.
- Added common-phase removal so STK remains authoritative for bulk Doppler while QuaDRiGa retains relative multipath phase.
- Added QDCHANNEL1 little-endian serialization, manifest creation, SHA256 provenance and explicit QuaDRiGa-path checks.
- Added a Python standard-library reference implementation and four mathematical regression tests.
- Extended QDCHANNEL1 v1 with required `radio.link_direction`, updated the validator and regenerated the example manifest.
- Updated the QuaDRiGa README with the export data flow, MATLAB example and current limitations.

### Verification Results
| Command | Result |
|---------|--------|
| `python -m quadriga.tools.create_example_bundle quadriga/examples/siso_two_path` | PASS |
| `python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path` | PASS; direction downlink, 3 snapshots, SISO, 2 paths |
| `python -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_channel_math -v` | PASS; 10 tests |
| `python -m py_compile ...` and `python -m json.tool ...` | PASS |
| `bash local_ntn/run_regressions.sh` in isolated WSL `/tmp` copy | PASS; trace parser, physical validation, real IQ, legacy visibility, local setup, syntax |
| `git diff --check` in the main project | PASS |

### Impact and Limitations
- No OAI source, RFsim runtime behavior, experiment configuration, credentials, logs or generated STK scenario files were changed.
- No dependency was installed.
- MATLAB/Octave/QuaDRiGa is absent on this machine, so the API-facing `.m` path has been reviewed but not executed end to end.
- The initial exporter intentionally supports one satellite-to-UE SISO service link; MIMO arrays and feeder-link modeling remain later work.

### Verification Environment Issue
- Direct WSL access to `/mnt/e` returned `Bad file descriptor` twice.
- The unchanged `local_ntn/` directory was copied to `/tmp/ntn-oai-step02-regression-20260925-1105` for isolated regression execution; it is not part of the project or commit.

## Session: 2026-09-25 - Step 2 Runtime Continuation

### Current Status
- **Phase:** Locating user-supplied MATLAB and QuaDRiGa runtime

### Discovery
- The active plan remains `2026-09-24-stk-quadriga-oai-integration-plan`.
- The Windows project root and `quadriga/` tree do not currently contain `matlab.exe`, `octave*.exe`, `qd_layout.m`, or `qd_simulation_parameters.m`.
- MATLAB/Octave is not currently resolved from the Windows PATH.
- Next search scope is the external WSL/OAI source root and standard MATLAB installation directories.
- User-provided paths were verified: MATLAB R2023b and QuaDRiGa 2.8.1-0 sources both exist.
- Compared the real STKTRACE2 header with the MATLAB parser and found a magic-line mismatch plus reversed DL/UL validity columns; the parser was corrected before the first runtime attempt.
- MATLAB R2023b successfully parsed the real blend trace as 1387 snapshots with 1387 valid DL and UL rows.
- The first parser-check command failed only because its expected count was incorrectly set to 1386; the file has two non-data lines plus 1387 data rows, so the assertion will be corrected and rerun.
- The corrected MATLAB parser test passed for all 1387 real snapshots.
- The first full QuaDRiGa export reached qd_layout.get_channels but failed with Each track must have a movement profile; the STK position assignment needs the QuaDRiGa 2.8.1 movement-profile API.
- Local QuaDRiGa source/tutorial review established the fix: attach relative STK time and cumulative 3-D track distance as a 2-by-N movement profile for both Tx and Rx tracks.
- After the movement-profile fix, QuaDRiGa generated the full 1387-snapshot NTN channel in about 4 seconds.
- Normalization then rejected snapshot 1 because the absolute active-path threshold 1e-15 is too high for satellite path powers; the threshold must be relative to each link snapshot.
- Replaced the absolute activity threshold with a per-snapshot relative-to-peak threshold and added a low-absolute-power NTN regression test; all 11 Python tests pass.
- MATLAB and QuaDRiGa then completed the full 1387-snapshot downlink export and wrote a QDCHANNEL1 manifest plus four binary arrays.
- QuaDRiGa warned that the 1-second track grid does not satisfy the 2 GHz sampling theorem; this runtime output validates the offline interface, not millisecond-scale residual Doppler fidelity.
- Independent validation reached the generated manifest but rejected random_seed because MATLAB encoded the double value in exponent notation, which Python parsed as a float; the writer now casts the seed to int64.
- Runtime direction handling now keeps QuaDRiGa's canonical satellite-Tx/ground-Rx NTN geometry for both directions; SISO uplink is exported through channel reciprocity and labeled separately in the manifest.
- Deterministic downlink repeat and reciprocal uplink both validated at 1387 snapshots, SISO, 11 paths, t=7614..9000 s. All four binary SHA256 values match the original downlink export.
- Final verification passed: 11 Python unit tests, py_compile, JSON schema parsing, generated example validation, isolated WSL trace/IQ regressions, and main-worktree git diff --check.
- Runtime validation evidence is stored in step02-runtime-direction-final-check.txt and step02-runtime-full-regression.txt; generated channel bundles remain untracked.

## Session: 2026-09-25 - Step 2A Link-Budget Audit

### Current Status
- **Phase:** Auditing path-loss, delay, Doppler, and gain composition for duplicate deterministic effects

### Scope
- Verify every stage numerically before OAI integration.
- Treat STK bulk delay, Doppler, and absolute gain as authoritative.
- Test whether QuaDRiGa residual gain still contains range-dependent free-space path-loss variation.
- Correct the exporter and contract if duplicate deterministic loss is detected.

### Baseline Audit Result
- Duplicate range loss is confirmed, not merely suspected: the current residual gain follows free-space variation with slope 0.995961.
- Adding it to STK power increases the free-space slope from 1.203847 to 2.199808.
- Investigating direct QuaDRiGa shadow-fading output before selecting the correction.

### Correction and Runtime Check
- Production residual_gain_db is now fixed at 0 dB; normalized multipath coefficients and relative delays are unchanged.
- Added audit_link_budget.py plus positive and duplicate-loss negative unit tests.
- Python audit/unit suite passes 13 tests.
- Old real bundle is rejected as expected; regenerated real downlink and uplink both pass QDCHANNEL1 validation and the link-budget audit.
- Saved complete real audit metrics in step02a-real-audit-reports.txt.

### Final Verification
- All 13 Python tests pass, including the positive audit path and duplicate-loss rejection case.
- The old real downlink bundle is rejected as a negative control; regenerated downlink and uplink bundles both pass validation and link-budget audit.
- Regenerated downlink and uplink binary payload SHA256 values match; only direction metadata differs.
- Isolated WSL trace parser, IQ regression, visibility gate, setup/config, Python syntax, Bash syntax, and git diff checks all pass.
- Full regression evidence is stored in step02a-full-regression.txt; the isolated WSL verification directory was /tmp/ntn-oai-step02a-audit-20260925-134544.
# Session: 2026-09-26 - Step 3A numerical re-verification

### Current Status
- **Phase:** Step 3A numerical re-verification in progress

### Actions Taken
- Recovered the active plan and confirmed the reader implementation checkpoint is `8b1bb1d` on branch `zky`.
- Opened visible PowerShell windows and saved transcripts for plan recovery and verification-input discovery.
- Found that the plan text was stale at Step 2A and added explicit Step 3 and Step 3A phases before running the audit.
- Located the real corrected downlink and uplink audit bundles in the project runtime-output directory.
- Ran a visible provenance/trace mapping inspection; its transcript is `step03-reverification-trace-map.txt`.

### Errors
- The first direct `apply_patch` call failed during Windows sandbox setup refresh; no file changed. Retried through the desktop apply-patch entry point.
- The first full re-verification launcher stopped before opening the test window because the outer PowerShell interpolated WSL `$(sha256sum ...)`. No test ran and no data changed; replaced the launcher with a literal placeholder template.
- The second launcher attempt also stopped before opening the test window because the orchestration JavaScript runtime has no `btoa` function. No test ran; switched to an explicit byte-to-Base64 encoder.
- The corrected visible run executed 13 Python tests successfully, then stopped at the real downlink link-budget audit with exit code 1. Bundle schema validation itself passed. A focused visible provenance/error diagnostic was started and saved to `step03-reverification-dl-failure.txt`.
- Diagnosed the nonzero audit as a mismatched STK trace selection, not a failed channel metric. Started a visible exact-hash and STKTRACE2 magic-line search, saved as `step03-reverification-find-trace.txt`.
- Re-ran with the matching CSV trace. Python and real-data numerical checks passed through the DL/UL payload comparison; the combined WSL stage returned nonzero without captured native output. Started a focused visible C-reader diagnosis in retained directory `/tmp/ntn-oai-step03-reverify-4uoRR3se`.
- Focused real DL C-reader regression passed completely. The remaining-stage launcher exposed a second shell-boundary quoting issue: PowerShell expanded Bash `$TRACE/$DL/$UL` to empty values, so the UL driver received `.` as its trace. No product code or data failed; the next retry transports the Bash script as Base64.
- Base64-isolated WSL stages passed real UL, static analysis, sanitizers, and STK/RFsim functional regressions. The isolated copy then failed only at `git diff --check` because it intentionally has no `.git`; launched a final visible main-worktree gate and numerical-report capture.
- Captured final DL/UL audit JSON with all numerical invariants passing. The main-worktree `git diff --check` initially found only blank EOF lines in this audit's planning files; removed those lines and retained user changes untouched.

### Final Verification Results
- 13 Python schema/channel-math/link-budget tests: PASS.
- Real downlink and uplink bundle validation: PASS, each 1387 snapshots, SISO, 11 paths.
- Real DL/UL link-budget audit: PASS; no repeated large-scale gain or bulk Doppler phase.
- Strict C reader and malformed-input tests for real DL/UL: PASS.
- GCC static analyzer and ASan/UBSan/leak checks: PASS.
- STK parser and RFsim IQ functional regression: PASS.
- Main worktree `git diff --check`: PASS after EOF cleanup.
