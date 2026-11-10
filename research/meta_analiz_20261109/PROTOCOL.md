# Meta-analiz 2026-11-09 — ön kayıt (sonuçlara bakılmadan yazıldı)

Yazım anı: 2026-11-09, testlerden ÖNCE. Bu klasördeki hiçbir betik bu dosya yazılmadan koşulmadı.
Kapsam: arşivin meta-analizinden türeyen iki hipotezin en ucuz ilk testi + bir betimsel denetim.
Canlı sisteme dokunulmaz; yalnız yerel dosyalar okunur.

## MA-01 — "Gece dilimi": C3 kazancı hangi saat diliminde birikiyor?

**İddia.** TR-C3 (NDX RSI2<10, 15:30 ET AL → ertesi 15:30 SAT) kazancının çoğu gece diliminde
(16:00 → ertesi 09:30 ET) birikir; ertesi günün gündüz dilimi az kazanç, çok oynaklık ekler.
Mekanizma: korku gününde zorunlu satış kapanışa yığılır; riski gece taşıyan taraf prim alır.

**Veri.** `research/c1_turev_20261105/data/mt5/NAS100_M30.csv.gz` (broker BID, 2018-05 → 2026-11,
sunucu = New York + 7 saat; `lab.mt5_bars` ile aynı çeviri). Olay tanımı `r4_core.series/feats`
ile birebir: S = 15:30 barından önceki barın kapanışı, RSI2 (Wilder, alfa 0,5) < 10, giriş = 15:30
barının açılışı + 1,3 puan. Bu veri C3'ün bulunduğu veridir; dilim sorusu için ilk bakıştır.

**Ölçüm.** Her olay için bp cinsinden: D1 = 15:30 → 16:00 (aynı gün), D2 = 16:00 → ertesi işlem günü
09:30 barının açılışı, D3 = 09:30 → 15:30. Varyantlar (hepsi aynı girişle, 2 bp/gece finansman):
V0 = özgün (ertesi 15:30), V1 = ertesi 09:30 açılışında çık, V2 = ertesi 10:00 açılışında çık,
V3 = 16:00 barının açılışında gir, ertesi 09:30'da çık.

**Geçme ölçütü (hepsi birlikte):**
1. V1 veya V2 ortalaması ≥ V0 ortalamasının %75'i,
2. aynı varyantın standart sapması ≤ V0'ın %80'i,
3. ay-blok bootstrap (3.000) ile P(işlem SR_V > işlem SR_V0) ≥ %90,
4. kronolojik iki yarının ikisinde de SR_V > SR_V0,
5. bağımsız dönem: QQQ günlük 1999-03 → 2018-04 (broker verisinden önce), kapanışta RSI2<10 →
   kapanışta AL; gece (kapanış → ertesi açılış) payı toplam kapanış→kapanış getirisinin ≥ %50'si
   ve gece ortalaması > 0, ay-blok P ≥ %90.
Beşi de geçerse: "C3-gece" B adayı (gölge önerisi). Biri düşerse: X (betimsel bilgi kalır).
Çoklu sınama: 3 varyant; hepsi raporlanır, en iyisi seçilip sunulmaz. Plasebo: tüm günlerde aynı
dilimlerin ortalaması (koşulsuz gece/gündüz sürüklenmesi) yan yana verilir.

**Sızıntı denetimi.** Sinyal yalnız 15:30'dan önce kapanmış barı kullanır (E16). Saat ekseni: en
oynak 30 dk barının 09:30 ET'ye düştüğü ay ay doğrulanır (E2/E78). Giriş spread'li (E7). QQQ
adımında sinyal ve giriş aynı kapanış fiyatıdır (kapanış emri varsayımı) — bu sınır rapora yazılır.

## MA-02 — "Göreli korku": ABD endeks çiftlerinde göreli RSI2 geri dönüşü (piyasa-nötr)

**İddia.** Bir ABD endeksi diğerlerine göre iki günde sert geride kalınca (göreli RSI2 < 10) fark
kısmen kapanır. Uzun geride kalan / kısa sepet işlemi piyasa yönünden bağımsız kazanır.
Mekanizma: endeks düzeyinde zorunlu satış (sektör rotasyonu, türev korunması) geçici fiyat
baskısı yaratır. Defterde çift / göreli fiyat işlemi kaydı yok (yeni bilgi sınıfı).

**Veri ve dönemler.** KEŞİF: Yahoo günlük kapanış ^NDX, ^GSPC, ^DJI 1999-01 → 2009-12
(`research/fitil_ret_20261106/data_d1_*.parquet`). TEST: aynı seriler 2010-01 → 2018-04.
KÖR: broker M30 15:30 ET fiyatları NAS100, US500, US30, US2000, 2018-05 → 2026-11 (dört sembol).

**Kural (tek, önceden sabit).** X_i = ln P_i − diğer endekslerin ln P ortalaması. RSI2 (Wilder
alfa 0,5) X_i üzerinde. RSI2 < 10 → i'yi AL, diğerlerini eşit ağırlıkla SAT (eşit nominal).
Çıkış: X_i'nin ilk yükseldiği gün (en çok 5 gün) — C3b'nin göreli hâli. Endeks başına tek
pozisyon. Ayna (ikincil): RSI2 > 90 → i'yi SAT, sepeti AL.
Maliyet: Yahoo aşamasında işlem başına toplam 4 bp (iki bacak, gidiş-dönüş) + 1,5 bp/gece.
Broker aşamasında her bacakta bar spread'i × 1,5 (giriş ve çıkışta yarımşar) + 1,5 bp/gece;
sinyal 15:30 öncesi kapanmış bardan, giriş 15:30 barının açılışı.

**Geçme ölçütü.** KEŞİF net ortalama > 0 ve ay-blok P ≥ %95 → ancak o zaman TEST ve KÖR okunur
(yine de üçü de raporlanır). TEST ve KÖR'ün her birinde net > 0, P ≥ %90 ve brüt ortalama ≥
2 × maliyet (E51). Üçü de geçerse B adayı; aksi hâlde X. Plasebo: sinyal dizisinin dairesel
kaydırması (500 çekiliş) ile aynı kural.

## MA-03 — Betimsel: risk bütçesi ile kanıt sınıfının eşleşmesi (hüküm değil, denetim)

`research/tp_sonrasi_ters_20261109/data/ndx_trades.parquet` (botun NDX işlemleri, 2026-06-30 →
11-09). Aile başına: karar sayısı, toplam lot, işlem başına $ risk (|giriş − SL| × lot), toplam net $,
karar başına ortalama R, en kötü gün. Yanına defterdeki kanıt sınıfı yazılır. Seçim yok, sınama yok.

## EK-1 — MA-04 "Kaldıraçlı akış yoğunluğu" (MA-01/02/03 sonuçları görüldükten sonra, MA-04 verisi görülmeden yazıldı)

**İddia.** C3b (RSI2<10 → ilk yükselen kapanış, ≤5 gün) etkisi, kaldıraçlı/zorunlu akışın yoğun
olduğu endekste daha büyüktür. Defterdeki kesit sırası (TR-C3b: QQQ > SPY > IWM > EFA > DIA) bununla
uyumlu ama sonradan okundu. Öngörü: yarı iletken (SOXX, SMH; SOXL/SOXS akışı) > QQQ; savunmacı
sektörler (XLP, XLU; kaldıraçlı akış yok denecek kadar az) < QQQ.

**Veri.** Yahoo günlük, temettü düzeltmeli kapanış: QQQ, SOXX, SMH, XLP, XLU; 2010-01 → 2026-11
(kaldıraçlı ETF dönemi). Bu sektör serilerine bu projede daha önce bakılmadı.
**Kural.** c3b.py'deki QQQ adımıyla birebir: kapanışta RSI2<10 → kapanışta AL, ilk yükselen
kapanışta SAT (≤5 gün), tek pozisyon, 4 bp giriş + 2 bp/gece.
**Ölçü.** Oynaklık farkını ayıklamak için işlem getirisi / girişteki 20 günlük günlük oynaklık
(R birimi). Yan yana bp de verilir.
**Geçme ölçütü (hepsi):** (1) SOXX ve SMH'nin R ortalaması, ikisi de QQQ'nunkinden büyük;
(2) XLP ve XLU'nun R ortalaması, ikisi de QQQ'nunkinden küçük; (3) aynı sıralama 2010-17 ve
2018-26 yarılarının ikisinde de; (4) SOXX net bp > 0, ay-blok P ≥ %95.
Geçerse: mekanizma kanıtı B (işlem kuralı değil; araç seçimi için yön). Geçmezse X.

## EK-2 — MA-05 "Lot = kanıt sınıfı" bağımsız dönem sınaması (kullanıcı onayıyla; sonuçlara bakılmadan yazıldı)

Önceden bilinen: CK-05 özet satırı (DAYCOMBO 2024 +0,044R, REENTRY 2024 +0,077R; 2025 −0,030 / −0,073).
Bu sınamada yeni olan: iki aile birlikte, dolar ve gün ölçeğinde, canlı lotla (30) kuyruk ölçümü ve lot plasebosu.

**Not (yöntem):** tek tip lotta tavan yalnız ölçek değiştirir, günlük SR aynı kalır. MA-03'teki SR artışı
lotun zamanla değişmesinden geliyordu. Bu yüzden soru ikiye ayrılır.

**A — Aile tam lotu hak ediyor mu? (bağımsız dönem)** Veri: kural birebir yeniden üretim, Dukascopy NDX 1m,
2024 (hiç kullanılmamış) + 2025 (CK-03 dış örneklem); DAYCOMBO akışı + ona bağlı REENTRY, ikisi aynı anda
açık olabilir (canlı davranış). İşlem $ = R × 110 puan × lot (sabit 80/110 braket, 1,5 puan spread dahil).
Ölçüt "tam lotu hak eder": iki aile birlikte, 2024 ∪ 2025'te ort. R > 0 ve 5 günlük blok bootstrap
P(ort. R > 0) ≥ %95 **ve** iki yılın her birinde ort. R > 0. Geçmezse "kanıt sınıfı C kalır": lot
küçültmenin beklenen $ bedeli sıfırdan ayırt edilemez, kuyruk lotla doğru orantılı küçülür → MH-04 bu aile
için desteklenir. Yanında raporlanır: 30 / 10 / 5 lotta toplam $, %95 aralık, en kötü gün, en kötü 5 gün,
en derin düşüş. Seçim yok; tek kural, tek geometri.

**B — Lot zamanlaması beceri taşıdı mı? (canlı, örneklem içi plasebo)** Veri: MA-03 karar tablosu (NDX,
418 karar). Her ailenin kendi lotları o ailenin kararları arasında rastgele karıştırılır (5.000 çekiliş);
kararın R'si sabit. Ölçüt "beceri var": gerçek net $ plasebo dağılımının ≥ %95 yüzdeliğinde. Değilse lot
artışı getiri değil varyans kararıdır. Yanında: plasebo medyan net $, gerçek en kötü 5 günün yüzdeliği.

**C — Diğer semboller (betimsel):** bot_trades (Supabase, salt-okuma) tüm semboller 2026-06-29 →; aile ×
sembol × yön başına karar, risk payı, net $, ort. R, en kötü 5 gün. $/puan çarpanı işlemlerin kendi
net/(fiyat farkı × lot) medyanından ölçülür. Hüküm yok.
