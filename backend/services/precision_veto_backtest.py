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
    """Stage 1c v2 kurallarını verilmiş bir DS üzerinde uygula (live fetch yok).
    Yeni mantık: hard veto YOK, sadece rejim-farkında soft penalty."""
    if ds is None or ds.atr <= 0:
        return None, 0.0
    total_penalty = 0.0

    nz = ds.nearest_memory_zone_in_direction(direction)
    if nz is not None and nz.freshness >= 0.5:
        d = abs(nz.center - price) / ds.atr
        broken = any(abs(c - nz.center) < ds.atr * 0.15
                      for c in ds.recently_broken_zone_centers)
        if d <= 0.20 and not broken:
            zone_type = "resistance" if direction == "BUY" else "support"
            trend_supports_zone = (
                (zone_type == "resistance" and ds.regime == "TRENDING_DOWN")
                or (zone_type == "support" and ds.regime == "TRENDING_UP")
            )
            if ds.regime == "RANGING" and nz.rejections >= 3:
                total_penalty += 15
            elif trend_supports_zone and nz.rejections >= 4 and nz.freshness >= 0.7:
                total_penalty += 8
            # TRENDING + trend yönünde zone → likidite hedefi, penalty YOK

    if direction == "BUY" and ds.pdh is not None:
        d = abs(ds.pdh - price) / ds.atr
        if d <= 0.10 and ds.pdh_rejections_today >= 2:
            total_penalty += 10
    if direction == "SELL" and ds.pdl is not None:
        d = abs(ds.pdl - price) / ds.atr
        if d <= 0.10 and ds.pdl_rejections_today >= 2:
            total_penalty += 10

    opposing = ("R1", "R2") if direction == "BUY" else ("S1", "S2")
    for name in opposing:
        if name not in ds.pivots:
            continue
        d = abs(ds.pivots[name] - price) / ds.atr
        if d <= 0.08:
            total_penalty += 5
            break

    if total_penalty > 20:
        total_penalty = 20
    return None, total_penalty


def _summarize(results: list[dict]) -> dict:
    from collections import defaultdict
    by_sym: dict = defaultdict(lambda: {
        "total": 0, "penalized": 0,
        "penalized_stopped": 0, "penalized_completed": 0,
        "clean_stopped": 0, "clean_completed": 0,
        "pen_stopped_pips": 0.0, "pen_completed_pips": 0.0,
    })
    overall = {"total": 0, "penalized": 0,
                "penalized_stopped": 0, "penalized_completed": 0,
                "clean_stopped": 0, "clean_completed": 0}

    for r in results:
        sym = r["symbol"]
        s = by_sym[sym]
        s["total"] += 1
        overall["total"] += 1
        is_pen = r["stage1c_penalty"] > 0
        if is_pen:
            s["penalized"] += 1
            overall["penalized"] += 1
            if r["corrected_status"] == "stopped":
                s["penalized_stopped"] += 1
                s["pen_stopped_pips"] += abs(r["realized_pips"])
                overall["penalized_stopped"] += 1
            elif r["corrected_status"] == "completed":
                s["penalized_completed"] += 1
                s["pen_completed_pips"] += max(0.0, r["realized_pips"])
                overall["penalized_completed"] += 1
        else:
            if r["corrected_status"] == "stopped":
                s["clean_stopped"] += 1
                overall["clean_stopped"] += 1
            elif r["corrected_status"] == "completed":
                s["clean_completed"] += 1
                overall["clean_completed"] += 1

    # Penaltı'nın seçici olup olmadığını ölçen iki metrik:
    #   pen_stop_rate  = penalize edilenlerin SL oranı (yüksek = doğru hedefliyoruz)
    #   clean_stop_rate= penalize edilmeyenlerin SL oranı (baz çizgi)
    # Aralarındaki fark = penaltının gerçek seçicilik kazancı.
    for sym, s in by_sym.items():
        s["pen_stopped_pips"] = round(s["pen_stopped_pips"], 2)
        s["pen_completed_pips"] = round(s["pen_completed_pips"], 2)
        s["net_pips_saved_if_vetoed"] = round(
            s["pen_stopped_pips"] - s["pen_completed_pips"], 2)
        s["penalty_rate_pct"] = round(100 * s["penalized"] / s["total"], 2) if s["total"] else 0
        pen_res = s["penalized_stopped"] + s["penalized_completed"]
        s["pen_stop_rate_pct"] = round(100 * s["penalized_stopped"] / pen_res, 1) if pen_res else None
        clean_res = s["clean_stopped"] + s["clean_completed"]
        s["clean_stop_rate_pct"] = round(100 * s["clean_stopped"] / clean_res, 1) if clean_res else None
        if s["pen_stop_rate_pct"] is not None and s["clean_stop_rate_pct"] is not None:
            s["selectivity_lift_pp"] = round(
                s["pen_stop_rate_pct"] - s["clean_stop_rate_pct"], 1)

    overall["penalty_rate_pct"] = round(
        100 * overall["penalized"] / overall["total"], 2) if overall["total"] else 0
    pen_res = overall["penalized_stopped"] + overall["penalized_completed"]
    overall["pen_stop_rate_pct"] = round(
        100 * overall["penalized_stopped"] / pen_res, 1) if pen_res else None
    clean_res = overall["clean_stopped"] + overall["clean_completed"]
    overall["clean_stop_rate_pct"] = round(
        100 * overall["clean_stopped"] / clean_res, 1) if clean_res else None
    if overall["pen_stop_rate_pct"] and overall["clean_stop_rate_pct"]:
        overall["selectivity_lift_pp"] = round(
            overall["pen_stop_rate_pct"] - overall["clean_stop_rate_pct"], 1)

    return {
        "status": "ok",
        "overall": overall,
        "by_symbol": dict(by_sym),
        "note": ("selectivity_lift_pp = penaltı verilen sinyallerin SL oranı − "
                  "verilmeyenlerin SL oranı. Pozitif = penaltı doğru hedefliyor."),
    }
