# Ön-kayıt — "Dalgalı tepe aralığı" şablon benzerliği (kullanıcı tanımı) — ME-09

> 2026-10-19, **ileri getiriler hesaplanmadan** yazıldı. Bu dosya yazılmadan önce yalnız şekil işleri yapıldı:
> adım 1 (`sablon_dogrulama.py` → `results/sablon_dogrulama.json`, şablonların birbirine benzerliği) ve adım 2
> (`etiketleme_gorseli.py` → `tur1_etiketleme.png`, sonrası gösterilmeyen 12 eşleşme). İkisi de hiçbir ileri getiri kullanmaz.
> Yöntem ME-08'den (`research/benzerlik_ornek_20261019/`) aynen alındı; farklar §9'da.

## 0. Soru
Kullanıcı NAS100 1h grafiğinde (TradingView, Capital.com CFD; görsel 6 ve 7) üç bölge işaretledi ve hepsinin **aynı yapı**
olduğunu söyledi: tepelere yakın dalgalı/oynak aralık — derin geri çekilmeler, alçalan tepeler, sonda düşüş. Sorular:
(1) ölçü üç şablonu birbirine benzer görüyor mu, (2) 10 yılda en benzer 12 bölge (etiketleme için), (3) yapı oluşurken
(kısmi) ve tamamlandıktan sonra +1 saat / +1 gün / +5 gün (kısmide ayrıca "kalan süre") fiyat ne yaptı — tabana göre.

## 1. Veri ve şablon sınırları
- NDX CFD 1h: `research/ndx_gate_forge/data/long_1h_utc.parquet` (2016-05-29 → 2026-07-14) + `bars_15m.parquet`'ten 1h'e
  toplanmış uzatma (→ 2026-10-02 04:00). ME-08 `load()` ile aynı. Zaman: UTC bar başlangıcı. Log kapanış.
- **Birincil şablon sınırları = kullanıcının yanıtındaki günler, UTC gün sınırıyla** (başlangıç günü 00:00 barı → bitiş günü
  23:00 barı); yalnız şablonun içindeki veri kullanıldı, bitişten sonraki hiçbir bar sınır seçiminde kullanılmadı:
  - T1 2026-07-06 00:00 → 2026-07-21 23:00 — **276 bar**, 14 işlem günü
  - T2 2026-07-17 00:00 → 2026-07-29 23:00 — **207 bar**, 11 işlem günü
  - T3 2026-08-13 00:00 → 2026-08-20 23:00 — **138 bar**, 7 işlem günü
- **Görsel ölçümü (duyarlılık, sonuç testinde KULLANILMAZ):** elips kenarlarının piksel→zaman dönüşümü (eksen etiketleri
  arası ≈ 1,7–2,8 piksel/bar): görsel 6 pembe T1 ≈ 07-07 07:00 → 07-21 15:00 (07-06 tepesi elipsin dışında); görsel 7 kırmızı
  T2 ≈ 07-16 12:00 → 07-29/30; görsel 7 sağ pembe T3 ≈ 08-11 08:00 → 08-20 ~06:00 (= ekranın sağ kenarı). Görsel 7 sol
  pembe elips 07-27'ye kadar uzanıyor; kullanıcı T1 için 07-21 dedi → kullanıcının sözü esas alındı.
- Fiyat düzeyleri Capital.com'dan birkaç on puan farklı (ör. 1 Temmuz tepesi bizde 30.341, ekranda ~30.100); şekil aynı.

## 2. Benzerlik ölçüsü (ME-08'de kullanıcının onayladığı ölçü, değiştirilmeden)
- Pencere → 64 noktaya zaman-esnek doğrusal yeniden örnekleme → z-normalize (ddof 0) → Öklid mesafe.
  (z-normalize vektörlerde d² = 128·(1 − r) → d eşiği bir şekil korelasyonu eşiğidir.)
- **Pencere uzunlukları şablonlardan:** medyan şablon uzunluğu 207 bar → L ∈ {0,8×, 1,0×, 1,2×} = **{166, 207, 248} bar**.
- D = min_{şablon ∈ {T1,T2,T3}, L} mesafe. Sorgu: her gün **20:00 UTC'de başlayan bar** (kapanışı 21:00); pencere o barda biter
  (o bar dahil) → yalnız kapanmış barlar.
- **Kısmi eşleşme:** şablonun ilk f kesri (round(f·uzunluk) bar) ile son round(f·L) bar; f ∈ {1/3, 1/2, 2/3}. Tam: f = 1.
- **Eşik:** her f için geliştirme dönemi gün-sonu D değerlerinin **%2'lik dilimi** (birincil) — "benzer gün"; %5 ikincil
  (tanımlayıcı). "Benzer olmayan" = D > o f'nin %5 dilimi.

## 3. Adım 1 sonucu (şekil, sonuç yok) — ölçü şablonları birbirine benzer görüyor mu?
`results/sablon_dogrulama.json`. Birincil sınırlarla tam aralık şekil korelasyonları: **T2–T3 r 0,87** (şablon başına D
dağılımında %2,8 dilim — sınırda benzer), **T1–T2 r 0,68** (%7–18), **T1–T3 r 0,44** (%24–32). Dedektör tarzı (her şablonun
son barında diğer ikisiyle, L ∈ LS): T1 %17, T2 %2,9, T3 %11 dilim. Görsel sınırlarla tablo değişiyor (T1–T3 r 0,78 / %1,9–3,3,
T2–T3 r 0,59, T1–T2 0,67) → **ölçü üçünü tutarlı biçimde aynı şekil saymıyor; benzerlik sınır seçimine duyarlı.**
Farklar: süre 14/11/7 işlem günü (2×); genlik (aralık) %5,8 / %7,9 / %3,9 (önceki 20 günün ortalama gün aralığının 2,6 / 3,9 /
2,0 katı); net −%1,9 / −%5,2 / −%1,8; %1 zigzag bacak sayısı 10 / 17 / 2 (%0,5'te 24 / 32 / 8); 1h oynaklık 25 / 38 / 20 bp;
en düşük nokta konumu 0,80 / 0,99 / 0,97 (T1 dipten toparlanarak bitiyor; T2/T3 dipte bitiyor); tepe önceki 20 günün zirvesine
göre −%2,7 / −%4,9 / +%1,0. Ortak olan nitel: tepeye yakın oynaklık + sonda düşüş; ortak bir **yol şekli** değil.
Etiketleme görselindeki 12 eşleşmenin hepsi T2 veya T3'e en yakın (T1'in kendi %2 dilimi 5,57, T2/T3 ~3,9 → birleşik
min-D dedektörü pratikte T2/T3 dedektörü). Bu yüzden şablon-başına dedektör de tanımlayıcı olarak raporlanır (§7).
**Karar:** ön-kayıtlı test ME-08 ölçüsüyle (birleşik min-D) yine de yapılır — kullanıcı "hepsi aynı yapı" dedi; ama
sonuç "üç şablonun ortak şekli" değil, "üçünden herhangi birine benzeyen pencereler" diye okunacak.

## 4. Sonuçlar (ufuklar) — hücreler
- Getiri = log(kapanış[Q+h] / kapanış[Q]), bp; ayrıca yukarı oranı.
- **Kısmi (f = 1/3, 1/2, 2/3):** +1 saat (1 bar), +1 gün (24 bar), +5 gün (120 bar), **kalan** = round((1−f)·207) bar
  (f=1/3 → 138, 1/2 → 104, 2/3 → 69).
- **Tam (f = 1):** +1 saat, +1 gün, +5 gün.
- **Aile: 3×4 + 3 = 15 hücre** (NDX, geliştirme, %2 eşik).

## 5. Kıyaslar (aynı ufuk, aynı dönem)
1. **Tüm günler** (koşulsuz; sürüklenme).
2. **Getiri + oynaklık eşli taban (asıl kıyas):** benzer OLMAYAN (D > %5 dilimi) günler; benzer günle aynı
   (geriye-dönük getiri ondalığı × geriye-dönük gerçekleşen oynaklık ondalığı) hücresinde. Geriye-dönük pencere = round(f·207)
   bar (69/104/138/207); getiri = log fiyat farkı; oynaklık = penceredeki ardışık 1h log getirilerin std'si. Ondalık sınırları
   geliştirme dönemindeki uygun günlerden. Hücrede < 10 taban günü varsa sırayla: beşlik × beşlik → yalnız getiri beşliği → tüm
   benzer-olmayan günler (geri düşüş sayısı raporlanır). Taban aynı dönemin günlerinden (doğrulamada doğrulama günlerinden).
3. **Plasebo şablon:** 500 rastgele üçlü — her biri gerçek şablonlarla aynı uzunlukta (276/207/138 bar) 3 rastgele geçmiş
   pencere (2016-06 → 2026-09, gerçek şablon aralığıyla çakışmayan); aynı boru hattı (aynı f, L, eşik kuralı, eşli taban);
   sorgunun penceresi ∪ ufku plasebo şablonuyla çakışıyorsa o sorgu o plasebo için dışarıda. Rapor: gerçek farkın plasebo
   dağılımındaki yüzdeliği (gün düzeyi ortalama fark ve olay medyanı için). Soru: "herhangi bir rastgele şekle benzemek"
   kadar mı, daha mı fazla?
- Belirsizlik: **takvim ayı blok bootstrap**, B = 10.000 (ME-08 `mboot`: ayları yerine koyarak çek, oran-toplam ortalama).
- **Olay (epizod) düzeyi:** bir hücrede benzer günler sorgu-günü indeksinde ardışık; aralık ≤ 10 sorgu günü → aynı olay.
  Olay sonucu = olay içindeki günlerin (getiri − eşli taban) farklarının ortalaması (ikincil: olayın ilk gününün farkı).
  Raporlanır: olay sayısı, medyan olay sonucu, negatif olay payı, ortalama, **en uç olay hariç ortalama** (öngörülen yönde en
  uç olay çıkarılır; ayrıca karşı yönde en uç çıkarılmış hâli), işaret testi.

## 6. Yön ve başarı ölçütü (ön-kayıtlı)
- **Ön-kayıtlı yön: AŞAĞI (fark < 0) — 15 hücrenin hepsi.** Gerekçe: kısmi hücrelerde şablonların kendi devamı düşüş (T2/T3
  dipte bitiyor; "alçalan tepeler"); tamamlanmışta grafikçi "tepe/dağıtım" iddiası. Rakip hipotez (proje meta-dersi 2,
  "korku döner": düşüşle biten yapıdan sonra yukarı) **yön dışı**: karşı yönde ölçütleri geçen hücre yalnız "ön-kayıt dışı aday
  (C)" sayılır; güçlü sayılması için P ≥ 1 − 0,025/30 = 0,99917 gerekir (iki yönlü aile).
- **Hücre GEÇER** (hepsi): (a) eşli tabana göre fark < 0 ve ay-blok P(fark < 0) ≥ 0,975; (b) iki yarıda da (2016-06 → 2020-12 /
  2021-01 → 2025-11) fark < 0; (c) ≥ 20 bağımsız olay; (d) olay düzeyinde medyan < 0, negatif olay payı ≥ %50 ve öngörülen yönde
  en uç olay çıkarılınca ortalama hâlâ < 0.
- **GÜÇLÜ:** GEÇER + P ≥ 1 − 0,025/15 = **0,99833** (Bonferroni, aile 15) + plasebo yüzdeliği ≤ %5 (öngörülen yönde).
- %5 eşik, şablon-başına dedektörler, tüm-günler kıyası: **tanımlayıcı**, başarı ailesine girmez.

## 7. Tanımlayıcı ekler (başarı ailesi dışı)
- Şablon-başına dedektör (yalnız T1 / T2 / T3; kendi %2 dilimi) aynı 15 hücre.
- Eşleşen pencerelerin içindeki yol (net getiri, aralık) ve oynaklık ondalığı dağılımı — "oluşurken fiyat ne yaptı".
- Benzer günlerin en yakın şablona göre dağılımı.

## 8. Dönemler, bağımsız piyasa, bugün
- **Geliştirme:** sorgu 2016-06 → sonuç ufku 2025-11-30 23:00'ü geçmeyenler. Eşik/ondalıklar buradan.
- **Doğrulama (bir kez bakılır):** 2025-12-01 → 2026-10-02; sorgunun penceresi (en uzun round(f·248)) ∪ ufku herhangi bir
  şablonla çakışıyorsa dışarıda. Şablonların hepsi bu dönemde → az olay beklenir; güç dürüstçe raporlanır. Kullanım: geçen
  hücre varsa aynı işaret mi (doğrulama); yoksa tanımlayıcı.
- **DAX (bağımsız piyasa):** `research/ndx_gate_forge/data/dax_1h.parquet`, **yalnız 2020-01 →**. Aynı NDX şablon vektörleri,
  aynı L (bar), aynı f. Sorgu: her hafta içi UTC gününün saati ≤ 20 olan son barı (saat 19 veya 20 olmalı; DAX CFD 2024+
  20 bar/gün). Ufuklar: +1 saat = 1 bar; **+1 gün = sonraki sorgu günü; +5 gün = 5. sonraki sorgu günü**; kalan = round((1−f)·207)
  bar. Eşik/ondalıklar DAX'ın kendi geliştirme döneminden (2020-01 → 2025-11). Yarılar 2020–2022 / 2023–2025-11.
  DAX'ta Temmuz–Ağustos 2026 şablon aralığı (NDX ile eşhareket) aynı çakışma kuralıyla dışarıda.
  **Teyit kuralı:** NDX'te geçen bir hücre, DAX'ta aynı işaret + ay-blok P ≥ 0,95 + ≥ 10 olay ise "bağımsız piyasada teyitli".
- **Bugün:** son mevcut bar (2026-10-02 04:00 UTC) ve son 20:00 sorgusu (2026-10-01) için her f'de D ve geliştirme
  dağılımındaki yüzdelik (≤ %2 / ≤ %5 → yapı oluşuyor); son 60 sorgu gününde benzer günler. Veri 2026-10-02'de bitiyor —
  2026-10-19 (kullanıcının ekran görüntüsü günü) hakkında bir şey söylenemez.

## 9. ME-08'den farklar
Şablon sayısı 3; L {166, 207, 248} (şablonlardan); taban trend-eşli yerine **getiri + oynaklık eşli** (oynak yapılar yüksek
oynaklıkta oluşur); ufuklar +1s/+1g/+5g (+ kısmide kalan; 20 gün yok); plasebo şablon eklendi; olay düzeyi ölçütleri
ön-kayıtta (ME-08'de sonradan tanılama — E6); DAX bağımsız piyasa; yön ön-kayıtlı AŞAĞI.

## 10. Hesap kısıtı
En çok 2 süreç, `nice`; betikler ve çıktılar `research/benzerlik_tepe_20261019/sablon/` altında; git commit yok.
Sonuç betiği `sonuc_testi.py` **bir kez** çalıştırılır; çökme düzeltmesi dışında değişiklik olursa SONUC.md'de yazılır.
