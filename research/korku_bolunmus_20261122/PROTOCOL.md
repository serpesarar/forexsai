# KORKU gecesi × CAPREV çıkış dersleri (bölünmüş giriş, yarım tutuş, kâr kuralı) — 5 TUR — ÖN KAYIT

## Kullanıcı isteği (2026-11-22)
"KORKU'ya aynı çıkışı denemek. Bu stratejiyi 5 tur geliştirecek şekilde araştır, her turda bir gelişim ilerlet."

## Defter kontrolü (3. KURAL) — tekrar edilmeyecekler
- KC-02 (§2.77): **XU = giriş fiyatını aşan ilk 16:00 (CAPREV "kâr" kuralının KORKU karşılığı) X** (kaybedeni 5 güne kadar tutuyor, en kötü −1.644).
  Bu tur XU'yu tek başına yeniden SINAMAZ; yalnız yeni yapının (bölünmüş giriş / yarım tutuş) bileşeni olarak ve canlı XP tabanına karşı ölçülür.
- XL-01 (§2.96) limit girişi X; XD-01 destek limiti X; XG-06 (§2.97) teyitli kademe (kontrol noktasında artıysa ek) C; XG-07 derin stop X; XG-10 başabaşa kadar tutma X.
- **Yeni olan:** (1) zamanda bölünmüş, KOŞULSUZ ikinci yarım (ertesi 16:00); (2) ilk kontrol kapanışında zarardaysa payın yarısını kapatma (yarım tutuş);
  tabanın canlı paket olması (T30 + OPEX vetosu + XP).

## Ortak veri ve ölçü (her tur)
- Sinyal: canlı paket — TWAP(09:30–15:30 kapanışları) ≤ −%0,3 ∧ son saat (P16 < O15), OPEX'e 0/1/2 işlem günü kala açma; `xp_gelistir_20261119/src/veri.py`
  `entry_features` + `korku_evren_20261119` T30 hücresi, birebir. Giriş 16:00 barı açılışı + spread (ask), çıkışlar 16:00 barı açılışı (bid), finansman 1,756 bp/takvim günü.
- Beslemeler: Duka NDX 1m (birincil), MT5 NAS100 M30; kör MT5 US500 / US30 / US2000. KEŞİF ≤ 2021-10-31, TEST sonrası (önceki KORKU turlarıyla aynı kesim). Kesim 2026-11-05.
- Ölçü: sabit lotta işlem başı net bp, isabet, günlük kitap Sharpe, CVaR5 (en kötü %5 ort.), maks. düşüş. Taban = canlı paket (E0 + XP, tam tutuş).

## TUR 1 — KR-01: bölünmüş giriş × çıkış kuralı × yarım tutuş (sonuçlardan ÖNCE)
- Giriş: E0 (tamamı 16:00) | E2 (yarısı sinyal 16:00, yarısı ertesi işlem günü 16:00, koşulsuz).
- Çıkış (her yarı kendi girişinden): XP (sonraki 16:00 > önceki 16:00; ilk referans kendi giriş günü 16:00 bid) | XU (16:00 bid ≥ kendi girişi). En geç kendi girişinden 5. işlem günü.
- Yarım tutuş h: 1,0 | 0,5 (yarının ilk kontrol 16:00'ında çıkış koşulu yoksa ve bid < giriş → yarısı orada kapanır).
- 8 hücre (E0-XP-h1 = taban). Stop yok (canlı ile aynı; acil %13 hiçbir geçmiş işlemi kesmiyor).
- Seçim: KEŞİF havuzu (Duka + MT5 4) — CVaR5 ≥ 1,2 × taban CVaR5 olan hücreler arasında taban üstü ort. farkı en yüksek **1 hücre** (taban hariç).
- **B:** TEST'te (i) Duka NDX ve MT5 NAS100 fark > 0; (ii) TEST havuzu (5 besleme) ay bloklu P ≥ 0,95; (iii) kör 3'ün ≥ 2'sinde fark > 0; (iv) Duka NDX Sharpe > taban;
  (v) Duka NDX ve MT5 NAS100 CVaR5 ≥ 1,5 × taban. C: (i) geçer biri düşer; X: (i) düşer.

## TUR 1 sonucu (değiştirilmez): **X**
KEŞİF'te 7 hücrenin 7'si tabanın altında (E2 −31…−40, yarım tutuş −10…−11, E0_XU_h1 −1,3 ama CVaR5 −757). Seçilen E0_XP_h0.5: TEST Duka −17,4, MT5 NAS100 −17,8,
CVaR5 −513 → −451. **Ders:** KORKU kenarı giriş gecesinde; ikinci yarıyı ertelemek o geceyi kaçırır, yarım tutuş ertesi günün dönüşlerini keser.

## TUR 2 — KR-02: ilk XP kontrolünde (D1 16:00) tutuş şartı (TUR 1'den SONRA, TUR 2 sonuçlarından ÖNCE)
Giriş ve gece aynen (E0, tam lot). D1 16:00'da XP çıkmadıysa (bid ≤ giriş günü 16:00) pozisyon ancak şart tutarsa XP ile sürer; tutmazsa D1 16:00'da kapanır.
- Şartlar (D1 16:00'da bilinir): S1 D1 zararı (bid/ask − 1) ≤ −a, a ∈ {50; 100; 150; 200} bp → kapat; S2 VIX D1 kapanışı / girişte bilinen dünkü VIX − 1 ≥ v, v ∈ {0,05; 0,10; 0,20} → kapat;
  S3 D1 kapanışı seans aralığının alt q'su, q ∈ {0,15; 0,25} → kapat; S4 diğer üç ABD endeksinden D1 günlük getirisi ≤ −%1 olan ≥ k, k ∈ {2; 3} → kapat;
  S5 D1 seans dibi < giriş günü seans dibi → kapat. Tek koşullu 14 hücre + farklı aileden ikili VEYA birleşimler.
  (XG-02 09:30/04:00 eşikleri ve 1–3 günlük tavanı sınamıştı, X; bu tur karar anı olarak yalnız D1 16:00'ı ve bağlam şartlarını kullanır.)
- Anatomi (betimleyici): D1'de tutulan işlemler ÇÖKÜŞ (son net ≤ −300 bp) / DÖNÜŞ (son net > 0) / SÜRÜNME; giriş ve D1 özellikleri, AUC, iki dönem.
- Seçim ve B: TUR 1 ile aynı (KEŞİF: CVaR5 ≥ 1,2 × taban, en yüksek fark, 1 hücre; TEST (i)–(v)).

## TUR 2 sonucu (değiştirilmez): **X**
68 hücrenin hepsi KEŞİF'te tabanın altında (en iyi S3_0,15 −4,1); seçilen S3_0,15 TEST Duka −10,4, MT5 −10,5, kör üçü eksi. Kuyruk %5'in tamamı D2–D5 çıkışlı (XP'nin
tuttuğu işlemler). Anatomi D1'de tutulanlar (KEŞİF 26 ÇÖKÜŞ / 174, TEST 33 / 343): D1 zararı AUC 0,24 / 0,11 (ters yönde 0,76 / 0,89), genişlik 0,71 / 0,78, VIX tırmanışı
0,76 / 0,64. **Ders:** çöküş D1'de tanınıyor ama derin D1 zararlıları ortalamada güçlü dönüyor; kesmek dönüşü öldürüyor.

## TUR 3 — KR-03: D1'de koşullu ekleme (TUR 2'den SONRA, TUR 3 sonuçlarından ÖNCE)
Giriş, gece ve XP aynen. D1 16:00'da XP çıkmadıysa ve D1 zararı ≤ −a bp ise **ve çöküş imzası yoksa** (genişlik br < 2 ∧ VIX tırmanışı < v) D1 16:00 ask'ında
u birim EK alınır. Ek birim ana pozisyonla aynı anda kapanır (ana XP çıkışı; ilk referans D1 16:00 bid). a ∈ {50; 100; 150}, u ∈ {0,5; 1,0}, v ∈ {0,10; ∞ (VIX şartı yok)},
genişlik şartı {var; yok} → 24 hücre. Sonuç işlem başına (ana + ek) net bp; Sharpe kitap.
- Seçim (KEŞİF): Sharpe > taban ∧ CVaR5 ≥ 1,5 × taban arasında taban üstü fark en yüksek 1 hücre.
- B: TEST (i) Duka NDX ve MT5 NAS100 fark > 0; (ii) havuz P ≥ 0,95; (iii) kör ≥ 2/3; (iv) Duka NDX Sharpe > taban; (v) Duka NDX ve MT5 CVaR5 ≥ 1,5 × taban;
  (vi) eklenen birimlerin kendi ortalaması iki dönemde de > 0.

## TUR 3 sonucu (değiştirilmez): **B**
Seçilen A50_u1,0 (D1 16:00 zararı ≤ −50 bp → 1 birim ek, ana XP'de birlikte çık; VIX/genişlik şartı yok). TEST: Duka +22,1, MT5 NAS100 +20,7, kör +21,2/+16,5/+6,7,
P 1,00, Duka Sharpe 1,97 → 2,10, CVaR5 −513 → −666 (sınır −770), ek birim KEŞİF +74,6 (136) / TEST +67,7 (217). Bedel: maks. düşüş Duka −1.226 → −1.966, US2000 −1.512 → −2.508.

## TUR 4 — KR-04: dokunulmamış beslemeler + kart ölçütleri (TUR 3'ten SONRA, TUR 4 sonuçlarından ÖNCE)
Donmuş A50_u1,0, hiçbir parametre değişmez.
- Dokunulmamış beslemeler: **EET30 ve NQ** (KORKU KC-01'de yalnız XP için kullanıldı; bu ekleme kuralı orada hiç ölçülmedi), tüm dönem.
- Kart ölçütleri (Duka NDX tüm dönem, mutlak net bp, işlem = ana + ek): (1) ≥ 150; (2) ort > 0 ∧ P(EV>0) ≥ %90; (3) kronolojik iki yarı ≥ 0 ve iki yarıda da fark > 0;
  (4) spread ×1,5 stresinde fark > 0; (5) icra: ek birim D1 16:00 + 1 bar açılışından alınırsa fark > 0; (6) tek pozisyon (ana + ek bir pozisyon sayılır) ile fark > 0.
- **B:** EET30 ve NQ'da fark > 0 ve CVaR5 ≥ 1,5 × taban, ve (1)–(6). C: biri düşer. X: EET30 ve NQ ikisinde de fark ≤ 0.

## TUR 4 sonucu (değiştirilmez): **B**
Dokunulmamış EET30 +23,8 bp (CVaR5 −395 → −554, sınır −593), NQ +6,2 (−424 → −623, sınır −636; Sharpe 1,72 → 1,40, maks. düşüş −1.241 → −2.353). Duka NDX tüm dönem
+20,4, kart 6/6: n 324, ort +94,7, P 1,00, yarılar +104/+85 (fark +23/+18), spread ×1,5 +20,3, sonraki bar +20,0, tek pozisyon +18,2 (253). Ek oranı %25.

## TUR 5 — KR-05: ek birimin çıkışı (düşüşü azaltma; TUR 4'ten SONRA, TUR 5 sonuçlarından ÖNCE)
Ekleme koşulu donmuş (D1 zararı ≤ −50 bp). Ek birimin çıkışı: Y1 ana ile birlikte (TUR 3); Y2 tek gece (D2 16:00); Y3 kendi XP'si (ilk referans D1 16:00 bid) en çok 2 gün;
Y4 D2 16:00'da kârdaysa çık, değilse ana ile. Ek büyüklüğü u ∈ {0,5; 1,0} → 8 hücre.
- Seçim (yalnız KEŞİF Duka + MT5 4; EET30/NQ kullanılmaz): KEŞİF farkı ≥ TUR 3 hücresinin yarısı (≥ +9,2) olanlar arasında KEŞİF havuz maks. düşüşü en küçük 1 hücre.
- **B:** TEST (i) Duka ve MT5 NAS100 fark > 0; (ii) havuz P ≥ 0,95; (iii) Duka ve MT5 NAS100 maks. düşüşü TUR 3 hücresininkinden küçük; (iv) EET30 ve NQ tüm dönem fark > 0;
  (v) Duka Sharpe > taban. C: (i) geçer biri düşer. X: (i) düşer.
