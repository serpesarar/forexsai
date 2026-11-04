"""capali_sizinti_testi.py — önek (prefix) sızıntı testi (meta-ders 9): veriyi C tarihinde kesip aileyi yeniden kur;
sonucu C'den önce biten her olayın komşu kümesi / kural çağrısı tam kesimsiz kurulumla AYNI olmalı.
(Özellik veya kütüphane gelecekteki bir bara bakıyorsa fark çıkar.)
Çalıştır: nice python3.13 research/mum_derin_tarama_20261013/capali/capali_sizinti_testi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capali_kur as K  # noqa: E402
import capali_veri as V  # noqa: E402


def build_all(tfs=("5m", "15m", "30m", "1h")) -> dict:
    daily = V.load_daily()
    fam = []
    for tf in tfs:
        G = V.Grid(tf, daily)
        if tf in ("5m", "15m", "30m"):
            fam += K.build_a(G) + K.build_d(G)
        if tf in ("15m", "30m", "1h"):
            fam += K.build_b(G)
        fam += K.build_c(G) + K.build_f(G)
    fam += K.build_e(daily)
    return {c["name"]: c for c in fam}


def main() -> None:
    full = build_all()
    cut = pd.Timestamp("2025-06-02", tz="UTC")
    V.HOLDOUT = cut; V.HOLD_NS = int(cut.value); K.HOLD_NS = int(cut.value)
    part = build_all()
    bad = 0; checked = 0; nev = 0
    for name, cp in part.items():
        cf = full[name]
        if cp["tf"] == "1d":
            continue      # günlük dosya HOLDOUT ile kesilir; aşağıda ayrıca
        m = cp["end"] < int(cut.value)
        k = int(m.sum())
        if k == 0:
            continue
        checked += 1; nev += k
        same = np.array_equal(cp["tq"][:k], cf["tq"][:k]) and np.array_equal(cp["day"][:k], cf["day"][:k])
        if cp["kind"] == "knn":
            same &= np.array_equal(cp["NB"][:k], cf["NB"][:k])
        else:
            same &= np.array_equal(np.nan_to_num(cp["call"][:k]), np.nan_to_num(cf["call"][:k]))
        if not same:
            bad += 1; print("FARK:", name)
    # günlük: kesilmiş takvimle
    dfull = {n: c for n, c in full.items() if c["tf"] == "1d"}
    for name, cp in part.items():
        if cp["tf"] != "1d":
            continue
        cf = dfull[name]; k = len(cp["tq"]) - 5
        checked += 1; nev += k
        if not (np.array_equal(cp["NB"][:k], cf["NB"][:k]) and np.array_equal(cp["day"][:k], cf["day"][:k])):
            bad += 1; print("FARK:", name)
    print(f"önek testi: {checked} konfig, {nev} olay karşılaştırıldı, farklı konfig = {bad}")


if __name__ == "__main__":
    main()
