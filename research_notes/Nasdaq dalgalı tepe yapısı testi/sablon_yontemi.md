# Nasdaq "dalgalı tepe aralığı" — şablon (şekil) eşleştirme yöntemi (ME-09)

Kapsam: kullanıcının 3 işaretli NAS100 1h bölgesi (T1 2026-07-06→07-21, T2 07-17→07-29, T3 08-13→08-20; görsel 6 ve 7) şablon
alınarak ME-08'deki ölçeksiz + süre-esnek şekil ölçüsüyle (64 nokta, z-normalize, Öklid; min şablon × pencere) 10 yıllık NDX
CFD 1h'te arandı; ön-kayıtlı, sızıntısız ileri getiri testi + olay düzeyi + plasebo + DAX. Bu hesaplamalı bir çalışmadır; tüm
"kaynaklar" yerel dosyalardır (betik ve çıktılar `research/benzerlik_tepe_20261019/sablon/`). Web kaynağı kullanılmadı.

## Üç şablon bu ölçüyle birbirine benziyor mu?

### Takeaway
Çoğunlukla hayır: yalnız T2–T3 sınırda benzer (r 0,87, dağılımın %2,8 diliminde); T1–T2 (r 0,68, %7–18) ve T1–T3 (r 0,44,
%24–32) benzer değil, ve tablo şablon sınırları birkaç saat/gün kayınca yer değiştiriyor. Dedektör T1 ve T3'ü kendi bitişlerinde
bile %2 eşikte tanımıyor (yalnız T2'yi tanıyor).

### Cited Findings
- Şablon sınırları kullanıcının günleri, UTC gün sınırıyla: T1 276 bar (14 işlem günü), T2 207 bar (11), T3 138 bar (7); pencere
  uzunlukları medyan 207'nin 0,8/1,0/1,2 katı = 166/207/248 bar; ön-kayıtta yazıldı — [PROTOCOL.md](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/PROTOCOL.md)
- Benzerlik eşiği (geliştirme dönemi gün-sonu D'lerinin %2 dilimi) D = 3,63 ≙ şekil korelasyonu r ≥ 0,897; %5 dilim D = 4,14 ≙
  r ≥ 0,866 (z-normalize vektörlerde d² = 128·(1 − r)) — [sablon_dogrulama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sablon_dogrulama.json)
- Çiftler (tam aralık, 64 nokta): T2–T3 r 0,871, şablon başına D dağılımında %2,76 / %2,84 dilim (tüm pencerelerde %1,19);
  T1–T2 r 0,680, %7,25 / %17,95; T1–T3 r 0,444, %24,27 / %31,69 — [sablon_dogrulama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sablon_dogrulama.json)
- Dedektör tarzı (her şablonun son barında, kendisi hariç diğer iki şablonla, L ∈ {166, 207, 248}): T1 %16,97, T2 %2,89, T3 %11,24
  dilim — [sablon_dogrulama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sablon_dogrulama.json)
- Kendini tanıma (f = 1, kendi bitişindeki 20:00 sorgusu, üç şablonun hepsiyle): T2 D 1,90 (dilim %0, benzer); T1 D 5,61 (dilim
  %16,1, en yakın T3) ve T3 D 5,69 (dilim %16,6, en yakın T2) %2 eşikte benzer DEĞİL — [ek_tanilama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/ek_tanilama.json)
- Görsellerden ölçülen alternatif sınırlarla (T1 07-07 07:00→07-21 15:00, T2 07-16 12:00→07-29, T3 08-11 08:00→08-20 06:00)
  çiftler: T1–T3 r 0,777 (%1,9 / %3,3), T1–T2 0,670, T2–T3 0,587 (%21 / %15) — [sablon_dogrulama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sablon_dogrulama.json)
- Farklar (T1/T2/T3): aralık %5,8/%7,9/%3,9 (önceki 20 günün ortalama gün aralığının 2,6/3,9/2,0 katı); net −%1,9/−%5,2/−%1,8;
  %1 zigzag bacağı 10/17/2 (%0,5'te 24/32/8); 1h oynaklık 25/38/20 bp; en düşük nokta konumu 0,80/0,99/0,97; tepe önceki 20 gün
  zirvesine göre −%2,7/−%4,9/+%1,0 — [sablon_dogrulama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sablon_dogrulama.json), şekil grafiği [sablon_sekilleri.png](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sablon_sekilleri.png)

### Inferences
- Kullanıcının "aynı yapı" dediği şey nitel bir ortaklık (tepe yakınında oynaklık + sonda düşüş); ortak bir yol şekli değil. Süre
  2 kat, bacak sayısı 2–17 arasında değişiyor; z-normalize Öklid bu farklara (özellikle salınımların zamanlamasına) duyarlı.
- Pencere ızgarası (166–248) T1 (276) ve T3'ü (138) kapsamıyor; birleşik min-D dedektörü pratikte T2/T3 dedektörü.

### Gaps
- Kullanıcının kendi etiketleri henüz yok; ölçünün onun gözünü yakalayıp yakalamadığı bilinmiyor.
- Şablon başına kendi uzunluğunun 0,8–1,2 katı pencereler (T1/T3'ü kapsayacak tanım) bu turda ön-kayıtlı değildi, sınanmadı.

## En benzer 12 bölge (etiketleme görseli, sonrası gösterilmeden)

### Takeaway
Görsel hazır; 12 eşleşmenin hepsi T2 veya T3'e en yakın (r 0,93–0,97), T1'e en yakın olan yok; çoğu "yükseliş/düzlük → dipte biten düşüş".

### Cited Findings
- Görsel (3 şablon ilk satırda, 12 eşleşme 4 saatlik mumlarla, yalnız pencere) — [tur1_etiketleme.png](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/tur1_etiketleme.png)
- Liste: #1 2021-09-22→10-01 (T3, r 0,967), #2 2024-08-28→09-09 (T3), #3 2021-09-02→09-15 (T2), #4 2020-08-28→09-09 (T3),
  #5 2022-10-03→10-12 (T3), #6 2018-12-07→12-24 (T2), #7 2022-04-29→05-12 (T3), #8 2022-04-18→04-27 (T3), #9 2020-02-14→02-28 (T2),
  #10 2020-02-28→03-12 (T3), #11 2023-12-26→2024-01-05 (T2), #12 2018-06-19→06-28 (T3, r 0,929) — [tur1_secilenler.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/tur1_secilenler.csv)

### Inferences
- Etiketleme, ölçünün "dalgalı tepe" yerine "oynak düşüş" bulduğunu doğrulayabilir/çürütebilir; T1 tipi (V dip + iki eşit tepe + toparlanma) görselde temsil edilmiyor.

### Gaps
- Aday tarama her 2 saatte bir biten pencerelerle yapıldı (testteki günde-bir sorgudan daha ince) — yalnız görsel için.

## Ön-kayıtlı sonuç testi (NDX geliştirme 2016-06 → 2025-11): kısmi ve tam eşleşmeden sonra fiyat

### Takeaway
Ön-kayıtlı yönde (aşağı, "tepe → düşüş sürer") 15 hücrenin 0'ı geçti; en yakını 1/2 aşama +5 gün −63 bp (P↓ 0,974, eşik 0,975)
ama eşik/sınır/DAX değişince dağılıyor. Ters yönde (kısa vadeli yukarı) 3 hücre tek-hücre ölçütlerini sağladı ama Bonferroni'yi
geçmedi ve sonradan tanılamada (DAX ters, %5 eşik, alternatif sınır, aile plasebosu p ≈ 0,16–0,20) dağıldı → kenar yok.

### Cited Findings
- Hücre başına 48 benzer gün, 28–41 bağımsız olay (aralık ≤ 10 sorgu günü = aynı olay); kıyas = getiri ondalığı × oynaklık ondalığı
  eşli benzer-olmayan günler — [hucreler_ndx.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/hucreler_ndx.csv)
- Fark (benzer − eşli taban, bp; ay-blok P(fark<0)): 1/3 aşama +1s +6,5 (0,004), +1g +33,6 (0,002), +5g −21,4 (0,72), kalan +4,7
  (0,44); 1/2 aşama +1s +4,2 (0,06), +1g −18,7 (0,87), +5g −63,2 (0,974), kalan −54,0 (0,96); 2/3 aşama +1s −5,5 (0,85), +1g +17,0
  (0,15), +5g −19,5 (0,58), kalan −22,9 (0,63); tam +1s +14,3 (0,018), +1g −21,4 (0,68), +5g +2,8 (0,47) — [sonuc_ciktisi.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sonuc_ciktisi.txt)
- 1/2 +5g ayrıntı: yarılar −117 / −18 bp, 41 olay, olay medyanı −51 bp, %56 negatif, en negatif olay hariç ortalama −52 bp,
  plasebo dilimi %8,2 → yalnız P ölçütünü 0,001 farkla kaçırıyor — [hucreler_ndx.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/hucreler_ndx.csv)
- Aynı hücre %5 eşikte −24,7 bp (P↓ 0,86), görsel sınırlarla −11,7 (0,65), DAX'ta −10,2 (0,61) — [ek_tanilama_ciktisi.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/ek_tanilama_ciktisi.txt), [hucreler_dax.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/hucreler_dax.csv)
- Ters yönde ölçütleri sağlayan 3 hücre: 1/3 +1s (+6,5, P↑ 0,996, 35 olay, %60 pozitif, plasebo dilimi %93), 1/3 +1g (+33,6,
  P↑ 0,998, yarılar +23/+40, olay medyanı +32, %71 pozitif, en iyi olay hariç +23, plasebo %95,6), tam +1s (+14,3, P↑ 0,982, yarılar
  +16/+13, 28 olay medyanı +9, %75 pozitif, en iyi hariç +8, plasebo %98,8); iki yönlü Bonferroni eşiği 0,99917'yi hiçbiri geçmiyor — [sonuc_ciktisi.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sonuc_ciktisi.txt)
- Sonradan tanılama: bu üç hücre DAX'ta −3,7 / −18,5 / −18,7 bp (ters), %5 eşikte +3,4 / +15,6 / +4,0 (P↑ 0,83/0,95/0,84),
  görsel sınırlarla −0,8 / +26,4 / −0,6; aile düzeyinde "plasebonun %95'i üstünde ≥ 2 hücre" 500 rastgele şablon üçlüsünün %20,4'ünde,
  en uç dilimi (%98,8) aşan maks %15,6'sında; olay medyanlarında 2 üst + 2 alt uç hücre — [ek_tanilama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/ek_tanilama.json)
- Şablon-başına dedektör (tanımlayıcı): yukarı hücrelerin kaynağı T3 benzerleri (T3 tam +1s +19,5 P↑ 0,999; T3 1/3 +1g +31,2
  P↑ 0,994); T1 ve T2 dedektörlerinde P ≥ 0,975 hücre yok — [hucreler_ndx_sablon_basina.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/hucreler_ndx_sablon_basina.csv)
- Tam eşleşmelerin penceresi içinde ("oluşurken"): medyan net −%5,0 (çeyrekler −%8,0 / −%2,9), medyan aralık %8,6; 48 günün 34'ü
  üst 4 oynaklık ondalığında; en yakın şablon T2 23 gün, T3 25 gün, T1 0 gün — [sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sonuc.json)
- Olay listesi (tarihler, olay başına fark): ör. tam +1g'de 2025-04-03 olayı −1.108 bp, 2022-05-12 +453 bp — [olaylar_ndx_gelistirme.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/olaylar_ndx_gelistirme.csv)

### Inferences
- "Tepe aralığından sonra fiyat düşmeye devam eder" iddiası bu ölçü ve veride desteklenmiyor; kısa vadeli yukarı sapma da seçim
  ve bağımsız piyasa sınamasından geçmiyor → ME-08 gibi tahmin değeri yok (X); dedektör yalnız tanımlayıcı.
- "+1 saat" ufku 20:00 barı kapanışından sonraki bar (22:00, günlük ara sonrası) veya Cuma'da Pazar açılışıdır; tam +1s'deki
  yukarı sapma, varsa, ara/hafta sonu boşluğu davranışıdır.

### Gaps
- %2 eşikte 10 yılda yalnız 28–41 olay: 50–60 bp'lik 5 günlük etkiyi güvenle ayırmak için güç sınırda (olay başı sapma yüzlerce bp).
- Olay sonuçları ilk-gün ölçüsüyle de raporlandı (CSV) ama ölçüt ortalama-farka göre verildi.

## Bağımsız piyasa (DAX) ve doğrulama dönemi

### Takeaway
DAX'ta NDX'i teyit edecek geçen hücre yok; NDX'teki yukarı adaylar DAX'ta ters işaretli. Doğrulama dönemi (2025-12 → 2026-10)
şablonlarla çakışmayan sorgularda hücre başına 0–4 benzer gün verdi → güç yok.

### Cited Findings
- DAX 2020-01 → 2025-11: hücre başına 31 benzer gün, 14–29 olay; aşağı yönde P ≥ 0,975 olan tek hücre 2/3 +1s (−13,0 bp, P↓ 0,975,
  yarılar −15/−12, 23 olay, medyan −3, %61 negatif) — NDX'te aynı hücre −5,5 (P↓ 0,85) — [hucreler_dax.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/hucreler_dax.csv)
- DAX benzer günlerinin %26'sı (1/3) / %48'i (tam) NDX benzer günlerine ±3 gün yakın → DAX kısmen aynı piyasa olaylarını görüyor — [ek_tanilama.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/ek_tanilama.json)
- NDX doğrulama: 168–182 uygun sorgu günü; tam aşamada 2 gün (2026-06-10/11, tek olay: +35 / +199 / +324 bp, +1s/+1g/+5g),
  1/3'te 4 gün (−14 / −42 / −100 / −45 bp), 2/3'te 0 — [hucreler_ndx.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/hucreler_ndx.csv)

### Inferences
- Bağımsız piyasa ve ileri dönem, NDX geliştirmedeki hiçbir sapmayı desteklemiyor; 15 hücrede 1 DAX isabeti tesadüf beklentisi (~0,4) düzeyinde.

### Gaps
- Şablonların hepsi doğrulama döneminde olduğundan ileri sınama yapısal olarak güçsüz; gölge kayıt yıllar sürer (yılda ~3–4 olay).

## Bugün bu yapı oluşuyor mu?

### Takeaway
Hayır: son mevcut barda (2026-10-02 04:00 UTC) kısmi/tam benzerlik yüzdelikleri %44–64 (eşik %2/%5). Son 60 sorgu gününde %2
benzerlik yalnız şablonların kendi dönemi içinde.

### Cited Findings
- Son bar D yüzdeliği: 1/3 %52,6 (en yakın T3), 1/2 %43,8 (T2), 2/3 %64,1 (T1), tam %46,7 (T3); son 20:00 sorgusu 2026-10-01:
  %60,2 / %41,3 / %61,6 / %47,6 — [sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sonuc.json)
- Son 60 sorgu gününde %2 benzer günler: tam 07-29, 08-21, 08-24; 2/3 07-17, 07-24, 08-19; 1/2 08-06, 08-17; 1/3 07-09, 07-21
  (hepsi şablon dönemi); Eylül'de yalnız %5 düzeyinde: 1/3 09-03, 09-21, 09-23; 1/2 09-23; 2/3 09-02 — [sonuc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/benzerlik_tepe_20261019/sablon/results/sonuc.json)

### Inferences
- 2 Ekim itibarıyla piyasa bu şablonların hiçbirine benzer bir 1–2 haftalık yol çizmiyordu.

### Gaps
- Yerel veri 2026-10-02 04:00 UTC'de bitiyor; kullanıcının ekran görüntülerinin alındığı 2026-10-19 için durum hesaplanamadı.
