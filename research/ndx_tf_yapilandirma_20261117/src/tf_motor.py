"""Zaman dilimi motoru — kaynak barlardan 2/3/90/210 dk mum üretir.

ÇAPA (tüm zaman dilimleri aynı): işlem günü New York 17:00'de başlar (= MT5 sunucu gece
yarısı, NY+7; MT5'in kendi H1/H4/D1 sınırı; CME günlük arasının bitişi). Her gün sıfırlanır:
    bar başlangıcı = gün başı + ⌊gün içi dakika / N⌋ · N
- 2, 3, 90 dk 1440'ı tam böler → her gün aynı ızgara. 90 dk ızgarası 09:30 ET'ye tam düşer.
- 210 dk 1440'ı bölmez: günün son barı 14:00–17:00 ET (180 dk, `sure_dk`=180). Böylece hiçbir
  mum iki işlem gününe taşmaz ve 90 ile 210 her 630 dk'da (ve 1260–1440 kuyruğunda) aynı
  sınırda buluşur → 7×90 dk = 3×210 dk.
- DST geçişi Pazar 02:00 NY'de, piyasa kapalıyken olur; işlem günü içinde saat atlamaz
  (bu varsayım `aggregate` içinde ikinci yolla doğrulanır).

OHLC kuralları: open = penceredeki İLK kaynak barın açılışı, close = SON barın kapanışı,
high = max(high), low = min(low) → fitiller kaynak fitillerinin birebir uç değeridir.
vol = toplam, spr = ortalama. `n_nominal` = pencerenin beslemenin işlem saatine düşen kaynak bar
sayısı (`CLOSED`: günlük ara hariç); `tam` = hiç kaynak barı eksik değil. Eksik kaynak barı uydurulmaz; `n_alt` ve `tam` ile işaretlenir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NY = "America/New_York"
DAY_START_H = 17
DAY_MIN = 1440
CLOSED_UNTIL_MIN = 60  # NY 17:00–18:00 günlük ara: NAS100/USATECH işlem görmez
# Beslemenin günlük kapalı dakikaları (işlem günü başından dakika, [başla, bit)).
# Ölçüldü (saat taraması): Dukascopy her gün 16:15–18:00 ET arası bar yok; MT5 Pzt–Per 16:59'a
# kadar işler, yalnız Cuma 16:55'te kapanır (o Cuma barları `tam=False` görünür — gerçek kısa seans).
CLOSED = {"DUKA": ((0, 60), (1395, 1440)), "MT5": ((0, 60),)}


def ny_wall(t: np.ndarray) -> pd.DatetimeIndex:
    return pd.to_datetime(t, unit="s", utc=True).tz_convert(NY).tz_localize(None)


def day_minute(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(işlem günü başlangıcı NY duvar saati, gün içi dakika)."""
    shifted = ny_wall(t) - pd.Timedelta(hours=DAY_START_H)
    day0 = shifted.normalize()
    mins = ((shifted - day0) // pd.Timedelta(minutes=1)).to_numpy().astype(np.int64)
    return day0.to_numpy(), mins


def bucket_length(bucket_min: np.ndarray, n: int) -> np.ndarray:
    return np.minimum(n, DAY_MIN - bucket_min)


def nominal_slots(bmin: np.ndarray, length: np.ndarray, src_tf: int,
                  closed: tuple[tuple[int, int], ...]) -> np.ndarray:
    """Pencerede beklenen kaynak bar sayısı: tamamı kapalı aralığa düşen kaynak dilimleri hariç.

    (Kalın kaynakta kısmen açık dilim — ör. M30 16:30 barı 16:55'te kapanır — beklenir.)
    """
    out = (length // src_tf).astype(np.int64)
    for c0, c1 in closed:
        lo = np.maximum(c0, bmin) - bmin
        hi = np.minimum(c1, bmin + length) - bmin
        k0 = -(-lo // src_tf)  # tavan
        k1 = hi // src_tf
        out -= np.maximum(0, k1 - k0)
    return out


def aggregate(src: pd.DataFrame, src_tf: int, out_tf: int, kaynak_tf: str | None = None,
              closed: tuple[tuple[int, int], ...] = ((0, CLOSED_UNTIL_MIN),)) -> pd.DataFrame:
    """src (t UTC bar açılışı, 1/5/15/30 dk) → out_tf dakikalık mumlar."""
    if out_tf % src_tf:
        raise ValueError(f"{out_tf} dk, {src_tf} dk'nın katı değil")
    t = src["t"].to_numpy()
    if np.any(np.diff(t) <= 0):
        raise ValueError("kaynak zaman sırası bozuk / duplike")
    day0, mins = day_minute(t)
    if np.any(mins % src_tf):
        raise ValueError("kaynak barlar NY 17:00 çapalı ızgarada değil")
    bmin = (mins // out_tf) * out_tf
    if np.any(mins + src_tf > bmin + bucket_length(bmin, out_tf)):
        raise ValueError("kaynak bar hedef pencereye sığmıyor")
    key = t - (mins - bmin) * 60

    # ikinci yol: çapa + kova dakikası NY'de yerelleştirilip UTC'ye çevrilir → aynı olmalı
    wall = pd.DatetimeIndex(day0) + pd.Timedelta(hours=DAY_START_H) + pd.to_timedelta(bmin, unit="m")
    key2 = wall.tz_localize(NY, ambiguous="raise", nonexistent="raise").tz_convert("UTC").asi8 // 10**9
    if not np.array_equal(key, key2):
        raise AssertionError("işlem günü içinde DST atlaması — çapa varsayımı bozuldu")

    g = pd.DataFrame({"k": key, "o": src["open"].to_numpy(), "h": src["high"].to_numpy(),
                      "l": src["low"].to_numpy(), "c": src["close"].to_numpy(),
                      "v": src["vol"].to_numpy(), "s": src["spr"].to_numpy(), "b": bmin})
    gb = g.groupby("k", sort=True)
    a = gb.agg(open=("o", "first"), high=("h", "max"), low=("l", "min"), close=("c", "last"),
               spr=("s", "mean"), n_alt=("o", "size"), bmin=("b", "first"))
    a["vol"] = gb["v"].sum(min_count=1)
    a = a.reset_index().rename(columns={"k": "t"})
    a["sure_dk"] = bucket_length(a["bmin"].to_numpy(), out_tf)
    a["n_nominal"] = nominal_slots(a["bmin"].to_numpy(), a["sure_dk"].to_numpy(), src_tf, closed)
    a["tam"] = a["n_alt"] == a["n_nominal"]
    a["kaynak_tf"] = kaynak_tf or f"{src_tf}m"
    a["zaman_utc"] = pd.to_datetime(a["t"], unit="s", utc=True)
    a["zaman_ny"] = a["zaman_utc"].dt.tz_convert(NY)
    cols = ["t", "zaman_utc", "zaman_ny", "open", "high", "low", "close", "vol", "spr",
            "sure_dk", "n_alt", "n_nominal", "tam", "kaynak_tf"]
    return a[cols]
