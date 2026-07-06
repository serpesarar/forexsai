"""Step 2 simple strategies for XAUUSD 5-pip scalping. Leak-free.

Higher-TF (5m/15m) levels are built only from FULLY-CLOSED higher-TF bars
strictly before the 1m decision bar's timestamp (searchsorted, side='right'
on close-timestamps <= decision time, then the level uses bars up to that).
"""
import numpy as np
import engine as E


def resample(t, o, h, l, c, v, period_sec):
    """Resample 1m to higher TF. A higher-TF bar's 'close_t' = end of its period.
    Returns arrays aligned by bucket, with close_t = bucket_start + period_sec."""
    bucket = (t // period_sec) * period_sec
    # group contiguous identical buckets
    out_t, out_o, out_h, out_l, out_c = [], [], [], [], []
    i = 0
    n = len(t)
    while i < n:
        j = i
        b = bucket[i]
        hi, lo = h[i], l[i]
        op = o[i]
        while j < n and bucket[j] == b:
            hi = max(hi, h[j]); lo = min(lo, l[j])
            j += 1
        cl = c[j-1]
        out_t.append(b + period_sec)   # close timestamp = period end
        out_o.append(op); out_h.append(hi); out_l.append(lo); out_c.append(cl)
        i = j
    return (np.array(out_t), np.array(out_o), np.array(out_h),
            np.array(out_l), np.array(out_c))


def build_levels(htf, window):
    """For each higher-TF bar index, rolling support(min low)/resistance(max high)
    over the prior `window` CLOSED bars (excluding current)."""
    _, _, hh, ll, _ = htf
    n = len(hh)
    res = np.full(n, np.nan)
    sup = np.full(n, np.nan)
    for i in range(n):
        s = max(0, i - window)
        if i - s >= 3:
            res[i] = hh[s:i].max()
            sup[i] = ll[s:i].min()
    return sup, res


def htf_level_at(htf_close_t, sup, res, dec_t):
    """Most recent closed higher-TF level at/before decision time dec_t."""
    idx = np.searchsorted(htf_close_t, dec_t, side="right") - 1
    if idx < 0:
        return np.nan, np.nan
    return sup[idx], res[idx]


# ---------------- Strategy 1: S/R bounce (5m + 15m) ----------------
def strat_sr_bounce(t, o, h, l, c, v, idx_range, tol=2.0, win5=20, win15=12,
                    require_both=False, session_filter=None):
    htf5 = resample(t, o, h, l, c, v, 300)
    htf15 = resample(t, o, h, l, c, v, 900)
    sup5, res5 = build_levels(htf5, win5)
    sup15, res15 = build_levels(htf15, win15)
    signals = []  # (decision_idx, direction)
    for i in idx_range:
        dt = t[i]
        if session_filter and E.session_of(dt) not in session_filter:
            continue
        s5, r5 = htf_level_at(htf5[0], sup5, res5, dt)
        s15, r15 = htf_level_at(htf15[0], sup15, res15, dt)
        if np.isnan(s5) or np.isnan(s15):
            continue
        lo, hi, cl, op = l[i], h[i], c[i], o[i]
        # BUY: touched support and closed back above (bounce)
        near_sup5 = lo <= s5 + tol and cl > s5
        near_sup15 = lo <= s15 + tol and cl > s15
        near_res5 = hi >= r5 - tol and cl < r5
        near_res15 = hi >= r15 - tol and cl < r15
        buy = (near_sup5 and near_sup15) if require_both else (near_sup5 or near_sup15)
        sell = (near_res5 and near_res15) if require_both else (near_res5 or near_res15)
        # also require bullish/bearish bar to confirm momentum of bounce
        if buy and not sell and cl > op:
            signals.append((i, "BUY"))
        elif sell and not buy and cl < op:
            signals.append((i, "SELL"))
    return signals


# ---------------- Strategy 2: Trend channel (5m) ----------------
def strat_channel(t, o, h, l, c, v, idx_range, win5=20, tol=2.0, session_filter=None):
    """Linear regression channel on last win5 closed 5m closes.
    Buy near lower band, sell near upper band (mean reversion within channel)."""
    htf5 = resample(t, o, h, l, c, v, 300)
    ct, _, hh, ll, cc = htf5
    n5 = len(cc)
    slope = np.full(n5, np.nan); mid = np.full(n5, np.nan); width = np.full(n5, np.nan)
    for i in range(win5, n5):
        y = cc[i-win5:i]
        x = np.arange(win5)
        a, b = np.polyfit(x, y, 1)        # slope a, intercept b
        fit = a * x + b
        resid = y - fit
        sd = resid.std()
        slope[i] = a
        mid[i] = a * win5 + b             # projected next value
        width[i] = sd
    signals = []
    for i in idx_range:
        dt = t[i]
        if session_filter and E.session_of(dt) not in session_filter:
            continue
        j = np.searchsorted(ct, dt, side="right") - 1
        if j < win5 or np.isnan(mid[j]) or width[j] < 1e-9:
            continue
        m, w, sl = mid[j], width[j], slope[j]
        lower = m - 1.5 * w
        upper = m + 1.5 * w
        lo, hi, cl, op = l[i], h[i], c[i], o[i]
        # mean reversion: buy at lower band, sell at upper band
        if lo <= lower + tol and cl > lower and cl > op:
            signals.append((i, "BUY"))
        elif hi >= upper - tol and cl < upper and cl < op:
            signals.append((i, "SELL"))
    return signals


def run(signals, t, o, h, l, c, label, spread=0.0):
    trades = []
    n = len(o)
    for (i, d) in signals:
        if i + 1 >= n:
            continue
        out, hold = E.simulate_trade(o, h, l, c, t, i + 1, d, spread=spread)
        if out:
            trades.append((out, hold, t[i + 1]))
    return E.report(trades, label)


# ---------------- Strategy 3: Momentum breakout (continuation) ----------------
def strat_breakout(t, o, h, l, c, v, idx_range, win5=20, tol=1.0, session_filter=None):
    """Break ABOVE resistance -> BUY (continuation); break BELOW support -> SELL."""
    htf5 = resample(t, o, h, l, c, v, 300)
    sup5, res5 = build_levels(htf5, win5)
    signals = []
    for i in idx_range:
        dt = t[i]
        if session_filter and E.session_of(dt) not in session_filter:
            continue
        s5, r5 = htf_level_at(htf5[0], sup5, res5, dt)
        if np.isnan(s5):
            continue
        cl, op = c[i], o[i]
        if cl > r5 + tol and cl > op:
            signals.append((i, "BUY"))
        elif cl < s5 - tol and cl < op:
            signals.append((i, "SELL"))
    return signals


# ---------------- Strategy 4: Trend-following (HTF EMA alignment) ----------------
def _ema(arr, span):
    a = 2.0 / (span + 1)
    out = np.empty_like(arr)
    out[0] = arr[0]
    for i in range(1, len(arr)):
        out[i] = a * arr[i] + (1 - a) * out[i-1]
    return out


def strat_trend(t, o, h, l, c, v, idx_range, ema_fast=20, ema_slow=50,
                mom_bars=5, session_filter=None):
    """5m EMA(fast)>EMA(slow) uptrend -> BUY on a 1m pullback-then-up;
    downtrend -> SELL. Pure continuation in the dominant trend."""
    htf5 = resample(t, o, h, l, c, v, 300)
    ct, _, _, _, cc = htf5
    ef = _ema(cc, ema_fast); es = _ema(cc, ema_slow)
    signals = []
    for i in idx_range:
        dt = t[i]
        if session_filter and E.session_of(dt) not in session_filter:
            continue
        j = np.searchsorted(ct, dt, side="right") - 1
        if j < ema_slow:
            continue
        up = ef[j] > es[j]
        dn = ef[j] < es[j]
        cl, op = c[i], o[i]
        # 1m momentum bar in trend direction
        if up and cl > op:
            signals.append((i, "BUY"))
        elif dn and cl < op:
            signals.append((i, "SELL"))
    return signals
