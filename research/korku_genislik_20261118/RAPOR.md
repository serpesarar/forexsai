# Korku genişliği — NDX korku gecesinde Dow ve Russell de korkuda mı? (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/gn.py`.

## Sonuç: X (genişlik doz değil)
NDX K1 geceleri (16:00 AL → ertesi 16:00), g = US30 ve US2000'den aynı gün K1 olanların sayısı.

| ort. bp (n) | g = 0 (yalnız teknoloji) | g = 1 | g = 2 (geniş korku) |
|---|---|---|---|
| ESKİ 2018–21 | +42 (23) | +20 (26) | **+107** (52) |
| YENİ 2021–26 | **+55** (42) | +26 (40) | +47 (64) |
| tüm dönem σ / en kötü | 142 / −407 | 168 / −420 | 243 / −612 |
| MT5 NAS100 tekrarı (tüm) | +46 | +11 | +73 |

- Geniş korkunun üstünlüğü yalnız ESKİ'de var (2020 Mart etkisi: yıl farkı +183). YENİ'de ters dönüyor.
- g=2 − g=0 farkının P değeri 0,79 → ölçüt geçmedi.
- **Bilgi:** kuyruk riskinin neredeyse tamamı geniş korku gecelerinde. Dar korkuda YENİ'de en kötü işlem −147 bp, σ 122. Bu bir doz
  kuralı değil ama lot büyütmeyi düşünürken akılda tutulmalı: geniş korku gecesinde lot artırmak yalnız kuyruğu büyütür.
- g=1 iki dönemde de en zayıf kova. Anlamlı değil, açıklaması yok.
