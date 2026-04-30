"""
Post-deploy verification — are the new snapshot fields landing in Supabase?

Run this 30+ minutes after deploy. Compares:
  - last 30 days  (legacy — should show low fill rate)
  - last 1 hour   (post-deploy — should show ~100% fill rate)

If post-deploy fill rate is still low, the enrich call is failing silently in
production logs.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
NOW = datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


CANARY_KEYS = [
    "snapshot_v",
    "regime_label", "mtf_trend", "volatility_regime",
    "near_resistance", "near_support",
    "overbought", "oversold",
    "exhaustion_up", "exhaustion_down",
    "sar_bearish",
    "M30_rsi_14", "M30_macd_hist", "M30_adx_14",
    "M30_dist_swing_high_30_atr", "M30_dist_swing_low_30_atr",
    "H1_rsi_14", "H4_adx_14", "H4_ema_stack",
    "macro_dxy_price", "macro_vix_price",
]


def fill_rate(since: datetime, label: str) -> dict:
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            r = c.get(f"{URL}/rest/v1/prediction_logs", headers=HEADERS,
                      params={"select": "factors,model_type,created_at",
                              "created_at": f"gte.{iso(since)}",
                              "order": "created_at.desc",
                              "limit": "1000", "offset": str(offset)})
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < 1000 or len(rows) >= 5000:
                break
            offset += 1000
    out = {"label": label, "since": iso(since), "rows_scanned": len(rows), "fills": {}}
    for k in CANARY_KEYS:
        n = 0
        for row in rows:
            f = row.get("factors")
            if isinstance(f, str):
                try: f = json.loads(f)
                except Exception: f = {}
            if isinstance(f, dict) and k in f and f[k] is not None:
                n += 1
        out["fills"][k] = (n, n / max(len(rows), 1) * 100)
    return out


def main():
    legacy = fill_rate(NOW - timedelta(days=30), "last 30d (legacy)")
    fresh = fill_rate(NOW - timedelta(hours=1), "last 1h (post-deploy)")

    print(f"\n=== Snapshot Logging Verification @ {iso(NOW)} ===\n")
    print(f"{'KEY':<35s} {'LEGACY 30d':>15s} {'LAST 1h':>15s}")
    print("-" * 70)
    for k in CANARY_KEYS:
        l_n, l_pct = legacy["fills"][k]
        f_n, f_pct = fresh["fills"][k]
        marker = "✓" if f_pct >= 50 else ("⚠" if f_pct > 0 else "❌")
        print(f"{k:<35s} {l_pct:>10.1f}% ({l_n:4d}) {f_pct:>10.1f}% ({f_n:4d}) {marker}")

    print(f"\nLegacy rows scanned: {legacy['rows_scanned']}")
    print(f"Fresh rows scanned: {fresh['rows_scanned']}")
    if fresh["rows_scanned"] == 0:
        print("\n⚠ No signals in the last hour. Run again later.")
    elif all(v[1] < 50 for v in fresh["fills"].values()):
        print("\n❌ Snapshot enrich is NOT working in production. Check backend logs for "
              "'signal_feature_snapshot enrich failed'.")
    else:
        print("\n✓ Snapshot enrich working correctly.")


if __name__ == "__main__":
    main()
