"""audit_claimB4.py — nedensel placebo + mutlak anlamlilik + split (80/110) + MT5 capraz kontrol."""
from __future__ import annotations
import numpy as np, pandas as pd

RNG = np.random.default_rng(23)
g = pd.read_parquet("data/grid.parquet"); e = pd.read_parquet("data/episodes.parquet")
for df in (g, e):
    df["hour"] = df.ts.dt.hour; df["date"] = df.ts.dt.date
    df["month"] = df.ts.dt.to_period("M").astype(str)
lo, hi = g.ts.min(), g.ts.max()
e = e[(e.ts >= lo) & (e.ts <= hi)].copy()

SPLIT_TRAIN_END = pd.Timestamp("2026-05-05", tz="UTC")
SPLIT_VAL_END = pd.Timestamp("2026-06-12", tz="UTC")
def split_of(ts):
    p = pd.Timedelta(days=2)
    return np.where(ts < SPLIT_TRAIN_END - p, "train",
           np.where(ts < SPLIT_TRAIN_END, "purge",
           np.where(ts < SPLIT_VAL_END - p, "val",
           np.where(ts < SPLIT_VAL_END, "purge", "test"))))
g["split"] = split_of(g.ts); e["split"] = split_of(e.ts)

print("[A] 80/110 — SPLIT bazinda (ham + saat-esit)")
def matched(ex, gx, keys):
    ec = ex.groupby(keys).agg(pev=("r","mean"), k=("r","size")).reset_index()
    gc = gx.groupby(keys).agg(ev=("r","mean")).reset_index()
    m = ec.merge(gc, on=keys, how="inner"); w = m.k.values
    return float((m.ev*w).sum()/w.sum()), float((m.pev*w).sum()/w.sum()), m
for d in ("BUY","SELL"):
    for sp in ("train","val","test"):
        gx = g[(g.direction==d)&(g.split==sp)]; ex = e[(e.direction==d)&(e.split==sp)]
        gh,ph,_ = matched(ex,gx,["hour"]); gd,pdd,_ = matched(ex,gx,["date","hour"])
        print(f"  {d} {sp:5s} izgara n={len(gx):5d} EV={gx.r.mean():+.4f} | pulse n={len(ex):4d} "
              f"EV={ex.r.mean():+.4f} | ham Δ={ex.r.mean()-gx.r.mean():+.4f} saat Δ={ph-gh:+.4f} "
              f"gun×saat Δ={pdd-gd:+.4f}")

print("\n[B] NEDENSEL PLACEBO — ayni gun, sinyalden SONRAKI izgara noktalarindan rastgele giris (B=2000)")
for d in ("BUY","SELL"):
    ex = e[e.direction==d]; gs = g[g.direction==d]
    gref = gs.r.mean()
    pools = []
    for r in ex.itertuples(index=False):
        p = gs[(gs.date==r.date) & (gs.ts >= r.ts)]
        pools.append(p.r.values if len(p) else np.array([]))
    valid = [p for p in pools if len(p)]
    obs = ex.r.mean()
    out = np.empty(2000)
    for b in range(2000):
        out[b] = np.mean([p[RNG.integers(len(p))] for p in valid])
    print(f"  {d}: gozlenen pulseEV={obs:+.4f} | ileri-placebo ort={out.mean():+.4f} sd={out.std():.4f} "
          f"| p(placebo>=gozlenen)={(out>=obs).mean():.3f} | havuz bulunan {len(valid)}/{len(ex)}")

print("\n[C] MUTLAK EV anlamliligi — gun-bloklu bootstrap (pulse epizodlari)")
for d in ("BUY","SELL"):
    ex = e[e.direction==d]; days = ex.date.unique()
    grp = {k:v.r.values for k,v in ex.groupby("date")}
    out = np.empty(6000)
    for b in range(6000):
        pick = RNG.choice(len(days), size=len(days), replace=True)
        out[b] = np.concatenate([grp[days[i]] for i in pick]).mean()
    l5,h95 = np.percentile(out,[5,95])
    print(f"  {d}: n={len(ex)} gun={len(days)} EV={ex.r.mean():+.4f} %5-95=[{l5:+.4f},{h95:+.4f}] "
          f"P(EV>0)={(out>0).mean()*100:.1f}%")

print("\n[D] ETKIN ORNEK: ayni gun icindeki epizodlarin sonuc korelasyonu")
for d in ("BUY","SELL"):
    ex = e[e.direction==d]
    per = ex.groupby("date").r.agg(["size","mean"])
    multi = per[per["size"]>1]
    # gun-ici varyans vs gunler-arasi varyans
    tot = ex.r.var(ddof=1)
    within = ex.groupby("date").r.transform("mean")
    between = within.var(ddof=1); wvar = (ex.r-within).var(ddof=1)
    icc = between/(between+wvar)
    neff = len(ex)/(1+(ex.groupby('date').size().mean()-1)*icc)
    print(f"  {d}: n={len(ex)} gun={ex.date.nunique()} gun-basi ort={ex.groupby('date').size().mean():.1f} "
          f"ICC(gun)={icc:.3f} → etkin n≈{neff:.0f}")

print("\n[E] MT5 GERCEK ISLEMLER (NAS100) — pulse kaynakli mi, yon karnesi")
try:
    m = pd.read_csv("data/mt5_positions.csv")
    print("  kolonlar:", list(m.columns))
    sym = [c for c in m.columns if "sym" in c.lower()]
    print(m.head(3).to_string())
except Exception as ex_:
    print("  okunamadi:", ex_)
