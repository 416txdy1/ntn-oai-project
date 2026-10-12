#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" = 0 || { echo 'Run with sudo'; exit 1; }
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
# Python resolves names/addresses and checks inode + ifindex ownership for every operation.
exec python3 "$HERE/verify_network.py" --action up "$@"
