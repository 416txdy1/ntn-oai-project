#!/usr/bin/env bash
# 完整 4×1 精度场景：前 357 秒新 QD 数据，原末尾 4 秒保持。
source "$(dirname -- "${BASH_SOURCE[0]}")/env_subarray4.sh"
export OAI_QD_DL_CHANNEL="$NTN_ROOT/.runtime/fidelity-full/downlink"
export OAI_QD_UL_CHANNEL="$NTN_ROOT/.runtime/fidelity-full/uplink"
