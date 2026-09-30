"""USOIL BUY çıkış taktiği ızgarası × rejim (eğim tertilleri L1'den).

Dönemler: L1 = 2025-05→2026-01 (seçim), L2 = 2026-02→09 (dış test), B (pulse, dış), A (bot, dış).
"""
import itertools
import pickle
import time
import numpy as np
import pandas as pd

A, B, Lg = pickle.load(open("usoil_sets.pkl", "rb"))
Lt = pd.to_datetime(Lg.meta.t)
L1 = (Lt < "2026-02-01").values
q1, q2 = np.nanquantile(Lg.meta.slope[L1], [1 / 3, 2 / 3])
print(f"rejim eşikleri (3g EMA 1g eğimi %): düşen < {q1:.3f} ≤ yatay < {q2:.3f} ≤ yükselen")


def reg(s):
    x = s.meta.slope.values
    return np.where(np.isnan(x), -1, np.where(x < q1, 0, np.where(x < q2, 1, 2)))


RG = {"L": reg(Lg), "B": reg(B), "A": reg(A)}
PER = {"L": np.where(L1, 0, 1),
       "B": (pd.to_datetime(B.meta.t, utc=True) >= pd.Timestamp("2026-08-01", tz="UTC")).astype(int).values,
       "A": (pd.to_datetime(A.meta.t, utc=True) >= pd.Timestamp("2026-08-01", tz="UTC")).astype(int).values}


def tactics():
    for tpm, tr in itertools.product((0.6, 0.8, 1.0, 1.25, 1.5, 2.0), (0.0, 0.3, 0.5, 0.8)):
        if tr > 0 and tpm < 1.0:
            continue
        yield dict(tp_mult=tpm, trail=tr, act=0)
        for first, P, L in itertools.product((0, -1), (0.4, 0.5, 0.6, 0.7, 0.8), (0.1, 0.2, 0.3, 0.5)):
            if first == 0 and L != 0.3:
                continue                                   # klasikte L anlamsız
            if P >= tpm:
                continue
            for lock in (0.0, 0.25, 0.5):
                if lock < P:
                    yield dict(tp_mult=tpm, trail=tr, act=1, first=first, P=P, L=L, lock=lock)
            yield dict(tp_mult=tpm, trail=tr, act=2, first=first, P=P, L=L)


if __name__ == "__main__":
    t0 = time.time(); rows = []
    for k, tac in enumerate(tactics()):
        row = dict(tac)
        for nm, s in (("L", Lg), ("B", B), ("A", A)):
            R = s.run(**tac)
            for p in (0, 1):
                for g in (0, 1, 2):
                    m = (PER[nm] == p) & (RG[nm] == g)
                    row[f"{nm}{p}_{g}"] = R[m].sum(); row[f"{nm}{p}_{g}_n"] = int(m.sum())
        rows.append(row)
        if k % 500 == 0:
            print(k, round(time.time() - t0), "s", flush=True)
    G = pd.DataFrame(rows); G.to_pickle("usoil_grid.pkl")
    print("taktik", len(G), round(time.time() - t0), "s")
