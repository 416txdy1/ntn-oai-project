# Task Plan: STK + QuaDRiGa + OAI stepwise integration

## Goal
Integrate QuaDRiGa into the existing deterministic STK-to-RFsim architecture one reversible, verified step at a time.

## Next Step
Wait for user review before Step 2: implement the MATLAB/Octave STK-to-QuaDRiGa exporter against QDCHANNEL1.

## Current Phase
Paused after Step 1 - QDCHANNEL1 contract and project skeleton complete

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
- [ ] Execute the plan
- [ ] Write to files before executing
- **Status:** pending

### Phase 4: Testing & Verification
- [ ] Verify requirements met
- [ ] Document test results
- **Status:** pending

### Phase 5: Delivery
- [ ] Review outputs
- [ ] Deliver to user
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Execute exactly one step per user turn | User requested review and reporting after every step |
| Use file backups instead of Git commits for Step 0 | Existing project and OAI worktrees are dirty; this preserves user changes without staging or committing them |
| Run commands in a visible PowerShell 7 window and save a transcript | User requested visibility into exact commands and outputs |
| Step 0 backup is the rollback point | It contains selected project/OAI sources, SHA256 values, commits, manifest, restore notes, transcript, and full regression output |
| Preserve the verified baseline on `zky` after explicit user authorization | OAI integration sources and project provenance are committed separately, while credentials, raw logs, generated STK data, and complete backup copies remain excluded |
| Step 1 changes only the offline interface contract and project skeleton | Keep RFsim behavior unchanged until the exported QuaDRiGa data format is independently validated |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| First visible terminal launch used a missing Program Files pwsh path | Retried with the pwsh path returned by Get-Command |
| First regression reached git diff --check and waited in pager | Terminated only the validated pager PID, then reran visibly with GIT_PAGER=cat and saved full output |
| First Step 1 completion check read a stale marker from an older discovery script | Preserve the stale marker for audit, use `STEP01_CONTRACT_DISCOVERY_DONE.json`, and rerun the verified script in a visible terminal |
| Windows PowerShell launch did not produce the unique Step 1 marker | Switched to the current PowerShell 7 runtime with explicit `-NoExit -Command`; discovery then completed successfully |
