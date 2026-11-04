"""Özellikler + önek (sızıntı) testi + olay üretimi. Sonuç (getiri) HESAPLAMAZ.

Çıktı: results/events.npz (hücre → karar dakikası t, akış yönü), results/event_counts.csv
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofl  # noqa: E402

t0 = time.time()
df = ofl.load_frame()
g = ofl.build_grid(df)
fc_next, blocked = ofl.rollover_cap()
valid = ofl.valid_entries(g)
hcap = fc_next - np.arange(ofl.N)
entry_ok = valid & ~blocked & (hcap >= 5)
F = ofl.features(df)
F["dp1sign"] = np.sign(2 * df["perp_taker_buy_base"].to_numpy().astype(float) - df["perp_volume"].to_numpy().astype(float))
print(f"özellikler {time.time()-t0:.0f}s; geçerli giriş {entry_ok.sum():,}")

# ---------------- önek testi: cut sonrası veriyi boz, cut'a kadar özellikler aynı kalmalı
cut = ofl.lib.tmin("2023-06-15 12:00")
df2 = df.copy()
rng = np.random.default_rng(3)
for c in ["spot_open", "spot_high", "spot_low", "spot_close", "perp_open", "perp_high", "perp_low", "perp_close"]:
    df2.loc[cut:, c] = df2.loc[cut:, c].to_numpy() * 1.3
for c in ["spot_volume", "spot_taker_buy_base", "perp_volume", "perp_taker_buy_base", "perp_trades"]:
    v = df2.loc[cut:, c].to_numpy()
    df2.loc[cut:, c] = (v * rng.uniform(0.2, 5, len(v))).astype(v.dtype)
F2 = ofl.features(df2)
leak = []
for k in F:
    if k in ("dp1sign", "minute", "cvd"):
        continue
    a, b = F[k][cut - 3000:cut], F2[k][cut - 3000:cut]
    if a.dtype == bool:
        same = np.array_equal(a, b)
    else:
        same = np.allclose(a, b, equal_nan=True, rtol=1e-9, atol=1e-9)
    if not same:
        leak.append(k)
# cvd fark tabanlı kullanılır
for n in [30, 60]:
    a = F["cvd"][cut - 3000:cut] - F[f"cmax{n}"][cut - 3000:cut]
    b = F2["cvd"][cut - 3000:cut] - F2[f"cmax{n}"][cut - 3000:cut]
    if not np.allclose(a, b, equal_nan=True):
        leak.append(f"cvd-cmax{n}")
print("önek testi:", "OK" if not leak else f"SIZINTI {leak}")
assert not leak
del df2, F2

# ---------------- olaylar
EV = {}


def add(name, dirarr, cond):
    t, d = ofl.events_from_dir(dirarr, cond, entry_ok)
    EV[name] = (t, d)


for w in [1, 5, 15]:
    z = F[f"zDp{w}"]
    for th in [3, 5]:
        c = (np.abs(z) >= th) & ~F[f"pbad{w}"]
        add(f"OF01_W{w}_th{th}", np.sign(z), c)
        c2 = c & (np.abs(F[f"zr{w}"]) <= 0.5) & ~F[f"sbad{w}"]
        add(f"OF02_W{w}_th{th}", np.sign(z), c2)
for w in [5, 15]:
    dlt = F[f"zDs{w}"] - F[f"zDp{w}"]
    for k in [3, 4]:
        c = (np.abs(dlt) >= k) & ~F[f"pbad{w}"] & ~F[f"sbad{w}"]
        add(f"OF03_W{w}_k{k}", np.sign(dlt), c)
for n in [30, 60]:
    dmax = F["cvd"] - F[f"cmax{n}"]
    dmin = F["cvd"] - F[f"cmin{n}"]
    nb = ~F[f"pbad{n}"]
    for gg in [0, 0.5]:
        up = (F["pc"] >= F[f"pmax{n}"]) & (dmax < -gg * F[f"sdc{n}"]) if gg > 0 else (F["pc"] >= F[f"pmax{n}"]) & (dmax < 0)
        dn = (F["pc"] <= F[f"pmin{n}"]) & (dmin > gg * F[f"sdc{n}"]) if gg > 0 else (F["pc"] <= F[f"pmin{n}"]) & (dmin > 0)
        d = np.where(up & nb, 1.0, np.where(dn & nb, -1.0, 0.0))
        add(f"OF04a_N{n}_g{gg:g}", d, d != 0)
    for gg in [0.5, 1]:
        up = (dmax >= 0) & (F["pc"] <= F[f"pmax{n}"] - gg * F[f"sdp{n}"])
        dn = (dmin <= 0) & (F["pc"] >= F[f"pmin{n}"] + gg * F[f"sdp{n}"])
        d = np.where(up & nb, 1.0, np.where(dn & nb, -1.0, 0.0))
        add(f"OF04b_N{n}_g{gg:g}", d, d != 0)
for v in ["v", "t"]:
    for w in [1, 5]:
        z = F[f"zl{v}{w}"]
        for th in [3, 5]:
            c = (z >= th) & ~F[f"pbad{w}"]
            add(f"OF05_{v}_W{w}_th{th}", F[f"dir{w}"], c)
qh = np.isin(F["minute"], [0, 15, 30, 45])
for th in [0, 2]:
    c = qh & ~F["pbad1"] & (np.abs(F["zDp1"]) >= th) & (F["dp1sign"] != 0)
    if th > 0:
        c &= np.sign(F["zDp1"]) == F["dp1sign"]
    add(f"OF06_th{th}", F["dp1sign"], c)

rows = []
for k, (t, d) in EV.items():
    e = t + 1
    sg = ofl.seg_of(e)
    rows.append({"cell": k, "n_all": len(t), **{f"n_{s}": int((sg == s).sum()) for s in ofl.SEG},
                 "buy_share": float((d > 0).mean()) if len(d) else np.nan})
cnt = pd.DataFrame(rows)
cnt.to_csv(os.path.join(ofl.RES, "event_counts.csv"), index=False)
print(cnt.to_string())
np.savez_compressed(os.path.join(ofl.RES, "events.npz"),
                    **{f"{k}__t": v[0] for k, v in EV.items()}, **{f"{k}__d": v[1] for k, v in EV.items()})
print(f"bitti {time.time()-t0:.0f}s")
