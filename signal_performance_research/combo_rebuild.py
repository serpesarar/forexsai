"""Rebuild per-symbol model combinations on HONEST 1m ground-truth outcomes.

Two tables:
  A. META source_combo table — re-grade the system's own meta_combination_stats
     concept (meta signals grouped by factors.source_combo) using GT outcomes
     instead of the inflated production status.
  B. NEW consensus combinations — derive which BASE models actually agreed
     (same symbol+direction within a 15-min bucket) and grade each model-set by
     GT win-rate AND net pips expectancy. Discovers combos the system isn't
     tracking. Also reports the consensus-depth lift on honest outcomes.

Input: gt_per_signal.jsonl (sym, mt, dir, t, tf, combo, regime, prod_win, gt, pips)
gt: 1=win 0=loss -1=neutral/timeout None=unevaluable.
"""
import json
from collections import defaultdict

rows = [json.loads(l) for l in open("signal_performance_research/gt_per_signal.jsonl")]
SYMS = ["USOIL.FOREX", "XAUUSD", "GDAXI.INDX", "NDX.INDX"]


def fam(mt):
    if mt.startswith("ml"):
        return "ml"
    return mt


def stats(items):
    """items = list of (gt, pips). Return wins,losses,n_res,wr,ev,pf."""
    w = sum(1 for g, _ in items if g == 1)
    l = sum(1 for g, _ in items if g == 0)
    nres = w + l
    res_pips = [p for g, p in items if g in (0, 1)]
    wr = w / nres if nres else 0
    ev = sum(res_pips) / nres if nres else 0
    gross_w = sum(p for g, p in items if g == 1)
    gross_l = -sum(p for g, p in items if g == 0)
    pf = gross_w / gross_l if gross_l > 0 else float("inf")
    return w, l, nres, wr, ev, pf


out = []
def emit(s=""):
    out.append(s); print(s)

# ── baseline GT-WR per symbol (all resolved) ──────────────────────────────────
emit("=" * 78)
emit("BASELINE GROUND-TRUTH WR per symbol (all models, resolved only)")
for sym in SYMS:
    items = [(r["gt"], r["pips"]) for r in rows if r["sym"] == sym and r["gt"] in (0, 1)]
    w, l, nres, wr, ev, pf = stats(items)
    emit(f"  {sym:13s} GT-WR {wr:5.1%}  EV {ev:+7.2f} pips/trade  PF {pf:4.2f}  N={nres}")

# ── A. META source_combo table, honest ───────────────────────────────────────
emit("\n" + "=" * 78)
emit("A. HONEST META source_combo TABLE (meta signals re-graded on GT)")
emit("   (replaces inflated meta_combination_stats; min 25 resolved)")
for sym in SYMS:
    g = defaultdict(list)
    for r in rows:
        if r["sym"] == sym and r["mt"] == "meta" and r.get("combo") and r["gt"] in (0, 1):
            g[r["combo"]].append((r["gt"], r["pips"]))
    items = [(c, *stats(v)) for c, v in g.items()]
    items = [x for x in items if x[3] >= 25]  # nres>=25
    items.sort(key=lambda x: -x[4])  # by WR
    emit(f"\n  --- {sym} (top by honest WR) ---")
    emit(f"    {'combo':34s}{'WR':>6}{'EV':>8}{'PF':>6}{'N':>6}")
    for c, w, l, nres, wr, ev, pf in items[:8]:
        emit(f"    {c:34s}{wr:6.1%}{ev:+8.2f}{pf:6.2f}{nres:6d}")

# ── B. NEW consensus combinations from base-model co-occurrence ───────────────
# bucket = (sym, dir, 15-min). family-set of base models present in bucket.
BASE = {"ml", "pulse1", "pulse2", "pulse3", "emel", "smc", "ai_panel"}
emit("\n" + "=" * 78)
emit("B. NEW CONSENSUS COMBINATIONS (base models agreeing, 15-min bucket, GT)")

buckets = defaultdict(list)
for r in rows:
    f = fam(r["mt"])
    if f not in BASE or r["dir"] not in ("BUY", "SELL"):
        continue
    buckets[(r["sym"], r["dir"], r["t"] // 900)].append(r)

# combo (frozenset of families) -> list of (gt,pips) for every member signal
combo_items = defaultdict(lambda: defaultdict(list))     # sym -> combo -> items
depth_items = defaultdict(lambda: defaultdict(list))     # sym -> depth -> items
pair_items = defaultdict(lambda: defaultdict(list))      # sym -> pair -> items
for (sym, d, _), rs in buckets.items():
    fams = sorted({fam(x["mt"]) for x in rs})
    cs = "+".join(fams)
    depth = min(len(fams), 5)
    for x in rs:
        if x["gt"] in (0, 1):
            combo_items[sym][cs].append((x["gt"], x["pips"]))
            depth_items[sym][depth].append((x["gt"], x["pips"]))
    for i in range(len(fams)):
        for j in range(i + 1, len(fams)):
            for x in rs:
                if x["gt"] in (0, 1):
                    pair_items[sym][f"{fams[i]}+{fams[j]}"].append((x["gt"], x["pips"]))

emit("\n  consensus DEPTH lift (distinct base families agreeing) on GT:")
for sym in SYMS:
    emit(f"  {sym}:")
    for depth in sorted(depth_items[sym]):
        w, l, nres, wr, ev, pf = stats(depth_items[sym][depth])
        if nres >= 30:
            emit(f"     {depth}{'+' if depth==5 else ' '} fam  WR {wr:5.1%}  EV {ev:+7.2f}  PF {pf:4.2f}  N={nres}")

for sym in SYMS:
    items = [(c, *stats(v)) for c, v in combo_items[sym].items()]
    items = [x for x in items if x[3] >= 40]
    by_wr = sorted(items, key=lambda x: -x[4])[:8]
    by_ev = sorted(items, key=lambda x: -x[5])[:8]
    emit(f"\n  --- {sym}: BEST combos by honest WR (min 40 res) ---")
    emit(f"    {'combo':30s}{'WR':>6}{'EV':>8}{'PF':>6}{'N':>6}")
    for c, w, l, nres, wr, ev, pf in by_wr:
        emit(f"    {c:30s}{wr:6.1%}{ev:+8.2f}{pf:6.2f}{nres:6d}")
    emit(f"  --- {sym}: BEST combos by net EV (pips/trade) ---")
    for c, w, l, nres, wr, ev, pf in by_ev:
        emit(f"    {c:30s}{wr:6.1%}{ev:+8.2f}{pf:6.2f}{nres:6d}")

emit("\n  best agreeing PAIRS by honest WR (min 120 member-res):")
for sym in SYMS:
    items = [(p, *stats(v)) for p, v in pair_items[sym].items()]
    items = [x for x in items if x[3] >= 120]
    items.sort(key=lambda x: -x[4])
    emit(f"  {sym}:")
    for p, w, l, nres, wr, ev, pf in items[:5]:
        emit(f"     {p:22s} WR {wr:5.1%}  EV {ev:+7.2f}  PF {pf:4.2f}  N={nres}")

open("signal_performance_research/combo_rebuild_results.txt", "w").write("\n".join(out))
