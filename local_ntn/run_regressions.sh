#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE/.."
set -x
cc -Wall -Wextra -Werror -I local_ntn local_ntn/test_trace.c local_ntn/stk_trace.c -lm -o /tmp/oai-stk-trace-test
/tmp/oai-stk-trace-test
python3 local_ntn/test_legacy_interpolation.py
PYTEST_PYTHON=${PYTEST_PYTHON:-python3}
if [ -x .runtime/test-venv/bin/python ]; then PYTEST_PYTHON=.runtime/test-venv/bin/python; fi
"$PYTEST_PYTHON" -m pytest -q local_ntn/test_stk_schedule.py
python3 local_ntn/test_trace_validation.py
python3 local_ntn/test_real_iq.py --sanitize
python3 local_ntn/test_local_setup.py
python3 -m py_compile local_ntn/paths.py local_ntn/prepare_local.py local_ntn/experiment.py local_ntn/provision_subscriber.py local_ntn/audit_auth.py local_ntn/validate_dynamic.py local_ntn/export_stk_trace.py
bash -n local_ntn/run_local.sh local_ntn/local_network.sh
git diff --check
