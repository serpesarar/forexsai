# NAS100 Mum Dizisi Atlası — tekrar eden mum dizileri (2026-10-02)

**Soru (kullanıcı):** NASDAQ 1m/5m/15m/30m grafiklerinde ~100 mumluk alanları tara;
her mumun belirli bir % sapma payı (ör. %0,01 / %0,05 / %0,07) içinde kaldığı,
birbirine en çok benzeyen modelleri bul, isimlendir, hangi zaman diliminde kaç kez
tekrarlandığını söyle. Örnek: MT5 ekran görüntüsündeki NAS100 M15 alanı
(sunucu 16 Eyl 03:00 → 17 Eyl 04:45, FOMC günü: yükseliş → flaş çöküş → V dönüş).

**Kullanıcı düzeltmesi (aynı gün):** 100 mumun tamamı benzemek zorunda değil.
100 mumluk alan içinden **herhangi sayıda ardışık mum** model olabilir; benzerlik
**her mumun boyu** (gövde + fitiller) üzerinden ±pay ile ölçülür.

## Sonuç (tek paragraf)

Kullanıcının örneği (100 mumluk M15 alanı ve 20 mumluk flaş çöküş + V çekirdeği) hiçbir zaman diliminde mum mum tekrar etmiyor; en benzer geçmiş alanlar plasebo serisinin verdiği kadar benzer (M15 %0,05: 40/100 vs plasebo 41/100). Genel taramada mum mum eşleşen en uzun tekrar 6–9 mum; kısa diziler (3–5 mum) çok tekrar ediyor ama 4 TF × 18 pay ızgarasında gerçek/plasebo oranının medyanı 1,0. Tekrarlardan sonraki 10 mumun yönü tabandan ayrışmıyor. Sonuç: NASDAQ'ta birebir tekrar eden mum dizisi, mum boyu dağılımından kendiliğinden doğan tesadüf düzeyinde; araç yine de her model için en yakın geçmiş anları tarihleriyle listeliyor.

## Veri

| TF | Kaynak | Aralık | Mum |
|---|---|---|---|
| 1m | Dukascopy US100 (2025) + Pepperstone (2026) | 2025-01-02 → 2026-10-02 | 533.627 |
| 5m | 1m'den türetildi | 2025-01-02 → 2026-10-02 | 106.809 |
| 15m | Pepperstone NAS100 | 2023-10-02 → 2026-10-02 | 70.863 |
| 30m | Pepperstone NAS100 | 2023-10-02 → 2026-10-02 | 35.441 |

- MT5 kutusu 1 dakikalığı yalnız ~100 gün tutuyor (bkz. `nasdaq_tam_veri_2026-08-29/OKUBENI.md`);
  Dukascopy veri sunucusu (`datafeed.dukascopy.com`) 2026-10-02'de bu ağdan zaman aşımına düştü
  (Google açılıyor) → M1/M5 3 yıla tamamlanamadı, ~21 ay. Boşluklar: 2025-08-22→27, 2026-01-01→02-10.
- M15/M30 broker verisinin 2026-07-15 öncesi broker saatinden (NY+7) UTC'ye çevrilmiş hâli
  `ndx_gate_forge/data/long_*_utc.parquet`'ten; sonrası Supabase `candle_cache`'ten taze.
- `candle_cache` 15m'de günlük arada (NY 17:00–18:00) bir önceki saatin **kopya barları** var
  (2026-09-16 21:00–21:45 UTC = 20:00–20:45'in birebir aynısı) → `build_bars.py` atıyor.
- Kaynak tutarlılığı: M1'den türetilen 15m ile broker 15m getiri korelasyonu 0,996 (2025) / 0,999 (2026).
- Şablon penceresi veride birebir doğrulandı: son bar 29150.5/29153.7/29114.2/29125.7 = ekran görüntüsü başlığı.

## Yöntem

- **Mum özellikleri** (açılışa göre %): tepe, dip, kapanış. İki mum benzer ⇔ üç farkın da |·| ≤ pay.
- **Model** = ardışık k mum (k ∈ 3…100). **Tekrar** = başka yerde k mumun HER BİRİ eşleşiyor;
  tekrarlar çakışmasız sayılır (aynı yerin kaydırması ayrı tekrar değil).
- **Pay sınırı:** pay ≤ dizideki mumların medyan boyunun 1/3'ü. Yoksa sessiz saatlerin minik
  mumları her şeyle eşleşir ve "en çok tekrar eden" düz diziler olur.
- **Hesap:** tüm mum çiftleri için köşegen koşu uzunluğu (n²/2 hücre, numba) → her başlangıç ve
  k için eşleşme sayısı → kesin çakışmasız örnek listesiyle tembel-açgözlü (CELF) motif seçimi.
- **Plasebo:** her mum %50 olasılıkla aynalanır (yeşil↔kırmızı, üst↔alt fitil): boylar aynı, yön
  dizilimi rastgele. Gerçek sayı plaseboyu belirgin geçmiyorsa model tesadüf geometrisidir.
- **Şablon araması:** (a) mum mum mutlak % (şablonun kendi TF'i), (b) mum mum ölçeksiz
  (boylar son 20 mumun ort. aralığına bölünür → tüm TF'ler), (c) çizgi benzerliği (kapanış rotası,
  serbest ölçek 0,1–10×, mumların %90'ı şablon yüksekliğinin %10/15/20 bandında). Şablonun kendisi
  ve kaydırmaları hem gerçek hem plasebo seride dışlanır.

## Bulgular

### 1. Kullanıcı örneği (şablon)

| Şablon | Ölçüm | Sonuç | Plasebo |
|---|---|---|---|
| 100 mumluk alan (M15) | mum mum %0,02 / 0,05 / 0,10 | tam 0 · en iyi 13 / 40 / 76 mum | 13 / 41 / 76 |
| 100 mumluk alan | ölçeksiz ×0,20, M1/M5/M15/M30 | tam 0 · en iyi 17 / 17 / 17 / 15 | 18 / 16 / 16 / 15 |
| 100 mumluk alan | çizgi %20 bant, M1/M5/M15/M30 | 136 / 25 / 14 / 6 | 139 / 25 / 21 / 5 |
| Flaş-V çekirdeği (20 mum, M15) | mum mum %0,05 / 0,07 | tam 0 · en iyi 9 / 12 | 8 / 10 |
| Flaş-V çekirdeği | çizgi %20 bant, M1/M5/M15/M30 | 73 / 38 / 30 / 20 | 100 / 32 / 39 / 18 |

Çizgi %10–15 bantta (şablon yüksekliğinin) eşleşme yok denecek kadar az (0–5). Flaş-V şekli M1/M15'te
plasebodan bile SEYREK. Olası açıklama (test edilmedi): gerçek piyasada büyük mumlar aynı yönde kümeleniyor,
işaret-karıştırılmış seride ise büyük mumlar rastgele yönle zikzak/V üretiyor.

### 2. Genel tarama — en çok tekrar eden dizi (gerçek / plasebo)

| TF | pay | 3 mum | 4 | 5 | 6 | 8 | en uzun |
|---|---|---|---|---|---|---|---|
| 30m | %0,03 | 38/36 | 8/10 | 4/4 | 2/2 | 0/0 | 7 |
| 30m | %0,05 | 46/40 | 10/10 | 4/4 | 2/3 | 0/0 | 7 |
| 30m | %0,07 | 51/39 | 9/10 | 5/4 | 2/2 | 0/0 | 6 |
| 30m | %0,1 | 33/29 | 7/8 | 3/3 | 2/2 | 0/0 | 6 |
| 15m | %0,02 | 68/73 | 15/16 | 5/4 | 3/2 | 0/0 | 7 |
| 15m | %0,03 | 92/102 | 17/21 | 9/6 | 3/3 | 2/2 | 8 |
| 15m | %0,05 | 72/70 | 13/14 | 5/5 | 3/3 | 2/2 | 8 |
| 15m | %0,07 | 60/59 | 13/12 | 5/5 | 3/2 | 0/2 | 6 |
| 5m | %0,01 | 73/76 | 18/18 | 6/5 | 4/3 | 2/0 | 8 |
| 5m | %0,015 | 122/114 | 22/21 | 7/6 | 3/3 | 2/2 | 8 |
| 5m | %0,02 | 142/128 | 27/28 | 11/8 | 4/4 | 2/2 | 8 |
| 5m | %0,03 | 118/113 | 20/20 | 7/7 | 4/3 | 2/2 | 8 |
| 5m | %0,05 | 68/75 | 14/15 | 5/5 | 3/3 | 2/0 | 8 |
| 1m | %0,005 | 365/324 | 59/50 | 12/10 | 5/5 | 2/2 | 9 |
| 1m | %0,0075 | 531/467 | 91/68 | 17/19 | 6/7 | 3/2 | 8 |
| 1m | %0,01 | 523/498 | 82/75 | 17/15 | 6/5 | 2/2 | 8 |
| 1m | %0,015 | 388/379 | 62/64 | 13/17 | 6/6 | 2/2 | 8 |
| 1m | %0,02 | 278/297 | 51/46 | 11/11 | 5/5 | 3/2 | 8 |

Örnek adlar: M15 %0,05 en sık 3 mumluk = Sabah Yıldızı (72, plasebo 70); M1 %0,01 = Sabah Yıldızı (523/498);
M30 %0,07 = üç yeşil mum (51/39); M15 %0,05 5 mum = V-Dip Dönüşü (5/5). Tek 9 mumluk tekrar: M1 %0,005,
2025-01-30 04:39 ↔ 2025-02-18 11:31 (sunucu saati).

### 3. Tekrar sonrası yön (bilgi)

n ≥ 30 olan 67 motifte sonraki 10 mum yükselme oranı − taban: ortalama ≈ 0 puan (TF bazında −0,6 / −0,4 / +1,0 / −0,4),
mutlak ortalama 3–8 puan (örneklem gürültüsü düzeyi). Çoklu karşılaştırma düzeltmesi yapılmadan bile hiçbir
motif belirgin değil → işlem kuralı adayı YOK (2. Kural: canlıya alma kartı olmadan kullanılmaz).

### 4. Yöntem notları / tuzaklar

- İlk deneme (100 mumun tamamının kapanış yolunu eşleştirme) kullanıcı düzeltmesiyle bırakıldı; orada da
  en çok tekrar eden "model" kararlı yükseliş/düşüş kanallarıydı ve sayılar plasebo düzeyindeydi (M30 %15 bant: 40 vs 33).
- Şablon aramasında plasebo serisi şablonun KENDİ konumunu da içerir (aynalanmamış yarısı kendini eşler) →
  öz-dışlama gerçek ve plasebo seride birlikte yapılmalı. İlk koşuda bu atlanınca plasebo yapay 58/100 çıktı.


### 5. Genişletilmiş tarama (kullanıcı: "farklı mum sayıları ve sapma oranlarında daha fazla örnek")

- Birebir mod: pay ızgarası genişletildi (M5 +%0,07, M15 +%0,10/0,15, M30 +%0,15/0,20); hücre başına 6 model
  (M1 birebir 3 — eski koşu yeniden kullanıldı).
- **Kısmi mod** (`diag_counts_partial`): k ∈ {10,15,20,30,50,75,100}, mumların ≥ %90/%80/%70'i pay içinde,
  ilk mum tutmalı, pay ≤ medyan mum boyunun 2/3'ü. Paylar: M1 %0,01/0,02 · M5 %0,02/0,03/0,05 ·
  M15 %0,03/0,05/0,07 · M30 %0,05/0,07/0,10.

| mod | en uzun tekrar eden dizi | gerçek/plasebo medyan (TF'ler) |
|---|---|---|
| birebir | 8–9 mum | 1,00 / 1,00 / 1,00 / 1,02 |
| %90 | 20 mum | 1,00–1,08 |
| %80 | 30 mum | 0,96–1,00 |
| %70 | 50 mum (M1'de iki ayrı 75 mumluk dizi 2'şer kez, plasebo 0; 100 hiç yok) | 1,00–1,13 |

**M1 kısmi (%0,01; 2026-10-04 tamamlandı, 71 model):** %90 → en uzun 20 mum (4×, plasebo 5), %80 → 30 mum (4×/4), %70 → **iki ayrı 75 mumluk dizi 2'şer kez (plasebo 0)**: "Testere – Yukarı Kapanış" 2025-06-05 02:57 ↔ 2025-07-21 19:42, "Düşüş – Tepki – Zayıflama" 2025-08-15 10:05 ↔ 2025-12-22 21:32; 50 mum 8× (6). 100 mum hiçbir modda yok. 30+ mumluk tekrarların %46'sı Asya, %38'i Avrupa seansında. n ≥ 30 olan 41 motifte ileri yön farkı ≈ 0. %0,02 payı denenmedi (önceki koşular Mac uykusunda zaman aşımına düşmüştü).

Örnekler: M5 %0,03 %70 30 mum "Yükseliş + Sınırlı Geri Çekilme" 50× (plasebo en iyi 49); M15 %0,05 %80 15 mum 63×
(plasebo 72); M15 %0,05 %70 50 mum "Düşüş + Zayıf Tepki" 3× (2); M30 %0,07 %80 30 mum "V-Dip Dönüşü" 3× (0).
19 şekil ailesi; en kalabalık: Kararlı Yükseliş, Yatay Bant/Testere, V-Dip Dönüşü, Boğa Bayrağı.

**Uzun tekrarlar sakin seansın ürünü:** 30+ mumluk kısmi tekrarların M15'te %69'u, M30'da %63'ü Asya seansında
(sunucu 01–09) başlıyor; M5'te %40. Küçük, birbirine benzeyen mumlar kısmi eşleşmeyi kolaylaştırıyor.

**Tekrar sonrası yön:** n ≥ 30 olan motiflerde sonraki 10 mum yükselme oranı − taban, mod/TF grup ortalamaları
±2 puan (yalnız 2 motifli bir grupta −7). Kenar yok.

### 6. Kısmi mod pay taraması %0,02 → %0,10 (kullanıcı: "sırayla tek tek koş", tüm TF'ler)

Çekirdek değişikliği: uygunluk (pay ≤ medyan mum boyu × 2/3) sayımın İÇİNE alındı (`diag_counts_partial(..., E, ...)`)
— geniş payda mumların çoğu eşleştiği için gereksiz çiftler sayılıyordu. M30 %0,07 kontrolü: her hücrede ilk motif ve
plasebo sayısı eski koşuyla aynı; 3.–6. sıradaki birkaç motifin sayısı aday sıralaması değiştiği için ±1–9 oynadı.
M1 %0,01 eski çekirdekle kaldı. Pay başına süre M1 ~2–15 dk (%0,02 en yavaş), diğerleri < 1 dk.

| TF | %90 en uzun | %80 en uzun | %70 en uzun | gerçek/plasebo medyan |
|---|---|---|---|---|
| M1 | 30 | 50 | 75 | 1,00 / 1,00 / 1,01 |
| M5 | 20 | 30 | 75 | 1,00 |
| M15 | 20 | 30 | 75 | 1,00 |
| M30 | 20 | 30 | 50 | 1,00–1,03 |

- 2.907 model (birebir + kısmi), 523 tekrarlı hücre, medyan oran 1,0; ≥1,5× olan 21 hücre (%4), hepsi 2–5 tekrar.
- 75 mum örnekleri: M1 %0,03 "Ters-V Tepe Dönüşü" 3× (plasebo 0) 2025-11-25 19:06 / 2026-07-01 20:06 / 2026-08-13 16:57;
  M5 %0,09–0,10 2× (0); M15 %0,08 "Yatay Bant" 2× (0) 2024-03-18 17:00 / 2025-03-14 19:30.
- 30+ mumluk tekrarların seansı payı izliyor: M15 %51 / M30 %59 Asya, M1 %65 ABD (geniş payda yalnız büyük
  mumlar uygun → ABD seansı). Önceki "M15 %69 Asya" sayısı dar paylardandı.
- n ≥ 30 olan 1.063 motifte ileri 10 mum yön farkı TF ortalaması 0 ile −1,5 puan.

## Dosyalar

- `build_bars.py` — 4 TF bar seti (`data/bars_<tf>.parquet`, gitignore'da)
- `seq_engine.py` — mum-mum motif motoru (numba); `naming.py` — mum/şekil adlandırma
- `run_seq.py` — tarama + şablon araması → `results/seq_scan.json`, `results/seq_templates.json`
- `shape_template.py` — çizgi düzeyinde şablon araması → `results/shape_templates.json`
- `engine.py` — çizgi eşleştirme yardımcıları
- `export_page.py` + `atlas_template.html` + `results/page_text.json` — HTML atlas üretimi
  (`python3 export_page.py atlas_template.html <çıktı.html> results/page_text.json`); çıktı klasörüne
  `data_<tf>.json` dosyaları da yazılır — artifact'a `files` ile birlikte yayınlanmalı (sayfa onları tembel yükler)
- Yayın: https://claude.ai/artifact/QrW5Bbwf8fDtkpwJaAwPKL

**Yeni bir model aramak** (ör. kullanıcının daire içine aldığı bölge), saatler MT5 sunucu saati:

```bash
python3 research/ndx_pattern_motifs/run_seq.py --no-discover --out seq_templates.json \
  --template 15m "2026-09-16 21:00" "2026-09-17 02:45" "Daire içindeki model"
python3 research/ndx_pattern_motifs/shape_template.py \
  --template 15m "2026-09-16 21:00" "2026-09-17 02:45" "Daire içindeki model"
```
