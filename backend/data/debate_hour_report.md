# Tartışma Saati — Tavan Analizi (2026-07-26)

**Soru:** ajan tartışması hangi saatte koşulursa en çok edge yakalayabilir?

**Skor = beceri:** koşullu kuralın test isabeti − en iyi SABİT yönün test
isabeti. Sabit yön zaten tutuyorsa tartışmaya gerek yok; tartışmanın
değeri sabit yönü geçtiği kadardır. Kural + sabit yön kronolojik train
(ilk %60) üzerinde seçilir, ikisi de test (son %40) üzerinde raporlanır.

**Plasebo:** 150 tur karıştırılmış ileri getiri, aynı seçim prosedürü. Gerçek zirve p95'i geçmezse saat seçimi gürültüdür.

## NDX.INDX — vekil NQ=F (NASDAQ 100 vadeli)
- Veri: 2024-03-03 → 2026-07-24 · 13675 adet 1h bar · train/test kesimi 2025-08-08
- **Zirve beceri +16.9pp · plasebo p95 +20.1pp → ❌ plaseboyu GEÇEMEDİ — saat seçimi gürültü**

| UTC | Etiket | 4h hareket (ATR) | 4h hareket % | P(yukarı) | sabit taban | koşullu kural | ufuk | n | koşullu WR | **beceri** |
|---|---|---|---|---|---|---|---|---|---|---|
| 21:00 | kapanış sonrası | 0.49 | 0.19 | 40% | always_short 48% | trend_ema | +2h | 65 | 64.6% | **+16.9pp** |
| 01:00 | Çin/HK açılış | 0.39 | 0.13 | 46% | always_long 47% | momentum_4h | +1h | 190 | 54.7% | **+7.9pp** |
| 19:00 | NY kapanışa | 0.54 | 0.18 | 44% | always_long 48% | reversal_4h | +2h | 206 | 55.3% | **+7.8pp** |
| 23:00 | Asya öncesi | 0.48 | 0.19 | 52% | always_short 44% | range_fade | +1h | 89 | 51.7% | **+7.5pp** |
| 17:00 | Londra kapanış | 0.81 | 0.26 | 47% | always_long 49% | follow_london | +1h | 235 | 54.9% | **+5.9pp** |
| 07:00 | Frankfurt ön | 0.68 | 0.18 | 53% | always_short 49% | range_fade | +1h | 104 | 53.8% | **+4.9pp** |
| 03:00 | Asya öğleden sonra | 0.45 | 0.16 | 57% | always_long 53% | momentum_4h | +2h | 229 | 57.6% | **+4.8pp** |
| 16:00 | NY öğleden sonra | 0.81 | 0.26 | 51% | always_long 52% | follow_london | +2h | 235 | 56.6% | **+4.3pp** |

**Hareket profili** — karar saatinden sonraki 4 saatte medyan mutlak hareket (ATR birimi). Yön öngörülemese bile bu betimsel: önünde yol olmayan saatte 4 saatlik yönlü karar vermenin anlamı yok.

| sıra | UTC | Etiket | 4h hareket (ATR) | 4h hareket % | mevcut koşu |
|---|---|---|---|---|---|
| 1 | 12:00 | NY ön-piyasa | 2.27 | 0.48 | ← ŞU AN BURADA |
| 2 | 11:00 | Londra öğle | 2.16 | 0.45 |  |
| 3 | 13:00 | NY açılış (13:30) | 1.86 | 0.47 | ← ŞU AN BURADA |
| 4 | 10:00 | Londra sabah | 1.84 | 0.39 |  |
| 5 | 14:00 | NY ilk saat | 1.33 | 0.35 |  |
| 6 | 09:00 | Londra sabah | 1.15 | 0.27 |  |

- Mevcut koşu saati: **12:00 UTC (hareket sırası 1/24), 13:00 UTC (hareket sırası 3/24)** · en hareketli saat: **12:00 UTC (2.27 ATR)**

## GDAXI.INDX — vekil ^GDAXI (DAX nakit (yalnız 07-16 UTC seansı))
- Veri: 2023-09-07 → 2026-07-24 · 6552 adet 1h bar · train/test kesimi 2025-05-30
- **Zirve beceri +9.4pp · plasebo p95 +25.5pp → ❌ plaseboyu GEÇEMEDİ — saat seçimi gürültü**

| UTC | Etiket | 4h hareket (ATR) | 4h hareket % | P(yukarı) | sabit taban | koşullu kural | ufuk | n | koşullu WR | **beceri** |
|---|---|---|---|---|---|---|---|---|---|---|
| 07:00 | Frankfurt ön | 0.66 | 0.26 | 48% | always_long 47% | momentum_4h | +2h | 149 | 56.4% | **+9.4pp** |
| 09:00 | Londra sabah | 0.76 | 0.30 | 47% | always_long 48% | range_fade | +4h | 122 | 56.6% | **+9.0pp** |
| 11:00 | Londra öğle | 0.72 | 0.28 | 52% | always_long 48% | range_fade | +2h | 119 | 55.5% | **+7.7pp** |
| 15:00 | NY öğle | nan | nan | 0% | always_long 48% | trend_ema | +1h | 104 | 50.0% | **+1.9pp** |
| 10:00 | Londra sabah | 0.75 | 0.26 | 53% | always_long 50% | range_fade | +2h | 117 | 52.1% | **+1.7pp** |
| 12:00 | NY ön-piyasa | 0.67 | 0.25 | 18% | always_long 50% | trend_ema | +4h | 104 | 51.0% | **+1.0pp** |
| 14:00 | NY ilk saat | nan | nan | 0% | always_long 53% | trend_ema | +2h | 104 | 51.9% | **-1.0pp** |
| 08:00 | Londra/DAX açılış | 0.64 | 0.24 | 50% | always_long 55% | momentum_4h | +2h | 230 | 50.9% | **-3.9pp** |

**Hareket profili** — karar saatinden sonraki 4 saatte medyan mutlak hareket (ATR birimi). Yön öngörülemese bile bu betimsel: önünde yol olmayan saatte 4 saatlik yönlü karar vermenin anlamı yok.

| sıra | UTC | Etiket | 4h hareket (ATR) | 4h hareket % | mevcut koşu |
|---|---|---|---|---|---|
| 1 | 11:00 | Londra öğle | 0.80 | 0.27 |  |
| 2 | 10:00 | Londra sabah | 0.75 | 0.25 |  |
| 3 | 12:00 | NY ön-piyasa | 0.73 | 0.24 |  |
| 4 | 09:00 | Londra sabah | 0.71 | 0.24 |  |
| 5 | 08:00 | Londra/DAX açılış | 0.67 | 0.23 | ← ŞU AN BURADA |
| 6 | 07:00 | Frankfurt ön | 0.65 | 0.25 |  |

- Mevcut koşu saati: **08:00 UTC (hareket sırası 5/6)** · en hareketli saat: **11:00 UTC (0.80 ATR)**

## XAUUSD — vekil GC=F (Altın vadeli)
- Veri: 2024-03-03 → 2026-07-24 · 13718 adet 1h bar · train/test kesimi 2025-08-06
- **Zirve beceri +12.8pp · plasebo p95 +19.9pp → ❌ plaseboyu GEÇEMEDİ — saat seçimi gürültü**

| UTC | Etiket | 4h hareket (ATR) | 4h hareket % | P(yukarı) | sabit taban | koşullu kural | ufuk | n | koşullu WR | **beceri** |
|---|---|---|---|---|---|---|---|---|---|---|
| 16:00 | NY öğleden sonra | 0.49 | 0.23 | 50% | always_long 44% | reversal_4h | +2h | 237 | 57.0% | **+12.8pp** |
| 08:00 | Londra/DAX açılış | 0.62 | 0.24 | 50% | always_long 50% | range_fade | +4h | 92 | 62.0% | **+12.2pp** |
| 22:00 | Asya öncesi | 0.71 | 0.30 | 48% | always_short 40% | range_fade | +2h | 54 | 50.0% | **+10.3pp** |
| 21:00 | kapanış sonrası | 0.86 | 0.45 | 39% | always_short 45% | reversal_4h | +6h | 64 | 53.1% | **+8.5pp** |
| 01:00 | Çin/HK açılış | 0.60 | 0.29 | 46% | always_long 44% | momentum_4h | +1h | 191 | 50.3% | **+6.3pp** |
| 13:00 | NY açılış (13:30) | 0.93 | 0.41 | 49% | always_long 50% | trend_ema | +2h | 239 | 56.5% | **+6.3pp** |
| 23:00 | Asya öncesi | 0.82 | 0.37 | 49% | always_long 53% | reversal_4h | +1h | 190 | 57.9% | **+5.3pp** |
| 03:00 | Asya öğleden sonra | 0.58 | 0.26 | 52% | always_short 52% | momentum_4h | +1h | 233 | 56.7% | **+4.9pp** |

**Hareket profili** — karar saatinden sonraki 4 saatte medyan mutlak hareket (ATR birimi). Yön öngörülemese bile bu betimsel: önünde yol olmayan saatte 4 saatlik yönlü karar vermenin anlamı yok.

| sıra | UTC | Etiket | 4h hareket (ATR) | 4h hareket % | mevcut koşu |
|---|---|---|---|---|---|
| 1 | 10:00 | Londra sabah | 1.28 | 0.39 |  |
| 2 | 11:00 | Londra öğle | 1.24 | 0.41 |  |
| 3 | 12:00 | NY ön-piyasa | 1.21 | 0.41 |  |
| 4 | 09:00 | Londra sabah | 1.02 | 0.32 |  |
| 5 | 13:00 | NY açılış (13:30) | 0.99 | 0.35 |  |
| 6 | 05:00 | Tokyo kapanışa | 0.82 | 0.27 |  |
| 8 | 08:00 | Londra/DAX açılış | 0.76 | 0.23 | ← ŞU AN BURADA |

- Mevcut koşu saati: **08:00 UTC (hareket sırası 8/24)** · en hareketli saat: **10:00 UTC (1.28 ATR)**

## USOIL.FOREX — vekil CL=F (WTI vadeli)
- Veri: 2024-03-03 → 2026-07-24 · 13510 adet 1h bar · train/test kesimi 2025-08-13
- **Zirve beceri +19.3pp · plasebo p95 +19.0pp → ✅ plaseboyu GEÇTİ**

| UTC | Etiket | 4h hareket (ATR) | 4h hareket % | P(yukarı) | sabit taban | koşullu kural | ufuk | n | koşullu WR | **beceri** |
|---|---|---|---|---|---|---|---|---|---|---|
| 22:00 | Asya öncesi | 0.38 | 0.40 | 40% | always_long 36% | follow_london | +6h | 118 | 55.1% | **+19.3pp** |
| 05:00 | Tokyo kapanışa | 0.99 | 0.63 | 49% | always_long 40% | range_fade | +2h | 92 | 55.4% | **+15.2pp** |
| 01:00 | Çin/HK açılış | 0.42 | 0.33 | 48% | always_long 45% | momentum_4h | +6h | 181 | 57.5% | **+12.6pp** |
| 00:00 | Asya erken | 0.46 | 0.32 | 44% | always_long 44% | momentum_4h | +4h | 184 | 55.4% | **+11.1pp** |
| 07:00 | Frankfurt ön | 1.25 | 0.74 | 53% | always_short 48% | follow_asia | +1h | 222 | 58.1% | **+9.7pp** |
| 04:00 | Asya geç | 0.76 | 0.51 | 45% | always_long 46% | momentum_4h | +4h | 222 | 54.5% | **+8.9pp** |
| 03:00 | Asya öğleden sonra | 0.57 | 0.38 | 42% | always_long 43% | momentum_4h | +4h | 222 | 51.8% | **+8.4pp** |
| 06:00 | Tokyo kapanış | 1.26 | 0.70 | 47% | always_long 42% | range_fade | +2h | 81 | 48.1% | **+6.6pp** |

**Hareket profili** — karar saatinden sonraki 4 saatte medyan mutlak hareket (ATR birimi). Yön öngörülemese bile bu betimsel: önünde yol olmayan saatte 4 saatlik yönlü karar vermenin anlamı yok.

| sıra | UTC | Etiket | 4h hareket (ATR) | 4h hareket % | mevcut koşu |
|---|---|---|---|---|---|
| 1 | 11:00 | Londra öğle | 1.65 | 0.80 |  |
| 2 | 12:00 | NY ön-piyasa | 1.63 | 0.79 |  |
| 3 | 10:00 | Londra sabah | 1.62 | 0.72 |  |
| 4 | 13:00 | NY açılış (13:30) | 1.49 | 0.77 | ← ŞU AN BURADA |
| 5 | 06:00 | Tokyo kapanış | 1.30 | 0.56 |  |
| 6 | 09:00 | Londra sabah | 1.29 | 0.61 |  |

- Mevcut koşu saati: **13:00 UTC (hareket sırası 4/24)** · en hareketli saat: **11:00 UTC (1.65 ATR)**
