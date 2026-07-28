"""audit_claimB5.py — asil test: BUY-SELL ASIMETRISI anlamli mi? + MT5 capraz kontrol."""
from __future__ import annotations
import numpy as np, pandas as pd

RNG = np.random.default_rng(101)
g = pd.read_parquet("data/grid.parquet"); e = pd.read_parquet("data/episodes.parquet")
for df in (g, e):
    df["hour"] = df.ts.dt.hour; df["date"] = df.ts.dt.date
lo, hi = g.ts.min(), g.ts.max(); e = e[(e.ts >= lo) & (e.ts <= hi)].copy()


def hour_matched_ev(ex, gx):
    w = ex.hour.value_counts(normalize=True)
    gm = gx.groupby("hour").r.mean()
    c = w.index.intersection(gm.index); ww = w.loc[c] / w.loc[c].sum()
    return float((gm.loc[c] * ww).sum())


print("[F] ASIMETRI TESTI: Δsecim(SELL) − Δsecim(BUY), gun-bloklu bootstrap B=4000")
days = sorted(set(e.date))
gd = {d: {k: v for k, v in g[g.direction == d].groupby("date")} for d in ("BUY", "SELL")}
ed = {d: {k: v for k, v in e[e.direction == d].groupby("date")} for d in ("BUY", "SELL")}

for mode in ("ham", "saat-esit", "RTH-only"):
    obs = {}
    for d in ("BUY", "SELL"):
        ex, gx = e[e.direction == d], g[g.direction == d]
        if mode == "RTH-only":
            ex = ex[(ex.hour >= 13) & (ex.hour < 20)]; gx = gx[(gx.hour >= 13) & (gx.hour < 20)]
            obs[d] = ex.r.mean() - gx.r.mean()
        elif mode == "saat-esit":
            obs[d] = ex.r.mean() - hour_matched_ev(ex, gx)
        else:
            obs[d] = ex.r.mean() - gx.r.mean()
    out = np.empty(4000)
    for b in range(4000):
        pick = [days[i] for i in RNG.integers(0, len(days), len(days))]
        vals = {}
        for d in ("BUY", "SELL"):
            ep = [ed[d][k] for k in pick if k in ed[d]]
            gp = [gd[d][k] for k in pick if k in gd[d]]
            if not ep or not gp:
                vals[d] = np.nan; continue
            E_ = pd.concat(ep); G_ = pd.concat(gp)
            if mode == "RTH-only":
                E_ = E_[(E_.hour >= 13) & (E_.hour < 20)]; G_ = G_[(G_.hour >= 13) & (G_.hour < 20)]
                vals[d] = E_.r.mean() - G_.r.mean()
            elif mode == "saat-esit":
                vals[d] = E_.r.mean() - hour_matched_ev(E_, G_)
            else:
                vals[d] = E_.r.mean() - G_.r.mean()
        out[b] = vals["SELL"] - vals["BUY"]
    out = out[np.isfinite(out)]
    l5, h95 = np.percentile(out, [5, 95])
    print(f"  {mode:10s} ΔSELL={obs['SELL']:+.4f} ΔBUY={obs['BUY']:+.4f} "
          f"fark={obs['SELL']-obs['BUY']:+.4f} %5-95=[{l5:+.4f},{h95:+.4f}] "
          f"P(fark>0)={(out > 0).mean()*100:.1f}%")

print("\n[G] MT5 GERCEK (NAS100) — yon bazinda")
m = pd.read_csv("data/mt5_positions.csv")
n = m[m.symbol.str.contains("NAS", case=False, na=False)]
print(f"  NAS100 pozisyon: {len(n)}")
if len(n):
    for d, grp in n.groupby("direction"):
        print(f"    {d}: n={len(grp)} kazanan={int((grp.profit>0).sum())} "
              f"WR={float((grp.profit>0).mean())*100:.1f}% toplam={grp.profit.sum():+.2f}")
    print("    yorum: bu sayilar farkli scope/geometrilerden gelir, dogrudan kiyas degil.")
print("  tum semboller yon karnesi:")
for (sy, d), grp in m.groupby(["symbol", "direction"]):
    print(f"    {sy:10s} {d:4s} n={len(grp):3d} WR={float((grp.profit>0).mean())*100:5.1f}% tot={grp.profit.sum():+9.2f}")
