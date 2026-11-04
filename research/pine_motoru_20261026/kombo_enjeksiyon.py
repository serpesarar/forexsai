"""Enjeksiyon (duyarlılık) sınaması — madenci bilinen güçteki bir kenarı bulabiliyor mu?

Gerçek özellik evreninin (~300 bin script durumu) içine, etiketten kurulmuş, gücü BİLİNEN sahte özellikler eklenir;
madencinin kendi akışı (tekli tarama → ışın araması → aday seçimi → doğrulama/kasa → model) değiştirilmeden koşar.
  - TEK_L*: tek başına kenarlı özellik, isabet = taban + L (tüm dönemlerde kalıcı)
  - KOMBO_d*: A ve B tek tek seyreltilmiş (kenarın yalnız A∧B'de yoğun olduğu) çiftler — saf etkileşim duyarlılığı
Kullanım: python kombo_enjeksiyon.py [SYM] [pencere] [h]
Çıktı: results_kombo/enjeksiyon_<pencere>_<SYM>_h<h>.csv
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kombo_madenci as KM  # noqa: E402

SINGLE_LIFTS = (0.03, 0.05, 0.08, 0.12)
SINGLE_RATES = (0.04, 0.08, 0.16, 0.30)   # barların payı → keşif olay sayısı ≈ 250…1.500
COMBO_LIFT = 0.08                   # A∧B kesişimindeki kenar
COMBO_CORE_RATE = 0.12
COMBO_NOISE_RATES = (0.06, 0.12, 0.36)   # A ve B'ye ayrı ayrı eklenen gürültü → tekli kenar ≈ L·çekirdek/(çekirdek+gürültü)
SEED = 20261029


def _pick(rng, up, dn, k, frac_up):
    ku = int(round(k * frac_up))
    return np.concatenate([rng.choice(up, ku, replace=False), rng.choice(dn, k - ku, replace=False)])


def plant(d, L, rng):
    """→ [(ad, bool dizi)] ve beklenen kombinasyon çiftleri."""
    n = len(d)
    valid = L["valid"]
    up, dn = np.flatnonzero(valid & (L["r"] > 0)), np.flatnonzero(valid & (L["r"] < 0))
    base = len(up) / (len(up) + len(dn))
    out, pairs = [], []
    for lift in SINGLE_LIFTS:
        for rate in SINGLE_RATES:
            x = np.zeros(n, bool)
            x[_pick(rng, up, dn, int(n * rate), base + lift)] = True
            out.append((f"A:PLANT|TEK_L{lift:.2f}_s{rate:.2f}", x))
    for nr in COMBO_NOISE_RATES:
        core = _pick(rng, up, dn, int(n * COMBO_CORE_RATE), base + COMBO_LIFT)
        names = []
        for side in "AB":
            x = np.zeros(n, bool)
            x[core] = True
            x[rng.choice(n, int(n * nr), replace=False)] = True
            nm = f"A:PLANT|KOMBO_g{nr:.2f}_{side}"
            out.append((nm, x))
            names.append(nm)
        pairs.append(tuple(names))
    return out, pairs, base


def main(sym="NDX", window="recent", h=4):
    t0 = time.time()
    KM.HS = (h,)
    excl = KM.EV.lookahead_sids()
    d = KM.EV.window_frame(sym, window)
    tf, n, sp = KM.EV.window_tf(window), len(d), d.split.values
    n_min = KM.GC.N_MIN[tf]
    packed, names, bull_f, bear_f, sname = KM.build_features(sym, window, d, excl)
    lp = KM.label_pack(d, tf, sym, np.random.default_rng(KM.GC.SEED))
    planted, pairs, base = plant(d, lp[h][0], np.random.default_rng(SEED))
    p0 = len(packed)
    for nm, x in planted:
        packed.append(np.packbits(x).tobytes())
        names.append(nm)
    mix, mix_names = KM.mix_features(bull_f, bear_f, sp == 0)
    fs = KM.Feats(packed, names, mix, mix_names, n)
    print(f"{sym} {window} h={h}: {len(fs)} özellik, {len(planted)} ekli, taban {base:.3f} ({time.time() - t0:.0f}s)",
          flush=True)
    nz, smax = KM.univariate(fs, lp, n_min)
    z1, n1 = nz[h][:, 1], nz[h][:, 0]
    rank = (-np.abs(z1)).argsort().argsort()
    found = KM.beam(fs, h, lp[h][1], z1, n1, smax[h], n_min)
    thr = float(np.quantile(smax[h], 0.95))
    disc_end = int(np.flatnonzero(sp == 0).max()) + 1
    chosen = KM.select(fs, found, h, disc_end)
    cand = {}
    for tup, z, ev in chosen:
        r = KM.split_rows(ev, lp[h][1], lp[h][0], 1.0 if z > 0 else -1.0, n_min)
        cand[tup] = dict(z=z, **r)
    rows = []
    for j, (nm, x) in enumerate(planted):
        i = p0 + j
        c = next((v for k, v in cand.items() if i in k), None)
        rs = KM.split_rows(np.flatnonzero(KM.events(x[:, None], h)[:, 0]), lp[h][1], lp[h][0], 1.0, n_min)
        rows.append(dict(ozellik=nm, kesif_n=n1[i], kesif_lift=rs["KESIF_lift"], kasa_lift=rs["KASA_lift"],
                         tekli_z=z1[i], tekli_sira=int(rank[i]) + 1, havuzda=rank[i] < KM.POOL,
                         isinda=rank[i] < KM.BEAM, aday=c is not None,
                         aday_kesif_z=c["z"] if c else np.nan, esik=thr,
                         aday_dogr_z=c["DOGRULAMA_z"] if c else np.nan, aday_kasa_z=c["KASA_z"] if c else np.nan,
                         kanitli=bool(c and c["kanitli"])))
    for a, b in pairs:
        ia, ib = p0 + [p[0] for p in planted].index(a), p0 + [p[0] for p in planted].index(b)
        key = tuple(sorted((ia, ib)))
        hit = key in cand
        ev = np.flatnonzero(KM.events((fs.vec(ia) & fs.vec(ib))[:, None], h)[:, 0])
        r = KM.split_rows(ev, lp[h][1], lp[h][0], 1.0, n_min)
        rows.append(dict(ozellik=f"{a}∧B", kesif_n=r["KESIF_n"], tekli_z=r["KESIF_z"], tekli_sira=np.nan, havuzda=np.nan, isinda=np.nan,
                         aday=hit, aday_kesif_z=r["KESIF_z"], esik=thr, aday_dogr_z=r["DOGRULAMA_z"],
                         aday_kasa_z=r["KASA_z"], kanitli=bool(hit and cand[key]["kanitli"])))
    out = pd.DataFrame(rows)
    out.to_csv(KM.OUT / f"enjeksiyon_{window}_{sym}_h{h}.csv", index=False)
    print(out.round(2).to_string(index=False))
    gen = [c for k, c in cand.items() if not any(i >= p0 and i < p0 + len(planted) for i in k)]
    print(f"gerçek scriptlerden aday {len(gen)}, kanıtlı {sum(c['kanitli'] for c in gen)}")
    mod = KM.model(fs, nz, lp, bull_f, bear_f, sp, n_min)
    print(f"model kasa AUC (ekli özelliklerle) {mod[0]['kasa_auc']:.4f}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "NDX", a[1] if len(a) > 1 else "recent", int(a[2]) if len(a) > 2 else 4)
