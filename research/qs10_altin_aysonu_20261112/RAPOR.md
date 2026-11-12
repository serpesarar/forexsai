# QS-10 — Ay sonu dengeleme testleri altında (XAUUSD): rapor (2026-11-12)

Ön kayıt `PROTOCOL.md`. Kod `qs10.py`, veri `veri.py` (GLD), sonuç `results/qs10.json`. Deneme: 16 hücre, tek seçim.

## Sonuç: X
| | n | ort net bp | isabet | P |
|---|---|---|---|---|
| Seçilen hücre (KEŞİF'te en yüksek t): **S1_SON_AYNI** — D−3'te SPY−TLT ≥ +%2 ise altını AL, ≤ −%2 ise SAT; son seans 09:30→16:00 | | | | |
| KEŞİF 2004-12 → 2014-12 (GLD) | 88 | +21,3 (t 1,96) | %56,8 | 0,97 |
| **TEST 2015-01 → 2026-10 (GLD)** | 99 | **−12,7** (t −1,8) | %40,4 | 0,04 |
| Broker XAUUSD 2018-06 → 2026-10, maliyet × 1,5 + swap | 64 | −8,5 | %42,2 | 0,18 |
| Destek GC=F 2000-08 → 2004-11 | 37 | −22,7 | %24,3 | 0,01 |
Ölçüt (a) TEST > 0 ✗, (b) iki yarı ≥ 0 ✗ (−11,9 / −13,4), (c) broker ✗ → **X**.

## 16 hücrenin TEST'i (şeffaflık)
Hiçbiri Holm sonrası anlamlı değil (hepsi 1,00). KEŞİF'te en güçlü dört hücre (S1 son seans ve S1 gece, iki yön) TEST'te tam tersine döndü:
KEŞİF'te "AYNI" yön +21, TEST'te "TERS" yön +8 (P 0,90 / 0,84). Yani altının ay sonu son seansındaki hareketi hisse/tahvil akışıyla ilişkili ama
**işareti çağdan çağa dönüyor** (2000-04 TERS, 2004-14 AYNI, 2015-26 TERS) → işlem kuralı olamaz; sonradan TERS yönü seçmek E23 olur.
Altının kendi ay itişi (S2) her pencerede gürültü (|t| < 0,8).

## Neden (mekanizma)
Emeklilik dengelemesi hisse ↔ tahvil arasında. Endekslerde canlı olan son seans + ay başı kurallarının gücü bu akışın doğrudan alıcı/satıcısı
olmasından geliyordu. Altın akışın parçası değil; faiz kanalıyla dolaylı bağ, altın–reel faiz ilişkisinin 2022 sonrası kırılmasıyla (bkz.
xauusd-macro: işaret dönmüş) tutarlı biçimde kararsız. Öncül zayıftı, sonuç öncülle uyumlu.

## Not
QS-09'un günlük 15–20 işlemlik hücreleri XAUUSD'de zaten koşulmuştu (3 tur, X). Altında ayakta kalan tek kural hâlâ günlük Donchian
kırılımı + EMA200 uzun (xauusd-daily-swing, canlıda değil).
