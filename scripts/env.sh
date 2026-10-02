#!/usr/bin/env bash
# 必须 source；使用此文件位置计算路径，不依赖调用目录或用户名。
NTN_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export OAI_REPO="$NTN_ROOT/.runtime/oai"
export OAI_BUILD_DIR="$OAI_REPO/cmake_targets/ran_build/build"
export OAI_BUILD_REPO="$OAI_REPO"
export OAI_STK_TRACE="$NTN_ROOT/examples/fdd-pass/trace.csv"
export OAI_QD_DL_CHANNEL="$NTN_ROOT/examples/fdd-pass/downlink"
export OAI_QD_UL_CHANNEL="$NTN_ROOT/examples/fdd-pass/uplink"
export OAI_UE_CONFIG="$NTN_ROOT/.private/ue.conf"
export OAI_AMF_IP=192.168.70.132 OAI_GNB_IP_CIDR=192.168.70.129/26
unset OAI_QD_CHANNEL OAI_STK_TRACE_EPOCH OAI_STK_PORT
unset OAI_STK_TRACE_EXTRA_LOSS_DB OAI_STK_TRACE_CN_OFFSET_DB OAI_STK_TRACE_BW_HZ OAI_STK_TRACE_NOISE
if [ -f "$NTN_ROOT/.private/settings.json" ]; then
  read -r OAI_AMF_IP OAI_GNB_IP_CIDR OAI_EXT_DN_IP OAI_EXT_DN_CONTAINER < <(
    python3 -c 'import json,sys;s=json.load(open(sys.argv[1]));print(s["amf_ip"],s["gnb_ip_cidr"],s["ext_dn_ip"],s["ext_dn_container"])' "$NTN_ROOT/.private/settings.json")
  export OAI_AMF_IP OAI_GNB_IP_CIDR OAI_EXT_DN_IP OAI_EXT_DN_CONTAINER
fi
export OAI_IPERF3_BIN="$NTN_ROOT/.runtime/iperf3/iperf3"
export OAI_IPERF3_LIBRARY_PATH="$NTN_ROOT/.runtime/iperf3/lib"
