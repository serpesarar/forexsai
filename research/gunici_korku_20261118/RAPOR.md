# Gün içi korku (zaman ekseni) + K1'in başka piyasalara taşınması (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/gk.py`.

## Sonuç

**1. Gün içi korku (10:30 / 12:00 / 14:00 kararı) — X.**
- 36 hücrelik ızgara şans düzeyinde: 3 aday, plasebo %95 = 12.
- Aynı gün kapanışta çıkan bütün hücreler zayıf.
- Dondurulan 3 adayın hiçbiri kör YENİ'de geçmedi:
  - 14:00 TWAP altı ≥ %1,0: YENİ +82,8 bp ama n 28, P %95,6.
  - 14:00 dibe yakın: +15,6.
  - 10:30 TWAP altı: −11,3.

**Ders:** kenar korkunun saatinde değil. "Kapanışa doğru korkulu günden **ertesi güne taşıma**"da. Sabah korkusu gün içinde
geri dönmüyor.

**2. K1 taşıması (§2.71 kuralı, değiştirilmeden, seçimsiz) — piyasalar arası çalışıyor.**

K1: 16:00'da fiyat günün ortalama fiyatının (09:30'dan beri TWAP) ≥ %0,5 altında ∧ 15:00 → 16:00 aşağı → 16:00 AL, ertesi gün
16:00 çık.

| piyasa (MT5 M30) | tetikli | taban | P | ESKİ / YENİ |
|---|---|---|---|---|
| NAS100 (§2.71) | +48,5 | +0,2 | — | — |
| **US30** 2018 → | **+31,4 bp** (n 160) | −1,4 | %97,7 | +45,4 / +19,6 |
| **US2000** 2018 → | **+31,4** (n 233) | −3,9 | %99,3 | +27,6 / +34,6 |
| **US500** 2021 → | **+22,9** (n 117) | +0,6 | %93,3 | +19,0 / +23,5 |
| XAUUSD | +6,1 (n 59) | +2,7 | %56 | −2,0 / +11,2 |

- K1 dört ABD hisse endeksinin dördünde, iki dönemde de artı. Fitilli KSG ise S&P 500'e taşınmamıştı.
- Altında yok. Mekanizma hisse piyasasının kapanış / gece yapısına özgü.

**Not:** ABD endeksleri birlikte hareket eder. Aynı gecede dört endekste birden açmak çeşitlendirme değil, büyük ölçüde aynı riskin
çoğaltılmasıdır. Taşıma kuralın genelliğini gösterir; portföy kazancı sınırlı.
