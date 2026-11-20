# CAPREV derin — SL/TP kümeleme, SL eleme, yüksek isabetli çıkış — ÖN KAYIT (2026-11-20, sonuçlardan önce)

## Kullanıcı isteği
"Bu strateji üzerinde daha fazla ayrım yaparak TP ve SL'leri gruplaştır, SL'leri elemeye çalış; kâr oranıyla beraber daha yüksek isabet."

## Önceki tur (§2.106 CR-01…05) ve fark
CR-05: 12 giriş özelliği, Duka KEŞİF ≈ 38 işlem → seçim gürültüsü, C/X. CR-03: XP stopsuz isabet %78, +102 bp ama DAX −19 → C.
Defter: TLT↓ × CAPREV C (DB-02, bağımsız dönem yok), VXN C (DB-03), fitil X (FK-01), artan VIX tanımsız (DB-04), CK2-03 C.
**Bu turun yöntemi tersine çevrilmiş örneklem:** özellikler ve çıkışlar **1990–2015 günlük vekil havuzunda** (5 endeks, ≈ 1.000 olay)
keşfedilip dondurulur; sınama **canlı kuralın gerçek 2018–26 işlemlerinde** (Duka NDX 1m, Duka DAX 1m, MT5 beslemeleri) ve
2016–26 günlük vekilde yapılır. 2018–26 işlemlerine seçimde hiç bakılmaz.

## Veri
- **KEŞİF havuzu:** günlük vekil (`caprev_tpsl_20261120/src/cr_gunluk.py` kuralı: stres ∧ dünkü VIX ≥ 18,4 ∧ Pzt–Per ∧ gün dibi < önceki dip;
  giriş min(açılış, önceki dip); stop 1×dvol; D0 kapanışı) — ^NDX, ^GSPC, ^DJI, ^RUT, ^GDAXI, 1990-01 → 2015-12, açılışı olmayan yıllar atılır.
- **TEST:** (a) Duka NDX 1m 2018–26 (birincil, canlı kural birebir); (b) Duka DAX 1m 2018–26 (canlı ikinci bacak); (c) MT5 NAS100 M30
  (besleme teyidi); (d) kör MT5 US500 / US30 / US2000 M30; (e) günlük vekil 2016–26, beş endeks.
- Ölçü sabit lotta net bp (spread + 1,756 bp/takvim günü finansman), isabet (net > 0), kitap Sharpe, en kötü %5 ortalaması (CVaR5).

## Aile F — günlük bağlam filtresi (gün başında bilinir)
Özellikler (ilgili endeksin kendi günlük serisinden, yalnız önceki günler; VIX önceki takvim günü):
sma200 (C/SMA200 − 1), sma50, dd252 (252 gün zirvesinden), r1z = r1/dvol, r5z = r5/(dvol·√5), volx = dvol/dvol60, düşüş serisi
(art arda eksi kapanış), stres10 (son 10 günde stres günü sayısı), önceki olaydan bu yana gün (≤ 60), VIX, VIX 252g yüzdeliği,
VIX 1g ve 5g değişimi, VIX/SMA10(VIX), VIX/VIX3M (2006-07+), günlük RSI2, dünkü kapanış konumu (C−L)/(H−L), dünkü aralık/(C·dvol),
TLT 1g getirisi (2002-07+), genişlik (diğer ABD endekslerinden dün stresli olanların sayısı), vadeye işlem günü, hafta günü,
ay sonuna ≤ 2 işlem günü.
- Kesimler KEŞİF havuzunda tertil (sürekli) ya da kategori. İki biçim: **D** = en kötü tertili/kategoriyi at; **K** = yalnız en iyi tertili tut.
- Skor: KEŞİF'te kalan işlemlerin ortalama net bp farkının t değeri ((ort_kalan − ort_tümü)/(sd_kalan/√n_kalan)). En yüksek skorlu
  **3 hücre** (farklı özellikler) dondurulur.
- Çok değişkenli **M**: aynı özelliklerle (standartlaştırılmış, eksik = KEŞİF medyanı) L2 lojistik (C 0,5) ve GBM (200 ağaç, derinlik 2,
  lr 0,05, subsample 0,8, random_state 0) KEŞİF'te "net > 0" hedefiyle eğitilir; filtre = tahmini en kötü üçte biri at (eşik KEŞİF %33'lüğü).
  Ayar yapılmaz.

## Aile X — yüksek isabetli çıkış (girişten sonra)
Hücre = en çok tutuş M ∈ {1, 2, 3, 5} işlem günü × felaket stopu c ∈ {yok (acil %7), 2,0, 3,0} × dvol × kural:
**kâr** (D0 kapanışından itibaren ilk kârlı seans kapanışında çık) ya da **yükselen** (D0 kârdaysa çık, değilse ilk "kapanış > önceki
kapanış" gününde çık) → 24 hücre. M dolunca son kapanışta çıkılır.
- Seçim: KEŞİF havuzunda isabeti tabandan ≥ 10 puan yüksek hücreler arasında net bp farkı en yüksek **2 hücre** dondurulur.

## Geçme (F, M, X için aynı)
- **B:** (i) Duka NDX'te ve Duka DAX'ta fark > 0 **ve** isabet tabandan yüksek; (ii) havuz (Duka NDX + Duka DAX + günlük 2016–26 beş endeks)
  eşli fark ay bloklu bootstrap P ≥ 0,983 (Bonferroni 3; X için 2 → 0,975); (iii) kör üç MT5 endeksinin ≥ 2'sinde fark > 0; (iv) Duka NDX kitap
  Sharpe artar; (v) yalnız X: CVaR5 tabanınkinin 2 katından kötü değil.
- **C:** (i) geçer, diğerlerinden biri düşer. **X:** Duka NDX ya da Duka DAX'ta fark ≤ 0.
- M: ek olarak Duka NDX ve DAX'ta AUC raporlanır (≥ 0,55 beklenir; hüküm filtre farkıyla).
- Betimleyici: F × X birleşimi (dondurulan en iyi filtre + en iyi çıkış); SL / TP / ZK sınıflarının özellik profili (KEŞİF ve TEST ayrı);
  X hücrelerinin canlı KORKU/KSG/C3b geceleriyle örtüşmesi.
- Canlıya bağlama bu çalışmadan VERİLMEZ. Sonuçlardan sonra yazılan her ek "EK-n" başlığıyla eklenir ve hükmü değiştirmez.

## EK-1 (ana sonuçlardan SONRA yazıldı; hükmü değiştirmez)
Ana koşu: F en iyi "dünkü aralık üst tertil" C, diğer F X; M (lojistik, GBM) X (TEST AUC ≈ 0,55); X (5 gün, 3×dvol, kâr/yükselen) X (DAX eksi).
KEŞİF SL/TP profilinde p < 0,01 olan yedi özellik iki tip gösteriyor ("ani panik" ↔ "uzayan çöküş"). Ölçülür:
(1) **Tip skoru** — yalnız KEŞİF'ten: işaretler KEŞİF'teki SL−TP farkının tersi (sma50 +, r5z +, stres10 −, vix_pct −, vix1 +, vade_egri −,
genişlik +), z'ler KEŞİF ortalama/sd'si, eksik = 0; filtre = skoru KEŞİF %33'lüğünün altında olanı at. Geçme ölçütleri F ile aynı.
(2) DAX'ın uzun tutuşta ayrışması: Duka NDX ve DAX'ta D0'da zararlı işlemlerin 1…5 gün içinde kâra dönme oranı ve dönmeyenlerin kaybı.
(3) Birleşim: "dünkü aralık üst tertil" × X_5_3.0_kar ve tip skoru × X_5_3.0_kar (betimleyici).
(4) X_5_3.0_kar tutuşlarının canlı KORKU/KSG/C3b geceleriyle örtüşmesi (Duka NDX).
