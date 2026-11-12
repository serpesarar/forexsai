# QS-11 — Altında kombinasyon taktikleri: rapor (2026-11-12)

Ön kayıt `PROTOCOL.md`. Kod `qs11.py`, sonuç `results/qs11.json`. 5 donmuş hücre, seçim yok, Holm.
Ölçüt "taban üstü fark": aynı yönde koşulsuz pozisyonun getirisinin üstü (altın 2004-26'da ~+3 bp/gün sürüklendi; uzun her kural kâğıtta artı görünür, E13).

## Sonuç: 5/5 X
| Hipotez | ayda işlem | net bp (GLD) | **taban üstü** (P) | yarılar (taban üstü) | broker XAUUSD 2018-26, maliyet ×1,5 | sınıf |
|---|---|---|---|---|---|---|
| H1 trendde düşüş günü (≤ −%1) AL, 3 gün | 1,6 | +18,5 | **+3,0** (0,61) | −6,2 / +13,6 | +21,5 (P 0,89, n 156) | X |
| H2 altın/gümüş göreli değer, 5 gün | 1,6 | −6,3 | −4,0 (0,37) | +9,1 / −12,3 | −26,2 | X |
| H3a COMEX opsiyon vadesi sonrası AL, 3 gün | 1,0 | −1,3 | −12,6 (0,11) | +6,7 / −29,0 | −23,1 | X |
| H3b vade öncesi SAT, 3 gün | 1,0 | −20,7 | −5,5 (0,32) | −7,9 / −3,4 | −27,6 | X |
| H4 borsa ≤ −%2 ∧ altın ≤ −%1 (likidasyon) AL, 5 gün | 0,2 | −4,8 | −25,0 (0,29) | −39,7 / +0,5 | +13,1 (n 18) | X |
Holm 5/5 = 1,00. GC/SI 2000-04 desteği hiçbirinde işareti kurtarmıyor.

## Okuma
- **H1 tek "artı" görünen** — broker'da işlem başı +21,5 bp. Ama aynı trend günlerinde rastgele 3 gün uzun durmak da neredeyse aynısını veriyor (fark +3 bp,
  ilk yarıda −6). Yani "düşüşte al" bir şey katmıyor; kazanan şey **altın yükseliş trendindeyken uzun durmak** (zaten bilinen: XS-01, R0B_G1).
  MK-13'ün aynası tutmadı: yükselişi kovalamak cezalı ama düşüşü almak ödüllü değil (asimetri).
- H2: altın gümüşün gerisinde kaldığında alma 2004-14'te +42 bp (taban üstü), 2015-26'da −9 → kararsız; kısa bacak her çağda eksi (altın düşüşe karşı direnç).
- H3: COMEX opsiyon vadesi takvim etkisi yok; 2015 sonrası vade sonrası uzun belirgin eksi (−29, P 0,01) — ters hipotezi şimdi seçmek E23.
- H4: borsayla birlikte satılan altın 5 günde dönmüyor (2008 ve 2013 düşüşleri devam etti); "korku döner" endekse özgü, altına taşınmıyor.

## Bütün altın arşiviyle birlikte
Altında 30+ deneme sonrası tek yapı ayakta: **trend devamı uzun** (günlük 55 gün tepesi + EMA200; 1h yeni 20 bar tepesi + "dün > +%1 ise atla").
İkisi de kutuda GÖLGE. Gölge karnesi (xau_shadow, 2026-10 →) henüz çok küçük (n 6, −0,6R) — karar için yetersiz.
