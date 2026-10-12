#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
# Profile/run selectors are resolved before importing paths; all consumers share this env.
if [[ ${OAI_NTN_PROFILE:-zky} == zky ]]; then
  export OAI_NTN_RUN_DIR="${OAI_NTN_RUN_DIR:-$HERE}"
fi
RUNTIME_EXPORTS=$(python3 "$HERE/runtime_config.py" --format env)
source /dev/stdin <<< "$RUNTIME_EXPORTS"
BUILD_DIR=$OAI_BUILD_DIR
UE_CONFIG=$OAI_UE_CONFIG
export OAI_STK_TRACE_RATE="${OAI_STK_TRACE_RATE:-0}"
unset OAI_STK_PORT
if [[ $OAI_NTN_PROFILE == zky ]]; then
  unset OAI_STK_TRACE_EPOCH
  export LD_LIBRARY_PATH="$BUILD_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
else
  # Dedicated source/build supplies every OAI shared library; inherited builds are excluded.
  export LD_LIBRARY_PATH="$BUILD_DIR"
fi
cd "$BUILD_DIR"
case "${1:-}" in
  gnb)
    exec ./nr-softmodem -O "$OAI_GNB_CONFIG" --rfsim \
      --rfsimulator.[0].serveraddr server --rfsimulator.[0].serverport "$OAI_RF_PORT"
    ;;
  ue)
    python3 "$HERE/verify_network.py" --profile "$OAI_NTN_PROFILE" --run-id "$OAI_NTN_RUN_ID"
    read -r DELAY < "$OAI_INITIAL_DELAY_FILE"
    exec ip netns exec "$OAI_NTN_NAMESPACE" ./nr-uesoftmodem \
      -O "$UE_CONFIG" \
      --rfsimulator.[0].serveraddr "$OAI_RF_HOST_IP" --rfsimulator.[0].serverport "$OAI_RF_PORT" \
      --rfsimulator.[0].prop_delay "$DELAY" \
      --band 254 -C 2488400000 --CO -873500000 -r 25 --numerology 0 --ssb 60 \
      --rfsim --rfsimulator.[0].options chanmod --time-sync-I 0.1 \
      --autonomous-ta --cont-fo-comp 2 --num-ul-actors 1
    ;;
  *) echo 'Usage: sudo -E bash run_local.sh gnb|ue';exit 2;;
esac
