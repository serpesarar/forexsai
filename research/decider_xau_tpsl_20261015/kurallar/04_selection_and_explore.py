"""Adım 4: (a) ön-kayıtlı seçim-alfası analizleri (Soru 5), (b) KEŞİF (ön-kayıt sonrası, verdikt almaz):
R1 ay/yarı kırılımı, R2'nin D2-dondurma (09-14) sonrası örneklem-dışı dilimi, R1 içinde D2, icra alt kümesi.
Çıktı: results/04_selection_explore.txt"""
import numpy as np
import pandas as pd
import rules_lib as L

HERE = L.HERE; OUT = HERE / "results"
GN = list(L.GEOMS)
rng = np.random.default_rng(7)
S = pd.read_pickle(HERE / "sim_decider.pkl"); S["day"] = S.day.astype(str)
C3 = pd.read_pickle(HERE / "sim_c3.pkl")
C3 = C3[~C3.gap240].copy()
lines = []
def P(s=""): lines.append(str(s)); print(s)


def boot_days(df: pd.DataFrame, fn, B: int = 3000) -> np.ndarray:
    days = df.day.unique(); out = np.empty(B)
    g = {d: x for d, x in df.groupby("day")}
    for b in range(B):
        pick = rng.choice(days, len(days), replace=True)
        out[b] = fn(pd.concat([g[d] for d in pick]))
    return out


def spearman(a, b):
    ra, rb = pd.Series(a).rank().values, pd.Series(b).rank().values
    return float(np.corrcoef(ra, rb)[0, 1])


B = S[S.direction == "BUY"].copy()
P("=== (i) size_factor ↔ R (BUY, n=%d)" % len(B))
for g in GN:
    rho = spearman(B.size_factor, B[g])
    bt = boot_days(B, lambda d: spearman(d.size_factor, d[g]), 2000)
    P(f"  {g}: Spearman {rho:+.3f} [%95 {np.percentile(bt,2.5):+.3f},{np.percentile(bt,97.5):+.3f}]")
P("=== (ii) lot kademesine göre EV (BUY)")
B["lot_k"] = B.lot_rule.round(2)
for g in GN:
    P(f"  {g}: " + " | ".join(f"lot {k}: n={len(x)} EV {x[g].mean():+.3f}" for k, x in B.groupby("lot_k")))
P("  size_factor çeyrekleri (G1/G2): " + " | ".join(
    f"{iv}: n={len(x)} {x[GN[0]].mean():+.3f}/{x[GN[1]].mean():+.3f}" for iv, x in B.groupby(pd.qcut(B.size_factor, 4, duplicates='drop'), observed=True)))
P("  $ toplamı gerçek lot vs sabit 0,01 lot (G1): %+.1f$ vs %+.1f$" % ((B[GN[0] + '_usd_oz'] * B.lot_rule * 100).sum(), B[GN[0] + '_usd_oz'].sum()))

P("\n=== (iii) OPEN BUY vs aynı günlerdeki OPEN-olmayan danışmalar (C3, BUY simüle, extremity ≥1,6)")
o = C3[(C3.action == "OPEN") & (C3.direction == "BUY")].copy(); w = C3[C3.action != "OPEN"].copy()
common = sorted(set(o.day) & set(w.day))
o2, w2 = o[o.day.isin(common)], w[w.day.isin(common)]
P(f"  ortak gün {len(common)} | OPEN BUY n={len(o2)} | OPEN-olmayan n={len(w2)} (sahte WAIT {int(w2.fake_wait.sum())}, gerçek WAIT {int((~w2.fake_wait).sum())})")
both = pd.concat([o2.assign(grp="O"), w2.assign(grp="W")])
for g in GN:
    diff = o2[g].mean() - w2[g].mean()
    bt = boot_days(both, lambda d: d[d.grp == "O"][g].mean() - d[d.grp == "W"][g].mean())
    P(f"  {g}: OPEN {o2[g].mean():+.3f} vs OPEN-olmayan {w2[g].mean():+.3f} → fark {diff:+.3f} [%95 {np.nanpercentile(bt,2.5):+.3f},{np.nanpercentile(bt,97.5):+.3f}] P(>0) {np.nanmean(bt>0):.2f}")
P("  aylara göre (G1/G2) OPEN vs OPEN-olmayan:")
for m, x in both.groupby(both.ts.dt.strftime("%m")):
    a, b_ = x[x.grp == "O"], x[x.grp == "W"]
    P(f"    {m}: OPEN n={len(a)} {a[GN[0]].mean():+.3f}/{a[GN[1]].mean():+.3f} | OPEN-olmayan n={len(b_)} {b_[GN[0]].mean():+.3f}/{b_[GN[1]].mean():+.3f}")
P("=== (iv) gerçek WAIT (model seçti) vs sahte WAIT (CLI hatası, seçim yok) — BUY simüle")
for g in GN:
    gw, fw = w[~w.fake_wait], w[w.fake_wait]
    P(f"  {g}: gerçek WAIT n={len(gw)} {gw[g].mean():+.3f} | sahte WAIT n={len(fw)} {fw[g].mean():+.3f} | dönemler gerçek {gw.ts.min():%m-%d}→{gw.ts.max():%m-%d}, sahte {fw.ts.min():%m-%d}→{fw.ts.max():%m-%d}")
P("=== (v) yön seçimi: decider SELL açtığında aynı an BUY olsaydı (C3 BUY simüle) vs SELL'in kendi R'si")
sel = S[S.direction == "SELL"].merge(C3[["id"] + GN].rename(columns={g: g + "_buycf" for g in GN}), on="id", how="inner")
for g in GN:
    P(f"  {g}: n={len(sel)} SELL {sel[g].mean():+.3f} | aynı an BUY-cf {sel[g + '_buycf'].mean():+.3f}")

# ---------------- KEŞİF
P("\n##### KEŞİF (ön-kayıt sonrası; verdikt almaz)")
B["m"] = B.ts.dt.strftime("%m"); B["R1"] = B.trig_sign > 0
P("R1 (güç tetik) ay kırılımı — G1/G2: güç vs dip")
for m, x in B.groupby("m"):
    a, b_ = x[x.R1], x[~x.R1]
    P(f"  {m}: güç n={len(a)} {a[GN[0]].mean():+.3f}/{a[GN[1]].mean():+.3f} | dip n={len(b_)} {b_[GN[0]].mean():+.3f}/{b_[GN[1]].mean():+.3f}")
P("R1 × D2 (G1/G2):")
for (r1, eq), x in B.groupby(["R1", "eq_block_buy"]):
    P(f"  güç={r1} D2-blok={eq}: n={len(x)} {x[GN[0]].mean():+.3f}/{x[GN[1]].mean():+.3f}")
P("R1 icra edilen (Ekim demo) vs gölge (G1/G2):")
for (r1, ex), x in B.groupby(["R1", "executed"]):
    P(f"  güç={r1} icra={ex}: n={len(x)} {x[GN[0]].mean():+.3f}/{x[GN[1]].mean():+.3f}")
post = B[B.ts >= pd.Timestamp("2026-09-14", tz="UTC")]
P(f"R2 (D2) 09-14 SONRASI (D2 için örneklem-dışı) n={len(post)} gün {post.day.nunique()}:")
for g in GN:
    a, b_ = post[post.eq_block_buy == False], post[post.eq_block_buy == True]  # noqa: E712
    P(f"  {g}: D2-temiz n={len(a)} {a[g].mean():+.3f} | D2-blok n={len(b_)} {b_[g].mean():+.3f}")
pre = B[B.ts < pd.Timestamp("2026-09-14", tz="UTC")]
for g in GN[:2]:
    a, b_ = pre[pre.eq_block_buy == False], pre[pre.eq_block_buy == True]  # noqa: E712
    P(f"  ÖNCESİ {g}: D2-temiz n={len(a)} {a[g].mean():+.3f} | D2-blok n={len(b_)} {b_[g].mean():+.3f}")
P("R1 C3 OPEN-olmayanlarda aylara göre (G2): " + " | ".join(
    f"{m}: güç n={int((x.trig_sign>0).sum())} {x[x.trig_sign>0][GN[1]].mean():+.3f} dip {x[x.trig_sign<0][GN[1]].mean():+.3f}" for m, x in w.groupby(w.ts.dt.strftime('%m'))))
P("R7 C3 OPEN-olmayanlarda aylara göre (G2): " + " | ".join(
    f"{m}: yakın n={int((x.dist_hi20_h1_atr<=1).sum())} {x[x.dist_hi20_h1_atr<=1][GN[1]].mean():+.3f} uzak {x[x.dist_hi20_h1_atr>1][GN[1]].mean():+.3f}" for m, x in w.groupby(w.ts.dt.strftime('%m'))))
P("R7 decider BUY aylara göre (G2): " + " | ".join(
    f"{m}: yakın n={int((x.dist_hi20_h1_atr<=1).sum())} {x[x.dist_hi20_h1_atr<=1][GN[1]].mean():+.3f} uzak {x[x.dist_hi20_h1_atr>1][GN[1]].mean():+.3f}" for m, x in B.groupby('m')))
(OUT / "04_selection_explore.txt").write_text("\n".join(lines))
