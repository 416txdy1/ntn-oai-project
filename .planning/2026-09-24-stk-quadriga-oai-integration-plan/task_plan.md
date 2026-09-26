# Task Plan: STK + QuaDRiGa + OAI stepwise integration

## Goal
Integrate QuaDRiGa into the existing deterministic STK-to-RFsim architecture one reversible, verified step at a time.

## Next Step
Await user review before Step 4 RFsim IQ multipath integration.

## Current Phase
Step 3A reader numerical re-verification complete

## Phases

### Phase 1: Requirements & Discovery
- [x] Understand user intent
- [x] Identify constraints
- [x] Document architecture and integration boundaries
- **Status:** complete

### Phase 2: Planning & Structure
- [x] Define approach
- [x] Create project structure
- **Status:** complete

### Phase 3: Implementation
- [x] Execute the plan
- [x] Write to files before executing
- **Status:** complete

### Phase 4: Testing & Verification
- [x] Verify requirements met
- [x] Document test results
- **Status:** complete

### Phase 5: Delivery
- [x] Review outputs
- [x] Deliver Step 2 checkpoint
- **Status:** complete

### Phase 6: Step 2 Runtime Validation
- [x] Locate and fingerprint the supplied MATLAB/QuaDRiGa runtime
- [x] Execute a real STKTRACE2-to-QDCHANNEL1 export
- [x] Fix runtime/API mismatches without starting OAI integration
- [x] Validate the generated bundle and all regressions
- [x] Commit a reversible runtime-validated checkpoint
- **Status:** complete

### Phase 7: Step 2A Link-Budget and Duplicate-Impairment Audit
- [x] Map every STK and QuaDRiGa output quantity to the final channel equation
- [x] Numerically compare STK gain, geometric FSPL, QuaDRiGa raw power variation, and residual gain
- [x] Remove or isolate any duplicated deterministic path-loss component
- [x] Add automated audit tests and regenerate real runtime bundles
- [x] Run all regressions and prepare a reversible audit checkpoint
- **Status:** complete

### Phase 8: Step 3 QDCHANNEL1 C Reader
- [x] Implement the standalone C reader and public API
- [x] Validate manifest, payload hashes, dimensions, and provenance
- [x] Add interpolation, out-of-range mute, and malformed-input tests
- [x] Preserve the implementation in Git commit `8b1bb1d`
- **Status:** complete

### Phase 9: Step 3A Numerical Re-verification
- [x] Re-run strict compile, static analysis, sanitizers, and malformed-input tests
- [x] Re-validate real downlink and uplink bundles numerically
- [x] Re-run link-budget duplicate-loss audit and STK/RFsim regressions
- [x] Record exact commands, metrics, and a reversible Git checkpoint
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Execute exactly one step per user turn | User requested review and reporting after every step |
| Use file backups instead of Git commits for Step 0 | Existing project and OAI worktrees are dirty; this preserves user changes without staging or committing them |
| Run commands in a visible PowerShell 7 window and save a transcript | User requested visibility into exact commands and outputs |
| Step 0 backup is the rollback point | It contains selected project/OAI sources, SHA256 values, commits, manifest, restore notes, transcript, and full regression output |
| Preserve the verified baseline on `zky` after explicit user authorization | OAI integration sources and project provenance are committed separately, while credentials, raw logs, generated STK data, and complete backup copies remain excluded |
| Step 1 changes only the offline interface contract and project skeleton | Keep RFsim behavior unchanged until the exported QuaDRiGa data format is independently validated |
| Step 2 first separated runtime-independent conversion from the QuaDRiGa API call | This allowed format/math verification before the runtime was supplied; MATLAB R2023b and QuaDRiGa 2.8.1-0 have now validated the same interface end to end |
| Keep the canonical satellite-Tx/ground-Rx NTN orientation for both directions | The current SISO uplink uses channel reciprocity and a distinct manifest direction; future MIMO support must transpose antenna dimensions explicitly |
| Disable production residual large-scale gain until shadow fading is independently available per snapshot | QuaDRiGa total path gain duplicates STK range loss; the current channel exposes only a scalar sf_parset for the single segment, so zero dB is the only unambiguous non-duplicating value |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| First visible terminal launch used a missing Program Files pwsh path | Retried with the pwsh path returned by Get-Command |
| First regression reached git diff --check and waited in pager | Terminated only the validated pager PID, then reran visibly with GIT_PAGER=cat and saved full output |
| First Step 1 completion check read a stale marker from an older discovery script | Preserve the stale marker for audit, use `STEP01_CONTRACT_DISCOVERY_DONE.json`, and rerun the verified script in a visible terminal |
| Windows PowerShell launch did not produce the unique Step 1 marker | Switched to the current PowerShell 7 runtime with explicit `-NoExit -Command`; discovery then completed successfully |
| WSL could not enter the project through `/mnt/e` during Step 2 verification | Copied only `local_ntn/` to a unique WSL `/tmp` directory, ran the unchanged regression script there, and separately ran `git diff --check` in the main project |
| Initial direction/hash assertion used a nonexistent top-level `link_direction` field | Corrected the check to `radio.link_direction`; all four binary hashes matched for original downlink, repeated downlink, and reciprocal uplink |
