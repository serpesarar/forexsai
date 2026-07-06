"""CORTEX confluence SHADOW signals — live forward-validation (log-only).

Evaluates the two most-robust, leak-verified confluence edges at their decision
hours and logs whether they fired + (later) whether they were right. NEVER
executes a trade. Opt-in via CORTEX_SIGNAL_ENABLED.

  NDX_L_spx  (14:00 UTC): bull_score ≥ 11 AND SPX 2h-momentum > +0.245%  → long, next 1h
  NDX_S_es   (15:00 UTC): macd_hist_M30 < -0.00071 AND first_hour < -0.20%
                          AND ES 2h-momentum < -0.21%                    → short, next 1h

Data is pulled fresh from yfinance (past bars only → leak-free). Thresholds were
frozen from the 2024-25 training split (cortex_signal_thresholds.json).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_THRESH_PATH = os.path.join(os.path.dirname(__file__), "cortex_signal_thresholds.json")
_NQ, _SPX, _ES = "NQ=F", "^GSPC", "ES=F"


def _thresholds() -> dict:
    try:
        with open(_THRESH_PATH) as fh:
            return json.load(fh)
    except Exception:
        return {}


# ── compact causal indicators (past-only) ─────────────────────────────────────
def _rsi(c, n=14):
    import numpy as np
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _panel_flags(bars):
    """Return (trend_agree, mom_agree, px_agree, rsi_agree) over 1h/4h/1d of `bars`."""
    import pandas as pd
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ta = ma = pa = ra = 0
    for rule in ("1h", "4h", "1D"):
        b = bars.resample(rule, label="right", closed="right").agg(agg).dropna() if rule != "1h" else bars
        if len(b) < 50:
            continue
        c = b["Close"]
        ema20, ema50 = c.ewm(span=20).mean(), c.ewm(span=50).mean()
        macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
        mh = (macd - macd.ewm(span=9).mean()).iloc[-1]
        ta += int(ema20.iloc[-1] > ema50.iloc[-1])
        ma += int(mh > 0)
        pa += int(c.iloc[-1] > ema20.iloc[-1])
        ra += int(_rsi(c).iloc[-1] > 50)
    return ta, ma, pa, ra


def _fetch(ticker: str):
    import yfinance as yf
    d = yf.download(ticker, period="30d", interval="1h", progress=False, auto_adjust=False)
    d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
    d = d.rename(columns=str.title)
    d.index = d.index.tz_convert("UTC") if d.index.tz else d.index.tz_localize("UTC")
    return d.dropna()


def _mom_to(series_close, when, hours=2) -> Optional[float]:
    import pandas as pd
    v_now = series_close.asof(when)
    v_prev = series_close.asof(when - pd.Timedelta(hours=hours))
    if v_now and v_prev:
        return (v_now / v_prev - 1) * 100
    return None


def evaluate(rule_id: str, now_utc: Optional[datetime] = None) -> Optional[dict]:
    """Evaluate one rule at `now_utc`. Returns a signal dict (fired or not), or
    None if data unavailable. Leak-free: all inputs are bars <= now."""
    import pandas as pd
    th = _thresholds().get(rule_id)
    if not th:
        return None
    now_utc = now_utc or datetime.now(timezone.utc)
    try:
        nq = _fetch(_NQ)
    except Exception as e:
        logger.warning("[cortex-signal] NQ fetch failed: %s", e)
        return None
    ts = pd.Timestamp(now_utc).tz_convert("UTC")
    nq = nq[nq.index <= ts]
    if len(nq) < 60:
        return None
    close = nq["Close"]
    ta, ma, pa, ra = _panel_flags(nq)
    bull = ta + ma + pa + ra
    macd_series = close.ewm(span=12).mean() - close.ewm(span=26).mean()
    macd_hist = float((macd_series - macd_series.ewm(span=9).mean()).iloc[-1])
    p_now = float(close.iloc[-1])
    p_prev = close.asof(ts - pd.Timedelta(hours=1))
    first_hour = (p_now / p_prev - 1) * 100 if p_prev else None

    sig: dict[str, Any] = {
        "rule_id": rule_id, "symbol": "NDX.INDX", "side": th.get("side", ""),
        "decision_ts_utc": ts.isoformat(), "horizon": "next_1h",
        "bull_score": bull, "macd_hist": round(macd_hist, 6),
        "first_hour_pct": round(first_hour, 4) if first_hour is not None else None,
        "price_at_decision": p_now, "x_spx": None, "x_es": None,
    }
    fired = False
    if rule_id == "NDX_L_spx":
        try:
            x_spx = _mom_to(_fetch(_SPX)["Close"], ts)
        except Exception:
            x_spx = None
        sig["x_spx"] = round(x_spx, 4) if x_spx is not None else None
        sig["side"] = "long"
        fired = (bull >= th["bull_min"] and x_spx is not None and x_spx > th["x_SPX_min"])
    elif rule_id == "NDX_S_es":
        try:
            x_es = _mom_to(_fetch(_ES)["Close"], ts)
        except Exception:
            x_es = None
        sig["x_es"] = round(x_es, 4) if x_es is not None else None
        sig["side"] = "short"
        fired = (macd_hist < th["macd_max"] and first_hour is not None
                 and first_hour < th["first_hour_max"]
                 and x_es is not None and x_es < th["x_ES_max"])
    sig["fired"] = bool(fired)
    return sig


def _client():
    from database.supabase_client import get_supabase_client, is_db_available
    return get_supabase_client() if is_db_available() else None


def record(sig: dict) -> bool:
    client = _client()
    if client is None or sig is None:
        return False
    try:
        res = client.table("cortex_confluence_signals").insert(sig)
        return not res.get("error")
    except Exception as e:
        logger.warning("[cortex-signal] record error: %s", e)
        return False


def evaluate_and_record(now_utc: Optional[datetime] = None) -> list[dict]:
    """Evaluate whichever rule matches the current decision hour; record it."""
    now_utc = now_utc or datetime.now(timezone.utc)
    hour = now_utc.hour
    out = []
    for rule_id, dh in (("NDX_L_spx", 14), ("NDX_S_es", 15)):
        if hour == dh:
            sig = evaluate(rule_id, now_utc)
            if sig:
                record(sig)
                out.append(sig)
                logger.info("[cortex-signal] %s fired=%s bull=%s",
                            rule_id, sig["fired"], sig.get("bull_score"))
    return out


_done: set[tuple[str, str]] = set()   # (utc_date, rule_id) — evaluated today


async def tick(now_utc: Optional[datetime] = None) -> Optional[list[dict]]:
    """Called each ~60s from the main loop. Fires each rule once per day, in the
    first ~3 min of its decision hour. Opt-in + fully fail-open."""
    try:
        from config import settings
        if not getattr(settings, "cortex_signal_enabled", False):
            return None
    except Exception:
        return None
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.minute >= 4:
        return None
    d = now_utc.date().isoformat()
    for k in [k for k in _done if k[0] != d]:
        _done.discard(k)
    out = []
    for rule_id, dh in (("NDX_L_spx", 14), ("NDX_S_es", 15)):
        if now_utc.hour == dh and (d, rule_id) not in _done:
            try:
                sig = evaluate(rule_id, now_utc)
                if sig:
                    record(sig)
                    _done.add((d, rule_id))
                    out.append(sig)
            except Exception as e:
                logger.warning("[cortex-signal] tick %s error: %s", rule_id, e)
    return out or None
