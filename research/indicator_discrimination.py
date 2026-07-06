"""
RESEARCH ONLY — per-symbol indicator discrimination: TP (win) vs SL (loss).

For each symbol+direction, pools all models' signals, labels each WIN/LOSS by
the repaired resolution_reason, then for EVERY numeric indicator in `factors`
computes:
  - median value on WINs vs LOSSes
  - AUC = P(indicator higher on a random WIN than a random LOSS).
    AUC 0.50 = no separation. >0.50 = higher value favors WIN.
    <0.50 = lower value favors WIN. |AUC-0.5| is the discrimination strength.
Then prints, per symbol/direction, the indicators ranked by discrimination and
a plain-language "winning range" read. Also compares BUY-TP vs SELL-TP setups.

Reads prediction_logs + factors only. Touches nothing.
"""
import sys
from collections import defaultdict

sys.path.insert(0, "backend")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client

PAGE = 1000
SINCE = "2026-04-25T00:00:00+00:00"
SYMBOLS = ["XAUUSD", "USOIL.FOREX", "NDX.INDX", "GDAXI.INDX"]
MIN_PER_GROUP = 40          # need at least this many wins AND losses for a key
SKIP_KEYS = {"session", "source", "strategy", "target_type", "news_count",
             "regime_label", "dow", "hour_utc", "symbol", "model_type"}


def label(row):
    st = row.get("status"); rr = (row.get("resolution_reason") or "")
    rr2 = rr.replace("repair_bulk:", "").replace("repair:", "")
    win = (rr2 in ("tp4_hit", "window_resolve_positive", "all_targets_hit")
           or rr2.endswith("tp4_hit")
           or (st == "completed" and "tp1_3_hit_then_sl" not in rr2))
    loss = ("sl_hit" in rr2) or rr2 in ("window_resolve_negative", "direction_flip",
                                        "tp1_3_hit_then_sl") or st == "stopped"
    if win and not loss: return "WIN"
    if loss: return "LOSS"
    return None


def fnum(v):
    try:
        x = float(v)
        if x != x: return None  # nan
        return x
    except (TypeError, ValueError):
        return None


def auc(wins, losses):
    """P(win > loss) via rank-sum (Mann-Whitney U / (n*m)). O(n log n)."""
    n, m = len(wins), len(losses)
    if n == 0 or m == 0: return None
    allv = sorted([(v, 0) for v in wins] + [(v, 1) for v in losses])
    # average ranks for ties
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j+1][0] == allv[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j+1): ranks[k] = avg
        i = j + 1
    rank_sum_win = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 0)
    u = rank_sum_win - n*(n+1)/2.0
    return u / (n*m)


def median(xs):
    s = sorted(xs); n = len(s)
    if n == 0: return None
    return s[n//2] if n % 2 else (s[n//2-1]+s[n//2])/2.0


def pctl(xs, p):
    s = sorted(xs)
    if not s: return None
    i = max(0, min(len(s)-1, int(round(p*(len(s)-1)))))
    return s[i]


def main():
    c = get_supabase_client()
    # data[symbol][direction][label][key] = list of values
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for sym in SYMBOLS:
        off = 0
        while True:
            r = (c.table("prediction_logs")
                 .select("ml_direction,status,resolution_reason,factors")
                 .eq("symbol", sym).gte("created_at", SINCE)
                 .order("created_at", desc=False).range(off, off+PAGE-1).execute())
            page = r.get("data") if isinstance(r, dict) else getattr(r, "data", [])
            if not page: break
            for row in page:
                d = (row.get("ml_direction") or "").upper()
                if d not in ("BUY", "SELL"): continue
                lab = label(row)
                if lab is None: continue
                counts[sym][d][lab] += 1
                f = row.get("factors") or {}
                for k, v in f.items():
                    if k in SKIP_KEYS: continue
                    x = fnum(v)
                    if x is None: continue
                    data[sym][d][lab][k].append(x)
            if len(page) < PAGE: break
            off += PAGE

    for sym in SYMBOLS:
        for d in ("BUY", "SELL"):
            nw = counts[sym][d]["WIN"]; nl = counts[sym][d]["LOSS"]
            tot = nw + nl
            if tot < 60: continue
            wr = nw/tot*100
            print(f"\n{'='*70}\n{sym}  {d}   WIN={nw}  LOSS={nl}  WR={wr:.1f}%")
            keys = set(data[sym][d]["WIN"]) | set(data[sym][d]["LOSS"])
            scored = []
            for k in keys:
                w = data[sym][d]["WIN"].get(k, [])
                l = data[sym][d]["LOSS"].get(k, [])
                if len(w) < MIN_PER_GROUP or len(l) < MIN_PER_GROUP: continue
                a = auc(w, l)
                if a is None: continue
                scored.append((abs(a-0.5), a, k, median(w), median(l),
                               pctl(w, .25), pctl(w, .75)))
            scored.sort(reverse=True)
            if not scored:
                print("  (not enough per-indicator data)"); continue
            print(f"  {'indicator':22s} {'AUC':>5s}  {'WIN_med':>9s} {'LOSS_med':>9s}  win 25-75% range")
            for strength, a, k, wm, lm, q1, q3 in scored[:12]:
                arrow = "WIN higher" if a > 0.5 else "WIN lower"
                star = "***" if strength >= 0.15 else ("**" if strength >= 0.10 else ("*" if strength >= 0.06 else ""))
                print(f"  {k:22s} {a:5.2f}  {wm:9.3f} {lm:9.3f}  [{q1:.2f} .. {q3:.2f}] {arrow} {star}")

    # ── BUY-TP vs SELL-TP setup comparison (winners only) ──
    print(f"\n{'#'*70}\nBUY-TP vs SELL-TP winner setups (median indicator on WINNING signals)")
    for sym in SYMBOLS:
        bw = data[sym]["BUY"]["WIN"]; sw = data[sym]["SELL"]["WIN"]
        keys = sorted((set(bw) | set(sw)) - SKIP_KEYS)
        rich = [k for k in keys if len(bw.get(k, [])) >= MIN_PER_GROUP and len(sw.get(k, [])) >= MIN_PER_GROUP]
        if not rich: continue
        print(f"\n  {sym}:")
        for k in rich:
            print(f"    {k:22s}  BUY-win med={median(bw[k]):9.3f}   SELL-win med={median(sw[k]):9.3f}")


if __name__ == "__main__":
    main()
