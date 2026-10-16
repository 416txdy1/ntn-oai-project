#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
source scripts/env_subarray4_fidelity.sh
for direction in downlink uplink; do
 if [[ "$direction" == downlink ]]; then bundle="$OAI_QD_DL_CHANNEL"; else bundle="$OAI_QD_UL_CHANNEL"; fi
 python3 -m quadriga.tools.validate_runtime_fidelity "$bundle"
 python3 -m quadriga.tools.audit_link_budget "$bundle" "$OAI_STK_TRACE"
 python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "$bundle" --real-trace "$OAI_STK_TRACE"
 python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle "$bundle" --trace "$OAI_STK_TRACE"
done
