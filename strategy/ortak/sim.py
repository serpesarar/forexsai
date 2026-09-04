"""Simülasyon çekirdeği — SIZINTISIZ.

Kurallar (hepsi bu oturumda pahalıya öğrenildi):
  * Özellikler YALNIZ girişten önce KAPANMIŞ barlardan (koşan bar elenir).
  * Aynı barda TP+SL → konservatif KAYIP.
  * Sürtünme her işlemde düşülür (varsayılan 2 puan).
"""
from __future__ import annotations
from bisect import bisect_left, bisect_right

SPREAD = 2.0
UFUK_SAAT = 48


def yaris(v, ts: float, giris: float, yon: str, tp_d: float, sl_d: float,
          saat: int = UFUK_SAAT, spread: float = SPREAD) -> tuple[float, str]:
    """Girişten SONRAKI barlarla TP/SL yarışı. Dönen: (puan_pnl, sonuç)."""
    i = bisect_right(v.bar_ts, ts)
    son = ts + saat * 3600
    sgn = 1 if yon == "BUY" else -1
    for k in range(i, len(v.barlar)):
        t, o, h, l, c = v.barlar[k]
        if t > son:
            return sgn * (c - giris) - spread, "timeout"
        htp = (h >= giris + tp_d) if sgn > 0 else (l <= giris - tp_d)
        hsl = (l <= giris - sl_d) if sgn > 0 else (h >= giris + sl_d)
        if htp and hsl:
            return -sl_d - spread, "sl"
        if htp:
            return tp_d - spread, "tp"
        if hsl:
            return -sl_d - spread, "sl"
    return 0.0, "acik"


def _kapali_idx(bars, ts: float) -> int:
    """ts'den ÖNCE kapanmış son barın indeksi+1 (koşan bar hariç)."""
    lo, hi = 0, len(bars)
    while lo < hi:
        m = (lo + hi) // 2
        if bars[m][0] < ts - 60:
            lo = m + 1
        else:
            hi = m
    return lo


def atr(bars, ts: float, n: int = 14) -> float | None:
    """Ortalama TR — yalnız kapanmış barlar."""
    i = _kapali_idx(bars, ts)
    seg = bars[max(0, i - (n + 1)):i]
    if len(seg) < 2:
        return None
    trs = [max(seg[j][2] - seg[j][3], abs(seg[j][2] - seg[j - 1][4]),
               abs(seg[j][3] - seg[j - 1][4])) for j in range(1, len(seg))]
    return sum(trs) / len(trs) if trs else None


def sikisma(bars, ts: float, hizli: int = 14, yavas: int = 100) -> float | None:
    """ATR(hızlı)/ATR(yavaş) — <1 sakin piyasa."""
    a, b = atr(bars, ts, hizli), atr(bars, ts, yavas)
    return (a / b) if (a and b) else None


_piv_cache: dict = {}


def pivotlar(bars, etiket: str, ts: float, geri: int = 100, k: int = 2,
             tol: float = 8.0) -> list[tuple[str, float, int]]:
    """Fraktal pivotları kümele. Dönen: [(tip 'R'/'S', seviye, dokunuş), ...]"""
    son = _kapali_idx(bars, ts) - 1
    if son < k * 2 + 5:
        return []
    key = (etiket, son, geri, k)
    if key in _piv_cache:
        return _piv_cache[key]
    seg = bars[max(0, son - geri + 1):son + 1]
    ham = []
    for i in range(k, len(seg) - k):
        if all(seg[i][2] >= seg[j][2] for j in range(i - k, i + k + 1) if j != i):
            ham.append(("R", seg[i][2]))
        if all(seg[i][3] <= seg[j][3] for j in range(i - k, i + k + 1) if j != i):
            ham.append(("S", seg[i][3]))
    kume: list = []
    for tip, p in sorted(ham, key=lambda x: x[1]):
        if kume and kume[-1][0] == tip and abs(kume[-1][1] - p) <= tol:
            n = kume[-1][2] + 1
            kume[-1] = (tip, (kume[-1][1] * kume[-1][2] + p) / n, n)
        else:
            kume.append((tip, p, 1))
    _piv_cache[key] = kume
    return kume


def konum(v, ts: float, saat: float) -> float | None:
    """Fiyatın son `saat` saatlik aralıktaki yeri: 0=dip, 1=tepe."""
    i0 = bisect_left(v.bar_ts, ts - saat * 3600)
    i1 = bisect_left(v.bar_ts, ts)
    seg = v.barlar[i0:i1]
    if len(seg) < 10:
        return None
    hi = max(x[2] for x in seg)
    lo = min(x[3] for x in seg)
    return (seg[-1][4] - lo) / (hi - lo) if hi > lo else 0.5
