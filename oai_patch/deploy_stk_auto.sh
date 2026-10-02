#!/usr/bin/env bash
set -euo pipefail
# 旧版覆盖部署入口保留兼容名称；仅准备仓库内生成树，不覆盖外部 OAI。
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 "$ROOT/scripts/prepare_sources.py"