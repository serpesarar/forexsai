"""Tanı (alg_ozet sonrası): çelişki isabeti, plasebo-geçme oranı, güçlü-oy alt kümeleri, 1g hareketi, yakın kaçanlar.
Çalıştır: python3.13 research/mum_derin_tarama_20261013/algoritmalar/alg_tani.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ORDER = [("1m", "15m"), ("1m", "1h"), ("1m", "1d"), ("5m", "15m"), ("5m", "1h"), ("5m", "1d"),
         ("15m", "15m"), ("15m", "1h"), ("15m", "1d"), ("1h", "1h"), ("1h", "1d")]
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
cfg = pd.read_csv(RES / "tum_yapilandirmalar.csv")
ok = cfg[cfg.n >= 200]

# (1) model tabana karşı çıktığında ne kadar haklı? (tüm yapılandırmalar havuzu, aile bazında)
rows = []
for tf, hz in ORDER:
    z = np.load(RES / f"{tf}_{hz}_q.npz")
    names = [s.split("|") for s in z["names"]]
    qt = z["qt"].astype(int); bm = z["bm"].astype(int); y = z["y"]
    for i, (fam, W, par, K, rule) in enumerate(names):
        if rule != "tum":
            continue
        c = z["calls"][:, i].astype(int); m = c != 0
        if m.sum() < 200:
            continue
        dis = m & (c != bm); agr = m & (c == bm)
        rows.append(dict(tf=tf, hz=hz, fam=fam, n=int(m.sum()), yukari_payi=float((c[m] == 1).mean()),
                         gercek_yukari=float((qt[m] == 1).mean()), n_celiski=int(dis.sum()),
                         celiski_isabet=float((c[dis] == qt[dis]).mean()) if dis.any() else np.nan,
                         celiski_dogal=float((qt[dis] != bm[dis]).mean()) if dis.any() else np.nan,
                         uyum_isabet=float((c[agr] == qt[agr]).mean()) if agr.any() else np.nan,
                         celiski_mv=float((c[dis] * y[dis]).mean()) if dis.any() else np.nan))
D = pd.DataFrame(rows)
g = D.groupby("fam").apply(lambda x: pd.Series(dict(
    yap=len(x), yukari_payi=x.yukari_payi.mean(), gercek_yukari=x.gercek_yukari.mean(),
    celiski_orani=(x.n_celiski / x.n).mean(),
    celiski_isabet=np.average(x.celiski_isabet, weights=x.n_celiski),
    uyum_isabet=x.uyum_isabet.mean(), celiski_mv_pts=np.average(x.celiski_mv, weights=x.n_celiski))))
print("(1) Model çoğunluk tabanına KARŞI çıktığında (çağrı ≠ taban) isabeti — 'tum' kuralı, n≥200 yapılandırmalar:")
print(g.round(4).to_string())
g.to_csv(RES / "tani_celiski.csv")
tot = D.n_celiski.sum(); acc = np.average(D.celiski_isabet, weights=D.n_celiski)
print(f"   havuz: {tot} çelişkili çağrı (yapılandırmalar arası örtüşür), ağırlıklı isabet {acc:.4f}")
th = D.groupby(["tf", "hz"]).apply(lambda x: np.average(x.celiski_isabet, weights=x.n_celiski)).round(4)
print("   TF×ufuk:", th.to_dict())

# (2) plasebo-geçme oranı: tesadüfte 1/21
pb = ok.groupby("fam").plc_beat.agg(["sum", "size"])
pb["oran"] = pb["sum"] / pb["size"]
pb["binom_p_tek"] = [binomtest(int(s), int(n), 1 / 21, alternative="greater").pvalue for s, n in zip(pb["sum"], pb["size"])]
print("\n(2) Plaseboyu (20 tekrarın hepsini) geçen yapılandırma oranı; tesadüf 1/21=0,048 (yapılandırmalar bağımlı → p iyimser):")
print(pb.round(4).to_string())
print("   toplam", int(ok.plc_beat.sum()), "/", len(ok), f"binom p={binomtest(int(ok.plc_beat.sum()), len(ok), 1/21, alternative='greater').pvalue:.3g}")
m_p = (ok.acc - ok.plc_mean)
print(f"   isabet − plasebo ortalaması: tüm {100*m_p.mean():.2f} puan; ufuk bazında",
      (100 * m_p.groupby(ok.hz).mean()).round(2).to_dict(), "; aile bazında", (100 * m_p.groupby(ok.fam).mean()).round(2).to_dict())

# (3) güçlü oy alt kümeleri
gs = cfg[cfg.rule == "guclu"]
print("\n(3) Güçlü-oy (|pay−0,5|≥0,2) yapılandırmaları: toplam", len(gs), "· n≥200:", int((gs.n >= 200).sum()),
      "· n≥200 içinde ort. fark", round(100 * gs[gs.n >= 200].exc.mean(), 2), "puan · ort. isabet",
      round(100 * gs[gs.n >= 200].acc.mean(), 2), "· ort. çoğunluk", round(100 * gs[gs.n >= 200].acc_maj.mean(), 2),
      "· ort. plasebo", round(100 * gs[gs.n >= 200].plc_mean.mean(), 2))
print("   n<200 güçlü yapılandırmalar arasında P≥0,975 & iki yarı +:")
x = gs[(gs.n >= 30) & (gs.n < 200) & (gs.P_boot >= 0.975) & (gs.exc_y1 > 0) & (gs.exc_y2 > 0)]
print(x[["tf", "hz", "fam", "W", "par", "K", "n", "acc", "acc_maj", "acc_hour", "exc", "t", "P_boot", "plc_max", "mv_pts"]].round(4).to_string())
print("   n<200 güçlü yapılandırmalarda P≥0,975 sayısı:", int(((gs.n >= 30) & (gs.n < 200) & (gs.P_boot >= 0.975)).sum()),
      "/", int(((gs.n >= 30) & (gs.n < 200)).sum()), "; P≤0,025:", int(((gs.n >= 30) & (gs.n < 200) & (gs.P_boot <= 0.025)).sum()))

# (4) 1 günlük ufukta hareket: model vs taban
d1 = ok[ok.hz == "1d"]
print("\n(4) 1g ufku (n≥200): ort. tahmin yönünde hareket model", round(d1.mv_pts.mean(), 2), "puan, taban", round(d1.mv_base_pts.mean(), 2),
      "puan; model>taban yapılandırma", int((d1.mv_pts > d1.mv_base_pts).sum()), "/", len(d1))
sh = ok[ok.hz != "1d"]
print("    kısa ufuklar: model", round(sh.mv_pts.mean(), 2), "taban", round(sh.mv_base_pts.mean(), 2), "puan; >1,5 puan:",
      int((sh.mv_pts > 1.5).sum()), "/", len(sh), "; mutlak hareket ort.", sh.groupby("hz").abs_y_pts.mean().round(1).to_dict())

# (5) ön-kayıt ölçütlerinin en çoğunu geçenler
print("\n(5) En çok ölçüt geçen 10 yapılandırma (n≥200):")
print(ok.sort_values(["gecen_olcut", "t"], ascending=False).head(10)[
    ["tf", "hz", "fam", "W", "par", "K", "rule", "n", "acc", "acc_maj", "acc_hour", "exc", "P_boot", "exc_y1", "exc_y2",
     "plc_mean", "plc_max", "mv_pts", "p_adj_maxT", "gecen_olcut"]].round(4).to_string())

# (6) ngram 15m/15m a3w6 güçlü komşu parametreler (yakın kaçan, n<200)
nb = cfg[(cfg.fam == "ngram") & (cfg.tf == "15m") & (cfg.hz == "15m")]
print("\n(6) ngram 15m/15m tüm parametreler:")
print(nb[["par", "rule", "n", "acc", "acc_maj", "acc_hour", "exc", "t", "P_boot", "exc_y1", "exc_y2", "plc_max"]].round(4).to_string())
nb2 = cfg[(cfg.fam == "ngram") & (cfg.par == "a3w6") & (cfg.rule == "guclu")]
print("    aynı ngram a3w6 güçlü, diğer TF×ufuk:")
print(nb2[["tf", "hz", "n", "acc", "acc_maj", "exc", "P_boot", "exc_y1", "exc_y2"]].round(4).to_string())
