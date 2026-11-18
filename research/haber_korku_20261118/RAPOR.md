# Habere dayanan korku ve habersiz korku (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/hb.py`. Makro takvim CPI/NFP/FOMC/JH, → 2026-10-02.

## Sonuç: C+ (habersiz korku daha güçlü dönüyor)
Korku gecesi (K1) ile aynı tür günlerin K1'siz gecelerinin farkı (bp):

| besleme | olay günü fark (n) | habersiz gün fark (n) | ESKİ DD | YENİ DD |
|---|---|---|---|---|
| NDX Duka | +31 (39) | +61 (211) | +68 | +5 |
| MT5 NAS100 | +26 (36) | +56 (197) | +62 | +11 |
| **US30 (kör)** | **−35** (32) | +53 (130) | +173 | +31 |
| **US2000 (kör)** | **−55** (43) | +58 (190) | +213 | +60 |

- Dört beslemede, iki dönemde de habersiz korku daha çok dönüyor. Kör US30/US2000'de makro olay günü korku gecesi iki dönemde de eksi.
- Mekanizma: makro olayla gelen düşüş bilgi taşır ve sürer; akıştan gelen kapanış korkusu döner. Petrol EIA bulgusuyla aynı ilke.
- NDX'te YENİ farkı küçük (+5): NDX'te olay günü korku gecesi hâlâ artı (+42 vs taban −16). Bu yüzden C+.
- **Kullanım önerisi (gölge):** makro olay günü korku gecesinde lotu yarıya indir. Russell/Dow'da bu gecelerde açma. NDX canlı kuralına
  yalnız etiket olarak eklenmeli; ileri ölçüm sonra.
