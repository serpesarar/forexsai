"""ROBUSTNESS PROOF for the recommended combos — beyond leak-freeness.

Three independent stress tests on the honest GT outcomes:
  1. INDEPENDENCE — the pulse models log every 1-3 min, so member-level N is
     inflated by near-duplicate rows. Collapse each (symbol, direction, combo) to
     ONE independent trade per 15-min bucket (disjoint in time) and per 60-min
     bucket (coarser), and recompute WR. If WR survives de-duplication, it is not
     an overlapping-sample illusion.
  2. OUT-OF-SAMPLE — split buckets by date at the median; report test-half WR. A
     real pattern persists out of sample; an overfit one collapses.
  3. BOOTSTRAP 95% CI — resample independent buckets with replacement; report the
     WR confidence interval and whether its LOWER bound clears the symbol baseline.

A combo is "certain" only if: WR holds after de-dup, OOS WR ≈ in-sample, and the
bootstrap lower bound > symbol baseline WR.
"""
import json, random
from collections import defaultdict
from statistics import mean

rows = [json.loads(l) for l in open("signal_performance_research/gt_per_signal.jsonl")]
random.seed(7)
BASE = {"ml", "pulse1", "pulse2", "pulse3", "emel", "smc", "ai_panel"}


def fam(mt):
    return "ml" if mt.startswith("ml") else mt


BASELINE = {"USOIL.FOREX": 0.726, "XAUUSD": 0.710, "GDAXI.INDX": 0.756, "NDX.INDX": 0.710}

RECO = {
    "USOIL.FOREX": [{"pulse1", "smc"}, {"pulse2", "pulse3", "smc"},
                    {"pulse3", "smc"}, {"pulse1", "pulse3", "smc"}],
    "XAUUSD": [{"emel", "pulse1", "pulse2", "pulse3"}, {"pulse1", "pulse2", "pulse3"},
               {"emel", "pulse1", "pulse3"}],
    "GDAXI.INDX": [{"pulse1", "pulse3", "smc"}, {"pulse2", "pulse3"},
                   {"ml", "pulse1", "pulse2", "pulse3"}],
    "NDX.INDX": [{"pulse1", "pulse2", "pulse3"}, {"emel", "pulse1", "pulse2", "pulse3"},
                 {"emel", "pulse2"}],
}

# Build buckets: (sym, dir, gran, t//gran) -> {fams set, member outcomes}
def build(gran):
    bk = defaultdict(lambda: {"fams": set(), "gt": [], "pips": [], "t": None})
    for r in rows:
        f = fam(r["mt"])
        if f not in BASE or r["dir"] not in ("BUY", "SELL") or r["gt"] not in (0, 1):
            continue
        key = (r["sym"], r["dir"], r["t"] // gran)
        b = bk[key]
        b["fams"].add(f); b["gt"].append(r["gt"]); b["pips"].append(r["pips"])
        b["t"] = r["t"] if b["t"] is None else min(b["t"], r["t"])
    return bk


def bucket_trades(bk, sym, combo):
    """independent trades for buckets whose family-set EXACTLY == combo."""
    out = []
    for (s, d, _), b in bk.items():
        if s != sym or b["fams"] != combo:
            continue
        win = 1 if mean(b["gt"]) >= 0.5 else 0   # consensus of the agreeing models
        out.append((b["t"], win, mean(b["pips"])))
    return out


def boot_ci(wins, n, B=3000):
    if n == 0:
        return (0, 0)
    arr = [1] * wins + [0] * (n - wins)
    ws = []
    for _ in range(B):
        s = sum(arr[random.randrange(n)] for _ in range(n))
        ws.append(s / n)
    ws.sort()
    return ws[int(0.025 * B)], ws[int(0.975 * B)]


bk15 = build(900)
bk60 = build(3600)

# member-level WR (the originally reported figure) for reference
member = defaultdict(lambda: [0, 0])
for r in rows:
    f = fam(r["mt"])
    if f not in BASE or r["dir"] not in ("BUY", "SELL") or r["gt"] not in (0, 1):
        continue
member_bk = build(900)  # reuse for member counts via bucket members

out = []
def emit(s=""):
    out.append(s); print(s)

emit("ROBUSTNESS PROOF — recommended combos (honest GT, leak-audited)")
emit("each row: member-WR(N) | 15m indep WR(N) | 60m indep WR(N) | OOS-test WR(N) | "
     "bootstrap95 CI | baseline")
for sym, combos in RECO.items():
    base = BASELINE[sym]
    emit(f"\n=== {sym}  (baseline GT-WR {base:.1%}) ===")
    for combo in combos:
        name = "+".join(sorted(combo))
        # member-level
        mw = mn = 0
        for (s, d, _), b in member_bk.items():
            if s == sym and b["fams"] == combo:
                mw += sum(b["gt"]); mn += len(b["gt"])
        mwr = mw / mn if mn else 0
        # 15m independent
        t15 = bucket_trades(bk15, sym, combo)
        w15 = sum(w for _, w, _ in t15); n15 = len(t15)
        wr15 = w15 / n15 if n15 else 0
        # 60m independent
        t60 = bucket_trades(bk60, sym, combo)
        w60 = sum(w for _, w, _ in t60); n60 = len(t60)
        wr60 = w60 / n60 if n60 else 0
        # OOS split by median bucket time (15m units)
        if t15:
            cutoff = sorted(t for t, _, _ in t15)[len(t15) // 2]
            test = [(w) for t, w, _ in t15 if t >= cutoff]
            tr = [(w) for t, w, _ in t15 if t < cutoff]
            oos_wr = mean(test) if test else 0
            tr_wr = mean(tr) if tr else 0
        else:
            oos_wr = tr_wr = 0; test = []
        lo, hi = boot_ci(w15, n15)
        clears = "✓" if lo > base else "✗"
        emit(f"  {name:28s} mem {mwr:4.0%}({mn:5d}) | 15m {wr15:4.0%}({n15:4d}) | "
             f"60m {wr60:4.0%}({n60:4d}) | OOS {oos_wr:4.0%}({len(test):4d}) | "
             f"CI[{lo:.0%},{hi:.0%}] {clears} >base")

emit("\nLegend: 'mem'=member-level (inflated by repeat logging); 15m/60m=one trade per "
     "disjoint bucket (independent); OOS=second-half-by-date test WR; CI=bootstrap 95% "
     "of the 15m independent WR; ✓ = CI lower bound above the symbol baseline.")
open("signal_performance_research/validate_combos_results.txt", "w").write("\n".join(out))
