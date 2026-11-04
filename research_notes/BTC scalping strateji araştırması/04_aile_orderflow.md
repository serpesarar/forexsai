# BTC scalping — aile: EMİR AKIŞI (taker dengesizliği, CVD ayrışması, hacim patlaması, spot–perp akışı, büyük işlem, çeyrek-saat)

Kapsam: 2026-10-22, sızıntısız 1m geri-testi; yeni indirme yok, kutuya/Supabase'e dokunulmadı, commit yok. Yalnız
`research/btc_scalp_20261021/fam_orderflow/` altına yazıldı. Ön kayıt sonuçlardan ÖNCE yazıldı:
[prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/prereg.md)
(Ek A1 = olay sayımı, getiri görülmeden; Ek A2 = sonuçlardan SONRA eklenen post-hoc incelemeler, açıkça etiketli).
Betikler: `00_selftest.py` (motor kaba-döngü eşlemesi), `01_build.py` (özellik + önek testi + olaylar), `02_eval.py`
(1.224 hücre, seçim, max-z boşu, kart), `03_explore_1s.py` (OF07), `04_posthoc.py` (Ek A2). Günlükler `logs/`, tablolar `results/`.
Python `/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python -I` (numpy 2.4.6, pandas 2.3.3). Ondalık: metinde virgül, tablolarda nokta.

**Protokol özeti (hepsi ön-kayıtlı):** fiyat yolu Binance spot 1m, akış Binance perp/spot taker hacmi; karar = t barı kapanışı,
giriş = t+1 açılışı; SL = S1 max(19 bp, 1,1×ATR5m) veya S2 max(28 bp, 2×ATR5m); TP/SL ∈ {1; 1,5; 2}; zaman stopu 15/30/60 dk;
aynı bar TP+SL → SL; SL boşluk-duyarlı + 1 bp kayma (vuruş dakikası |1m getiri| > DISCOVERY p99 = 29,3 bp ise 5 bp);
NY 17:00 rollover'dan 2 dk önce zorunlu kapanış, [RO−2, RO+3) giriş yok; maliyet PEP 1,85 bp (stres 2,78; sabit 15 $; Binance maker 4 /
taker 10); epizod bastırma 30 dk/hücre/yön. Bölmeler DISCOVERY 2021-06→2023-12 · OOS 2024-01-11→2025-06 · BLIND 2025-07→2026-10-20;
seçim yalnız DISCOVERY'de, kart POST = OOS∪BLIND üzerinde.

---

## 1. Veri, motor ve sızıntı denetimleri güvenilir mi?

### Takeaway
Evet. Motor kaba-döngüyle birebir (0/108.000), özellikler önek testinden geçti, rollover/DST doğru. Rastgele girişin net R'si tam
olarak maliyet/SL kadar negatif (S1 ≈ −0,09…−0,11R, S2 ≈ −0,05…−0,07R); yani ölçüm tabanı not 03'teki fizikle tutarlı.

### Cited Findings
- `Engine.outcome` (rollover sınırlı H′, boşluk-duyarlı SL, kayma, üç aynı-bar modu) 3.000 rastgele giriş × 6 geometri × 2 yön × 3 mod
  kaba döngüyle karşılaştırıldı: **uyuşmazlık 0 / 108.000**; hiçbir giriş zorunlu-kapanış penceresinde değil, min H′ = 5 —
  [00_selftest.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/logs/00_selftest.log). İlk-dokunuş
  çekirdeği `feasibility/lib.py` (önceki kaba-döngü doğrulaması 0/18.000) — [03_maliyet_fizibilite_kaldirac.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20scalping%20strateji%20ara%C5%9Ft%C4%B1rmas%C4%B1/03_maliyet_fizibilite_kaldirac.md).
- Önek testi: 2023-06-15 12:00 sonrası fiyatlar ×1,3 ve hacimler rastgele ×0,2–5 bozuldu; öncesindeki 3.000 dakikanın tüm özellikleri
  (z-skorları, CVD farkları, N-bar max/min, hacim z) **birebir aynı** → "önek testi: OK" — [01_build.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/logs/01_build.log).
- Rollover: 2024-07-10 ve 2025-03-09 (yaz) zorunlu kapanış 20:58 UTC; 2024-01-10 ve 2025-11-02 (kış) 21:58 UTC (DST geçiş günleri dahil doğru).
- Geçerli giriş dakikası 2.815.230 (ATR5m mevcut); DISCOVERY |1m getiri| p99 = 29,29 bp (kayma eşiği) — [02_eval.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/logs/02_eval.log).
- Rastgele giriş net R (PEP), segment ortalaması: S1 geometrileri −0,086…−0,109R, S2 −0,050…−0,066R; DISC/OOS/BLIND arasında ±0,01 —
  [random_entry_baseline.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/random_entry_baseline.csv).

### Inferences
- Plasebo tabanı = "maliyet/SL"; her hücre bu tabana karşı okunmalı (sıfıra değil). S1'in SL'i 2024+'da çoğunlukla 19 bp tabanına
  yapışıyor (seçilen OF04b/OF06 hücrelerinde POST medyan SL tam 19,0 bp) → 2024+ rejiminde "ATR-ölçekli" S1 fiilen sabit 19 bp braket.

### Gaps
- Fiyat yolu Binance spot; Pepperstone broker M1 ile teyit (E47) yapılamadı — broker verisi yalnız 2026-10-05→21 ve en yakın aday
  (OF02_W15_th5) bu pencerede hiç olay üretmedi.

---

## 2. Ön-kayıtlı yedi hipotez maliyet sonrası kârlı mı?

### Takeaway
**Hayır — yedisi de RED.** Her biri POST'ta net negatif (−0,023…−0,093R, −0,9…−2,2 bp/işlem), kart 1/6 (yalnız hacim ölçütü).
Akış koşullu girişlerin plaseboya göre brüt fazlalığı en iyi durumda +0,01–0,04R / sub-bp; gereken ≥0,15R'nin çok altında.
İki hücre plaseboyu istatistiksel olarak yeniyor (OF01, OF06: plasebo yüzdeliği ≥99,9, Holm p < 0,05) ama ekonomik olarak değil.

### Cited Findings
Seçilen hücreler (DISCOVERY'de birincil modda en yüksek z, n ≥ 100, aynı-bar < %0,5) ve POST kartları —
[selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/selected.json):

| Hipotez (mod) | seçilen hücre · geometri | DISC n / R / z | POST n | WR | ort R | bp | %95 GA (R) | P(EV>0) | yarılar | stres R | icra farkı | tek-poz R | plasebo % | BLIND R | yıl 24/25/26 | işlem/gün | Holm p | p_sel | kart | verdikt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OF01 taker dengesizliği uç (ters) | W1 θ3 · S2 r2 H15 | 11.139 / −0.042 / 0.86 | 12.499 | .489 | −0.037 | −1.53 | [−0.049, −0.025] | 0.00 | −0.038/−0.036 | −0.060 | 0.053 | −0.036 | 99.9 | −0.033 | −/−/− | 12.3 | 0.014 | 1.00 | 1/6 | RED |
| OF02 emilim fade | W15 θ3 · S1 r2 H15 | 163 / +0.042 / 1.61 | 438 | .454 | −0.066 | −0.88 | [−0.152, +0.022] | 0.07 | −0.067/−0.064 | −0.096 | 0.077 | −0.066 | 69.3 | −0.059 | −/−/− | 0.43 | 1.00 | 1.00 | 1/6 | RED |
| OF03 spot–perp ayrışması (spot'u izle) | W5 k3 · S2 r2 H30 | 3.650 / −0.028 / 1.52 | 4.629 | .452 | −0.055 | −2.04 | [−0.079, −0.030] | 0.00 | −0.059/−0.052 | −0.077 | 0.053 | −0.053 | 52.3 | −0.044 | −/−/− | 4.6 | 1.00 | 1.00 | 1/6 | RED |
| OF04a fiyat yeni uç, CVD teyitsiz (ters) | N30 g0 · S2 r1.5 H60 | 33.615 / −0.052 / 1.72 | 37.294 | .460 | −0.060 | −2.06 | [−0.067, −0.052] | 0.00 | −0.056/−0.063 | −0.087 | 0.066 | −0.059 | 64.8 | −0.063 | −/−/− | 36.8 | 1.00 | 1.00 | 1/6 | RED |
| OF04b CVD yeni uç, fiyat teyitsiz (CVD'yi izle) | N30 g0.5 · S1 r1.5 H60 | 3.825 / −0.057 / 2.02 | 7.579 | .428 | −0.093 | −2.23 | [−0.118, −0.068] | 0.00 | −0.091/−0.095 | −0.134 | 0.105 | −0.095 | 73.9 | −0.097 | −/−/− | 7.5 | 1.00 | 1.00 | 1/6 | RED |
| OF05 hacim patlaması (devam) | log-hacim W5 θ3 · S2 r1.5 H60 | 1.547 / +0.028 / 3.45 | 1.209 | .436 | −0.023 | −2.14 | [−0.082, +0.034] | 0.19 | −0.036/−0.010 | −0.040 | 0.049 | −0.010 | 91.0 | −0.012 | +/−/− | 1.2 | 0.69 | 0.245 | 1/6 | RED |
| OF06 çeyrek-saat (ters; kalibrasyon) | θ0 · S1 r1 H15 | 58.590 / −0.058 / 9.79 | 64.131 | .457 | −0.087 | −1.81 | [−0.093, −0.081] | 0.00 | −0.074/−0.100 | −0.130 | 0.097 | −0.087 | 100.0 | −0.099 | −/−/− | 63.2 | 0.006 | 0.01 | 1/6 | RED |

- Brüt (maliyetsiz) POST ortalamaları: OF01 +0,32 bp, OF02 +0,97, OF03 −0,19, OF04a −0,21, OF04b −0,38, OF05 −0,29, OF06 +0,04 bp;
  plaseboya göre brüt fazlalık −0,001…+0,019R. Ek ölçüt "brüt fazlalık ≥ 0,15R veya brüt ≥ 2×maliyet (3,7 bp)" hiçbirinde yok — aynı kaynak.
- Venue karşılaştırması (aynı hücreler, POST ort R): sabit 15 $ ≈ PEP'ten 0,001–0,005R kötü; Binance maker 4 bp −0,063 (OF05) … −0,187 (OF06);
  Binance taker 10 bp −0,173 … −0,467R — aynı kaynak.
- Aynı-bar oranları %0–0,03 (hepsi < %0,5); iyimser/sezgisel aynı-bar varyantları gerçekçiden ≤0,001R farklı → sonuç aynı-bar
  konvansiyonuna duyarsız. İcra farkının (0,05–0,10R) tamamı maliyet+kaymadan geliyor (E44) — aynı kaynak.
- Tüm 1.224 hücrenin POST kartı: ort R > 0 olan 30 hücre (15'i aynı küçük OF02_W15_th5 hücresinin geometrileri, n=57), kart ≥4/6 olan 10
  hücre (9'u OF02_W15_th5, n=57 < 150; biri OF02_W5_th5 n=171, +0,030R), 6/6 **0**. n ≥ 150 olan 1.044 hücrede en iyi POST ort R +0,030,
  en iyi plasebo-fazlalığı +0,091R, brüt ≥ 3,7 bp yalnız 1 hücre — [cards_all_post.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/cards_all_post.csv),
  [all_cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/all_cells.csv).
- Max-z seçim düzeltmesi (DISCOVERY, 1.224 hücre, 200 tam-gün dairesel kaydırma): gözlenen max z 9,79 (OF06); boş dağılım medyan 2,97,
  %95 4,44, %99 9,60 (tüm hücreler); n ≥ 30 hücrelerle %95 3,73. p_sel: OF06 0,01, OF05 0,245 (n≥30: 0,12), diğer beşi ≈1,0 —
  [maxz_null.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/maxz_null.json).
- Olay sayıları (DISC/OOS/BLIND): OF06 θ0 58.599/33.910/30.221; OF04a N30 g0 33.620/19.730/17.564; OF01 W1 θ3 11.141/6.790/5.709;
  OF05 θ5 hücreleri 2024+'da ~0 (log-hacim z ≥ 5 artık oluşmuyor) — [event_counts.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/event_counts.csv).

### Inferences
- Bu, literatürün öngördüğü tablo: akış–fiyat ilişkisi büyük ölçüde eşzamanlı, ileriye dönük kısım sub-bp. Vafin (2026) aynı-aralık
  mekanik bağ uyarısı — [SSRN 6938742](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6938742); çeyrek-saat makalesi "1 dk dengesizliğin
  öngörü ilişkisi çok zayıf" — [arXiv 2607.09426](https://arxiv.org/html/2607.09426v2). 1m karar + sonraki açılış girişi bu bilgiyi fiyata
  yansımış görüyor.
- OF01 ve OF06 "plaseboyu yeniyor" ama +0,01–0,02R fazlalık 1,85 bp'lik maliyetin (S1'de ≈0,10R) onda biri. İstatistiksel anlamlılık ≠ ekonomik kenar.
- OF05 (hacim patlaması devam) DISCOVERY'de kart 4/6, plasebo %99,9, +0,028R idi; POST'ta −0,023R'ye düştü (2024 +, 2025–26 −). Klasik
  dönem çürümesi; p_sel 0,245 zaten seçim yükünü işaret ediyordu.

### Gaps
- Pepperstone'un haber/oynaklık anlarındaki spread genişlemesi bilinmiyor; akış uçları tam da bu anlara yığılır → gerçek maliyet
  muhtemelen 1,85 bp'den yüksek (sonuç değişmez, daha kötüleşir).

---

## 3. A priori mod seçimi (devam mı dönüş mü) doğru muydu? (E49)

### Takeaway
Kısmen yanlıştı, ama fark etmez: DISCOVERY'deki en yüksek z'ler birincil değil **ikincil** modlardaydı (OF01 devam, OF04a fiyat-yönü,
OF03 perp'i izle) ve bunların hepsi POST'ta söndü ya da işaret değiştirdi. Mod seçimini ön kayıtta sabitlemek doğru karardı.

### Cited Findings
- OF01_W5_θ5 **devam**, S2 r1 H15: DISC n 2.003, +0,014R, fazlalık +0,062, z 3,63 → OOS −0,068 / BLIND −0,098R, POST z −1,85 (işaret döndü) —
  [all_cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/all_cells.csv).
- OF04a_N60_g0,5 fiyat-yönü (ayrışmaya rağmen kırılımı izle), S1 r1 H15: DISC fazlalık +0,053, z 4,10 → OOS +0,030 (z 2,17) → BLIND +0,002 (z 0,18); net R her segmentte negatif (−0,033/−0,064/−0,094).
- OF03_W15_k3 perp'i izle, S2 r2 H60: DISC +0,033R z 3,19 → OOS +0,027R z 2,40 → BLIND −0,037R z 0,73.
- OF06 ikincil mod (çeyrek-saat akışını izle) POST z −3,31: çeyrek-saat dönüş işareti tutarlı (aşağıda §5).

### Inferences
- "Aşırı taker alımı → kısa vadede devam" DISCOVERY'de (2021–23, yüksek oynaklık) hafif çalışıp 2024+'da tersine dönüyor; akış-modunun
  işareti rejime bağlı ve ölçek-küçük. Hangi mod seçilirse seçilsin net sonuç negatif.

### Gaps
- Mod işaretinin rejim bağımlılığını (oynaklık / ETF öncesi-sonrası) ayrıca modellemek bu ön kaydın dışında kaldı; kenar büyüklüğü
  (≤0,06R brüt fazlalık) maliyeti zaten karşılamadığı için öncelikli değil.

---

## 4. 1 s / büyük işlem özellikleri (6 ay, keşif) bilgi ekliyor mu?

### Takeaway
Hayır. Büyük-işlem (≥5 BTC aggTrade) net dengesizliği ve 1 s patlama net dengesizliği, aynı dönemdeki basit 1m delta sinyali gibi
plasebo düzeyinde; büyük-işlem sinyali olaylarda %98 oranında 1m delta ile aynı işaretli (gereksiz bilgi).

### Cited Findings
2026-04-20→10-20 (yalnız BLIND içinde), sabit geometri S1 r1 H30, seçim yok — [of07_explore_1s.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/of07_explore_1s.csv), [03_explore_1s.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/logs/03_explore_1s.log):

| hücre | mod | n | işlem/gün | ort R | bp | brüt bp | fazlalık R | P(EV>0) | plasebo % |
|---|---|---|---|---|---|---|---|---|---|
| OF07a büyük-işlem net z≥3 | devam | 1.973 | 10.7 | −0.097 | −1.98 | −0.13 | +0.007 | 0.00 | 67.2 |
| OF07a | ters | 1.973 | 10.7 | −0.115 | −2.68 | −0.83 | −0.009 | 0.00 | 31.6 |
| OF07b 1 s patlama net z≥3 | devam | 2.282 | 12.4 | −0.117 | −2.36 | −0.51 | −0.013 | 0.00 | 24.3 |
| OF07b | ters | 2.282 | 12.4 | −0.098 | −2.28 | −0.43 | +0.009 | 0.00 | 69.8 |
| OF07c kontrol: 1m delta z≥3 (OF01 W1 θ3) | ters | 2.069 | 11.2 | −0.091 | −2.20 | −0.35 | +0.014 | 0.00 | 77.7 |
| OF07d büyük-işlem ∧ ¬1m-delta-uç | devam | 1.079 | 5.9 | −0.100 | −2.10 | −0.25 | +0.003 | 0.00 | 53.6 |

- OF07a olaylarının %56,9'unda aynı dakika |z_D(1)| ≥ 3; büyük-işlem işareti ile 1m delta işareti olayların %98,2'sinde aynı.
- Bu dönemde SL medyanı 19 bp (S1 tabanı); plasebo ort. ≈ −0,105R.

### Inferences
- 6 aylık 1 s verisiyle ±0,01R'lik farklar ayırt edilemez (gereken n binlerce bağımsız işlem; not 03 §4: +0,05R için ~1.600); ama brüt
  bp'lerin hepsi ≤ 0 olduğundan büyük bir gizli kenar yok. "Whale print" fikri BTC perp'te dakika ufkunda 1m delta'nın ötesinde bilgi
  taşımıyor (bu örneklemde).

### Gaps
- Spot aggTrades işlenmedi (not 02); spot büyük işlemleri test edilmedi. 1 s yol, aynı-bar çözümü için kullanılmadı (aynı-bar oranları
  zaten ≤ %0,03).

---

## 5. Çeyrek-saat etkisi (arXiv 2607.09426) — kalibrasyon

### Takeaway
Simülatör bilinen sub-bp etkiyi buluyor: çeyreğin ilk dakikasındaki taker akışının tersine işlem, çeyrek-dışı kontrol dakikalarına göre
belirgin (2021–22 brüt fazlalık +1,2–1,4 bp, z 5–7), ama yıllar içinde sönüyor (2025 +0,12, 2026 +0,04 bp) ve hiçbir yıl maliyeti
karşılamıyor (net −0,9…−2,0 bp). Makalenin "~0,5 bp, taker ücretinin onda biri" tespitiyle tutarlı.

### Cited Findings
- Makale: Binance perp çeyrek-saat açılışında ~%26 fazla işlem; ilk-yarım-saat getirisi akışa göre negatif profilli; gerçekleşen tahmin hedefi
  sınır başına ~0,5 bp — [arXiv 2607.09426](https://arxiv.org/html/2607.09426v2) (not 01 üzerinden).
- Bizim ölçüm (S1 r1 H15, ters, yıl başına; brüt fazlalık = aynı yıl/saat plaseboya göre) — [posthoc_quarter_hour.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/posthoc_quarter_hour.csv):

| yıl | çeyrek dakikalar {00,15,30,45}: brüt bp / fazlalık bp / z / net bp | kontrol {07,22,37,52}: brüt / fazlalık / z |
|---|---|---|
| 2021 | +0.95 / +1.36 / 5.5 / −0.90 | −1.14 / −0.75 / −2.7 |
| 2022 | +0.87 / +1.20 / 7.3 / −0.99 | −0.48 / −0.15 / −0.8 |
| 2023 | +0.34 / +0.54 / 4.8 / −1.51 | −0.44 / −0.24 / −2.5 |
| 2024 | +0.39 / +0.67 / 4.6 / −1.46 | −0.70 / −0.42 / −2.9 |
| 2025 | −0.11 / +0.12 / 1.0 / −1.96 | −0.24 / −0.02 / −0.1 |
| 2026 | −0.19 / +0.04 / 0.3 / −2.04 | −0.19 / +0.04 / 0.3 |

- Ön-kayıtlı seçim (OF06 θ0 S1 r1 H15): Holm p 0,006, p_sel 0,01, plasebo %100 — ama POST net −0,087R, −1,81 bp; BLIND −0,099R — [selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/selected.json).

### Inferences
- Bu ailedeki **tek gerçek ve seçim-düzeltmesine dayanıklı etki** budur ve işlem edilemez: büyüklüğü maliyetin ~1/3–1/40'ı ve
  çürüyor (BTC-M07 turn-of-the-candle ile aynı desen). Kalibrasyon ✓: motor küçük gerçek etkileri öldürmüyor, maliyet öldürüyor.

### Gaps
- Makalenin 10 sn'lik açılış getirisi ve 4–12 saatlik ufku 1m/≤60 dk tasarımında sınanamadı (kapsam dışı, scalp değil).

---

## 6. Sonuç: en iyi aday(lar), defter satırları ve yeni yöntem tuzakları

### Takeaway
Emir akışı ailesinden **LIVE veya SHADOW aday yok**. Tek kayda değer yakın-aday (post-hoc, C): 15 dk emilim-fade'in en uç köşesi
(OF02 W15 θ≥5) — her segmentte pozitif ama 5,4 yılda 80 olay ve POST'a bakılarak bulundu; scalp stratejisi olarak hacmi yok.

### Cited Findings
- Post-hoc emilim platosu (fade, |z_r| ≤ 0,5) — [posthoc_absorption_plateau.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/posthoc_absorption_plateau.csv):
  W1 θ3–6 hepsi negatif (−0,05…−0,16R); W5 θ3–5 negatif/≈0, θ6 S2 r2 H60 +0,068 (n 107; OOS −0,234); W15 θ3 −0,066 / −0,003, θ4 −0,003 / +0,068,
  **θ5 S1 r1 H15: n 80, +0,176R, +9,4 bp, fazlalık +0,266R, z 3,1; DISC +0,196 (n 22) / OOS +0,266 (n 20) / BLIND +0,150 (n 37)**;
  aynı θ5 S2 r2 H60 +0,277R ama OOS −0,062; θ6 n 34.
- OF02_W15_θ5 S1 r1 H15 olayları: yıl 2021…2026 ort R +0,085/+0,067/+0,451/+0,098/+0,246/+0,152 (6/6 pozitif); BUY 47 (+0,140R), SELL 33
  (+0,228R); WR %62,5; en iyi 5 gün toplamın %49'u; en iyi 5 işlem hariç +0,123R; %94'ü hafta içi —
  [of02_W15_th5_events_S1_r1_H15.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/of02_W15_th5_events_S1_r1_H15.csv).
- Bu hücre ön kayıtta DISCOVERY n=22 < 100 olduğu için seçime giremedi; aynı hipotezin seçilen hücresi (W15 θ3, DISC fazlalık +0,125R)
  POST'ta +0,021 fazlalık / −0,066R net ile çöktü — [selected.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_orderflow/results/selected.json).

### Inferences

#### En iyi aday(lar)
- **Ön-kayıtlı geçen: yok.** 7 seçimin 7'si RED (kart 1/6; POST net −0,023…−0,093R).
- **Yakın aday (post-hoc, sınıf C) — "15 dk emilim fade'i":** karar dakikası t'de perp taker delta toplamı D_15 (son 15 dk) için 30 günlük
  geçmiş z-skoru |z_D(15)| ≥ 5 **ve** spot 15 dk log getirisinin 30g z-skoru |z_r(15)| ≤ 0,5 (akış var, fiyat gitmemiş); işlem akışın
  **tersine**, giriş t+1 açılışı; SL = max(19 bp, 1,1×ATR5m), TP = 1×SL, 15 dk zaman stopu; 30 dk epizod bastırma; rollover'dan 2 dk önce kapat.
  Neden geçmiyor: (i) n = 80 / 5,4 yıl (~15/yıl) → kart n ≥ 150'ye ~10 yılda ulaşır; (ii) POST'a bakarak bulundu (1.224 hücrelik tarama,
  seçim yükü düzeltilmedi); (iii) plato dar (θ4'te ≈0, W5/W1'de negatif); (iv) en iyi 5 gün toplamın yarısı. Yapılacaksa: **yeni ön kayıtla
  yalnız ileri gölge** (θ=5, W=15, S1 r1 H15 dondurulmuş), ≥30 bağımsız olay sonra oku; mekanizma hipotezi = limit-emir duvarının agresif
  akışı emmesi (pasif büyük katılımcı) sonrası geri dönüş.
- **Ekonomik olmayan gerçek etkiler (strateji değil, bağlam):** çeyrek-saat akış dönüşü (OF06; 2021–24 brüt +0,5–1,4 bp, 2025+ ≈0) ve
  1m taker uç dönüşü (OF01; plasebo yüzdeliği %99,9, fazlalık +0,017R). İkisi de maliyetin altında.

#### Defter satırı taslağı (§2.11'e, §6 biçimi)
| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-SC-OF01 | 2026-10-22 | **Perp taker dengesizliği ucu** (D_W = W dk delta toplamı, 30g geçmiş z; \|z\| ≥ θ; W 1/5/15, θ 3/5; a priori TERS, ikincil DEVAM); S1/S2 ATR5m braket × TP/SL 1/1,5/2 × 15/30/60 dk; giriş t+1 açılışı, PEP 1,85 bp, rollover−2 dk kapanış. Ön kayıt `research/btc_scalp_20261021/fam_orderflow/prereg.md` | Seçim W1 θ3 S2 r2 H15 (DISC z 0,86) → POST n 12.499, −0,037R (−1,53 bp), GA [−0,049, −0,025], plasebo %99,9 (fazlalık +0,017R), Holm 0,014, p_sel 1,0, kart 1/6. İkincil DEVAM W5 θ5 DISC z 3,63 → POST z −1,85 (E49). Kanıt `fam_orderflow/results/selected.json`, `all_cells.csv` | X |
| BTC-SC-OF02 | 2026-10-22 | **Emilim fade** (\|z_D(W)\| ≥ θ ∧ \|z_r(W)\| ≤ 0,5 → akışın tersi; W 1/5/15, θ 3/5) | Seçim W15 θ3 S1 r2 H15: DISC +0,042R (n 163) → POST n 438, −0,066R, P %7, plasebo %69, BLIND −0,059 → RED. **Post-hoc köşe W15 θ5** (DISC n 22, seçime giremedi): S1 r1 H15 n 80 +0,176R/+9,4 bp, DISC/OOS/BLIND +0,20/+0,27/+0,15, 6/6 yıl +, en iyi 5 gün %49; θ4 ≈0, W1/W5 negatif. Kanıt `posthoc_absorption_plateau.csv`, `of02_W15_th5_events_S1_r1_H15.csv` | X (ön-kayıtlı) / C (θ5 köşesi, yalnız yeni ön kayıtla ileri gölge) |
| BTC-SC-OF03 | 2026-10-22 | **Spot–perp taker akış ayrışması** (Δ = z_Dspot(W) − z_Dperp(W), \|Δ\| ≥ k; W 5/15, k 3/4; a priori SPOT'u izle) | Seçim W5 k3 S2 r2 H30 → POST n 4.629, −0,055R, plasebo %52, BLIND −0,044. İkincil (perp'i izle) W15 k3 DISC z 3,19 → OOS z 2,40 → BLIND −0,037R. Kanıt `selected.json`, `all_cells.csv` | X |
| BTC-SC-OF04 | 2026-10-22 | **CVD–fiyat ayrışması** (a: perp kapanış N-bar yeni uç ∧ CVD önceki N max'ın g·σ altında → ters; b: CVD yeni N uç ∧ fiyat g·σ geride → CVD yönü; N 30/60) | a: N30 g0 S2 r1.5 H60 POST n 37.294 −0,060R, plasebo %65; b: N30 g0,5 S1 r1.5 H60 POST n 7.579 −0,093R, plasebo %74; p_sel ≈1. İkincil "ayrışmaya rağmen kırılımı izle" DISC z 4,10 → BLIND z 0,18. Pratisyen "delta divergence" iddiası BTC 1m'de desteklenmiyor. Kanıt `selected.json`, `all_cells.csv` | X |
| BTC-SC-OF05 | 2026-10-22 | **Hacim / işlem-sayısı patlaması** (log hacim veya işlem sayısı W 1/5 dk, 30g z ≥ θ 3/5; yön = W-bar yönü; a priori DEVAM) | Seçim log-hacim W5 θ3 S2 r1.5 H60: DISC +0,028R, plasebo %99,9, kart 4/6 → POST n 1.209 −0,023R, P %19, BLIND −0,012, yıl 2024 + / 2025–26 −; p_sel 0,245. θ5 hücreleri 2024+'da ~0 olay. Kanıt `selected.json`, `event_counts.csv` | X |
| BTC-SC-OF06 | 2026-10-22 | **Çeyrek-saat akış dönüşü** (arXiv 2607.09426 kalibrasyonu: :00/:15/:30/:45 dakikası delta işaretinin tersi) | DISC z 9,79 (ailenin max'ı, p_sel 0,01), POST Holm 0,006, plasebo %100 — ama net −0,087R/−1,81 bp. Brüt fazlalık yıl yıl +1,36/+1,20/+0,54/+0,67/+0,12/+0,04 bp; çeyrek-dışı kontrol ≈0/negatif → etki çeyreğe özgü, gerçek, çürüyen, maliyetin altında (BTC-M07 deseni). Kanıt `posthoc_quarter_hour.csv` | X (strateji) / A (olgu, sub-bp) |
| BTC-SC-OF07 | 2026-10-22 | **Büyük işlem (≥5 BTC aggTrade) / 1 s patlama net dengesizliği** (7g z ≥ 3, 2026-04-20→10-20, sabit S1 r1 H30, iki mod; keşif) | Tüm hücreler plasebo düzeyinde (−0,091…−0,117R, brüt −0,83…+0,01 bp, plasebo %24–78); büyük-işlem işareti olayların %98'inde 1m delta ile aynı; 1m delta'dan bağımsız kısım (OF07d) +0,003 fazlalık. Kanıt `of07_explore_1s.csv` | X (keşif, 6 ay) |

#### Yeni yöntem tuzakları (E51… önerisi)
- **E51 — Büyük n'de "plaseboyu yeniyor" ≠ kenar.** n = 10⁴–10⁵ olayda +0,01–0,02R'lik (sub-bp) brüt fazlalık plasebo yüzdeliği %99,9–100,
  Holm p < 0,05 ve hatta seçim-düzeltmeli p_sel 0,01 verir (OF06, OF01), oysa net −0,04…−0,09R. Önlem: kartın plasebo/Holm/max-z ölçütlerini
  **brüt fazlalık ≥ maliyet/SL + tampon** ön-filtresiyle birlikte zorunlu kıl; z'yi değil fazlalığın bp büyüklüğünü raporla (E44'ün istatistik yüzü).
- **E52 — Max-z boşunun kuyruğunu küçük-n hücreler belirler.** 1.224 hücrelik ailede boş max-z'nin %99'u 9,6 (tüm hücreler) vs 4,0 (n ≥ 30):
  n = 8–37 olaylı hücreler kaydırmalarda aşırı z üretir. Ön kayıtta max-z'ye girecek hücreler için **asgari n** yaz (yoksa düzeltme fiilen geçilemez,
  ya da tersine, n ölçütü yazılmazsa keyfi seçilir).
- **E53 — Ön-kayıtlı asgari-n kuralı hücreyi dışarıda bırakınca, aynı hücreyi POST tablosundan "keşfetmek" seçimi POST'a taşır.** OF02 W15 θ5
  (DISC n 22) üç segmentte de pozitif görünüyor ama 1.224 POST hücresi tarandıktan sonra bulundu; bu hâliyle OOS/BLIND artık bağımsız
  doğrulama değil. Önlem: böyle köşeler yalnız **yeni ön kayıt + ileri veri** ile açılır; defterde "post-hoc, C" etiketi zorunlu (E12/E40 akrabası).
- **E54 — Sabit bp SL tabanı ATR ölçeklemesini sessizce kapatır.** S1 = max(19 bp, 1,1×ATR5m) 2024+'da medyan tam 19,0 bp (ATR5m ≈ 12–13 bp);
  "ATR-ölçekli braket" fiilen sabit bp braket olur ve yıllar arası oynaklık uyarlaması kaybolur. Önlem: tabana yapışan işlem payını raporla; yıl
  karşılaştırmasında bp ve R'yi birlikte oku (E50 ile birlikte).

### Gaps
- Evrim Paneli oturum notu ve backlog (1. KURAL) ile `docs/KAPI_KAYIT_DEFTERI.md` satır ekleme bu görevin yazma kısıtı nedeniyle yapılmadı;
  yukarıdaki taslak satırlar koordinatör tarafından eklenmeli. Backlog önerisi: "OF02 W15 θ5 emilim-fade — yeni ön kayıt + ileri gölge
  (≥30 bağımsız olay)" (experiment, low).
- Akış verisi Binance'e ait; Pepperstone CFD'nin kendi akışı yok. Sinyal Binance'ten, icra CFD'de varsayıldı; besleme farkı ve haber anı
  spread genişlemesi modellenmedi (tümü sonucu kötüleştirir).
- bookDepth (defter dengesizliği) ve metrics (OI, L/S) bu ailenin kapsamı dışında bırakıldı (paralel aileler).
