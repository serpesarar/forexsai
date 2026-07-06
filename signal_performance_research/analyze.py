"""Production signal success table — per model, per combination, per day/date.

Source: prediction_logs resolved rows (status completed=WIN / stopped=LOSS),
2026-02-18 → 2026-05-29. Combinations from (a) the system's own
meta_combination_stats table and (b) derived co-occurrence (models that fired the
SAME direction on the SAME symbol within a 15-min bucket).

NOTE on WR scale: production "completed" means a TP was hit on 5m-candle eval, which
the prior 1m-replay work showed is geometry-inflated (in-bar TP/SL ambiguity). So
treat these WRs as the SYSTEM'S REPORTED numbers (useful for ranking models/combos
and finding good days), not as leak-free ground truth.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone

rows = json.load(open("signal_performance_research/resolved_logs.json"))
combos = json.load(open("signal_performance_research/meta_combos.json"))
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


for r in rows:
    r["_dt"] = parse(r["created_at"])
    r["_win"] = 1 if r["status"] == "completed" else 0

N = len(rows)
print(f"Resolved signals: {N}  ({sum(r['_win'] for r in rows)} win / "
      f"{N-sum(r['_win'] for r in rows)} loss)  overall WR "
      f"{sum(r['_win'] for r in rows)/N:.1%}")
print(f"Window: {min(r['_dt'] for r in rows).date()} → {max(r['_dt'] for r in rows).date()}")


def wr_table(key_fn, title, min_n=50, top=None, sort_wr=True):
    agg = defaultdict(lambda: [0, 0])  # key -> [wins, total]
    for r in rows:
        k = key_fn(r)
        if k is None:
            continue
        agg[k][0] += r["_win"]; agg[k][1] += 1
    items = [(k, w, n, w/n) for k, (w, n) in agg.items() if n >= min_n]
    items.sort(key=lambda x: (x[3] if sort_wr else x[2]), reverse=True)
    if top:
        items = items[:top]
    print(f"\n=== {title} (min {min_n} resolved) ===")
    for k, w, n, p in items:
        print(f"  {str(k):28s} WR {p:5.1%}  N={n:6d}  ({w}W/{n-w}L)")
    return agg


# ---- 1. per model_type ----
wr_table(lambda r: r["model_type"], "WR by MODEL", min_n=50, sort_wr=True)

# ---- 2. per model x symbol ----
wr_table(lambda r: f"{r['model_type']}|{r['symbol']}", "WR by MODEL x SYMBOL",
         min_n=200, top=25)

# ---- 3. per symbol ----
wr_table(lambda r: r["symbol"], "WR by SYMBOL", min_n=100)

# ---- 4. day of week (overall + per model) ----
wr_table(lambda r: DOW[r["_dt"].weekday()], "WR by DAY-OF-WEEK (all models)",
         min_n=100, sort_wr=False)
print("\n=== WR by MODEL x DAY-OF-WEEK (min 80) ===")
md = defaultdict(lambda: [0, 0])
for r in rows:
    md[(r["model_type"], DOW[r["_dt"].weekday()])][0] += r["_win"]
    md[(r["model_type"], DOW[r["_dt"].weekday()])][1] += 1
for mt in ["meta", "smc", "pulse1", "pulse2", "pulse3", "emel", "ml"]:
    cells = []
    for d in DOW[:5]:
        w, n = md[(mt, d)]
        cells.append(f"{d} {w/n:4.0%}({n})" if n >= 80 else f"{d}  --   ")
    print(f"  {mt:8s} " + " ".join(cells))

# ---- 5. by hour-of-day (UTC) ----
wr_table(lambda r: f"h{r['_dt'].hour:02d}", "WR by HOUR-OF-DAY UTC (all models)",
         min_n=300, sort_wr=True, top=10)

# ---- 6. best / worst calendar dates ----
wr_table(lambda r: r["_dt"].date().isoformat(), "BEST calendar DATES",
         min_n=120, top=12, sort_wr=True)
print("  --- WORST dates ---")
agg = defaultdict(lambda: [0, 0])
for r in rows:
    agg[r["_dt"].date().isoformat()][0] += r["_win"]; agg[r["_dt"].date().isoformat()][1] += 1
worst = sorted([(k, w, n, w/n) for k, (w, n) in agg.items() if n >= 120], key=lambda x: x[3])[:8]
for k, w, n, p in worst:
    print(f"  {k:28s} WR {p:5.1%}  N={n:6d}")

# ---- 7. combinations from meta_combination_stats (system's own) ----
print("\n=== TOP COMBINATIONS (meta_combination_stats, system-maintained) ===")
cc = [c for c in combos if c.get("total_signals", 0) >= 60]
cc.sort(key=lambda c: (c.get("win_rate") or 0), reverse=True)
print(f"{'combo_key':22s}{'symbol':9s}{'regime':10s}{'WR':>6}{'N':>6}{'PF':>6}{'EV':>7}")
for c in cc[:20]:
    print(f"  {c['combo_key']:20s}{c['symbol']:9s}{(c.get('regime') or '-'):10s}"
          f"{(c.get('win_rate') or 0):6.1%}{c.get('total_signals',0):6d}"
          f"{(c.get('profit_factor') or 0):6.2f}{(c.get('expectancy') or 0):+7.2f}")
print("  --- by expectancy ---")
cc.sort(key=lambda c: (c.get("expectancy") or -99), reverse=True)
for c in cc[:10]:
    print(f"  {c['combo_key']:20s}{c['symbol']:9s}{(c.get('regime') or '-'):10s}"
          f"{(c.get('win_rate') or 0):6.1%}{c.get('total_signals',0):6d}"
          f"{(c.get('profit_factor') or 0):6.2f}{(c.get('expectancy') or 0):+7.2f}")

# ---- 8. derived co-occurrence combinations (validation) ----
print("\n=== DERIVED CO-OCCURRENCE (models agreeing same dir, 15-min bucket) ===")
buckets = defaultdict(list)  # (symbol, dir, time15) -> list of rows
for r in rows:
    if r["ml_direction"] not in ("BUY", "SELL"):
        continue
    b = (r["symbol"], r["ml_direction"], int(r["_dt"].timestamp()//900))
    buckets[b].append(r)
# consensus level WR
lvl = defaultdict(lambda: [0, 0])
pair = defaultdict(lambda: [0, 0])
for b, rs in buckets.items():
    models = set(r["model_type"] for r in rs)
    k = min(len(models), 4)
    for r in rs:
        lvl[k][0] += r["_win"]; lvl[k][1] += 1
    ml = sorted(models)
    for i in range(len(ml)):
        for j in range(i+1, len(ml)):
            for r in rs:
                pair[(ml[i], ml[j])][0] += r["_win"]; pair[(ml[i], ml[j])][1] += 1
print("  consensus level (distinct models agreeing in bucket) -> WR:")
for k in sorted(lvl):
    w, n = lvl[k]
    print(f"    {k}{'+' if k==4 else ' '} model(s): WR {w/n:5.1%}  N={n}")
print("  top agreeing PAIRS (min 300 member-signals):")
pl = [(p, w, n, w/n) for p, (w, n) in pair.items() if n >= 300]
pl.sort(key=lambda x: x[3], reverse=True)
for p, w, n, prc in pl[:15]:
    print(f"    {p[0]:8s}+{p[1]:8s} WR {prc:5.1%}  N={n}")
