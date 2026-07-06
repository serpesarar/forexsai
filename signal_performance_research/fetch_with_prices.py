"""Fetch resolved prediction_logs WITH price fields for 1m ground-truth replay.

Only need rows resolved (completed/stopped) AND dated <= 2026-05-21 (the last day
the 1m bar files cover). Paginated REST pull. Cached to signals_priced.json.
"""
import json
import os
import httpx

# manual .env load
env = {}
for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

URL = env["SUPABASE_URL"].rstrip("/")
KEY = env.get("SUPABASE_SERVICE_ROLE_KEY") or env["SUPABASE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

COLS = ",".join([
    "created_at", "model_type", "symbol", "ml_direction", "status",
    "ml_entry_price", "ml_target_price", "ml_stop_price", "ml_confidence",
    "timeframe", "strategy",
    "source_combo:factors->>source_combo", "regime:factors->>regime",
])

# 1m bars end 2026-05-21T03:21Z; only verify signals created on/before that.
BOUNDARY = "2026-05-21T03:21:00"

base = (f"{URL}/rest/v1/prediction_logs?select={COLS}"
        f"&status=in.(completed,stopped)"
        f"&created_at=lte.{BOUNDARY}"
        f"&order=created_at.asc")

out = []
step = 1000
with httpx.Client(timeout=60.0) as c:
    off = 0
    while True:
        hh = dict(H); hh["Range-Unit"] = "items"; hh["Range"] = f"{off}-{off+step-1}"
        r = c.get(base, headers=hh)
        r.raise_for_status()
        batch = r.json()
        out.extend(batch)
        print(f"fetched {len(batch)} (total {len(out)})")
        if len(batch) < step:
            break
        off += step

json.dump(out, open("signal_performance_research/signals_priced.json", "w"))
print(f"TOTAL saved: {len(out)}")
