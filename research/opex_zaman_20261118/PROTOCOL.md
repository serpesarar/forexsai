# OZ — OPEX vade penceresinde zamanlı tutuş haritası (1 sa / 5 sa / 1 gün / 1,5 gün)

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Kullanıcı: "bu belirli bölgeyi tutup 1 gün, 1 saat, 5 saat ya da 1,5 gün tutmak".
Yorum: §2.91'in bölgesi = aylık OPEX haftası (ayın 3. Cuma'sı F). Soru: bu bölgede hangi giriş anı × tutuş süresi kâr ediyor
(TP/SL yok, yalnız zaman çıkışı), ve sonuç kontrol haftalarından farklı mı?

## Çapalar (NY saati, işlem günü ofseti F'ye göre) — 8
SAL16 (F−3 16:00), CAR0930 (F−2 09:30), CAR16 (F−2 16:00), PER0930 (F−1 09:30), PER16 (F−1 16:00), CUM0930 (F 09:30),
CUM16 (F 16:00, vade kapanışı), PZT0930 (F+1 09:30, vade sonrası).
## Tutuşlar — 4
1 sa, 5 sa, 1 gün (24 sa), 1,5 gün (36 sa) **işlem saati** olarak (beslemede var olan barlar sayılır; hafta sonu kapalı süre sayılmaz).
## Ölçü
Uzun brüt getiri (bp); kontrol = aynı çapa/tutuş, OPEX dışı haftalar (her haftanın son işlem günü Cuma ise F yerine o Cuma).
Fark = OPEX − kontrol. İşlem neti: seçilen yönde gerçek spread (giriş ask/bid, çıkış bid/ask), uzunda finansman × tutuş/24 sa.
## Seçim ve doğrulama
- KEŞİF: MT5 NAS100 H1 2016-01 → 2018-03 + Duka NDX 1m 2018-04 → 2021-10. 32 hücre; yön = KEŞİF farkının işareti;
  dondurma: |t| en büyük ilk 4 hücre, en az biri farkı ≥ 0 ve P ≥ 0,90.
- TEST (kör): Duka 2021-11 → 2026-11; bağımsız besleme MT5 NAS100 M30 2021-11 →; kör piyasa MT5 US500/US30/US2000 M30 2018 → (tüm dönem).
- Uzun geçmiş: dondurulan hücrenin günlük karşılığı varsa (açılış/kapanış çapaları, 1 seans ≈ 5 sa, 1 gün, 1,5 gün) QQQ 1999 → ve
  ^NDX 1985 → (yalnız kapanış–kapanış).
- Hüküm: B = TEST'te seçilen yönde fark > 0 ve P ≥ 1 − 0,10/4, işlem neti > 0, bağımsız besleme ve kör piyasaların ≥ 2/3'ü aynı yön,
  uzun geçmiş aynı yön + 2. KURAL kartı ≥ 5/6. Aynı yön TEST P ≥ 0,90 → C+. Aksi X.
- Bilgi (seçim dışı): 32 hücrenin tamamı TEST'te raporlanır; OPEX haftasının "en iyi tutuşu" ayrıca her çapa için.

## Sonuç (ızgara, 2026-11-18): dondurulan 4 hücrenin 3'ü TEST'te ters (KEŞİF 2016–21 Perşembe yükselişi → TEST düşüş), CUM0930_1gün SAT
TEST P 0,68 (kör US500/US30/US2000 0,95–0,97) → ızgara X / C.

## EK-1 (2026-11-18, ızgaradan sonra) — "bölge" = OPEX Çar/Per korku günü; alım yerine SAT, zamanlı tutuş
SV-01: bu bölgede K1 korku gecesi uzunları kaybettiriyor. Soru: aynı anda SAT + zaman çıkışı kâr eder mi, hangi süre?
Olay: canlı K1 tanımı (`korku_genislik/gn.py::nts`: 16:00 ≤ TWAP −%0,5 ∧ son saat aşağı) ve giriş günü OPEX Çarşamba/Perşembe.
Giriş 16:00 barı (bid), tutuş 1 sa / 5 sa / 1 gün / 1,5 gün işlem saati, çıkış ask. Beslemeler: Duka NDX, MT5 NAS100 M30, US500,
US30, US2000. **Birincil: 1 gün** (SV-01'in ölçtüğü süre). Kontrol: aynı K1 olayları OPEX dışında (uzun yönde) aynı tutuşlarla.
Uzun geçmiş: günlük C3b (RSI2 < 10) OPEX Çar/Per girişleri SAT, kapanış → 1/2 gün sonra kapanış, ^NDX 1985–99 ve QQQ 1999+.
Geçme B: birincil tutuşta SAT neti 5 beslemenin ≥ 4'ünde > 0, havuz (z) P ≥ 0,95, ^NDX 1985–99 aynı yön, kart ≥ 5/6.
Uyarı: olay sayısı küçük (besleme başına ~20–33); SAT, korku dönüşüne karşı işlem olduğundan kuyruk riski raporlanır.
