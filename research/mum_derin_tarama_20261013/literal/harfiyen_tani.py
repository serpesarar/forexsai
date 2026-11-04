"""Harfiyen tanım (%0,015 birebir) 1m eşleşmelerinin hangi anlarda bulunduğu: saat, sorgu mumu boyu, uygunluk.
SONUÇ (gelecek fiyat) KULLANMAZ, yalnız Faz B eşleşme sayıları. Çalıştır: python3 harfiyen_tani.py"""
import numpy as np, pandas as pd
from _lit import RES, XS, load
D = load("1m"); Z = np.load(RES / "scan" / "1m_2.npz"); qs = Z["qs"]          # TOLS[2] = pct 0.015
rng_q = np.array([np.median(D["pct"][q - 9:q + 1, 0] - D["pct"][q - 9:q + 1, 1]) for q in qs])
hr = D["hour"][qs]
rows = []
for xi, X in enumerate(XS):
    has = Z["nind"][:, 0, xi, 0, 0] > 0
    rows.append(dict(X=int(X), sorgu=len(qs), eslesmeli=int(has.sum()), pay=round(has.mean(), 3),
                     eslesmeli_medyan_mum_boyu=round(float(np.median(rng_q[has])), 4) if has.any() else np.nan,
                     eslesmesiz_medyan_mum_boyu=round(float(np.median(rng_q[~has])), 4),
                     eslesmeli_asya_payi=round(float(((hr[has] >= 23) | (hr[has] < 7)).mean()), 3) if has.any() else np.nan,
                     tum_sorgu_asya_payi=round(float(((hr >= 23) | (hr < 7)).mean()), 3),
                     eslesmeli_uygun_pay=round(float(Z["qelig"][has, xi].mean()), 3) if has.any() else np.nan))
o = pd.DataFrame(rows); print(o.to_string()); o.to_csv(RES / "harfiyen_1m_tani.csv", index=False)
print("1m sorgu-penceresi medyan mum boyu (10 mum) — tüm sorgular: %.4f%%; 3×0,015 = 0,045%% eşiğini geçen sorgu payı: %.3f"
      % (np.median(rng_q), np.mean(rng_q >= 0.045)))
