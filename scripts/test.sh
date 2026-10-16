#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
source scripts/env.sh
python3 scripts/test_ntn_dtx_config.py
python3 scripts/test_handover_metrics.py
python3 scripts/test_physical_start.py
python3 scripts/test_handover_driver.py
python3 local_ntn/test_manifest_provenance.py
python3 local_ntn/test_numeric_audit.py
python3 scripts/test_full_pass.py
python3 scripts/test_monotonic_ping.py
python3 local_ntn/test_blend_interpolation.py
python3 local_ntn/test_stk_timing_assist.py
python3 local_ntn/test_network_config.py
python3 local_ntn/test_preflight.py
python3 local_ntn/test_local_setup.py
python3 local_ntn/test_legacy_interpolation.py
PYTEST_PYTHON=${PYTEST_PYTHON:-python3}
if [ -x .runtime/test-venv/bin/python ]; then PYTEST_PYTHON=.runtime/test-venv/bin/python; fi
"$PYTEST_PYTHON" -m pytest -q local_ntn/test_stk_schedule.py
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py --sanitize
python3 quadriga/tests/test_rfsim_history.py
python3 -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_channel_math quadriga.tests.test_audit_link_budget quadriga.tests.test_handover_bundle
for direction in downlink uplink; do
 python3 -m quadriga.tools.audit_link_budget "examples/fdd-pass/$direction" "$ROOT/examples/fdd-pass/trace.csv"
 python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "examples/fdd-pass/$direction" --real-trace "$ROOT/examples/fdd-pass/trace.csv"
 python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle "examples/fdd-pass/$direction" --trace "$ROOT/examples/fdd-pass/trace.csv"
done
for dataset in seamless firsthandover; do
 if [ "$dataset" = seamless ]; then bundle_root=examples/handover; else bundle_root=examples/handover/firsthandover; fi
 trace="local_ntn/stk_trace_${dataset}.csv"
 for direction in downlink uplink; do
  python3 -m quadriga.tools.audit_link_budget "$bundle_root/$direction" "$trace"
  python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "$bundle_root/$direction" --real-trace "$trace"
  python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle "$bundle_root/$direction" --trace "$trace"
 done
done
python3 scripts/test_tx_predictor_contract.py --root "$ROOT"
python3 scripts/test_rx_tracker_iq.py --root "$ROOT"

python3 scripts/test_diag_window.py
python3 scripts/test_gnb_ta_diag.py
