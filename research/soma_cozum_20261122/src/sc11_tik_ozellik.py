"""SC-11 — saniye düzeyi nedensel tik özellikleri (PROTOCOL SC-11).

`pencere(M, a, b, y)` → [a, b] aralığındaki HER saniye s için özellikler. s saniyesinde yalnız t_ms < (s+1)·1000 tikleri
(o saniyenin sonuna kadar) ve son TAMAMLANMIŞ 1m bar (s'nin dakikasından önceki) kullanılır. Yöne hizalı değerler y ile çarpılır.
Seviyeler SC-08 motorundan (sunucu saatine hizalı H4 20 / H1 55 mum Donchian, gün içi uç). Doğruluk: tests/test_sc11.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import sc08_ozellik as F
import sc_tick as TK

GETIRI_N = (5, 15, 30, 60, 120, 300)
TIK_N = (10, 30, 60, 300)
GERI = 3600
YOK_SN = 3600.0


def _seviye(M: F.Motor, s: np.ndarray, y: int) -> dict:
    bar = M.bar
    k = np.searchsorted(bar.t, s // 60 * 60) - 1                     # son tamamlanmış 1m bar
    o: dict[str, np.ndarray] = {"k": k}
    for ad, n in (("H4", 20), ("H1", 55)):
        T, dk = M.tf[ad], F.TF_DK[ad]
        bc = np.clip(np.searchsorted(T.kova, (s + M.sun[k]) // (dk * 60)) - 1, 0, len(T.C) - 1)
        o[f"ext_{ad}"] = T.g[f"hh{n}"][bc] if y > 0 else T.g[f"ll{n}"][bc]
        o[f"atr_{ad}"] = T.g["atr"][bc]
    D1 = M.tf["D1"]
    ayni = D1.kova_1m[k] == (s + M.sun[k]) // 86400
    o["gun_ext0"] = np.where(ayni, D1.kumh[k] if y > 0 else D1.kuml[k], -np.inf if y > 0 else np.inf)
    rng = pd.Series(bar.h - bar.l).rolling(60, min_periods=30).mean().to_numpy()
    o["atr1"] = rng[k]
    return o


def _son_dogru(m: np.ndarray) -> np.ndarray:
    """Her konumda, o konuma kadar (dahil) son True'nun indeksi (yoksa −1)."""
    return np.maximum.accumulate(np.where(m, np.arange(len(m)), -1))


def pencere(M: F.Motor, a: int, b: int, y: int) -> pd.DataFrame:
    s = np.arange(a, b + 1, dtype="int64")
    t, bid, ask, vol = TK.aralik(a - GERI, b + 1)
    o: dict[str, np.ndarray] = {"s": s}
    if len(t) < 10:
        return pd.DataFrame(o)
    e = np.searchsorted(t, (s + 1) * 1000)                            # s saniyesi sonuna kadarki tik sayısı
    son = np.clip(e - 1, 0, len(t) - 1)
    gecerli = e > 0
    p = np.where(gecerli, bid[son], np.nan)
    sv = _seviye(M, s, y)
    atr1 = sv["atr1"]
    for n in GETIRI_N:
        i = np.searchsorted(t, (s - n + 1) * 1000) - 1
        o[f"r{n}"] = np.where(i >= 0, (p - bid[np.maximum(i, 0)]) * y / atr1, np.nan)
    i_saat = np.searchsorted(t, (s - GERI + 1) * 1000)
    hiz = (e - i_saat) / GERI
    for n in TIK_N:
        o[f"tk{n}"] = (e - np.searchsorted(t, (s - n + 1) * 1000)) / (n * np.maximum(hiz, 1e-9))
    kv = np.r_[0.0, np.cumsum(vol)]
    i60 = np.searchsorted(t, (s - 60 + 1) * 1000)
    o["hacim60"] = (kv[e] - kv[i60]) / np.maximum((kv[e] - kv[i_saat]) / 60, 1e-12)
    # spread: s'nin dakikasından önceki 60 dakikanın dakika medyanlarının medyanı
    spr = ask - bid
    dk = t // 60000
    md = pd.Series(spr).groupby(dk).median()
    taban = md.rolling(60, min_periods=10).median().shift(1)
    o["spread"] = spr[son] / taban.reindex(s // 60).to_numpy()
    # son 60 sn aralık (saniye başına uç, 60 saniyelik kayan uç)
    sn = t // 1000
    sec = pd.DataFrame({"sn": sn, "b": bid}).groupby("sn")["b"].agg(["max", "min"])
    tam = sec.reindex(np.arange(a - 60, b + 1))
    hi = tam["max"].rolling(60, min_periods=1).max().to_numpy()[60:]
    lo = tam["min"].rolling(60, min_periods=1).min().to_numpy()[60:]
    o["aralik60"] = (hi - lo) / atr1
    # tik yön dizisi: ardışık aynı yönlü değişim uzunluğu ve son 30 sn yön payı
    d = np.sign(np.diff(bid, prepend=bid[0]))
    nz = np.flatnonzero(d != 0)
    run = np.zeros(len(t))
    if len(nz):
        sg = d[nz]
        degis = np.r_[True, sg[1:] != sg[:-1]]
        bas = np.maximum.accumulate(np.where(degis, np.arange(len(nz)), 0))
        val = sg * (np.arange(len(nz)) - bas + 1)
        j = np.searchsorted(nz, np.arange(len(t)), side="right") - 1
        run = np.where(j >= 0, val[np.maximum(j, 0)], 0.0)
    o["ardisik"] = run[son] * y
    cu, cd = np.r_[0, np.cumsum(d > 0)], np.r_[0, np.cumsum(d < 0)]
    i30 = np.searchsorted(t, (s - 30 + 1) * 1000)
    up, dn = cu[e] - cu[i30], cd[e] - cd[i30]
    o["yon30"] = np.where(up + dn > 0, (up if y > 0 else dn) / np.maximum(up + dn, 1), np.nan)
    # seviyeler: uzaklık ve geçişten bu yana süre
    for ad in ("H4", "H1"):
        ext = sv[f"ext_{ad}"]
        o[f"d_{ad}"] = (p - ext) * y / sv[f"atr_{ad}"]
        gec = np.full(len(s), np.nan)
        for u in np.unique(ext[np.isfinite(ext)]):
            m = ext == u
            ub = _son_dogru((bid - u) * y <= 0)[son[m]]
            beri = np.where(ub >= 0, s[m] - t[np.maximum(ub, 0)] // 1000, YOK_SN)
            gec[m] = np.where((p[m] - u) * y > 0, np.minimum(beri, YOK_SN), -1.0)
        o[f"gecis_{ad}"] = gec
    # gün içi uç: sunucu günü başına koşan uç (başlangıç = pencere başındaki bar ucu)
    sun_t = F.sunucu_ofset(t // 1000)
    gun = (t // 1000 + sun_t) // 86400
    k0 = np.searchsorted(M.bar.t, (a - GERI) // 60 * 60) - 1
    D1 = M.tf["D1"]
    bas0 = D1.kumh[k0] if y > 0 else D1.kuml[k0]
    ayni0 = D1.kova_1m[k0] == gun[0]
    yb = bid * y
    kos = pd.Series(yb).groupby(gun).cummax().to_numpy()
    tohum = bas0 * y if ayni0 else -np.inf
    kos = np.where(gun == gun[0], np.maximum(kos, tohum), kos)
    onceki = np.r_[tohum, kos[:-1]]
    onceki[np.r_[False, gun[1:] != gun[:-1]]] = -np.inf               # yeni sunucu günü: uç sıfırlanır
    yeni = yb > onceki
    sy = _son_dogru(yeni)[son]
    o["gun_yeni_sn"] = np.where(sy >= 0, np.minimum(s - t[np.maximum(sy, 0)] // 1000, YOK_SN), YOK_SN)
    o["gun_uzak"] = (kos[son] - yb[son]) / atr1
    o["sn_dk"] = (s % 60).astype(float)
    o["dk5"] = ((s // 60) % 5).astype(float)
    X = pd.DataFrame(o)
    X.loc[~gecerli, X.columns[1:]] = np.nan
    return X.replace([np.inf, -np.inf], np.nan)


OZELLIKLER = ([f"r{n}" for n in GETIRI_N] + [f"tk{n}" for n in TIK_N]
              + ["hacim60", "spread", "aralik60", "ardisik", "yon30", "d_H4", "gecis_H4", "d_H1", "gecis_H1",
                 "gun_yeni_sn", "gun_uzak", "sn_dk", "dk5"])
