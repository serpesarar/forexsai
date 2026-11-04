# Aile: türev konumlanma sinyalleri (OI, funding, baz/premium, L/S oranları, tasfiye vekilleri) → BTC scalp

Kapsam: 2026-10-22, sızıntısız geri-test. Yalnız mevcut veri (`research/btc_scalp_20261021/data/btc_scalp_1m.parquet` +
`metrics_5m_effective.parquet`), yeni indirme yok, kutuya/Supabase'e dokunulmadı, commit yok. Tüm kod, ön kayıt ve çıktılar
[fam_turev/](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/) altında:
[prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/prereg.md) (sonuçtan önce yazıldı; EK-1 sayım
düzeltmesi sonuçtan önce, EK-2 sonradan açıklama), `scripts/01_prep.py` → `02_outcomes.py` (ilk-dokunuş motoru, kaba döngüyle 0/8.000 uyuşmazlık) →
`03_events.py` → `04_eval.py` (468 hücre, seçim, max-z, plasebo, kart) → `05_diag.py` / `06_posthoc.py` (yalnız bilgi). Çıktılar `out/`:
`cells.csv` (468 hücrenin hepsi, DISC/OOS/BLIND), `selected.json` + `summary.csv` (ID başına), `event_counts.csv`, `gross_edge_cells.csv`,
`dv02_asymmetry.csv`, `posthoc.csv`, `maxz_null.npy`; günlükler `logs/`. Python `.venv` (numpy 2.4.6), `-I`.
Ondalık ayırıcı tablolarda virgül.

## 1. Türev konumlanma sinyalleri, gerçekçi maliyet sonrası kârlı bir BTC scalp stratejisi veriyor mu?

### Takeaway
**Hayır.** 5 alt aile, 40 ön-kayıtlı hipotez, 468 hücre: DISC'te seçilen hücrelerin **hiçbiri** canlıya alma kartını geçmedi; LIVE-aday 0,
GÖLGE-aday 0, 40/40 RED. Ailenin en iyi seçilebilir DISC hücresi z = 1,63 (max-z p_sel 0,25; boş dağılımın %95'i 2,47) — seçim bile
tesadüften ayırt edilemiyor. Seçilebilir 370 hücreden **hiçbiri** DISC, OOS ve BLIND'ın üçünde birden net pozitif değil; POST'ta net
pozitif olan hücre payı %6,8 (25/370). Tasfiye vekiline OI teyidi eklemek (S05/S06'nın "yeni tanımı") fade'i **kurtarmıyor**, tersine
OI-teyitli long tasfiyesinden sonra düşüş sürüyor (DV02-P1oL-F POST −0,199R, P(EV>0) %0,2).

### Cited Findings
- Protokol: DISC 2021-06-01→2023-12-31 / OOS 2024-01-11→2025-06-30 / BLIND 2025-07-01→2026-10-20; karar barı t kapanışı → giriş t+1 açılışı;
  SL = max(19 bp, 1,1×ATR14(5m)), TP = r×SL (r 1/1,5/2), zaman stopu 15/60 dk (DV03c 35 dk), aynı bar → SL, SL kayması 1 bp (DISC p99
  |1m getiri| = 29,3 bp üstündeki dakikada 5 bp), rollover (NY 17:00 − 2 dk) öncesi zorla kapanış; maliyet PEP 1,85 bp birincil —
  [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/prereg.md)
- İşlem yolu Binance **spot** 1m (Pepperstone CFD spot endeksini izler; fizibilite motoruyla aynı). SL medyanı 2021 29,7 bp, 2022 23,3 bp,
  2023–26 19,0 bp (19 bp tabanı işlemlerin %54–71'inde bağlayıcı) — [logs/01_prep.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/logs/01_prep.log)
- Rastgele giriş (aynı geometri) net PEP ≈ −0,085…−0,110R; brüt long −0,008R / short +0,007R (H60, r1) — yani taban sıfır değil, maliyet/R ≈ 0,09R —
  [logs/02_outcomes.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/logs/02_outcomes.log)
- Max-z boş dağılımı (500 kopya, tüm ailenin olay zamanları DISC içinde ortak tam-gün dairesel kaydırma): medyan 1,26, %90 2,03, %95 2,47,
  %99 2,84; gözlenen en iyi seçilebilir hücre DV03c-S th−1 r1,5 H35 z = 1,63 → p_sel 0,25 — [out/maxz_null.npy](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/maxz_null.npy), [out/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/cells.csv)
- Verdikt dağılımı: RED 34, RED (değerlendirilemez: seçilebilir hücre yok) 3, RED (kendi aynı-bar oranı ≥ %0,5 → prereg §3 geçersiz) 3.
  Kart dağılımı: 0/6 → 7 ID, 1/6 → 29, 2/6 → 3, 5/6 → 1 (DV04c-U; aynı-bar ile geçersiz). POST Holm p'lerinin hepsi 1,00 —
  [out/selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/selected.json)
- Taban-üstü **brüt** kenar (aynı yıl × UTC saati × bölme rastgele girişinin brüt R'sine göre) üç bölmede de pozitif olan hücre 61/456 = %13,4;
  bağımsız işaretlerde beklenen 1/8 = %12,5 → tesadüf düzeyi. Üç bölmede de ≥ +0,05R brüt kenar: 7 hücre (hepsi aşağıda ele alınan iki
  küçük-n kümeden) — [out/gross_edge_cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/gross_edge_cells.csv)

### Inferences
- Bu aile 1m karar / 15–60 dk ufukta, 19 bp+ stoplu CFD scalp'i için **bilgi taşımıyor**: ne net ne de (tesadüf düzeyinin üstünde) brüt.
  Literatür notundaki (01) "funding/OI/liq kısa ufukta kanıt yok" boşluğu burada olumsuz yönde kapanıyor (bu veri, bu tanımlar ve bu geometri için).
- Kart ölçüt 5 (icra farkı) burada fiilen "net ort R ≥ ~2 × maliyet/R ≈ 0,18R" demek (iyimser senaryo maliyetsiz; E44 ile aynı) —
  40 ID'nin hiçbiri bu çıtaya yaklaşmıyor (DV04c-U hariç; o da geçersiz, aşağıda).
- Tek-pozisyon zinciri (kart 6) bu ailede olay setiyle **aynı**: olaylar ≥60 dk epizodlu ve H ≤ 60 olduğundan çakışma yok; ölçüt 6 burada ölçüt 2'nin kopyası.

### Gaps
- Gerçek USDT-M tasfiye akışı yok (vekil kesin ama seyrek, en büyük tasfiyelerin %82–87'sini kaçırıyor — veri notu 02); gerçek tasfiye ısı haritasıyla
  sonuç değişebilir, bu veriyle sınanamaz.
- 1m vekil olaylarında aynı-bar oranı %0,6–3,1 → ön kayıt gereği geçersiz; bu (en "scalp" benzeri) bölge yalnız 1 s veriyle sınanabilir
  (aggTrades yalnız 2026-04-20 sonrası işlenmiş).
- Broker (Pepperstone) M1 ile teyit yapılmadı (E47): sonuçlar zaten negatif olduğu için verdikt değişmez; pozitif bir aday olsaydı zorunlu olurdu.

## 2. Hipotez başına sonuç tablosu (POST = OOS ∪ BLIND, seçilen DISC hücresi, net PEP 1,85 bp)

### Takeaway
Değerlendirilebilen 37 ID'nin 35'i POST'ta net negatif, 1'i ≈0 (DV02-P1oL-W +0,000), yalnız DV04c-U pozitif (3 ID'de seçilebilir hücre yok) (+0,243R, n 117) ve o da hem DISC'te negatif hem
kendi aynı-bar oranıyla (%0,85) geçersiz. P(EV>0) ≥ %90 olan tek ID DV04c-U.

### Cited Findings
Sütunlar: DISC seçimi (n / ort R / gün-kümeli z), p_sel (max-z), POST n, WR (net R > 0 payı, %), ort R, ort net bp, gün-blok bootstrap %95 GA,
P(EV>0) %, kronolojik yarılar, stres (2,78 bp), icra farkı (iyimser − gerçekçi R), tek-pozisyon R (n), plasebo yüzdeliği (aynı yıl×saat×yön
rastgele giriş / koşul serisinin dairesel kaydırması; kalıcı rejim ID'lerinde (DV03a, DV05) birincil dairesel), OOS R, BLIND n / R, yıl işaretleri
(2021→2026, tüm dönem), POST işlem/gün, kart, POST Holm, verdikt — [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv), [out/selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/selected.json)

| ID | Seçilen hücre (DISC) | DISC n / R / z | p_sel | POST n | WR | ort R | bp | %95 GA | P(EV>0) | yarılar | stres | icra farkı | tek-poz | plasebo % (saat / dairesel) | OOS R | BLIND n / R | yıllık işaret 21…26 | işlem/gün | kart | Holm | verdikt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DV01a-C | W60_k2.5 BUY r1,0 H15 | 85 / +0,096 / +1,12 | 0,63 | 170 | 48,8 | -0,056 | -0,9 | [-0,185; +0,075] | 21,0 | -0,109 / -0,003 | -0,083 | +0,066 | -0,056 (n 170) | 71,0 / 74,5 | -0,114 | 78 / +0,012 | + + + − − + | 0,17 | 1/6 | 1,00 | RED |
| DV01a-R | W60_k2.5 SELL r2,0 H15 | 85 / -0,177 / -1,68 | 1,00 | 170 | 47,1 | -0,053 | -3,3 | [-0,197; +0,091] | 22,8 | -0,040 / -0,067 | -0,080 | +0,071 | -0,053 (n 170) | 65,0 / 68,5 | -0,026 | 78 / -0,085 | − − − − + − | 0,17 | 1/6 | 1,00 | RED |
| DV01b-R | W60_k2.5 SELL r1,0 H15 | 179 / -0,022 / -0,34 | 1,00 | 121 | 46,3 | -0,100 | -4,6 | [-0,242; +0,045] | 9,0 | -0,067 / -0,132 | -0,122 | +0,059 | -0,100 (n 121) | 45,2 / 42,0 | -0,079 | 41 / -0,140 | − + − − − − | 0,12 | 0/6 | 1,00 | RED |
| DV01b-C | W60_k1.5 BUY r2,0 H60 | 516 / +0,036 / +0,59 | 0,96 | 488 | 36,9 | -0,107 | -2,3 | [-0,221; +0,002] | 2,6 | -0,203 / -0,010 | -0,135 | +0,079 | -0,107 (n 488) | 41,0 / 45,5 | -0,169 | 202 / -0,018 | + + + − − + | 0,48 | 1/6 | 1,00 | RED |
| DV01c-C | W60_k1.5 SELL r1,0 H15 | 311 / +0,007 / +0,15 | 1,00 | 370 | 48,9 | -0,057 | -1,8 | [-0,142; +0,028] | 9,7 | -0,031 / -0,083 | -0,087 | +0,074 | -0,057 (n 370) | 79,8 / 73,5 | -0,029 | 205 / -0,079 | − + + − − − | 0,36 | 1/6 | 1,00 | RED |
| DV01c-R | W15_k2.5 BUY r1,5 H60 | 96 / +0,028 / +0,25 | 1,00 | 182 | 44,0 | -0,017 | +0,3 | [-0,193; +0,157] | 41,9 | -0,065 / +0,031 | -0,045 | +0,085 | -0,017 (n 182) | 83,8 / 82,5 | -0,017 | 97 / -0,017 | − + − + − − | 0,18 | 1/6 | 1,00 | RED |
| DV01d-R | W60_k2.5 BUY r2,0 H60 | 217 / -0,084 / -1,04 | 1,00 | 198 | 36,4 | -0,162 | -5,1 | [-0,329; +0,006] | 2,6 | -0,042 / -0,281 | -0,184 | +0,067 | -0,162 (n 198) | 22,2 / 22,5 | -0,064 | 83 / -0,297 | + − − − − − | 0,20 | 2/6 | 1,00 | RED |
| DV01d-C | W15_k2.5 SELL r2,0 H15 | 542 / +0,039 / +0,84 | 0,88 | 458 | 35,6 | -0,135 | -4,5 | [-0,231; -0,028] | 0,3 | -0,208 / -0,061 | -0,162 | +0,074 | -0,135 (n 458) | 6,8 / 12,5 | -0,186 | 178 / -0,054 | + + − − − − | 0,45 | 1/6 | 1,00 | RED |
| DV02-P5L-F | P5 BUY r1,0 H60 | 699 / -0,161 / -4,17 | 1,00 | 521 | 50,5 | -0,076 | -1,8 | [-0,166; +0,016] | 5,0 | -0,021 / -0,131 | -0,105 | +0,086 | -0,076 (n 521) | 80,6 / 78,5 | -0,005 | 227 / -0,168 | − − − − − − | 0,51 | 1/6 | 1,00 | RED |
| DV02-P5L-W | P5 SELL r2,0 H15 | 699 / +0,030 / +0,70 | 0,94 | 521 | 37,8 | -0,124 | -3,0 | [-0,222; -0,021] | 0,6 | -0,139 / -0,109 | -0,153 | +0,079 | -0,124 (n 521) | 12,6 / 12,0 | -0,169 | 227 / -0,066 | + + − − − − | 0,51 | 1/6 | 1,00 | RED |
| DV02-P1L-F | seçilebilir hücre yok (aynı-bar ≥ %0,5 veya n_DISC<50) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | RED (değerlendirilemez) |
| DV02-P1L-W | P1 SELL r2,0 H60 | 681 / -0,022 / -0,41 | 1,00 | 548 | 33,9 | -0,118 | -2,2 | [-0,236; +0,005] | 2,9 | -0,070 / -0,166 | -0,152 | +0,104 | -0,118 (n 548) | 22,8 / 29,5 | -0,071 | 268 / -0,167 | − + − − − − | 0,54 | 1/6 | 1,00 | RED |
| DV02-P1oL-F | P1oi BUY r2,0 H60 | 485 / -0,141 / -2,50 | 1,00 | 347 | 33,1 | -0,199 | -6,3 | [-0,339; -0,063] | 0,2 | -0,123 / -0,276 | -0,229 | +0,094 | -0,199 (n 347) | 8,2 / 9,5 | -0,133 | 153 / -0,284 | − − − − − − | 0,34 | 2/6 | 1,00 | RED |
| DV02-P1oL-W | P1oi SELL r1,5 H15 | 485 / +0,004 / +0,09 | 1,00 | 347 | 43,8 | +0,000 | -0,2 | [-0,134; +0,130] | 50,5 | -0,026 / +0,026 | -0,030 | +0,079 | +0,000 (n 347) | 97,6 / 98,0 | -0,040 | 153 / +0,052 | + + − − − + | 0,34 | 2/6 | 1,00 | RED |
| DV02-P5S-F | P5 SELL r1,0 H15 | 609 / -0,081 / -2,32 | 1,00 | 400 | 50,2 | -0,026 | +0,0 | [-0,115; +0,062] | 27,9 | +0,011 / -0,064 | -0,057 | +0,089 | -0,026 (n 400) | 95,2 / 96,5 | -0,003 | 187 / -0,053 | − − − + − − | 0,39 | 1/6 | 1,00 | RED (aynı-bar ≥ %0,5 → hücre geçersiz, prereg §3) |
| DV02-P5S-W | P5 BUY r2,0 H60 | 609 / -0,039 / -0,73 | 1,00 | 400 | 39,5 | -0,041 | -0,4 | [-0,178; +0,088] | 25,4 | -0,050 / -0,032 | -0,071 | +0,088 | -0,041 (n 400) | 84,8 / 89,0 | -0,035 | 187 / -0,048 | + − − − − − | 0,39 | 1/6 | 1,00 | RED |
| DV02-P1S-F | seçilebilir hücre yok (aynı-bar ≥ %0,5 veya n_DISC<50) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | RED (değerlendirilemez) |
| DV02-P1S-W | seçilebilir hücre yok (aynı-bar ≥ %0,5 veya n_DISC<50) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | RED (değerlendirilemez) |
| DV02-P1oS-F | P1oi SELL r1,0 H60 | 443 / -0,112 / -2,39 | 1,00 | 243 | 50,2 | -0,082 | -1,9 | [-0,219; +0,044] | 9,3 | -0,041 / -0,124 | -0,115 | +0,112 | -0,082 (n 243) | 59,4 / 63,5 | -0,052 | 130 / -0,108 | − − − − − − | 0,24 | 1/6 | 1,00 | RED (aynı-bar ≥ %0,5 → hücre geçersiz, prereg §3) |
| DV02-P1oS-W | P1oi BUY r2,0 H15 | 443 / -0,011 / -0,21 | 1,00 | 243 | 42,8 | -0,080 | -2,5 | [-0,217; +0,066] | 13,8 | +0,008 / -0,166 | -0,113 | +0,088 | -0,080 (n 243) | 62,8 / 56,0 | +0,031 | 130 / -0,176 | + − + + − − | 0,24 | 1/6 | 1,00 | RED |
| DV03a-L | th3.0 SELL r2,0 H60 | 686 / +0,054 / +1,22 | 0,53 | 524 | 38,7 | -0,046 | -1,5 | [-0,147; +0,067] | 21,6 | -0,091 / -0,001 | -0,082 | +0,096 | -0,046 (n 524) | 83,6 / 96,0 | -0,046 | 0 / — | + − − | 0,52 | 1/6 | 1,00 | RED |
| DV03a-S | th-1.0 BUY r1,5 H60 | 732 / +0,037 / +0,74 | 0,93 | 225 | 40,0 | -0,135 | -2,6 | [-0,323; +0,040] | 6,9 | +0,052 / -0,320 | -0,172 | +0,098 | -0,135 (n 225) | 36,2 / 38,0 | +0,008 | 142 / -0,219 | + − + − + − | 0,22 | 1/6 | 1,00 | RED |
| DV03b-L | th1.5 SELL r1,5 H60 | 623 / +0,034 / +0,83 | 0,88 | 704 | 41,2 | -0,100 | -1,8 | [-0,186; -0,011] | 1,4 | -0,178 / -0,021 | -0,141 | +0,106 | -0,100 (n 704) | 46,2 / 44,5 | -0,100 | 0 / — | + + − | 0,69 | 1/6 | 1,00 | RED |
| DV03b-S | th0 BUY r2,0 H60 | 1814 / -0,045 / -1,58 | 1,00 | 2597 | 38,7 | -0,117 | -2,6 | [-0,163; -0,073] | 0,0 | -0,100 / -0,134 | -0,162 | +0,114 | -0,117 (n 2597) | 35,0 / 39,5 | -0,081 | 1524 / -0,143 | − − − − − − | 2,56 | 1/6 | 1,00 | RED |
| DV03c-L | th3.0 SELL r2,0 H35 | 92 / -0,013 / -0,09 | 1,00 | 71 | 47,9 | -0,051 | -0,4 | [-0,311; +0,208] | 33,5 | -0,086 / -0,017 | -0,085 | +0,083 | -0,051 (n 71) | 57,4 / 57,0 | -0,051 | 0 / — | − + − | 0,07 | 0/6 | 1,00 | RED |
| DV03c-S | th-1.0 BUY r1,5 H35 | 80 / +0,177 / +1,63 | 0,25 | 9 | 22,2 | -0,470 | -9,2 | [-1,043; +0,094] | 5,5 | -0,458 / -0,478 | -0,503 | +0,090 | -0,470 (n 9) | 10,0 / 7,5 | -1,131 | 7 / -0,280 | + + + − − − | 0,01 | 1/6 | 1,00 | RED |
| DV03d-L | th3.0 BUY r1,5 H15 | 88 / -0,187 / -1,78 | 1,00 | 68 | 50,0 | -0,050 | -5,1 | [-0,288; +0,168] | 31,1 | +0,006 / -0,107 | -0,085 | +0,080 | -0,050 (n 68) | 65,6 / 80,5 | -0,050 | 0 / — | − − − | 0,07 | 0/6 | 1,00 | RED |
| DV03d-S | th-1.0 SELL r1,0 H60 | 75 / -0,098 / -0,90 | 1,00 | 10 | 30,0 | -0,490 | -21,4 | [-1,085; +0,237] | 8,8 | -0,700 / -0,280 | -0,524 | +0,090 | -0,490 (n 10) | 10,6 / 7,5 | -0,466 | 7 / -0,501 | + − − + − − | 0,01 | 1/6 | 1,00 | RED |
| DV04a-H | k3.0 SELL r2,0 H60 | 2725 / -0,117 / -4,72 | 1,00 | 4060 | 40,2 | -0,052 | -1,0 | [-0,090; -0,011] | 0,7 | -0,047 / -0,056 | -0,092 | +0,110 | -0,052 (n 4060) | 97,2 / 98,0 | -0,047 | 2062 / -0,056 | − − − − − − | 4,00 | 1/6 | 1,00 | RED |
| DV04a-L | k3.0 BUY r2,0 H60 | 2612 / -0,110 / -4,32 | 1,00 | 3823 | 39,0 | -0,102 | -2,0 | [-0,143; -0,060] | 0,0 | -0,082 / -0,121 | -0,141 | +0,111 | -0,102 (n 3823) | 61,8 / 55,5 | -0,086 | 1936 / -0,117 | + − − − − − | 3,77 | 1/6 | 1,00 | RED |
| DV04b-U | b1.0 SELL r2,0 H60 | 1613 / -0,106 / -3,19 | 1,00 | 1420 | 35,9 | -0,131 | -3,3 | [-0,199; -0,058] | 0,0 | -0,142 / -0,120 | -0,163 | +0,100 | -0,131 (n 1420) | 8,6 / 9,0 | -0,156 | 634 / -0,100 | − − − − − − | 1,40 | 1/6 | 1,00 | RED |
| DV04b-D | b3.0 BUY r2,0 H60 | 640 / -0,048 / -0,89 | 1,00 | 226 | 38,1 | -0,015 | +4,4 | [-0,202; +0,175] | 42,2 | +0,054 / -0,084 | -0,041 | +0,098 | -0,015 (n 226) | 85,6 / 84,5 | -0,005 | 57 / -0,044 | − − + + − + | 0,22 | 1/6 | 1,00 | RED |
| DV04c-U | b3.0 BUY r2,0 H60 | 352 / -0,064 / -1,01 | 1,00 | 117 | 48,7 | +0,243 | +16,6 | [-0,006; +0,483] | 97,0 | +0,365 / +0,123 | +0,223 | +0,075 | +0,243 (n 117) | 100,0 / 99,0 | +0,225 | 21 / +0,323 | + − − + − + | 0,12 | 5/6 | 1,00 | RED (aynı-bar ≥ %0,5 → hücre geçersiz, prereg §3) |
| DV04c-D | b3.0 SELL r2,0 H60 | 321 / +0,022 / +0,30 | 0,99 | 114 | 36,8 | -0,057 | +1,1 | [-0,302; +0,186] | 32,1 | -0,075 / -0,039 | -0,078 | +0,073 | -0,057 (n 114) | 61,0 / 60,0 | -0,086 | 20 / +0,080 | + + − − − + | 0,11 | 0/6 | 1,00 | RED |
| DV05-TOP-L | k3.0 SELL r1,0 H15 | 211 / -0,036 / -0,67 | 1,00 | 455 | 49,2 | -0,098 | -2,5 | [-0,166; -0,035] | 0,1 | -0,108 / -0,087 | -0,138 | +0,091 | -0,098 (n 455) | 45,8 / 42,0 | -0,127 | 274 / -0,078 | − + − − + − | 0,45 | 1/6 | 1,00 | RED |
| DV05-TOP-S | k3.0 BUY r2,0 H15 | 86 / +0,159 / +1,35 | 0,42 | 205 | 45,4 | -0,040 | -0,9 | [-0,200; +0,120] | 28,8 | -0,131 / +0,051 | -0,080 | +0,091 | -0,040 (n 205) | 82,6 / 85,5 | -0,200 | 142 / +0,031 | + + + − − + | 0,20 | 1/6 | 1,00 | RED |
| DV05-GLB-L | k2.0 SELL r1,0 H60 | 662 / -0,048 / -1,32 | 1,00 | 826 | 48,3 | -0,101 | -2,6 | [-0,184; -0,025] | 0,4 | -0,052 / -0,151 | -0,142 | +0,100 | -0,101 (n 826) | 48,8 / 41,0 | -0,061 | 377 / -0,150 | − − − − − − | 0,81 | 1/6 | 1,00 | RED |
| DV05-GLB-S | k2.0 BUY r1,5 H60 | 1013 / +0,022 / +0,62 | 0,95 | 934 | 41,9 | -0,096 | -1,9 | [-0,173; -0,023] | 0,6 | -0,099 / -0,094 | -0,140 | +0,111 | -0,096 (n 934) | 66,0 / 76,0 | -0,097 | 469 / -0,096 | + − − − − − | 0,92 | 1/6 | 1,00 | RED |
| DV05-DIV-B | d BUY r2,0 H15 | 405 / -0,120 / -2,65 | 1,00 | 309 | 46,9 | -0,012 | +0,0 | [-0,119; +0,105] | 38,6 | -0,074 / +0,049 | -0,055 | +0,097 | -0,012 (n 309) | 97,6 / 96,0 | +0,368 | 290 / -0,037 | − − − + − − | 0,30 | 1/6 | 1,00 | RED |
| DV05-DIV-S | d SELL r1,0 H60 | 307 / +0,039 / +0,81 | 0,90 | 266 | 50,8 | -0,050 | -0,5 | [-0,204; +0,081] | 24,3 | +0,052 / -0,152 | -0,092 | +0,105 | -0,050 (n 266) | 80,2 / 80,0 | +0,118 | 204 / -0,101 | + − − + − − | 0,26 | 1/6 | 1,00 | RED |

Maliyet ve icra varyantları (POST ort R; aynı seçilen hücre):

| ID | PEP 1,85 | PEP stres 2,78 | sabit 15 $ | Binance maker 4 | Binance taker 10 | iyimser (kart 5) | OHLC-sezgisel | +1 dk gecikme | mod aynası |
|---|---|---|---|---|---|---|---|---|---|
| DV01a-C | -0,056 | -0,083 | -0,055 | -0,118 | -0,290 | +0,011 | -0,056 | -0,074 | -0,081 |
| DV01a-R | -0,053 | -0,080 | -0,053 | -0,115 | -0,288 | +0,018 | -0,053 | -0,058 | -0,007 |
| DV01b-R | -0,100 | -0,122 | -0,105 | -0,151 | -0,296 | -0,041 | -0,100 | -0,132 | -0,014 |
| DV01b-C | -0,107 | -0,135 | -0,111 | -0,173 | -0,359 | -0,028 | -0,107 | -0,102 | -0,032 |
| DV01c-C | -0,057 | -0,087 | -0,060 | -0,125 | -0,316 | +0,017 | -0,057 | -0,033 | -0,092 |
| DV01c-R | -0,017 | -0,045 | -0,020 | -0,082 | -0,263 | +0,068 | -0,017 | -0,018 | -0,030 |
| DV01d-R | -0,162 | -0,184 | -0,162 | -0,214 | -0,360 | -0,094 | -0,162 | -0,206 | -0,078 |
| DV01d-C | -0,135 | -0,162 | -0,138 | -0,197 | -0,372 | -0,061 | -0,135 | -0,141 | -0,011 |
| DV02-P5L-F | -0,076 | -0,105 | -0,081 | -0,144 | -0,334 | +0,011 | -0,076 | -0,132 | -0,090 |
| DV02-P5L-W | -0,124 | -0,153 | -0,129 | -0,192 | -0,383 | -0,045 | -0,124 | -0,100 | -0,026 |
| DV02-P1L-W | -0,118 | -0,152 | -0,122 | -0,196 | -0,415 | -0,014 | -0,118 | -0,080 | -0,078 |
| DV02-P1oL-F | -0,199 | -0,229 | -0,205 | -0,268 | -0,461 | -0,105 | -0,199 | -0,301 | +0,007 |
| DV02-P1oL-W | +0,000 | -0,030 | -0,005 | -0,069 | -0,261 | +0,079 | +0,000 | +0,016 | -0,137 |
| DV02-P5S-F | -0,026 | -0,057 | -0,032 | -0,096 | -0,291 | +0,063 | -0,026 | -0,009 | -0,142 |
| DV02-P5S-W | -0,041 | -0,071 | -0,046 | -0,111 | -0,306 | +0,047 | -0,041 | -0,013 | -0,050 |
| DV02-P1oS-F | -0,082 | -0,115 | -0,089 | -0,159 | -0,373 | +0,029 | -0,082 | -0,077 | -0,120 |
| DV02-P1oS-W | -0,080 | -0,113 | -0,086 | -0,156 | -0,370 | +0,009 | -0,080 | -0,077 | -0,065 |
| DV03a-L | -0,046 | -0,082 | -0,058 | -0,129 | -0,361 | +0,049 | -0,046 | -0,072 | -0,113 |
| DV03a-S | -0,135 | -0,172 | -0,143 | -0,221 | -0,462 | -0,036 | -0,135 | -0,153 | -0,021 |
| DV03b-L | -0,100 | -0,141 | -0,112 | -0,195 | -0,461 | +0,007 | -0,100 | -0,072 | -0,107 |
| DV03b-S | -0,117 | -0,162 | -0,123 | -0,221 | -0,511 | -0,003 | -0,117 | -0,119 | -0,096 |
| DV03c-L | -0,051 | -0,085 | -0,063 | -0,129 | -0,347 | +0,032 | -0,051 | -0,005 | -0,217 |
| DV03c-S | -0,470 | -0,503 | -0,477 | -0,548 | -0,765 | -0,379 | -0,470 | +0,017 | -0,261 |
| DV03d-L | -0,050 | -0,085 | -0,062 | -0,130 | -0,352 | +0,030 | -0,050 | -0,039 | -0,049 |
| DV03d-S | -0,490 | -0,524 | -0,495 | -0,567 | -0,782 | -0,400 | -0,490 | -0,490 | +0,322 |
| DV04a-H | -0,052 | -0,092 | -0,055 | -0,144 | -0,401 | +0,058 | -0,052 | -0,034 | -0,118 |
| DV04a-L | -0,102 | -0,141 | -0,106 | -0,193 | -0,449 | +0,009 | -0,101 | -0,106 | -0,070 |
| DV04b-U | -0,131 | -0,163 | -0,134 | -0,206 | -0,413 | -0,031 | -0,131 | -0,104 | -0,005 |
| DV04b-D | -0,015 | -0,041 | -0,020 | -0,076 | -0,245 | +0,083 | -0,015 | -0,160 | -0,273 |
| DV04c-U | +0,243 | +0,223 | +0,239 | +0,198 | +0,072 | +0,318 | +0,243 | +0,261 | -0,238 |
| DV04c-D | -0,057 | -0,078 | -0,062 | -0,106 | -0,243 | +0,016 | -0,057 | -0,064 | -0,065 |
| DV05-TOP-L | -0,098 | -0,138 | -0,103 | -0,191 | -0,453 | -0,007 | -0,098 | -0,099 | -0,086 |
| DV05-TOP-S | -0,040 | -0,080 | -0,029 | -0,133 | -0,394 | +0,052 | -0,040 | -0,017 | -0,123 |
| DV05-GLB-L | -0,101 | -0,142 | -0,109 | -0,194 | -0,453 | -0,002 | -0,101 | -0,085 | -0,097 |
| DV05-GLB-S | -0,096 | -0,140 | -0,102 | -0,196 | -0,476 | +0,014 | -0,096 | -0,111 | -0,130 |
| DV05-DIV-B | -0,012 | -0,055 | -0,008 | -0,112 | -0,390 | +0,085 | -0,012 | +0,025 | -0,158 |
| DV05-DIV-S | -0,050 | -0,092 | -0,040 | -0,148 | -0,421 | +0,054 | -0,050 | -0,126 | -0,164 |

### Inferences
- Binance maker (4 bp) ve taker (10 bp) varyantlarında **tüm** ID'ler negatif (DV04c-U maker +0,198 / taker +0,072 hariç). Sabit-15 $ varyantı PEP'ten
  ancak birkaç binde R farklı (POST dönemi fiyatları 40–120 k$ → 15 $ ≈ 1,3–3,7 bp).
- Plasebo yüzdeliği ≥ %95 olan ama net negatif ID'ler var (DV04a-H %97/−0,052R, DV02-P1oL-W %98/+0,000, DV05-DIV-B %98/−0,012, DV02-P5S-F %95/−0,026):
  "rastgele girişten (−0,09R) daha az kaybediyor" ≠ kâr. Bu hücrelerin taban-üstü brüt kenarı +0,03…+0,08R, maliyet/R ≈ 0,09–0,10R'nin altında.
- +1 dk ek gecikmede (sağlamlık) üç ID küçük artıya dönüyor (DV02-P1oL-W +0,000→+0,016, DV05-DIV-B −0,012→+0,025, DV03c-S −0,470→+0,017 ama n 9); hepsi maliyet/R'nin (≈0,09R) ve icra çıtasının altında, hiçbir kart ölçütünü değiştirmiyor — gecikmeye duyarlılık gürültü düzeyinde.

### Gaps
- Per-yıl tam sayılar (n, R, bp) yalnız seçilen hücreler için `selected.json → years`; tüm hücrelerin yıllık kırılımı çıkarılmadı (gerek görülmedi: üç bölme işareti `cells.csv`'de).

## 3. OI × fiyat dörtlüleri (DV01): yeni long / short kapatma / yeni short / long tasfiyesi → devam mı dönüş mü?

### Takeaway
Dört dörtlünün hiçbirinde, iki modun (devam/dönüş) hiçbirinde POST net pozitif hücre seçilmedi; 8 ID'nin hepsi RED (POST −0,017…−0,162R).
"OI ile fiyat aynı yönde → devam, ters yönde → dönüş" folklorü 15–60 dk'da bu veride **yok**: seçilen hücrelerin DISC işaretleri OOS/BLIND'da tutmuyor.

### Cited Findings
- Tanım: [eff−W, eff) penceresinde perp log getirisi ve OI değişimi, 30 g kayan z (shift(1)); |z| ≥ k (k 1,5/2,5), W 15/60 dk; karar = metrics satırının
  yayınlandığı dakika (eff, 1 dk pay), giriş eff+1. Olay sayıları (tüm dönem, epizodlu): ör. W15 k1,5 a/b/c/d = 1.691 / 2.464 / 1.284 / 2.860 —
  [out/event_counts.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/event_counts.csv)
- Hizalama denetimi: 1m ızgarada t = eff satırının `metrics_eff_ts` değeri %100 eff (2024-03-04 damga geçişi doğru çözülmüş) — [logs/03_events.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/logs/03_events.log)
- En iyi DISC: DV01a-C (fiyat↑ OI↑ → BUY) W60 k2,5 r1 H15 DISC +0,096R (n 85) → POST −0,056R, OOS −0,114, BLIND +0,012; 2024 −0,044 / 2025 −0,212.
  W15 k2,5 hücresi DISC'te z 2,56 (+0,18R, n 148) idi ama aynı-bar %0,7 → seçilemez; OOS −0,03 / BLIND −0,06 (yine tutmuyor) — [out/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/cells.csv)
- Taban-üstü brüt kenar ID ortalamaları (DISC/OOS/BLIND, R): a-C +0,110/−0,042/+0,036; b-R −0,063/−0,024/−0,046; c-C −0,026/+0,013/−0,010;
  d-R −0,060/0,000/−0,028 — dönemler arası işaret değişiyor — [out/gross_edge_by_hid.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/gross_edge_by_hid.csv)

### Inferences
- "Long tasfiyesi (fiyat↓ OI↓) → dönüş" (DV01d-R) en kötü dörtlülerden: POST −0,162R, BLIND −0,297R. Aşağı yönlü OI boşalması 15–60 dk'da
  dönmüyor; "korku döner" (§3 meta-ders 2) bu ölçekte ve bu tanımla görülmüyor.

### Gaps
- OI yalnız 5 dk çözünürlükte ve 1–6 dk gecikmeli; dakika-altı OI (canlı WebSocket) bu sonucu değiştirebilir mi bilinmiyor.

## 4. Tasfiye vekili olayları (DV02): fade mi follow mu, long-liq/short-liq asimetrisi — S05/S06'nın OI-teyitli yeni tanımı

### Takeaway
Değerlendirilebilen dört fade kolunun (korku döner / coşku döner) hepsi POST'ta net negatif; değerlendirilemeyen iki 1 dk fade kolu da DISC'te −0,17…−0,23R; follow kolları da negatif ya da ≈0. OI teyidi fade'i
kötüleştiriyor. 1 dk akış vekilinde kendi aynı-bar oranı %0,6–3,1 → bu kollar ön kayıt gereği geçersiz. Asimetri dönemler arası tutarsız;
tek tutarlı parça "short-squeeze'i fade etme" kolunun brüt olarak da kaybetmesi (coşku dönmez — BTC-S06 ile aynı mekanizma, 1 dk ölçekte).

### Cited Findings
- DV02-P5L-F (5 dk long-liq vekili → BUY): DISC −0,161R (z −4,17), POST −0,076R, BLIND −0,168R; 6 yılın 6'sında negatif. DV02-P1oL-F (1 dk akış +
  OI ≤ −2σ teyidi → BUY): DISC −0,141, POST −0,199 [−0,339; −0,063], P(EV>0) %0,2, BLIND −0,284, yılların hepsi negatif — [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv)
- DV02-P1L-F/P1S-F/P1S-W: altı geometrinin hepsinde (ya da 5/6'sında) DISC aynı-bar ≥ %0,5 (P1S-F r1: %3,1) → seçilebilir hücre yok; ham DISC net R
  P1L-F −0,17…−0,19, P1S-F −0,17…−0,23 (yine de negatif) — [out/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/cells.csv)
- Asimetri (taban-üstü brüt R, 6 geometri ortalaması; L-fade / S-fade / fark): P5 DISC −0,096/−0,048/−0,048, OOS +0,079/+0,054/+0,025, BLIND −0,046/+0,020/−0,066;
  P1 DISC −0,065/−0,088/+0,023, OOS +0,052/−0,114/+0,166, BLIND +0,099/−0,060/+0,159; P1o DISC −0,076/−0,058/−0,018, OOS −0,018/−0,045/+0,027,
  BLIND −0,108/+0,004/−0,112 — [out/dv02_asymmetry.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/dv02_asymmetry.csv)
- Post-hoc (ön-kayıtsız): 1 dk short-liq akışını takip (BUY) net R DISC −0,056…−0,095, OOS −0,040…+0,079, BLIND −0,032…+0,003; OI teyitli sürümü BLIND −0,10…−0,18 —
  [out/posthoc.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/posthoc.csv)

### Inferences
- E41 kontrolü: P1'de L−S farkı OOS/BLIND'da +0,16 ama kaynağı S-fade kolunun kaybı (ve L-fade'in yalnız 2024+ brüt artısı), L-fade **netinde** pozitif değil
  (DISC −0,17). "Korku döner"in OI-teyitli versiyonu BTC'de 15–60 dk'da yok; S05'in (−0,021R) yeni tanımla tekrar açılması sonucu değiştirmedi.
- Vekil olayları yüksek oynaklık dakikaları → ATR-SL geniş (seçilen hücrelerde medyan SL 32–36 bp), ama aynı-bar hâlâ yüksek: likidasyon kaskadında
  1m bar her iki seviyeyi birden süpürüyor. 1m veride bu olayların "kenarı" ölçülemez; ölçülebilen kısmı negatif.

### Gaps
- Alt-dakika sıralama (1 s) 2026-04 öncesi yok → P1 kolları için aynı-bar belirsizliği çözülemedi.

## 5. Funding (DV03): kalabalık taraf kontraryan, uzlaşma (00/08/16 UTC) öncesi/sonrası

### Takeaway
Dört funding hipotezinin hiçbiri çalışmıyor; ayrıca **fp ≥ 1,5 bp rejimi 2025-07'den beri hiç oluşmadı** → "kalabalık long" kollarının BLIND olayı 0
(yapısal olarak doğrulanamaz). Uzlaşma öncesi "öder taraf kapatır" (DV03c) ve sonrası "rahatlama" (DV03d) a priori yönlerinde negatif; aynaları da
(post-hoc) negatif ya da n < 10.

### Cited Findings
- Funding dağılımı (settled, 5.904 uzlaşma): %31'i tam 1,00 bp, p95 1,79, p99 4,6 bp; fp ≥ 1,5 bp saatleri DISC 1.310 / OOS 1.175 / BLIND **0** —
  [prereg.md §0/EK-1](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/prereg.md), [out/event_counts.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/event_counts.csv)
- DV03a-L (fp ≥ 3 bp saatlik → SELL): DISC +0,054 → POST −0,046 (2021 +0,092, 2023 −0,062, 2024 −0,051), dairesel plasebo %96 ama net negatif.
  DV03b-S (fp ≤ 0 ∧ 2×ATR1m yukarı şok → BUY): POST n 2.597, −0,117R, P(EV>0) %0,0; DV03b-L −0,100R — [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv)
- DV03c/d: θ = −1 bp kollarında OOS+BLIND toplam 9–10 olay (n yetersiz); θ = 0 kolları (n 444/426 DISC) seçilmedi. Post-hoc ayna "negatif uzlaşma sonrası BUY"
  θ0: DISC −0,016…−0,070, OOS −0,018…−0,065, BLIND −0,039…−0,177 (6/6 geometri negatif) — [out/posthoc.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/posthoc.csv)
- `funding_last_estimated=1` (Ekim 2026) yalnız DV03d'yi etkiler; DV03d'nin BLIND olayları θ0 kolunda, seçilen θ−1 hücresinde BLIND 7 olay — verdikti etkilemiyor.

### Inferences
- BTC-M06 (koşulsuz funding saati) X idi; işarete/seviyeye koşullamak (yeni tanım) da X. Funding 8 saatlik ve 2024 sonrası sıkışmış bir seri; scalp ufkunda
  bilgi değil, en fazla rejim etiketi. Funding'in kendisi (premium'un uç kısmı) DV04a'da daha doğrudan sınandı, o da negatif.

### Gaps
- Funding tahminimiz (`funding_pred_running`) Binance arayüzündeki "tahmini funding" ile birebir doğrulanmadı (veri notu 02).

## 6. Premium/baz dislokasyonu (DV04): premium z ortalamaya dönüş; spot-öncülü vs perp-öncülü hareketler

### Takeaway
Premium z-uçlarını fade etmek iki yönde de negatif (POST −0,052 / −0,102R, n ~4.000/yön). Perp-öncülü 5 dk ±3σ yukarı hareketi fade etmek negatif
(−0,131R; yani perp-öncülü yükselişler de sürüyor). Tek pozitif ID, **spot-öncülü yukarı hareketi takip** (DV04c-U b3, POST +0,243R) — ama DISC'te
negatif (−0,064), POST'un %71'i 2024'te, BLIND n 21, kendi aynı-bar oranı %0,85 → ön kayıt gereği geçersiz; seçilebilirliği "en az kötü DISC hücresi" olmasından.

### Cited Findings
- DV04a-H (zp ≥ 3 → SELL) DISC −0,117 (z −4,72), POST −0,052 [−0,090; −0,011], 6 yılın 6'sı negatif, saat-plasebo %97,2; DV04a-L POST −0,102 —
  [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv)
- DV04c-U b3 r2 H60: DISC n 352 −0,064R; OOS n 96 +0,225; BLIND n 21 +0,323; yıllar 2021 +0,055 (n 126), 2022 −0,095 (165), 2023 −0,224 (61), 2024 +0,300 (83),
  2025 −0,003 (32), 2026 +0,713 (11); POST GA [−0,006; +0,483], P(EV>0) %97,0, stres +0,223, icra farkı +0,075, plasebo %100/%99, kart 5/6 (n 117 < 150),
  POST aynı-bar %0,85, medyan SL 54,7 bp, p_sel 1,00 — [out/selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/selected.json)
- Post-hoc: aynı yukarı ±3σ hareketlerde "perp-öncülü takip" b3 OOS −0,004…−0,091, BLIND +0,011…+0,130 (n 58, aynı-bar %1,7–3,4); b1 hem perp- hem spot-öncülü
  takip DISC'te 12/12 negatif — [out/posthoc.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/posthoc.csv)

### Inferences
- "Perp primi şişince sat" kalabalık-kaldıraç fade'i BTC 15–60 dk'da çalışmıyor; tersine premium z-uçları çoğunlukla hareketin devam ettiği anlar.
- DV04c-U bir **dönem (2024, ETF-sonrası spot talebi) etkisi** gibi duruyor: DISC'te negatif, 2025'te ≈0, BLIND 21 olay. Mekanizma hipotezi ("spot-öncülü
  yükseliş = gerçek talep, sürer") makul ama bu veriyle kanıtlanamaz; yalnız yeni ön kayıt + ileri gölge + 1 s veriyle (aynı-bar sorunu) açılabilir.

### Gaps
- Spot = Binance spot; Coinbase/ETF akışı yok (veri notu 01: CME/Coinbase lead 0,05–0,15 sn). "Spot-öncülü"nün Binance-spot dışı karşılığı ölçülmedi.

## 7. Long/short oranları (DV05): top-trader / global kalabalık uçları (kontraryan) ve ıraksama

### Takeaway
Altı ID'nin hepsi POST'ta negatif (−0,012…−0,101R). Global hesap oranı k=3 DISC'te yalnız 13 olay / 3 gün (2021-06-09, 2022-05-12 LUNA, 2023-08-29) —
seçilemedi; ama DISC Holm'u "geçen" 5 hücrenin tamamı bu 13 olaydan geliyor (gün-kümeli SE 3 kümeyle anlamsız → z 11,7 sahte).

### Cited Findings
- Seçilen hücreler: TOP-L k3 −0,098 [−0,166; −0,035], TOP-S k3 −0,040, GLB-L k2 −0,101, GLB-S k2 −0,096, DIV-B −0,012 (OOS n 19), DIV-S −0,050; dairesel plasebo
  (birincil) %41–96 — [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv)
- Eksik dönemler: top-trader oranları 2021-12→2022-12 çoğunlukla NaN → TOP k3 DISC olayları 219/88 (L/S); DIV-B OOS yalnız 19 olay — [out/event_counts.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/event_counts.csv)
- DISC Holm < 0,05 olan 5 hücre: hepsi DV05-GLB-S k3 (n 11–13, 3 gün; OOS +0,001…+0,223, BLIND −0,012…−0,259) — [out/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/cells.csv)

### Inferences
- L/S oranları kalıcı rejim değişkeni; kontraryan okuması 15–60 dk'da ne ilk dönemde ne sonra çalışıyor. "Akıllı para (top) vs kalabalık (global)" ıraksaması da yok.

### Gaps
- Oranların canlı yayın gecikmesi ölçülmedi (veri notu 02); +1 dk gecikme sağlamlığı sonucu değiştirmedi.

## En iyi aday(lar)

### Takeaway
**LIVE veya GÖLGE adayı yok.** En yakın ıskalar ve neden düştükleri:

### Cited Findings
1. **DV04c-U — spot-öncülü 5 dk yukarı şoku takip (BUY).** Tam tanım: karar barı t'de r5 = ln(spot_close[t]/spot_close[t−5]), z5 = r5 / std(r5; önceki 30 g, shift(1)) ≥ 3
   ∧ Δbaz₅ = basis_perp_spot_bp[t] − basis_perp_spot_bp[t−5] ≤ −3 bp (spot perp'ten hızlı yükseldi); epizod 60 dk; giriş t+1 açılışı BUY; SL = max(19 bp, 1,1×ATR14(5m)),
   TP = 2×SL, zaman 60 dk, rollover öncesi kapat. POST n 117, +0,243R (+16,6 bp), P(EV>0) %97, plasebo %100, kart 5/6. **Düşme nedenleri:** (i) DISC −0,064R (seçim
   en-az-kötü hücreyi aldı, p_sel 1,00 — keşif kanıtı yok), (ii) POST aynı-bar %0,85 ≥ %0,5 → ön kayıt gereği geçersiz, (iii) n 117 < 150, (iv) POST'un ağırlığı
   2024 (n 83 / +0,300), BLIND n 21, (v) Holm 1,00 — [out/selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/selected.json)
2. **DV02-P1oL-W — OI-teyitli 1 dk long tasfiyesini takip (SELL)**, r1,5 H15: POST +0,000R (n 347), BLIND +0,052, plasebo %98 — taban-üstü brüt +0,068R
   maliyetin (≈0,09R) altında; DISC +0,004 — [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv)
3. **DV04a-H — premium z ≥ 3 fade (SELL)**: n ~4.000 ile en yüksek hacim; plasebo %97 ama net −0,052R, 6/6 yıl negatif — "rastgeleden az kayıp" kalıbı.

### Inferences
- Hiçbiri canlıya ya da gölgeye önerilmez. DV04c-U yalnız bir **fikir (C)** olarak defterde kalmalı: yeniden açmak için yeni ön kayıt (DISC'i 2024+ yapmayan),
  1 s veriyle aynı-bar çözümü ve ≥150 ileri olay gerekir.

### Gaps
- Broker M1 teyidi yapılmadı (aday olmadığından).

## Defter satırı taslağı

### Takeaway
§2.11'e (veya yeni "§2.12 BTC scalp türev ailesi") eklenecek satırlar; biçim §6. Kanıt kökü `research/btc_scalp_20261021/fam_turev/` (ön kayıt `prereg.md`, sonuçlar `out/`).

### Cited Findings
| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-SC-DV01 | 2026-10-22 | **OI × fiyat dörtlüleri** (5 dk metrics, [eff−W, eff) W 15/60; perp getiri z ve ΔOI z ≥ k, k 1,5/2,5; 4 dörtlü × devam/dönüş; SL max(19 bp, 1,1×ATR5m), TP 1/1,5/2×SL, 15/60 dk; giriş eff+1) | 8 ID × 24 hücre. Seçilenlerin POST (2024-01-11→2026-10-20) net R'si −0,017…−0,162, hiçbiri P(EV>0) > %42; en iyi DISC (yeni long→BUY, W60 k2,5) +0,096 → POST −0,056; long tasfiyesi→BUY (dönüş) POST −0,162, BLIND −0,297. Max-z p_sel ≥ 0,63. Kanıt `out/summary.csv`, `cells.csv` | X |
| BTC-SC-DV02 | 2026-10-22 | **Tasfiye vekili fade/follow** (5 dk vekil P5; 1 dk akış vekili P1; P1 ∧ aynı 5 dk pencerede z_OI ≤ −2 = P1oi; long-liq/short-liq × fade/follow; BTC-S05/S06'nın OI-teyitli yeni tanımı) | Fade kollarının hepsi negatif: P5L-F POST −0,076 (6/6 yıl −), P1oL-F −0,199 [−0,339; −0,063] P %0,2; follow kolları −0,124…+0,000. P1 kolları aynı-bar %0,6–3,1 → ön kayıtla geçersiz. Asimetri dönemler arası tutarsız; short-squeeze fade brüt de kaybediyor (coşku dönmez). **OI teyidi fade'i kurtarmıyor.** Kanıt `out/summary.csv`, `dv02_asymmetry.csv`, `posthoc.csv` | X |
| BTC-SC-DV03 | 2026-10-22 | **Funding** (fp = kendi nedensel tahminimiz; saatlik kalabalık-taraf kontraryan θL 1,5/3 bp, θS 0/−1 bp; kalabalık ∧ 2×ATR1m karşı şok; uzlaşma −30 dk öder-taraf kapanışı H35; uzlaşma +1 dk rahatlama) | 8 ID'nin POST'u −0,046…−0,490; fp ≥ 1,5 bp 2025-07'den beri yok → kalabalık-long kollarının BLIND'ı 0. Saatlik fp ≥ 3 SELL dairesel plasebo %96 ama −0,046R. Ayna "negatif uzlaşma sonrası BUY" (sonradan) θ0 6/6 geometri her bölmede negatif. BTC-M06'nın koşullu hâli de X. Kanıt `out/summary.csv`, `posthoc.csv` | X |
| BTC-SC-DV04 | 2026-10-22 | **Premium/baz** (premium 1.440 dk z ≥ 3/5 fade; 5 dk ±3σ spot hareketi × Δbaz₅ ≥ 1/3 bp: perp-öncülü fade, spot-öncülü takip) | Premium fade iki yönde negatif (H −0,052 n 4.060, L −0,102 n 3.823; 6/6 yıl −); perp-öncülü yukarı fade −0,131. **Spot-öncülü yukarı takip (b3, r2, H60)** POST +0,243R n 117 P %97 plasebo %100 kart 5/6 — ama DISC −0,064, POST aynı-bar %0,85 (ön kayıtla geçersiz), %71'i 2024, BLIND n 21, p_sel 1,00. Kanıt `out/selected.json`, `posthoc.csv` | X (DV04c-U: C fikir — yeni ön kayıt + 1 s veri + ileri gölge) |
| BTC-SC-DV05 | 2026-10-22 | **L/S oranları** (log oran 30 g z; top-trader pozisyon / global hesap ≥ k veya ≤ −k, k 2/3, saatlik kontraryan; top z ≥ 2 ∧ global z ≤ −1 ıraksaması) | 6 ID POST −0,012…−0,101; dairesel plasebo %41–96. GLB k3 DISC'te 13 olay / 3 gün → DISC Holm'u "geçen" 5 hücre küme-sayısı artefaktı. Kanıt `out/summary.csv`, `cells.csv` | X |
| BTC-SC-DV00 | 2026-10-22 | Aile özeti: 40 ID / 468 hücre, PEP 1,85 bp, sonraki 1m açılışı, aynı yıl×saat plasebo + dairesel kaydırma, max-z 500 kopya | LIVE 0, GÖLGE 0, RED 40. En iyi seçilebilir DISC z 1,63 (boş %95 = 2,47). 370 seçilebilir hücreden üç bölmede de net + olan 0; taban-üstü brüt + olan %13,4 (tesadüf %12,5). Binance maker/taker'da tüm ID'ler (DV04c-U hariç) negatif. | X (aile) |

### Inferences
- Defterin §3'üne aday meta-ders: "Türev konumlanma verisi (OI/funding/premium/L-S/tasfiye vekili) BTC'de 15–60 dk ufkunda ne net ne tesadüf-üstü brüt bilgi
  taşıyor; kalabalık-kaldıraç fade'leri (premium, funding, L/S, tasfiye) sistematik olarak **devam** eden hareketleri satıyor/alıyor."

### Gaps
- Defter bu ajan tarafından düzenlenmedi (yazma kapsamı yalnız `fam_turev/`); satırlar koordinatörün eklemesi için taslaktır. 1. KURAL oturum notu da aynı nedenle yazılmadı.

## Yeni yöntem tuzakları

### Takeaway
Bu turda bulunan, defterin §1'ine eklenmeye aday 5 tuzak (numara koordinatöre bırakıldı; E50 sonrası).

### Cited Findings
- **(T1) Gün-kümeli SE az kümeyle sahte z üretir.** DV05-GLB-S k3'te 13 olay 3 güne düşüyor → z 11,7, DISC Holm 5 hücrede "anlamlı"; OOS/BLIND'da işaret dağınık.
  Önlem: z/Holm tablosuna küme (bağımsız gün) sayısını yaz; küme < 20–30 ise z raporlama, hücreyi n_gün ile süz (ön kayıttaki n ≥ 50 olay süzgeci yetmez, gün sayısı da gerekir) —
  [out/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/cells.csv)
- **(T2) Nominal seviye eşiği yapısal rejim kaymasında bölmeyi boşaltır.** fp ≥ 1,5 bp 2025-07'den beri hiç yok → funding "kalabalık long" kollarının BLIND'ı 0
  (E40/E45'in funding karşılığı). Önlem: ön kayıtta her bölmenin beklenen olay sayısını özellik dağılımından hesapla; seviye yerine kayan yüzdelik + nominal alt sınır ikilisini ayrı hücre yap —
  [out/event_counts.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/event_counts.csv)
- **(T3) "Plasebonun üstünde ama sıfırın altında."** Maliyetli rastgele giriş −0,09…−0,11R olduğu için %95–98 plasebo yüzdeliği ile −0,05R birlikte görülür
  (DV04a-H, DV05-DIV-B, DV02-P1oL-W). Önlem: plasebo ölçütünü her zaman net-R > 0 ve brüt-kenar ≥ maliyet/R ile birlikte uygula; yüzdeliği tek başına "kenar" diye raporlama —
  [out/summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/summary.csv)
- **(T4) Kaskad/akış olaylarında aynı-bar oranı rastgele girişin 20–100 katı.** Rastgele girişte %0,01–0,04 iken 1 dk tasfiye vekili olaylarında %0,6–3,1 → en "scalp"
  benzeri olaylar 1m veriyle ölçülemez; olay setinin **kendi** aynı-bar oranı hücre bazında (ve POST'ta ayrıca) denetlenmeli, yalnız seçim döneminde değil
  (EK-2: ilk koşuda yalnız DISC'te uygulanmıştı) — [out/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/cells.csv), [prereg.md EK-2](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/prereg.md)
- **(T5) "Seçilen en iyi DISC hücresi" negatif olabilir; POST'ta pozitif çıkması keşif değildir.** DV04c-U DISC −0,064 ile seçildi (grubun en az kötüsü), POST +0,243.
  Önlem: verdikt şemasına "seçilen hücrenin DISC net R'si > 0" koşulunu ön kayıtta ekle; aksi hâlde mekanik GÖLGE üretilebilir (bu turda aynı-bar kuralı yakaladı) —
  [out/selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/out/selected.json)
- Ek olgu (tuzak değil, taban): ±1,1×ATR5m simetrik brakette BTC 1m'de aşağı seviye yukarıdan biraz daha sık önce vuruluyor (H60 r1 brüt long −0,008R / short +0,007R,
  5 yılda pozitif sürüklenmeye rağmen; motor kaba döngüyle doğrulandı) → aynı-yön plasebo zorunlu, sıfır taban değil (E43 ile akraba) —
  [logs/02_outcomes.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_turev/logs/02_outcomes.log)

### Inferences
- T4 ile T5 birleşince: en ilginç görünen ıskalar (likidasyon dakikaları, ±3σ şoklar) tam da 1m verinin güvenilmez olduğu anlarda yoğunlaşıyor; bu ailede
  "kenar" iddiası 1 s veri olmadan kurulamaz ve 1 s veri yalnız son 6 ay için var.

### Gaps
- T1–T5'in diğer ailelerde (paralel ajanlar) tekrarlanıp tekrarlanmadığı bu not kapsamında kontrol edilmedi.
