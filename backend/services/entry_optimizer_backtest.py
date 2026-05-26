"""
Entry Optimizer — 90 günlük honest replay backtest.

Her resolved sinyal için:
  1. signal_created_at anına kadar 15m candles point-in-time olarak topla
  2. MarketStructureAnalyzer.analyze(candles) → OB + FVG yapısı
  3. entry_optimizer.decide_from_payload(signal, ob_payload, cfg) → action
  4. Outcome simülasyonu (1m bar walk-forward):
     - EXECUTE_NOW: optimizer'ın SL/TP'sine göre walk → first-hit
     - LIMIT_ORDER: max_wait_candles içinde limit_price'a değdi mi → değdiyse o
       andan itibaren SL/TP walk; değmediyse "limit_missed"
     - REJECT: trade yok, realized = 0

Karşılaştırma:
  - Original sistem: prediction_replay_corrections'ın corrected_exit_price'ı
    (mevcut TP/SL config ile) → realized pips
  - Entry Optimizer: simülasyon çıktısı

Çıktı: action başına n, gerçek WR (sadece resolved), avg realized R, net pips
delta. Markdown tablo + verdict.
"""
from __future__ import annotations

import asyncio
import bisect
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def _parse(t):
    try:
        return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except Exception:
        return None


def _atr_from_candles(candles_15m: list[dict], period: int = 14) -> float:
    if len(candles_15m) < period + 1:
        return 0.0
    trs = []
    for i in range(len(candles_15m) - period, len(candles_15m)):
        h = float(candles_15m[i].get("high") or 0)
        l = float(candles_15m[i].get("low") or 0)
        cp = float(candles_15m[i - 1].get("close") or 0)
        trs.append(max(h - l, abs(h - cp), abs(l - cp)))
    return sum(trs) / len(trs) if trs else 0.0


def _candles_to_ob_payload(candles_15m: list[dict], symbol: str) -> dict:
    """MarketStructureAnalyzer ile OB/FVG yapısını çıkar, entry_optimizer'ın
    beklediği payload şemasına dönüştür.

    DİKKAT: Candle ve MarketStructureAnalyzer aynı modülden (v2) import
    edilmeli — v1 ile karıştırılırsa duck typing'de sessiz başarısızlık olur."""
    debug = {"step": "init"}
    try:
        # v2'nin kendi Candle sınıfı — analyze ile aynı modülde
        from order_block_detector_v2 import MarketStructureAnalyzer, Candle
        debug["step"] = "import_ok"
    except Exception as e:
        return {"order_blocks": [], "fvg_list": [], "swing_points": [],
                "_error": f"import: {e}"}

    cand_objs = []
    for b in candles_15m:
        try:
            ts = b.get("ts") or b.get("timestamp")
            # timestamp = epoch seconds (float) — v2 Candle dataclass: float
            if isinstance(ts, datetime):
                ts_val = ts.timestamp()
            elif isinstance(ts, (int, float)):
                ts_val = float(ts)
            else:
                # string fallback — parse veya 0
                try:
                    ts_val = datetime.fromisoformat(
                        str(ts).replace("Z", "+00:00")).timestamp()
                except Exception:
                    ts_val = 0.0
            cand_objs.append(Candle(
                timestamp=ts_val,
                open=float(b.get("open") or b.get("o") or 0),
                high=float(b.get("high") or b.get("h") or 0),
                low=float(b.get("low") or b.get("l") or 0),
                close=float(b.get("close") or b.get("c") or 0),
                volume=float(b.get("volume") or b.get("v") or 0),
            ))
        except Exception as e:
            debug["candle_err"] = str(e)[:80]
            continue
    debug["n_candles"] = len(cand_objs)
    if len(cand_objs) < 20:
        return {"order_blocks": [], "fvg_list": [], "swing_points": [],
                "_debug": debug}

    try:
        structure = MarketStructureAnalyzer.analyze(cand_objs, symbol=symbol)
        debug["step"] = "analyzed"
        debug["ob_count_raw"] = len(structure.ob_list or [])
        debug["fvg_count_raw"] = len(structure.fvg_list or [])
    except Exception as e:
        return {"order_blocks": [], "fvg_list": [], "swing_points": [],
                "_error": f"analyze: {e}", "_debug": debug}

    obs = [ob.to_dict() for ob in (structure.ob_list or [])[:10]]
    fvgs = [f.to_dict() for f in (structure.fvg_list or [])]
    sp = []
    for attr in ("swing_points", "swings"):
        v = getattr(structure, attr, None)
        if v:
            for s in v:
                sp.append({"index": int(getattr(s, "index", 0) or 0)})
            break
    debug["ob_enriched"] = len(obs)
    debug["fvg_enriched"] = len(fvgs)
    debug["swings"] = len(sp)
    return {"order_blocks": obs, "fvg_list": fvgs, "swing_points": sp,
            "structure": {"counts": {"ob": len(obs)}},
            "combined_signal": {}, "_debug": debug}


def _simulate_outcome(bars_after: list[dict], direction: str,
                       entry: float, sl: float, tp: float
                       ) -> tuple[str, float, int]:
    """1m bars üzerinde walk → first-hit. Döner: (status, exit_price, bars_walked).
    status ∈ {completed, stopped, expired}."""
    if not bars_after or entry <= 0 or sl <= 0 or tp <= 0:
        return ("expired", entry, 0)
    for i, b in enumerate(bars_after):
        h = float(b.get("high") or 0)
        l = float(b.get("low") or 0)
        if direction == "BUY":
            hit_tp = h >= tp
            hit_sl = l <= sl
        else:
            hit_tp = l <= tp
            hit_sl = h >= sl
        if hit_tp and hit_sl:
            # in-bar ambiguity — OHLC heuristic
            o = float(b.get("open") or 0)
            c = float(b.get("close") or 0)
            bullish = c >= o
            tp_first = (not bullish) if direction == "BUY" else bullish
            return (("completed", tp, i + 1) if tp_first
                     else ("stopped", sl, i + 1))
        if hit_tp:
            return ("completed", tp, i + 1)
        if hit_sl:
            return ("stopped", sl, i + 1)
    return ("expired", float(bars_after[-1].get("close") or entry), len(bars_after))


def _simulate_limit_then_outcome(bars_after: list[dict], direction: str,
                                    limit_price: float, max_wait_bars_1m: int,
                                    sl: float, tp: float, symbol: str = ""
                                    ) -> tuple[str, float, dict]:
    """Limit fill kontrolü → fill olursa o noktadan SL/TP walk.

    Fill olmazsa (max_wait_bars_1m'de değmediyse): FALLBACK_MARKET — o anki
    bar fiyatından market entry, sembolün varsayılan TP/SL config'iyle
    walk-forward. 2026-05-26 tweak: önceki sürüm "limit_missed" döndürürdü,
    1213 sinyalin %37.8'i = 459 sinyal kaybediyorduk.

    Döner: (status, exit_price, info)."""
    if not bars_after or limit_price <= 0:
        return ("expired", limit_price, {"reason": "no_bars"})
    fill_idx = -1
    for i, b in enumerate(bars_after[:max_wait_bars_1m]):
        h = float(b.get("high") or 0)
        l = float(b.get("low") or 0)
        if direction == "BUY" and l <= limit_price:
            fill_idx = i
            break
        if direction == "SELL" and h >= limit_price:
            fill_idx = i
            break
    if fill_idx >= 0:
        status, exit_p, bars_walked = _simulate_outcome(
            bars_after[fill_idx + 1:], direction, limit_price, sl, tp)
        return (status, exit_p, {"fill_idx_1m": fill_idx,
                                  "post_fill_bars": bars_walked,
                                  "via": "limit_fill"})
    # ── FALLBACK_MARKET after limit timeout ─────────────────────────────────
    timeout_idx = min(len(bars_after) - 1, max_wait_bars_1m - 1)
    timeout_bar = bars_after[timeout_idx]
    fallback_entry = float(timeout_bar.get("open")
                            or timeout_bar.get("close") or limit_price)
    try:
        from services.target_config import (
            calculate_target_prices, calculate_stoploss_price)
        targets = calculate_target_prices(fallback_entry, direction, symbol, "15m")
        fb_tp = targets.get("TP2") or targets.get("TP1") or fallback_entry
        fb_sl = calculate_stoploss_price(fallback_entry, direction, symbol, "15m")
    except Exception:
        # Ultra-safe — orijinal SL/TP'yi entry'ye paralel kaydır
        delta_sl = sl - limit_price
        delta_tp = tp - limit_price
        fb_sl = fallback_entry + delta_sl
        fb_tp = fallback_entry + delta_tp
    status, exit_p, bars_walked = _simulate_outcome(
        bars_after[timeout_idx + 1:], direction, fallback_entry, fb_sl, fb_tp)
    return (status, exit_p, {"fill_idx_1m": -1,
                              "via": "fallback_market_after_timeout",
                              "fallback_entry": fallback_entry,
                              "fallback_sl": fb_sl, "fallback_tp": fb_tp,
                              "post_fallback_bars": bars_walked,
                              "waited_bars": timeout_idx + 1})


def _realized_pips_signed(symbol: str, direction: str,
                            entry: float, exit_p: float) -> float:
    try:
        from services.target_config import pips_from_price_change
    except Exception:
        diff = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
        return diff
    diff = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
    try:
        mag = abs(pips_from_price_change(abs(diff), symbol))
        return mag if diff >= 0 else -mag
    except Exception:
        return diff


# ─── Slippage + spread modeli ────────────────────────────────────────────────
# Sembol bazlı spread (pip cinsinden — USOIL için yüzde)
SPREAD_PIPS = {
    "XAUUSD": 3.5,
    "NDX.INDX": 1.5,
    "GDAXI.INDX": 1.5,
    "USOIL.FOREX": 0.03,   # percentage (0.03%)
}
# Slippage aralığı (pip — USOIL için yüzde)
SLIPPAGE_RANGE = (0.1, 0.5)


def _spread_price(symbol: str, entry: float) -> float:
    """Sembol spread'ini price units'e çevir."""
    sp = SPREAD_PIPS.get(symbol, 1.0)
    if symbol == "USOIL.FOREX":
        return entry * sp / 100.0
    return sp   # pip_value=1.0 hepsi için


def _apply_slippage(entry: float, direction: str, symbol: str,
                     rng: random.Random) -> float:
    """Market entry'ye spread/2 + random slip ekle (aleyhe yönde)."""
    spread = _spread_price(symbol, entry)
    slip_pips = rng.uniform(*SLIPPAGE_RANGE)
    if symbol == "USOIL.FOREX":
        slip = entry * slip_pips / 100.0
    else:
        slip = slip_pips
    if direction == "BUY":
        return entry + spread / 2 + slip
    return entry - spread / 2 - slip


# ─── Ana fonksiyon ───────────────────────────────────────────────────────────
async def backtest_entry_optimizer(days: int = 90,
                                     sample_per_scope: int = 300,
                                     symbols: Optional[list[str]] = None,
                                     timeframe: str = "15m",
                                     day_offset_start: int = 0,
                                     day_offset_end: Optional[int] = None,
                                     apply_slippage: bool = False,
                                     ) -> dict:
    """Stage 4'ten geçen tüm resolved sinyaller üzerinde Entry Optimizer'ı
    point-in-time simüle eder. sample_per_scope=0 → tümü."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    from services.signal_replay_1m import _load_all_1m_bars_sync
    from services.precision_veto_backtest import _aggregate, _slice_up_to
    from services.entry_optimizer import decide_from_payload, DEFAULT_CONFIG

    symbols = symbols or ["XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()
    # Walk-forward window — days içinde alt aralık
    window_start = now - timedelta(days=days - day_offset_start)
    window_end = (now - timedelta(days=days - day_offset_end)
                   if day_offset_end is not None else now)

    # ── Sinyaller ────────────────────────────────────────────────────────────
    rows: list[dict] = []
    offset = 0
    PAGE = 1000
    while True:
        q = (client.table("prediction_replay_corrections").select(
            "prediction_id,symbol,model_type,direction,entry_price,timeframe,"
            "signal_created_at,corrected_status,corrected_exit_price,"
            "corrected_mfe_pips,corrected_mae_pips,replay_status")
             .gte("signal_created_at", since)
             .order("signal_created_at", desc=False)
             .range(offset, offset + PAGE - 1))
        res = q.execute() if hasattr(q, "execute") else q
        page = (res.data if hasattr(res, "data")
                 else (res.get("data") if isinstance(res, dict) else [])) or []
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
    # Walk-forward filtering — sadece [window_start, window_end] aralığındaki sinyaller
    if day_offset_start > 0 or day_offset_end is not None:
        filtered = []
        for r in rows:
            ts = _parse(r.get("signal_created_at"))
            if ts is None: continue
            if ts < window_start: continue
            if ts > window_end: continue
            filtered.append(r)
        rows = filtered
    if not rows:
        return {"status": "ok", "scanned": 0, "note": "veri yok"}

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

    # ── Sembol başına 1m bars + 15m agregasyon ──────────────────────────────
    per_symbol: dict = {}
    for sym in symbols:
        bars_1m = await asyncio.to_thread(_load_all_1m_bars_sync, sym)
        if not bars_1m:
            continue
        per_symbol[sym] = {
            "1m": bars_1m, "1m_keys": [b["ts"] for b in bars_1m],
            "15m": _aggregate(bars_1m, "15m"),
        }
        per_symbol[sym]["15m_keys"] = [b["ts"] for b in per_symbol[sym]["15m"]]
    if not per_symbol:
        return {"status": "error", "error": "1m candle yok"}

    # ── Her sinyal için decide + simüle ──────────────────────────────────────
    cfg = DEFAULT_CONFIG
    actions: dict = {"EXECUTE_NOW": [], "LIMIT_ORDER": [],
                       "FALLBACK_MARKET": [], "PASSTHROUGH": []}
    # Slippage rng — deterministik (seed = prediction_id hash)
    slip_rng = random.Random(42) if apply_slippage else None
    errors = 0
    per_sym_stats: dict = {}
    payload_diag = {"empty_payloads": 0, "had_obs": 0, "had_fvgs": 0,
                     "import_errors": 0, "analyze_errors": 0,
                     "first_error": None, "sample_debug": None}

    for r in rows:
        sym = r["symbol"]
        ps = per_symbol.get(sym)
        if not ps:
            continue
        cutoff = _parse(r["signal_created_at"])
        if cutoff is None:
            continue
        # Point-in-time 15m slice
        c_15m = _slice_up_to(ps["15m"], ps["15m_keys"], cutoff, last_n=cfg["candle_limit"])
        if len(c_15m) < 30:
            continue
        current_price = float(c_15m[-1].get("close") or r["entry_price"] or 0)
        if current_price <= 0:
            continue
        atr = _atr_from_candles(c_15m)
        # OB payload
        ob_payload = _candles_to_ob_payload(c_15m, sym)
        if ob_payload.get("_error"):
            err = ob_payload["_error"]
            if "import" in err:
                payload_diag["import_errors"] += 1
            else:
                payload_diag["analyze_errors"] += 1
            if payload_diag["first_error"] is None:
                payload_diag["first_error"] = err
                payload_diag["sample_debug"] = ob_payload.get("_debug")
        if not ob_payload.get("order_blocks") and not ob_payload.get("fvg_list"):
            payload_diag["empty_payloads"] += 1
            if payload_diag["sample_debug"] is None:
                payload_diag["sample_debug"] = ob_payload.get("_debug")
        else:
            if ob_payload.get("order_blocks"):
                payload_diag["had_obs"] += 1
            if ob_payload.get("fvg_list"):
                payload_diag["had_fvgs"] += 1
        try:
            signal = {"symbol": sym, "direction": r["direction"],
                        "price": current_price, "atr": atr,
                        "timeframe": timeframe}
            decision = decide_from_payload(signal, ob_payload, cfg)
        except Exception as e:
            errors += 1
            logger.debug("decide err: %s", e)
            continue

        # ── İleri 1m bars (outcome simülasyonu) ─────────────────────────────
        # Max 6 saat ileri (24×15m = 360 mum)
        window_end = cutoff + timedelta(minutes=360)
        idx_end = bisect.bisect_right(ps["1m_keys"], window_end)
        idx_start = bisect.bisect_right(ps["1m_keys"], cutoff)
        bars_after = ps["1m"][idx_start:idx_end]

        action = decision.get("action") or "REJECT"
        entry_p = float(decision.get("entry_price") or 0)
        sl_p = float(decision.get("sl_price") or 0)
        tp_p = float(decision.get("tp_price") or 0)

        # Original outcome (karşılaştırma için)
        orig_status = r["corrected_status"]
        orig_exit = float(r.get("corrected_exit_price") or 0)
        orig_pips = _realized_pips_signed(sym, r["direction"],
                                            float(r["entry_price"]), orig_exit)
        orig_r_mult = None
        if atr > 0:
            try:
                from services.target_config import pips_from_price_change
                atr_pips = pips_from_price_change(atr, sym)
                if atr_pips > 0:
                    orig_r_mult = orig_pips / atr_pips
            except Exception:
                pass

        outcome: dict = {"symbol": sym, "direction": r["direction"],
                          "action": action,
                          "structure_type": decision.get("structure_type"),
                          "priority_score": decision.get("priority_score"),
                          "orig_status": orig_status,
                          "orig_realized_pips": round(orig_pips, 3),
                          "orig_r_mult": round(orig_r_mult, 3) if orig_r_mult is not None else None}

        def _r_from_pips(pips_val: float) -> Optional[float]:
            if atr <= 0:
                return None
            try:
                from services.target_config import pips_from_price_change
                ap = pips_from_price_change(atr, sym)
                if ap > 0:
                    return pips_val / ap
            except Exception:
                pass
            return None

        if action in ("EXECUTE_NOW", "FALLBACK_MARKET", "PASSTHROUGH"):
            # Her ikisi de market entry — sadece SL/TP kaynağı farklı
            # Slippage: gerçekçi market fill — spread/2 + uniform slip
            if apply_slippage and slip_rng is not None:
                entry_p = _apply_slippage(entry_p, r["direction"], sym, slip_rng)
            status, exit_p, bw = _simulate_outcome(
                bars_after, r["direction"], entry_p, sl_p, tp_p)
            sim_pips = _realized_pips_signed(sym, r["direction"], entry_p, exit_p)
            outcome.update({"sim_status": status, "sim_exit": exit_p,
                            "sim_bars_walked": bw,
                            "sim_realized_pips": round(sim_pips, 3),
                            "sim_r_mult": (round(_r_from_pips(sim_pips), 3)
                                            if _r_from_pips(sim_pips) is not None
                                            else None)})
        elif action == "LIMIT_ORDER":
            max_wait_1m = int(decision.get("max_wait_candles") or 5) * 15
            status, exit_p, info = _simulate_limit_then_outcome(
                bars_after, r["direction"], entry_p, max_wait_1m, sl_p, tp_p,
                symbol=sym)
            actual_entry = (info.get("fallback_entry") if info.get("via") ==
                              "fallback_market_after_timeout" else entry_p)
            # Slippage: limit fill için küçük (filled exactly), fallback market için tam slippage
            if apply_slippage and slip_rng is not None:
                if info.get("via") == "fallback_market_after_timeout":
                    actual_entry = _apply_slippage(actual_entry, r["direction"],
                                                     sym, slip_rng)
                else:
                    # Limit fill — sadece spread'in yarısı (favorable fill)
                    actual_entry = _apply_slippage(actual_entry, r["direction"],
                                                     sym, slip_rng) * 0.5 + actual_entry * 0.5
            sim_pips = _realized_pips_signed(sym, r["direction"],
                                               actual_entry, exit_p)
            outcome.update({"sim_status": status, "sim_exit": exit_p,
                            "sim_info": info,
                            "sim_entry_actual": actual_entry,
                            "sim_realized_pips": round(sim_pips, 3),
                            "sim_r_mult": (round(_r_from_pips(sim_pips), 3)
                                            if _r_from_pips(sim_pips) is not None
                                            else None)})

        actions.setdefault(action, []).append(outcome)
        ss = per_sym_stats.setdefault(sym, {"total": 0,
                                              "by_action": {}})
        ss["total"] += 1
        ss["by_action"][action] = ss["by_action"].get(action, 0) + 1

    summary = _summarize(actions, per_sym_stats, errors, len(rows))
    summary["payload_diagnostics"] = payload_diag
    # Per-symbol delta — main run'dan ek çağrı yapmaya gerek yok
    summary["per_symbol_delta"] = _summarize_per_symbol_delta(actions)
    return summary


def _summarize_per_symbol_delta(actions: dict) -> dict:
    """Sembol bazında original vs optimizer toplam pip + delta_pct."""
    from collections import defaultdict
    per: dict = defaultdict(lambda: {"n": 0, "orig_pips": 0.0, "opt_pips": 0.0})
    for act, rows in actions.items():
        for r in rows:
            sym = r.get("symbol")
            if not sym: continue
            per[sym]["n"] += 1
            per[sym]["orig_pips"] += r.get("orig_realized_pips") or 0
            per[sym]["opt_pips"] += r.get("sim_realized_pips") or 0
    out = {}
    for sym, s in per.items():
        op = s["orig_pips"]; sp = s["opt_pips"]
        out[sym] = {
            "n": s["n"],
            "original_pips": round(op, 2),
            "optimizer_pips": round(sp, 2),
            "delta_pips": round(sp - op, 2),
            "delta_pct": (round(100 * (sp - op) / abs(op), 1)
                           if abs(op) > 1e-9 else None),
        }
    return out


def _summarize(actions: dict, per_sym_stats: dict, errors: int,
                scanned: int) -> dict:
    def stats(rows: list[dict], key_pips: str, key_r: str, key_status: str) -> dict:
        if not rows:
            return {"n": 0}
        pips = [r.get(key_pips) for r in rows if r.get(key_pips) is not None]
        rmult = [r.get(key_r) for r in rows if r.get(key_r) is not None]
        wins = sum(1 for r in rows if (r.get(key_status) == "completed"))
        losses = sum(1 for r in rows if (r.get(key_status) == "stopped"))
        out = {"n": len(rows),
                "avg_pips": round(sum(pips) / len(pips), 3) if pips else None,
                "sum_pips": round(sum(pips), 2) if pips else None,
                "avg_r_mult": round(sum(rmult) / len(rmult), 3) if rmult else None,
                "wins": wins, "losses": losses,
                "win_rate_pct": round(100 * wins / (wins + losses), 1)
                                  if (wins + losses) else None}
        return out

    # Per-action özet
    summary: dict = {}
    for act, rows in actions.items():
        s_orig = stats(rows, "orig_realized_pips", "orig_r_mult", "orig_status")
        s_sim = stats(rows, "sim_realized_pips", "sim_r_mult", "sim_status")
        # LIMIT — fill rate + timeout fallback breakdown
        extra: dict = {}
        if act == "LIMIT_ORDER" and rows:
            filled = sum(1 for r in rows
                          if (r.get("sim_info") or {}).get("via") == "limit_fill")
            timeout_fallback = sum(1 for r in rows
                                     if (r.get("sim_info") or {}).get("via") ==
                                          "fallback_market_after_timeout")
            extra["fill_rate_pct"] = round(100 * filled / len(rows), 1)
            extra["filled_n"] = filled
            extra["timeout_fallback_n"] = timeout_fallback
            extra["timeout_fallback_pct"] = round(
                100 * timeout_fallback / len(rows), 1)
            # Fill olan vs timeout fallback'in ayrı performansı
            fill_rows = [r for r in rows
                          if (r.get("sim_info") or {}).get("via") == "limit_fill"]
            tof_rows = [r for r in rows
                          if (r.get("sim_info") or {}).get("via") ==
                            "fallback_market_after_timeout"]
            extra["fills_avg_pips"] = (
                round(sum(r.get("sim_realized_pips") or 0 for r in fill_rows)
                       / len(fill_rows), 3) if fill_rows else None)
            extra["timeout_fallback_avg_pips"] = (
                round(sum(r.get("sim_realized_pips") or 0 for r in tof_rows)
                       / len(tof_rows), 3) if tof_rows else None)
        # FALLBACK_MARKET — yapısız sinyaller (default config kullanıldı)
        if act == "FALLBACK_MARKET" and rows:
            extra["note"] = ("Yapı bulunamadı/uzak — default symbol TP/SL ile "
                              "market entry. Stage 4 sizing dışarıda uygulanır.")
        summary[act] = {"original_system": s_orig,
                          "entry_optimizer": s_sim,
                          **extra}

    # Sistem geneli karşılaştırma
    all_rows = [r for rows in actions.values() for r in rows]
    total_orig_pips = sum(r.get("orig_realized_pips") or 0 for r in all_rows)
    total_sim_pips = sum(r.get("sim_realized_pips") or 0 for r in all_rows)
    n = len(all_rows)
    overall = {
        "n": n,
        "original_total_pips": round(total_orig_pips, 2),
        "optimizer_total_pips": round(total_sim_pips, 2),
        "delta_pips": round(total_sim_pips - total_orig_pips, 2),
        "delta_pct": (round(100 * (total_sim_pips - total_orig_pips)
                              / abs(total_orig_pips), 2)
                        if abs(total_orig_pips) > 1e-9 else None),
        "avg_orig_pips_per_signal": round(total_orig_pips / n, 3) if n else None,
        "avg_sim_pips_per_signal": round(total_sim_pips / n, 3) if n else None,
    }

    # Verdict
    parts = []
    fb = summary.get("FALLBACK_MARKET", {})
    fb_opt = fb.get("entry_optimizer", {})
    if fb_opt.get("n"):
        parts.append(f"FALLBACK_MARKET: {fb_opt['n']} sinyal default config'le, "
                      f"avg {fb_opt.get('avg_pips')} pips, WR %{fb_opt.get('win_rate_pct')}.")
    limit = summary.get("LIMIT_ORDER", {})
    if limit.get("fill_rate_pct") is not None:
        parts.append(f"LIMIT: fill %{limit['fill_rate_pct']} (avg {limit.get('fills_avg_pips')}p), "
                      f"timeout-fallback %{limit.get('timeout_fallback_pct')} "
                      f"(avg {limit.get('timeout_fallback_avg_pips')}p).")
    if overall["delta_pct"] is not None:
        if overall["delta_pct"] > 5:
            parts.append(f"Toplam P&L iyileşmesi +%{overall['delta_pct']} → DEPLOY önerilir.")
        elif overall["delta_pct"] > -2:
            parts.append(f"Toplam P&L değişimi %{overall['delta_pct']} (marjinal) → TWEAK / shadow mode.")
        else:
            parts.append(f"Toplam P&L %{overall['delta_pct']} kötüleşti → HOLD, eşikleri gözden geçir.")
    verdict = " ".join(parts) or "Yeterli veri yok."

    return {
        "status": "ok",
        "scanned": scanned,
        "errors": errors,
        "by_action": summary,
        "overall": overall,
        "per_symbol": per_sym_stats,
        "verdict": verdict,
        "interpretation": {
            "original_system": "Mevcut TP/SL config ile gerçekleşen sonuçlar (prediction_replay_corrections).",
            "entry_optimizer": "Entry Optimizer'ın kararı + simüle edilmiş 1m walk-forward sonuç.",
            "REJECT.orig_win_rate_pct_if_we_had_traded": "Reddedilen sinyaller gerçekte WR'i — düşükse veto doğru.",
            "LIMIT_ORDER.fill_rate_pct": "Limit emirlerin max_wait_candles içinde dolma oranı.",
            "delta_pct": "(optimizer_total - original_total) / |original_total|. Pozitif = iyileşme.",
        },
    }
