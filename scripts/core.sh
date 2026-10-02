#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
PROJECT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["compose_project"])' "$ROOT/.private/settings.json")
case "${1:-}" in
 up) docker compose -p "$PROJECT" -f "$ROOT/.private/core/compose.yaml" up -d --wait --wait-timeout 180 ;;
 stop) docker compose -p "$PROJECT" -f "$ROOT/.private/core/compose.yaml" stop ;;
 status) docker compose -p "$PROJECT" -f "$ROOT/.private/core/compose.yaml" ps ;;
 *) echo 'Usage: bash scripts/core.sh up|stop|status'; exit 2 ;;
esac