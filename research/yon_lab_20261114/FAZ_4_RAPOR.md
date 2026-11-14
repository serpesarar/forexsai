# FAZ 4 — Şans haritası (Yön Lab, 2026-11-14)

Kod: `src/atlas.py`. Tablolar: `results/referans_atlasi_aile.csv`, `referans_atlasi_uye.csv`, `referans_atlasi_ret_kirilim.csv`,
`durum_atlasi_tekli.csv`, `atlas_real/calib_curve.csv`; grafik `results/referans_atlasi_kalibrasyon.svg`.
Eşikler (martingal piyasa, 10 tekrarın en büyük |t|'si, KEŞİF): aile yarışı **2,23** · üye mıknatıs/duvar **3,38** ·
ret/kırılım **4,13** · tekli durum (bağımsız n ≥ 100) **6,42**.

## 1. Kalibrasyon: U/(U+D) kovalarına göre gözlenen vs analitik vs hayalet
Pivot (PIV) ailesi, KEŞİF (52.582 çözülmüş yarış): 0,3–0,4 kovası gözlenen 0,377 / analitik 0,371 / hayalet 0,379;
0,4–0,5: 0,494 / 0,488 / 0,494; 0,6–0,7: 0,670 / 0,659 / 0,665; 0,8–0,9: 0,862 / 0,844 / 0,844. EMA, CAL, TWAP, RND, ICHI eğrileri
aynı (grafik). **Kumarbazın iflası formülü D/(U+D) yarışın neredeyse tamamını açıklıyor**; gözlenen ile analitik arasındaki
+0,5…+1,5 puanlık sistematik fark yukarı sürüklenmedir ve hayalette de vardır.

## 2. Referans aileleri — gerçek vs hayalet (aile içi en yakın üst/alt yarışı)
| Aile | n (KEŞİF) | P gözlenen | P hayalet | P analitik | FAZLA (hayalet) | t | DOĞRULAMA t | KÖR t |
|---|---|---|---|---|---|---|---|---|
| EMA | 35.522 | 0,504 | 0,508 | 0,504 | −0,48 p | −1,48 | 0,37 | −0,93 |
| SMA | 26.301 | 0,504 | 0,501 | 0,497 | +0,27 | 0,42 | −0,37 | 0,27 |
| BB | 44.150 | 0,521 | 0,521 | 0,515 | −0,07 | −0,12 | −0,80 | 0,73 |
| KC | 41.042 | 0,527 | 0,524 | 0,517 | +0,28 | 0,40 | −0,36 | 0,74 |
| DON | 41.111 | 0,533 | 0,530 | 0,525 | +0,28 | 0,45 | 0,01 | 0,87 |
| TWAP | 48.168 | 0,507 | 0,506 | 0,500 | +0,10 | 0,29 | 0,02 | −0,38 |
| PIV | 50.919 | 0,507 | 0,507 | 0,502 | −0,00 | −0,01 | 0,06 | −0,04 |
| CAL | 47.874 | 0,518 | 0,517 | 0,511 | +0,16 | 0,31 | −0,77 | 0,00 |
| RND | 49.854 | 0,513 | 0,509 | 0,502 | +0,37 | 0,64 | −0,80 | −0,35 |
| FIB | 17.453 | 0,505 | 0,501 | 0,499 | +0,39 | 0,39 | −0,51 | −0,85 |
| ICHI | 25.675 | 0,525 | 0,513 | 0,510 | +1,20 | **1,58** | 0,94 | 0,12 |
| TRD | 17.181 | 0,510 | 0,519 | 0,518 | −0,93 | −0,73 | 0,68 | 0,66 |
| CLU | 51.364 | 0,503 | 0,504 | 0,498 | −0,08 | −0,35 | −0,71 | −0,36 |
**Hiçbir aile hayaletten ayrılmıyor** (en büyük |t| 1,58 < 2,23); üç dönemin hiçbirinde |t| > 1,6.

## 3. Üye düzeyi "mıknatıs / duvar" (229 üye × üst/alt × 3 dönem)
Seviye p'nin d ∈ [0,05; 1,5] ATR üstünde/altında iken, aynı uzaklıktaki karşı (sahte) seviyeden önce ona değme oranı − hayalet.
KEŞİF: ağırlıklı ortalama FAZLA **−0,22 puan**, medyan |t| 0,76, |t| > 2 olan 6/229 (şansla beklenen ≈ 10). En uç: EMA200-D1 üstte
−15,6 p ama yalnız 55 bağımsız olay (t −2,90 < 3,38). EMA200, VWAP/TWAP, önceki gün dibi, kanal kenarı (BB/KC/DON) — **hiçbiri
mıknatıs ya da duvar değil.**

## 4. Değdikten sonra ret / kırılım (215 üye × taraf, KEŞİF)
Gerçek kırılım oranı ortalama **%50,5**, hayalet **%50,8** (fark −0,28 p); |t| > 2: 10/215 (şans ≈ 10); en büyük |t| 2,64 < 4,13.
Aile ortalamaları: EMA %49,9 vs hayalet %50,8 · PIV %50,6 vs %50,8 · DON %52,7 vs %51,4 · TWAP %50,4 vs %50,6 · RND %50,9 vs %50,9.
Defterin TK/TL/KC bulgusu (kenar/çizgi = hayalet) **tüm seviye ailelerine genellendi**.

## 5. Tekli durumlar — eşlenmiş tabana göre fark (3.642 hücre × etiket, KEŞİF)
- Gerçek veride |t| > 4 olan hücre **31**, martingal piyasalarda ortalama **1,6** (Poisson p ≈ 1e-29) → **durumlarda gerçek bilgi var**.
- 31'in 30'u `dir_15m`: hepsi aynı mekanizma — **yukarı aşırı uzama sonraki 15 dakikada bir miktar geri veriyor** (ve aşağı aşırı uzama
  tersine): TWAP z en üst %20 → −3,3 p (t −7,49, tek eşik-üstü hücre), Williams %R tepe −2,3 p, 3 beyaz asker −3,1 p, M5 ROC12 alt
  %20 +2,8 p, BB %B tepe −2,6 p, M5 RSI14 tepe −2,5 p. 1 saatte yalnız 1 hücre |t|>4; 4 saat ve seans sonunda yok.
- Zorunlu akış bayrakları (ay sonu/başı, vade haftası, çeyrek sonu, tatil öncesi), GEX/DIX, VIX rejimi gün-içi yön etiketlerinde eşik
  altında.

## Faz 5'e girdi
Hayaletten ayrılan referans ailesi: **yok** (ölü listesine). Tabandan ayrılan durumlar: 15 dakikalık aşırı-uzama dönüş ailesi.
DUR koşulu oluşmadı (durumlar tabandan ayrıldı + Faz 6 katmanlarına erişildi).
