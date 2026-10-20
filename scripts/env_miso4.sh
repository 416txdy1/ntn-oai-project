#!/usr/bin/env bash
# 四个独立 RF 通道，下行 4x1 / 上行 1x4。
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"
export OAI_SPATIAL_MODE=miso4
export OAI_QD_DL_CHANNEL="$NTN_ROOT/examples/fdd-miso4/downlink"
export OAI_QD_UL_CHANNEL="$NTN_ROOT/examples/fdd-miso4/uplink"
