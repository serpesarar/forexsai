"""Part A — time/session/day window ranking (direction-agnostic view).

Uses cached 5/5 outcomes net of $0.30 spread. Working 40% split into 5 time blocks.
For each window x direction: per-block WR, overall WR, mean PnL, block-WR std
(stability), worst-block WR, N. Also a 'pooled both-direction' WR per window (the
literal 'regardless of direction' number — expected ~50% by construction).

Ranks by worst-block WR (robustness) with a min-trades-per-block floor.
"""
import numpy as np
import engine as E
from datetime import datetime, timezone

MIN_BLOCK = 25
NB = 5

d = np.load("/Users/melihcanodacioglu/Desktop/panel/xau_scalp_research/outcomes_5_5_sp030.npz")
buy, sell, buyp, sellp = d["buy"], d["sell"], d["buyp"], d["sellp"]
t, o, h, l, c, v = E.load()
n = len(t)
ws, _ = E.slices(n)
work_end = n - E.MAX_HOLD - 1
edges = np.linspace(ws, work_end, NB+1).astype(int)
blocks = [(edges[i], edges[i+1]) for i in range(NB)]

hour = ((t % 86400)//3600).astype(int)
dow = np.array([datetime.fromtimestamp(int(x), tz=timezone.utc).weekday() for x in t])
sess = np.array([E.session_of(x) for x in t])
base = np.zeros(n, bool); base[ws:work_end] = True


def per_block(out, pnl, mask):
    wrs, ns, pnls = [], [], []
    for (lo, hi) in blocks:
        m = mask.copy(); m[:lo] = False; m[hi:] = False
        sel = m & (out >= 0)
        nn = int(sel.sum())
        wrs.append(float(out[sel].mean()) if nn else 0.0)
        ns.append(nn)
        pnls.append(float(pnl[m].mean()) if m.sum() else 0.0)
    return wrs, ns, pnls


def evalwin(name, mask):
    rows = []
    for dlabel, out, pnl in (("BUY", buy, buyp), ("SELL", sell, sellp)):
        wrs, ns, pnls = per_block(out, pnl, mask)
        if min(ns) < MIN_BLOCK:
            continue
        totn = sum(ns); ov = sum(w*x for w, x in zip(wrs, ns))/totn
        mean_pnl = float(pnl[mask & (out >= 0)].mean())
        rows.append((min(wrs), ov, np.std(wrs), totn, mean_pnl, name, dlabel, wrs, ns))
    return rows


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
        windows.append((f"dow={dw}+{s}", base & (dow == dw) & (sess == s)))
for dw in range(5):
    for hr in range(24):
        windows.append((f"dow={dw}+h{hr:02d}", base & (dow == dw) & (hour == hr)))

print(f"Windows enumerated: {len(windows)} x 2 directions (multiple-comparison context)")
all_rows = []
for name, mask in windows:
    all_rows.extend(evalwin(name, mask))

all_rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
print(f"\nRanked by WORST-block WR (>= {MIN_BLOCK} trades/block). Top 30:")
print(f"{'minWR':>6}{'ovWR':>6}{'std':>5}{'totN':>6}{'mPnL$':>7}  per-block WR           window/dir")
for r in all_rows[:30]:
    minwr, ov, std, totn, mpnl, name, dl, wrs, ns = r
    wrstr = " ".join(f"{w:.0%}" for w in wrs)
    print(f"{minwr:>6.0%}{ov:>6.0%}{std:>5.2f}{totn:>6}{mpnl:>+7.2f}  [{wrstr}]  {name} {dl}")

# literal "regardless of direction" pooled WR for the headline windows
print("\n--- POOLED both-direction WR (literal 'regardless of BUY/SELL') ---")
print("(expected ~50%: pooling near-complementary BUY & SELL outcomes)")
for name, mask in [("win01-03", base & (hour >= 1) & (hour < 3)),
                   ("sess=London", base & (sess == "London")),
                   ("sess=NY_overlap", base & (sess == "NY_overlap")),
                   ("sess=Asia", base & (sess == "Asia"))]:
    both = np.concatenate([buy[mask & (buy >= 0)], sell[mask & (sell >= 0)]])
    print(f"  {name}: pooled WR {both.mean():.1%} over {len(both)} dir-trades")
