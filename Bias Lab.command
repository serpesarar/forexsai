#!/bin/bash
# MiroShark Bias Lab — çift tıkla aç.
# Backend'i (yoksa) başlatır ve kontrol panelini tarayıcıda açar.
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
URL="http://localhost:${PORT}/api/bias-test/lab"
HEALTH="http://localhost:${PORT}/api/health"

echo "▶ MiroShark Bias Lab başlatılıyor…"

# venv
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Backend zaten çalışıyor mu?
if curl -s -o /dev/null "$HEALTH" 2>/dev/null; then
  echo "✓ Backend zaten çalışıyor (:$PORT)"
else
  echo "… Backend başlatılıyor (log: /tmp/forexsai_backend.log)"
  ( cd backend && PORT="$PORT" nohup python main.py >/tmp/forexsai_backend.log 2>&1 & )
  # Hazır olana kadar bekle (maks ~40 sn)
  for i in $(seq 1 40); do
    if curl -s -o /dev/null "$HEALTH" 2>/dev/null; then break; fi
    sleep 1
  done
  if curl -s -o /dev/null "$HEALTH" 2>/dev/null; then
    echo "✓ Backend hazır"
  else
    echo "✗ Backend başlamadı — /tmp/forexsai_backend.log dosyasına bak"
    echo "  (genelde .env eksik: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)"
    read -r -p "Çıkmak için Enter…" _
    exit 1
  fi
fi

echo "▶ Panel açılıyor: $URL"
open "$URL"
echo "Bu pencereyi kapatabilirsin (backend arka planda çalışmaya devam eder)."
