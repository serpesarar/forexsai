# FAZ 8 — DOĞRULAMA, KÖR TEST, KÖR TAŞIMA (Yön Lab, 2026-11-14)

Kod: `src/faz89.py`. Çıktı: `results/faz8_hucreler.csv`, `faz89_ozet.json`, kilit `results/FINAL_OPENED.json` (tek açılış).

## Hücre birliği (24 doğrulanmış hücreden herhangi biri aktif) — 15 dk yön FAZLASI (eşlenmiş tabana göre)
| Dönem | n | FAZLA | t |
|---|---|---|---|
| KEŞİF 2021-12 → 2024-06 | 21.104 | **−2,33 p** | −7,33 |
| DOĞRULAMA 2024-07 → 2025-12 | 11.789 | **−1,35 p** | −3,09 |
| **KÖR TEST 2026-01 → 11-04** | 6.905 | **−0,70 p** | −1,21 |
Etki her dönemde yarıya iniyor; KÖR'de işaret korunuyor ama anlamlı değil. "Dramatik kötüleşme" (işaret dönmesi) yok — kör veriyle
hiçbir ayar yapılmadı.

## KÖR TAŞIMA (Pepperstone M1, sıfır ayar, NDX KEŞİF eşikleri)
| Endeks | Dönem | n | FAZLA 15 dk | t | SHORT 15 dk EV (R) |
|---|---|---|---|---|---|
| US500 | 2026-09-04 → 11-13 | 1.673 | −1,62 p | −1,18 | −0,37 |
| US30 | 2026-09-04 → 11-13 | 1.687 | −0,47 p | −0,40 | −0,08 |
| US2000 | 2026-09-04 → 11-13 | 1.558 | −2,33 p | −1,78 | −0,64 |
| GER40 | 2026-08-20 → 11-13 | 1.760 | −1,30 p | −1,19 | −0,11 |
Yön işareti **4/4 endekste aynı** (mekanizma piyasalar arası taşınıyor), hiçbiri tek başına anlamlı değil (2,5 aylık M1).

## Model (dir_15m, ≤ 2025-12 ile eğitildi, 2026'da tek tahmin)
X = 0,08 (KEŞİF bloklarında seçildi): DOĞRULAMA yön isabeti %53,4 (n 1.625), KÖR %53,0 (n 100).
