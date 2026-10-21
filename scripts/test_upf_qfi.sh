#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$ROOT/scripts/test_upf_qfi.py"
mkdir -p "$ROOT/.runtime/upf-qfi"
c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -g \
  "$ROOT/upf_patch/test_downlink_qfi.cpp" -o "$ROOT/.runtime/upf-qfi/test_downlink_qfi"
"$ROOT/.runtime/upf-qfi/test_downlink_qfi"
