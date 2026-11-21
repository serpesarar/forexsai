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
