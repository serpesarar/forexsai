"""NDX Reflex Engine — live service (momentum-continuation + 15-minute time-stop).

This is the ONLY validated, leak-free NDX edge from the ndx_reflex_engine research
(FINAL_PEF.md / DIRECTION_STUDY.md re-validation): momentum-continuation events,
exited by a pure 15-minute time-stop, with a catastrophic 1.5×ATR stop as a backstop.
It does NOT predict direction (proven unpredictable at 5m/60m) — it harvests
short-horizon momentum drift with asymmetric payoff.

Guarantees against leakage / inflation:
  * detector uses only CLOSED 1m and 15m bars (the forming 15m bar is dropped) —
    the exact fix that removed the 70%→52% lookahead in the research.
  * ATR / stretch / regime computed strictly from bars up to the confirm bar.
  * outcomes resolved by walking real 1m bars from entry to the 15-minute deadline
    (catastrophic SL checked intrabar); never by a reported/optimistic convention.
  * SHADOW by default (REFLEX_MODE=shadow) — writes signals only, no orders. The MT5
    bot executes only when explicitly enabled there.

Env:
  REFLEX_ENABLED=1        turn the loop on (default off)
  REFLEX_MODE=shadow|live tag written on signals (default shadow)
  REFLEX_SYMBOL=NDX.INDX
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from database.supabase_client import get_supabase_client, is_db_available
from services.data_hub import get_candles, get_price

logger = logging.getLogger("reflex_engine")

SYMBOL = os.environ.get("REFLEX_SYMBOL", "NDX.INDX")
MODE = os.environ.get("REFLEX_MODE", "shadow")
ENABLED = os.environ.get("REFLEX_ENABLED", "0") == "1"

# ── frozen, validated parameters (research: mom_cont + time-stop) ──
MOM_STRETCH_ATR = 2.0          # 15m stretch trigger
SL_ATR = 1.5                   # catastrophic backstop distance (×1m ATR)
TIME_STOP_MIN = 15             # the validated exit
ATR_PERIOD = 14
REFRACTORY_MIN = 30            # no double-fire per direction
EVENT_WINDOW_UTC = (13, 20)    # NY session only
_last_event: dict[str, datetime] = {}   # direction -> last fire time


# ── helpers ───────────────────────────────────────────────────────────────

def _bars_df(limit: int = 600) -> pd.DataFrame | None:
    raw = get_candles(SYMBOL, "1m", limit=limit)
    if not raw or len(raw) < 60:
        return None
    df = pd.DataFrame(raw)
    if "timestamp" not in df or "close" not in df:
        return None
    df["ts"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close"])


def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _adx(df: pd.DataFrame, period: int = 14) -> float:
    h, l, c = df["high"], df["low"], df["close"]
    up, dn = h.diff(), -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    v = dx.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    return float(v) if np.isfinite(v) else 20.0


def _regime(df: pd.DataFrame) -> str:
    adx = _adx(df)
    atr = _atr(df)
    pctl = atr.rolling(1200, min_periods=200).rank(pct=True).iloc[-1]
    pctl = float(pctl) if np.isfinite(pctl) else 0.5
    if pctl >= 0.80:
        return "EXPANSION"
    if pctl <= 0.25 and adx < 20:
        return "CONTRACTION"
    if adx >= 25:
        return "TREND"
    return "CHOP"


def detect_event(df: pd.DataFrame) -> dict | None:
    """Return the most-recent mom_cont event on CLOSED bars, or None.

    Leak-free: the forming 1m bar (last row, possibly incomplete) and the forming 15m
    bar are excluded. 15m stretch uses only fully closed 15m bars.
    """
    if df is None or len(df) < 120:
        return None
    # drop the last row (may be the still-forming 1m bar)
    d = df.iloc[:-1].copy()
    now = df["ts"].iloc[-1]
    lo, hi = EVENT_WINDOW_UTC
    if not (lo <= now.hour < hi):
        return None

    # 15m from closed 1m bars, label at close, drop the forming 15m bin
    b15 = (d.set_index("ts")
           .resample("15min", label="right", closed="right")
           .agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
           .dropna())
    # only keep 15m bars whose close time <= last closed 1m ts (fully closed)
    b15 = b15[b15.index <= d["ts"].iloc[-1]]
    if len(b15) < 25:
        return None
    ema20 = b15["close"].ewm(span=20, adjust=False).mean()
    atr15 = (b15["high"] - b15["low"]).rolling(14).mean()
    stretch = float(((b15["close"] - ema20) / atr15.replace(0, np.nan)).iloc[-1])
    if not np.isfinite(stretch) or abs(stretch) < MOM_STRETCH_ATR:
        return None
    direction = "BUY" if stretch > 0 else "SELL"

    # 1m confirm inside the current (post-last-closed-15m) block: pullback then
    # a close beyond the prior 1m extreme (mirrors research detect_mom_cont)
    last15_close = b15.index[-1]
    blk = d[d["ts"] > last15_close]
    if len(blk) < 3:
        return None
    for k in range(2, len(blk)):
        w = blk.iloc[:k]
        bar = blk.iloc[k - 1]
        if direction == "BUY" and bar["close"] > w["high"].iloc[:-1].max() and w["low"].min() < w["close"].iloc[0]:
            confirm = bar
            break
        if direction == "SELL" and bar["close"] < w["low"].iloc[:-1].min() and w["high"].max() > w["close"].iloc[0]:
            confirm = bar
            break
    else:
        return None

    atr1 = float(_atr(d).iloc[-1])
    if not np.isfinite(atr1) or atr1 <= 0:
        return None
    return {"event_time": confirm["ts"].to_pydatetime(), "direction": direction,
            "stretch": round(stretch, 3), "atr": round(atr1, 3), "regime": _regime(d)}


# ── loop tick: detect + resolve ─────────────────────────────────────────────

async def tick() -> None:
    """One reflex cycle: resolve due signals, then look for a new event."""
    if not ENABLED or not is_db_available():
        return
    try:
        _resolve_due()
    except Exception as e:  # noqa: BLE001
        logger.error(f"reflex resolve error: {e}")
    try:
        _maybe_emit()
    except Exception as e:  # noqa: BLE001
        logger.error(f"reflex emit error: {e}")


def _maybe_emit() -> None:
    df = _bars_df()
    ev = detect_event(df)
    if not ev:
        return
    now = datetime.now(timezone.utc)
    last = _last_event.get(ev["direction"])
    if last and (now - last) < timedelta(minutes=REFRACTORY_MIN):
        return
    price = get_price(SYMBOL)
    if price is None:
        return
    atr = ev["atr"]
    is_buy = ev["direction"] == "BUY"
    sl = price - SL_ATR * atr if is_buy else price + SL_ATR * atr
    deadline = now + timedelta(minutes=TIME_STOP_MIN)
    record = {
        "symbol": SYMBOL, "event_time": ev["event_time"].isoformat(),
        "entry_time": now.isoformat(), "direction": ev["direction"], "family": "mom_cont",
        "regime": ev["regime"], "entry_price": round(price, 3), "sl_price": round(sl, 3),
        "exit_deadline": deadline.isoformat(), "status": "active", "atr": atr,
        "stretch": ev["stretch"], "mode": MODE,
        "explanation": {
            "why": f"15m momentum stretch {ev['stretch']}×ATR ({ev['regime']}); "
                   f"1m pullback-resume confirm. Exit: market at +{TIME_STOP_MIN}min. "
                   f"Catastrophic SL {SL_ATR}×ATR. No direction prediction — momentum drift edge.",
            "params": {"time_stop_min": TIME_STOP_MIN, "sl_atr": SL_ATR},
        },
    }
    client = get_supabase_client()
    res = client.table("reflex_signals").insert_ignore(record)
    if res is not None:
        _last_event[ev["direction"]] = now
        logger.info(f"🟢 REFLEX {MODE} {ev['direction']} @ {price:.1f} "
                    f"stretch={ev['stretch']} regime={ev['regime']} → exit {deadline:%H:%M}")


def _resolve_due() -> None:
    client = get_supabase_client()
    now = datetime.now(timezone.utc)
    q = (client.table("reflex_signals").select("*")
         .eq("status", "active").eq("symbol", SYMBOL)
         .lte("exit_deadline", now.isoformat()).limit(50).execute())
    rows = (q or {}).get("data", []) if isinstance(q, dict) else (q.data if hasattr(q, "data") else [])
    if not rows:
        return
    df = _bars_df()
    for sig in rows:
        try:
            _resolve_one(client, sig, df)
        except Exception as e:  # noqa: BLE001
            logger.error(f"reflex resolve_one error id={sig.get('id')}: {e}")


def _resolve_one(client, sig: dict, df: pd.DataFrame | None) -> None:
    is_buy = sig["direction"] == "BUY"
    entry = float(sig["entry_price"])
    sl = float(sig["sl_price"])
    atr = float(sig.get("atr") or 0.0)
    sl_dist = SL_ATR * atr if atr > 0 else abs(entry - sl)
    entry_t = pd.to_datetime(sig["entry_time"], utc=True)
    deadline = pd.to_datetime(sig["exit_deadline"], utc=True)

    exit_price, status, reason = None, None, None
    if df is not None and len(df):
        win = df[(df["ts"] >= entry_t) & (df["ts"] <= deadline)]
        for _, bar in win.iterrows():
            hit_sl = (bar["low"] <= sl) if is_buy else (bar["high"] >= sl)
            if hit_sl:
                exit_price, status, reason = sl, "closed_loss", "catastrophic_sl"
                break
        if exit_price is None and not win.empty:
            exit_price = float(win["close"].iloc[-1]); reason = "time_stop"
    if exit_price is None:  # no bars available → fall back to current price
        exit_price = get_price(SYMBOL) or entry
        reason = "time_stop_fallback"

    pnl = (exit_price - entry) if is_buy else (entry - exit_price)
    r = pnl / sl_dist if sl_dist > 0 else 0.0
    if status is None:
        status = "closed_win" if pnl > 0 else ("closed_loss" if pnl < 0 else "closed_flat")
    upd = {"status": status, "exit_time": datetime.now(timezone.utc).isoformat(),
           "exit_price": round(exit_price, 3), "pnl_points": round(pnl, 3),
           "r_multiple": round(r, 4), "updated_at": datetime.now(timezone.utc).isoformat()}
    client.table("reflex_signals").eq("id", sig["id"]).update(upd).execute()
    logger.info(f"♻️ REFLEX resolve id={sig['id']} {sig['direction']} {status} "
                f"r={r:+.2f} ({reason})")
