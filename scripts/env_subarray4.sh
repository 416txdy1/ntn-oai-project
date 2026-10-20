#!/usr/bin/env bash
# 16x16 阵列映射为 4 个 8x8 子阵端口；OAI 为 4x1 / 1x4。
export OAI_SPATIAL_MODE=miso4-subarray
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"
if [[ ${OAI_NTN_PROFILE:-zky} == zky ]]; then
  export OAI_QD_DL_CHANNEL="$NTN_ROOT/examples/fdd-miso4-subarray/downlink"
  export OAI_QD_UL_CHANNEL="$NTN_ROOT/examples/fdd-miso4-subarray/uplink"
fi
