#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" = 0 || { echo 'Run with sudo'; exit 1; }
NS=oai-stk-ue
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
if ip netns list | grep -q "^${NS}\b"; then
  python3 "$HERE/verify_network.py"
  ip -n "$NS" -br addr
  exit 0
fi
if ip link show oai-stk-host >/dev/null 2>&1 || ip route show | grep -q '10.201.0.0/30'; then
  echo 'Network name/address conflict; refusing to overwrite';exit 1
fi
ip netns add "$NS"
ip link add oai-stk-host type veth peer name oai-stk-peer
ip link set oai-stk-peer netns "$NS"
ip addr add 10.201.0.1/30 dev oai-stk-host
ip link set oai-stk-host up
ip -n "$NS" addr add 10.201.0.2/30 dev oai-stk-peer
ip -n "$NS" link set oai-stk-peer up
ip -n "$NS" link set lo up
python3 "$HERE/verify_network.py" --claim
# No default route to the host: user traffic must pass through oaitun_ue1.
ip -n "$NS" -br addr
