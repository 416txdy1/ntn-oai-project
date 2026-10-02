#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
source "$ROOT/scripts/env.sh"
mkdir -p "$ROOT/.runtime/iperf3/lib"
docker cp "$OAI_EXT_DN_CONTAINER:/usr/bin/iperf3" "$OAI_IPERF3_BIN"
docker cp -L "$OAI_EXT_DN_CONTAINER:/usr/lib/x86_64-linux-gnu/libiperf.so.0" "$OAI_IPERF3_LIBRARY_PATH/libiperf.so.0"
LD_LIBRARY_PATH="$OAI_IPERF3_LIBRARY_PATH" "$OAI_IPERF3_BIN" --version