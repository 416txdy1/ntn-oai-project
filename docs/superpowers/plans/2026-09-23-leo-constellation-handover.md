# LEO Constellation Handover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create an STK LEO constellation scenario, select the best in-view satellite for the gNB/UE link, export a deterministic OAI trace plus handover schedule, and log the active satellite identifier.

**Architecture:** Clone a verified base LEO satellite into a small phased constellation, using phase-separated orbital states. STK evaluates elevation/access for every satellite and emits one selected-link trace plus a sidecar schedule. OAI replays the selected trace on the RFsim IQ clock and reads the sidecar only for human-readable satellite/handover logging; RF behavior remains driven by the trace.

**Tech Stack:** STK 12 Python API (`agi.stk12`), Python CSV/JSON, C RFsim channel model, existing local NTN trace tests, OAI RFsim build.

## Global Constraints

- Preserve the existing single-satellite scene and OAI templates; create a new scenario/output directory.
- Never commit subscriber secrets, passwords, private keys, raw UE logs, or build trees.
- Use the RFsim IQ sample clock as the deterministic time base; gNB and UE use the same trace and rate.
- Do not use broad process-kill commands.

## Review Focus

- No satellite is above the acquisition elevation: export invalid RF samples and do not invent a link.
- Current satellite drops below the release mask while another is visible: perform a single deterministic handover and log both IDs.
- Trace/schedule timestamps differ by one sample: preserve monotonic schedule lookup and keep channel replay deterministic.
- STK is unavailable or a copied satellite cannot be propagated: fail with a clear message and leave the original scene untouched.
- OAI runs without a schedule sidecar: RF replay still works and logs `satellite_id=unknown`.

---

### Task 1: Add a reproducible constellation scenario builder

**Files:**
- Create: `local_ntn/create_leo_constellation.py`
- Create: `local_ntn/constellation_config.json`
- Create: `docs/leo_constellation.md`

**Interfaces:**
- CLI `python local_ntn/create_leo_constellation.py --base-scenario <Scenario1.sc> --output-dir <dir> --count 6 --planes 3 --phase-deg 30`
- Produces a saved STK scenario and a JSON manifest containing satellite names, planes, phase offsets, and object paths.

- [ ] **Step 1: Define the default six-satellite layout**

Use three planes with two satellites per plane, 30° phase separation, 10° acquisition/release elevation masks, and names `OAI_LEO_P01_S01` … `OAI_LEO_P03_S02`. Keep the existing base orbit/propagator and copy it before editing the new objects.

- [ ] **Step 2: Implement safe STK attach/load and object cloning**

Attach to an active STK instance when available; otherwise start STK and load the supplied scenario. Copy the base satellite through the STK object collection API, never mutate the original base object, and save under a new output directory.

- [ ] **Step 3: Implement phase offsets and endpoint creation**

For each copied satellite, adjust the orbital anomaly using the propagator’s classical orbit-state representation. Create per-satellite feeder/service endpoint objects only where required by the exporter, and retain the existing gNB/UE ground objects.

- [ ] **Step 4: Add a smoke test mode**

`--dry-run` prints the intended object names and phase offsets without saving. Normal mode saves the `.sc` file and manifest and reports the STK scenario path.

- [ ] **Step 5: Run the builder against a copy**

Run the CLI with the current verified `Scenario1.sc`; confirm six satellites are present and the original scene file hash is unchanged.

### Task 2: Export selected-satellite trace and handover schedule

**Files:**
- Modify: `local_ntn/export_stk_trace.py`
- Create: `local_ntn/satellite_schedule.py`
- Modify: `local_ntn/README.md`

**Interfaces:**
- CLI adds `--satellites`, `--schedule-out`, `--acquire-elev-deg`, `--release-elev-deg`, `--min-dwell-s`.
- `satellite_schedule.select_satellite(candidates, current_id, acquire_elev, release_elev, min_dwell_s)` returns `(selected_id, switched)`.

- [ ] **Step 1: Add a pure selection test fixture**

Use deterministic candidate rows to assert highest-elevation selection, release-mask handover, no-candidate invalid state, and no immediate ping-pong during the minimum dwell interval.

- [ ] **Step 2: Implement schedule selection**

At each export epoch, query every constellation satellite’s gNB/UE elevation/access state, retain the current satellite above the release mask, otherwise choose the highest-elevation candidate above acquisition mask, and record `time,satellite_id,elevation_deg,visible,switched`.

- [ ] **Step 3: Export OAI trace using the selected satellite**

Keep the existing `STKTRACE2` 22-field format unchanged. For each row, read position/velocity/link power/CN from the selected satellite; mark RF validity false when no candidate exists. Write a JSON metadata field pointing to the schedule sidecar.

- [ ] **Step 4: Run parser and schedule tests**

Run the trace validation and selection tests; verify schedule rows are monotonic, contain at least one switch in the designed interval, and selected IDs exist in the manifest.

### Task 3: Log the active satellite in OAI RFsim

**Files:**
- Create: `local_ntn/stk_schedule.h`
- Create: `local_ntn/stk_schedule.c`
- Modify: `local_ntn/stk_trace_channel.c`
- Modify: `local_ntn/run_local.sh`
- Modify: `local_ntn/README.md`

**Interfaces:**
- Environment `OAI_STK_SCHEDULE` points to the schedule CSV.
- `stk_schedule_lookup(time_s, result)` returns the active ID, elevation, and switch flag; absent files return `unknown` without changing RF behavior.

- [ ] **Step 1: Add schedule parser tests**

Test exact timestamp, interpolation/previous-row lookup, switch detection, malformed rows, and missing-file fallback.

- [ ] **Step 2: Implement bounded CSV schedule reader**

Load and validate a small schedule sidecar once at startup, keep rows monotonic, and binary-search by STK epoch. Reject non-finite times and cap the row count to prevent accidental unbounded allocation.

- [ ] **Step 3: Integrate logging at the existing IQ-second log point**

When the active satellite changes, print `[HW] STK satellite handover: <old> -> <new>`; in each periodic `STKTRACE2` line append `satellite_id=<id> elevation_deg=<value>`. Do not alter delay, Doppler, gain, noise, or validity calculations.

- [ ] **Step 4: Run unit tests and compile the local channel module**

Run the schedule/parser tests and the project’s trace/IQ regression tests. If the external OAI source is available, rebuild `rfsimulator` with the documented command.

### Task 4: End-to-end constellation test and documentation

**Files:**
- Create: `local_ntn/test_constellation_handover.py`
- Modify: `docs/leo_constellation.md`

**Interfaces:**
- CLI `python local_ntn/test_constellation_handover.py --trace <csv> --schedule <csv>` validates that the trace is readable, schedule IDs are present, and at least one handover occurs.

- [ ] **Step 1: Run deterministic offline regression**

Run the trace parser, IQ regression, schedule tests, and the handover validator; save only aggregate results, not raw UE logs.

- [ ] **Step 2: Run STK export smoke test**

Export a short interval at 1 Hz and verify one or more handovers or, if the chosen interval has no handover, report the visible interval and extend the interval without modifying RFsim code.

- [ ] **Step 3: Run OAI connectivity test when binaries/core are available**

Start core, gNB, and UE using the existing local controller, verify `oaitun_ue1`, run bounded ping/iperf, and report packet loss/throughput plus the satellite IDs observed in the gNB/UE logs.

- [ ] **Step 4: Record exact commands and results**

Update the documentation with commands, output paths, assumptions, and any STK-license/runtime limitation. Commit only source/config/docs and push after verification.
