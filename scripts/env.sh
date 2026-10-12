#!/usr/bin/env bash
# Source this file; resolve everything before exporting any configuration.
NTN_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd) || return 1
if [ "${OAI_NTN_PROFILE:-zky}" = zky ]; then
  # Preserve the existing shell defaults (paths.py has a different private UE default).
  NTN_RESOLVED_ENV=$(OAI_REPO="$NTN_ROOT/.runtime/oai" \
    OAI_BUILD_DIR="$NTN_ROOT/.runtime/oai/cmake_targets/ran_build/build" \
    OAI_BUILD_REPO="$NTN_ROOT/.runtime/oai" \
    OAI_STK_TRACE="$NTN_ROOT/examples/fdd-pass/trace.csv" \
    OAI_QD_DL_CHANNEL="$NTN_ROOT/examples/fdd-pass/downlink" \
    OAI_QD_UL_CHANNEL="$NTN_ROOT/examples/fdd-pass/uplink" \
    OAI_UE_CONFIG="$NTN_ROOT/.private/ue.conf" \
    OAI_AMF_IP=192.168.70.132 OAI_GNB_IP_CIDR=192.168.70.129/26 \
    python3 "$NTN_ROOT/local_ntn/runtime_config.py" --format env) || return 1
else
  NTN_RESOLVED_ENV=$(python3 "$NTN_ROOT/local_ntn/runtime_config.py" --format env) || return 1
fi
eval "$NTN_RESOLVED_ENV"
unset NTN_RESOLVED_ENV
unset OAI_QD_CHANNEL OAI_STK_TRACE_EPOCH OAI_STK_PORT
unset OAI_STK_TRACE_EXTRA_LOSS_DB OAI_STK_TRACE_CN_OFFSET_DB OAI_STK_TRACE_BW_HZ OAI_STK_TRACE_NOISE
