# QS-01 — QQQ "kapanış saati" stratejisi (Instagram, quantifiedstrategies) — ön kayıt (2026-11-11)

Kaynak: kullanıcının paylaştığı Reel ekran görüntüleri ("How This QQQ Closing-Hour Trading Strategy Works",
iddia: 10 yılda ~256 işlem). Bu dosya sonuçlara bakılmadan yazıldı.

## Kural (videodaki birebir hâli)
Kurulum (hepsi):
1. Dünkü QQQ kapanışı 50 günlük hareketli ortalamanın ALTINDA (SMA50 dünkü kapanış dahil son 50 kapanış).
2. Bugün açılış > dünkü kapanış × 1,006 (≥ %0,60 boşluk yukarı).
3. 15:00 ET'de fiyat > bugünkü açılış.
4. 15:00 ET'de gün aralığının üst %23'ünde: (fiyat − gün dibi) / (gün tepesi − gün dibi) > 0,77
   (tepe/dip 09:30 → 15:00 arası).
Giriş: sonraki 5 dk bar (~15:05 ET). Stop: girişin %1 altı (sabit). Çıkış: 16:00. Yalnız uzun, günde tek işlem, gece yok.

## Defter taraması (§0)
Bu kural sistemde YOK. Yakınları: KSG (NK-06/07, canlı) son saat AŞAĞI → 16:00'da AL, gece tut (zıt koşul, farklı
pencere); C3b 15:30 RSI2<10 AL (aşırı satım, gece tutar); GM-01 son yarım saat momentumu (Baltussen) C, +3,3 bp;
NK-02 "SMA50 altında yükseliş ∧ hacim" → ertesi gün sol kuyruk (C); NK-05 ayı rallisi vetosu X; GS-04 güçlü açılış
mumu C. Yeni olan: aynı gün içi, SMA50 altı + boşluk yukarı + 15:00 gücü kesişimi, 15:05→16:00 tutuş. Daha önce
sınanmadı → açılabilir. Mekanizma iddiası: ayı rejiminde boşlukla açılıp gün boyu tutunan ralli → açık pozisyonların
(açığa satıcılar) kapanışa doğru kapatma baskısı + gün içi momentum (Gao vd. 2018).

## Veri ve icra
- **Birincil (P):** broker NAS100 M30, 2018-05-25 → 2026-11-04 (`c1_turev_20261105/data/mt5`, sunucu = NY+7).
  Günlük kapanış = 16:00 ET'de başlayan barın açılışı (= 15:30 barının kapanışı); açılış = 09:30 barının açılışı.
  15:00 durumu: 09:30…14:30 barlarının tepe/dip ve 14:30 barının kapanışı. Giriş: 15:00 barının açılışı + maliyet
  (M30'da 15:05 yok; 5 dk farkı R ile ölçülür). Stop: 15:00 ve 15:30 barlarının dibi ≤ giriş×0,99 → stop fiyatından çık.
  Çıkış: 16:00 barının açılışı (bid). Maliyet: `kazanan_turev_20261111/ortak.py` modeli (RTH: max(spread, medyan)×1,5).
- **Birebir (R):** Dukascopy NDX 1m 2021-11 → 2026-11 (`geri_cekilme_limit_20261109/data/path.parquet`, UTC→ET
  zoneinfo). 15:00 durumu = 14:59 barının kapanışına kadar; giriş 15:05 barının açılışı + spr; stop 1m dipleriyle;
  çıkış 16:00 barının açılışı. İkincil giriş 15:00.
- **Kör (K):** broker US500, US30, US2000 M30 2018 → 2026 — aynı kural, her biri kendi SMA50 / boşluğu.
- Getiri bp; R = bp / 100 (risk %1).

## Kıyaslar (hepsi aynı veri, aynı maliyet)
- **T0 taban:** tüm günler 15:00→16:00 uzun (koşulsuz son saat).
- **T1 gün içi güç tabanı:** yalnız koşul 3+4 (rejim ve boşluk yok).
- **Ablasyon (betimsel, karar dışı):** her koşul tek tek çıkarılır.
- **Plasebo:** aynı yıl dağılımıyla T0 günlerinden rastgele n gün (10.000) → kuralın ortalamasının yüzdeliği.

## Geçme ölçütleri (P'de; hepsi)
1. Net ort > 0 ve gün-blok bootstrap P(ort > 0) ≥ %90.
2. Kronolojik iki yarının ikisi de ≥ 0.
3. Spread × 1,5 stresinde net ort > 0.
4. Özgüllük: kural − T0 farkı > 0, P ≥ %90 (plasebo yüzdeliği ≥ %90).
5. Kör: üç endeksin havuz ortalaması > 0 ve en az 2/3 artı.
6. Birebir (R): Dukascopy'de net ort > 0 (yön teyidi; n küçük olduğundan P şartı yok).
Hacim (kart ölçütü 1, ≥150 olay) ayrıca raporlanır; altında kalırsa en iyi sınıf C+.
Sınıf: 1–6 geçer + hacim ≥150 → B (kart adayı); 1–4 geçer, 5 veya 6 düşer → C; 1 veya 2 düşerse → X.

## Sızıntı denetimi
Koşul 1 dünkü kapanışla (t−1), koşul 2 bugünkü 09:30 açılışıyla, koşul 3–4 yalnız 15:00 öncesi kapanmış barlarla.
Giriş 15:00'dan SONRA. Önek testi: 15:00 sonrası barlar silinince sinyal kümesi değişmemeli.
