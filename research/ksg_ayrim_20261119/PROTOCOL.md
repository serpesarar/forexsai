# KSG (kapanış saati gecesi) kaybeden/kazanan ayrımı — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği
"Bu kural da önceki gibi SL ve TP olanları ayrıştır, farklarını çözümle, SL olanları aradan çıkar." KSG'de TP/SL yok:
**kazanan = net > 0, kaybeden = net < 0** (16:00 ET giriş + spread → ertesi işlem günü 09:30 çıkış, finansman). İkincil: net ≤ −50 bp.

## Defter kontrolü
- Bilinen ayrıştırıcılar: fitilli KSG (§2.68 FK-01…03, B: fitilli +28,6 / fitilsiz +1,9 bp), VIX ≥ 25 dozu (DB-02/NX-08, canlı),
  FOMC öncesi gece (FG-01, B), OPEX vetosu (GX-05/06, B), Cuma vetosu X, ay başı X, son saat derinliği tertili C (NX-07).
- §2.99/§2.100 (korku paketi) yöntemi ve dersi (§3-50/51): kaybeden girişte tanınmıyor, kalite filtresi mümkün.
- **Yeni olan:** KSG gecelerinde 6 TF kanal + `ta` bataryası (xp_paket_ayrim motoru), büyük örneklem, kör üç endeks.

## Veri
- Geceler: `research/ksg_opex_canli_20261119/src/oynat.py` ile canlı kodun birebir sinyali (ksg_live.find_signal), 2018-05 → 2026-11-05.
  Birincil MT5 NAS100; ikincil Duka NDX; **kör** MT5 US500 (2018-06+), US30, US2000 (aynı kural, kendi gecesi).
- KEŞİF ≤ 2021-10-31, TEST sonrası. Özellikler: motor.feed_trade_feats (16:00'a çapalı, sızıntı testli) + dünkü VIX, vadeye gün, haftanın günü.

## Adımlar (sabit)
1. Tek tek: NAS100 KEŞİF AUC, 1.000 permütasyonla aile eşiği; geçenlerin TEST/Duka/kör yönü.
2. Modeller (yalnız NAS100 KEŞİF eğitimi): L1 lojistik (C KEŞİF içi seçilir), LightGBM sınıflandırıcı, LightGBM regresyon (net, %2,5/97,5 kırpık).
   Veto: KEŞİF OOF'ta en riskli %15 ve %30 (eşik KEŞİF'te donar).
3. Kümeleme: KEŞİF PCA-10 + KMeans (siluet), kaybeden yoğun küme TEST'te de yoğun mu.
## Geçme ölçütü ("SL olanları çıkarmak")
- **B:** veto kümesinin TEST ortalaması < 0 ve blok bootstrap P ≥ 0,90, NAS100 **ve** Duka'da; kör üç endeksin ≥ 2'sinde vetolanan < kalan;
  vetolu kitabın Sharpe'ı NAS100 TEST'te vetosuzdan yüksek.
- **C:** vetolanan < kalan (≥ 15 bp fark) ama ortalaması eksi değil (kalite filtresi).
- **X:** hiçbiri. Canlıya bağlama yok; B çıkarsa ileri gölge + kart ayrı adım.
