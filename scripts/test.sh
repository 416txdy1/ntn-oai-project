#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
case "${OAI_SPATIAL_MODE:-siso}" in
 miso2) source scripts/env_miso.sh ;;
 miso4) source scripts/env_miso4.sh ;;
 miso4-subarray) source scripts/env_subarray4.sh ;;
 siso) source scripts/env.sh ;;
 *) echo "不支持的空间模式"; exit 2 ;;
esac
python3 scripts/test_full_pass.py
python3 scripts/test_iq_udp.py
python3 scripts/test_spatial_audit.py
python3 local_ntn/test_feedback_diagnostics.py
python3 scripts/test_monotonic_ping.py
python3 local_ntn/test_blend_interpolation.py
python3 local_ntn/test_stk_timing_assist.py
python3 local_ntn/test_network_config.py
python3 local_ntn/test_preflight.py
python3 local_ntn/test_spatial_config.py
python3 local_ntn/test_local_setup.py
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py
python3 quadriga/tests/test_rfsim_history.py
python3 -m unittest quadriga.tests.test_validate_bundle quadriga.tests.test_channel_math quadriga.tests.test_audit_link_budget
for direction in downlink uplink; do
 if [[ "$direction" == downlink ]]; then bundle="$OAI_QD_DL_CHANNEL"; else bundle="$OAI_QD_UL_CHANNEL"; fi
 python3 -m quadriga.tools.audit_link_budget "$bundle" "$OAI_STK_TRACE"
 python3 quadriga/tests/run_qd_channel_reader_tests.py --real-bundle "$bundle" --real-trace "$OAI_STK_TRACE"
 python3 quadriga/tests/run_qd_rfsim_adapter_test.py --sanitize --oai-repo "$OAI_REPO" --build-repo "$OAI_REPO" --bundle "$bundle" --trace "$OAI_STK_TRACE"
done
