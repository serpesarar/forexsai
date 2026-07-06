"""Full edge battery for one instrument. Mirrors the XAUUSD investigation.

Run:  python3 mae_battery.py SYMBOL    (SYMBOL in XAUUSD/NDX/USOIL/DAX)

Sections:
  0  Setup: barrier/spread, blocks, bull/bear labelling by per-block price drift.
  1  70% WR search: BUY/SELL/both baselines + window scan (hour/2h/session/dow/
     dow+hour/dow+session) ranked by worst-block WR, drift control, direction-
     agnostic pooled WR.
  2  Rule strategies: SR bounce, channel, breakout, trend-follow, candle dir,
     RSI extremes, vol terciles, trend states, momentum states.
  3  ML: lean GBM, expanding walk-forward, per-fold WR, bootstrap CI, before/after
     spread.
  4  EV search: GBM director vs naive drift baseline, per-block mean PnL, bootstrap
     CI (success = CI lower bound > 0).
  5  Regime: 7 configs (fixed time / direction-only / time+dir / time+regime /
     dir+regime / time+dir+regime / ML classifier), bull-vs-bear block split.
All net of spread, 1m resolution, pessimistic tie-break, walk-forward where fitted.
"""
import sys
import numpy as np
import mae
from sklearn.ensemble import GradientBoostingClassifier

NB = 5
MIN_BLOCK = 25


def main(sym):
    t, o, h, l, c, v = mae.load(sym)
    n = len(t)
    ws, ts = mae.slices(n)
    work_end = n - mae.MAX_HOLD - 1
    barrier = mae.barrier_for(c)
    spread = barrier * mae.SPREAD_FRAC
    edges = np.linspace(ws, work_end, NB+1).astype(int)
    blocks = [(edges[i], edges[i+1]) for i in range(NB)]
    print(f"########## {sym} ##########")
    print(f"N={n}  working idx {ws}..{work_end}  barrier={barrier:.4f} "
          f"(0.10% of median {np.median(c):.2f})  spread={spread:.4f}")

    # block price drift -> bull/bear
    bull, bear = set(), set()
    drifts = []
    for i, (lo, hi) in enumerate(blocks):
        dr = c[hi-1]-c[lo]; drifts.append(dr)
        (bull if dr > 0 else bear).add(i)
    print("block drifts: " + " ".join(f"b{i+1}{d:+.0f}" for i, d in enumerate(drifts))
          + f"  BULL={sorted(x+1 for x in bull)} BEAR={sorted(x+1 for x in bear)}")

    # outcomes
    ob, pb, vb = mae.simulate_all(o, h, l, c, t, "BUY", barrier, spread)
    os_, ps, vs = mae.simulate_all(o, h, l, c, t, "SELL", barrier, spread)
    base = np.zeros(n, bool); base[ws:work_end] = True
    hour, dow, sess = mae.time_arrays(t)

    def blk_wr(out, mask):
        wrs, ns = [], []
        for lo, hi in blocks:
            m = mask.copy(); m[:lo] = False; m[hi:] = False
            sel = m & (out >= 0); nn = int(sel.sum())
            wrs.append(float(out[sel].mean()) if nn else 0.0); ns.append(nn)
        return wrs, ns

    # ---------- 1. baselines ----------
    print("\n--- 1. BASELINE WR (resolved, net spread) ---")
    for lbl, out, pnl in (("BUY", ob, pb), ("SELL", os_, ps)):
        sel = base & (out >= 0)
        print(f"  always {lbl}: WR {out[sel].mean():.1%} N={sel.sum()} "
              f"meanPnL {pnl[sel].mean():+.4f}")
    bothout = np.concatenate([ob[base & (ob >= 0)], os_[base & (os_ >= 0)]])
    print(f"  BUY+SELL pooled WR {bothout.mean():.1%} N={len(bothout)} (≈50% by geometry)")

    # ---------- window scan ----------
    windows = []
    for hr in range(24):
        windows.append((f"hour={hr:02d}", base & (hour == hr)))
    for a in range(0, 24, 2):
        windows.append((f"win{a:02d}-{a+2:02d}", base & (hour >= a) & (hour < a+2)))
    for s in ("London", "NY_overlap", "Asia", "Other"):
        windows.append((f"sess={s}", base & (sess == s)))
    for dw in range(5):
        windows.append((f"dow={dw}", base & (dow == dw)))
    for dw in range(5):
        for s in ("London", "NY_overlap", "Asia", "Other"):
            windows.append((f"dow{dw}+{s}", base & (dow == dw) & (sess == s)))
    for dw in range(5):
        for hr in range(24):
            windows.append((f"dow{dw}+h{hr:02d}", base & (dow == dw) & (hour == hr)))
    rows = []
    for name, m in windows:
        for dl, out, pnl in (("BUY", ob, pb), ("SELL", os_, ps)):
            wrs, ns = blk_wr(out, m)
            if min(ns) < MIN_BLOCK:
                continue
            totn = sum(ns); ov = sum(w*x for w, x in zip(wrs, ns))/totn
            mp = float(pnl[m & (out >= 0)].mean())
            rows.append((min(wrs), ov, np.std(wrs), totn, mp, name, dl, wrs))
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
    print(f"\n--- window scan: {len(windows)}x2 dirs. Top 12 by WORST-block WR (>={MIN_BLOCK}/blk) ---")
    print(f"{'minWR':>6}{'ovWR':>6}{'std':>5}{'N':>6}{'mPnL':>7}  per-block        win/dir")
    for r in rows[:12]:
        mn, ov, sd, tn, mp, nm, dl, wrs = r
        print(f"{mn:>6.0%}{ov:>6.0%}{sd:>5.2f}{tn:>6}{mp:>+7.3f}  "
              f"[{' '.join(f'{w:.0%}' for w in wrs)}]  {nm} {dl}")
    # drift control on top 5
    print("  drift control (top 5): this-dir ov vs opposite-dir ov")
    for r in rows[:5]:
        mn, ov, sd, tn, mp, nm, dl, wrs = r
        m = dict(windows)[nm]
        opp, oo = (os_, "SELL") if dl == "BUY" else (ob, "BUY")
        sel = m & (opp >= 0); ow = opp[sel].mean() if sel.any() else 0
        print(f"    {nm} {dl} ov {ov:.0%} | {oo} ov {ow:.0%} | sum {ov+ow:.0%}")

    # ---------- 2. rule strategies ----------
    print("\n--- 2. RULE STRATEGIES (overall WR / mean PnL, BUY & SELL where directional) ---")
    rsi = mae.rsi(c); a14 = mae.atr(h, l, c); e20 = mae.ema(c, 20); e50 = mae.ema(c, 50)
    adx14, pdi, mdi = mae.adx(h, l, c)
    r5 = np.zeros(n); r5[5:] = c[5:]-c[:-5]
    atr_w = a14[ws:work_end]; q1, q2 = np.percentile(atr_w, [33, 66])
    volb = np.where(a14 <= q1, 0, np.where(a14 <= q2, 1, 2))
    hh20 = np.array([h[max(0, i-20):i].max() if i > 0 else h[i] for i in range(n)])
    ll20 = np.array([l[max(0, i-20):i].min() if i > 0 else l[i] for i in range(n)])

    def rule(name, cond, direction):
        out = ob if direction == "BUY" else os_
        pnl = pb if direction == "BUY" else ps
        m = base & cond & (out >= 0)
        nn = int(m.sum())
        if nn < 100:
            print(f"  {name:34s} {direction}: N={nn} (too few)"); return
        print(f"  {name:34s} {direction}: WR {out[m].mean():.1%} meanPnL {pnl[m].mean():+.4f} N={nn}")
    near = a14  # proximity tolerance ~1 ATR
    rule("SR bounce (near prior low)", (c - ll20) < near, "BUY")
    rule("SR bounce (near prior high)", (hh20 - c) < near, "SELL")
    rule("channel low (RSI<35 + below e50)", (rsi < 35) & (c < e50), "BUY")
    rule("channel high (RSI>65 + above e50)", (rsi > 65) & (c > e50), "SELL")
    rule("breakout up (c>prior20 high)", c > hh20, "BUY")
    rule("breakout dn (c<prior20 low)", c < ll20, "SELL")
    rule("trend-follow up (e20>e50,ADX>25)", (e20 > e50) & (adx14 > 25), "BUY")
    rule("trend-follow dn (e20<e50,ADX>25)", (e20 < e50) & (adx14 > 25), "SELL")
    rule("candle up bar", (c > o), "BUY")
    rule("candle dn bar", (c < o), "SELL")
    rule("RSI<30 reversal", rsi < 30, "BUY")
    rule("RSI>70 reversal", rsi > 70, "SELL")
    for vb_ in (0, 1, 2):
        rule(f"vol tercile={vb_}", volb == vb_, "BUY")
        rule(f"vol tercile={vb_}", volb == vb_, "SELL")
    rule("momentum up (r5>0)", r5 > 0, "BUY")
    rule("momentum dn (r5<0)", r5 < 0, "SELL")

    # ---------- 3. ML walk-forward ----------
    print("\n--- 3. ML GBM walk-forward (P(BUY win)), per-fold WR, bootstrap CI ---")
    feat = np.column_stack([
        np.r_[0, np.diff(c)]/c, (c-e20)/c, (c-e50)/c, e20-e50, adx14, pdi-mdi,
        rsi, a14/c, r5/c, np.sign(r5),
        np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24)])
    feat = np.nan_to_num(feat)
    y = ob.copy()
    folds = NB
    fb = np.linspace(ws, work_end, folds+1).astype(int)
    THR = 0.58
    sel_pnls_net = []; sel_pnls_gross = []; fold_wr = []
    for k in range(1, folds):
        tr = np.zeros(n, bool); tr[fb[0]:fb[k]] = True; tr &= (y >= 0)
        if tr.sum() < 500:
            continue
        g = GradientBoostingClassifier(n_estimators=120, max_depth=3,
                                       learning_rate=0.05, subsample=0.8,
                                       random_state=0).fit(feat[tr], y[tr])
        seg = np.zeros(n, bool); seg[fb[k]:fb[k+1]] = True
        idx = np.where(seg)[0]
        p = g.predict_proba(feat[idx])[:, 1]
        # trade BUY if p>=THR, SELL if p<=1-THR
        bsel = idx[p >= THR]; ssel = idx[p <= 1-THR]
        wins = []; pn = []; pg = []
        for i in bsel:
            if ob[i] >= 0:
                wins.append(ob[i]); pn.append(pb[i]); pg.append(pb[i]+spread*np.sign(1))
        for i in ssel:
            if os_[i] >= 0:
                wins.append(os_[i]); pn.append(ps[i]); pg.append(ps[i]+spread)
        if wins:
            fold_wr.append((np.mean(wins), len(wins)))
            sel_pnls_net += pn; sel_pnls_gross += pg
    if fold_wr:
        for i, (w, nn) in enumerate(fold_wr):
            print(f"  fold{i+1}: WR {w:.1%} N={nn}")
        xn = np.array(sel_pnls_net); xg = np.array(sel_pnls_gross)
        lo, hi = mae.boot_ci(xn)
        print(f"  POOLED net: N={len(xn)} WR {(xn>0).mean():.1%} meanPnL {xn.mean():+.4f} "
              f"CI[{lo:+.4f},{hi:+.4f}] {'+EV*' if lo>0 else ''}")
        print(f"  POOLED gross(no spread): meanPnL {xg.mean():+.4f} WR {(xg>0).mean():.1%}")
    else:
        print("  no selections")

    # ---------- 4. EV search vs drift baseline ----------
    print("\n--- 4. EV: GBM director (per-block mean PnL) vs naive drift baseline ---")
    # GBM director using margin selection, expanding WF, per-block
    block_pn = {i: [] for i in range(NB)}
    MARGIN = 0.10
    for k in range(1, folds):
        tr = np.zeros(n, bool); tr[fb[0]:fb[k]] = True; tr &= (y >= 0)
        if tr.sum() < 500:
            continue
        g = GradientBoostingClassifier(n_estimators=120, max_depth=3,
                                       learning_rate=0.05, subsample=0.8,
                                       random_state=0).fit(feat[tr], y[tr])
        seg = np.zeros(n, bool); seg[fb[k]:fb[k+1]] = True
        idx = np.where(seg)[0]
        p = g.predict_proba(feat[idx])[:, 1]
        for i in idx[p >= 0.5+MARGIN]:
            if ob[i] >= 0: block_pn[k].append(pb[i])
        for i in idx[p <= 0.5-MARGIN]:
            if os_[i] >= 0: block_pn[k].append(ps[i])
    allpn = [x for k in block_pn for x in block_pn[k]]
    if allpn:
        x = np.array(allpn); lo, hi = mae.boot_ci(x)
        worst = min((np.mean(block_pn[k]) if block_pn[k] else 0) for k in range(1, folds))
        print(f"  GBM director: N={len(x)} meanPnL {x.mean():+.4f} CI[{lo:+.4f},{hi:+.4f}] "
              f"worst-block mean {worst:+.4f} {'+EV*' if lo>0 else ''}")
    # naive drift baseline: trade prevailing e20>e50 direction
    sgn = np.sign(e20-e50)
    bm = base & (sgn > 0) & (ob >= 0); sm = base & (sgn < 0) & (os_ >= 0)
    dpn = np.concatenate([pb[bm], ps[sm]])
    lo, hi = mae.boot_ci(dpn)
    print(f"  drift baseline (trade e20>e50 side): N={len(dpn)} meanPnL {dpn.mean():+.4f} "
          f"CI[{lo:+.4f},{hi:+.4f}]")

    # ---------- 5. regime configs ----------
    print("\n--- 5. REGIME configs (net spread), bull vs bear block PnL split ---")
    e200 = mae.ema(c, 200)
    r60 = np.zeros(n); r60[60:] = c[60:]/c[:-60]-1
    regime = np.zeros(n, int)
    regime[(c > e200) & (e20 > e50) & (r60 > 0) & (adx14 > 20)] = 1
    regime[(c < e200) & (e20 < e50) & (r60 < 0) & (adx14 > 20)] = -1
    time_mask = base & ((sess == "London") | (sess == "NY_overlap"))

    def cfg(name, dirarr, elig):
        pnls = np.zeros(n); res = np.zeros(n, bool)
        m = elig & (dirarr > 0) & (ob >= 0); pnls[m] = pb[m]; res |= m
        m = elig & (dirarr < 0) & (os_ >= 0); pnls[m] = ps[m]; res |= m
        nn = int(res.sum())
        if nn == 0:
            print(f"  {name:36s} no trades"); return
        bl = be = 0.0
        for i, (lo, hi) in enumerate(blocks):
            mm = res.copy(); mm[:lo] = False; mm[hi:] = False
            tot = float(pnls[mm].sum())
            if i in bull: bl += tot
            else: be += tot
        wr = float((pnls[res] > 0).mean()); mean = float(pnls[res].mean())
        flag = "  <-WINS BOTH" if (bl > 0 and be > 0) else ("  (bear-only=drift)" if be > 0 >= bl else "")
        print(f"  {name:36s} N={nn:5d} WR {wr:.0%} mean {mean:+.4f} "
              f"bull{bl:+7.0f} bear{be:+7.0f}{flag}")

    cfg("(2) always SELL", np.where(base, -1, 0), base)
    cfg("(2) always BUY", np.where(base, 1, 0), base)
    # (1) fixed time + train-majority dir, WF
    d1 = np.zeros(n, int)
    for k in range(1, NB):
        prior = np.zeros(n, bool); prior[edges[0]:edges[k]] = True; pm = prior & time_mask
        wb = pb[pm & (ob >= 0)].mean() if (pm & (ob >= 0)).any() else -9
        wsl = ps[pm & (os_ >= 0)].mean() if (pm & (os_ >= 0)).any() else -9
        ch = 1 if wb >= wsl else -1
        seg = np.zeros(n, bool); seg[edges[k]:edges[k+1]] = True; d1[seg & time_mask] = ch
    cfg("(1) time+fixed-dir WF", d1, time_mask)
    cfg("(3) time+SELL", np.where(time_mask, -1, 0), time_mask)
    cfg("(4) time+regime", np.where(time_mask, regime, 0), time_mask)
    cfg("(5) regime-gated", regime.copy(), base)
    cfg("(6) time+regime-gated", np.where(time_mask, regime, 0), time_mask)
    # (7) ML regime classifier
    d7 = np.zeros(n, int)
    for k in range(1, NB):
        tr = np.zeros(n, bool); tr[edges[0]:edges[k]] = True; tr &= (y >= 0)
        if tr.sum() < 500: continue
        g = GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.05,
                                       subsample=0.8, random_state=0).fit(feat[tr], y[tr])
        seg = np.zeros(n, bool); seg[edges[k]:edges[k+1]] = True; idx = np.where(seg)[0]
        p = g.predict_proba(feat[idx])[:, 1]
        d7[idx[p >= 0.62]] = 1; d7[idx[p <= 0.38]] = -1
    cfg("(7) ML classifier WF", d7, base)
    print()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "XAUUSD")
