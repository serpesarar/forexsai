"""Narrow recurring-edge search for XAUUSD 5-pip (1:1) trades.

Discipline:
  - Fixed condition grid (direction x hour/window/session/dow/vol/trend/candle).
  - 5/5 outcome computed NET of $0.30 spread, 1m resolution, pessimistic tie-break.
  - Working 40% slice split into 5 equal TIME BLOCKS (walk-forward style).
  - A condition is reported only with PER-BLOCK WR. Robust = high WR in EVERY block
    (esp. the last = out-of-sample tail), not just on average.
  - Drift control: for each candidate we also print the OPPOSITE-direction WR in the
    same condition. If BUY~SELL sum to ~100% and only the trend-aligned side wins,
    it's directional drift, not a recurring edge.
  - Multiple-comparison honesty: total #conditions tested is printed.
"""
import numpy as np
import engine as E
import strategies as S
import ml_model as M

SPREAD = 0.30
MIN_PER_BLOCK = 25      # require at least this many resolved trades in EVERY block
N_BLOCKS = 5


def precompute():
    t, o, h, l, c, v = E.load()
    n = len(o)
    # 5/5 outcomes net of spread, both directions
    buy = np.full(n, -1, np.int8)
    sell = np.full(n, -1, np.int8)
    for i in range(n-1):
        ob, _ = E.simulate_trade(o, h, l, c, t, i+1, "BUY", spread=SPREAD)
        if ob == "win": buy[i] = 1
        elif ob == "loss": buy[i] = 0
        os_, _ = E.simulate_trade(o, h, l, c, t, i+1, "SELL", spread=SPREAD)
        if os_ == "win": sell[i] = 1
        elif os_ == "loss": sell[i] = 0
    # conditioning variables
    from datetime import datetime, timezone
    hour = ((t % 86400)//3600).astype(int)
    dow = np.array([datetime.fromtimestamp(int(x), tz=timezone.utc).weekday() for x in t])
    # ATR + terciles (computed on working slice for bucket edges)
    atr = M.atr(h, l, c, 14)
    rsi = M.rsi(c, 14)
    # 5m trend via EMA20/50
    htf5 = S.resample(t, o, h, l, c, v, 300)
    ct, _, _, _, cc5 = htf5
    ef = S._ema(cc5, 20); es = S._ema(cc5, 50)
    j5 = np.searchsorted(ct, t, side="right") - 1
    j5c = np.clip(j5, 0, len(cc5)-1)
    trend = np.where(j5 < 0, 0, np.sign(ef[j5c] - es[j5c])).astype(int)  # -1,0,1
    bar_dir = np.sign(c - o).astype(int)
    return dict(t=t, o=o, h=h, l=l, c=c, v=v, n=n, buy=buy, sell=sell,
                hour=hour, dow=dow, atr=atr, rsi=rsi, trend=trend, bar_dir=bar_dir)


def block_wr(out, mask, blocks):
    """Return list of (wr, n) per block for resolved trades under mask."""
    res = []
    for (lo, hi) in blocks:
        bm = mask.copy()
        bm[:lo] = False; bm[hi:] = False
        sel = bm & (out >= 0)
        nn = int(sel.sum())
        wr = float(out[sel].mean()) if nn else 0.0
        res.append((wr, nn))
    return res


def main():
    D = precompute()
    n = D["n"]; ws, _ = E.slices(n)
    work_end = n - E.MAX_HOLD - 1
    edges = np.linspace(ws, work_end, N_BLOCKS+1).astype(int)
    blocks = [(edges[i], edges[i+1]) for i in range(N_BLOCKS)]
    print(f"Working slice idx {ws}..{work_end}, {N_BLOCKS} blocks of ~{(work_end-ws)//N_BLOCKS} bars each")
    # vol terciles from working slice atr
    atr_w = D["atr"][ws:work_end]
    q1, q2 = np.percentile(atr_w, [33, 66])
    volb = np.where(D["atr"] <= q1, 0, np.where(D["atr"] <= q2, 1, 2))

    # ---- build fixed condition grid ----
    conds = []  # (name, direction, mask)
    base = np.zeros(n, bool); base[ws:work_end] = True
    sess = np.array([E.session_of(x) for x in D["t"]])
    for d in ("BUY", "SELL"):
        out = D[d.lower()]
        conds.append((f"{d} ALL", d, base.copy(), out))
        for hr in range(24):
            conds.append((f"{d} hour={hr:02d}", d, base & (D["hour"]==hr), out))
        for a in range(0, 24, 2):
            conds.append((f"{d} win {a:02d}-{a+2:02d}", d, base & (D["hour"]>=a) & (D["hour"]<a+2), out))
        for s in ("London","NY_overlap","Asia","Other"):
            conds.append((f"{d} sess={s}", d, base & (sess==s), out))
        for dw in range(5):
            conds.append((f"{d} dow={dw}", d, base & (D["dow"]==dw), out))
        for vb in (0,1,2):
            conds.append((f"{d} vol={vb}", d, base & (volb==vb), out))
        for tr in (-1,0,1):
            conds.append((f"{d} trend={tr:+d}", d, base & (D["trend"]==tr), out))
        conds.append((f"{d} RSI<30", d, base & (D["rsi"]<30), out))
        conds.append((f"{d} RSI>70", d, base & (D["rsi"]>70), out))
        conds.append((f"{d} barUp", d, base & (D["bar_dir"]>0), out))
        conds.append((f"{d} barDn", d, base & (D["bar_dir"]<0), out))
        # a few 2-way combos
        for s in ("London","NY_overlap","Asia"):
            for tr in (-1,1):
                conds.append((f"{d} sess={s} trend={tr:+d}", d, base & (sess==s) & (D["trend"]==tr), out))
        for vb in (0,2):
            for tr in (-1,1):
                conds.append((f"{d} vol={vb} trend={tr:+d}", d, base & (volb==vb) & (D["trend"]==tr), out))

    print(f"\nTotal conditions tested: {len(conds)} (multiple-comparison context)\n")

    # evaluate
    rows = []
    for name, d, mask, out in conds:
        bw = block_wr(out, mask, blocks)
        ns = [x[1] for x in bw]
        wrs = [x[0] for x in bw]
        if min(ns) < MIN_PER_BLOCK:
            continue
        overall_n = sum(ns)
        overall_w = sum(wr*nn for wr,nn in bw)
        overall_wr = overall_w/overall_n
        rows.append((min(wrs), overall_wr, min(ns), overall_n, name, d, wrs, mask, out))

    # Sort by WORST-block WR (robustness), then overall
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
    print("Ranked by WORST-block WR (robustness). Showing top 25 with >=25 trades/block:")
    print(f"{'minWR':>6}{'ovWR':>6}{'minN':>5}{'totN':>6}  per-block WR            condition")
    for r in rows[:25]:
        minwr, ovwr, minn, totn, name, d, wrs, mask, out = r
        wrstr = " ".join(f"{w:.0%}" for w in wrs)
        print(f"{minwr:>6.0%}{ovwr:>6.0%}{minn:>5}{totn:>6}  [{wrstr}]  {name}")

    # Drift control on the best few: compare opposite direction same condition
    print("\n--- DRIFT CONTROL (opposite direction, same time/condition mask) ---")
    seen = set()
    for r in rows[:8]:
        minwr, ovwr, minn, totn, name, d, wrs, mask, out = r
        opp = D["sell"] if d == "BUY" else D["buy"]
        bw = block_wr(opp, mask, blocks)
        ow = sum(w*nn for w,nn in bw)/max(sum(nn for _,nn in bw),1)
        print(f"  {name}: this-dir overall {ovwr:.0%} | opposite-dir overall {ow:.0%}  (sum={ovwr+ow:.0%})")


if __name__ == "__main__":
    main()
