#!/usr/bin/env bash
set -Eeuo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TAG="constellation-20260923"
LOG="$HERE/validation-$TAG.txt"
TRACE="$HERE/stk_trace.csv"
SCHEDULE="$HERE/satellite_schedule.csv"

exec > >(tee -a "$LOG") 2>&1
echo "=== NTN constellation validation $(date -Is) ==="
echo "trace=$TRACE"
echo "schedule=$SCHEDULE"

if [[ ! -s "$TRACE" || ! -s "$SCHEDULE" ]]; then
  echo "ERROR: trace or schedule is missing" >&2
  exit 2
fi

echo "[1/5] Requesting sudo authorization (enter the password in this terminal)"
sudo -v

echo "[2/5] Starting OAI 5GC services"
cd /home/kayoko/oai-cn5g-fed/docker-compose-v220
docker compose -f docker-compose-basic-nrf.yaml -f docker-compose-extdn-ubuntu.yaml up -d --wait --wait-timeout 120

echo "[3/5] Starting gNB and UE with the deterministic STK trace"
cd "$HERE"
sudo -E env OAI_STK_TRACE="$TRACE" OAI_STK_SCHEDULE="$SCHEDULE" OAI_STK_TRACE_RATE=1 \
  python3 "$HERE/validate_dynamic.py" --tag "$TAG"

echo "[4/5] Collecting compact results"
for f in "$HERE/ping-dynamic-$TAG.txt" "$HERE/iperf-dynamic-$TAG.txt" "$HERE/iperf-dl-dynamic-$TAG.txt"; do
  echo "--- $f ---"
  if [[ -f "$f" ]]; then tail -n 30 "$f"; else echo "missing"; fi
done

echo "[5/5] Finished; gNB/UE are still running for inspection."
echo "To stop only this run: sudo python3 '$HERE/experiment.py' stop"
