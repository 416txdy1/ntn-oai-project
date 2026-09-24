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
