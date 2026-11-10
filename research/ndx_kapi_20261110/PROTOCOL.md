# NASDAQ kazanç kapısı araması — ön kayıt (2026-11-10)

Kullanıcı hedefi: yalnız NASDAQ üzerinde, bulunana kadar. Bu dosya her turdan ÖNCE yazılır; tur ekleri
(EK-n) sonuç görülmeden eklenir. Deneme sayacı aşağıda tutulur (E23: aynı geçmişe çok bakış).

Defter taraması: DAYCOMBO/REENTRY kapıları (TD-01 0/89, IO-23) ve NDX'in kendi OHLC'sinden türeyen kapılar
(GF-01, GC, PN, TL, KC, KS-01a) yeniden açılmaz. Yeni olan: **bilgi sınıfı**. Kapı değişkenleri NDX'in kendi
mumundan değil; Nasdaq oynaklık endeksinin fiyata göre tepkisi, QQQ'nun gerçek borsa hacmi, eşit ağırlıklı
endeksin göreli getirisi. Mekanizma ilkesi (defter §3-21): "kim işlem yapmak zorunda?"

## Tur 1 — "Düşüş günü sonrası uzun" tabanına üç kapı

**Taban olay.** QQQ kapanışı önceki kapanışın altında (düşüş günü t). Giriş: t+1 açılışı. Çıkış: t+1
kapanışı. Sonuç Y = bp. Açılış girişi bilerek seçildi: kapı değişkenleri (VXN kapanışı 16:15 ET, tam gün
hacmi) 16:00 kapanışında bilinmez (E99). Tabanın kendisi GR-01'de biliniyor; sınanan şey kapıların farkı.

**Kapılar (her biri tek, önceden sabit eşik):**
- **K-A korku aşımı.** e_t = ΔlnVXN_t − (a + b·r_t); (a, b) önceki 252 günün EKK'sı (t hariç), r_t = QQQ
  günlük getirisi. Kapı açık: e_t > 0 (oynaklık, fiyat düşüşünün ima ettiğinden fazla sıçramış → korku
  fiyatlandı). Karşı durum: e_t ≤ 0 (korkusuz düşüş = bıçak; defter KS-01b "sakin düşüş").
- **K-B teslimiyet hacmi.** QQQ hacmi_t / önceki 60 günün medyanı ≥ 1,5 (defterdeki 1,5 eşiği; KS-01a'da
  endeks "hacmi" ile sınanmıştı, burada gerçek ETF hacmi).
- **K-C yaygın satış.** r(QQEW)_t − r(QQQ)_t < 0 (eşit ağırlıklı daha çok düştü → geniş tabanlı tasfiye).
- **Referans (yeni bulgu sayılmaz):** VIX_t ≥ 18,4 (bilinen stres etkisi; motor kontrolü).

**Dönemler.** K-A, K-B: KEŞİF 2001-03 → 2010-12 · TEST 2011-01 → 2018-04 · KÖR 2018-05 → 2026-11.
K-C (QQEW 2006-04'te başlar): KEŞİF 2006-06 → 2012-12 · TEST 2013-01 → 2018-04 · KÖR aynı.

**Geçme ölçütü (kapı başına, hepsi):**
1. KEŞİF: fark Δ = ort(Y | açık) − ort(Y | kapalı) > 0; kapı etiketinin taban olaylar içinde dairesel
   kaydırma permütasyonu (2.000) ile tek yönlü p; üç kapı için Holm ≤ 0,05.
2. TEST ve KÖR'ün her birinde Δ > 0, ay-blok bootstrap P(Δ > 0) ≥ %90.
3. TEST ve KÖR'ün her birinde kapı açıkken ort(Y) − 2 bp (maliyet) > 0, P ≥ %90.
4. VIX katmanı: Δ, VIX ≥ 18,4 ve < 18,4 katmanlarının ikisinde de KÖR'de > 0 (stresin kopyası değilse).
Dördü de geçerse → Tur 1b: broker NAS100 M30 2018-05 → 2026-11'de icra kartı (16:30 ET girişi dahil,
gerçek spread × 1,5, 2 bp/gece, tek pozisyon, iki yarı, en iyi 5 hariç). Biri düşerse kapı X.
Plasebo: aynı kapı "yükseliş günü sonrası" olaylarda (etki korkuya özgüyse orada görülmemeli) — raporlanır.

**Sızıntı denetimi.** Kapı değişkenleri t günü kapanışında (en geç 16:15 ET) kesinleşir, giriş t+1 açılışı.
EKK penceresi t'yi içermez. Medyan hacim t'yi içermez. Önek testi: t sonrası veriyi silince t'nin kapı
değeri değişmemeli (kodda doğrulanır).

## Deneme sayacı
| Tur | Kapı sayısı | Geçen | Not |
|---|---|---|---|
| 1 | 3 (+1 referans) | 0 | K-A, K-B, K-C X. Referans stres etkisi yalnız 2001-10 ve 2018-26'da; 2011-18'de yok |
| 2 | 1 aday + 2 öngörü | 0 | S1 havuz −24,5 bp ama medyan +2,3 (sol kuyruk), Ö2 ✗, SPY ✗ → X; Ö1 (SMA50 altı ralli −39 bp) C izi |
| 3 | 1 kapı (QQQ aşaması) | 0 | G-IBS gece: açıkken +10,6 / +21,3 / +13,6 bp, Δ 3/3 artı ama p≈0,25 ve eşik altı → X; broker aşaması koşulmadı |
| 4 | 1 kapı | 0 (4/5) | G-DD: açık +0,286R / kapalı +0,074R, Δ +0,212 P 0,992 perm 0,012, 3/3 set, 7/9 yıl, plasebo temiz; ölçüt 3 (kapalı ≤ +0,05) düştü → veto değil, C+ |
| 5 | 1 veto | 0 | Ayı rallisi vetosu: dün yükseliş kolunda SMA50 altı +0,076R / üstü +0,072R, fark yok → X |
| 3b | rapor (12 hücre) | — | Tur 3 broker aşaması; 'son saat < 0' hücresi öne çıktı → Tur 6 |
| 6 | 1 kural, 6 doğrulama + 2 sağlamlık ölçütü | D1 ✓ D2 ✓ D4 ✓ D5 ✓ D6 ✓ S1 ✓ S2 ✓ · D3 ✗ (kural net +6,0 ama Δ P 0,79 < 0,90) | Şema gereği **C+** (çağa özgü: 2020'den beri 7/7 yıl, 2018-19 eksi); kart 6/6 |

## EK-1 — Tur 2: "Sıkışma günü" (Tur 1 sonuçları görüldükten sonra, aşağıdaki ölçümler görülmeden yazıldı)

**Gözlem (sonradan, Tur 1 plasebo hücresi; kanıt sayılmaz):** yükseliş günü ∧ QQQ hacmi ≥ 1,5× → ertesi
gün açılış→kapanış KEŞİF −30 bp (n 84), TEST −1 (n 92), KÖR −42 (n 94). Bakılan plasebo hücresi 12 idi.

**Mekanizma.** Düşüşte satıcı zorunludur; açığa satış sıkışmasında ALICI zorunludur. Zorunlu alım bitince
fiyat geri verir. Sıradan yükseliş ("coşku dönmez") bundan ayrılır: zorunlu taraf yoktur. Bu, defterin
"kim işlem yapmak zorunda?" ilkesinin kısa taraftaki tek öngörüsüdür.

**S1 (gözlenen tanım, aynen):** r_t > 0 ∧ hacim_t / medyan(önceki 60 gün) ≥ 1,5. Sonuç Y = t+1 açılış → kapanış.

**Yeni öngörüler (bu veride henüz bakılmadı; mekanizma doğruysa tutmalı):**
- **Ö1 bağlam.** S1 günleri içinde kapanış < SMA50 (düşüş eğilimi içi ralli = sıkışma) olanlar, kapanış ≥
  SMA50 olanlardan daha eksi: üç dönemin üçünde işaret aynı ve havuzda ay-blok P(fark < 0) ≥ %95.
- **Ö2 doz.** Yükseliş günlerinde hacim oranı ile Y arasında Spearman korelasyonu üç dönemin üçünde eksi,
  havuzda p < 0,05; ayrıca S1 ∧ r_t ≥ %1, S1 ∧ r_t < %1'den daha eksi (havuz).
- **Sağlamlık.** Havuz S1: medyan < 0; en eksi 5 gün çıkınca ortalama hâlâ < −5 bp; ≥ 3 olaylı yılların
  ≥ %60'ı eksi; ay-blok P(ort < 0) ≥ %97,5.
- **Kardeş piyasa (mekanizma körü, NASDAQ dışı yalnız teyit için):** SPY ve IWM, kendi hacimleriyle S1,
  2001-03 → 2026-11: her birinde ort < 0, ay-blok P ≥ %90. (Aynı takvim günleri: tam bağımsız değil.)
- **Eski dönem:** QQQ 1999-06 → 2001-02 S1: yalnız işaret raporlanır (n küçük).

**Hüküm şeması.** Ö1 ∧ Ö2 ∧ sağlamlık ∧ kardeş piyasa hepsi geçerse → Tur 2b: broker NAS100 M30 2018-26
icra kartı (09:30 ET açılışında SAT, 16:00'da kapat; spread × 1,5; ayrıca "ertesi gün uzun açma" vetosu
olarak botun DAYCOMBO yeniden üretiminde 2024-26). Sağlamlık düşerse X. Ö1 veya Ö2'den yalnız biri düşerse C.

## EK-2 — Tur 3: "Kapanış baskısı gecesi" (Tur 2 ve yıl×hücre betimsel tablosu görüldükten sonra yazıldı)

**Görülen (betimsel tablo, kanıt sayılmaz):** düşüş günü ∧ VIX_t ≥ 18,4 sonrası gece (kapanış → ertesi açılış)
QQQ getirisi dört çağda +7,9 / +7,3 / +11,1 / +10,4 bp; gün-içi kol yalnız 2018+'da artı (+22,8).
Kapı değişkenlerine (IBS, son saat) bu tabanda henüz bakılmadı.

**Mekanizma.** Korku gününde zorunlu satış kapanışa yığılır (kaldıraçlı ETF dengelemesi, korunma, teminat).
Fiyat kapanışta gün dibine yakınsa baskı kapanışa kadar sürmüştür; riski gece taşıyan prim alır.
Yeniden açma gerekçesi: ME-07 (son saat → gece) 205 geceyle "sonuçsuz" kalmıştı (güç yetersiz); burada
27 yıl günlük + 8,5 yıl broker M30 var ve taban korku hücresine daraltıldı. KS-01a IBS'yi C3b olaylarında
(çok günlü çıkış) sınamıştı; burada hedef yalnız gece.

**Taban T:** r_t < 0 ∧ VIX_{t−1} ≥ 18,4 (VIX önceki günün kapanışı: 16:00 girişinde kesin bilinir).
**Sonuç:** Y = (Açılış_{t+1} + temettü_{t+1}) / Kapanış_t − 1, bp. Cuma kapanışı → Pazartesi açılışı tek gece.
**Kapı G-IBS:** IBS_t = (C − L)/(H − L) < 0,2 (defterdeki eşik). Karşı: IBS ≥ 0,2.

**QQQ aşaması (27 yıl).** KEŞİF 1999-06 → 2010-12 · TEST 2011-01 → 2018-04 · KÖR 2018-05 → 2026-11.
Ölçüt: (1) KEŞİF Δ > 0, dairesel kaydırma p ≤ 0,05; (2) TEST ve KÖR'ün her birinde Δ > 0, ay-blok
P ≥ %90; (3) her üç dönemde kapı açıkken ort(Y) ≥ 12 bp (CFD maliyeti ≈ 4 bp'nin 3 katı; E51) ve
P(ort > 4 bp) ≥ %90; (4) plasebo: aynı kapı yükseliş günlerinde (IBS < 0,2 nadir) ve VIX_{t−1} < 18,4
düşüş günlerinde raporlanır (hüküm dışı).

**Broker aşaması (QQQ aşaması geçerse karta, geçmezse yalnız raporlanır):** NAS100 M30 2018-05 → 2026-11.
Gün = 09:30–16:00 ET seansı; r_t = 16:00 barı açılışı / önceki günün 16:00 barı açılışı − 1; IBS seans
barlarından; giriş 16:00 barı açılışı + spread, çıkış ertesi işlem günü 09:30 barı açılışı; maliyet bar
spread'i × 1,5 + 1,8 bp/gece (Cuma ×3). İkinci kapı **G-SON:** 15:00 → 16:00 getirisi < 0.
Kart ölçütleri (2. KURAL): n ≥ 150, ort > 0 ve P ≥ %90, iki yarı ≥ 0, spread × 1,5'te artı, en iyi 5 hariç
artı, tek pozisyon (zaten gece başına tek).
**Hüküm:** QQQ (1)–(3) ∧ broker kartı → B (gölge adayı). QQQ geçer, broker geçmez → C. QQQ geçmez → X.

## EK-3 — Tur 4: canlı ORB × VIX kuralına "dün düşüş" kapısı (Tur 1–3 görüldükten sonra, ORB işlemlerinde bu kırılım görülmeden yazıldı)

**Görülen (kanıt sayılmaz, yön bilgisi buradan geliyor):** QQQ açılış→kapanış, 2018-27: düşüş günü ∧ VIX ≥ 18,4
sonrası +22,8 bp (n 523), yükseliş günü ∧ VIX ≥ 18,4 sonrası −5,8 bp (n 491). 2011-18'de fark yok.
Karşı ipucu (defter TR-P1): ORB, dünü RSI2 < 10 OLMAYAN günlerde 3 setin 2'sinde daha iyiydi.

**Soru.** HB-03 C1 (ORB uzun ∧ önceki gün VIX ≥ 18,4; n 605, +0,185R) VIX'i şart koşuyor ama dünün yönünü
ayırmıyor. Kenar yalnız düşüş günü sonrasında mı?

**Veri.** `research/haber_derin_20261105/results_havuz_10yil.csv` (kartın kendi işlem tablosu, 1.464 ORB
uzun işlemi; yeniden simülasyon yok). Üç set: 1h 2016-06 → 2021-06 · 30m 2021-23 · 5m 2024-26.
**Kapı G-DD:** NDX nakit kapanışı(d−1) < kapanış(d−2) (Yahoo ^NDX; d gününün açılışından önce bilinir).
Eşik yok, ayar yok. C1 içinde açık / kapalı kıyaslanır.

**Geçme ölçütü (hepsi):**
1. Üç setin üçünde Δ = ortR(açık) − ortR(kapalı) > 0.
2. Havuzda ay-blok P(Δ > 0) ≥ %95 ve C1 dizisi içinde dairesel kaydırma p ≤ 0,05.
3. Kapalı kol havuzda ortR ≤ +0,05 (kenar gerçekten bir kolda toplanıyor) ve açık kol ortR ≥ +0,25.
4. Yıl bazında Δ > 0 olan yıl ≥ 7/10 (kolun ≥ 10 işlemi olan yıllar).
5. Plasebo: aynı kapı VIX < 18,4 ORB işlemlerinde Δ'nın ay-blok P(Δ > 0) < %90 (etki korkuya özgü).
Yanında (E110): toplam R ve aylık Sharpe, kapılı vs kapısız.
**Hüküm:** beşi de → B− (dünün yönü örtüşen veride görüldüğü için; ileri gölge şart). Biri düşerse X.

## EK-4 — Tur 5: "Ayı rallisi vetosu" (Tur 4 yıl tablosu görüldükten sonra; SMA50 kırılımı ORB işlemlerinde ve hacimsiz günlük hücrede görülmeden yazıldı)

**Görülen (kanıt sayılmaz):** Tur 4 kapalı kolu (dün yükseliş) 2019, 2020, 2022, 2024'te eksi; 2021, 2023, 2025'te
artı — takvim yılı düzeyinde "eğilim" sezgisi buradan. Tur 2 Ö1 (ön-kayıtlı, geçti): yüksek hacimli yükseliş
günü kapanış < SMA50 ise ertesi gün açılış→kapanış −44,8 / −5,1 / −57,1 bp, SMA50 üstünde +11 / +2 / −18.

**İddia.** Yüksek VIX'te düşüş eğilimi içindeki yükseliş günü zorunlu alımdır (açığa satış kapama); ertesi gün
uzun taraf ödemez. Veto V: önceki gün VIX ≥ 18,4 ∧ NDX kapanışı(d−1) > kapanış(d−2) ∧ kapanış(d−1) < SMA50(d−1)
→ d günü ORB uzun AÇMA. SMA50 = 50 günlük basit ortalama, d−1 dahil (kapanışta bilinir). Tek tanım, ayar yok.

**A. ORB işlem tablosunda (C1, n ≈ 597; üç set).** Vetolanan kol K_v, kalan kol K_r.
Ölçüt: (1) K_v havuz ortR ≤ 0; (2) Δ = ortR(K_r) − ortR(K_v) > 0, ay-blok P ≥ %95, dairesel kaydırma p ≤ 0,05;
(3) üç setin üçünde Δ > 0; (4) K_v'nin ≥ 8 işlemi olan yıllarında ortR(K_v) < ortR(K_r) olan yıl ≥ %70;
(5) portföy (E110): veto sonrası toplam R ≥ veto öncesi ve aylık Sharpe artışı için ay-blok P ≥ %90;
(6) n(K_v) ≥ 60.
**B. Günlük 27 yıl desteği (QQQ, hacim şartı YOK).** Hücre: r_t > 0 ∧ VIX_{t−1} ≥ 18,4 ∧ kapanış_t < SMA50_t;
sonuç t+1 açılış→kapanış. Ölçüt: KEŞİF 2001-03→2010, TEST 2011→2018-04, KÖR 2018-05→ üçünde de ort ≤ 0 ve
aynı günlerde SMA50 üstü hücreden düşük; havuz ay-blok P(fark < 0) ≥ %95.
**Hüküm.** A(1–6) ∧ B → B (veto, gölge adayı). A geçer B geçmez → C+ (2016+ çağına özgü). A düşerse X.
Plasebo: aynı veto VIX < 18,4 ORB işlemlerinde (etki beklenmez), raporlanır.

## EK-5 — Tur 6: "Kapanış saati gecesi" (KSG) — ME-07'nin güçlü tekrarı (Tur 3b hücre tablosu görüldükten sonra; aşağıdaki D1–D6 ölçümleri görülmeden yazıldı)

**Öncül (defter).** ME-06(f) sonradan ipucu → ME-07 ön-kayıtlı tek sınama: NDX son nakit saati (15→16 NY) aşağıysa
gece (16:00 → 09:00) yükselir. 205 gece: Δ +12,7 bp, P 0,906 → SONUÇSUZ (güç yetersiz); DAX'ta etki yok; hüküm C.
Yeniden açma gerekçesi: yeni veri (broker NAS100 M30, 2018-05 → 2026-11, 2.095 gece; ME-07 gecelerinin 10 katı),
gerçek maliyet (spread + swap), saat özgüllüğü sınaması, 2016-18 bağımsız dönem, üç ABD endeksinde kör tekrar.

**Görülen (Tur 3b, kanıt sayılmaz; 12 hücreye bakıldı):** son saat < 0: n 1.038, brüt +11,0, net +7,1 bp,
P 0,997, yarılar +5,8 / +8,4. Son saat ≥ 0: net −6,1. Günün yönü geceyi ayırmıyor (düşüş +4,7 / yükseliş +4,1 brüt).

**Kural KSG (tek tanım).** NAS100, 16:00 ET: (16:00 barı açılışı / 15:00 barı açılışı − 1) < 0 → 16:00 barı
açılışında AL (ask = bid + bar spread'i), ertesi seansın 09:30 barı açılışında SAT. Stop yok. Maliyet:
spread × 1,5 + 1,8 bp × gece sayısı (Cuma → Pazartesi 3). İkincil: KSG-V = KSG ∧ önceki gün VIX ≥ 18,4.

**Doğrulamalar (henüz görülmedi):**
- **D1 yıl.** 2018…2026 dokuz takvim yılının ≥ 7'sinde KSG net > 0 ve ≥ 7'sinde Δ(brüt: son saat aşağı − yukarı) > 0.
- **D2 özgüllük.** Altı saat penceresi (10→11 … 15→16) için Δ_h = ort(brüt gece | saat aşağı) − ort(| saat yukarı).
  15→16 penceresi en büyük Δ'ya sahip olmalı ve hem düşüş hem yükseliş günlerinin içinde Δ_15→16 > 0 olmalı.
- **D3 bağımsız dönem.** NDX 1h, 2016-06 → 2018-05-14 (`backend/data/candle_history/NDX_1h.npz`, broker örnekleminden
  önce): sinyal 15:00 barı (kapanış/açılış − 1 < 0), sonuç 16:00 → ertesi 09:00 barı açılışı. Δ > 0 ve ay-blok
  P(Δ > 0) ≥ %90; KSG ort. brüt − 3,9 bp > 0. Eksen denetimi: en oynak saat barı 09 veya 10 ET olmalı.
- **D4 kör enstrüman.** US500, US30, US2000 broker M30 2018-26, kural aynen (kendi son saati, kendi spread'i):
  üçünün üçünde KSG net > 0 ve Δ > 0; üç endeksin gece-ortalaması serisinde ay-blok P(Δ > 0) ≥ %95.
- **D5 besleme.** Dukascopy NDX 1m 2021-11 → 2026-11 (1,5 puan spread + 1,8 bp/gece): KSG net > 0, P ≥ %90;
  ortak gecelerde broker ile gece getirisi korelasyonu ≥ 0,95.
- **D6 kart.** n ≥ 150; net > 0, P ≥ %90; iki yarı ≥ 0; spread × 3 stresinde net > 0; giriş 16:30'a gecikince
  (16:30 barı açılışı) net > 0 ve kayıp ≤ ortalamanın yarısı; en iyi 5 gece hariç net > 0; gece başına tek pozisyon.
**Hüküm.** D1 ∧ D2 ∧ D6 zorunlu (düşerse X). Üstüne D3 ∧ D4 ∧ D5 → **B** (yeni NASDAQ kuralı, gölge adayı).
D3 veya D4 düşerse → C+ (çağa / araca özgü). Raporlanır (hüküm dışı): çıkış 03:00 ve 08:00 ET; KSG-V; aylık Sharpe;
C3 olay geceleriyle örtüşme; en kötü gece.

## EK-6 — Tur 6 sağlamlık (D1–D6 görüldükten sonra; aşağıdakiler görülmeden yazıldı)
Amaç icra artefaktını dışlamak (E7, E97): sinyal fiyatı ile giriş fiyatı aynı an (16:00 barı açılışı).
- **S1 gecikmeli giriş (Dukascopy 1m, ölçüt):** sinyal 15:00 → 16:00 açılışları; giriş 16:01, 16:05, 16:15
  barı açılışı + 1,5 puan; çıkış 09:30. Üçünde de net > 0 ve 16:05 için ay-blok P ≥ %90. Düşerse KSG X.
- **S2 sinyal kaynağı (ölçüt):** sinyal 15:00 → 15:55 (16:00 fiyatı görülmeden), giriş 16:00 + 1,5 puan: net > 0.
- **S3 doz-tepki (rapor):** son saat getirisi beşte birlik dilimlerine göre gece brüt getirisi.
- **S4 haftanın günü, VIX kovası, seçimsiz dairesel kaydırma p (rapor).**
- **S5 2020 öncesi / sonrası (rapor):** D1'de etki 2020'de başlıyor göründü; iki dilim ayrı yazılır.

Not (EK-6 sapması): Dukascopy'de 16:15–16:30 ET arası bar yok (endeks CFD arası). S1'in 16:15 girişi yerine 16:14 kullanıldı; sonuç görülmeden değiştirildi.

## EK-7 — Canlı çıkış zamanlaması (canlı modül yazılırken fark edilen soru; sonuç görülmeden yazıldı)
Soru: KSG kazancının ne kadarı 09:30 ET'de CFD fiyatının vadeli tabanlı → nakit tabanlı geçişindeki açılış sıçramasında? Canlı çıkış
09:30:00 açılışında değil, tarama döngüsünün ilk turunda gerçekleşir (gecikme 0–60+ sn).
- **T1 sıçrama:** 09:29 barı kapanışından 09:30 barı açılışına getiri (bp), KSG geceleri vs diğer geceler (Dukascopy 1m 2021-11→2026-11 ve broker M30 2018-26: 09:00 barı kapanışı → 09:30 açılışı).
- **T2 çıkış gecikmesi (Dukascopy 1m, ölçüt):** çıkış 09:30, 09:31, 09:32, 09:35, 09:45 açılışı (bid; giriş 16:00 + 1,5 puan, 1,8 bp/gece): ortalama net
  ve ay-blok P. Ölçüt: 09:32 çıkışında net > 0 ve P ≥ %90. Düşerse canlı çıkış mekaniği kenarı taşımıyor → sınıf C'ye iner ve yeniden tasarım gerekir.
