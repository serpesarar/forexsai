"""
Precision Veto — Stage 1c (Day Structure) point-in-time backtest.

Leak-siz değerlendirme: her sinyal için sadece o sinyalin oluştuğu ANDA
var olan 1m bar verisiyle Day Structure'ı yeniden hesaplar, Stage 1c'yi
çalıştırır, sonucu signal'in gerçek `corrected_status`'uyla karşılaştırır.

Bu sayede haftasonu beklemeden Stage 1c'nin gerçek-veride etkisini
ölçebiliriz: kaç sinyal vetolanırdı, vetolananların kaçı SL'ye gidiyordu
(good_catch), kaçı TP yapıyordu (missed_win), pip etkisi nedir.
"""
from __future__ import annotations

import asyncio
import bisect
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ─── 1m → daha üst TF agregasyonu ────────────────────────────────────────────
def _floor_ts(ts: datetime, tf: str) -> datetime:
    if tf == "15m":
        return ts.replace(second=0, microsecond=0,
                          minute=(ts.minute // 15) * 15)
    if tf == "1h":
        return ts.replace(second=0, microsecond=0, minute=0)
    if tf == "1d":
        return ts.replace(second=0, microsecond=0, minute=0, hour=0)
    return ts.replace(second=0, microsecond=0)


def _aggregate(bars_1m: list[dict], tf: str) -> list[dict]:
    """1m bar listesinden TF agregasyonu. bars_1m sıralı (ts ascending) varsayılır."""
    if tf == "1m" or not bars_1m:
        return bars_1m
    buckets: dict[datetime, dict] = {}
    order: list[datetime] = []
    for b in bars_1m:
        ts = b["ts"]
        k = _floor_ts(ts, tf)
        if k not in buckets:
            buckets[k] = {"ts": k, "open": b["open"], "high": b["high"],
                          "low": b["low"], "close": b["close"],
                          "volume": b.get("volume", 0)}
            order.append(k)
        else:
            bb = buckets[k]
            bb["high"] = max(bb["high"], b["high"])
            bb["low"] = min(bb["low"], b["low"])
            bb["close"] = b["close"]
            bb["volume"] += b.get("volume", 0) or 0
    return [buckets[k] for k in order]


# ─── Point-in-time veri çekme ────────────────────────────────────────────────
def _slice_up_to(bars: list[dict], ts_keys: list, cutoff: datetime,
                 last_n: Optional[int] = None) -> list[dict]:
    """bisect ile cutoff'a kadar olan tüm barları döndür (en fazla son N)."""
    if not bars:
        return []
    idx = bisect.bisect_right(ts_keys, cutoff)
    sliced = bars[:idx]
    if last_n and len(sliced) > last_n:
        sliced = sliced[-last_n:]
    return sliced


# ─── Realized pips (signed) — shadow-report ile aynı mantık ──────────────────
def _realized_pips(symbol: str, direction: str,
                   entry: float, exit_p: float) -> float:
    if not entry or not exit_p:
        return 0.0
    diff = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
    try:
        from services.target_config import pips_from_price_change
        mag = abs(pips_from_price_change(abs(diff), symbol))
        return mag if diff >= 0 else -mag
    except Exception:
        return diff


# ─── Ana backtest ────────────────────────────────────────────────────────────
async def backtest_stage1c(days: int = 90,
                            symbols: Optional[list[str]] = None,
                            sample_per_scope: int = 0) -> dict:
    """Stage 1c'yi tüm `prediction_replay_corrections` üzerinde leak-siz çalıştırır.

    sample_per_scope=0 → tüm sinyaller; >0 → her (sembol, yön) için
    rasgele örneklem (hızlı tarama)."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    from services.signal_replay_1m import _load_all_1m_bars_sync
    from services.day_structure_service import compute_day_structure
    from services.precision_veto_service import _stage1c_day_structure

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    symbols = symbols or ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]

    # ── prediction_replay_corrections'tan replay_status=ok kayıtları al ─────
    rows: list[dict] = []
    offset = 0
    PAGE = 1000
    while True:
        q = (client.table("prediction_replay_corrections").select(
            "prediction_id,symbol,model_type,direction,entry_price,timeframe,"
            "signal_created_at,corrected_status,corrected_exit_price,replay_status")
            .gte("signal_created_at", since)
            .order("signal_created_at", desc=False)
            .range(offset, offset + PAGE - 1))
        res = q.execute() if hasattr(q, "execute") else q
        page = res.data if hasattr(res, "data") else (
            res.get("data") if isinstance(res, dict) else []) or []
        if not page:
            break
        rows.extend(page)
        if len(page) < PAGE:
            break
        offset += PAGE

    rows = [r for r in rows if r.get("replay_status") == "ok"
            and r.get("corrected_status") in ("completed", "stopped")
            and r.get("symbol") in symbols
            and r.get("direction") in ("BUY", "SELL")
            and r.get("entry_price")]

    if not rows:
        return {"status": "ok", "scanned": 0, "note": "veri yok"}

    # Sembol+yön bazında örnekle (sample_per_scope > 0 ise)
    if sample_per_scope > 0:
        from collections import defaultdict
        by_scope: dict = defaultdict(list)
        for r in rows:
            by_scope[(r["symbol"], r["direction"])].append(r)
        sampled = []
        rng = random.Random(42)
        for k, lst in by_scope.items():
            sampled.extend(lst if len(lst) <= sample_per_scope
                           else rng.sample(lst, sample_per_scope))
        rows = sorted(sampled, key=lambda r: r.get("signal_created_at"))

    # ── Her sembol için 1m bars + TF agregasyonları (bir kez) ───────────────
    per_symbol: dict = {}
    for sym in symbols:
        bars_1m = await asyncio.to_thread(_load_all_1m_bars_sync, sym)
        if not bars_1m:
            continue
        per_symbol[sym] = {
            "1m": bars_1m, "1m_keys": [b["ts"] for b in bars_1m],
            "15m": _aggregate(bars_1m, "15m"),
            "1h": _aggregate(bars_1m, "1h"),
            "1d": _aggregate(bars_1m, "1d"),
        }
        per_symbol[sym]["15m_keys"] = [b["ts"] for b in per_symbol[sym]["15m"]]
        per_symbol[sym]["1h_keys"] = [b["ts"] for b in per_symbol[sym]["1h"]]
        per_symbol[sym]["1d_keys"] = [b["ts"] for b in per_symbol[sym]["1d"]]

    if not per_symbol:
        return {"status": "error", "error": "candle_cache'de 1m veri yok"}

    # ── Sinyalleri tek tek point-in-time çalıştır ───────────────────────────
    def _parse(t):
        try:
            return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        except Exception:
            return None

    results: list[dict] = []
    for r in rows:
        sym = r["symbol"]
        ps = per_symbol.get(sym)
        if not ps:
            continue
        cutoff = _parse(r["signal_created_at"])
        if cutoff is None:
            continue
        # Point-in-time slice'lar
        c_15m = _slice_up_to(ps["15m"], ps["15m_keys"], cutoff, last_n=400)
        c_1h = _slice_up_to(ps["1h"], ps["1h_keys"], cutoff, last_n=200)
        c_1d = _slice_up_to(ps["1d"], ps["1d_keys"], cutoff, last_n=30)
        if len(c_15m) < 30 or len(c_1d) < 2:
            continue

        tf = r.get("timeframe") or "15m"
        try:
            ds = await compute_day_structure(
                sym, tf,
                _injected_candles={"15m": c_15m, "1h": c_1h, "1d": c_1d, "tf": c_15m},
                _as_of=cutoff,
            )
        except Exception as e:
            logger.debug("day_structure compute hatası: %s", e)
            continue
        if ds is None:
            continue

        direction = r["direction"]
        price = float(r["entry_price"])
        try:
            reason, penalty, det = await _stage1c_day_structure(sym, direction,
                                                                  price, tf)
        except Exception:
            continue
        # _stage1c_day_structure compute_day_structure'ı tekrar çağırıyor (live!)
        # — backtest için doğrusu DS'i bizim hesapladığımız 'ds' olmalı.
        # Bu yüzden direkt kuralları burada uygulayalım (live fetch yok).
        reason, penalty = _eval_stage1c_with_ds(ds, direction, price)

        realized = _realized_pips(sym, direction, price,
                                  float(r.get("corrected_exit_price") or 0))
        results.append({
            "symbol": sym, "model_type": r.get("model_type"),
            "direction": direction,
            "corrected_status": r["corrected_status"],
            "realized_pips": round(realized, 3),
            "stage1c_reason": reason,
            "stage1c_penalty": penalty,
            "would_veto": bool(reason),
        })

    # ── Sonuçları topla ─────────────────────────────────────────────────────
    summary = _summarize(results)
    summary["scanned"] = len(rows)
    summary["evaluated"] = len(results)
    summary["symbols_loaded"] = list(per_symbol.keys())
    return summary


def _eval_stage1c_with_ds(ds, direction: str, price: float
                           ) -> tuple[Optional[str], float]:
    """Stage 1c kurallarını verilmiş bir DS objesi üzerinde uygula
    (live fetch yapmadan — backtest için)."""
    from services.precision_veto_service import PRECISION_VETO_CONFIG
    cfg = PRECISION_VETO_CONFIG
    if ds is None or ds.atr <= 0:
        return None, 0.0
    mem_dist = float(cfg["stage1c_memory_distance_atr"])
    mem_min_rej = int(cfg["stage1c_memory_min_rejections"])
    mem_min_fresh = float(cfg["stage1c_memory_min_freshness"])

    nearest_zone = ds.nearest_memory_zone_in_direction(direction)
    if nearest_zone is not None:
        d = abs(nearest_zone.center - price) / ds.atr
        if (d <= mem_dist and nearest_zone.rejections >= mem_min_rej
                and nearest_zone.freshness >= mem_min_fresh):
            return "memory_zone_rejection_path", 0.0

    pdh_pdl_dist = float(cfg["stage1c_pdh_pdl_distance_atr"])
    min_today_rej = int(cfg["stage1c_pdh_pdl_min_rejections_today"])
    if direction == "BUY" and ds.pdh is not None:
        d = abs(ds.pdh - price) / ds.atr
        if d <= pdh_pdl_dist and ds.pdh_rejections_today >= min_today_rej:
            return "pdh_rejected_liquidity", 0.0
    if direction == "SELL" and ds.pdl is not None:
        d = abs(ds.pdl - price) / ds.atr
        if d <= pdh_pdl_dist and ds.pdl_rejections_today >= min_today_rej:
            return "pdl_rejected_liquidity", 0.0

    sp1_dist = float(cfg["stage1c_pivot_penalty_distance_atr"])
    sp1_pen = float(cfg["stage1c_pivot_penalty"])
    opposing = ("R1", "R2", "R3") if direction == "BUY" else ("S1", "S2", "S3")
    for name in opposing:
        if name not in ds.pivots:
            continue
        d = abs(ds.pivots[name] - price) / ds.atr
        if d <= sp1_dist:
            return None, sp1_pen
    return None, 0.0


def _summarize(results: list[dict]) -> dict:
    from collections import defaultdict
    by_sym: dict = defaultdict(lambda: {
        "total": 0, "vetoed": 0, "penalized": 0,
        "good_catch": 0, "missed_win": 0, "neutral": 0,
        "pips_saved": 0.0, "pips_missed": 0.0,
    })
    by_reason: dict = defaultdict(lambda: {"good": 0, "missed": 0})
    overall = {"total": 0, "vetoed": 0, "good_catch": 0, "missed_win": 0,
               "penalized": 0}

    for r in results:
        sym = r["symbol"]
        s = by_sym[sym]
        s["total"] += 1
        overall["total"] += 1
        if r["would_veto"]:
            s["vetoed"] += 1
            overall["vetoed"] += 1
            bucket = by_reason[r["stage1c_reason"]]
            if r["corrected_status"] == "stopped":
                s["good_catch"] += 1
                s["pips_saved"] += abs(r["realized_pips"])
                overall["good_catch"] += 1
                bucket["good"] += 1
            elif r["corrected_status"] == "completed":
                s["missed_win"] += 1
                s["pips_missed"] += max(0.0, r["realized_pips"])
                overall["missed_win"] += 1
                bucket["missed"] += 1
            else:
                s["neutral"] += 1
        elif r["stage1c_penalty"] > 0:
            s["penalized"] += 1
            overall["penalized"] += 1

    for sym, s in by_sym.items():
        s["pips_saved"] = round(s["pips_saved"], 2)
        s["pips_missed"] = round(s["pips_missed"], 2)
        s["net_pips_saved"] = round(s["pips_saved"] - s["pips_missed"], 2)
        s["veto_rate_pct"] = round(100 * s["vetoed"] / s["total"], 2) if s["total"] else 0
        resolved = s["good_catch"] + s["missed_win"]
        s["veto_precision_pct"] = round(100 * s["good_catch"] / resolved, 1) if resolved else None

    overall_resolved = overall["good_catch"] + overall["missed_win"]
    overall["veto_precision_pct"] = round(
        100 * overall["good_catch"] / overall_resolved, 1) if overall_resolved else None
    overall["veto_rate_pct"] = round(
        100 * overall["vetoed"] / overall["total"], 2) if overall["total"] else 0

    return {
        "status": "ok",
        "overall": overall,
        "by_symbol": dict(by_sym),
        "by_reason": dict(by_reason),
    }
