#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${PIPELINE_URL:-http://localhost:8093}"
MODEL="${AI_MODEL:-qwen2.5-coder:7b}"

echo "[1/4] Starting AI-SIEM-SOAR stack..."
docker compose up -d --build

echo "[2/4] Checking Ollama model: $MODEL"
if ! docker exec ai-siem-ollama ollama list | awk '{print $1}' | grep -Fxq "$MODEL"; then
  echo "Model not found. Pulling $MODEL ..."
  docker exec ai-siem-ollama ollama pull "$MODEL"
fi

echo "[3/4] Waiting for pipeline..."
for i in {1..60}; do
  if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then break; fi
  sleep 2
done
curl -fsS "$BASE_URL/health" >/dev/null

echo "[4/4] Sending five repeated SSH-deny events from one source IP..."
for n in 1 2 3 4 5; do
  curl -fsS -X POST "$BASE_URL/v1/process" \
    -H 'Content-Type: application/json' \
    -d "{"raw":"2026-10-03 23:55:0$n FW-DEMO [ALM-900$n] peer=45.13.22.91 target=10.20.1.15 svc=ssh result=reject attempts=$((10+n))","source":"demo-firewall"}" \
    | python3 -m json.tool
done

echo
echo "Audit file: ./data/audit/events.jsonl"
echo "SOAR is configured in safe dry-run mode by default (SOAR_DRY_RUN=true)."
