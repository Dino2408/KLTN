#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[[ -f .env ]] || cp .env.example .env

sudo sysctl -w vm.max_map_count=262144 >/dev/null 2>&1 || true

docker compose up -d
