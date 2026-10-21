"""Adım 5: mutlak EV için aile-bazlı düzeltme (White RC tarzı): 8 kural × 3 geometri = 24 test/yön, ortak gün-blok
bootstrap (aynı gün seçimi tüm testlere), merkezlenmiş max-t. Ayrıca Bonferroni z* (24 ve 48 test).
Çıktı: results/05_reality_check.txt"""
import numpy as np
import pandas as pd
import rules_lib as L

HERE = L.HERE; OUT = HERE / "results"
from scipy_free import norm_ppf

GN = list(L.GEOMS)
S = pd.read_pickle(HERE / "sim_decider.pkl"); S["day"] = S.day.astype(str)
RULES_BUY = {"R1": lambda d: d.trig_sign > 0, "R2": lambda d: d.eq_block_buy == False,  # noqa: E712
             "R3": lambda d: d.h1_above_ema50 == True, "R4": lambda d: d.d1_up == True,  # noqa: E712
             "R5": lambda d: d.sess_ldn_ny == True, "R6": lambda d: d.atr5_ratio < 1.5,  # noqa: E712
             "R7": lambda d: d.dist_hi20_h1_atr <= 1.0, "R8": lambda d: d.size_factor >= 0.2}
rng = np.random.default_rng(11)
lines = []
def P(s=""): lines.append(str(s)); print(s)

B = S[S.direction == "BUY"].reset_index(drop=True)
u, inv = np.unique(B.day.values, return_inverse=True)
keys, sums, cnts = [], [], []
for rn, fn in RULES_BUY.items():
    m = fn(B).fillna(False).astype(bool).values
    for g in GN:
        v = np.where(m, B[g].values, 0.0)
        sums.append(np.bincount(inv, weights=v, minlength=len(u)))
        cnts.append(np.bincount(inv, weights=m.astype(float), minlength=len(u)))
        keys.append((rn, g))
Ssum, Scnt = np.array(sums), np.array(cnts)            # [24, ndays]
obs = Ssum.sum(1) / Scnt.sum(1)
NB = 4000
W = rng.multinomial(len(u), np.ones(len(u)) / len(u), size=NB).astype(float)   # [NB, ndays]
bm = (W @ Ssum.T) / (W @ Scnt.T)                     # [NB, 24]
sd = bm.std(0, ddof=1)
t = obs / sd
tmax = np.max((bm - obs[None, :]) / sd[None, :], axis=1)
P(f"BUY: 24 test | Bonferroni z*(24)={norm_ppf(1-0.05/24):.2f}, z*(48)={norm_ppf(1-0.05/48):.2f}")
for k, (rn, g) in enumerate(keys):
    p_rc = float((tmax >= t[k]).mean())
    P(f"  {rn} {g:20s} EV {obs[k]:+.3f} t(gün) {t[k]:+.2f} | RC p {p_rc:.3f}")
(OUT / "05_reality_check.txt").write_text("\n".join(lines))
