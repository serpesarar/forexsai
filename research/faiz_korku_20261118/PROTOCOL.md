# Ön kayıt — Korkunun kaynağı: faiz şoku mu, büyüme korkusu mu? (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
K1 korku gecesi (§2.71) kaynağına bakmadan alır. İki farklı korku olabilir:
- **Faiz korkusu:** 10 yıllık getiri aynı gün yükselir. Değerleme şokudur; 2022'de süreklilik gösterdi.
- **Güvenliğe kaçış / büyüme korkusu:** getiri düşer.
Hangisinin daha iyi döndüğü defterde sınanmadı. Yalnız KT-02 ile Yön Lab, koşulsuz yön için TNX'in çapraz varlık bilgisini sınadı (X).

## Veri
- NDX Duka (K1, 16:00 → ertesi 16:00).
- ^TNX günlük kapanış (yfinance, `qs03_akis_takvim_20261111/data/TNX.parquet`). Faiz endeksinin kapanışı ≤ 16:00 ET'dir; aynı gün
  kullanılır. ΔY = Close(d) − Close(d−1), yüzde puanı × 100 = bp.
- Kör taşıma: MT5 US30 ve US2000'de aynı ayrım.

## Kovalar (K1 geceleri)
F+ : ΔY ≥ +5 bp (faiz korkusu) · F− : ΔY ≤ −5 bp (güvenliğe kaçış) · F0 : arası.

## Ölçüt (tek ayrım, iki yön de önceden tanımlı)
- D = ort(F−) − ort(F+). NDX'te ESKİ ve YENİ'de aynı işaret ∧ tüm dönem P(işaret) ≥ 0,95 ∧ US30 ve US2000'de de aynı işaret → **C+**
  (doz/kaçınma etiketi; tek başına kural değil).
- Aynı işaret ama P < 0,95 → C. Değilse X.
- Bilgi: F+ kovasının iki dönemde ayrı ayrı ortalaması ("faiz korkusunda alma" kaçınma kuralı mı?).
