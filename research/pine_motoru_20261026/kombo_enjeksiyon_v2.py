"""v2 enjeksiyon (duyarlılık) sınaması — PROTOCOL EK-P9 "önce duyarlılık".

Gerçek özellik evrenine, etiketten kurulmuş gücü BİLİNEN sahte özellikler eklenir; v2 madencinin akışı değişmeden koşar.
  - TEK_L<lift>_s<sıklık>: tek başına kenarlı (isabet = taban + lift)
  - ETK_L<lift>_c<çekirdek>_A/B: A ve B TEK BAŞINA kenarsız (çekirdekteki yukarı eğilim, kendi gürültüsündeki aşağı
    eğilimle sıfırlanır); kenar yalnız A∧B'de (= çekirdek). Çiftler çift kümesine zorla alınır (popülerlik seçimi ayrıca
    raporlanır: sahte özelliklerin boost'u 0 olduğu için doğal seçimde girmezlerdi).
Kullanım: python kombo_enjeksiyon_v2.py [pencere=recent] [SYM=NDX] [h,h,...=1,4,12]
Çıktı: results_kombo_v2/enjeksiyon_<pencere>_<SYM>.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kombo_madenci as KM  # noqa: E402
import kombo_madenci_v2 as V2  # noqa: E402

SINGLE_LIFTS = (0.03, 0.05, 0.08, 0.12)
SINGLE_RATES = (0.04, 0.08, 0.16, 0.30)
PAIR_LIFTS = (0.05, 0.08, 0.12)
PAIR_CORES = (0.04, 0.08)
SEED = 20261029


def _pick(rng, up, dn, k, frac_up):
    ku = int(round(k * frac_up))
    return np.concatenate([rng.choice(up, ku, replace=False), rng.choice(dn, k - ku, replace=False)])


def plant(L, n, h, rng):
    """Etiket h'ye göre kurulur; sahte barlar h-ızgarasında (çift olayları ızgarada sayıldığı için)."""
    g = np.zeros(n, bool)
    g[::h] = True
    valid = L["valid"] & g
    up, dn = np.flatnonzero(valid & (L["r"] > 0)), np.flatnonzero(valid & (L["r"] < 0))
    base = len(up) / (len(up) + len(dn))
    ng = len(up) + len(dn)
    out, pairs = [], []
    for lift in SINGLE_LIFTS:
        for rate in SINGLE_RATES:
            x = np.zeros(n, bool)
            x[_pick(rng, up, dn, int(ng * rate), base + lift)] = True
            out.append((f"A:PLANT|h{h}_TEK_L{lift:.2f}_s{rate:.2f}", x))
    for lift in PAIR_LIFTS:
        for core in PAIR_CORES:
            k = int(ng * core)
            S = _pick(rng, up, dn, k, base + lift)
            rest_up, rest_dn = np.setdiff1d(up, S), np.setdiff1d(dn, S)
            names = []
            for side in "AB":
                N = _pick(rng, rest_up, rest_dn, k, base - lift)          # aşağı eğilimli gürültü → A tek başına ≈ taban
                rest_up, rest_dn = np.setdiff1d(rest_up, N), np.setdiff1d(rest_dn, N)
                x = np.zeros(n, bool)
                x[S] = True
                x[N] = True
                nm = f"A:PLANT|h{h}_ETK_L{lift:.2f}_c{core:.2f}_{side}"
                out.append((nm, x))
                names.append(nm)
            pairs.append(tuple(names))
    return out, pairs, base


def main(window="recent", sym="NDX", hs=(1, 4, 12)):
    KM.HS = V2.HS = tuple(hs)
    excl = KM.EV.lookahead_sids()
    d = KM.EV.window_frame(sym, window)
    tf = KM.EV.window_tf(window)
    planted, pairs = [], []
    for h in hs:
        L = V2.hit_labels(d, tf, h, KM.GC.SPREAD[sym])
        p, pr, base = plant(L, len(d), h, np.random.default_rng(SEED + h))
        planted += p
        pairs += pr
    c = V2.prepare(sym, window, excl, extra=planted)
    fs, p0 = c["fs"], c["p0"]
    idx = {nm: p0 + j for j, (nm, _) in enumerate(planted)}
    force = [idx[a] for pr in pairs for a in pr]
    natural = set(V2.pair_set(fs, c["boosts"], np.flatnonzero(c["sp"] == 0)))
    m = V2.mine(c, sym, window, force=force)
    nz = m["nz"]
    rows = []
    for nm, i in idx.items():
        h = int(nm.split("|h")[1].split("_")[0])
        if "_TEK_" not in nm and not nm.endswith("_A"):
            continue
        z1 = nz[h][:, 1]
        rank = int((np.abs(z1) > abs(z1[i])).sum()) + 1
        if "_TEK_" in nm:
            hit = [r for r in m["beam"] if r["h"] == h and i in r["tup"]]
            kind, name = "tek", nm
        else:
            b = idx[nm[:-1] + "B"]
            hit = [r for r in m["pairs"] if r["h"] == h and {r["idx_a"], r["idx_b"]} == {i, b}]
            hit += [r for r in m["beam"] if r["h"] == h and {i, b} <= set(r["tup"])]
            kind, name = "etkilesim", nm[:-2]
        r0 = hit[0] if hit else None
        rows.append(dict(tur=kind, ozellik=name, h=h, tekli_z=float(z1[i]), tekli_sira=rank,
                         dogal_cift_kumesinde=i in natural, aday=r0 is not None,
                         kesif_z=r0["KESIF_z"] if r0 else np.nan, dogr_z=r0["DOGRULAMA_z"] if r0 else np.nan,
                         kasa_z=r0["KASA_z"] if r0 else np.nan, kasa_lift=r0["KASA_lift"] if r0 else np.nan,
                         kanitli=bool(r0 and r0["kanitli"])))
    out = pd.DataFrame(rows)
    V2.OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(V2.OUT / f"enjeksiyon_{window}_{sym}.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.round(2).to_string(index=False))
    real_p = [r for r in m["pairs"] if r["idx_a"] < p0 and r["idx_b"] < p0]
    real_b = [r for r in m["beam"] if all(i < p0 for i in r["tup"])]
    print(f"gerçek scriptlerden: çift aday {len(real_p)} kanıtlı {sum(r['kanitli'] for r in real_p)}; "
          f"ışın aday {len(real_b)} kanıtlı {sum(r['kanitli'] for r in real_b)}")
    print("model kasa AUC:", [round(r["kasa_auc"], 3) for r in m["model"]])


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "recent", a[1] if len(a) > 1 else "NDX",
         tuple(int(x) for x in a[2].split(",")) if len(a) > 2 else (1, 4, 12))
