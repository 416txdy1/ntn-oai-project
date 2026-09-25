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
