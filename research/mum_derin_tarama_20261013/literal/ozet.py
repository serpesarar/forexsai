"""Özet tablolar (aile.csv, fizibilite.csv, null_max.csv, aday_eleme.csv) → results/ozet_*.csv + ekrana."""
import numpy as np, pandas as pd
from _lit import RES
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 300)
F = pd.read_csv(RES / "fizibilite.csv"); A = pd.read_csv(RES / "aile.csv"); N = pd.read_csv(RES / "null_max.csv")
E = pd.read_csv(RES / "aday_eleme.csv")
TFO = ["1m", "5m", "15m", "1h"]

print("=== 1. FİZİBİLİTE — harfiyen tanım (%0,015, birebir), bağımsız eşleşme, ufuk 1h ===")
for el in (False, True):
    g = F[(F.rep == "pct") & (F.tol == 0.015) & (F.kural == "birebir") & (F.uygunluk == el) & (~F.seans) & (F.ufuk == "1h")]
    t = g.set_index(["tf", "X"])[["uygun_sorgu", "bag_med", "bag_p75", "bag_p90", "ham_p90", "pay_ge1", "pay_ge30"]]
    print(f"-- uygunluk={el}"); print(t.round(3).to_string())
    t.to_csv(RES / f"ozet_fiz_harfiyen_uyg{int(el)}.csv")

print("\n=== 1b. En uzun X: sorguların ≥%50'sinde ≥30 bağımsız eşleşme (ufuk 1h; seans kapalı) ===")
g = F[(~F.seans) & (F.ufuk == "1h")].copy()
g["ok"] = g.pay_ge30 >= 0.5
xm = g[g.ok].groupby(["tf", "rep", "tol", "kural", "uygunluk"]).X.max().unstack("kural")
xm = xm.reindex(columns=["birebir", "%90_son1", "%80_son1", "%70_son1", "%70_son3"])
print(xm.to_string()); xm.to_csv(RES / "ozet_fiz_xmax.csv")

print("\n=== 2. HARFİYEN İLERİ TEST (%0,015 birebir, uygunluk/seans kapalı, n_min=1, güçlü oy yok) ===")
g = A[(A.rep == "pct") & (A.tol == 0.015) & (A.kural == "birebir") & (~A.uygunluk) & (~A.seans) & (A.n_min == 1) & (~A.guclu_oy)]
cols = ["tf", "ufuk", "X", "uygun_sorgu", "cagri", "bag_olay", "ort_komsu", "isabet", "taban_cogunluk", "taban_saat", "fazla", "hareket_puan"]
g = g[g.cagri > 0][cols].sort_values(["tf", "ufuk", "X"]); print(g.round(2).to_string()); g.to_csv(RES / "ozet_harfiyen_ileri.csv", index=False)
g2 = A[(A.rep == "pct") & (A.tol == 0.015) & (A.kural == "birebir") & (A.uygunluk) & (A.n_min == 1) & (~A.guclu_oy) & (A.cagri > 0)]
print("-- uygunluk açık:"); print(g2[cols + ["seans"]].round(2).to_string())

act = A[A.cid.notna()].copy()
print(f"\n=== 3. AİLE: {len(A)} yapılandırma, {len(act)} aktif (≥200 bağımsız olay) ===")
real_best = act.fazla.max(); q95 = N.max_fazla.quantile(0.95)
act["z"] = act.fazla / 100 / (0.5 / np.sqrt(act.bag_olay))
print(f"gerçek en iyi fazla {real_best:.2f} puan; null max %50/%95/%99 = {N.max_fazla.quantile(.5):.2f}/{q95:.2f}/{N.max_fazla.quantile(.99):.2f}; "
      f"p = {(N.max_fazla >= real_best).mean():.3f}")
print(f"gerçek en iyi z {act.z.max():.2f}; null max_z %95 = {N.max_z.quantile(.95):.2f}; p = {(N.max_z >= act.z.max()).mean():.3f}")
for tf in TFO:
    a = act[act.tf == tf]
    if len(a):
        print(f"  {tf}: aktif {len(a)}, en iyi {a.fazla.max():.2f}, null %95 (yalnız {tf}) {N[f'max_fazla_{tf}'].quantile(.95):.2f}, "
              f"p = {(N[f'max_fazla_{tf}'] >= a.fazla.max()).mean():.3f}")
print("ölçüt merdiveni (aktif):")
m = {"≥200 olay": np.ones(len(act), bool)}
m["fazla ≥ 2"] = act.fazla >= 2
m["+ iki yarı > 0"] = m["fazla ≥ 2"] & (act.yari1 > 0) & (act.yari2 > 0)
m["+ hareket > 1,5"] = m["+ iki yarı > 0"] & (act.hareket_puan > 1.5)
for k, v in m.items():
    print(f"  {k}: {int(v.sum())}")
print("  + plasebo + bootstrap ≥ 0,975 (aday, seçim düzeltmesi öncesi):", int(E.aday.sum()))
print("  + seçim düzeltmesi (fazla > null max %95):", int((E.aday & (E.fazla > q95)).sum()))

print("\n=== 4. Ayar yönleri — aktif yapılandırmalarda ortalama fazla (puan) ===")
for col in ("X", "tol", "kural", "uygunluk", "seans", "guclu_oy", "n_min", "ufuk", "tf"):
    t = act.groupby(col).agg(yapi=("fazla", "size"), ort_fazla=("fazla", "mean"), med_fazla=("fazla", "median"),
                             pay_ge2=("fazla", lambda x: (x >= 2).mean()), ort_isabet=("isabet", "mean"))
    print(f"-- {col}"); print(t.round(3).to_string())
key = ["tf", "rep", "tol", "X", "kural", "uygunluk", "seans", "ufuk", "n_min"]
pv = A[A.cagri >= 100].pivot_table(index=key, columns="guclu_oy", values=["fazla", "isabet", "cagri"]).dropna()
print("-- eşli: güçlü oy (≥%70) − düz oy, aynı yapılandırma (çağrı ≥100 ikisinde de):",
      f"n={len(pv)}, fazla farkı ort {(pv[('fazla', True)] - pv[('fazla', False)]).mean():.2f}, medyan {(pv[('fazla', True)] - pv[('fazla', False)]).median():.2f}, "
      f"isabet farkı ort {(pv[('isabet', True)] - pv[('isabet', False)]).mean():.2f}")
cal = pd.read_csv(RES / "null_kalibrasyon.csv"); print("\n=== 5. null kalibrasyonu ==="); print(cal.round(2).to_string())
