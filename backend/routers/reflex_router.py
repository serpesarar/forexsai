"""Reflex Engine API — live signals + performance for the panel and MT5 bot.

Endpoints (all read-only, no auth — same as other learning/panel GETs):
  GET /api/reflex/live?symbol=NDX.INDX          → active signals (bot polls this)
  GET /api/reflex/signals?symbol=&days=7&limit=  → recent signals with outcomes
  GET /api/reflex/performance?symbol=&days=30    → WR / EV / profit factor / DD
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from database.supabase_client import get_supabase_client, is_db_available

logger = logging.getLogger("reflex_router")
router = APIRouter(prefix="/api/reflex", tags=["reflex"])

DEFAULT_SYMBOL = "NDX.INDX"


def _rows(query_result) -> list:
    if query_result is None:
        return []
    if isinstance(query_result, dict):
        return query_result.get("data", []) or []
    return getattr(query_result, "data", []) or []


@router.get("/live")
async def reflex_live(symbol: str = Query(DEFAULT_SYMBOL)):
    """Active (unresolved) signals — the MT5 bot polls this to open/close trades."""
    if not is_db_available():
        return {"symbol": symbol, "active": [], "db": False}
    client = get_supabase_client()
    res = (client.table("reflex_signals").select("*")
           .eq("symbol", symbol).eq("status", "active")
           .order("event_time", desc=True).limit(20).execute())
    return {"symbol": symbol, "active": _rows(res)}


@router.get("/signals")
async def reflex_signals(symbol: str = Query(DEFAULT_SYMBOL),
                         days: int = Query(7, ge=1, le=90),
                         limit: int = Query(50, ge=1, le=500)):
    """Recent signals (active + resolved) for the panel table."""
    if not is_db_available():
        return {"symbol": symbol, "signals": [], "db": False}
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    client = get_supabase_client()
    res = (client.table("reflex_signals").select("*")
           .eq("symbol", symbol).gte("event_time", since)
           .order("event_time", desc=True).limit(limit).execute())
    return {"symbol": symbol, "days": days, "signals": _rows(res)}


@router.get("/performance")
async def reflex_performance(symbol: str = Query(DEFAULT_SYMBOL),
                             days: int = Query(30, ge=1, le=365)):
    """Honest performance summary over resolved signals."""
    empty = {"symbol": symbol, "days": days, "n": 0, "active": 0, "win_rate": None,
             "ev_r": None, "profit_factor": None, "avg_win": None, "avg_loss": None,
             "total_r": 0.0, "max_drawdown_r": 0.0, "by_regime": {}}
    if not is_db_available():
        return {**empty, "db": False}
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    client = get_supabase_client()
    res = (client.table("reflex_signals").select("*")
           .eq("symbol", symbol).gte("event_time", since)
           .order("event_time", desc=False).limit(2000).execute())
    rows = _rows(res)
    active = [r for r in rows if r.get("status") == "active"]
    resolved = [r for r in rows if r.get("status", "").startswith("closed")
                and r.get("r_multiple") is not None]
    if not resolved:
        return {**empty, "active": len(active)}

    rs = [float(r["r_multiple"]) for r in resolved]
    wins = [x for x in rs if x > 0]
    losses = [x for x in rs if x <= 0]
    equity, peak, dd = 0.0, 0.0, 0.0
    for x in rs:
        equity += x
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    by_regime: dict = {}
    for r in resolved:
        reg = r.get("regime") or "?"
        by_regime.setdefault(reg, []).append(float(r["r_multiple"]))
    by_regime_stats = {
        k: {"n": len(v), "win_rate": round(sum(1 for x in v if x > 0) / len(v), 3),
            "ev_r": round(sum(v) / len(v), 4)}
        for k, v in by_regime.items()
    }
    return {
        "symbol": symbol, "days": days, "n": len(resolved), "active": len(active),
        "win_rate": round(len(wins) / len(resolved), 4),
        "ev_r": round(sum(rs) / len(rs), 4),
        "profit_factor": round(gross_win / gross_loss, 3) if gross_loss > 0 else None,
        "avg_win": round(sum(wins) / len(wins), 3) if wins else None,
        "avg_loss": round(sum(losses) / len(losses), 3) if losses else None,
        "total_r": round(sum(rs), 3),
        "max_drawdown_r": round(dd, 2),
        "by_regime": by_regime_stats,
    }
