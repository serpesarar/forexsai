"""OF07 keşif: büyük işlem / 1 s patlama (2026-04-20→10-20, yalnız BLIND içi; karta ulaşamaz).

Sabit geometri S1, ρ=1, H=30; iki mod; seçim yok. Kontrol: OF01 W1 θ3 aynı dönem.
Ayrıca 1 s yolla seçilen hücrelerin aynı-bar belirsizliğini çözmek için yardımcı yok (amb oranı zaten raporlanıyor).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofl  # noqa: E402

N = ofl.N
df = ofl.load_frame(cols=["agg_large_buy_qty", "agg_large_sell_qty", "agg_max_1s_buy_qty", "agg_max_1s_sell_qty",
                          "agg_max_agg_qty", "agg_buy_qty", "agg_sell_qty"])
g = ofl.build_grid(df)
fc_next, blocked = ofl.rollover_cap()
hcap = fc_next - np.arange(N)
entry_ok = ofl.valid_entries(g) & ~blocked & (hcap >= 5)
atr5 = ofl.lib.atr_5m(g)
entry_ok &= ~np.isnan(atr5)
a0, a1 = ofl.SEG["DISC"]
absret = np.abs(np.diff(np.log(g["close_ff"]), prepend=np.nan)) * 1e4
slip_thr = float(np.nanpercentile(absret[a0:a1], 99))
eng = ofl.Engine(g, atr5, entry_ok, hcap, slip_thr)
E = np.where(entry_ok)[0]
P0, P1 = ofl.lib.tmin("2026-04-20"), ofl.lib.tmin("2026-10-21")
YR, HR = ofl.year_hour(np.arange(N))
YH = (YR - 2021) * 24 + HR
DAY = np.arange(N) // 1440
GEOM = ("S1", 1.0, 30)

# kova ortalamaları yalnız bu dönemdeki girişlerden (aynı saat; yıl tek)
Ep = E[(E >= P0) & (E < P1)]
RFp, MUp = {}, {}
for s in (1, -1):
    o = eng.outcome(Ep, np.full(len(Ep), s, dtype=np.int8), GEOM)
    r, _ = ofl.net_R(o, "PEP")
    a = np.full(N, np.nan)
    a[Ep] = r
    RFp[s] = a
    MUp[s] = np.bincount(HR[Ep], weights=r, minlength=24) / np.maximum(np.bincount(HR[Ep], minlength=24), 1)

W7 = 10080


def z7(x):
    s = pd.Series(x)
    return ((s - s.rolling(W7, min_periods=W7).mean().shift(1)) / s.rolling(W7, min_periods=W7).std().shift(1)).to_numpy()


lb = df["agg_large_buy_qty"].to_numpy().astype(float)
ls = df["agg_large_sell_qty"].to_numpy().astype(float)
mb = df["agg_max_1s_buy_qty"].to_numpy().astype(float)
ms = df["agg_max_1s_sell_qty"].to_numpy().astype(float)
pz = df["perp_zero_vol"].to_numpy()
inper = np.zeros(N, dtype=bool)
inper[P0:P1] = True
eok = entry_ok & inper
sigs = {}
zl = z7(lb - ls)
sigs["OF07a_large_net_z3"] = (np.sign(zl), np.abs(zl) >= 3)
zb = z7(mb - ms)
sigs["OF07b_burst_net_z3"] = (np.sign(zb), np.abs(zb) >= 3)
vp = df["perp_volume"].to_numpy().astype(float)
dp = 2 * df["perp_taker_buy_base"].to_numpy().astype(float) - vp
zd = ofl.zpast(dp)
sigs["OF07c_ctrl_OF01_W1_th3"] = (np.sign(zd), (np.abs(zd) >= 3) & (pz == 0))
# ek tanımlayıcı: (a) ∧ ¬(c) — büyük işlem sinyali 1m delta'nın ötesinde bilgi taşıyor mu
sigs["OF07d_large_not_ctrl"] = (np.sign(zl), (np.abs(zl) >= 3) & ~(np.abs(zd) >= 3))

rows = []
rng = np.random.default_rng(9)
for name, (dr, cond) in sigs.items():
    t, d = ofl.events_from_dir(dr, cond & inper, eok)
    for mode in (1, -1):
        e = t + 1
        sd = (d * mode).astype(np.int8)
        o = eng.outcome(e, sd, GEOM)
        r, bp = ofl.net_R(o, "PEP")
        x = r - np.where(sd == 1, MUp[1][HR[e]], MUp[-1][HR[e]])
        m, se, z = ofl.cluster_z(x, DAY[e])
        pe, lo, hi = ofl.day_boot(r, DAY[e], 2000)
        # plasebo: aynı saat, aynı yön, aynı dönem
        B = 1000
        tot = np.zeros(B)
        for h in np.unique(HR[e]):
            idx = np.where(HR[e] == h)[0]
            C = Ep[HR[Ep] == h]
            drw = C[rng.integers(0, len(C), size=(B, len(idx)))]
            tot += np.where(sd[idx][None, :] == 1, RFp[1][drw], RFp[-1][drw]).sum(1)
        pm = tot / len(e)
        keep = ofl.single_position(e, o["tau"])
        oopt = eng.outcome(e, sd, GEOM, amb_mode="tp", slip=False)
        rows.append({"cell": name, "mode": "devam" if mode == 1 else "ters", "n": len(e),
                     "trades_per_day": len(e) / ((P1 - P0) / 1440), "WR": float((r > 0).mean()),
                     "meanR": float(r.mean()), "mean_bp": float(bp.mean()), "gross_bp": float(o["ret"].mean()),
                     "excessR": float(m), "z": float(z), "CI_lo": lo, "CI_hi": hi, "P_EV": pe,
                     "placebo_pct": float((pm < r.mean()).mean() * 100), "placebo_meanR": float(pm.mean()),
                     "single_R": float(r[keep].mean()), "optR": float((oopt["ret"] / oopt["sl"]).mean()),
                     "amb": float(o["amb"].mean()), "sl_bp_med": float(np.median(o["sl"]))})
out = pd.DataFrame(rows)
out.to_csv(os.path.join(ofl.RES, "of07_explore_1s.csv"), index=False)
print(out.round(4).to_string())
# örtüşme: (a) olaylarının yüzde kaçı aynı dakikada (c) koşulunu da taşıyor
ta, _ = ofl.events_from_dir(np.sign(zl), (np.abs(zl) >= 3) & inper, eok)
print("OF07a olaylarında |zD1|>=3 payı:", float((np.abs(zd[ta]) >= 3).mean()))
print("corr(sign large_net, sign delta) olaylarda:", float((np.sign(zl[ta]) == np.sign(zd[ta])).mean()))
