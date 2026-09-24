#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
REPO=$(python3 "$HERE/paths.py" repo)
UE_CONFIG=$(python3 "$HERE/paths.py" ue)
export OAI_STK_TRACE="$HERE/stk_trace.csv"
export OAI_STK_TRACE_RATE="${OAI_STK_TRACE_RATE:-0}"
unset OAI_STK_PORT
# This bounded launcher generates initial SIB19/TA from the first trace row.
unset OAI_STK_TRACE_EPOCH
cd "$REPO/cmake_targets/ran_build/build"
case "${1:-}" in
  gnb)
    exec ./nr-softmodem -O "$HERE/gnb.local.conf" --rfsim
    ;;
  ue)
    python3 "$HERE/verify_network.py"
    read -r DELAY < "$HERE/initial_delay_ms.txt"
    exec ip netns exec oai-stk-ue ./nr-uesoftmodem \
      -O "$UE_CONFIG" \
      --rfsimulator.[0].serveraddr 10.201.0.1 --rfsimulator.[0].prop_delay "$DELAY" \
      --band 254 -C 2488400000 --CO -873500000 -r 25 --numerology 0 --ssb 60 \
      --rfsim --rfsimulator.[0].options chanmod --time-sync-I 0.1 \
      --autonomous-ta --cont-fo-comp 2 --num-ul-actors 1
    ;;
  *) echo 'Usage: sudo OAI_STK_TRACE_RATE=0 bash run_local.sh gnb|ue';exit 2;;
esac
