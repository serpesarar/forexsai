"""naming.py — mum dizisi / kapanış yolu için Türkçe formasyon adı.

Zigzag pivotları (eşik = yüksekliğin %28'i) + bacak sayısı + seviye karşılaştırması.
Kurallar kasıtlı olarak basit ve açıklanabilir: amaç teknik-analiz literatüründeki
adla "aynı şeyi gördüğümüzü" söylemek, gizli bir sınıflandırıcı değil.
"""
from __future__ import annotations

import numpy as np

ZZ = 0.28            # pivot eşiği (yüksekliğin oranı)
SPIKE = 0.35         # tek mumda yüksekliğin ≥%35'i → "flaş"
LEVEL_EQ = 0.15      # iki tepe/dip "eşit" sayılma toleransı


def zigzag(y: np.ndarray, thr: float = ZZ) -> list[tuple[int, float]]:
    """[0,1]'e ölçekli yol → pivotlar (başlangıç + teyitli iç pivotlar + bitiş).

    Bir pivot ancak karşı yönde ≥ thr hareketle teyit edilir; bitişteki thr'den
    küçük geri çekilme yeni bacak sayılmaz.
    """
    n = len(y)
    piv = [(0, float(y[0]))]
    trend, hi_i, lo_i, ext = 0, 0, 0, 0
    for i in range(1, n):
        if trend == 0:
            hi_i = i if y[i] > y[hi_i] else hi_i
            lo_i = i if y[i] < y[lo_i] else lo_i
            if y[hi_i] - y[lo_i] >= thr:
                if hi_i > lo_i:
                    if lo_i > 0 and y[0] - y[lo_i] >= thr:
                        piv.append((lo_i, float(y[lo_i])))
                    trend, ext = 1, hi_i
                else:
                    if hi_i > 0 and y[hi_i] - y[0] >= thr:
                        piv.append((hi_i, float(y[hi_i])))
                    trend, ext = -1, lo_i
        elif trend == 1:
            if y[i] > y[ext]:
                ext = i
            elif y[ext] - y[i] >= thr:
                piv.append((ext, float(y[ext])))
                trend, ext = -1, i
        else:
            if y[i] < y[ext]:
                ext = i
            elif y[i] - y[ext] >= thr:
                piv.append((ext, float(y[ext])))
                trend, ext = 1, i
    piv.append((n - 1, float(y[-1])))
    return piv


def describe(close_path: np.ndarray) -> dict:
    """Ad + kısa açıklama + yön dizisi."""
    p = np.asarray(close_path, float)
    y = (p - p.min()) / max(p.max() - p.min(), 1e-12)
    piv = zigzag(y)
    legs = [np.sign(b[1] - a[1]) for a, b in zip(piv[:-1], piv[1:])]
    # ardışık aynı yönlü bacakları birleştir
    merged: list[float] = []
    for s in legs:
        if not merged or s != merged[-1]:
            merged.append(s)
    seq = "".join("↑" if s > 0 else "↓" for s in merged)
    spike = float(np.max(np.abs(np.diff(y)))) >= SPIKE
    imax, imin = int(np.argmax(y)), int(np.argmin(y))
    net = float(y[-1] - y[0])
    family = _name(merged, piv, y, net, imax, imin)
    name = "Flaş " + family if spike else family
    return {"name": name, "family": family, "seq": seq, "net": round(net, 3), "spike": spike,
            "pivots": [(int(i), round(v, 3)) for i, v in piv]}


def _name(m: list[float], piv, y, net, imax, imin) -> str:
    n = len(m)
    if n <= 1:
        return "Kararlı Yükseliş" if net > 0 else "Kararlı Düşüş"
    inner = piv[1:-1]
    highs = [v for i, v in inner if v >= 0.5]
    lows = [v for i, v in inner if v < 0.5]
    if n == 2:
        if m[0] < 0:   # ↓↑
            rec = y[-1]
            return "V-Dip Dönüşü" if rec >= 0.7 else "Düşüş + Zayıf Tepki"
        rec = 1 - y[-1]
        return "Ters-V Tepe Dönüşü" if rec >= 0.7 else "Yükseliş + Sınırlı Geri Çekilme"
    if n == 3:
        if m[0] > 0:   # ↑↓↑
            if y[-1] >= 0.9 and imax == len(y) - 1:
                return "Yükseliş – Düzeltme – Devam (Boğa Bayrağı)"
            if imin > 0.4 * len(y) and y[imin] < 0.15:
                return "Yükseliş – Çöküş – Toparlanma"
            return "Yükseliş – Geri Çekilme – Tepki"
        if y[-1] <= 0.1 and imin == len(y) - 1:
            return "Düşüş – Tepki – Devam (Ayı Bayrağı)"
        if imax > 0.4 * len(y) and y[imax] > 0.85:
            return "Düşüş – Sıçrama – Geri Satış"
        return "Düşüş – Tepki – Zayıflama"
    if n == 4:
        if m[0] < 0 and len(lows) >= 2 and abs(lows[0] - lows[-1]) <= LEVEL_EQ:
            return "Çift Dip (W)"
        if m[0] > 0 and len(highs) >= 2 and abs(highs[0] - highs[-1]) <= LEVEL_EQ:
            return "Çift Tepe (M)"
        return "Testere – " + ("Yukarı Kapanış" if net > 0 else "Aşağı Kapanış")
    tops = [v for (i, v), s in zip(piv[1:-1], m[:-1]) if s > 0]
    bots = [v for (i, v), s in zip(piv[1:-1], m[:-1]) if s < 0]
    if len(tops) >= 3 and tops[1] > max(tops[0], tops[2]) + 0.1:
        return "Omuz-Baş-Omuz (OBO)"
    if len(bots) >= 3 and bots[1] < min(bots[0], bots[2]) - 0.1:
        return "Ters Omuz-Baş-Omuz (TOBO)"
    return "Yatay Bant / Testere"


# ─── Mum dizisi adlandırma (değişken uzunluklu motifler) ───────────────────────
DOJI_BODY = 0.10      # gövde/aralık < %10 → doji
LONG_WICK = 2.0       # fitil ≥ 2×gövde → çekiç / kayan yıldız
MARU_BODY = 0.85      # gövde/aralık ≥ %85 → marubozu


def candle_type(o: float, h: float, l: float, c: float) -> str:
    rng = max(h - l, 1e-12)
    body = abs(c - o)
    up, lo = h - max(o, c), min(o, c) - l
    if body / rng < DOJI_BODY:
        return "Doji"
    if lo >= LONG_WICK * body and up <= body:
        return "Çekiç" if c >= o else "Asılı Adam"
    if up >= LONG_WICK * body and lo <= body:
        return "Ters Çekiç" if c >= o else "Kayan Yıldız"
    if body / rng >= MARU_BODY:
        return "Yeşil Marubozu" if c > o else "Kırmızı Marubozu"
    return "Yeşil" if c > o else "Kırmızı"


def name_candles(ohlc: np.ndarray) -> dict:
    """k mumluk dizi → klasik mum formasyonu adı (k≤3) veya yol + mum bileşimi adı."""
    a = np.asarray(ohlc, float)
    k = len(a)
    types = [candle_type(*row) for row in a]
    bull = a[:, 3] > a[:, 0]
    body = np.abs(a[:, 3] - a[:, 0])
    rng = np.maximum(a[:, 1] - a[:, 2], 1e-12)
    name = None
    if k == 2:
        o1, c1, o2, c2 = a[0, 0], a[0, 3], a[1, 0], a[1, 3]
        if not bull[0] and bull[1] and c2 >= o1 and o2 <= c1:
            name = "Yutan Boğa"
        elif bull[0] and not bull[1] and c2 <= o1 and o2 >= c1:
            name = "Yutan Ayı"
    if k == 3:
        mid1 = (a[0, 0] + a[0, 3]) / 2
        if bull.all() and np.all(np.diff(a[:, 3]) > 0) and np.all(body / rng >= 0.5):
            name = "Üç Beyaz Asker"
        elif (~bull).all() and np.all(np.diff(a[:, 3]) < 0) and np.all(body / rng >= 0.5):
            name = "Üç Kara Karga"
        elif not bull[0] and body[1] < 0.5 * body[0] and bull[2] and a[2, 3] > mid1:
            name = "Sabah Yıldızı"
        elif bull[0] and body[1] < 0.5 * body[0] and not bull[2] and a[2, 3] < mid1:
            name = "Akşam Yıldızı"
    path = np.concatenate([[a[0, 0]], a[:, 3]])
    shape = describe(path) if k >= 4 else None
    if name is None:
        if k <= 4:
            name = " → ".join(types)
        else:
            name = shape["name"] if k >= 10 else shape["family"]   # kısa yolda "flaş" anlamsız
    doji = np.array([t == "Doji" for t in types])
    n_bull = int((bull & ~doji).sum())
    n_bear = int((~bull & ~doji).sum())
    big = int((body >= np.median(body) * 2).sum()) if k >= 3 else 0
    return {"name": name, "types": types, "family": shape["family"] if shape else name,
            "composition": f"{n_bull} yeşil / {n_bear} kırmızı" + (f" / {int(doji.sum())} doji" if doji.any() else ""),
            "big_candles": big}
