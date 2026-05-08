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

# Grid search parameters
DEFAULT_TP_CANDIDATES = (3, 5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 50, 75, 100)
DEFAULT_SL_CANDIDATES = (5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 50, 75, 100)
MIN_SAMPLE_SIZE = 30           # below this, recommendation is unreliable
MATERIAL_PNL_DELTA_PIPS = 50   # below this, recommendation = "no change"


# ---------------------------------------------------------------------------
# Current config snapshot — read from target_config.py without coupling
# ---------------------------------------------------------------------------

def get_current_config(symbol: str, timeframe: Optional[str] = None) -> dict:
    """Pull the current static TP/SL config for the symbol."""
    try:
        from services.target_config import get_symbol_config, calculate_target_prices
        cfg = get_symbol_config(symbol)
        # Targets are a list of TargetLevel(name, pips); use TP4 (deepest) as the
        # representative TP for "fully ridden" signals
        targets = list(cfg.targets) if cfg and cfg.targets else []
        tp_pips = float(targets[-1].pips) if targets else 0.0
        sl_pips = float(getattr(cfg, "stoploss_pips", 0))
        # Also surface TP1 since that's where most signals close
        tp1_pips = float(targets[0].pips) if targets else 0.0
        return {
            "tp_pips": tp_pips,
            "tp1_pips": tp1_pips,
            "sl_pips": sl_pips,
            "all_tp_levels": [{"name": t.name, "pips": float(t.pips)} for t in targets],
            "pip_value": float(getattr(cfg, "pip_value", 1.0)),
        }
    except Exception as e:
        logger.warning("[tp_sl] could not read target_config for %s: %s", symbol, e)
        return {"tp_pips": 0.0, "tp1_pips": 0.0, "sl_pips": 0.0, "all_tp_levels": []}


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
            "id,symbol,model_type,ml_direction,ml_entry_price,timeframe,status,resolution_reason,created_at"
        ).eq("symbol", symbol).gte("created_at", since).in_(
            "status", ["completed", "stopped"]
        ).limit(10000)
        if model_type:
            q = q.eq("model_type", model_type)
        if direction in ("BUY", "SELL"):
            q = q.eq("ml_direction", direction)
        if timeframe:
            q = q.eq("timeframe", timeframe)
        res = q.execute() if hasattr(q, "execute") else q
        signals = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
    except Exception as e:
        logger.exception("[tp_sl] fetch signals failed: %s", e)
        return []
    if not signals:
        return []

    pred_ids = [s["id"] for s in signals]
    outcomes: dict[str, dict] = {}
    try:
        for i in range(0, len(pred_ids), 200):
            chunk = pred_ids[i:i + 200]
            r = client.table("outcome_results").select(
                "prediction_id,highest_profit_pips,lowest_drawdown_pips,exit_price"
            ).in_("prediction_id", chunk)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
            for o in data:
                outcomes[o["prediction_id"]] = o
    except Exception as e:
        logger.warning("[tp_sl] outcome fetch failed: %s", e)

    enriched: list[dict] = []
    for s in signals:
        o = outcomes.get(s["id"])
        if not o:
            continue
        mfe = float(o.get("highest_profit_pips") or 0)
        mae = float(o.get("lowest_drawdown_pips") or 0)
        # Realized P/L for timeout cases — sign by status
        realized = mfe if s.get("status") == "completed" else -mae
        enriched.append({
            "id": s["id"],
            "symbol": s["symbol"],
            "model_type": s.get("model_type"),
            "direction": s.get("ml_direction"),
            "timeframe": s.get("timeframe"),
            "status": s.get("status"),
            "mfe_pips": mfe,
            "mae_pips": mae,
            "realized_pnl_pips": realized,
        })
    return enriched


# ---------------------------------------------------------------------------
# Core simulation: replay (TP, SL) pair against MFE/MAE distribution
# ---------------------------------------------------------------------------

def simulate_tp_sl(signals: list[dict], tp_pips: float, sl_pips: float) -> dict:
    """For each historical signal: would (tp, sl) have hit? Return aggregated metrics.

    Conservative ordering assumption: if BOTH would have hit (MAE>=SL AND MFE>=TP),
    we assume SL fired first. This is safer than the optimistic counterpart and
    aligns with how most retail trades resolve when the candle's wick spikes
    against you before extending in your favor.
    """
    if not signals:
        return {"tp": tp_pips, "sl": sl_pips, "n": 0,
                "wins": 0, "losses": 0, "timeouts": 0,
                "net_pnl": 0.0, "win_rate": None}
    wins = losses = timeouts = 0
    pnl = 0.0
    for s in signals:
        mfe = s["mfe_pips"]
        mae = s["mae_pips"]
        if mae >= sl_pips and sl_pips > 0:
            losses += 1
            pnl -= sl_pips
        elif mfe >= tp_pips and tp_pips > 0:
            wins += 1
            pnl += tp_pips
        else:
            timeouts += 1
            pnl += s.get("realized_pnl_pips", 0.0)
    n_resolved = wins + losses
    return {
        "tp": tp_pips, "sl": sl_pips, "n": len(signals),
        "wins": wins, "losses": losses, "timeouts": timeouts,
        "net_pnl": round(pnl, 2),
        "win_rate": round(wins / n_resolved * 100, 2) if n_resolved else None,
        "avg_pnl_per_trade": round(pnl / len(signals), 3) if signals else 0,
        "rr_ratio": round(tp_pips / sl_pips, 2) if sl_pips > 0 else None,
    }


def grid_search(signals: list[dict],
                tp_candidates: list[float] = None,
                sl_candidates: list[float] = None) -> dict:
    """Try every (TP, SL) combo, return best by net_pnl + top 5 for inspection."""
    tp_candidates = tp_candidates or list(DEFAULT_TP_CANDIDATES)
    sl_candidates = sl_candidates or list(DEFAULT_SL_CANDIDATES)
    results = []
    for tp in tp_candidates:
        for sl in sl_candidates:
            results.append(simulate_tp_sl(signals, tp, sl))
    results.sort(key=lambda r: -r["net_pnl"])
    return {"best": results[0] if results else None, "top5": results[:5], "all": results}


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
                      mfe_stats: dict, mae_stats: dict, n: int) -> tuple[str, str]:
    cur_tp, cur_sl = current.get("tp_pips", 0), current.get("sl_pips", 0)
    rec_tp, rec_sl = optimal["tp"], optimal["sl"]

    parts: list[str] = []

    # SL analysis
    if cur_sl > 0:
        # What % of fails would have stopped at the recommended SL vs current?
        cur_sl_hit_pct = ((np.array([s for s in [mae_stats.get("p10"), mae_stats.get("p25"),
                                                  mae_stats.get("p50"), mae_stats.get("p70"),
                                                  mae_stats.get("p80"), mae_stats.get("p90")
                                                  ] if s is not None]) >= cur_sl).sum()
                         / 6 * 100) if mae_stats else 0
        if rec_sl > cur_sl * 1.2:
            parts.append(
                f"⚠ Mevcut SL ({cur_sl:.0f} pips) çok dar. MAE p70 = {mae_stats.get('p70')} pips "
                f"— tipik bir 'reverse-then-recover' setup'ta sinyal SL hit ediyor ama sonra MFE "
                f"genellikle {mfe_stats.get('p50')} pips'e ulaşıyor. Önerilen SL ({rec_sl:.0f}) "
                f"bu kayıpların büyük kısmını engeller."
            )
        elif rec_sl < cur_sl * 0.8:
            parts.append(
                f"⚠ Mevcut SL ({cur_sl:.0f} pips) gereksiz geniş. MAE p90 = {mae_stats.get('p90')} pips "
                f"— sinyallerin %90'ı bu kadar derine zaten gitmiyor. Daha sıkı SL ({rec_sl:.0f}) "
                f"genel risk-adjusted return'ü artırır."
            )

    # TP analysis
    if cur_tp > 0:
        if rec_tp > cur_tp * 1.3:
            parts.append(
                f"📈 Mevcut TP ({cur_tp:.0f} pips) erken kapatıyor. MFE p70 = {mfe_stats.get('p70')} pips "
                f"— sinyallerin önemli bir kısmı çok daha derin gidebiliyor ama TP nedeniyle erken kapanıyor. "
                f"Önerilen TP ({rec_tp:.0f}) parayı masada bırakmaz."
            )
        elif rec_tp < cur_tp * 0.7:
            parts.append(
                f"📊 Mevcut TP ({cur_tp:.0f} pips) çok uzak. MFE median = {mfe_stats.get('median')} pips "
                f"— çoğu sinyal o seviyeye ulaşamıyor. Daha yakın TP ({rec_tp:.0f}) win-rate'i artırır."
            )

    if not parts:
        parts.append(
            f"Mevcut konfig ({cur_tp:.0f}/{cur_sl:.0f}) optimal civarında ({rec_tp:.0f}/{rec_sl:.0f}). "
            f"Net P/L farkı {optimal['net_pnl'] - simulate_tp_sl([{'mfe_pips': mfe_stats.get('mean', 0), 'mae_pips': mae_stats.get('mean', 0), 'realized_pnl_pips': 0}], cur_tp, cur_sl)['net_pnl']:.0f} pips civarında. Değişiklik gerekmeyebilir."
        )

    parts.append(f"Sample: {n} resolved signal, MFE/MAE based grid search.")

    # Severity
    delta = optimal["net_pnl"]  # we'll compute delta against current externally
    severity = "low"
    return " ".join(parts), severity


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

    mfe_values = [s["mfe_pips"] for s in signals]
    mae_values = [s["mae_pips"] for s in signals]
    mfe_stats = distribution_stats(mfe_values)
    mae_stats = distribution_stats(mae_values)

    grid = grid_search(signals)
    best = grid["best"]
    out["mfe_distribution"] = mfe_stats
    out["mae_distribution"] = mae_stats
    out["recommended"] = {
        "tp_pips": best["tp"], "sl_pips": best["sl"],
        "net_pnl_pips": best["net_pnl"], "win_rate": best["win_rate"],
        "rr_ratio": best.get("rr_ratio"),
    }
    out["grid_top5"] = grid["top5"]

    current_cfg = get_current_config(symbol, timeframe)
    out["current"] = current_cfg
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
        severity = _classify_severity(pnl_delta, len(signals))
        out["severity"] = severity
        reasoning, _ = _build_reasoning(symbol, current_cfg, best, mfe_stats, mae_stats, len(signals))
        out["reasoning"] = reasoning
    else:
        out["delta"] = None
        out["severity"] = "none"
        out["reasoning"] = "current config unavailable for comparison"

    out["status"] = "ok"

    if persist:
        try:
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
                "severity": out.get("severity"),
                "reasoning": out.get("reasoning"),
                "status": "pending",
            }
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
