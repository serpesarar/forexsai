"""Leak-free 1m backtest engine for XAUUSD 5-pip scalping.

Conventions (production-consistent):
  - 1 pip = $1.00 for XAUUSD  => TP = +$5.00, SL = -$5.00
  - Entry at the OPEN of the bar AFTER the decision bar (no same-bar lookahead).
  - TP/SL resolved on 1m bars. In-bar ambiguity (bar touches both TP and SL):
    resolved pessimistically as a LOSS (SL-first). This is the honest lower bound.
  - Trades never evaluate across a session gap: if the next bar is >GAP_MIN
    minutes away, the trade is force-closed at the last close (counted by sign).
  - Max holding horizon capped at MAX_HOLD bars; unresolved -> 'timeout'.
"""
import json
from datetime import datetime, timezone
import numpy as np

PATH = "/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_xauusd_1m_bars.json"
PIP = 1.0
TP_PIPS = 5.0
SL_PIPS = 5.0
TP_D = TP_PIPS * PIP   # $5
SL_D = SL_PIPS * PIP   # $5
MAX_HOLD = 30          # bars (minutes)
GAP_MIN = 5            # minutes; larger inter-bar gap => session boundary


def load():
    bars = json.load(open(PATH))["bars"]
    t = np.array([b["t"] for b in bars], dtype=np.int64)
    o = np.array([b["o"] for b in bars], dtype=np.float64)
    h = np.array([b["h"] for b in bars], dtype=np.float64)
    l = np.array([b["l"] for b in bars], dtype=np.float64)
    c = np.array([b["c"] for b in bars], dtype=np.float64)
    v = np.array([b["v"] for b in bars], dtype=np.float64)
    return t, o, h, l, c, v


def slices(n):
    """Return (working_start, test_split). First 60% untouched."""
    ws = int(n * 0.60)
    ts = ws + int((n - ws) * 0.70)
    return ws, ts


def simulate_trade(o, h, l, c, t, entry_idx, direction, tp_d=TP_D, sl_d=SL_D,
                   max_hold=MAX_HOLD, spread=0.0):
    """Simulate one trade entered at OPEN of bar entry_idx.

    spread: cost in $ applied against entry (entry worse by spread/2 each side
            modeled simply by widening required TP by `spread` and SL unchanged...
            here we apply: effective entry = open +/- spread (pay the spread).
    Returns outcome str: 'win','loss','timeout','gap'.
    """
    n = len(o)
    if entry_idx >= n:
        return None, 0
    entry = o[entry_idx]
    if direction == "BUY":
        entry += spread          # buy at ask (pay spread)
        tp = entry + tp_d
        sl = entry - sl_d
    else:
        entry -= spread          # sell at bid
        tp = entry - tp_d
        sl = entry + sl_d

    prev_t = t[entry_idx]
    for k in range(entry_idx, min(entry_idx + max_hold, n)):
        # session-gap guard (skip the entry bar's own prev check)
        if k > entry_idx and (t[k] - prev_t) > GAP_MIN * 60:
            # force close at previous bar's close, count by sign
            px = c[k - 1]
            pnl = (px - entry) if direction == "BUY" else (entry - px)
            return ("win" if pnl > 0 else "loss"), (k - 1 - entry_idx)
        prev_t = t[k]
        hi, lo = h[k], l[k]
        if direction == "BUY":
            hit_tp = hi >= tp
            hit_sl = lo <= sl
        else:
            hit_tp = lo <= tp
            hit_sl = hi >= sl
        if hit_tp and hit_sl:
            return "loss", (k - entry_idx)          # pessimistic tie-break
        if hit_sl:
            return "loss", (k - entry_idx)
        if hit_tp:
            return "win", (k - entry_idx)
    return "timeout", (min(entry_idx + max_hold, n) - 1 - entry_idx)


def session_of(ts):
    """UTC hour -> session label."""
    hr = datetime.fromtimestamp(int(ts), tz=timezone.utc).hour
    if 7 <= hr < 10:
        return "London"
    if 13 <= hr < 16:
        return "NY_overlap"
    if 0 <= hr < 7:
        return "Asia"
    return "Other"


def report(trades, label="", include_timeout_as_loss=False):
    """trades: list of (outcome, hold_bars, ts). Print WR + session breakdown."""
    res = [tr for tr in trades if tr[0] in ("win", "loss")]
    timeouts = [tr for tr in trades if tr[0] == "timeout"]
    if include_timeout_as_loss:
        res = res + [("loss", tr[1], tr[2]) for tr in timeouts]
    n = len(res)
    wins = sum(1 for tr in res if tr[0] == "win")
    wr = wins / n if n else 0.0
    avg_hold = np.mean([tr[1] for tr in res]) if res else 0.0
    print(f"\n=== {label} ===")
    print(f"  resolved trades : {n}  (timeouts excluded: {len(timeouts)})")
    print(f"  WIN RATE        : {wr:.1%}  ({wins}/{n})")
    print(f"  avg hold (min)  : {avg_hold:.1f}")
    # session breakdown
    for sess in ("London", "NY_overlap", "Asia", "Other"):
        sub = [tr for tr in res if session_of(tr[2]) == sess]
        if sub:
            w = sum(1 for tr in sub if tr[0] == "win")
            print(f"    {sess:<11}: {w/len(sub):.1%}  ({w}/{len(sub)})")
    return wr, n


def simulate_pnl(o, h, l, c, t, entry_idx, direction, tp_d, sl_d, max_hold, spread=0.0):
    """Return net $ PnL of one trade (pessimistic SL-first tie-break, gap-closed).
    Returns (pnl, resolved_bool, hold)."""
    n = len(o)
    if entry_idx >= n:
        return 0.0, False, 0
    entry = o[entry_idx] + (spread if direction == "BUY" else -spread)
    if direction == "BUY":
        tp = entry + tp_d; sl = entry - sl_d
    else:
        tp = entry - tp_d; sl = entry + sl_d
    prev_t = t[entry_idx]
    for k in range(entry_idx, min(entry_idx + max_hold, n)):
        if k > entry_idx and (t[k] - prev_t) > GAP_MIN * 60:
            px = c[k-1]
            pnl = (px - entry) if direction == "BUY" else (entry - px)
            return pnl, True, (k-1-entry_idx)
        prev_t = t[k]
        hi, lo = h[k], l[k]
        if direction == "BUY":
            hit_tp = hi >= tp; hit_sl = lo <= sl
        else:
            hit_tp = lo <= tp; hit_sl = hi >= sl
        if hit_sl:   # pessimistic: SL first on ambiguity
            return -sl_d, True, (k-entry_idx)
        if hit_tp:
            return tp_d, True, (k-entry_idx)
    # timeout: mark-to-market at last close
    px = c[min(entry_idx+max_hold, n)-1]
    pnl = (px - entry) if direction == "BUY" else (entry - px)
    return pnl, False, (min(entry_idx+max_hold, n)-1-entry_idx)
