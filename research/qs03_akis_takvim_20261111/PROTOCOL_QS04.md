# QS-04 — R1 dengeleme kapısının genişletilmesi + aynı mantıkla yeni kapı — ön kayıt (2026-11-11)

Temel: QS-03 R1 (B, kart 6/6): D−3 kapanışında Δ = SPY ay içi − TLT ay içi; Δ ≥ +%2 → KISA, ≤ −%2 → UZUN, D−3 → D.
Teşhis: TEST'te kazanç tahvil bacağından, ay içi profilde artı yalnız son haftada; D−1/D−2 sinyalli (yeni aya taşan) tutuşlar eksi.
Sonuçlar görülmeden yazıldı. Karar hipotezi 4 (E1, E2, E4, N5); E3, E5 betimsel. Deneme sayacı QS-03 + 4.

Ortak: dönemler KEŞİF 2002-08→2013-12, TEST 2014-01→2026-10, bağımsız 1990-01→2002-07 (^GSPC + sentetik tahvil, mümkünse).
Maliyet ETF 2 bp, yabancı endeks 3 bp. Bootstrap 5.000 (işlem = ay).

## E1 — Çeyrek sonu akışı (çeyreklik dengeleyenler)
Mekanizma: fonların bir kısmı çeyrek sonunda dengeler; o zaman sapma çeyrek içi (QTD) farktır.
- E1 kuralı: Mart/Haziran/Eylül/Aralık'ta Δ_Q = SPY QTD − TLT QTD (D−3'e kadar), diğer aylarda R1'in Δ'sı; eşik ve pencere aynı.
- Ölçüt: E1 − R1 (aylık P&L farkı, QQQ+SPY) KEŞİF ve TEST'te > 0; E1'in kendisi iki dönemde P ≥ %90; bağımsız dönemde E1 ≥ R1.
  Üçü → R1'in yerine **E1** (genişleme kabul) · biri düşerse X (R1 olduğu gibi kalır).

## E2 — Ay başı geri tepme
Mekanizma: ay sonu zorunlu akış fiyatı geçici iter; akış bitince geri döner (profilde yeni aya taşan tutuşların eksi olması).
- Sinyal D kapanışında tam ay Δ_D (SPY − TLT, önceki ay sonu → D). Δ_D ≥ +%2 → UZUN (satılan hisse geri alınır), ≤ −%2 → KISA.
  Tutuş D → D+3 kapanış (yeni ayın ilk 3 günü). Taban: aynı pencere her ay uzun (ay dönümü sürüklenmesi).
- Ölçüt: QQQ+SPY havuz ort > 0 ve P ≥ %90 KEŞİF ve TEST'te; uzun bacak − taban > 0 iki dönemde; bağımsız ^GSPC > 0. Hepsi → **B**;
  ilk ikisi → **C+**; diğer **X**.

## E4 — Küresel taşma
Mekanizma: küresel dengeli fonlar ABD hisse/tahvil oranıyla birlikte dünya hissesini de alır/satar.
- Aynı ABD sinyali (R1 Δ, D−3). Yabancı piyasa girişi: ABD D−3 kapanışından sonraki ilk yerel kapanış; çıkış: ABD D tarihine eşit ya da
  önceki son yerel kapanış (≥ 1 gün tutuş, yoksa atla). Piyasalar: ^GDAXI, ^STOXX50E, ^N225, ^FTSE + defterdeki 12 (AEX, AXJO, BSESN,
  BVSP, FCHI, GSPTSE, IBEX, JKSE, KS11, MXX, SSMI, TWII). Dönem 2002-08→2026-10 (TLT), bağımsız 1990-2002 (sentetik).
- Ölçüt: 2002-26'da piyasaların ≥ %60'ı artı ∧ işaret p ≤ 0,10 ∧ havuz ort > 0; DAX artı; broker GER40 M30 2018-26 (D−2 09:00 CET
  açılış girişi değil, basit: ABD D−3 16:30 ET → D 11:30 ET, GER40 seansı içinde) net > 0. Hepsi → **B−** (GER40'a taşınabilir);
  ilk ölçüt → **C+**; diğer **X**.

## N5 — ABD / uluslararası hisse dengelemesi (aynı mantıkla yeni kapı)
Mekanizma: küresel fonlar bölge ağırlıklarını da ay sonunda geri kurar; ABD hissesi uluslararasını çok geçtiyse ABD satılır.
- Δ2 = SPY ay içi − EFA ay içi (D−3). Δ2 ≥ +%2 → NASDAQ KISA, ≤ −%2 → UZUN, D−3 → D.
- Ölçüt: (a) N5 kuralı QQQ+SPY KEŞİF ve TEST'te ort > 0, P ≥ %90; (b) artımlı bilgi: pencere getirisi ~ Δ + Δ2 regresyonunda Δ2 katsayısı
  iki dönemde < 0 ve t ≤ −1,5. (a) ∧ (b) → **B** (yeni kapı) · yalnız (a) → **C** (Δ'nın kopyası olabilir) · diğer **X**.

## Betimsel (karar dışı)
- E3 doz: R1 tetiklenen aylar |Δ| üçte birlik kovalarında ortalama (mekanizma doz eğrisi beklenir).
- E5 anatomi: broker NAS100 2018-26, R1 tutuşunun hangi gün ve saatlerde oluştuğu (D−2, D−1, D; D'nin son saati).
- Birleşik: hayatta kalan hipotezler R1 ile tek sinyalde (işaretlerin toplamı) — kart yeniden.

## Sızıntı
Tüm Δ'lar sinyal günü kapanışına kadar. Yabancı girişi ABD kapanışından sonra. EFA, TLT, SPY aynı 16:00 kapanışı.
