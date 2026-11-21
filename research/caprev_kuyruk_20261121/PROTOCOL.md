# CAPREV kâr çıkışı — kuyruk (çöküş) anatomisi ve tutuş koruması — ÖN KAYIT (2026-11-21, sonuçlardan önce)

## Kullanıcı isteği
"Kâr çıkışında en kötü %5 −250'den −475 bp'ye çıkıyor. Girişten sonra büyük çöküş gelen işlemlerle gelmeyenlerin farkını derin
analiz et; ön kayıt hükmünü onaylatacak bir yapıya taşı."

## Çıkış noktası (§2.107 CD-04)
X_5_3.0_kar (kârlı ilk seans kapanışında çık, en çok D5, felaket stopu 3×dvol): Duka NDX %57→%89, +48→+106 bp, CVaR5 −250→−475;
DAX +38→+21, CVaR5 −258→−731 → X. 2026-11-21'den beri NDX'te CANLI (kullanıcı kararı, kartsız). Kuyruk işlemlerinin hepsi D0
kapanışında zararda olup tutulan ve tutuş sırasında 3×dvol stopuna giden işlemler (ön inceleme: yalnız sıralama, özellik bakılmadı).

## Veri ve örneklem (CD ile aynı, `caprev_derin_20261120/cache/olaylar.parquet` olay tanımı)
- KEŞİF: günlük vekil 1990–2015, ^NDX ^GSPC ^DJI ^RUT ^GDAXI (1.264 olay). Seçim yalnız burada.
- TEST: Duka NDX 1m (birincil), Duka DAX 1m, MT5 NAS100 M30, kör MT5 US500/US30/US2000 M30, günlük vekil 2016–26 (5 endeks).
- Kapanış s (s = 0…5) bilgisi: işlemin kendi beslemesinin s kapanış fiyatı (bid); gün aralığı/dibi endeksin günlük serisinden;
  VIX kapanışı: ABD endekslerinde s günü, DAX'ta s−1 günü (DAX 17:30 Berlin kapanışında günün VIX kapanışı bilinmez); VIX3M aynı kural;
  genişlik (diğer ABD endekslerinden s günü ≤ −%1,5 olanlar) ABD'de s günü, DAX'ta s−1 günü (dört ABD endeksi).

## A — anatomi (betimleyici)
Tutulan işlemler (D0 kapanışı < giriş) üç sınıf: **ÇÖKÜŞ** (tutuşta 3×dvol stopu ya da son çıkış ≤ −2×dvol), **DÖNÜŞ** (kârla çıktı),
**SÜRÜNME** (diğer). (1) Giriş özellikleri (CD'nin 20 + 3 kategorisi) ÇÖKÜŞ vs diğer: KEŞİF ve TEST'te fark + permütasyon p, AUC;
(2) D0 kapanışı ve D1 kapanışı yol özellikleri (aşağıdaki z, dz, clv, alt dip, vixchg, vix, genişlik, vade) aynı karşılaştırma.

## G — tutuş koruması (karar anı: her seans kapanışı, işlem hâlâ zararda ve stop olmamışken; çıkış o kapanış bid'i)
Tek koşullu hücreler:
- G1 zarar kesme: z_s = (kapanış/giriş − 1)/dvol ≤ −a, a ∈ {0,5; 1,0; 1,5; 2,0}
- G2 VIX tırmanışı: VIX_s / (girişte bilinen dünkü VIX) − 1 ≥ v, v ∈ {0,10; 0,20; 0,30}
- G3 VIX seviyesi: VIX_s ≥ L, L ∈ {30; 35; 40}
- G4 alt dip (s ≥ 1): s günü dibi < s−1 günü dibi
- G5 zayıf kapanış: (C−L)/(H−L) ≤ q, q ∈ {0,15; 0,25}
- G6 genişlik: diğer ABD endekslerinden s günü ≤ −%1,5 olan sayısı ≥ k, k ∈ {2; 3}
- G7 vade eğrisi: VIX_s/VIX3M_s ≥ t, t ∈ {1,05; 1,10} (eksikse koşul yok)
- G8 sekmeme (s ≥ 1): kapanış_s < kapanış_{s−1}
- G9 tutuş kısaltma: zararda tutuş en çok M ∈ {1; 2; 3} gün (CD ızgarasıyla aynı aile, referans)
Çift hücreler: tek hücrelerin farklı aileden ikili VEYA birleşimleri.

Seçim (yalnız KEŞİF havuzu, beş endeks birlikte): uygun = isabet ≥ taban + 10 puan **ve** CVaR5 ≥ 1,5 × taban CVaR5 (taban = canlı kural,
D0 çıkışı, 1×dvol). Uygunlar arasında taban üstü ortalama net bp farkı en yüksek **2 hücre** (en az biri tek koşullu) dondurulur.
Hiçbiri uygun değilse eşik 2,0 × taban CVaR5'e gevşer (yazılır).

## Geçme (dondurulan her hücre için; CD-X ile aynı + kuyruk şartı)
- **B:** (i) Duka NDX'te ve Duka DAX'ta taban üstü fark > 0 ve isabet tabandan yüksek; (ii) havuz (Duka NDX + Duka DAX + günlük 2016–26 beş
  endeks) eşli fark ay bloklu bootstrap P ≥ 0,975 (Bonferroni 2); (iii) kör üç MT5 endeksinin ≥ 2'sinde fark > 0; (iv) Duka NDX kitap Sharpe
  tabandan yüksek; (v) Duka NDX ve DAX'ta CVaR5 taban CVaR5'inin 2 katından kötü değil; (vi) Duka NDX'te CVaR5 korumasız X_5_3.0_kar'dan iyi.
- **C:** (i) geçer, diğerlerinden biri düşer. **X:** Duka NDX ya da DAX'ta fark ≤ 0.
- Ölçü: sabit lotta net bp (spread + 1,756 bp/takvim günü finansman), isabet (net > 0), kitap Sharpe (iş günü serisi), CVaR5.
- Betimleyici: korumalı hücrenin korumasız X_5_3.0_kar'a göre farkı (NDX), yıllara göre kuyruk, 2020-Şubat/Mart davranışı.
- Canlı değişiklik yalnız B'de ve kullanıcıya bildirilerek; sonuçlardan sonra yazılan her ek EK-n başlığıyla eklenir, hükmü değiştirmez.

## KQ-01 sonucu (ana koşu, değiştirilmez)
Seçilen G1_z0.5|G3_vix40 ve G1_z0.5|G7_term1.1 → **C** (yalnız (v) düştü: DAX CVaR5 −520 vs sınır −516). Anatomi (betimleyici):
çöküşü girişte zayıf (en iyi TEST AUC 0,68 vix_sma10), **D0 kapanışında** güçlü ayırt eden iki işaret üç örneklemde de tekrarlıyor:
z_0 (D0 kapanış zararı/dvol; AUC 0,27–0,34) ve clv_0 (D0 kapanışının gün aralığındaki konumu; AUC 0,30–0,44). Kuyruk stoplarının
çoğu D1–D4'te. ⚠️ Bu tanımlar TEST anatomisi görüldükten SONRA seçildi → KQ-02'ye dokunulmamış besleme şartı eklenir.

## KQ-02 — tutuş uygunluğu + stop takvimi (yeni tanım; KQ-01 sonuçlarından SONRA, KQ-02 sonuçlarından ÖNCE)
Hücre = D0 gün içi stop c0 ∈ {1,0; 3,0}×dvol × D0 sonrası stop c1 ∈ {1,5; 2,0; 3,0}×dvol (girişten) × D0 kapanışı tutma şartı
[z_0 > −a, a ∈ {0,5; 0,75; 1,0; ∞}] ∧ [clv_0 > q, q ∈ {0; 0,15; 0,25}] (şart tutmazsa D0 kapanışında çık) × s ≥ 1 kapanış koruması
∈ {yok; G8 sekmeme; G2 vixchg ≥ 0,10} → 216 hücre. Kural "kâr", en çok D5 (CD-04). clv_0 eksikse şart yok.
- Seçim (yalnız KEŞİF, KQ-01 ile aynı): isabet ≥ taban + 10 puan ∧ CVaR5 ≥ 1,5 × taban CVaR5; en yüksek taban üstü ortalama fark
  **2 hücre** dondurulur (yoksa 2,0 ×).
- Geçme: KQ-01'in (i)–(vi) ölçütleri **ve (vii) dokunulmamış beslemeler**: EET30 ve NQ (NDX, bu çıkış ve yol özellikleriyle hiç
  ölçülmedi) ile MT5_GER40 (DAX M30, 2016+) üçünde de taban üstü fark > 0 ve CVaR5 tabanın 2 katından kötü değil.
  B = (i)–(vii) hepsi; C = (i) geçer, biri düşer; X = Duka NDX ya da DAX'ta fark ≤ 0.

## KQ-02 sonucu (ana koşu, değiştirilmez)
Seçilen c0 3,0 / c1 1,5 / a 0,5 / q 0 / G2 vixchg ≥ 0,10 ve c0 3,0 / c1 3,0 / a 0,5 / q 0,25 / G2 → **C**. Birincide yalnız (vii) düştü:
NDX taze beslemeleri geçti (EET30 +15,0, NQ +14,6), DAX taze beslemesi MT5_GER40 −20,9 (korumasız kâr çıkışı orada −31,2).
İkincide ayrıca (v) DAX.

## KQ-03 — NDX kapsamı (KQ-02 sonuçlarından SONRA, KQ-03 sonuçlarından ÖNCE)
⚠️ Kapsam daraltması DAX'ın düştüğü görüldükten sonra yapıldı. Gerekçe sonuçtan bağımsız değildir; mekanizma CD EK-1'de var
(D0 zararlıların 5 günde toparlanması NDX %77, DAX %61). Canlı kâr çıkışı 2026-11-21'den beri zaten yalnız NDX'te. DAX bacağı canlı tabanda kalır.
- Hücre ızgarası KQ-02 ile aynı (216) + korumasız X_5_3.0_kar.
- Seçim: yalnız KEŞİF ABD endeksleri (^NDX ^GSPC ^DJI ^RUT 1990–2015), KQ-02 kuralıyla (isabet ≥ taban + 10 ∧ CVaR5 ≥ 1,5 × taban), 2 hücre.
- **B (NDX kapsamı):** (i) Duka NDX ve MT5 NAS100'de fark > 0 ve isabet > taban; (ii) havuz (Duka NDX + günlük 2016–26 NDX/GSPC/DJI/RUT)
  ay bloklu P ≥ 0,975; (iii) kör MT5 US500/US30/US2000'in ≥ 2'sinde fark > 0; (iv) Duka NDX Sharpe > taban; (v) Duka NDX ve MT5 NAS100
  CVaR5 ≥ 2 × taban; (vi) Duka NDX CVaR5 korumasız kâr çıkışından iyi; (vii) taze EET30 ve NQ'da fark > 0 ve CVaR5 ≥ 2 × taban.
- **Canlıya alma kartı (CLAUDE.md 2. kural), B hücresi için**, ABD endeks ailesi havuzunda (Duka NDX + MT5 US500/US30/US2000; kural her
  endekste kendi verisiyle) mutlak net bp ile: (1) ≥ 150 işlem; (2) ort > 0 ve ay bloklu P(EV>0) ≥ %90; (3) kronolojik iki yarı ≥ 0;
  (4) spread ×1,5 stresinde (maliyet +%50) ort > 0; (5) icra: giriş zaten tetik barı bitişindeki SONRAKİ barın açılışı + gerçek spread
  (cr_motor px_at; bar kapanışı değil) → yapısal olarak sağlanır, iyimser (tetik kapanışı) ile fark raporlanır; (6) aynı anda tek pozisyon
  (aile içinde, tarih sırasıyla, açıkken gelen tetik atlanır) ile ort > 0.
- C / X tanımları KQ-02 ile aynı (X = Duka NDX'te fark ≤ 0).

## KQ-03 sonucu (değiştirilmez)
c03.0_c11.5_a0.5_q0.0_G2_vixchg0.1 → B, kart 6/6 LIVE; korumasız kâr çıkışı C (taze NQ CVaR5). 2026-11-21 canlıya bağlandı (5b9458f2).
Kalan şüphe: NDX kapsamı DAX sonucu görüldükten sonra seçildi.

## KQ-04 — kapsam kuralı + donmuş kural, HİÇ KULLANILMAMIŞ endekslerde (KQ-03'ten SONRA, KQ-04 sonuçlarından ÖNCE)
- **Kapsam kuralı (yalnız KEŞİF'ten, yapısal):** bir endeks kâr çıkışına uygundur ⇔ kendi 1990–2015 günlük vekil CAPREV olaylarında, D0 kapanışında
  zararda olanların 5 işlem günü içinde girişe dönme oranı ≥ 0,65. (KEŞİF değerleri ön incelemede: NDX 0,73, GSPC 0,72, DJI 0,68, RUT 0,66,
  GDAXI 0,60 → eşik DAX ile ABD'yi ayıran 0,65; DAX'ın bu ölçüde en düşük olduğu KEŞİF'te de görülüyor.) Bu oran korumanın sonucunu kullanmaz.
- **Örneklem:** CAPREV araştırmalarının hiçbirinde kullanılmamış dört günlük endeks: ^FTSE, ^STOXX50E, ^N225, ^HSI (yfinance,
  `research/kasa_trend_20261028/data/`), açılışı olmayan yıllar atılır. Kural günlük vekil (cr_gunluk), dünkü ABD VIX ≥ 18,4; ABD dışı olduğundan
  s ≥ 1 VIX koruması s−1 günü VIX kapanışıyla (DAX kuralı). Donmuş hücre: KQ-03 seçimi, hiçbir parametre değişmez.
- **Sınama:** her endeksin 2016–2026 dönemi (birincil); 1990–2015 ikincil (bu endeksler seçimde hiç yoktu, o dönem de dışarıda).
- **B (kapsam + kural doğrulandı):** kapsam içi (oran ≥ 0,65) dokunulmamış endeksler havuzunda 2016–26: (i) taban üstü ortalama fark > 0 ve ay bloklu
  P ≥ 0,90; (ii) kapsam içi endekslerin en az yarısında fark > 0; (iii) havuz CVaR5 ≥ 2 × taban CVaR5; (iv) kapsam dışı endeks varsa havuz farkı kapsam
  içinden küçük (kuralın yönü). Kapsam içi endeks yoksa hüküm "sınanamadı". C: (i) geçer, biri düşer. X: (i) fark ≤ 0.

## KQ-04 sonucu (değiştirilmez): **C**
Dört dokunulmamış endeksin dördü de kapsam içi (toparlanma 0,66–0,74). Kapsam içi havuz 2016–26 (298 işlem): korumalı fark +0,6 bp, P 0,54 → (i) düştü;
(ii) 3/4 artı, (iii) CVaR5 −430 vs taban −227 (1,9×) geçti, (iv) kapsam dışı yok. Korumasız kâr çıkışı aynı havuzda +22,2 bp, P 0,983, CVaR5 −596 (2,6×);
1990–2015'te dört endeksin dördünde artı (+25…+32). Okuma: "kâra kadar tut" kenarı genelleşiyor, KQ-03 koruması genelleşmiyor; kuyruk kâr çıkışının yapısal bedeli.

## KQ-05 — kısmi tutuş (KQ-04 sonuçlarından SONRA, KQ-05 sonuçlarından ÖNCE)
⚠️ Fikir KQ-04'te korumasız kâr çıkışının kenarı genelleştirip kuyruk ölçütünü (2×) ~1,3 katla kaçırdığı görüldükten sonra kuruldu.
- Yapı: D0 kapanışında pozisyon zarardaysa ve stop olmadıysa payın (1 − h)'si D0 kapanışında kapanır, h'si hücre kuralıyla tutulur.
  h ∈ {0,5; 1,0} × KQ-02'nin 216 hücresi + korumasız X_5_3.0_kar → 434 hücre (h = 1 KQ-03 ile aynı).
- Seçim: yalnız KEŞİF ABD endeksleri 1990–2015, KQ-03 kuralıyla (isabet ≥ taban + 10 ∧ CVaR5 ≥ 1,5 × taban; en yüksek fark), 2 hücre.
  İsabet: işlem net > 0 (iki parçanın toplamı).
- **B:** KQ-03'ün (i)–(vii) NDX ölçütleri **ve** KQ-04 dokunulmamış havuzunda (FTSE/Stoxx/Nikkei/HSI 2016–26) fark > 0 ∧ P ≥ 0,90 ∧ CVaR5 ≥ 2 × taban
  **ve** canlıya alma kartı 6/6 (ABD aile havuzu). C: NDX (i) geçer, biri düşer. X: Duka NDX fark ≤ 0.

## KQ-05 sonucu (değiştirilmez): **C**
Seçilen c0 3 / c1 3 / tutma şartı yok / VIX +%10 / h 0,5 ve aynısı c1 2: NDX ölçütleri (i)–(vii) ve kart 6/6 geçti (Duka NDX +78,1 bp, isabet %78,
Sharpe 1,12, CVaR5 −394), dokunulmamış havuz +3,3 / +3,6 bp (P 0,71 / 0,73) → düştü. Betimleyici (seçilmedi, KEŞİF CVaR5 −705 uygunluk dışı):
korumasız h 0,5 → Duka NDX +79,5 / −405, EET30 +28,5 / −437, NQ +20,6 / −417, dokunulmamış havuz +8,7 (P 0,909) / CVaR5 −471 (sınır −454).
**Araştırma burada kapanır:** dokunulmamış endeksler üç turda kullanıldı; yeni tur seçim gürültüsüne dönüşür. Temiz kalan tek kanıt ileri canlı veri.

## KQ-06 — farklı giriş yeri + büyük çöküşe karşı tutuş şartı, korumasız kâr çıkışı (kullanıcı isteği; KQ-05'ten SONRA, KQ-06 sonuçlarından ÖNCE)
Kullanıcı: "korumasızı daha fazla araştır, farklı bir işleme giriş yeri ya da en kötü/büyük ölçekli düşüşlerden koruyacak bir strateji ara."
- **Çıkış sabit:** kâr kuralı (ilk kârlı seans kapanışı, ilk kontrol kapanışından itibaren en çok 5 kontrol), felaket stopu ortalama giriş × (1 − 3·dvol), VIX koruması YOK.
- **Giriş (E):** E0 canlı tetik (günlük vekilde min(açılış, önceki dip)); E1 D0 seans kapanışında al; E2 bölünmüş (yarısı E0, yarısı D0 kapanışı, iki ayrı yarım pozisyon);
  E3a / E3b E0'ın 0,5 / 1,0 × dvol altına D0 boyunca limit (dolmazsa işlem yok = 0); E4 D1 açılışında al.
- **Tutuş şartı (U, girişte bilinen; tutmazsa canlı taban işlemi: 1×dvol stop, D0 çıkışı):** U0 hepsi; U1 kapanış > SMA200 (dün); U2 dünkü VIX < 30;
  U3 252 gün zirvesinden düşüş > −%15.
- **Tutuş payı:** h ∈ {0,5; 1,0} (ilk kontrol kapanışı zarardaysa 1 − h orada kapanır). → 6 × 4 × 2 = 48 hücre.
- **Seçim:** yalnız KEŞİF ABD endeksleri 1990–2015, günlük vekil; KQ-03 kuralı (isabet ≥ taban + 10 ∧ CVaR5 ≥ 1,5 × taban; en yüksek fark), 2 hücre.
- **Yeni dokunulmamış piyasalar (bu çalışmada indirildi, hiçbir CAPREV turunda yok):** ^FCHI ^AEX ^SSMI ^IBEX ^GSPTSE ^AXJO ^KS11 ^BVSP ^TWII ^MXX (yfinance
  günlük, açılışı olmayan yıllar atılır), 2000–2026; KQ-04 kapsam kuralı (kendi 1990–2015 toparlanması ≥ 0,65; veri yoksa 2000–2009) uygulanır.
- **B:** (a) NDX: Duka NDX ve MT5 NAS100 fark > 0 ∧ isabet > taban; havuz (Duka NDX + günlük 2016–26 ABD 4) P ≥ 0,975; Duka NDX Sharpe > taban; Duka NDX ve MT5
  CVaR5 ≥ 2 × taban; EET30 ve NQ fark > 0 ∧ CVaR5 ≥ 2 × taban (E4 seçilirse 1m beslemelerde D1 açılış = D1 09:30 ilk bar); (b) yeni piyasalar kapsam içi havuzunda
  fark > 0 ∧ P ≥ 0,90 ∧ CVaR5 ≥ 2 × taban; (c) kart 6/6. C: (a)'nın ilk şartı geçer, biri düşer. X: Duka NDX fark ≤ 0.

## KQ-06 sonucu (değiştirilmez)
Seçilen **E2_U0_h0.5** (yarısı tetikte, yarısı D0 kapanışında; ilk kontrol kapanışı zarardaysa her yarının yarısı orada kapanır): **C** — yalnız (a) kör MT5 ≥ 2/3 düştü
(US500 −23,1, US30 −18,6, US2000 −3,1). Geçenler: Duka NDX +28,3 (ort +76,2, isabet %73, Sharpe 0,71 → 1,51, CVaR5 −253 vs taban −250), MT5 NAS100 +32,4 / −247,
EET30 +28,2 / −261, NQ +26,7 / −256, havuz P 1,00, yeni piyasalar kapsam içi (FCHI/SSMI/IBEX/BVSP) +32,6 P 0,998 CVaR5 −473 (sınır −678), kart 6/6 LIVE.
E4_U3_h1.0: yeni piyasalarda −2,8 (P 0,42) → B olamaz; 1m beslemelerde E4 hesaplanmadı (NDX ölçütleri taban ile dolduruldu, hüküm yazılmaz).
Betimleyici (EK, hükmü değiştirmez): E2_U0_h0.5 yeni 10 piyasanın 10'unda artı (kapsam dışı AEX/GSPTSE/KS11/TWII/MXX/AXJO dahil, +4…+59);
kör CFD açığı D0 kapanışı yarısından (MT5 US500/US30 E1 −57/−43, aynı endeks günlük vekil +30/+34); DAX'ta E2 −8,8 (Duka) / −1,3 (MT5) → DAX tabanda kalır;
E2_U0_h1.0 (seçilmedi) NDX +50,8 / CVaR5 −342 / isabet %81.
