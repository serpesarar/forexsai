"""audit_claimB.py — IDDIA B skeptik denetimi: pulse SELL 'secim degeri' gercek mi?

Testler:
 1. Ham kiyas (iddianin kendisi) — yeniden uretim
 2. SAAT-esitlenmis kiyas (post-stratification: izgara, epizodlarin UTC saat dagilimiyla agirliklanir)
 3. (GUN x SAAT) hucre-esitlenmis kiyas — ayni gunun ayni saatinde izgara ne yapiyordu?
 4. Epizod kuralinin (ayni anda 1 pozisyon) izgaraya uygulanmasi
 5. GUN-bloklu bootstrap (secim degeri icin %5-95 araligi)
 6. Ay bazinda ayristirma
 7. Ortak zaman penceresi kontrolu
"""
from __future__ import annotations
import numpy as np, pandas as pd

RNG = np.random.default_rng(7)

g = pd.read_parquet("data/grid.parquet")
e = pd.read_parquet("data/episodes.parquet")

for df in (g, e):
    df["hour"] = df.ts.dt.hour
    df["date"] = df.ts.dt.date
    df["month"] = df.ts.dt.to_period("M").astype(str)

# ── ortak pencere ──────────────────────────────────────────────────────────
lo, hi = g.ts.min(), g.ts.max()
e_all = e.copy()
e = e[(e.ts >= lo) & (e.ts <= hi)].copy()
print(f"[0] ortak pencere {lo} → {hi}")
print(f"    epizod: {len(e_all)} → {len(e)} (pencere disi {len(e_all)-len(e)})")


def stat(x):
    return len(x), x.outcome.mean() * 100, x.r.mean()


print("\n[1] HAM KIYAS (iddianin kendisi)")
base = {}
for d in ("BUY", "SELL"):
    gx, ex = g[g.direction == d], e[e.direction == d]
    n1, w1, v1 = stat(gx); n2, w2, v2 = stat(ex)
    base[d] = (v1, v2)
    print(f"  {d}: izgara n={n1} WR={w1:.1f}% EV={v1:+.4f} | pulse n={n2} WR={w2:.1f}% EV={v2:+.4f}"
          f"  → secim degeri {v2-v1:+.4f}R")

# ── 2. saat-esitlenmis izgara ───────────────────────────────────────────────
print("\n[2] SAAT-ESITLENMIS (izgara, epizod saat dagilimiyla yeniden agirliklanir)")
hour_match = {}
for d in ("BUY", "SELL"):
    gx, ex = g[g.direction == d], e[e.direction == d]
    w = ex.hour.value_counts(normalize=True)
    gm = gx.groupby("hour").agg(ev=("r", "mean"), wr=("outcome", "mean"), n=("r", "size"))
    common = w.index.intersection(gm.index)
    ww = w.loc[common] / w.loc[common].sum()
    ev = float((gm.ev.loc[common] * ww).sum())
    wr = float((gm.wr.loc[common] * ww).sum()) * 100
    hour_match[d] = ev
    print(f"  {d}: izgara(saat-esit) WR={wr:.1f}% EV={ev:+.4f} | pulse EV={ex.r.mean():+.4f}"
          f"  → secim degeri {ex.r.mean()-ev:+.4f}R")

# ── 3. (gun x saat) hucre esitlemesi ────────────────────────────────────────
print("\n[3] (GUN x SAAT) HUCRE-ESITLENMIS — ayni gun, ayni saat")
cell_match = {}
for d in ("BUY", "SELL"):
    gx, ex = g[g.direction == d], e[e.direction == d]
    gc = gx.groupby(["date", "hour"]).agg(ev=("r", "mean"), wr=("outcome", "mean"),
                                          n=("r", "size")).reset_index()
    ec = ex.groupby(["date", "hour"]).agg(pev=("r", "mean"), pwr=("outcome", "mean"),
                                          k=("r", "size")).reset_index()
    m = ec.merge(gc, on=["date", "hour"], how="inner")
    cov = m.k.sum() / len(ex)
    gev = float((m.ev * m.k).sum() / m.k.sum())
    gwr = float((m.wr * m.k).sum() / m.k.sum()) * 100
    pev = float((m.pev * m.k).sum() / m.k.sum())
    pwr = float((m.pwr * m.k).sum() / m.k.sum()) * 100
    cell_match[d] = (gev, pev, m)
    print(f"  {d}: eslesen epizod {m.k.sum()}/{len(ex)} (kapsam {cov*100:.0f}%), hucre={len(m)}")
    print(f"      izgara(hucre-esit) WR={gwr:.1f}% EV={gev:+.4f} | pulse WR={pwr:.1f}% EV={pev:+.4f}"
          f"  → secim degeri {pev-gev:+.4f}R")

# ── 4. epizod kuralini izgaraya uygula ──────────────────────────────────────
print("\n[4] EPIZOD KURALI IZGARAYA UYGULANDI (ayni anda 1 pozisyon)")
b1 = pd.read_csv("data/bars_1m.csv")
b1["ts"] = pd.to_datetime(b1["ts"], utc=True)
ts1m = b1["ts"].dt.tz_convert("UTC")
epi_grid = {}
for d in ("BUY", "SELL"):
    gx = g[g.direction == d].sort_values("ts").reset_index(drop=True)
    open_until = None
    idx = []
    for i, r in enumerate(gx.itertuples(index=False)):
        if open_until is not None and r.ts < open_until:
            continue
        idx.append(i)
        open_until = ts1m.iloc[int(r.exit_i)]
    ge = gx.iloc[idx]
    epi_grid[d] = ge
    n, w, v = stat(ge)
    print(f"  {d}: izgara-epizod n={n} WR={w:.1f}% EV={v:+.4f}"
          f" | pulse EV={e[e.direction==d].r.mean():+.4f}"
          f"  → secim degeri {e[e.direction==d].r.mean()-v:+.4f}R")

# ── 4b. epizod kurali + saat esitlemesi birlikte ────────────────────────────
print("\n[4b] IZGARA-EPIZOD + SAAT ESITLEMESI")
for d in ("BUY", "SELL"):
    ge, ex = epi_grid[d], e[e.direction == d]
    w = ex.hour.value_counts(normalize=True)
    gm = ge.groupby("hour").agg(ev=("r", "mean"), wr=("outcome", "mean"), n=("r", "size"))
    common = w.index.intersection(gm.index)
    ww = w.loc[common] / w.loc[common].sum()
    ev = float((gm.ev.loc[common] * ww).sum())
    print(f"  {d}: izgara-epizod(saat-esit) EV={ev:+.4f} | pulse EV={ex.r.mean():+.4f}"
          f"  → secim degeri {ex.r.mean()-ev:+.4f}R   (kapsanan saat {len(common)})")

# ── 5. gun-bloklu bootstrap ─────────────────────────────────────────────────
print("\n[5] GUN-BLOKLU BOOTSTRAP (B=4000) — secim degeri = pulseEV - izgaraEV(hucre-esit)")


def dayblock_boot(pairs_by_day, B=4000):
    """pairs_by_day: {gun: (pulse_r_array, grid_r_array_agirlikli)}"""
    days = list(pairs_by_day.keys())
    out = np.empty(B)
    for b in range(B):
        pick = RNG.choice(len(days), size=len(days), replace=True)
        pr, gr, wt = [], [], []
        for i in pick:
            p, q, k = pairs_by_day[days[i]]
            pr.append(p); gr.append(q); wt.append(k)
        pr = np.concatenate(pr); gr = np.concatenate(gr)
        out[b] = pr.mean() - gr.mean()
    return out


for d in ("BUY", "SELL"):
    gev, pev, m = cell_match[d]
    # gun bazinda: o gunun eslesen hucrelerindeki pulse r'leri ve k-agirlikli izgara ev'leri
    by_day = {}
    for day, grp in m.groupby("date"):
        p = np.repeat(grp.pev.values, grp.k.values)
        q = np.repeat(grp.ev.values, grp.k.values)
        by_day[day] = (p, q, grp.k.values)
    dist = dayblock_boot(by_day)
    lo5, hi95 = np.percentile(dist, [5, 95])
    lo2, hi97 = np.percentile(dist, [2.5, 97.5])
    print(f"  {d}: gun sayisi={len(by_day)}  nokta={pev-gev:+.4f}R"
          f"  %5-95=[{lo5:+.4f}, {hi95:+.4f}]  %2.5-97.5=[{lo2:+.4f}, {hi97:+.4f}]"
          f"  P(>0)={float((dist>0).mean())*100:.1f}%")

# ham (esitlenmemis) secim degeri icin de gun-bloklu bootstrap
print("\n[5b] HAM secim degeri icin gun-bloklu bootstrap (izgara sabit referans)")
for d in ("BUY", "SELL"):
    ex = e[e.direction == d]
    gref = g[g.direction == d].r.mean()
    days = ex.date.unique()
    grp = {k: v.r.values for k, v in ex.groupby("date")}
    out = np.empty(4000)
    for b in range(4000):
        pick = RNG.choice(len(days), size=len(days), replace=True)
        out[b] = np.concatenate([grp[days[i]] for i in pick]).mean() - gref
    lo5, hi95 = np.percentile(out, [5, 95])
    print(f"  {d}: gun={len(days)} nokta={ex.r.mean()-gref:+.4f} %5-95=[{lo5:+.4f},{hi95:+.4f}]"
          f" P(>0)={float((out>0).mean())*100:.1f}%")

# ── 6. ay bazinda ────────────────────────────────────────────────────────────
print("\n[6] AY BAZINDA (SELL)")
for d in ("SELL", "BUY"):
    print(f"  --- {d}")
    rows = []
    for mo in sorted(e.month.unique()):
        ex = e[(e.direction == d) & (e.month == mo)]
        gx = g[(g.direction == d) & (g.month == mo)]
        if len(ex) == 0 or len(gx) == 0:
            continue
        w = ex.hour.value_counts(normalize=True)
        gm = gx.groupby("hour").agg(ev=("r", "mean"))
        c = w.index.intersection(gm.index)
        ww = w.loc[c] / w.loc[c].sum()
        gev_h = float((gm.ev.loc[c] * ww).sum())
        rows.append(dict(ay=mo, n=len(ex), pulseEV=ex.r.mean(), gridEV=gx.r.mean(),
                         gridEV_saat=gev_h, secim_ham=ex.r.mean() - gx.r.mean(),
                         secim_saat=ex.r.mean() - gev_h))
    print(pd.DataFrame(rows).round(4).to_string(index=False))
