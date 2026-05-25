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
    beklediği payload şemasına dönüştür."""
    try:
        from order_block_detector_v2 import MarketStructureAnalyzer
    except Exception as e:
        logger.warning("[entry-bt] MarketStructureAnalyzer import: %s", e)
        return {"order_blocks": [], "fvg_list": [], "swing_points": []}

    # MarketStructureAnalyzer.analyze beklenen format: Candle objesi listesi.
    # OrderBlockService _rows_to_candles helper'ı bunu yapıyor; ama bizim
    # candle dict'lerimizden direkt liste yapmak için kendi minimal Candle
    # sınıfımızı kullanabiliriz. Daha temizi: order_block_detector'dan Candle'ı import et.
    try:
        from order_block_detector import Candle
    except Exception as e:
        logger.warning("[entry-bt] Candle import: %s", e)
        return {"order_blocks": [], "fvg_list": [], "swing_points": []}

    cand_objs = []
    for b in candles_15m:
        try:
            ts = b.get("ts") or b.get("timestamp")
            if isinstance(ts, datetime):
                ts_iso = ts.isoformat()
            else:
                ts_iso = str(ts)
            cand_objs.append(Candle(
                timestamp=ts_iso,
                open=float(b.get("open") or b.get("o") or 0),
                high=float(b.get("high") or b.get("h") or 0),
                low=float(b.get("low") or b.get("l") or 0),
                close=float(b.get("close") or b.get("c") or 0),
                volume=float(b.get("volume") or b.get("v") or 0),
            ))
        except Exception:
            continue
    if len(cand_objs) < 20:
        return {"order_blocks": [], "fvg_list": [], "swing_points": []}

    try:
        structure = MarketStructureAnalyzer.analyze(cand_objs, symbol=symbol)
    except Exception as e:
        logger.warning("[entry-bt] analyze hata %s: %s", symbol, e)
        return {"order_blocks": [], "fvg_list": [], "swing_points": []}

    obs = [ob.to_dict() for ob in (structure.ob_list or [])[:10]]
    fvgs = [f.to_dict() for f in (structure.fvg_list or [])]
    # swing_points → "current_idx" hesabı için (entry_optimizer kullanıyor)
    sp = []
    for attr in ("swing_points", "swings"):
        v = getattr(structure, attr, None)
        if v:
            for s in v:
                sp.append({"index": int(getattr(s, "index", 0) or 0)})
            break
    return {"order_blocks": obs, "fvg_list": fvgs, "swing_points": sp,
            "structure": {"counts": {"ob": len(obs)}},
            "combined_signal": {}}


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
                                    sl: float, tp: float
                                    ) -> tuple[str, float, dict]:
    """Limit fill kontrolü → fill olursa o noktadan SL/TP walk.
    Döner: (status, exit_price, info).
    status ∈ {completed, stopped, expired, limit_missed}."""
    if not bars_after or limit_price <= 0:
        return ("limit_missed", limit_price, {"reason": "no_bars"})
    fill_idx = -1
    for i, b in enumerate(bars_after[:max_wait_bars_1m]):
        h = float(b.get("high") or 0)
        l = float(b.get("low") or 0)
        # Limit fill: BUY için fiyat limit_price'a İNERSE, SELL için ÇIKARSA
        if direction == "BUY" and l <= limit_price:
            fill_idx = i
            break
        if direction == "SELL" and h >= limit_price:
            fill_idx = i
            break
    if fill_idx < 0:
        return ("limit_missed", limit_price,
                {"waited_bars": min(len(bars_after), max_wait_bars_1m)})
    status, exit_p, bars_walked = _simulate_outcome(
        bars_after[fill_idx + 1:], direction, limit_price, sl, tp)
    return (status, exit_p, {"fill_idx_1m": fill_idx,
                              "post_fill_bars": bars_walked})


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


# ─── Ana fonksiyon ───────────────────────────────────────────────────────────
async def backtest_entry_optimizer(days: int = 90,
                                     sample_per_scope: int = 300,
                                     symbols: Optional[list[str]] = None,
                                     timeframe: str = "15m",
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
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

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
        page = res.data if hasattr(res, "data") else []
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
    actions: dict = {"EXECUTE_NOW": [], "LIMIT_ORDER": [], "REJECT": []}
    errors = 0
    per_sym_stats: dict = {}

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

        if action == "REJECT":
            outcome["sim_status"] = "no_trade"
            outcome["sim_realized_pips"] = 0.0
            outcome["sim_r_mult"] = 0.0
        elif action == "EXECUTE_NOW":
            status, exit_p, bw = _simulate_outcome(
                bars_after, r["direction"], entry_p, sl_p, tp_p)
            sim_pips = _realized_pips_signed(sym, r["direction"], entry_p, exit_p)
            sim_r = None
            if atr > 0:
                try:
                    from services.target_config import pips_from_price_change
                    ap = pips_from_price_change(atr, sym)
                    if ap > 0:
                        sim_r = sim_pips / ap
                except Exception:
                    pass
            outcome.update({"sim_status": status, "sim_exit": exit_p,
                            "sim_bars_walked": bw,
                            "sim_realized_pips": round(sim_pips, 3),
                            "sim_r_mult": round(sim_r, 3) if sim_r is not None else None})
        elif action == "LIMIT_ORDER":
            max_wait_1m = int(decision.get("max_wait_candles") or 5) * 15
            status, exit_p, info = _simulate_limit_then_outcome(
                bars_after, r["direction"], entry_p, max_wait_1m, sl_p, tp_p)
            if status == "limit_missed":
                sim_pips = 0.0; sim_r = 0.0
            else:
                sim_pips = _realized_pips_signed(sym, r["direction"], entry_p, exit_p)
                sim_r = None
                if atr > 0:
                    try:
                        from services.target_config import pips_from_price_change
                        ap = pips_from_price_change(atr, sym)
                        if ap > 0:
                            sim_r = sim_pips / ap
                    except Exception:
                        pass
            outcome.update({"sim_status": status, "sim_exit": exit_p,
                            "sim_info": info,
                            "sim_realized_pips": round(sim_pips, 3),
                            "sim_r_mult": round(sim_r, 3) if sim_r is not None else None})

        actions.setdefault(action, []).append(outcome)
        ss = per_sym_stats.setdefault(sym, {"total": 0,
                                              "by_action": {}})
        ss["total"] += 1
        ss["by_action"][action] = ss["by_action"].get(action, 0) + 1

    return _summarize(actions, per_sym_stats, errors, len(rows))


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
        # LIMIT için fill rate
        extra: dict = {}
        if act == "LIMIT_ORDER" and rows:
            filled = sum(1 for r in rows if r.get("sim_status") not in
                          ("limit_missed", None, "no_trade"))
            extra["fill_rate_pct"] = round(100 * filled / len(rows), 1)
            extra["filled_n"] = filled
        # REJECT için "kaçırılan kazanç" — original'da TP olanlar
        if act == "REJECT" and rows:
            orig_wins = sum(1 for r in rows if r.get("orig_status") == "completed")
            orig_losses = sum(1 for r in rows if r.get("orig_status") == "stopped")
            extra["orig_win_rate_pct_if_we_had_traded"] = round(
                100 * orig_wins / (orig_wins + orig_losses), 1) if (orig_wins + orig_losses) else None
            extra["orig_avg_pips_we_skipped"] = (
                round(sum(r.get("orig_realized_pips") or 0 for r in rows) / len(rows), 3))
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
    rejects = summary.get("REJECT", {})
    rej_orig_wr = (rejects.get("orig_win_rate_pct_if_we_had_traded") or 0)
    if rej_orig_wr and rej_orig_wr < 50:
        parts.append(f"REJECT doğru çalışıyor: reddedilenlerin gerçek WR'i %{rej_orig_wr} (<50%).")
    elif rej_orig_wr:
        parts.append(f"REJECT şüpheli: reddedilenlerin gerçek WR'i %{rej_orig_wr} (>=50%). FILTER TOO STRICT?")
    limit = summary.get("LIMIT_ORDER", {})
    if limit.get("fill_rate_pct") is not None:
        parts.append(f"LIMIT fill rate %{limit['fill_rate_pct']}.")
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
