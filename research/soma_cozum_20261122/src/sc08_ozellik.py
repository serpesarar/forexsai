"""SC-08 — çok zaman dilimli nedensel özellik motoru (sorgu noktası başına).

Sorgu: (k, p, y, t_simdi). k = son TAMAMLANMIŞ 1m bar indeksi, p = anlık bid fiyatı, y = yön (±1), t_simdi = sorgu anı (UTC sn).
Üst zaman dilimi mumları broker SUNUCU saatine (ny7: UTC+2 kış / +3 ABD yaz saati) göre kovalanır → H4/D1 mumları
sağlayıcının MT5'te gördüğüyle aynı sınırlardadır. Her zaman diliminde:
  - "c_" önekli: son tamamlanmış mumdan (b−1),
  - "a_" önekli: oluşan mum + anlık fiyat p ile güncellenmiş (EMA/RSI/BB/Stokastik/Donchian kırılımı).
Yöne hizalı özellikler y ile çarpılır (alışta yukarı = +). Mesafeler o zaman diliminin ATR14'ü biriminde.
Doğruluk: tests/test_sc08.py (yavaş pandas referansıyla eşitlik + nedensellik).
"""
from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import sc_veri as V

NY = ZoneInfo("America/New_York")
TF_DK = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
EMA_N = (9, 20, 50, 100, 200)


def sunucu_ofset(t: np.ndarray) -> np.ndarray:
    """ny7 sunucu ofseti (sn) her UTC zamanı için; saat başına bir kez hesaplanır."""
    saat = t // 3600
    u = np.unique(saat)
    z = pd.to_datetime(u * 3600, unit="s", utc=True).tz_convert(NY)
    yaz = np.array([x.dst().total_seconds() > 0 for x in z])
    of = np.where(yaz, 3 * 3600, 2 * 3600)
    return of[np.searchsorted(u, saat)]


def _wilder(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).ewm(alpha=1 / n, adjust=False).mean().to_numpy()


def _ema(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


@dataclass
class TF:
    """Tamamlanmış mum serisi + göstergeler (indeks = mum sırası) ve 1m → mum eşlemesi."""
    ad: str
    kova_1m: np.ndarray        # her 1m barın mum kovası
    kova: np.ndarray           # mum kovaları (sıralı, benzersiz)
    O: np.ndarray
    H: np.ndarray
    L: np.ndarray
    C: np.ndarray
    Vo: np.ndarray
    ilk_1m: np.ndarray         # mumun ilk 1m bar indeksi
    kumh: np.ndarray           # 1m bazında mum içi kümülatif tepe / dip
    kuml: np.ndarray
    g: dict                    # göstergeler


def tf_kur(bar: V.Bar, vol: np.ndarray, sun: np.ndarray, dk: int) -> TF:
    kova_1m = (bar.t + sun) // (dk * 60)
    kova, ilk, ters = np.unique(kova_1m, return_index=True, return_inverse=True)
    son = np.r_[ilk[1:], len(bar)] - 1
    O, C = bar.o[ilk], bar.c[son]
    H = np.maximum.reduceat(bar.h, ilk)
    L = np.minimum.reduceat(bar.l, ilk)
    Vo = np.add.reduceat(vol, ilk)
    kumh = pd.Series(bar.h).groupby(ters).cummax().to_numpy()
    kuml = pd.Series(bar.l).groupby(ters).cummin().to_numpy()
    g: dict[str, np.ndarray] = {}
    onc = np.r_[C[0], C[:-1]]
    tr = np.maximum(H, onc) - np.minimum(L, onc)
    g["atr"] = _wilder(tr, 14)
    g["atr_med"] = pd.Series(g["atr"]).rolling(100, min_periods=20).median().to_numpy()
    for n in EMA_N:
        g[f"ema{n}"] = _ema(C, n)
    d = np.diff(C, prepend=C[0])
    g["rs_up"], g["rs_dn"] = _wilder(np.maximum(d, 0), 14), _wilder(np.maximum(-d, 0), 14)
    e12, e26 = _ema(C, 12), _ema(C, 26)
    g["e12"], g["e26"] = e12, e26
    g["macd"] = e12 - e26
    g["macd_sig"] = _ema(g["macd"], 9)
    s19 = pd.Series(C).rolling(19)
    g["sum19"], g["sq19"] = s19.sum().to_numpy(), pd.Series(C ** 2).rolling(19).sum().to_numpy()
    g["sma20"] = pd.Series(C).rolling(20).mean().to_numpy()
    g["std20"] = pd.Series(C).rolling(20).std(ddof=0).to_numpy()
    g["hh13"] = pd.Series(H).rolling(13).max().to_numpy()
    g["ll13"] = pd.Series(L).rolling(13).min().to_numpy()
    for n in (20, 55):
        g[f"hh{n}"] = pd.Series(H).rolling(n).max().to_numpy()
        g[f"ll{n}"] = pd.Series(L).rolling(n).min().to_numpy()
    up, dn = np.diff(H, prepend=H[0]), -np.diff(L, prepend=L[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atrw = _wilder(tr, 14)
    g["di_p"] = 100 * _wilder(pdm, 14) / atrw
    g["di_n"] = 100 * _wilder(ndm, 14) / atrw
    dx = 100 * np.abs(g["di_p"] - g["di_n"]) / np.maximum(g["di_p"] + g["di_n"], 1e-12)
    g["adx"] = _wilder(dx, 14)
    g["vol20"] = pd.Series(Vo).rolling(20).mean().to_numpy()
    renk = np.sign(C - O)
    seri = np.zeros(len(C))
    for i in range(1, len(C)):
        seri[i] = seri[i - 1] + renk[i] if renk[i] != 0 and np.sign(seri[i - 1]) in (0, renk[i]) else renk[i]
    g["seri"] = seri
    gecis = np.sign(g["macd"] - g["macd_sig"])
    yas = np.zeros(len(C))
    for i in range(1, len(C)):
        yas[i] = yas[i - 1] + 1 if gecis[i] == gecis[i - 1] else 0
    g["macd_yas"] = yas
    return TF("", kova_1m, kova, O, H, L, C, Vo, ilk, kumh, kuml, g)


class Motor:
    def __init__(self, bar: V.Bar, vol: np.ndarray):
        self.bar, self.vol = bar, vol
        self.sun = sunucu_ofset(bar.t)
        self.tf = {ad: tf_kur(bar, vol, self.sun, dk) for ad, dk in TF_DK.items()}
        self.vol20_1m = pd.Series(vol).rolling(20, min_periods=5).mean().to_numpy()
        self.vol60_1m = pd.Series(vol).rolling(60, min_periods=10).mean().to_numpy()

    # ───────── tek zaman dilimi ─────────
    def _tf_ozellik(self, ad: str, k: np.ndarray, p: np.ndarray, y: np.ndarray, t_simdi: np.ndarray) -> dict:
        T = self.tf[ad]
        g = T.g
        dk = TF_DK[ad]
        kova_simdi = (t_simdi + self.sun[k]) // (dk * 60)
        b = np.searchsorted(T.kova, kova_simdi)                 # oluşan mumun konumu (yoksa yeni mum)
        oldu = (b < len(T.kova)) & (T.kova[np.minimum(b, len(T.kova) - 1)] == kova_simdi)
        bc = b - 1                                              # son tamamlanmış mum
        bc = np.clip(bc, 1, len(T.C) - 1)
        k_ayni = oldu & (T.kova_1m[k] == kova_simdi)            # k barı oluşan mumun içinde mi
        f_O = np.where(k_ayni, T.O[np.minimum(b, len(T.O) - 1)], p)
        f_H = np.where(k_ayni, np.maximum(T.kumh[k], p), p)
        f_L = np.where(k_ayni, np.minimum(T.kuml[k], p), p)
        atr = g["atr"][bc]
        o: dict[str, np.ndarray] = {}
        P = f"{ad}_"
        C = T.C[bc]
        for n in EMA_N:
            e = g[f"ema{n}"][bc]
            al = 2 / (n + 1)
            o[P + f"c_ema{n}"] = y * (C - e) / atr
            o[P + f"a_ema{n}"] = y * (p - (e + al * (p - e))) / atr
            o[P + f"egim{n}"] = y * (e - g[f"ema{n}"][bc - 1]) / atr
        es = np.stack([g[f"ema{n}"][bc] for n in EMA_N])
        o[P + "ema_sira"] = (np.sign(es[:-1] - es[1:]) == y).sum(0).astype(float)
        rs = g["rs_up"][bc] / np.maximum(g["rs_dn"][bc], 1e-12)
        rsi = 100 - 100 / (1 + rs)
        d = p - C
        up = g["rs_up"][bc] + (np.maximum(d, 0) - g["rs_up"][bc]) / 14
        dn = g["rs_dn"][bc] + (np.maximum(-d, 0) - g["rs_dn"][bc]) / 14
        a_rsi = 100 - 100 / (1 + up / np.maximum(dn, 1e-12))
        o[P + "c_rsi"] = np.where(y > 0, rsi, 100 - rsi)
        o[P + "a_rsi"] = np.where(y > 0, a_rsi, 100 - a_rsi)
        o[P + "c_macdh"] = y * (g["macd"][bc] - g["macd_sig"][bc]) / atr
        a12 = g["e12"][bc] + 2 / 13 * (p - g["e12"][bc])
        a26 = g["e26"][bc] + 2 / 27 * (p - g["e26"][bc])
        a_m = a12 - a26
        a_s = g["macd_sig"][bc] + 0.2 * (a_m - g["macd_sig"][bc])
        o[P + "a_macdh"] = y * (a_m - a_s) / atr
        o[P + "c_macd0"] = y * g["macd"][bc] / atr
        o[P + "macd_yas"] = np.where(np.sign(g["macd"][bc] - g["macd_sig"][bc]) == y, g["macd_yas"][bc], -g["macd_yas"][bc] - 1)
        bb = (C - g["sma20"][bc]) / np.maximum(2 * g["std20"][bc], 1e-12)
        m20 = (g["sum19"][bc] + p) / 20
        v20 = (g["sq19"][bc] + p ** 2) / 20 - m20 ** 2
        a_bb = (p - m20) / np.maximum(2 * np.sqrt(np.maximum(v20, 0)), 1e-12)
        o[P + "c_bb"], o[P + "a_bb"] = y * bb, y * a_bb
        hh, ll = np.maximum(g["hh13"][bc - 0], f_H), np.minimum(g["ll13"][bc], f_L)
        st = (p - ll) / np.maximum(hh - ll, 1e-12) * 100
        o[P + "a_stoch"] = np.where(y > 0, st, 100 - st)
        o[P + "adx"] = g["adx"][bc]
        o[P + "di"] = y * (g["di_p"][bc] - g["di_n"][bc])
        o[P + "atr_oran"] = atr / g["atr_med"][bc]
        o[P + "atr_bp"] = atr / C * 1e4
        for n in (20, 55):
            hh_, ll_ = g[f"hh{n}"][bc], g[f"ll{n}"][bc]
            o[P + f"c_don{n}"] = np.where(y > 0, (C - ll_), (hh_ - C)) / np.maximum(hh_ - ll_, 1e-12)
            o[P + f"a_kir{n}"] = np.where(y > 0, p - hh_, ll_ - p) / atr        # > 0: anlık fiyat N mum tepesini/dibini aştı
        rng_ = np.maximum(T.H[bc] - T.L[bc], 1e-12)
        o[P + "c_govde"] = y * (C - T.O[bc]) / rng_
        o[P + "c_renk"] = y * np.sign(C - T.O[bc])
        o[P + "c_seri"] = y * g["seri"][bc]
        o[P + "c_vol"] = T.Vo[bc] / g["vol20"][bc]
        o[P + "a_mum"] = y * (p - f_O) / atr                                     # oluşan mumun yönü
        o[P + "a_onceki_kir"] = np.where(y > 0, p - T.H[bc], T.L[bc] - p) / atr  # önceki mumun tepesini/dibini aştı mı
        o[P + "a_mum_konum"] = np.where(y > 0, (p - f_L), (f_H - p)) / np.maximum(f_H - f_L, 1e-12)
        return o

    # ───────── seviyeler ─────────
    def _seviye(self, k: np.ndarray, p: np.ndarray, y: np.ndarray, t_simdi: np.ndarray) -> dict:
        D = self.tf["D1"]
        H1 = self.tf["H1"]
        atr = H1.g["atr"][np.clip(np.searchsorted(H1.kova, (t_simdi + self.sun[k]) // 3600) - 1, 0, len(H1.C) - 1)]
        gun = (t_simdi + self.sun[k]) // 86400
        b = np.searchsorted(D.kova, gun)
        bc = np.clip(b - 1, 0, len(D.C) - 1)
        oldu = (b < len(D.kova)) & (D.kova[np.minimum(b, len(D.kova) - 1)] == gun) & (D.kova_1m[k] == gun)
        acilis = np.where(oldu, D.O[np.minimum(b, len(D.O) - 1)], p)
        pH, pL, pC = D.H[bc], D.L[bc], D.C[bc]
        piv = (pH + pL + pC) / 3
        o = {}
        yon_lvl = lambda lv: y * (p - lv) / atr  # noqa: E731  (+ = seviyenin yön tarafında)
        o["SV_onc_gun_tepe"] = np.where(y > 0, p - pH, pL - p) / atr           # >0: önceki gün tepesi/dibi kırıldı
        o["SV_onc_gun_dip_karsi"] = np.where(y > 0, p - pL, pH - p) / atr
        o["SV_gun_acilis"] = yon_lvl(acilis)
        o["SV_onc_kapanis"] = yon_lvl(pC)
        o["SV_pivot"] = yon_lvl(piv)
        r1, s1 = 2 * piv - pL, 2 * piv - pH
        o["SV_R1S1"] = np.where(y > 0, p - r1, s1 - p) / atr
        D1 = self.tf["D1"]
        gun_tepe = np.where(oldu, np.maximum(D1.kumh[k], p), p)
        gun_dip = np.where(oldu, np.minimum(D1.kuml[k], p), p)
        o["SV_gun_konum"] = np.where(y > 0, p - gun_dip, gun_tepe - p) / np.maximum(gun_tepe - gun_dip, 1e-12)
        o["SV_gun_tepeye"] = np.where(y > 0, gun_tepe - p, p - gun_dip) / atr  # gün içi uca uzaklık
        hafta = (t_simdi + self.sun[k] - 4 * 86400) // (7 * 86400)
        wk = (D.kova * 86400 - 4 * 86400) // (7 * 86400)
        wH = pd.Series(D.H).groupby(wk).max()
        wL = pd.Series(D.L).groupby(wk).min()
        onc_h = wH.reindex(hafta - 1).to_numpy()
        onc_l = wL.reindex(hafta - 1).to_numpy()
        o["SV_onc_hafta"] = np.where(y > 0, p - onc_h, onc_l - p) / atr
        for r in (10, 50, 100):
            yakin = np.where(y > 0, np.ceil(p / r) * r, np.floor(p / r) * r)
            o[f"SV_yuvarlak{r}"] = np.abs(yakin - p) / atr                     # yöndeki ilk yuvarlak sayıya uzaklık
            o[f"SV_yuvarlak{r}_arka"] = np.abs(p - np.where(y > 0, np.floor(p / r) * r, np.ceil(p / r) * r)) / atr
        # Asya seansı (00–07 UTC) tepe/dip
        z_gun = t_simdi // 86400
        m1 = self.bar
        asya = ((m1.t % 86400) < 7 * 3600)
        gk = m1.t // 86400
        aH = pd.Series(np.where(asya, m1.h, -np.inf)).groupby(gk).max()
        aL = pd.Series(np.where(asya, m1.l, np.inf)).groupby(gk).min()
        sonra = (t_simdi % 86400) >= 7 * 3600
        ah, alw = aH.reindex(z_gun).to_numpy(), aL.reindex(z_gun).to_numpy()
        o["SV_asya_kir"] = np.where(sonra, np.where(y > 0, p - ah, alw - p) / atr, np.nan)
        return o

    def _zaman_hacim(self, k: np.ndarray, t_simdi: np.ndarray) -> dict:
        z = pd.to_datetime(t_simdi, unit="s", utc=True)
        sun = pd.to_datetime(t_simdi + self.sun[k], unit="s", utc=True)
        v = self.vol
        v5 = pd.Series(v).rolling(5).sum().to_numpy()
        return {"Z_saat": z.hour.to_numpy().astype(float), "Z_sunucu_saat": sun.hour.to_numpy().astype(float),
                "Z_dakika": z.minute.to_numpy().astype(float), "Z_gun": z.dayofweek.to_numpy().astype(float),
                "HC_vol1": v[k] / self.vol20_1m[k], "HC_vol5": v5[k] / (5 * self.vol60_1m[k])}

    def ozellik(self, k: np.ndarray, p: np.ndarray, y: np.ndarray, t_simdi: np.ndarray) -> pd.DataFrame:
        k, p, y, t_simdi = (np.asarray(a) for a in (k, p, y, t_simdi))
        o: dict = {}
        for ad in TF_DK:
            o.update(self._tf_ozellik(ad, k, p, y, t_simdi))
        o.update(self._seviye(k, p, y, t_simdi))
        o.update(self._zaman_hacim(k, t_simdi))
        X = pd.DataFrame(o)
        return X.replace([np.inf, -np.inf], np.nan)  # sıfıra bölme (ör. Asya seansı barı yok) → eksik, sonsuz değil


def yukle(bas: str = "2023-01-01") -> Motor:
    d = pd.read_parquet(V.BAR_CACHE, columns=["t", "vol"])
    bar = V.barlar()
    i = np.searchsorted(bar.t, pd.Timestamp(bas, tz="UTC").timestamp())
    assert np.array_equal(d["t"].to_numpy()[i:], bar.t[i:])
    return Motor(bar.dilim(i, len(bar)), d["vol"].to_numpy(float)[i:])
