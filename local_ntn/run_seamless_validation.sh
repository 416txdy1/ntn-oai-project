#!/usr/bin/env bash
echo "Task4 restoration guard: use isolated wrapper after adaptation" >&2
exit 2
#!/usr/bin/env bash
set -Eeuo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TAG="seamless-20260924"
TRACE="$HERE/stk_trace_seamless.csv"
SCHEDULE="$HERE/satellite_schedule_seamless.csv"
LOG="$HERE/validation-$TAG.txt"
RATE="${OAI_STK_TRACE_RATE:-0.1}"
INITIAL_LEAD="${OAI_STK_INITIAL_LEAD_RFSIM:-0}"

exec > >(tee -a "$LOG") 2>&1
echo "=== NTN seamless handover validation $(date -Is) ==="
echo "trace=$TRACE"
echo "schedule=$SCHEDULE"
echo "rate=$RATE STK-s/RFsim-s initial_lead=$INITIAL_LEAD RFsim-s"
[[ -s "$TRACE" && -s "$SCHEDULE" ]] || { echo "ERROR: trace slice or schedule is missing"; exit 2; }

echo "[1/4] Requesting sudo authorization (enter the password in this terminal)"
sudo -v

echo "[2/4] Starting OAI 5GC services"
cd /home/kayoko/oai-cn5g-fed/docker-compose-v220
docker compose -f docker-compose-basic-nrf.yaml -f docker-compose-extdn-ubuntu.yaml up -d --wait --wait-timeout 120

echo "[3/4] Starting gNB/UE and running concurrent probes over both handovers"
cd "$HERE"
sudo -E env OAI_STK_TRACE="$TRACE" OAI_STK_SCHEDULE="$SCHEDULE" \
  OAI_STK_TRACE_RATE="$RATE" OAI_STK_INITIAL_LEAD_RFSIM="$INITIAL_LEAD" \
  python3 "$HERE/test_seamless.py" --tag "$TAG" --duration 620 --rate "$RATE"

echo "[4/4] Finished. Logs: ping-seamless-$TAG.txt, iperf-seamless-$TAG.txt"
echo "To stop only this run: sudo python3 '$HERE/experiment.py' stop"
