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

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Do not create a Git commit for Step 0 | Existing user changes and generated scenario data should not be staged or bundled into an agent-created commit |
| Do not back up UE credentials, databases, raw logs, or build output | Protect secrets and keep rollback scope limited to integration source files |
| Commit through an isolated OAI worktree | Preserve all existing uncommitted changes in the `develop` worktree while creating a clean, reviewable `zky` commit |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| git diff --check opened an interactive pager | Exact pager PID was validated and terminated; verification rerun used GIT_PAGER=cat |

## Resources
- .planning/2026-09-24-stk-quadriga-oai-integration-plan/backups/step-00-baseline-20260924-161100
