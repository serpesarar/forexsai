# OZ — OPEX vade penceresinde zamanlı tutuş (1 sa / 5 sa / 1 gün / 1,5 gün) — 2026-11-18

Ön kayıt `PROTOCOL.md` + EK-1. Kod `src/oz.py`, `src/ek1_sat.py`; çıktılar `results/`.

## 1) Saf takvim tutuşu ızgarası (8 çapa × 4 tutuş = 32 hücre)
KEŞİF (MT5 H1 2016–18 + Duka 2018–21): 15/32 hücre P ≥ 0,90; dondurulan 4 hücre ve kör sonuç:

| Hücre | KEŞİF | TEST Duka 2021–26 | MT5 NAS100 | kör US500 / US30 / US2000 | QQQ günlük karşılığı 1999–2015 / 2016–26 | Hüküm |
|---|---|---|---|---|---|---|
| Çar 16:00 → 1,5 gün AL | +40 bp (P 0,99) | **−29** | −36 | −16 / +8 / +3 | −16 / +2 | X (ters) |
| Per 09:30 → 1 gün AL | +30 (0,99) | **−42** (P ters 0,96) | −46 | −1 / +11 / −4 | −19 / +11 | X (ters) |
| Per 09:30 → 5 sa AL | +22 (0,98) | −11 | −14 | +8 / +8 / 0 | −17 / +6 | X |
| **Cum (vade günü) 09:30 → 1 gün SAT** | +44 (0,98) | +13 (P 0,68) | +10 (0,66) | **+32 / +28 / +36 (0,95–0,97)** | **+26 (0,964) / +27 (0,965)** | **C+** |

Ders: 2016–21'de OPEX Perşembe'si yükseliyordu, 2021–26'da düşüyor — seçilen yönler kör dönemde döndü (§3-44). Ayakta kalan tek
hücre vade günü sabahından Pazartesi sabahına satış: işlem neti QQQ'da ≈ +20 bp (vade günü + hafta sonu zayıf), 27 yıl iki yarıda ve
3 kör piyasada aynı yön; ama NASDAQ gün içi kör testte zayıf → C+.

## 2) "Bölge" = OPEX Çar/Per korku günü → SAT + zamanlı tutuş (EK-1)
| Tutuş | Duka | MT5 NAS100 | US500 | US30 | US2000 | havuz z P | yarılar |
|---|---|---|---|---|---|---|---|
| 1 sa | −1 | +2 | −2 | −5 | −4 | 0,23 | +2 / −5 |
| 5 sa | −9 | −4 | −4 | −9 | +1 | 0,10 | +1 / −11 |
| **1 gün (birincil)** | +25 | +19 | −6 | +19 | +1 | 0,83 | +43 / −17 |
| 1,5 gün | +30 | +17 | +17 | +29 | +23 | 0,968 | +44 / +3 |
Günlük C3b (RSI2 < 10) OPEX Çar/Per girişi SAT: ^NDX 1985–99 1 gün +45 (P 0,98), 2 gün +135 (P 0,9996); QQQ +19 / +17 (P 0,80 / 0,69).
Hüküm: birincil (1 gün) havuz P 0,83 ve ikinci yarı eksi → **C**; 1,5 gün daha iyi ama sonradan seçildi → C+ en fazla. Bölge
**satış** için değil **veto** için güçlü (SV-01 B kalır): korku alımı orada kaybettiriyor, ama tersine dönmek güvenilir kazanç vermiyor.

## 3) Yan bulgu — normal haftalarda K1 korku gecesi alımının zaman profili
1 sa ≈ −0,5…−9,5, 5 sa ≈ −3…+4, **1 gün +33…+54**, 1,5 gün +27…+64 (5 besleme). Kazanç ilk 5 saatte (16:00–21:00) değil, gece ve ertesi
gün oluşuyor; 1,5 gün 1 günden belirgin iyi değil → canlı çıkış (ertesi 16:00) yerinde.
