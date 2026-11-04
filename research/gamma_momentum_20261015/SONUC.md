# GM-01 — Gamma koşullu son yarım saat momentumu (NDX) — sonuç (2026-10-15)

Ön-kayıt: `PROTOCOL.md` (sonuçtan önce). Betik: `gm_test.py` (bir kez koşuldu). Ham: `results/sonuc.json`, `results/gunler_*.csv`.
Gamma: SqueezeMetrics `data/DIX.csv` (S&P 500 dealer GEX — NDX için **vekil**), d günü için d−1 değeri.

**Karar: GEÇMEDİ (sınıf C).** Yön teoriyle aynı ama anlamlı değil; doğrulama döneminde yalnız 9 negatif-gamma günü var (güçsüz).

| Set | GEX<0 gün | Ort. kazanç | Puan | İsabet | P (gün) | P (hafta blok) | Yarılar (bp) | GEX≥0 | H2 P |
|---|---|---|---|---|---|---|---|---|---|
| **30m geliştirme 2021-06→2025-11 (birincil)** | 146 | +3,3 bp | +4,7 | %51,4 | **0,80** | 0,82 | +2,9 / +3,8 | −0,6 bp (947) | **0,84** |
| 1h vekil 2016-05→2025-11 (ikincil) | 241 | +10,9 bp | +9,7 | %56,0 | 0,968 | 0,969 | +18,9 / +2,9 | +1,1 bp (2.108) | 0,945 |
| 30m doğrulama 2025-12→2026-10 | 9 | −5,7 bp | −12,7 | %55,6 | — | — | — | −0,2 bp (197) | 0,22 |
| 1h doğrulama | 9 | −18,0 bp | −44,4 | %44,4 | — | — | — | +0,8 bp (142) | 0,12 |

Okuma:
- Birincil ölçütler (P ≥ 0,975 ve H2 P ≥ 0,95) geçilmedi; işaret doğru, iki yarı pozitif, puan spread'in (1,5) üstünde.
- 1h vekilde etki daha belirgin ama ilk yarıda yoğun (2016–2020 +18,9 bp → sonrası +2,9 bp): yayın sonrası zayıflama
  (GHLZ 2018, Baltussen 2021) ile tutarlı.
- Negatif-gamma günlerinin 104'ü 2022'de; olay yılda ~30 ve tek rejime yığılı.
- Göreli gamma (kendi 1 yılının alt %20'si, ikincil) 30m'de etkisiz (−1,2 bp).
- 15m→30m uzatma hizalaması %100.

Yeniden açma şartı: yeni bağımsız veri — ileri gölge dönemde ≥ 30 negatif-GEX günü, ya da QQQ/NDX'e özgü gamma serisi.
