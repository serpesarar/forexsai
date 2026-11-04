"""Sızıntı/kısıt denetimi + süre profili (alg_tarama.build_sets üzerinde). Kullanım: _kontrol.py <tf> <n_sorgu>"""
from __future__ import annotations

import cProfile
import pstats
import sys
import time

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import alg_tarama as A  # noqa: E402

tf = sys.argv[1]; nq = int(sys.argv[2])
P = A.prep(tf)
assert (P["te"].max() < A.CUTOFF.value), "holdout"
print(tf, "bar", P["n"], "son bar bitişi", np.datetime64(int(P["te"].max()), "ns"))
hzs = [h for h in A.HZ if A.HZ[h] >= A.TF_MIN[tf] and h != "1d"]
Qall = A.pick_queries(P, hzs, A.SHORT_SPACING[tf])
Qi = Qall[np.linspace(0, len(Qall) - 1, nq).astype(int)]
print("tüm kısa sorgu", len(Qall))
pr = cProfile.Profile(); t0 = time.time(); pr.enable()
S = A.build_sets(P, Qi, hzs)
pr.disable(); print(f"build {time.time() - t0:.1f}s → sorgu başına {(time.time() - t0) / nq * 1000:.0f} ms")
pstats.Stats(pr).sort_stats("tottime").print_stats(12)
# kısıt denetimi
bad = 0; chk = 0
for hz in hzs:
    L = P["lab"][hz]; gap = L["gap"]
    for key, s in S.sets[hz].items():
        fam, W, par = key
        cov = {"cokolcek": 33, "refR7": 8, "ngram": 9}.get(fam, W + 1)
        arr = s["cand"] if s["kind"] == "nw" else s["nbm"]
        for qi, q in enumerate(Qi):
            nb = arr[qi, :s["nn"][qi]].astype(np.int64)
            if len(nb) == 0:
                continue
            chk += 1
            e1 = np.any(P["te"][nb] + A.HZ[hz] * A.MIN_NS > P["te"][q])        # sonuç karar anında kapanmış mı
            e2 = np.any(nb > q - cov)                                             # pencere çakışması
            e3 = np.any(P["ts"][nb] < P["ts"][q] - A.LIB_NS)                      # 5 yıl
            sn = np.sort(nb); e4 = np.any(np.diff(sn) < gap)                      # sonuç pencereleri çakışmaz
            e5 = not np.all(L["ok"][nb])
            if e1 or e2 or e3 or e4 or e5:
                bad += 1
                if bad < 5:
                    print("İHLAL", hz, key, q, e1, e2, e3, e4, e5)
print(f"denetlenen komşu listesi {chk}, ihlal {bad}")
