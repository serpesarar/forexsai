"""Tüm dakikalar için ilk-dokunuş indekslerini hesapla (rastgele giriş evreni).

Çıktı: out/hits.npz — e (giriş barı), p0, k_up_<bp>, k_dn_<bp> (sabit bp seviyeleri),
k_up_a1_<m>/k_dn_a1_<m> (m×ATR14 1m), k_up_a5_<m>/k_dn_a5_<m> (m×ATR14 5m), atr1, atr5, rv.
k = pencere [e, e+1440) içinde ilk dokunuş barının göreli indeksi; 1440 = dokunuş yok.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

LEVELS_BP = [3, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 40, 50, 60, 75, 100, 150, 200]
ATR_MULTS = [0.5, 1.0, 2.0, 3.0]


def main() -> None:
    os.makedirs(lib.OUT, exist_ok=True)
    t0 = time.time()
    g = lib.load_grid()
    e = lib.entries(g)
    p0 = g["open"][e]
    print(f"giriş sayısı {len(e):,}  ({time.time()-t0:.1f}s)", flush=True)
    MX, MN = lib.sparse_tables(g["high"], g["low"])
    print(f"seyrek tablo ({time.time()-t0:.1f}s)", flush=True)
    res = {"e": e.astype(np.int32), "p0": p0}
    for b in LEVELS_BP:
        f = b / 1e4
        res[f"k_up_{b}"] = lib.first_hit(MX, e, p0 * (1 + f), lib.LMAX, True).astype(np.int16)
        res[f"k_dn_{b}"] = lib.first_hit(MN, e, p0 * (1 - f), lib.LMAX, False).astype(np.int16)
        print(f"  {b} bp ({time.time()-t0:.1f}s)", flush=True)
    a1 = lib.atr_1m(g)[e]
    a5 = lib.atr_5m(g)[e]
    rv = lib.rv_24h(g)[e]
    res.update(atr1=a1, atr5=a5, rv=rv)
    for name, a in [("a1", a1), ("a5", a5)]:
        av = np.where(np.isnan(a), np.inf, a)  # ATR yoksa dokunuş yok → sonra dışlanır
        for m in ATR_MULTS:
            res[f"k_up_{name}_{m}"] = lib.first_hit(MX, e, p0 + m * av, lib.LMAX, True).astype(np.int16)
            res[f"k_dn_{name}_{m}"] = lib.first_hit(MN, e, p0 - m * av, lib.LMAX, False).astype(np.int16)
            print(f"  {name}×{m} ({time.time()-t0:.1f}s)", flush=True)
    np.savez_compressed(f"{lib.OUT}/hits.npz", **res)
    print(f"bitti {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
