"""Multi-asset leak-free 1m scalp engine + indicators + vectorized barrier sim.

Replicates the XAUUSD research engine semantics for ANY instrument:
  - Entry at OPEN of bar AFTER the decision bar (no same-bar lookahead).
  - 1m TP/SL walk, pessimistic SL-first in-bar tie-break (honest lower bound).
  - Session-gap guard: gap > GAP_MIN min => force-close at prior close, count by sign.
  - Max hold MAX_HOLD bars; unresolved => timeout (excluded from WR, marked-to-market
    for PnL).
  - Spread paid on entry (BUY at ask, SELL at bid).

Cross-asset fairness: barrier = BARRIER_PCT of instrument median price, spread =
SPREAD_FRAC of the barrier. This keeps the *geometry* identical to XAUUSD
($5 barrier on ~$5000 = 0.10%; $0.30 spread = 6% of barrier), so the comparison
isolates whether each instrument's PRICE PROCESS carries edge, independent of
absolute cost levels. Real-world spreads on indices/oil may be proportionally wider
(noted in the report).
"""
import json
import numpy as np
from datetime import datetime, timezone

DATA = {
    "XAUUSD": "/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_xauusd_1m_bars.json",
    "NDX":    "/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_ustec_1m_bars.json",
    "USOIL":  "/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_xtiusd_1m_bars.json",
    "DAX":    "/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_de40_1m_bars.json",
}
BARRIER_PCT = 0.0010    # 0.10% of price (matches XAUUSD $5/$5000)
SPREAD_FRAC = 0.06      # spread = 6% of barrier (matches $0.30/$5)
MAX_HOLD = 30
GAP_MIN = 5


def load(sym):
    bars = json.load(open(DATA[sym]))["bars"]
    t = np.array([b["t"] for b in bars], np.int64)
    o = np.array([b["o"] for b in bars], np.float64)
    h = np.array([b["h"] for b in bars], np.float64)
    l = np.array([b["l"] for b in bars], np.float64)
    c = np.array([b["c"] for b in bars], np.float64)
    v = np.array([b["v"] for b in bars], np.float64)
    return t, o, h, l, c, v


def slices(n):
    ws = int(n*0.60)
    ts = ws + int((n-ws)*0.70)
    return ws, ts


def barrier_for(c):
    return float(np.median(c) * BARRIER_PCT)


def simulate_all(o, h, l, c, t, direction, barrier, spread, max_hold=MAX_HOLD,
                 gap=GAP_MIN):
    """Vectorized over all decision bars i (entry at o[i+1]).
    Returns (outcome int8: 1 win/0 loss/-1 timeout, pnl float net $, valid bool).
    valid[i] True only where full horizon exists (i+max_hold < n)."""
    n = len(o)
    idx = np.arange(n)
    valid = idx <= (n - max_hold - 2)
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = np.empty(n); entry[:-1] = o[1:]; entry[-1] = o[-1]
    entry_eff = entry + sgn*spread
    tp = entry_eff + sgn*barrier
    sl = entry_eff - sgn*barrier
    resolved = np.zeros(n, bool)
    outcome = np.full(n, -1, np.int8)
    pnl = np.zeros(n)
    for s in range(1, max_hold+1):
        j = np.minimum(idx + s, n-1)
        if s >= 2:
            jp = np.minimum(idx + s - 1, n-1)
            gap_now = (t[j] - t[jp]) > gap*60
            ng = gap_now & ~resolved & valid
            if ng.any():
                px = c[jp]
                p = np.where(direction == "BUY", px - entry_eff, entry_eff - px)
                outcome[ng] = (p[ng] > 0).astype(np.int8)
                pnl[ng] = p[ng]
                resolved |= ng
        hi = h[j]; lo = l[j]
        if direction == "BUY":
            hit_sl = lo <= sl; hit_tp = hi >= tp
        else:
            hit_sl = hi >= sl; hit_tp = lo <= tp
        nl = hit_sl & ~resolved & valid           # pessimistic SL first
        outcome[nl] = 0; pnl[nl] = -barrier; resolved |= nl
        nw = hit_tp & ~resolved & valid
        outcome[nw] = 1; pnl[nw] = barrier; resolved |= nw
    # timeouts -> mark-to-market at i+max_hold
    unres = ~resolved & valid
    jend = np.minimum(idx + max_hold, n-1)
    px = c[jend]
    p = np.where(direction == "BUY", px - entry_eff, entry_eff - px)
    pnl[unres] = p[unres]   # outcome stays -1 (excluded from WR)
    outcome[~valid] = -1
    return outcome, pnl, valid


# ---------------- indicators (causal) ----------------
def ema(x, span):
    a = 2/(span+1)
    out = np.empty_like(x, float); out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a*x[i] + (1-a)*out[i-1]
    return out


def rsi(c, p=14):
    d = np.diff(c, prepend=c[0])
    up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    ru = ema(up, p); rd = ema(dn, p)
    rs = ru/np.where(rd == 0, 1e-9, rd)
    return 100 - 100/(1+rs)


def atr(h, l, c, p=14):
    tr = np.maximum(h-l, np.maximum(np.abs(h-np.roll(c, 1)), np.abs(l-np.roll(c, 1))))
    tr[0] = h[0]-l[0]
    return ema(tr, p)


def adx(h, l, c, p=14):
    up = np.diff(h, prepend=h[0]); dn = -np.diff(l, prepend=l[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h-l, np.maximum(np.abs(h-np.roll(c, 1)), np.abs(l-np.roll(c, 1))))
    tr[0] = h[0]-l[0]
    a = ema(tr, p)
    pdi = 100*ema(pdm, p)/np.where(a == 0, 1, a)
    mdi = 100*ema(mdm, p)/np.where(a == 0, 1, a)
    dx = 100*np.abs(pdi-mdi)/np.where((pdi+mdi) == 0, 1, pdi+mdi)
    return ema(dx, p), pdi, mdi


def session_of_hour(hr):
    if 7 <= hr < 10: return "London"
    if 13 <= hr < 16: return "NY_overlap"
    if 0 <= hr < 7: return "Asia"
    return "Other"


def time_arrays(t):
    hour = ((t % 86400)//3600).astype(int)
    dow = np.array([datetime.fromtimestamp(int(x), tz=timezone.utc).weekday() for x in t])
    sess = np.array([session_of_hour(int(hr)) for hr in hour])
    return hour, dow, sess


def boot_ci(x, iters=2000, seed=7):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    m = [rng.choice(x, len(x), replace=True).mean() for _ in range(iters)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
