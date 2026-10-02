#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
source scripts/env.sh
python3 local_ntn/test_network_config.py
python3 local_ntn/test_preflight.py
python3 local_ntn/test_local_setup.py
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py
python3 quadriga/tests/test_rfsim_history.py
python3 -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_channel_math quadriga.tests.test_audit_link_budget
for direction in downlink uplink; do
 python3 -m quadriga.tools.audit_link_budget "examples/fdd-pass/$direction" "$OAI_STK_TRACE"
 python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "examples/fdd-pass/$direction" --real-trace "$OAI_STK_TRACE"
 python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle "examples/fdd-pass/$direction" --trace "$OAI_STK_TRACE"
done