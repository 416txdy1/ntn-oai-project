#!/usr/bin/env bash
# 单独启用 2x1 下行 / 1x2 上行，保留默认 SISO 入口。
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"
export OAI_SPATIAL_MODE=miso2
export OAI_QD_DL_CHANNEL="$NTN_ROOT/examples/fdd-miso/downlink"
export OAI_QD_UL_CHANNEL="$NTN_ROOT/examples/fdd-miso/uplink"
