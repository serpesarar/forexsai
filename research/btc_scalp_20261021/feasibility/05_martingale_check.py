"""Motor yansızlık sınaması (E42 yöntemi) + kısa ufuk seri bağımlılığı.

1) Her yıl için barlar göreli (o,h,l,c)/önceki kapanış dörtlüsü olarak BÜTÜN hâlinde karıştırılır
   (seri bağımlılık yok edilir, bar-içi yapı korunur) → sentetik martingal benzeri yol.
   Aynı motorla braketler: gerçek − sentetik farkı = verinin yol bağımlılığı; sentetikte asimetrik
   braketlerin brüt EV'si ≈ 0 (− belirsizlik) çıkmalı.
2) Varyans oranı VR(q) = Var(q-dk getiri)/(q·Var(1-dk)), q ∈ {2,5,15,60}, yıl bazında; 1-dk otokorelasyon.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

H = 60
BRK = [(5, 100), (10, 50), (5, 5), (10, 10), (20, 20), (50, 10), (100, 5)]
rng = np.random.default_rng(42)
g = lib.load_grid()
ts = lib.T0 + pd.to_timedelta(np.arange(lib.N), unit="m")
year = ts.year.to_numpy()


def eval_path(o, h, l, c, step: int = 7):
    """Kesintisiz yol üzerinde her step dakikada giriş; gerçekçi kurallar (aynı bar → SL)."""
    MX, MN = lib.sparse_tables(h, l, klev=7)  # 2^6=64 ≥ 60
    n = len(o)
    e = np.arange(1, n - H, step)
    p0 = o[e]
    out = {}
    for tp, sl in BRK:
        res = []
        for side in (1, -1):
            if side == 1:
                ktp = lib.first_hit(MX, e, p0 * (1 + tp / 1e4), H, True)
                ksl = lib.first_hit(MN, e, p0 * (1 - sl / 1e4), H, False)
            else:
                ktp = lib.first_hit(MN, e, p0 * (1 - tp / 1e4), H, False)
                ksl = lib.first_hit(MX, e, p0 * (1 + sl / 1e4), H, True)
            tpf = (ktp < ksl) & (ktp < H)
            slf = (ksl <= ktp) & (ksl < H)
            r = np.where(tpf, tp, np.where(slf, -sl, side * (c[e + H - 1] / p0 - 1) * 1e4))
            res.append(r.mean())
        out[f"{tp}/{sl}"] = (res[0], res[1])
    return out


rows = []
vr_rows = []
for y in [2022, 2024, 2025]:
    m = (year == y) & ~np.isnan(g["close"])
    o, h, l, c = (g[k][m] for k in ["open", "high", "low", "close"])
    # yalnız kesintisiz olsun diye eksik dakikalar atlandı (yıl içinde birkaç dakika)
    real = eval_path(o, h, l, c)
    pc = np.concatenate([[c[0]], c[:-1]])
    q = np.vstack([o / pc, h / pc, l / pc, c / pc]).T[1:]
    syn = {}
    for rep in range(3):
        qq = q[rng.permutation(len(q))]
        cs = c[0] * np.cumprod(qq[:, 3])
        pcs = np.concatenate([[c[0]], cs[:-1]])
        so, sh, sl_, sc = pcs * qq[:, 0], pcs * qq[:, 1], pcs * qq[:, 2], cs
        r = eval_path(so, sh, sl_, sc)
        for k, v in r.items():
            syn.setdefault(k, []).append(v)
    for k in real:
        sL = np.mean([v[0] for v in syn[k]]); sS = np.mean([v[1] for v in syn[k]])
        rows.append({"year": y, "tp/sl": k, "real_L_bp": real[k][0], "real_S_bp": real[k][1],
                     "syn_L_bp": sL, "syn_S_bp": sS})
    lr = np.diff(np.log(c))
    v1 = lr.var()
    vr = {"year": y, "ac1": np.corrcoef(lr[:-1], lr[1:])[0, 1]}
    for qn in [2, 5, 15, 60]:
        s = np.convolve(lr, np.ones(qn), "valid")[::qn]
        vr[f"VR{qn}"] = s.var() / (qn * v1)
    vr_rows.append(vr)
    print(y, "ok", flush=True)

df = pd.DataFrame(rows)
df.to_csv(f"{lib.OUT}/martingale_check.csv", index=False)
vr = pd.DataFrame(vr_rows)
vr.to_csv(f"{lib.OUT}/variance_ratio.csv", index=False)
pd.set_option("display.width", 200)
print(df.round(3).to_string())
print(vr.round(4).to_string())
