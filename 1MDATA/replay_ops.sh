#!/bin/bash
# ForexSAI — replay operation helper.
# Run from the 1mdata folder:  bash replay_ops.sh <step>
#
# Steps:
#   upload-xau   Re-upload XAUUSD 1m bars with purge (fixes the wrong-tz data)
#   dry          Dry-run replay on 20 XAUUSD signals (no DB writes)
#   run-full     FULL sweep — replay every signal since 2026-02-10, persists
#   report       Per-scope original-vs-corrected diff (last 90 days)

BASE="https://upbeat-flow-production.up.railway.app"

case "$1" in
  upload-xau)
    echo ">> Re-uploading XAUUSD 1m bars (purge + offset 0)..."
    curl -X POST -F 'file=@mt5_xauusd_1m_bars.json' \
      "$BASE/api/mt5/upload-1m-bars?purge_existing=true"
    echo
    ;;
  dry)
    echo ">> Dry-run replay: 20 XAUUSD signals since 2026-05-15..."
    curl -X POST \
      "$BASE/api/replay/run?since=2026-05-15&symbol=XAUUSD&limit=20&dry_run=true"
    echo
    ;;
  run-full)
    echo ">> FULL replay sweep since 2026-02-10 (persists corrections)..."
    curl -X POST "$BASE/api/replay/run?since=2026-02-10"
    echo
    ;;
  report)
    echo ">> Replay report (last 90 days)..."
    curl "$BASE/api/replay/report?days=90"
    echo
    ;;
  *)
    echo "Usage: bash replay_ops.sh {upload-xau|dry|run-full|report}"
    exit 1
    ;;
esac
