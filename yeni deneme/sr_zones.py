"""
sr_zones.py — 1m destek/direnç (S/R) kümeleme + S/R-temelli giriş/TP planı.

Kullanıcı mimarisi:
  - Son N (vars. 100) adet 1m mumu al.
  - 'cap' genişliğinde (NDX 10 puan, XAU 3 $) bölgeler tara; bir bölgeye mumun
    fitili (high/low) veya kapanışı >3 mumda dokunmuşsa → o bölge S/R seviyesi.
  - BUY sinyali → en yakın DESTEK'ten (fiyatın altı) gir; SELL → en yakın
    DİRENÇ'ten (fiyatın üstü) gir. TP = giriş yönündeki bir sonraki S/R bölgesi.
  - Yukarıdan/aşağıdan kovalama YOK: uygun S/R yoksa veya çok uzaksa işlem AÇMA.

Saf mantık — MT5/HTTP bağımlılığı yok; bot ve testler bunu çağırır.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence


@dataclass
class Zone:
    """Bir S/R bölgesi."""
    center: float        # bölge merkezi (üye dokunuşların ortalaması)
    touches: int         # bölgeye dokunan AYRI mum sayısı
    width: float         # cap genişliği (referans)
    lo: float            # üye dokunuşların min'i
    hi: float            # üye dokunuşların max'ı


@dataclass
class EntryPlan:
    """S/R-temelli giriş planı (pending limit emir için)."""
    direction: str       # BUY / SELL
    entry: float         # giriş (destek/direnç merkezi)
    tp: float
    sl: float
    tp_source: str       # 'sr' | 'fixed'
    entry_zone: Zone
    tp_zone: Optional[Zone]
    reason: str          # gözlem/log için açıklama


def _to_hlc(candles: Iterable) -> list[tuple[float, float, float]]:
    """MT5 rates (numpy structured), dict listesi veya (h,l,c) tuple listesini
    ortak (high, low, close) tuple listesine indir."""
    out: list[tuple[float, float, float]] = []
    for c in candles:
        if isinstance(c, dict):
            out.append((float(c["high"]), float(c["low"]), float(c["close"])))
        elif isinstance(c, (tuple, list)):
            out.append((float(c[0]), float(c[1]), float(c[2])))
        else:  # numpy void / namedtuple-benzeri (MT5 copy_rates satırı)
            out.append((float(c["high"]), float(c["low"]), float(c["close"])))
    return out


def detect_zones(candles: Sequence, width: float,
                 min_touch_candles: int = 4, lookback: int = 100) -> list[Zone]:
    """Son `lookback` mumda, `width` genişlikli yüksek-dokunuşlu S/R bölgelerini bul.

    Algoritma (greedy non-maximum suppression):
      1. Aday merkez = tüm high/low/close fiyatları.
      2. Her aday için, ±width/2 içine fitili/kapanışı düşen KULLANILMAMIŞ mum say.
      3. En çok dokunulan adayı bölge yap; üye mumları 'kullanıldı' işaretle.
      4. Hiçbir aday `min_touch_candles`'a ulaşmayana kadar tekrar et.

    Args:
        candles: 1m mum dizisi (MT5 rates / dict / (h,l,c) tuple).
        width: bölge cap genişliği (fiyat birimi).
        min_touch_candles: bir bölgenin S/R sayılması için min ayrı mum (>3 → 4).
        lookback: son kaç mum incelensin.

    Returns:
        Fiyata göre artan sıralı Zone listesi.
    """
    hlc = _to_hlc(candles)[-lookback:]
    if not hlc:
        return []
    half = width / 2.0
    cands = sorted({round(p, 5) for h, l, c in hlc for p in (h, l, c)})
    used = [False] * len(hlc)
    zones: list[Zone] = []

    def members_of(center: float) -> list[int]:
        out = []
        for i, (h, l, c) in enumerate(hlc):
            if used[i]:
                continue
            if abs(h - center) <= half or abs(l - center) <= half or abs(c - center) <= half:
                out.append(i)
        return out

    while True:
        best_center, best_members = None, []
        for center in cands:
            m = members_of(center)
            if len(m) > len(best_members):
                best_center, best_members = center, m
        if best_center is None or len(best_members) < min_touch_candles:
            break
        # bölge merkezi = üye mumların merkeze EN YAKIN dokunuş fiyatlarının ortalaması
        pts = []
        for i in best_members:
            h, l, c = hlc[i]
            pts.append(min((h, l, c), key=lambda p: abs(p - best_center)))
        zc = sum(pts) / len(pts)
        zones.append(Zone(center=round(zc, 5), touches=len(best_members),
                          width=width, lo=min(pts), hi=max(pts)))
        for i in best_members:
            used[i] = True

    zones.sort(key=lambda z: z.center)
    return zones


def _ema(values: Sequence[float], period: int) -> float:
    """Basit EMA (son değer)."""
    if not values:
        return 0.0
    k = 2.0 / (period + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e


def _atr(hlc: Sequence[tuple], period: int) -> float:
    """ATR (önceki kapanışlı true range, son `period` ortalaması)."""
    if len(hlc) < 2:
        return 0.0
    trs = []
    for i in range(1, len(hlc)):
        h, l, _ = hlc[i]
        pc = hlc[i - 1][2]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    n = min(period, len(trs))
    return sum(trs[-n:]) / n if n else 0.0


def momentum_stretch(candles: Sequence, direction: str,
                     ema_period: int = 20, atr_period: int = 14) -> float:
    """Yöne hizalı momentum gücü = işaretli dist(EMA20)/ATR (backend'in doğruladığı
    `dist_ema20_atr` göstergesinin aynısı). Pozitif & büyük = işlem yönünde güçlü
    momentum ('aşırı momentum'). Mum dizisi tercihen M15 olmalı (backend ile tutarlı).
    """
    hlc = _to_hlc(candles)
    if len(hlc) < ema_period + 2:
        return 0.0
    closes = [c for _, _, c in hlc]
    ema = _ema(closes[-(ema_period * 4):], ema_period)
    atr = _atr(hlc, atr_period)
    if atr <= 0:
        return 0.0
    raw = (closes[-1] - ema) / atr
    return raw if direction.upper() == "BUY" else -raw


def nearest_support(zones: Sequence[Zone], price: float,
                    margin: float = 0.0) -> Optional[Zone]:
    """Fiyatın ALTINDAKİ en yakın bölge (BUY limit girişi için)."""
    below = [z for z in zones if z.center < price - margin]
    return max(below, key=lambda z: z.center) if below else None


def nearest_resistance(zones: Sequence[Zone], price: float,
                       margin: float = 0.0) -> Optional[Zone]:
    """Fiyatın ÜSTÜNDEKİ en yakın bölge (SELL limit girişi için)."""
    above = [z for z in zones if z.center > price + margin]
    return min(above, key=lambda z: z.center) if above else None


def plan_sr_entry(zones: Sequence[Zone], direction: str, price: float,
                  fixed_tp_dist: float, fixed_sl_dist: float,
                  max_entry_dist: float,
                  min_tp_dist: float = 0.0,
                  max_tp_dist: float = float("inf")) -> Optional[EntryPlan]:
    """S/R-temelli giriş planı üret. Uygun S/R yoksa/çok uzaksa None (işlem açma).

    BUY  : en yakın destekten gir; TP = girişin üstündeki bir sonraki direnç.
    SELL : en yakın dirençten gir; TP = girişin altındaki bir sonraki destek.
    SL   : araştırılmış sabit mesafe (fixed_sl_dist). TP S/R yoksa fixed_tp_dist.
    """
    direction = direction.upper()
    if direction == "BUY":
        z = nearest_support(zones, price)
        if z is None:
            return None
        if price - z.center > max_entry_dist:        # destek çok aşağıda → kovalama yok
            return None
        entry = z.center
        tp_zone = nearest_resistance(zones, entry)
        if tp_zone and min_tp_dist <= (tp_zone.center - entry) <= max_tp_dist:
            tp, tp_src = tp_zone.center, "sr"
        else:
            tp, tp_src, tp_zone = entry + fixed_tp_dist, "fixed", None
        sl = entry - fixed_sl_dist
    elif direction == "SELL":
        z = nearest_resistance(zones, price)
        if z is None:
            return None
        if z.center - price > max_entry_dist:
            return None
        entry = z.center
        tp_zone = nearest_support(zones, entry)
        if tp_zone and min_tp_dist <= (entry - tp_zone.center) <= max_tp_dist:
            tp, tp_src = tp_zone.center, "sr"
        else:
            tp, tp_src, tp_zone = entry - fixed_tp_dist, "fixed", None
        sl = entry + fixed_sl_dist
    else:
        return None

    reason = (f"{direction} @S/R={entry:.5f} ({z.touches} dokunuş) "
              f"TP={tp:.5f}[{tp_src}] SL={sl:.5f} | fiyat={price:.5f}")
    return EntryPlan(direction=direction, entry=round(entry, 5), tp=round(tp, 5),
                     sl=round(sl, 5), tp_source=tp_src, entry_zone=z,
                     tp_zone=tp_zone, reason=reason)
