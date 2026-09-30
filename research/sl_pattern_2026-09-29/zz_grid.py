"""Zikzak kural ızgarası: A (bot, train/test) + B (pulse replay, H1/H2) üzerinde."""
import itertools
import pickle
import time
import numpy as np
import pandas as pd

A, B, C = pickle.load(open("zz_ds.pkl", "rb"))
SPLIT = pd.Timestamp("2026-08-01", tz="UTC")
A_te = (pd.to_datetime(A.meta.t, utc=True) >= SPLIT).values
B_te = (pd.to_datetime(B.meta.t, utc=True) >= SPLIT).values

Ps = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
Ls = [0.05, 0.1, 0.2, 0.3, 0.5]
LOCKS = [(-0.3, False), (-0.2, False), (-0.1, False), (0.0, False), (0.05, False),
         (0.25, True), (0.5, True)]
AGES = [0, 15, 30, 60]


def rules():
    for n_p in (1, 2, 3):
        firsts = (0, 1, -1)
        for first in firsts:
            if n_p == 1 and first == 1:
                continue                      # "önce kâr, 1. kâr ziyareti" = first=0 ile aynı
            Pas = Ps if n_p >= 2 else [None]
            Lset = Ls if (n_p >= 2 or first == -1) else [0.2]   # L yalnız zikzakta anlamlı
            for P, Pa, L, age in itertools.product(Ps, Pas, Lset, AGES):
                for lock, ltp in LOCKS:
                    if ltp and lock >= (Pa if Pa is not None else P):
                        continue
                    yield dict(n_p=n_p, first=first, P=P, Pa=Pa, L=L, age=age,
                               lock=lock, lock_tp=ltp, action=0, delay=2)
                yield dict(n_p=n_p, first=first, P=P, Pa=Pa, L=L, age=age,
                           lock=0.0, lock_tp=False, action=1, delay=2)


def stats(ds, R, te):
    b = ds.base; d = R - b
    saved = int(((b < 0) & (R > b + 1e-9)).sum()); killed = int(((b > 0) & (R < b - 1e-9)).sum())
    return d.sum(), d[~te].sum(), d[te].sum(), saved, killed, (R > 0).mean()


if __name__ == "__main__":
    t0 = time.time(); out = []
    for i, r in enumerate(rules()):
        Ra, _ = A.run(**r); Rb, _ = B.run(**r)
        a = stats(A, Ra, A_te); b = stats(B, Rb, B_te)
        usd = ((Ra - A.base) * A.meta.usd_R.values).sum()
        out.append({**r, "A_dR": a[0], "A_tr": a[1], "A_te": a[2], "A_saved": a[3],
                    "A_killed": a[4], "A_wr": a[5], "A_usd": usd,
                    "B_dR": b[0], "B_h1": b[1], "B_h2": b[2], "B_saved": b[3],
                    "B_killed": b[4], "B_wr": b[5]})
        if i % 5000 == 0:
            print(i, round(time.time() - t0), "s", flush=True)
    O = pd.DataFrame(out)
    O.to_pickle("zz_grid.pkl")
    print("toplam kural", len(O), round(time.time() - t0), "s")
