#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
BUILD_DIR=$(python3 "$HERE/paths.py" build)
UE_CONFIG=$(python3 "$HERE/paths.py" ue)
STK_TRACE=$(python3 "$HERE/paths.py" trace)
export OAI_STK_TRACE="$STK_TRACE"
export OAI_STK_TRACE_RATE="${OAI_STK_TRACE_RATE:-0}"
unset OAI_STK_PORT
# This bounded launcher generates initial SIB19/TA from the first trace row.
unset OAI_STK_TRACE_EPOCH
DL_FREQUENCY=$(python3 "$HERE/paths.py" dl-frequency)
UL_OFFSET=$(python3 "$HERE/paths.py" ul-offset)
# 库与二进制必须来自同一次构建。
export LD_LIBRARY_PATH="$BUILD_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$BUILD_DIR"
case "${1:-}" in
  gnb)
    case "${OAI_SPATIAL_MODE:-siso}" in
      siso) CONFIG="$HERE/gnb.local.conf" ;;
      miso2) CONFIG="$HERE/gnb.miso.conf" ;;
      *) echo 'Unsupported OAI_SPATIAL_MODE'; exit 2 ;;
    esac
    exec ./nr-softmodem -O "$CONFIG" --rfsim
    ;;
  ue)
    python3 "$HERE/verify_network.py"
    read -r DELAY < "$HERE/initial_delay_ms.txt"
    exec ip netns exec oai-stk-ue ./nr-uesoftmodem \
      -O "$UE_CONFIG" \
      --rfsimulator.[0].serveraddr 10.201.0.1 --rfsimulator.[0].prop_delay "$DELAY" \
      --band 254 -C "$DL_FREQUENCY" --CO "$UL_OFFSET" -r 25 --numerology 0 --ssb 60 \
      --rfsim --rfsimulator.[0].options chanmod --time-sync-I 0.1 \
      --autonomous-ta --cont-fo-comp 2 --num-ul-actors 1
    ;;
  *) echo 'Usage: sudo OAI_STK_TRACE_RATE=0 bash run_local.sh gnb|ue';exit 2;;
esac
