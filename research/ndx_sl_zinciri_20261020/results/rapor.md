# 2026-10-19 NDX SL zinciri — karşı-olgu kuralları (ön-kayıt PROTOCOL.md)

İşlem: 321 bot NDX (DECIDER hariç), geçmiş 315, 10-19 6. Birim R; $ ikincil (lot 1→30 değişti).

| kural | geçmiş engel | geçmiş kurt.R | geçmiş kurt.$ | 10-19 engel | 10-19 kurt.R | 10-19 kurt.$ | geçmiş SL/TP engel | yarılar R | plasebo % | hüküm |
|---|---|---|---|---|---|---|---|---|---|---|
| K1 günlük fren (tüm magic, −3.000$) | 1 | -0.710 | -2367 | 3 | 1.270 | 4399 | 0/1 | -0.00/-0.71 | 54.000 | geçmedi |
| K2 aynı yönde üst üste binme yok | 28 | -7.660 | -13511 | 4 | 2.270 | 7699 | 8/19 | +0.55/-8.21 | 8.900 | geçmedi |
| K3 SL sonrası 60 dk soğuma | 107 | -14.440 | -5061 | 3 | 1.270 | 4399 | 39/67 | -4.44/-10.00 | 16.400 | geçmedi |
| K4 DAYCOMBO günde 1 | 21 | -8.450 | -12656 | 4 | 2.270 | 7699 | 4/17 | -0.00/-8.45 | 28.200 | geçmedi |
| K5a SQZ<1,00 engel (DAYCOMBO+REENTRY) | 25 | -6.090 | -10847 | 5 | 3.270 | 11029 | 7/18 | -0.00/-6.09 | 88.700 | geçmedi |
| K5b SQZ<1,00 engel (tüm bot aileleri) | 153 | 5.050 | -7844 | 5 | 3.270 | 11029 | 66/82 | +8.27/-3.22 | 97.500 | geçmedi |
| K6 REENTRY yalnız TP sonrası | 10 | -3.780 | -2096 | 2 | 0.270 | 1057 | 2/8 | -0.00/-3.78 | 61.300 | geçmedi |

## Geçmişte zincir/üst üste binme ne kadar sık ve sonucu?
- tüm bot NDX (DECIDER hariç): n=315 ortR +0.067 · SL %38
- DAYCOMBO+REENTRY: n=51 ortR +0.357 · SL %22
- aynı yönde açık pozisyon varken açılan: n=24 ortR +0.198 SL %33 · diğerleri ortR +0.056
- SL'den sonraki 60 dk içinde açılan: n=105 ortR +0.124 SL %37 · diğerleri ortR +0.038
- günün 2.+ DAYCOMBO'su: n=18 ortR +0.348 SL %22 · diğerleri ortR +0.050
- SL sonrası REENTRY: n=10 ortR +0.378 SL %20 · diğerleri ortR +0.057

## 10-19 işlemleri ve her kuralın hükmü
| pid | family | t0 | outcome | R | net | sqz | K1 | K2 | K3 | K4 | K5a | K5b | K6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 406111028 | DAYCOMBO | 2026-10-19 14:26:13+00:00 | TP | 0.727 | 2400.000 | 1.313 |  |  |  |  |  |  |  |
| 406146411 | REENTRY | 2026-10-19 15:30:10+00:00 | SL | -1.000 | -3330.000 | 0.677 |  |  |  |  | ENGEL | ENGEL |  |
| 406147613 | DAYCOMBO | 2026-10-19 15:31:28+00:00 | SL | -1.000 | -3300.000 | 0.726 |  | ENGEL |  | ENGEL | ENGEL | ENGEL |  |
| 406181680 | REENTRY | 2026-10-19 16:32:31+00:00 | SL | -1.000 | -3300.000 | 0.903 | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL |
| 406189588 | DAYCOMBO | 2026-10-19 16:51:33+00:00 | SL | -1.000 | -3342.000 | 0.938 | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL |  |
| 406245827 | REENTRY | 2026-10-19 20:02:38+00:00 | TP | 0.727 | 2243.090 | 1.475 | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL | ENGEL |