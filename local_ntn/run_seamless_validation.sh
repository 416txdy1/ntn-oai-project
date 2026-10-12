#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
# RuntimeConfig selects the pseudo handover profile and dedicated run paths.
exec python3 "$HERE/test_seamless.py"  "$@"
