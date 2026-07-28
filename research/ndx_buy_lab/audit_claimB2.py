"""audit_claimB2.py — ayrıştırma: 'secim degeri' nerede kayboluyor + placebo."""
from __future__ import annotations
import numpy as np, pandas as pd

RNG = np.random.default_rng(11)
g = pd.read_parquet("data/grid.parquet"); e = pd.read_parquet("data/episodes.parquet")
for df in (g, e):
    df["hour"] = df.ts.dt.hour; df["date"] = df.ts.dt.date
    df["month"] = df.ts.dt.to_period("M").astype(str)
lo, hi = g.ts.min(), g.ts.max()
e = e[(e.ts >= lo) & (e.ts <= hi)].copy()


def matched(ex, gx, keys):
    """izgarayi ex'in `keys` dagilimiyla yeniden agirlikla → (izgaraEV, pulseEV, kapsam)."""
    ec = ex.groupby(keys).agg(pev=("r", "mean"), k=("r", "size")).reset_index()
    gc = gx.groupby(keys).agg(ev=("r", "mean"), gn=("r", "size")).reset_index()
    m = ec.merge(gc, on=keys, how="inner")
    w = m.k.values
    return float((m.ev * w).sum() / w.sum()), float((m.pev * w).sum() / w.sum()), w.sum() / len(ex), m


print("SECIM DEGERI AYRISTIRMA (ortak pencere)")
print(f"{'kontrol':32s} {'BUY':>26s}   {'SELL':>26s}")
specs = [("kontrol yok (ham)", None),
         ("saat", ["hour"]),
         ("ay", ["month"]),
         ("ay x saat", ["month", "hour"]),
         ("hafta(ISO)", ["iso_week"]),
         ("hafta x saat", ["iso_week", "hour"]),
         ("gun", ["date"]),
         ("gun x saat", ["date", "hour"])]
for df in (g, e):
    df["iso_week"] = df.ts.dt.isocalendar().week.astype(int).astype(str) + "-" + df.ts.dt.year.astype(str)

res = {}
for name, keys in specs:
    line = f"{name:32s} "
    for d in ("BUY", "SELL"):
        gx, ex = g[g.direction == d], e[e.direction == d]
        if keys is None:
            gev, pev, cov = gx.r.mean(), ex.r.mean(), 1.0
        else:
            gev, pev, cov, _ = matched(ex, gx, keys)
        res[(name, d)] = (gev, pev, cov)
        line += f"izg{gev:+.4f} pls{pev:+.4f} Δ{pev-gev:+.4f}({cov*100:.0f}%)  "
    print(line)

# ── SELL: aylik katki tablosu (ham secim degeri kimden geliyor) ──────────────
print("\nSELL — AYLIK KATKI (ham secim degerine)")
gref = g[g.direction == "SELL"].r.mean()
ex = e[e.direction == "SELL"]
rows = []
for mo, grp in ex.groupby("month"):
    contrib = len(grp) / len(ex) * (grp.r.mean() - gref)
    gm = g[(g.direction == "SELL") & (g.month == mo)]
    rows.append(dict(ay=mo, n=len(grp), pulseEV=grp.r.mean(), izgaraAy=gm.r.mean(),
                     ham_katki=contrib))
t = pd.DataFrame(rows)
print(t.round(4).to_string(index=False))
print(f"  toplam ham secim degeri = {t.ham_katki.sum():+.4f}R  (mayis harici: "
      f"{t[t.ay!='2026-05'].ham_katki.sum():+.4f}R)")
ex2 = ex[ex.month != "2026-05"]
print(f"  MAYIS CIKARILIRSA: pulse SELL n={len(ex2)} EV={ex2.r.mean():+.4f} vs izgara(mayissiz) "
      f"{g[(g.direction=='SELL')&(g.month!='2026-05')].r.mean():+.4f} → "
      f"Δ={ex2.r.mean()-g[(g.direction=='SELL')&(g.month!='2026-05')].r.mean():+.4f}R")

# ── placebo: pulse zaman damgalarini AYNI GUN icinde karistir ────────────────
print("\nPLACEBO — pulse SELL zamanlarini AYNI GUN icinde rastgele kaydir (B=2000)")
gs = g[g.direction == "SELL"].copy()
by_day_grid = {k: v for k, v in gs.groupby("date")}
by_day_hour = {k: v for k, v in gs.groupby(["date", "hour"])}
obs = ex.r.mean() - gref


def placebo(scope):
    out = np.empty(2000)
    for b in range(2000):
        vals = []
        for r in ex.itertuples(index=False):
            pool = by_day_grid.get(r.date) if scope == "day" else by_day_hour.get((r.date, r.hour))
            if pool is None or len(pool) == 0:
                pool = by_day_grid.get(r.date)
            if pool is None or len(pool) == 0:
                continue
            vals.append(pool.r.values[RNG.integers(len(pool))])
        out[b] = np.mean(vals) - gref
    return out


for scope in ("day", "day+hour"):
    dist = placebo(scope)
    p = float((dist >= obs).mean())
    print(f"  kapsam={scope:9s} gozlenen Δ={obs:+.4f}  placebo ort={dist.mean():+.4f} "
          f"sd={dist.std():.4f}  p(placebo>=gozlenen)={p:.3f}")

# ── model bazinda ────────────────────────────────────────────────────────────
print("\nMODEL BAZINDA (gun x saat esitlenmis)")
for d in ("BUY", "SELL"):
    for mdl in ("pulse1", "pulse2", "pulse3"):
        ex_m = e[(e.direction == d) & (e.model == mdl)]
        if len(ex_m) < 20:
            print(f"  {d} {mdl}: n={len(ex_m)} (az)"); continue
        gev, pev, cov, _ = matched(ex_m, g[g.direction == d], ["date", "hour"])
        gev_h, pev_h, _, _ = matched(ex_m, g[g.direction == d], ["hour"])
        print(f"  {d} {mdl}: n={len(ex_m)} EV={ex_m.r.mean():+.4f} | Δsaat={pev_h-gev_h:+.4f} "
              f"| Δgun×saat={pev-gev:+.4f}")

# ── RTH-only kiyas (en dogal adil kiyas) ────────────────────────────────────
print("\nRTH-ONLY (13:30-20:00 UTC ~ NY seansi) ham kiyas")
for d in ("BUY", "SELL"):
    gx = g[(g.direction == d) & (g.ts.dt.hour >= 13) & (g.ts.dt.hour < 20)]
    ex_ = e[(e.direction == d) & (e.ts.dt.hour >= 13) & (e.ts.dt.hour < 20)]
    print(f"  {d}: izgara n={len(gx)} WR={gx.outcome.mean()*100:.1f} EV={gx.r.mean():+.4f} | "
          f"pulse n={len(ex_)} WR={ex_.outcome.mean()*100:.1f} EV={ex_.r.mean():+.4f} → Δ{ex_.r.mean()-gx.r.mean():+.4f}")
