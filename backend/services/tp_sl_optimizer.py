"""
TP/SL Optimizer — find the data-driven optimal Take-Profit and Stop-Loss
levels per (symbol, model_type, direction) using historical MFE/MAE.

Concept:
  - prediction_logs + outcome_results give us per-signal MFE (max favorable
    excursion in pips) and MAE (max adverse excursion in pips).
  - For each candidate (TP, SL) pair, replay every historical signal:
        if MAE ≥ SL → would have been stopped (-SL pips)   [conservative: SL first]
        elif MFE ≥ TP → would have hit TP   (+TP pips)
        else → timeout, realize as (highest_profit - lowest_drawdown) sign
  - Grid-search produces the (TP, SL) that maximizes net P/L.
  - Compare with current static config in services/target_config.py.
  - If delta is material, write a row to tp_sl_recommendations and
    optionally raise an improvement_proposal of type 'tp_sl_tweak'.

Public:
    await analyze_tp_sl(symbol, model_type, direction, timeframe, days) → dict
    await analyze_all_combinations(days) → list[dict]
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Grid search parameters (legacy — kept for callers that pass explicit grids)
DEFAULT_TP_CANDIDATES = (3, 5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 50, 75, 100)
DEFAULT_SL_CANDIDATES = (5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 50, 75, 100)
MIN_SAMPLE_SIZE = 30           # below this, recommendation is unreliable
MATERIAL_PNL_DELTA_PIPS = 50   # below this, recommendation = "no change"
MIN_TRIGGER_RATE_PCT = 40      # a combo that triggers on <40% of signals
                               # is rejected as "untradeable in practice"


def _adaptive_grid(values: list[float], current_anchors: list[float],
                    floor: float = 1.0) -> list[float]:
    """Build a data-driven candidate grid.

    Strategy:
      - 1-pip granularity in the dense zone (p25..p90 of the distribution)
      - 2-pip granularity in the tail (p90..p99)
      - Always include current static config values so the comparison shows
        them as actual grid points (otherwise the "current" point is off-grid
        and the optimizer can't honestly tell us "no change needed").
      - Cap at p99 + 20% safety margin so we don't search dead space.

    USOIL uses percentage values (e.g. 0.05 = 0.05%). For those, we drop to
    0.01% granularity automatically by detecting max < 5.
    """
    if not values:
        return list(DEFAULT_TP_CANDIDATES)
    arr = np.array(values, dtype=float)
    arr = arr[np.isfinite(arr) & (arr > 0)]
    if arr.size == 0:
        return list(DEFAULT_TP_CANDIDATES)

    p25 = float(np.percentile(arr, 25))
    p90 = float(np.percentile(arr, 90))
    p95 = float(np.percentile(arr, 95))
    p99 = float(np.percentile(arr, 99))
    # Upper bound: cap at p99 to ignore single-trade outliers that would
    # otherwise stretch the grid into useless territory (e.g. one signal
    # with 766-pip MAE bloating SL candidates up to 766).
    upper = min(float(arr.max()), p99)

    # Detect percentage-unit symbols (USOIL): tiny max → fine granularity
    if upper < 5:
        step_dense = 0.01
        step_tail = 0.02
    elif upper < 50:
        step_dense = 1.0
        step_tail = 2.0
    else:
        step_dense = 2.0
        step_tail = 5.0

    low = max(floor, round(p25 - step_dense, 4))
    cands: set[float] = set()
    # Dense zone p25..p90 at fine step
    v = low
    while v <= p90:
        cands.add(round(v, 4))
        v += step_dense
    # Tail zone p90..upper at coarser step
    v = p90
    while v <= upper:
        cands.add(round(v, 4))
        v += step_tail
    # Always anchor current static config values
    for a in current_anchors:
        if a and a > 0:
            cands.add(round(float(a), 4))

    return sorted(cands)


# ---------------------------------------------------------------------------
# Current config snapshot — read from target_config.py without coupling
# ---------------------------------------------------------------------------

def get_current_config(symbol: str, timeframe: Optional[str] = None) -> dict:
    """Pull the current static TP/SL config for the symbol.

    Returns all TP levels so the comparison can be honest: the "effective TP"
    a signal experiences depends on which level closes it, not the deepest one.
    """
    try:
        from services.target_config import get_symbol_config
        cfg = get_symbol_config(symbol)
        targets = list(cfg.targets) if cfg and cfg.targets else []
        sl_pips = float(getattr(cfg, "stoploss_pips", 0))
        all_levels = [{"name": t.name, "pips": float(t.pips)} for t in targets]
        tp1_pips = float(targets[0].pips) if targets else 0.0
        tp_deepest_pips = float(targets[-1].pips) if targets else 0.0
        return {
            # Primary comparison anchor — TP1 is where most signals actually close.
            "tp_pips": tp1_pips,
            "tp1_pips": tp1_pips,
            "tp_deepest_pips": tp_deepest_pips,
            "sl_pips": sl_pips,
            "all_tp_levels": all_levels,
            "pip_value": float(getattr(cfg, "pip_value", 1.0)),
            "is_percentage": bool(getattr(cfg, "is_percentage", False)),
        }
    except Exception as e:
        logger.warning("[tp_sl] could not read target_config for %s: %s", symbol, e)
        return {"tp_pips": 0.0, "tp1_pips": 0.0, "tp_deepest_pips": 0.0,
                "sl_pips": 0.0, "all_tp_levels": []}


# ---------------------------------------------------------------------------
# Data fetch — last N days of resolved signals + outcomes
# ---------------------------------------------------------------------------

async def _fetch_signals_with_outcomes(
    client, symbol: str, model_type: Optional[str], direction: Optional[str],
    timeframe: Optional[str], days: int,
) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        q = client.table("prediction_logs").select(
            "id,symbol,model_type,ml_direction,ml_entry_price,timeframe,status,resolution_reason,"
            "highest_profit_pips,lowest_drawdown_pips,exit_price,created_at"
        ).eq("symbol", symbol).gte("created_at", since).limit(10000)
        if model_type:
            q = q.eq("model_type", model_type)
        if direction in ("BUY", "SELL"):
            q = q.eq("ml_direction", direction)
        if timeframe:
            q = q.eq("timeframe", timeframe)
        res = q.execute() if hasattr(q, "execute") else q
        rows = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        signals = [r for r in rows if r.get("status") in ("completed", "stopped")]
    except Exception as e:
        logger.exception("[tp_sl] fetch signals failed: %s", e)
        return []
    if not signals:
        return []

    # Detect percentage-unit symbol once (USOIL stores TP/SL as % of entry).
    try:
        from services.target_config import get_symbol_config
        _scfg = get_symbol_config(symbol)
        is_pct = bool(getattr(_scfg, "is_percentage", False))
        pip_val = float(getattr(_scfg, "pip_value", 1.0)) or 1.0
    except Exception:
        is_pct = False
        pip_val = 1.0

    enriched: list[dict] = []
    for s in signals:
        # MFE/MAE are price excursions during the signal's lifetime, NOT the
        # realized P/L at exit. A "completed" signal closed at the actual TP
        # level it hit (TP1..TP4), but the bar's wick may have spiked far
        # past that — MFE can be 5× the realized P/L on a wicky candle.
        mfe = abs(float(s.get("highest_profit_pips") or 0))
        mae = abs(float(s.get("lowest_drawdown_pips") or 0))

        # Compute TRUE realized P/L from entry/exit prices. This is the only
        # honest answer for "timeout" rows in the new backtest grid — using
        # MFE there would credit profit that the trade never locked in
        # (it closed at the old, smaller TP).
        entry = float(s.get("ml_entry_price") or 0)
        exit_p = float(s.get("exit_price") or 0)
        direction = s.get("ml_direction")
        status = s.get("status")
        if entry > 0 and exit_p > 0 and direction in ("BUY", "SELL"):
            raw_diff = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
            if is_pct:
                realized = (raw_diff / entry) * 100.0  # pips = % of entry
            else:
                realized = raw_diff / pip_val
        else:
            # Fallback only if exit_price is missing — use the bounded estimate
            realized = mfe if status == "completed" else -mae

        enriched.append({
            "id": s["id"],
            "symbol": s["symbol"],
            "model_type": s.get("model_type"),
            "direction": direction,
            "timeframe": s.get("timeframe"),
            "status": status,
            "mfe_pips": mfe,
            "mae_pips": mae,
            "realized_pnl_pips": realized,
        })
    return enriched


# ---------------------------------------------------------------------------
# Core simulation: replay (TP, SL) pair against MFE/MAE distribution
# ---------------------------------------------------------------------------

def simulate_tp_sl(signals: list[dict], tp_pips: float, sl_pips: float) -> dict:
    """For each historical signal: would (tp, sl) have hit? Aggregate metrics.

    Resolution logic per signal (mfe, mae both positive magnitudes):
      - MAE >= SL  AND  MFE <  TP  → clear LOSS (only SL would've hit)
      - MFE >= TP  AND  MAE <  SL  → clear WIN  (only TP would've hit)
      - MFE >= TP  AND  MAE >= SL  → AMBIGUOUS: tie-break with historical
              `status`: completed → TP fired first → WIN;
                        stopped   → SL fired first → LOSS.
      - Neither threshold breached → TIMEOUT.

    P/L ranking uses ONLY wins (+TP) and losses (-SL). Timeouts are NOT
    credited any P/L in `net_pnl` — they're trades that never reach the
    new TP/SL targets, and the new system may not exit them at all (or
    exits via a time-based mechanism whose P/L we can't credit to this
    TP/SL pair). Counting timeouts at +MFE (old behavior) tricks the
    optimizer into recommending huge TPs that almost never trigger but
    "earn" credit from timeouts closing at the OLD smaller TP.

    `net_pnl_with_timeouts` is exposed for review only — it shows what
    happens if timeouts realize at their historical exit P/L (assumes the
    old system's exit mechanism would still kick in).
    """
    if not signals:
        return {"tp": tp_pips, "sl": sl_pips, "n": 0,
                "wins": 0, "losses": 0, "timeouts": 0, "ambiguous": 0,
                "net_pnl": 0.0, "net_pnl_with_timeouts": 0.0, "win_rate": None}
    wins = losses = timeouts = ambiguous = 0
    pnl = 0.0
    timeout_realized_total = 0.0
    for s in signals:
        mfe = s["mfe_pips"]
        mae = s["mae_pips"]
        hit_sl = sl_pips > 0 and mae >= sl_pips
        hit_tp = tp_pips > 0 and mfe >= tp_pips
        if hit_sl and hit_tp:
            ambiguous += 1
            if s.get("status") == "completed":
                wins += 1
                pnl += tp_pips
            else:
                losses += 1
                pnl -= sl_pips
        elif hit_sl:
            losses += 1
            pnl -= sl_pips
        elif hit_tp:
            wins += 1
            pnl += tp_pips
        else:
            timeouts += 1
            # Do NOT add to net_pnl — timeouts don't lock in a TP/SL outcome.
            # Track them in a side field for transparency.
            timeout_realized_total += float(s.get("realized_pnl_pips", 0.0))
    n_resolved = wins + losses
    return {
        "tp": tp_pips, "sl": sl_pips, "n": len(signals),
        "wins": wins, "losses": losses, "timeouts": timeouts,
        "ambiguous": ambiguous,
        "net_pnl": round(pnl, 2),
        "net_pnl_with_timeouts": round(pnl + timeout_realized_total, 2),
        "timeout_realized_pips": round(timeout_realized_total, 2),
        "win_rate": round(wins / n_resolved * 100, 2) if n_resolved else None,
        "trigger_rate_pct": round(n_resolved / len(signals) * 100, 2) if signals else 0,
        "avg_pnl_per_trade": round(pnl / len(signals), 3) if signals else 0,
        "rr_ratio": round(tp_pips / sl_pips, 2) if sl_pips > 0 else None,
    }


def grid_search(signals: list[dict],
                tp_candidates: list[float] = None,
                sl_candidates: list[float] = None,
                min_trigger_rate_pct: float = MIN_TRIGGER_RATE_PCT,
                mfe_stats: Optional[dict] = None,
                mae_stats: Optional[dict] = None,
                current_anchors: Optional[list[float]] = None) -> dict:
    """Try every (TP, SL) combo, return best by net_pnl + top 5 for inspection.

    Sanity bands (when distributions are passed):
      - TP must lie in [MFE p25, MFE p80] — outside this window we're either
        scalping for noise (too tight) or chasing outliers (too wide).
      - SL must lie in [MAE p25, MAE p80] — too tight = noise-stop, too wide
        = unrealistic (we'd never see it fire in production).
      - Current config anchors are always preserved so the comparison row
        stays in the search even if it lies outside the bands.

    Tradeable filter: combos that trigger on <`min_trigger_rate_pct`% of
    signals are dropped — they're not a viable system.

    Ranking ties (within 2% net_pnl of best) are broken by:
      1. higher win_rate
      2. higher trigger_rate (more trades, less luck)
      3. smaller TP (closer to the "honest" mean — wide TP is lottery)
      4. smaller SL (less downside per loss)
    """
    tp_candidates = list(tp_candidates) if tp_candidates else list(DEFAULT_TP_CANDIDATES)
    sl_candidates = list(sl_candidates) if sl_candidates else list(DEFAULT_SL_CANDIDATES)
    current_anchors = current_anchors or []

    # Sanity bands — clip to meaty distribution region, always keep anchors.
    # Note: lo can legitimately be 0 (e.g. MFE p25=0 when many signals close
    # quickly). We accept lo>=0; we only bail when stats are missing,
    # negative, or the band collapses (lo >= hi).
    def _within(cands: list[float], stats: dict, lo_key: str, hi_key: str) -> list[float]:
        lo = stats.get(lo_key) if stats else None
        hi = stats.get(hi_key) if stats else None
        if lo is None or hi is None or lo < 0 or hi <= 0 or lo >= hi:
            return cands
        kept = [c for c in cands if lo <= c <= hi]
        for a in current_anchors:
            if a and a > 0 and a not in kept and lo <= a <= hi * 1.5:
                # Only re-add anchors that aren't wildly outside the band;
                # an anchor at 3× the upper bound shouldn't drag the search.
                kept.append(a)
        return sorted(set(kept))

    tp_sane = _within(tp_candidates, mfe_stats or {}, "p25", "p80")
    sl_sane = _within(sl_candidates, mae_stats or {}, "p25", "p80")
    # Fall back to full grid if sanity bands removed everything
    if not tp_sane:
        tp_sane = tp_candidates
    if not sl_sane:
        sl_sane = sl_candidates
    tp_candidates, sl_candidates = tp_sane, sl_sane
    all_results = []
    for tp in tp_candidates:
        for sl in sl_candidates:
            all_results.append(simulate_tp_sl(signals, tp, sl))
    if not all_results:
        return {"best": None, "top5": [], "all": [], "tradeable_count": 0}

    tradeable = [r for r in all_results
                 if (r.get("trigger_rate_pct") or 0) >= min_trigger_rate_pct]

    if not tradeable:
        # No combo triggers enough — return overall best but flag it.
        all_results.sort(key=lambda r: -r["net_pnl"])
        return {"best": all_results[0], "top5": all_results[:5],
                "all": all_results, "tradeable_count": 0,
                "no_tradeable_warning": (
                    f"No (TP,SL) combo triggers on ≥{min_trigger_rate_pct}% "
                    f"of signals — model output may be too narrow for any "
                    f"reasonable TP/SL setting."
                )}

    top_pnl = max(r["net_pnl"] for r in tradeable)
    tolerance = max(1.0, abs(top_pnl) * 0.02)
    tradeable.sort(key=lambda r: (
        -r["net_pnl"] if (top_pnl - r["net_pnl"]) > tolerance else -top_pnl,
        -(r.get("win_rate") or 0),
        -(r.get("trigger_rate_pct") or 0),
        r["tp"],
        r["sl"],
    ))
    return {"best": tradeable[0], "top5": tradeable[:5],
            "all": all_results, "tradeable_count": len(tradeable)}


# ---------------------------------------------------------------------------
# Distribution stats
# ---------------------------------------------------------------------------

def distribution_stats(values: list[float]) -> dict:
    if not values:
        return {}
    arr = np.array(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean": round(float(arr.mean()), 2),
        "median": round(float(np.median(arr)), 2),
        "p10": round(float(np.percentile(arr, 10)), 2),
        "p25": round(float(np.percentile(arr, 25)), 2),
        "p50": round(float(np.percentile(arr, 50)), 2),
        "p70": round(float(np.percentile(arr, 70)), 2),
        "p80": round(float(np.percentile(arr, 80)), 2),
        "p90": round(float(np.percentile(arr, 90)), 2),
        "p95": round(float(np.percentile(arr, 95)), 2),
        "max": round(float(arr.max()), 2),
    }


# ---------------------------------------------------------------------------
# Reasoning generator — human-readable why
# ---------------------------------------------------------------------------

def _build_reasoning(symbol: str, current: dict, optimal: dict,
                      mfe_stats: dict, mae_stats: dict, n: int,
                      per_level_sim: Optional[list[dict]] = None,
                      current_sim: Optional[dict] = None,
                      pct_unit: bool = False) -> tuple[str, str]:
    """Data-grounded reasoning: every claim references an actual percentile or
    count. Avoids generic templates; mentions only the analyses that fired."""
    cur_tp1 = current.get("tp1_pips", 0)
    cur_tp_deep = current.get("tp_deepest_pips", 0)
    cur_sl = current.get("sl_pips", 0)
    rec_tp, rec_sl = optimal["tp"], optimal["sl"]
    unit = "%" if pct_unit else "pip"
    fmt = (lambda v: f"{v:.3f}{unit}") if pct_unit else (lambda v: f"{v:.1f} {unit}")

    parts: list[str] = []

    # 1) Anchor the comparison honestly — TP1 is where most signals close
    if cur_tp1 > 0:
        parts.append(
            f"Mevcut TP ladder: TP1={fmt(cur_tp1)}, TP4={fmt(cur_tp_deep)}, SL={fmt(cur_sl)}. "
            f"Karşılaştırma TP1 üzerinden — sinyallerin çoğu burada kapanır."
        )

    # 2) MFE distribution evidence
    p50_mfe = mfe_stats.get("p50")
    p70_mfe = mfe_stats.get("p70")
    p90_mfe = mfe_stats.get("p90")
    if p50_mfe is not None:
        # How many signals would have run past current TP1?
        if cur_tp1 and p70_mfe is not None and p70_mfe > cur_tp1 * 1.5:
            parts.append(
                f"📈 MFE p70={fmt(p70_mfe)}, p90={fmt(p90_mfe)} → sinyallerin en az %30'u "
                f"TP1'in {p70_mfe / max(cur_tp1, 1e-9):.1f}× üstüne gidiyor; TP1 erken kapatıyor."
            )
        elif cur_tp1 and p50_mfe < cur_tp1 * 0.7:
            parts.append(
                f"📊 MFE median={fmt(p50_mfe)} → sinyallerin yarısından fazlası TP1'e "
                f"({fmt(cur_tp1)}) ulaşmıyor; TP1 çok uzak."
            )

    # 3) MAE distribution evidence (mae_stats already in positive magnitude
    # because _fetch_signals_with_outcomes normalizes via abs())
    p70_mae = mae_stats.get("p70")
    p90_mae = mae_stats.get("p90")
    p95_mae = mae_stats.get("p95")
    if p70_mae is not None and cur_sl > 0:
        if p90_mae is not None and p90_mae < cur_sl * 0.6:
            parts.append(
                f"⚠ SL fazla geniş: MAE p90={fmt(p90_mae)} ama SL={fmt(cur_sl)} "
                f"— %90 sinyal SL'ye uzaktan yakın bile geçmiyor. Sıkı SL risk/return iyileştirir."
            )
        elif p70_mae > cur_sl:
            parts.append(
                f"⚠ SL fazla dar: MAE p70={fmt(p70_mae)} > SL={fmt(cur_sl)} "
                f"— sinyallerin en az %30'u doğal volatilite içinde stop oluyor."
            )

    # 3b) Truncation-bias warning: MFE is censored by the historical TP4 exit.
    # If we're recommending a TP beyond what the data actually observed in
    # quantity (p90), flag that the upside might be over- or under-stated.
    mfe_p95 = mfe_stats.get("p95")
    mfe_max = mfe_stats.get("max")
    if mfe_p95 is not None and rec_tp > mfe_p95 * 1.1:
        parts.append(
            f"⚠ Veri kısıtı: Önerilen TP={fmt(rec_tp)} > MFE p95={fmt(mfe_p95)}. "
            f"Tarihsel veride sinyaller eski TP4={fmt(cur_tp_deep)}'da kapandığı için "
            f"daha derin MFE gözlemlenemedi. Yeni TP'nin gerçek başarısı canlı "
            f"trackingten teyit edilmeli."
        )
    elif mae_stats.get("p95") is not None and rec_sl > mae_stats["p95"] * 1.1:
        parts.append(
            f"⚠ Veri kısıtı: Önerilen SL={fmt(rec_sl)} > MAE p95={fmt(mae_stats['p95'])}. "
            f"Daha geniş SL için 'stopped' sinyallerin gerçek devamı bilinmiyor; "
            f"backtest'in bu kısmı optimistik olabilir."
        )

    # 4) Per-TP-level efficiency (TP1..TP4)
    if per_level_sim:
        lines = []
        for lvl in per_level_sim:
            lines.append(
                f"{lvl['name']}({fmt(lvl['tp_pips'])}): "
                f"win={lvl['win_rate']}%, net={lvl['net_pnl']:+.1f}"
            )
        parts.append("Per-TP simulasyonu: " + " | ".join(lines))

    # 5) Recommendation framing
    rec_str = (f"Önerilen: TP={fmt(rec_tp)}, SL={fmt(rec_sl)} → "
               f"{optimal.get('wins',0)}W/{optimal.get('losses',0)}L/"
               f"{optimal.get('timeouts',0)}T, "
               f"net {optimal.get('net_pnl',0):+.1f} {unit}, "
               f"WR {optimal.get('win_rate', '—')}%")
    amb = optimal.get("ambiguous", 0)
    if amb > 0:
        amb_pct = amb / n * 100 if n else 0
        rec_str += (f" (ambiguous={amb}, %{amb_pct:.1f} — TP+SL aynı barda "
                    f"vurabilirdi; tarihsel `status` ile çözüldü)")
    if current_sim:
        delta_pnl = optimal["net_pnl"] - current_sim["net_pnl"]
        delta_wr = (optimal.get("win_rate") or 0) - (current_sim.get("win_rate") or 0)
        rec_str += (f". Mevcut TP1 ile karşılaştırma: net P/L "
                    f"{delta_pnl:+.1f} {unit}, win-rate {delta_wr:+.1f}pp.")
    parts.append(rec_str)

    parts.append(f"Sample: {n} resolved signal (grid {len(optimal.get('_grid_dim', '?'))})")

    return " ".join(parts), "low"


def _classify_severity(pnl_delta: float, sample_size: int) -> str:
    if sample_size < MIN_SAMPLE_SIZE:
        return "none"
    if pnl_delta < MATERIAL_PNL_DELTA_PIPS:
        return "none"
    if pnl_delta >= 500:
        return "critical"
    if pnl_delta >= 200:
        return "high"
    if pnl_delta >= 100:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_tp_sl(
    symbol: str,
    model_type: Optional[str] = None,
    direction: Optional[str] = None,
    timeframe: Optional[str] = None,
    days: int = 60,
    persist: bool = True,
) -> dict:
    """Run the full TP/SL analysis for one scope. Persists if persist=True."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    signals = await _fetch_signals_with_outcomes(
        client, symbol, model_type, direction, timeframe, days)

    out: dict = {
        "symbol": symbol, "model_type": model_type, "direction": direction,
        "timeframe": timeframe, "analysis_window_days": days,
        "sample_size": len(signals),
    }
    if len(signals) < MIN_SAMPLE_SIZE:
        out["status"] = "insufficient_data"
        out["reason"] = f"only {len(signals)} resolved signals (need ≥{MIN_SAMPLE_SIZE})"
        return out

    # MFE/MAE are already normalized to positive magnitude in
    # _fetch_signals_with_outcomes.
    mfe_values = [s["mfe_pips"] for s in signals]
    mae_values = [s["mae_pips"] for s in signals]
    mfe_stats = distribution_stats(mfe_values)
    mae_stats = distribution_stats(mae_values)

    current_cfg = get_current_config(symbol, timeframe)
    out["current"] = current_cfg
    pct_unit = bool(current_cfg.get("is_percentage"))

    # Adaptive, data-driven grid — 1-pip granularity in p25..p90 hot zone.
    tp_anchors = [lvl["pips"] for lvl in current_cfg.get("all_tp_levels", [])]
    sl_anchors = [current_cfg.get("sl_pips")] if current_cfg.get("sl_pips") else []
    tp_grid = _adaptive_grid(mfe_values, tp_anchors)
    sl_grid = _adaptive_grid(mae_values, sl_anchors)

    # Execution-friction floors — drop unrealistically tight candidates.
    # Why: signal_lifecycle samples MFE/MAE every 3-15 min, so historical
    # MAE values are a LOWER BOUND on intra-bar drawdown. An SL below the
    # symbol's typical spread+slippage+noise floor is backtest-optimal but
    # unfilled in live execution. Same idea for TP < min_tp.
    try:
        from services.target_config import get_symbol_config as _gsc
        _base = _gsc(symbol)
        noise_floor = float(getattr(_base, "noise_floor_pips", 0) or 0)
        min_tp = float(getattr(_base, "min_tp_pips", 0) or 0)
    except Exception:
        noise_floor = 0
        min_tp = 0
    if noise_floor > 0:
        sl_grid = [s for s in sl_grid if s >= noise_floor]
        if not sl_grid:
            sl_grid = [noise_floor]
    if min_tp > 0:
        tp_grid = [t for t in tp_grid if t >= min_tp]
        if not tp_grid:
            tp_grid = [min_tp]

    grid = grid_search(
        signals,
        tp_candidates=tp_grid,
        sl_candidates=sl_grid,
        mfe_stats=mfe_stats,
        mae_stats=mae_stats,
        current_anchors=tp_anchors + sl_anchors,
    )
    best = grid["best"]
    if best is None:
        out["status"] = "error"
        out["reason"] = "grid_search returned no results"
        return out
    best["_grid_dim"] = f"{len(tp_grid)}×{len(sl_grid)}"
    if grid.get("no_tradeable_warning"):
        out["warning"] = grid["no_tradeable_warning"]
    if noise_floor > 0:
        out["execution_floor"] = {
            "noise_floor_pips": noise_floor,
            "min_tp_pips": min_tp,
            "note": (
                f"SL candidates clamped to ≥{noise_floor} pip (spread + intra-bar "
                f"noise). Historical MAE p25=0 is a lower bound — real execution "
                f"sees more drawdown than tick-sampled MFE/MAE captures."
            ),
        }

    out["mfe_distribution"] = mfe_stats
    out["mae_distribution"] = mae_stats
    out["grid_dim"] = {"tp_candidates": len(tp_grid), "sl_candidates": len(sl_grid),
                       "tp_range": [tp_grid[0], tp_grid[-1]] if tp_grid else None,
                       "sl_range": [sl_grid[0], sl_grid[-1]] if sl_grid else None}
    out["recommended"] = {
        "tp_pips": best["tp"], "sl_pips": best["sl"],
        "net_pnl_pips": best["net_pnl"], "win_rate": best["win_rate"],
        "rr_ratio": best.get("rr_ratio"),
    }
    out["grid_top5"] = grid["top5"]

    # Per-TP-level simulation: how does each existing TP level perform
    # against the current SL? This is the honest answer to "should we move TP".
    per_level_sim: list[dict] = []
    if current_cfg.get("sl_pips") and current_cfg.get("all_tp_levels"):
        for lvl in current_cfg["all_tp_levels"]:
            sim = simulate_tp_sl(signals, lvl["pips"], current_cfg["sl_pips"])
            per_level_sim.append({
                "name": lvl["name"], "tp_pips": lvl["pips"], "sl_pips": current_cfg["sl_pips"],
                "net_pnl": sim["net_pnl"], "win_rate": sim["win_rate"],
                "wins": sim["wins"], "losses": sim["losses"], "timeouts": sim["timeouts"],
                "ambiguous": sim.get("ambiguous", 0),
            })
    out["per_tp_level_simulated"] = per_level_sim

    # Honest "current" baseline = TP1+SL (where most signals actually close).
    if current_cfg.get("tp_pips") and current_cfg.get("sl_pips"):
        current_sim = simulate_tp_sl(signals, current_cfg["tp_pips"], current_cfg["sl_pips"])
        out["current_simulated"] = current_sim
        pnl_delta = best["net_pnl"] - current_sim["net_pnl"]
        winrate_delta = ((best.get("win_rate") or 0) - (current_sim.get("win_rate") or 0))
        out["delta"] = {
            "net_pnl_pips": round(pnl_delta, 2),
            "winrate_pp": round(winrate_delta, 2),
            "tp_change": round(best["tp"] - current_cfg["tp_pips"], 2),
            "sl_change": round(best["sl"] - current_cfg["sl_pips"], 2),
        }
        out["severity"] = _classify_severity(pnl_delta, len(signals))
        reasoning, _ = _build_reasoning(symbol, current_cfg, best, mfe_stats, mae_stats,
                                          len(signals), per_level_sim=per_level_sim,
                                          current_sim=current_sim, pct_unit=pct_unit)
        out["reasoning"] = reasoning
    else:
        out["delta"] = None
        out["severity"] = "none"
        out["reasoning"] = "current config unavailable for comparison"

    out["status"] = "ok"

    if persist:
        try:
            # Supersede prior pending rows for the same scope so the dashboard
            # doesn't pile up duplicates as we keep re-running the analysis.
            # Custom Supabase wrapper auto-executes .update() — don't chain
            # .execute() on the dict it returns.
            try:
                supersede_q = client.table("tp_sl_recommendations").eq(
                    "symbol", symbol).eq("status", "pending")
                if direction:
                    supersede_q = supersede_q.eq("direction", direction)
                if model_type:
                    supersede_q = supersede_q.eq("model_type", model_type)
                else:
                    supersede_q = supersede_q.is_("model_type", "null")
                if timeframe:
                    supersede_q = supersede_q.eq("timeframe", timeframe)
                else:
                    supersede_q = supersede_q.is_("timeframe", "null")
                sup_res = supersede_q.update({"status": "superseded"})
                if isinstance(sup_res, dict) and sup_res.get("error"):
                    logger.warning("[tp_sl] supersede returned error: %s",
                                   sup_res.get("error"))
            except Exception as sup_err:
                logger.warning("[tp_sl] supersede failed (non-fatal): %s", sup_err)

            row = {
                "symbol": symbol,
                "model_type": model_type,
                "direction": direction,
                "timeframe": timeframe,
                "sample_size": len(signals),
                "analysis_window_days": days,
                "current_tp_pips": current_cfg.get("tp_pips"),
                "current_sl_pips": current_cfg.get("sl_pips"),
                "current_net_pnl_pips": (out.get("current_simulated") or {}).get("net_pnl"),
                "current_win_rate": (out.get("current_simulated") or {}).get("win_rate"),
                "recommended_tp_pips": best["tp"],
                "recommended_sl_pips": best["sl"],
                "recommended_net_pnl_pips": best["net_pnl"],
                "recommended_win_rate": best["win_rate"],
                "expected_pnl_delta_pips": (out.get("delta") or {}).get("net_pnl_pips"),
                "expected_winrate_delta_pp": (out.get("delta") or {}).get("winrate_pp"),
                "mfe_distribution": mfe_stats,
                "mae_distribution": mae_stats,
                "grid_top5": grid["top5"],
                "per_tp_level_simulated": per_level_sim,
                "grid_dim": out.get("grid_dim"),
                "severity": out.get("severity"),
                "reasoning": out.get("reasoning"),
                "status": "pending",
            }
            # insert auto-executes in this wrapper (returns dict)
            client.table("tp_sl_recommendations").insert(row)
        except Exception as e:
            logger.warning("[tp_sl] persist failed: %s", e)
            out["persist_error"] = str(e)[:200]

    return out


SUPPORTED_SYMBOLS = ("XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX")


async def analyze_all_combinations(days: int = 60,
                                    per_direction: bool = True) -> list[dict]:
    """Run analysis for every (symbol, direction). Returns list of recommendations."""
    results: list[dict] = []
    for symbol in SUPPORTED_SYMBOLS:
        if per_direction:
            for direction in ("BUY", "SELL"):
                try:
                    r = await analyze_tp_sl(symbol, direction=direction, days=days)
                    results.append(r)
                except Exception as e:
                    logger.exception("[tp_sl] %s/%s failed: %s", symbol, direction, e)
        else:
            try:
                r = await analyze_tp_sl(symbol, days=days)
                results.append(r)
            except Exception as e:
                logger.exception("[tp_sl] %s failed: %s", symbol, e)
    return results


# ---------------------------------------------------------------------------
# Cron loop — runs alongside the AI-Ops orchestrator
# ---------------------------------------------------------------------------

async def daily_loop() -> None:
    """Lifespan task — runs once per 24h after a 30-min initial delay."""
    import asyncio
    await asyncio.sleep(1800)
    while True:
        try:
            results = await analyze_all_combinations(days=60)
            ok = sum(1 for r in results if r.get("status") == "ok")
            insufficient = sum(1 for r in results if r.get("status") == "insufficient_data")
            material = sum(1 for r in results if r.get("severity") in ("medium", "high", "critical"))
            logger.info("[tp_sl] daily cycle: %d analyses, %d ok, %d insufficient, %d material",
                        len(results), ok, insufficient, material)
        except Exception as e:
            logger.exception("[tp_sl] daily cycle failed: %s", e)
        await asyncio.sleep(86400)
