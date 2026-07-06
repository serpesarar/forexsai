"""
Re-damıtma Adım 1 — KAPSAMLI edge taraması (yön-hizalı, tüm feature, dedup+CV+placebo).
Tüm feature uzayını (kanal/VWAP/VP/sweep/ADX/S-R × 5m/15m/30m) yön-hizalı flatten edip
combo_filter (greedy + nested-CV + placebo) ile her model/sembol → kaçırdığımız kural?
"""
import json, sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
sys.path.insert(0, str(ROOT / "yeni deneme"))
from combo_filter import discover_rule, nested_cv, placebo, evaluate

recs = [json.loads(l) for l in open(ROOT / "sr_rejection_research" / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])
TFS = ["5m", "15m", "30m"]


def flatten(r):
    buy = r["dir"] == "BUY"; ind = {}
    for tf in TFS:
        f = r["f"].get(tf)
        if not f:
            continue
        c = (f.get("chan") or {}).get("50") or (f.get("chan") or {}).get(50)
        if c and c["spp"] > 1e-9:
            z = c["pm"] / c["spp"]; ind[f"{tf}_rev_chan"] = (-z) if buy else z   # ≥2.5=reversion
        if f.get("vwap"):
            vz = f["vwap"]["vwap_z"]; ind[f"{tf}_rev_vwap"] = (-vz) if buy else vz
        if f.get("vp"):
            vp = f["vp"]["vp_pos"]; ind[f"{tf}_rev_vp"] = (-vp) if buy else vp
        dl = f["d_sup"] if buy else f["d_res"]
        if dl is not None:
            ind[f"{tf}_dist_level"] = dl
        ind[f"{tf}_touched"] = 1.0 if (f["touched_sup"] if buy else f["touched_res"]) else 0.0
        if f.get("sweep"):
            s = f["sweep"]
            ind[f"{tf}_sweep_rev"] = 1.0 if (s["bull"] if buy else s["bear"]) else 0.0
            ind[f"{tf}_sweep_cont"] = 1.0 if (s["bear"] if buy else s["bull"]) else 0.0
        if f.get("adx") is not None:
            ind[f"{tf}_adx"] = f["adx"]
    return ind


# dedup (60dk/kurulum) + flatten
last = {}; rows = []
for r in recs:
    k = (r["model"], r["symbol"], r["dir"]); t = datetime.fromisoformat(r["t"]).timestamp()
    if k in last and t - last[k] <= 3600:
        continue
    last[k] = t
    ind = flatten(r)
    if ind:
        rows.append({"win": r["win"], "ind": ind, "symbol": r["symbol"], "model": r["model"]})
print(f"Dedup + flatten: {len(rows)} sinyal\n")


def my_candidates(rs, qs=(0.2, 0.35, 0.5, 0.65, 0.8)):
    keys = set()
    for r in rs:
        keys.update(k for k, v in r["ind"].items() if isinstance(v, (int, float)))
    out = []
    for k in sorted(keys):
        vals = sorted(r["ind"][k] for r in rs if k in r["ind"])
        if len(vals) < 30:
            continue
        for q in qs:
            thr = vals[int(q * (len(vals) - 1))]
            out += [(k, "<", thr), (k, ">", thr)]
    return out


def report(rs, title, max_conds=3, min_n=120):
    n = len(rs)
    print("=" * 76); print(f"{title} | n={n}"); print("=" * 76)
    if n < min_n:
        print("  n az, atlandı"); return
    base = sum(x["win"] for x in rs) / n
    cands = my_candidates(rs)
    rule = discover_rule(rs, cands, max_conds=max_conds, min_keep_frac=0.20)
    if not rule:
        print(f"  base WR={base*100:.0f}% — anlamlı kural yok"); return
    wr, kept = evaluate(rs, rule)
    cv = nested_cv(rs, cands, max_conds=max_conds, min_keep_frac=0.20)
    p = placebo(rs, cands, M=100, max_conds=max_conds, min_keep_frac=0.20)
    print(f"  base WR={base*100:.0f}%")
    print(f"  KURAL: " + "  AND  ".join(f"{k} {d} {t:.3g}" for k, d, t in rule))
    print(f"  in-sample: WR {wr*100:.0f}% ({kept}/{n}, +{(wr-base)*100:.0f}pp)")
    if cv:
        print(f"  nested-CV: WR {cv[0]*100:.0f}% (DÜRÜST OOS, {cv[2]}/4 fold)")
    verdict = "✅ GERÇEK" if p < 0.05 else ("⚠️ sınırda" if p < 0.2 else "❌ overfit/şans")
    print(f"  placebo p={p:.3f} → {verdict}")


by_model = defaultdict(list)
for r in rows:
    by_model[r["model"]].append(r)
for model in ["pulse3", "pulse1", "pulse2", "meta", "smc"]:
    if len(by_model.get(model, [])) >= 200:
        report(by_model[model], f"MODEL: {model}")
        print()
