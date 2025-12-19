#!/usr/bin/env bash
set -euo pipefail

curl -s -X GET http://localhost:8000/api/health | jq
curl -s -X POST http://localhost:8000/api/run/nasdaq | jq
curl -s -X POST http://localhost:8000/api/run/xauusd | jq
curl -s -X POST http://localhost:8000/api/run/pattern-engine -H 'Content-Type: application/json' -d '{"last_n": 500, "select_top": 0.3, "output_selected_only": true}' | jq
curl -s -X POST http://localhost:8000/api/claude/analyze-patterns -H 'Content-Type: application/json' -d '{"symbol": "NDX.INDX", "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"]}' | jq
curl -s -X POST http://localhost:8000/api/claude/analyze-sentiment | jq
