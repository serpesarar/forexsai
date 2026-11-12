# DAX profesörü — DAX'a özgü yeni kapı araması (ön kayıt)

Tarih: 2026-11-12 · Kullanıcı isteği: "DAX'ın uzmanı ol, DAX'ı nelerin etkilediğini ve nasıl işlem gördüğünü
çıkar, mevcut DAX işlemlerini incele, daha önce denenenleri hesaba katarak yeni kapılar bul."

Bu dosya sonuçlar hesaplanmadan ÖNCE yazıldı. Bundan sonra yapılan her değişiklik "EK-n" olarak eklenir.

## 0. Defter taraması (3. KURAL) — DAX'ta zaten bilinenler
- Canlıda GER40'ta: CAPREV (GF-18/22, A−), C3b (TR-C3b kör GER40 +29,3 bp, P %93,4), teyitli çekiç (FR-15 GER40 +0,144R),
  MOM/SR GDAXI BUY (OLD-04), CHREV, DECIDER.
- X kalanlar (tekrar EDİLMEYECEK): 1m scalp (OLD-01), açılış aralığı / FCR / boşluk-hizalı kırılım (FC-01…07), SMC, MTF süpürme,
  trend kanalı sekmesi (TK, DAX'ta kırılım da yok), trend çizgileri, limit geri çekilme (Y-01), HH/HL yapısı, TOM (KT-02),
  TSMOM (KT-01), günlük geri dönüş maliyet sonrası (GR-01), haber yönü (HB), ay sonu Avrupa son seansı söndü (QS-07 H6 B−),
  günlük sıklıkta 6 aile (QS-09 T1–T3; DAX "önceki seansı takip" seçildi, TEST −2,8 bp), gösterge çakışmaları (GC/PN).
- Meta-dersler: kenar "endeks + uzun + korku + zaman çıkışı" durumunda (§3-21); ortak soru "kim işlem yapmak zorunda?";
  sıklık kenarın düşmanı (§3-26); korku ölçüsü varlığa özgü (§3-11) — VDAX verisi yok (yfinance'te ^VDAX/V1X yok), bu yüzden
  VDAX kapısı bu turda sınanamaz.

## 1. Hipotezler (DAX'ın piyasa mikro yapısından; hepsi "zorunlu işlem yapan taraf" mekanizmalı)

### D1 — DAX-KSG: Xetra kapanış saati gecesi (NK-06'nın donmuş kuralının kör taşınması)
Mekanizma: Xetra kapanış müzayedesi (17:30 Berlin) endeks fonlarının / kapanışa bağlı emirlerin zorunlu akışı;
son nakit saatindeki satış baskısı gece geri verilir (NAS100'de 15→16 ET kartı 6/6, C+). GER40'a bugüne kadar taşınmadı
(NK-06 D4 yalnız US500/US30/US2000; QS-09 T1 farklı tanım: |sinyal| dilim filtresi, günlük sıklık).
- Kural (donmuş): GER40 16:30→17:30 Berlin getirisi < 0 → 17:30 barının açılışında AL → ertesi işlem günü 09:00 Berlin
  barının açılışında SAT. Stop yok.
- Karşı kol: aynı saat getirisi ≥ 0 olan geceler (aynı giriş/çıkış).
- Veri: broker GER40 M30 (c1_turev_20261105/data/mt5, sunucu = New York + 7 kuralıyla UTC'ye; eksen önce Xetra 09:00
  açılış hacim tepesiyle yıl yıl denetlenir), 2018-06 → 2026-11.
- Maliyet: bar spread'i × 1,5 (gidiş-dönüş tek spread) + gece swap'ı %4,94/yıl → 1,35 bp/gece, Cuma gecesi ×3.
- Geçme (B): net > 0 ve blok bootstrap P ≥ 0,95; iki kronolojik yarı > 0; Δ (kural − karşı kol) > 0, P ≥ 0,95;
  spread × 3 hâlâ > 0; yıl ≥ 6/9 artı. Hepsi tutmazsa C/X.
- Sağlamlık (karar dışı): çıkış 08:00 / 10:00, giriş 18:00, VIX ≥ 18,4 alt kümesi, Cuma hariç.

### D2 — Eurex vade haftası (opsiyon vadesi akışı)
Mekanizma: DAX opsiyon/vadeli (ODAX/FDAX) her ayın 3. Cuması 13:00 Berlin Xetra gün-içi müzayedesinde uzlaşır;
vade haftasında yapıcıların delta hedge akışı ve pozisyon devri. ABD'de Stivers & Sun (2013): vade haftası getirisi
yüksek, sonraki hafta düşük. DAX'ta defterde hiç sınanmadı (COMEX altın vadesi QS-11 H3 X, farklı varlık).
- Vade günü = ayın 3. Cuması; o gün işlem yoksa önceki işlem günü.
- D2a (aylık): vade haftası uzun = vade gününden önceki haftanın son kapanışı → vade günü kapanışı.
  Ölçü: vade haftası getirisi − diğer haftaların (aynı tanım: önceki hafta son kapanış → hafta son kapanışı) ortalaması.
- D2b (çeyreklik, Mart/Haziran/Eylül/Aralık "Hexensabbat"): aynı ölçü yalnız çeyrek vadeleri.
- D2c (vade sonrası hafta): vade sonrası haftanın getirisi − diğer haftalar (öngörü < 0).
- Veri: ^GDAXI günlük (yfinance, kapanış; performans endeksi, temettü içerir) KEŞİF 1990-01 → 2007-12,
  TEST 2008-01 → 2026-11; broker GER40 (M30'dan günlük kapanış 17:30 Berlin) 2018-06 → 2026-11 üçüncü set.
- Geçme (B): TEST farkı öngörülen yönde, ay-blok bootstrap P ≥ 0,95; KEŞİF aynı işaret; broker aynı işaret;
  D2a/b/c arasında Holm (3 test). Kural olarak işlenebilirlik: mutlak net getiri (spread + 7 gece swap) > 0.

### D3 — FOMC öncesi DAX sürüklenmesi (Lucca–Moench 2015'in DAX'ı)
Mekanizma: duyuru öncesi risk primi; DAX nakit 17:30'da kapanır, FOMC 20:00 Berlin → Xetra günü "saf öncesi".
NDX'te sınandı X (GF-07, HB-03 S7/S15; 2024-25). DAX yeni piyasa; ön olasılık DÜŞÜK (literatürde 2015 sonrası sönme).
- Kural: FOMC gününden önceki işlem günü kapanışı → FOMC günü kapanışı (^GDAXI günlük) uzun.
- Ölçü: o günlerin getirisi − tüm günlerin ortalaması; FOMC takvimi `research/xau_best_days_20261015/makro/out/calendar.csv`
  (2008-01 → 2026-06, 147 olay — tek dönem; yarılar 2008-16 / 2017-26).
- Geçme (B): fark > 0, P ≥ 0,95, iki yarı > 0; broker GER40 2018+ aynı işaret.

## 2. Genel kurallar
- Sızıntı: tüm sinyaller karar anında kapanmış barlardan; günlük sette giriş = sinyal gününün kapanışı (bilinir, çünkü
  sinyal takvimden gelir). M30 eksen denetimi geçmeyen yıl dışlanır ve yazılır.
- Plasebo: D1 için karşı kol + rastgele 17:30 gecesi (aynı sayıda, 2.000 çekiliş); D2/D3 için takvim kaydırma
  (vade gününü ±1…±2 hafta kaydırılmış sahte vadeler) ve gün-blok bootstrap.
- Sonuç ne olursa olsun deftere (§2.48) yazılır; geçen bir aday canlıya bağlanmaz, önce 2. KURAL kartı + gölge.

## EK-1 (2026-11-12, D3 sağlamlığında GÖRÜLDÜKTEN SONRA yazıldı — sınıf en fazla C)
Gözlem: ^GDAXI 2008-26'da FOMC'nin ertesi işlem günü (FOMC günü kapanışı → ertesi kapanış, ABD tepkisini içerir) −26,8 bp
(diğer günler +2,7). Aday kullanım: DAX uzun girişleri için o gün VETO (FOMC günü 17:30 → ertesi gün 17:30 açılmasın).
Sınama: iki yarı, en kötü 5 gün hariç, yıl tablosu, Euro Stoxx 50 / CAC / FTSE aynı tanım, broker GER40 FOMC günü 19:30 →
ertesi 17:30. Geçme: iki yarı < 0 ve en kötü 5 hariç < 0 ve ≥ 2/3 yan endeks < 0. Geçse de C (sonradan); gölge etiketi önerilir.
