"""Regime-aware filter test for XAUUSD 5/5 (1:1) scalping.

User question: the SELL 'edge' was dismissed as gold-decline drift. Can an advanced
regime-aware model DETECT when that drift is active vs. when it reverses, and time
entries — SELL only in confirmed bearish regime, BUY only in confirmed bullish,
flat in neutral/choppy?

Method:
  - Trade decision per eligible bar: BUY / SELL / FLAT. PnL from cached 5/5 outcomes
    net of $0.30 spread (buyp/sellp). All regime features are CAUSAL (backward EMAs,
    ADX, rolling returns, prev-day dir, rolling drift). DXY/yields/news NOT in the
    OHLCV-only file, so omitted (stated, not faked).
  - Working 40% slice split into 5 TIME BLOCKS = bull(1,+97) bear(2,-156) bear(3,-96)
    bull(4,+130) bear(5,-144). The decisive honesty test: does a config win in BOTH
    bull and bear blocks? Bear-only wins = drift-following, not regime skill.
  - 7 configs compared (user's list). Fitted configs (1,3,7) use EXPANDING
    walk-forward (fit blocks <k, apply to block k). Rule configs (2,4,5,6) are
    parameter-free and causal.
  - Baseline: naive 'always trade prevailing rolling-drift direction'.
Reports per-config: overall WR, mean PnL/trade, total PnL, trades, and the
bull-block vs bear-block PnL split (the drift detector).
"""
import numpy as np
import engine as E
import ml_model as M
import strategies as S
from datetime import datetime, timezone
from sklearn.ensemble import GradientBoostingClassifier

SPREAD = 0.30
NB = 5

d = np.load("outcomes_5_5_sp030.npz")
buy, sell, buyp, sellp = d["buy"], d["sell"], d["buyp"], d["sellp"]
t, o, h, l, c, v = E.load()
n = len(t)
ws, _ = E.slices(n)
work_end = n - E.MAX_HOLD - 1
edges = np.linspace(ws, work_end, NB+1).astype(int)
blocks = [(edges[i], edges[i+1]) for i in range(NB)]
BULL = {0, 3}   # block index (0-based): blocks 1 and 4 are bull
BEAR = {1, 2, 4}


def ema(x, span):
    a = 2/(span+1)
    out = np.empty_like(x, float)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a*x[i] + (1-a)*out[i-1]
    return out


def adx(h, l, c, p=14):
    up = np.diff(h, prepend=h[0]); dn = -np.diff(l, prepend=l[0])
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h-l, np.maximum(np.abs(h-np.roll(c, 1)), np.abs(l-np.roll(c, 1))))
    tr[0] = h[0]-l[0]
    atr = ema(tr, p)
    pdi = 100*ema(plus_dm, p)/np.where(atr == 0, 1, atr)
    mdi = 100*ema(minus_dm, p)/np.where(atr == 0, 1, atr)
    dx = 100*np.abs(pdi-mdi)/np.where((pdi+mdi) == 0, 1, (pdi+mdi))
    return ema(dx, p), pdi, mdi


# ---- causal regime features ----
ema20 = ema(c, 20); ema50 = ema(c, 50); ema200 = ema(c, 200)
adx14, pdi, mdi = adx(h, l, c, 14)
r60 = np.zeros(n); r60[60:] = c[60:]/c[:-60]-1        # 1h rolling return
r240 = np.zeros(n); r240[240:] = c[240:]/c[:-240]-1   # 4h rolling return
atr14 = M.atr(h, l, c, 14)
volexp = np.ones(n); volexp[120:] = atr14[120:]/np.where(atr14[:-120] == 0, 1, atr14[:-120])
# rolling directional drift: sign of cumulative return over last 120 bars (2h)
drift120 = np.sign(r60)  # proxy; sign of 1h return
hour = ((t % 86400)//3600).astype(int)

# rule-based regime: +1 bull, -1 bear, 0 neutral/choppy
regime = np.zeros(n, int)
bull_mask = (c > ema200) & (ema20 > ema50) & (r60 > 0) & (adx14 > 20)
bear_mask = (c < ema200) & (ema20 < ema50) & (r60 < 0) & (adx14 > 20)
regime[bull_mask] = 1
regime[bear_mask] = -1

# trend-following sign (no choppy gate) for drift baseline
trend_sign = np.sign(ema20 - ema50).astype(int)

base = np.zeros(n, bool); base[ws:work_end] = True

# best fixed window from part_a (Monday/London cluster). For 'time' configs use
# the London+NY session window which had most volume; keep it simple & explicit.
sess = np.array([E.session_of(x) for x in t])
time_mask = base & ((sess == "London") | (sess == "NY_overlap"))


def pnl_of(direction_arr, eligible):
    """direction_arr: per-bar +1 BUY / -1 SELL / 0 flat. Return pnl array & resolved mask
    restricted to eligible bars with a nonzero, resolved decision."""
    pnls = np.zeros(n); res = np.zeros(n, bool)
    bm = eligible & (direction_arr > 0) & (buy >= 0)
    pnls[bm] = buyp[bm]; res |= bm
    sm = eligible & (direction_arr < 0) & (sell >= 0)
    pnls[sm] = sellp[sm]; res |= sm
    # WR: win if pnl>0
    return pnls, res


def block_split(pnls, res):
    rows = []
    bull_pnl = bear_pnl = 0.0
    for i, (lo, hi) in enumerate(blocks):
        m = res.copy(); m[:lo] = False; m[hi:] = False
        nn = int(m.sum())
        tot = float(pnls[m].sum())
        wr = float((pnls[m] > 0).mean()) if nn else 0.0
        rows.append((nn, wr, tot))
        if i in BULL: bull_pnl += tot
        else: bear_pnl += tot
    return rows, bull_pnl, bear_pnl


def summarize(name, direction_arr, eligible):
    pnls, res = pnl_of(direction_arr, eligible)
    nn = int(res.sum())
    if nn == 0:
        print(f"{name:42s}  no trades"); return
    wr = float((pnls[res] > 0).mean())
    mean = float(pnls[res].mean()); tot = float(pnls[res].sum())
    rows, bull, bear = block_split(pnls, res)
    pb = " ".join(f"{r[2]:+5.0f}" for r in rows)
    flag = ""
    if bull > 0 and bear > 0: flag = "  <-- wins BULL & BEAR"
    elif bear > 0 and bull <= 0: flag = "  (bear-only = drift)"
    print(f"{name:42s} N={nn:5d} WR={wr:4.0%} mean={mean:+5.2f} tot={tot:+7.0f} | "
          f"bull{bull:+6.0f} bear{bear:+6.0f} | blk[{pb}]{flag}")


print(f"Blocks (0-based): BULL={sorted(BULL)} BEAR={sorted(BEAR)}  spread=${SPREAD}")
print("="*135)

# ---------- Config 2: direction-only pockets (naive drift baselines) ----------
allbuy = np.where(base, 1, 0)
allsell = np.where(base, -1, 0)
summarize("(2) always BUY", allbuy, base)
summarize("(2) always SELL", allsell, base)

# ---------- Baseline: always trade prevailing rolling-drift direction ----------
drift_dir = np.where(base, trend_sign, 0)
summarize("BASELINE drift-follow (ema20>50 sign)", drift_dir, base)

# ---------- Config 1: fixed time/session, fixed train-majority direction ----------
# expanding walk-forward: pick majority-winning direction on prior blocks, apply
dir1 = np.zeros(n, int)
for k in range(1, NB):
    prior = np.zeros(n, bool)
    prior[edges[0]:edges[k]] = True
    pm = prior & time_mask
    wb = float((buyp[pm & (buy >= 0)] > 0).mean()) if (pm & (buy >= 0)).any() else 0
    ws_ = float((sellp[pm & (sell >= 0)] > 0).mean()) if (pm & (sell >= 0)).any() else 0
    chosen = 1 if wb >= ws_ else -1
    seg = np.zeros(n, bool); seg[edges[k]:edges[k+1]] = True
    dir1[seg & time_mask] = chosen
summarize("(1) time/session + fixed-dir (WF)", dir1, time_mask)

# ---------- Config 3: time + direction (SELL only in London/NY) ----------
summarize("(3) time + SELL", np.where(time_mask, -1, 0), time_mask)

# ---------- Config 4: time + regime (trend-following in window) ----------
dir4 = np.where(time_mask, regime, 0)
summarize("(4) time + regime (flat if neutral)", dir4, time_mask)

# ---------- Config 5: direction + regime (regime-gated, all sessions) ----------
summarize("(5) regime-gated (SELL-bear/BUY-bull)", regime.copy(), base)

# ---------- Config 6: time + direction + regime ----------
summarize("(6) time + regime-gated", np.where(time_mask, regime, 0), time_mask)

# ---------- Config 7: ML regime classifier + rule entry ----------
# GBM trained on regime features to predict P(up) at 5/5 horizon; expanding WF.
feat = np.column_stack([
    (c-ema20)/c, (c-ema50)/c, (c-ema200)/c, ema20-ema50, adx14, pdi-mdi,
    r60, r240, volexp, drift120, np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24)])
feat = np.nan_to_num(feat)
y = buy.copy()  # 1 if BUY wins (=P up proxy)
dir7 = np.zeros(n, int)
MARGIN = 0.12
for k in range(1, NB):
    tr = np.zeros(n, bool); tr[edges[0]:edges[k]] = True; tr &= (y >= 0)
    if tr.sum() < 500: continue
    g = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05,
                                   subsample=0.8, random_state=0)
    g.fit(feat[tr], y[tr])
    seg = np.zeros(n, bool); seg[edges[k]:edges[k+1]] = True
    idx = np.where(seg)[0]
    p = g.predict_proba(feat[idx])[:, 1]
    dir7[idx[p >= 0.5+MARGIN]] = 1
    dir7[idx[p <= 0.5-MARGIN]] = -1
summarize("(7) ML classifier + margin entry (WF)", dir7, base)

print("="*135)
print("Decisive test: a real regime detector is +PnL in BOTH bull and bear blocks.")
print("Bear-only positive = it is just following gold's net decline (drift), as before.")
