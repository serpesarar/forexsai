"""trade_eval_null2.py — (1) oynaklık-eşli plasebo: rastgele girişler yalnız aynı (k, pay, oran) UYGUNLUK maskesini
geçen konumlardan (aynı büyüklükte mumlar) seçilir; 30 tekrar, top-20/50. (2) top-20 sınama işlemlerinin gün kümelenmesi."""
import json, sys
import numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import trade_eval as E
from run_seq import TF
from seq_engine import run_lengths, eligible_ratio, ELIG_RATIO, ELIG_RATIO_PARTIAL

o = json.loads((HERE / "results" / "seq_scan.json").read_text())
cache = []
for t in o["tfs"]:
    T = TF(t["tf"]); run = run_lengths(T.brk)
    for m in [m for m in t["exact"]["motifs"] + t.get("partial", {}).get("motifs", []) if m["fwd"]["n"] >= E.MIN_OCC]:
        occ = E.occurrences(T, run, m); ent = occ + m["k"]; ent = ent[ent < len(T.o)]; ent = ent[T.seg[ent] == T.seg[ent - 1]]
        R = E.trade_R(T.o, T.h, T.l, T.c, T.seg, ent, E.atr_at(T, ent), E.TPS, E.SLS, E.MAX_HOLD, E.SPREAD)
        r = E.select_and_test(R, ent)
        if r is None: continue
        el = eligible_ratio(T.X, T.brk, m["k"], m["tol"], ELIG_RATIO if m.get("q", 1.0) == 1.0 else ELIG_RATIO_PARTIAL)
        pool = np.where(el)[0] + m["k"]
        pool = pool[(pool < len(T.o)) & (pool >= ent.min()) & (pool <= ent.max())]
        pool = pool[T.seg[pool] == T.seg[pool - 1]]
        cache.append((t["tf"], T, ent, pool, r))
real = [c[4] for c in cache]
def topk(res, K): return float(np.mean([r["oos_R"] for r in sorted(res, key=lambda r: -r["is_R"])[:K]]))
rng = np.random.default_rng(9); null = {20: [], 50: []}
for rep in range(30):
    res = []
    for tf, T, ent, pool, r in cache:
        if len(pool) < len(ent): continue
        pe = np.sort(rng.choice(pool, size=len(ent), replace=False))
        rp = E.select_and_test(E.trade_R(T.o, T.h, T.l, T.c, T.seg, pe, E.atr_at(T, pe), E.TPS, E.SLS, E.MAX_HOLD, E.SPREAD), pe)
        if rp is not None: res.append(rp)
    for K in null: null[K].append(topk(res, K))
for K in null:
    nv = np.array(null[K]); g = topk(real, K)
    print(f"OYNAKLIK-EŞLİ plasebo, en iyi {K}: gerçek {g:+.3f} | plasebo ort {nv.mean():+.3f} %95 üst {np.percentile(nv,95):+.3f} max {nv.max():+.3f} | p={np.mean(nv>=g):.2f}")
# gün kümelenmesi
top = sorted(cache, key=lambda c: -c[4]["is_R"])[:20]
rows = []
for tf, T, ent, pool, r in top:
    d = 0 if r["dir"] == "BUY" else 1; ti = int(np.where(E.TPS == r["tp"])[0][0]); si = int(np.where(E.SLS == r["sl"])[0][0])
    ents = np.sort(ent)[r["n_is"]:]
    Rv = r["R_all"][r["n_is"]:, d, ti, si]
    for e, v in zip(ents[:len(Rv)], Rv):
        rows.append({"day": str(T.d.ts.iat[e].date()), "R": v, "tf": tf})
x = pd.DataFrame(rows); byday = x.groupby("day").R.sum().sort_values(ascending=False)
print(f"top-20 sınama: {len(x)} işlem, {x.day.nunique()} farklı gün, toplam {x.R.sum():+.1f}R, ortR {x.R.mean():+.3f}")
print("  en kârlı 5 gün:", {k: round(v, 1) for k, v in byday.head(5).items()}, f"→ çıkarılınca toplam {x.R.sum()-byday.head(5).sum():+.1f}R")
print("  en kârlı 10 gün çıkarılınca:", round(x.R.sum() - byday.head(10).sum(), 1), "R")

# ── kart: top-20 portföyünün SINAMA işlemleri (seçim seçim-yarısında yapıldı) ──
rows = []
for tf, T, ent, pool, r in top:
    d = 0 if r["dir"] == "BUY" else 1; ti = int(np.where(E.TPS == r["tp"])[0][0]); si = int(np.where(E.SLS == r["sl"])[0][0])
    ents = np.sort(ent)[r["n_is"]:]; Rv = r["R_all"][r["n_is"]:, d, ti, si]
    for e, v in zip(ents[:len(Rv)], Rv):
        sl_pts = E.SLS[si] * float(E.atr_at(T, np.array([e]))[0])
        rows.append({"t": T.d.ts.iat[e], "R": v, "R15": v - 0.5 * E.SPREAD / sl_pts, "tf": tf,
                     "hold_end": T.d.ts.iat[min(e + E.MAX_HOLD, len(T.o) - 1)]})
x = pd.DataFrame(rows).sort_values("t").reset_index(drop=True)
R = x.R.to_numpy(); h = len(R) // 2
u, inv = np.unique(x.t.dt.strftime("%F"), return_inverse=True); s, k = np.bincount(inv, weights=R), np.bincount(inv)
pick = np.random.default_rng(1).integers(0, len(u), (4000, len(u))); bm = s[pick].sum(1) / k[pick].sum(1)
keep, busy = [], pd.Timestamp.min.tz_localize("UTC")
for i, rr in x.iterrows():
    if rr.t >= busy: keep.append(i); busy = rr.hold_end      # muhafazakâr: tutma tavanına kadar meşgul say
print(f"\nKART top-20 portföy sınama: n={len(R)} {x.t.min().date()}→{x.t.max().date()} WR %{100*(R>0).mean():.1f} ortR {R.mean():+.3f} "
      f"P(EV>0) %{100*(bm>0).mean():.1f} CI[{np.percentile(bm,2.5):+.3f},{np.percentile(bm,97.5):+.3f}] yarılar {R[:h].mean():+.3f}/{R[h:].mean():+.3f} "
      f"spread×1,5 {x.R15.mean():+.3f} tek-poz n={len(keep)} ortR {x.loc[keep].R.mean():+.3f}")
