"""
Programmatic failure analyzer — bedava root-cause tagging her resolved sinyal için.

Anthropic kredisi gerektirmez. AI pipeline'ın yerini ALMAZ — onun PRE-FILTER'ı:
  1) Bu script tüm resolved (completed/stopped) sinyallere kural-tabanlı tags atar.
  2) failure_analyses tablosuna yazar (zaten var olan tablo, kullanılmıyor).
  3) Eğitim aşamasında bu tags'i feature olarak kullanırız (categorical: rsi_overbought, near_resistance, against_trend, fake_move, etc.).
  4) AI (Claude/DeepSeek) yalnızca kuralların "unknown" işaretlediği örnekler için çağrılır → maliyet 100x düşer.

Çıktı şeması (failure_analyses tablosuna uyumlu):
    prediction_id, symbol, direction, entry_price, failure_price,
    failure_reason (pipe-separated tags),
    rsi_at_failure, volume_change, nearest_resistance, nearest_support,
    fib_level_hit, macd_divergence, recommendation

KULLANIM:
    python xauusdegitim/programmatic_failure_analyzer.py --symbol XAUUSD --days 90 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
BASE = f"{URL}/rest/v1"

NOW = datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_resolved_predictions(symbol: str, days: int) -> list[dict]:
    since = NOW - timedelta(days=days)
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            params = {
                "symbol": f"eq.{symbol}",
                "model_type": "like.ml*",
                "status": "in.(completed,stopped)",
                "created_at": f"gte.{iso(since)}",
                "select": ("id,symbol,model_type,ml_direction,ml_confidence,status,resolution_reason,"
                           "ml_entry_price,ml_target_price,ml_stop_price,factors,created_at,timeframe"),
                "order": "created_at.desc",
                "limit": "1000",
                "offset": str(offset),
            }
            r = c.get(f"{BASE}/prediction_logs", headers=HEADERS, params=params)
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
    return rows


def fetch_outcome(prediction_id: str, client: httpx.Client) -> dict | None:
    r = client.get(f"{BASE}/outcome_results", headers=HEADERS,
                   params={"prediction_id": f"eq.{prediction_id}", "limit": "1"})
    if r.status_code != 200:
        return None
    data = r.json()
    return data[0] if data else None


def existing_failure_ids(client: httpx.Client) -> set[str]:
    """All prediction_ids that already have a failure_analyses row — for idempotency."""
    ids: set[str] = set()
    offset = 0
    while True:
        r = client.get(f"{BASE}/failure_analyses", headers=HEADERS,
                       params={"select": "prediction_id", "limit": "1000", "offset": str(offset)})
        if r.status_code != 200:
            return ids
        batch = r.json()
        for row in batch:
            pid = row.get("prediction_id")
            if pid:
                ids.add(pid)
        if len(batch) < 1000:
            break
        offset += 1000
    return ids


# ---------------------------------------------------------------------------
# Rule-based tagger
# ---------------------------------------------------------------------------

def parse_factors(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def tag_failure(prediction: dict, outcome: dict | None) -> dict:
    """
    Apply rule-based tags. Returns a dict ready for failure_analyses insert.
    Returns None if signal was a WIN (no failure to tag).
    """
    direction = prediction.get("ml_direction") or "HOLD"
    if direction not in ("BUY", "SELL"):
        return None

    status = prediction.get("status")
    resolution = prediction.get("resolution_reason") or ""
    factors = parse_factors(prediction.get("factors"))

    # We tag both stop-outs AND tp1_3_then_sl (partial wins that turned bad)
    is_failure = (
        status == "stopped"
        or resolution in ("sl_hit", "tp1_3_hit_then_sl", "window_resolve_negative", "direction_flip")
    )
    if not is_failure:
        return None

    entry = prediction.get("ml_entry_price")
    sl = prediction.get("ml_stop_price")
    target = prediction.get("ml_target_price")
    failure_price = (outcome or {}).get("exit_price") or sl

    tags: list[str] = []
    rsi = factors.get("rsi_14") or factors.get("rsi") or factors.get("rsi_14_M30")
    macd_hist = factors.get("macd_hist") or factors.get("macd_hist_M30")
    adx_val = factors.get("adx") or factors.get("adx_14")
    vol_ratio = factors.get("volume_ratio") or factors.get("vol_ratio")
    trend_dir = factors.get("trend_direction") or factors.get("regime")
    near_res = factors.get("nearest_resistance_distance") or factors.get("resistance_distance")
    near_sup = factors.get("nearest_support_distance") or factors.get("support_distance")
    bb_pctb = factors.get("bb_pctb") or factors.get("bb_position")

    # --- RSI extreme ---
    try:
        rsi_v = float(rsi) if rsi is not None else None
    except Exception:
        rsi_v = None
    if rsi_v is not None:
        if direction == "BUY" and rsi_v > 70:
            tags.append("RSI_OVERBOUGHT_BUY")
        if direction == "SELL" and rsi_v < 30:
            tags.append("RSI_OVERSOLD_SELL")
        if direction == "BUY" and rsi_v < 35:
            tags.append("RSI_FALLING_BUY")  # buying weakness without confirmation
        if direction == "SELL" and rsi_v > 65:
            tags.append("RSI_RISING_SELL")

    # --- MACD divergence proxy ---
    macd_div = False
    try:
        m_v = float(macd_hist) if macd_hist is not None else None
        if m_v is not None:
            if direction == "BUY" and m_v < 0:
                tags.append("MACD_NEG_BUY")
                macd_div = True
            if direction == "SELL" and m_v > 0:
                tags.append("MACD_POS_SELL")
                macd_div = True
    except Exception:
        pass

    # --- Against trend ---
    if isinstance(trend_dir, str):
        td = trend_dir.upper()
        if direction == "BUY" and ("DOWN" in td or "BEAR" in td):
            tags.append("AGAINST_TREND_BUY")
        if direction == "SELL" and ("UP" in td or "BULL" in td):
            tags.append("AGAINST_TREND_SELL")

    # --- Weak trend (ADX) ---
    try:
        a_v = float(adx_val) if adx_val is not None else None
        if a_v is not None and a_v < 18:
            tags.append("LOW_ADX_RANGING")
    except Exception:
        pass

    # --- S/R proximity at entry ---
    try:
        nr = float(near_res) if near_res is not None else None
        ns = float(near_sup) if near_sup is not None else None
        if direction == "BUY" and nr is not None and nr < 15:
            tags.append("BUY_INTO_RESISTANCE")
        if direction == "SELL" and ns is not None and ns < 15:
            tags.append("SELL_INTO_SUPPORT")
    except Exception:
        pass

    # --- Bollinger extreme ---
    try:
        bb = float(bb_pctb) if bb_pctb is not None else None
        if bb is not None:
            if direction == "BUY" and bb > 0.95:
                tags.append("BB_UPPER_BUY")
            if direction == "SELL" and bb < 0.05:
                tags.append("BB_LOWER_SELL")
    except Exception:
        pass

    # --- Volume confirmation ---
    try:
        vr = float(vol_ratio) if vol_ratio is not None else None
        if vr is not None and vr < 0.6:
            tags.append("LOW_VOLUME_CONFIRMATION")
    except Exception:
        pass

    # --- Fake move from outcome MFE/MAE ---
    if outcome:
        mfe = outcome.get("highest_profit_pips") or 0
        mae = outcome.get("lowest_drawdown_pips") or 0
        if mfe and mae and mae > mfe * 1.5 and mfe > 5:
            tags.append("FAKE_MOVE_REVERSAL")
        if mae and mfe < 5 and mae > 15:
            tags.append("STOP_HUNT")

    # --- Resolution-derived ---
    if resolution == "tp1_3_hit_then_sl":
        tags.append("TP_GREED_REVERSAL")
    if resolution == "direction_flip":
        tags.append("REGIME_FLIP")

    if not tags:
        tags = ["UNKNOWN_REASON"]

    return {
        "prediction_id": prediction["id"],
        "symbol": prediction.get("symbol"),
        "direction": direction,
        "entry_price": entry,
        "failure_price": failure_price,
        "failure_reason": "|".join(tags),
        "rsi_at_failure": rsi_v,
        "volume_change": vol_ratio,
        "nearest_resistance": near_res,
        "nearest_support": near_sup,
        "fib_level_hit": None,
        "macd_divergence": macd_div,
        "recommendation": _build_recommendation(tags, direction),
    }


def _build_recommendation(tags: list[str], direction: str) -> str:
    if "AGAINST_TREND_BUY" in tags or "AGAINST_TREND_SELL" in tags:
        return "Trend-aware filter ekle: ana TF (H1/H4) trendine ters sinyalde confidence -25"
    if "RSI_OVERBOUGHT_BUY" in tags:
        return "RSI>70 iken BUY → confidence -30 veya HOLD'a düşür"
    if "RSI_OVERSOLD_SELL" in tags:
        return "RSI<30 iken SELL → confidence -30 veya HOLD'a düşür"
    if "BUY_INTO_RESISTANCE" in tags:
        return "Yakın direnç (<15 pips) → BUY için TP'yi kısalt veya HOLD"
    if "SELL_INTO_SUPPORT" in tags:
        return "Yakın destek (<15 pips) → SELL için TP'yi kısalt veya HOLD"
    if "FAKE_MOVE_REVERSAL" in tags or "STOP_HUNT" in tags:
        return "Volatilite filtresi: ATR > avg×1.5 + low_volume → entry erteleme"
    if "TP_GREED_REVERSAL" in tags:
        return "TP1 hit sonrası SL'yi BE'ye taşı (trailing/breakeven mantığı)"
    if "LOW_VOLUME_CONFIRMATION" in tags:
        return "Volume z-score < 0 ise confidence -15"
    return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--dry-run", action="store_true", help="Skip Supabase writes")
    ap.add_argument("--limit", type=int, default=None, help="Cap inserts (smoke test)")
    args = ap.parse_args()

    print(f">> Fetching resolved predictions: symbol={args.symbol} days={args.days}")
    preds = fetch_resolved_predictions(args.symbol, args.days)
    print(f"   {len(preds)} resolved ML predictions")

    with httpx.Client(timeout=60) as client:
        existing = existing_failure_ids(client)
        print(f"   {len(existing)} already in failure_analyses (will skip)")

        new_records: list[dict] = []
        skipped_win = 0
        skipped_existing = 0
        tag_counter: dict[str, int] = {}
        for p in preds:
            if p["id"] in existing:
                skipped_existing += 1
                continue
            outcome = fetch_outcome(p["id"], client)
            rec = tag_failure(p, outcome)
            if rec is None:
                skipped_win += 1
                continue
            new_records.append(rec)
            for t in rec["failure_reason"].split("|"):
                tag_counter[t] = tag_counter.get(t, 0) + 1
            if args.limit and len(new_records) >= args.limit:
                break

        print(f"\n   skipped (already analyzed): {skipped_existing}")
        print(f"   skipped (was a win): {skipped_win}")
        print(f"   new records to insert: {len(new_records)}")

        print("\n   --- Tag distribution (this run) ---")
        for t, n in sorted(tag_counter.items(), key=lambda x: -x[1]):
            print(f"     {t:30s} {n}")

        if args.dry_run:
            print("\n[dry-run] Skipping insert. First 3 records preview:")
            for r in new_records[:3]:
                print("     ", json.dumps(r, default=str))
            return

        # Bulk insert in batches of 200
        if not new_records:
            return
        for i in range(0, len(new_records), 200):
            chunk = new_records[i:i + 200]
            r = client.post(f"{BASE}/failure_analyses", headers={**HEADERS, "Prefer": "return=minimal"},
                            json=chunk)
            if r.status_code not in (200, 201):
                print(f"   ⚠ insert {i}: {r.status_code} {r.text[:300]}")
                break
            print(f"   inserted {i + len(chunk)}/{len(new_records)}")
        print("DONE")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text[:500]}", file=sys.stderr)
        sys.exit(2)
