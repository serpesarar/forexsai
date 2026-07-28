"""fix_time.py — candle_cache bar zaman damgalarındaki BROKER SAATİ kaymasını düzelt.

KEŞİF (2026-07-28, bu araştırmada bulundu — canlı sistemi de ilgilendiren bir HATA):
`candle_cache`'e yazılan barların zaman damgası MT5 **broker sunucu saati**
(kış UTC+2 / ABD-yaz UTC+3) iken UTC olarak etiketleniyor. `prediction_logs.created_at`
ise gerçek UTC. Yani sinyal ile mum aynı saat ekseninde DEĞİL.

ÜÇ BAĞIMSIZ KANIT
1. Saat profili: ABD nakit açılışı (13:30 UTC) 1m barlarda 16:30 etiketinde patlıyor.
2. Panelin kendi kaydettiği anlık fiyat (`prediction_logs.ml_entry_price`, gerçek UTC)
   ile bar kapanışı arasındaki medyan mutlak fark: offset 0'da 71.8 puan,
   offset −180 dk'da **19.9 puan**.
3. Ay bazında ölçülen en iyi offset DST ile tutarlı: 03-08 (ABD yaz saati) öncesi
   −120, sonrası −180, ve **2026-07-16'da 0'a düşüyor** (o tarihte bir düzeltme inmiş).

ETKİSİ
* Sinyal↔bar bağlantısı kuran her analiz bozuk: işlem sinyalden 3 saat ÖNCE açılıyor,
  özellikler 3 saat bayat. (dataset.parquet / episodes.parquet ilk sürümleri.)
* Yalnız bar-bar analizleri (geometri taraması, uzun ızgara) İÇ TUTARLI → geçerli;
  yalnız saat/seans etiketleri ve günlük makro birleşimi 3 saat kaymış olur.
* ⚠️ `bot_router.py`'deki "momentum filtresi: filtresiz %51.4 → filtreli %78.6" OOS
  doğrulaması büyük olasılıkla AYNI kaymanın ürünü: kaymış eşlemede panel snapshot'ı
  işlemin ilk 3 saatini bilir → yapay yüksek isabet. Denetim gerekir.
"""
from __future__ import annotations

import pandas as pd

# (başlangıç, bitiş, dakika cinsinden düzeltme) — bar_ts + offset = gerçek UTC
OFFSETS = [
    (pd.Timestamp("2000-01-01", tz="UTC"), pd.Timestamp("2026-03-08", tz="UTC"), -120),
    (pd.Timestamp("2026-03-08", tz="UTC"), pd.Timestamp("2026-07-16", tz="UTC"), -180),
    (pd.Timestamp("2026-07-16", tz="UTC"), pd.Timestamp("2100-01-01", tz="UTC"), 0),
]


def correct(df: pd.DataFrame, col: str = "ts") -> pd.DataFrame:
    """Bar zaman damgalarını gerçek UTC'ye çevir."""
    d = df.copy()
    t = pd.to_datetime(d[col], utc=True)
    shift = pd.Series(pd.Timedelta(0), index=d.index)
    for lo, hi, mins in OFFSETS:
        m = (t >= lo) & (t < hi)
        shift[m] = pd.Timedelta(minutes=mins)
    d[col] = t + shift
    return d.sort_values(col).drop_duplicates(col).reset_index(drop=True)
