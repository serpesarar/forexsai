"""Motor kalibrasyonu: saf Brown hareketi (dakikada 60 alt adım → 1m OHLC). Asimetrik braket brüt EV'si ≈ 0 olmalı.
İkinci varyant: Student-t(3) alt adımlar (sıçramalı/kalın kuyruk) — bar-içi sıçramalarda SL'in seviyeden dolduğu
varsayımının yarattığı iyimser yanlılığı ölçer. Ayrıca alt adım çözünürlüğünde 'gerçek' sonuç (yol bilinir) hesaplanır."""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

H = 60; SUB = 60; NMIN = 400_000
BRK = [(5, 100), (10, 50), (5, 5), (10, 10), (20, 20), (50, 10), (100, 5)]
rng = np.random.default_rng(1)
rows = []
for kind in ["gauss", "t3"]:
    sig = 4.5e-4 / np.sqrt(SUB)  # ~4,5 bp/dk
    if kind == "gauss":
        z = rng.standard_normal(NMIN * SUB)
    else:
        z = rng.standard_t(3, NMIN * SUB) / np.sqrt(3.0)
    lp = np.cumsum(z * sig) - 0.5 * sig**2 * np.arange(1, NMIN * SUB + 1)  # fiyat martingal
    P = 50000 * np.exp(lp).reshape(NMIN, SUB)
    pc = np.concatenate([[50000.0], P[:-1, -1]])
    o = pc.copy()            # açılış = önceki kapanış (sürekli)
    h = np.maximum(P.max(1), o); l = np.minimum(P.min(1), o); c = P[:, -1]
    MX, MN = lib.sparse_tables(h, l, klev=7)
    e = np.arange(1, NMIN - H, 13)
    p0 = o[e]
    for tp, sl in BRK:
        for side in (1, -1):
            if side == 1:
                ktp = lib.first_hit(MX, e, p0 * (1 + tp / 1e4), H, True); ksl = lib.first_hit(MN, e, p0 * (1 - sl / 1e4), H, False)
            else:
                ktp = lib.first_hit(MN, e, p0 * (1 - tp / 1e4), H, False); ksl = lib.first_hit(MX, e, p0 * (1 + sl / 1e4), H, True)
            tpf = (ktp < ksl) & (ktp < H); slf = (ksl <= ktp) & (ksl < H); amb = (ktp == ksl) & (ktp < H)
            r = np.where(tpf, tp, np.where(slf, -sl, side * (c[e + H - 1] / p0 - 1) * 1e4))
            # alt-adım gerçek sonucu (yalnız ilk 20k giriş, döngü): yol bilinir, dolum = gerçek ilk aşan alt-adım fiyatı
            m = min(20000, len(e)); rt = np.empty(m)
            for i in range(m):
                path = P[e[i]:e[i] + H].ravel() / p0[i] - 1
                path = side * path * 1e4
                up = np.flatnonzero(path >= tp); dn = np.flatnonzero(path <= -sl)
                iu = up[0] if len(up) else 10**9; idn = dn[0] if len(dn) else 10**9
                if iu < idn: rt[i] = tp            # limit TP: seviyeden (iyimser değil)
                elif idn < iu: rt[i] = path[idn]  # stop: ilk aşan alt-adım fiyatı (kayma dahil)
                else: rt[i] = path[-1]
            rows.append({"kind": kind, "tp/sl": f"{tp}/{sl}", "side": "L" if side == 1 else "S",
                         "engine_bp": r.mean(), "engine_bp_first20k": r[:m].mean(), "subtick_true_bp": rt.mean(),
                         "amb": amb.mean()})
    print(kind, "ok", flush=True)
df = pd.DataFrame(rows)
df.to_csv(f"{lib.OUT}/brownian_check.csv", index=False)
pd.set_option("display.width", 200)
print(df.round(3).to_string())
