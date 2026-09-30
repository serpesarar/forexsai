"""Koşullu olasılık: n'inci kâr ziyaretine varan işlemler oradan sonra ne yapıyor?

Her olay durumu (ilk olay + kâr ziyareti sayısı) için, o ana varan işlemlerde:
  P(TP)          : sonunda TP (baz kuralla)
  P(giriş önce)  : TP'den önce girişe (0R) geri dönüş  → BE'nin kazanan öldürme olasılığı
  P(SL | giriş)  : girişe dönenlerin SL ile bitme oranı → BE'nin kurtarma olasılığı
BE'nin başabaş koşulu (lock=0): P(giriş önce ∧ sonra TP)·rr < P(giriş önce ∧ sonra SL)·1
"""
import pickle
import numpy as np
import pandas as pd
from numba import njit

A, B, C = pickle.load(open("zz_ds.pkl", "rb"))


@njit(cache=True)
def trace(FAV, ADV, OPN, CLS, off, ln, rr, Pf, L, maxv):
    """Her işlem için: kâr ziyareti k'ye varıldı mı (k=1..maxv), ilk olay, sonrasında
    girişe dönüş var mı, nihai sonuç (TP=1/SL=-1/0)."""
    N = off.shape[0]
    reach = np.zeros((N, maxv), np.int8)
    back = np.zeros((N, maxv), np.int8)       # o ziyaretten SONRA, çıkıştan önce ≤0 görüldü mü
    firstz = np.zeros(N, np.int8)
    fin = np.zeros(N, np.int8)
    vals = np.empty(4)
    for k in range(N):
        o = off[k]; n = ln[k]; tp = rr[k]; P = Pf * tp
        last = 0; pv = 0; fz = 0
        for j in range(n):
            f = FAV[o + j]; a = ADV[o + j]
            # geri dönüş işaretleri (bu bardan itibaren): önceki ziyaretler için
            if a <= 0.0:
                for q in range(pv):
                    back[k, q] = 1
            if a <= -1.0:
                fin[k] = -1; break
            if f >= tp:
                fin[k] = 1; break
            op = OPN[o + j]; c = CLS[o + j]
            vals[0] = op
            if c >= op:
                vals[1] = a; vals[2] = f
            else:
                vals[1] = f; vals[2] = a
            vals[3] = c
            for q in range(4):
                v = vals[q]
                z = 1 if v >= P else (-1 if v <= -L else 0)
                if z != 0 and z != last:
                    if fz == 0:
                        fz = z
                    last = z
                    if z == 1:
                        if pv < maxv:
                            reach[k, pv] = 1
                        pv += 1
        firstz[k] = fz
    return reach, back, firstz, fin


def table(ds, name, Pf=0.6, L=0.2, maxv=3):
    reach, back, fz, fin = trace(ds.FAV, ds.ADV, ds.OPN, ds.CLS, ds.off, ds.ln, ds.rr, Pf, L, maxv)
    rr = float(np.median(ds.rr))
    rows = []
    for v in range(maxv):
        for f, lab in ((0, "fark etmez"), (1, "önce kâr"), (-1, "önce zarar")):
            m = reach[:, v] == 1
            if f != 0:
                m &= fz == f
            n = m.sum()
            if n < 20:
                continue
            tp = (fin[m] == 1).mean()
            bk = back[m, v] == 1
            kill = ((fin[m] == 1) & bk).mean()
            save = ((fin[m] == -1) & bk).mean()
            rows.append(dict(set=name, visit=v + 1, first=lab, n=int(n), P_TP=round(tp, 3),
                             P_back=round(bk.mean(), 3), kill=round(kill, 3), save=round(save, 3),
                             BE_net_R=round(save * 1.0 - kill * rr, 3)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    for Pf, L in ((0.4, 0.2), (0.6, 0.2), (0.6, 0.1)):
        print(f"\n=== kâr eşiği TP yolunun %{int(Pf*100)}'i, zarar eşiği {L}R ===")
        print(pd.concat([table(A, "A bot", Pf, L), table(B, "B pulse", Pf, L),
                         table(C, "C sentetik", Pf, L)]).to_string(index=False))
