# QS-02 — QS-01'den türeyen senaryo ailesi: rapor (2026-11-11)

Ön kayıt: `PROTOCOL_QS02.md` (Tur 1) + EK-1 (Tur 2) + EK-2 (Tur 3). Kod: `qs02.py`, `qs02b.py`, `qs02c.py` (kontrol),
`qs02d_anatomi.py` (betimsel), `qs02e.py`. Sonuçlar `results/qs02*.json`, işlemler `results/qs02_islemler.csv`.
Deneme sayacı: **22 karar hücresi** (18 + 3 + 1) + kontroller/betimseller.

## Kısa hüküm
**22/22 X.** Kullanıcının asıl sorusu ("dün güçlü yükseldi, bugün aşağı boşlukla açıldı → ne olur?") için net cevap:
**bu kurulumun kendine özgü bir yönü yok.** Boşluk, sıradan bir aşağı boşluk gününden daha sık ya da daha seyrek kapanmıyor;
ortalama sonuç birkaç çöküş gününe bağlı; hem "al" hem "sat" kolu bağımsız veride dağılıyor.

## Tur 1 — 18 senaryo (broker NAS100 M30 2018-26; kör US500/US30/US2000; QQQ 1999-2018)
| ID | Senaryo | NAS100 net bp (n) | Kör (US500/US30/US2000) | QQQ 99-18 | Sınıf |
|---|---|---|---|---|---|
| A1 | coşku ∧ aşağı boşluk → gün boyu AL | −12,3 (69) | −18,5 / −15,9 / +10,3 | −22,6 (129) | X |
| A3 | + 10:00'da açılışın altında → 10:00–16:00 SAT | +27,8 (27), P 0,87, y2 −8,4, en iyi 5 hariç −20,5 | +19 / +14 / +5 | — | X |
| A4 | + 10:00'da açılışın üstünde → AL | −16,6 (42) | +3 / −23 / +8 | — | X |
| A5/A6 | 15:00 zayıf → SAT / boşluk kapandı → AL | n 14 / 18 (betimsel) | | | — |
| A7/A8 | kırmızı kapanış → gece / iki gün AL | −0,7 / −13,0 (33) | | +19,9 / −34,4 | X |
| B1 | korku ∧ yukarı boşluk → AL | **+31,4 (76), P 0,98**, y2 +2,3 | −15 / +40 / −9 | −3,5 (183) | X |
| B2 | + 15:00 güçlü → son saat AL | +3,9 (28) | | | X |
| B3 | coşku ∧ yukarı boşluk ≥ %0,6 → AL | −21,1 (42) | hepsi eksi | −32,7 | X |
| C1 | QS-01 boğa rejiminde | −3,4 (88) | | | X |
| C2 | QS-01 aynası (boğa ∧ aşağı boşluk ∧ zayıf 15:00 → SAT) | −3,4 (48) | hepsi eksi | | X |
| C3 | ayı ∧ aşağı boşluk ∧ güçlü 15:00 → AL | +2,0 (47) | | | X |
| C4 | ayı rallisi söndü → SAT | −3,5 (87) | | | X |
| C5 | QS-01 gücü geceye taşar mı | −3,8 (67) | +13 / +17 / +6 | | X |
| D5 | 3 günlük ≥ %3 koşu ∧ aşağı boşluk → AL | +3,7 (32) | | −2,4 | X |
| D6 | 52 hafta zirvesinde aşağı boşluk → AL | −12,4 (44) | | +15,8 (P 0,97) | X |
Holm'da en iyi hücre (B1) 0,285. QS-01'in "ters/kardeş" hâllerinin hiçbiri son saatte bir şey üretmiyor; QS-01'in
kendi C'si (ayı yılları) yalnız kalıyor.

## Tur 2 — ters iz, 15 bağımsız piyasa (≤ 2018-04)
- **H2a coşku kırılması → SAT:** 12 yabancı piyasanın 6'sı artı, havuz +9,0 → X. QQQ +12, SPY +4, IWM −6.
- **H2c korku ∧ daha da aşağı açılış → AL ("korku döner"):** ABD ETF'lerinde güçlü (QQQ +50,9, IWM +37,3, SPY +19,0) ama
  yabancıda 8/12, havuz +2,1, işaret p 0,19 → X.
- **H2f haftalık coşku (5 gün ≥ +%3) ∧ Pazartesi ∧ aşağı boşluk → SAT:** ön-kayıtlı ölçütü geçti (10/11, +29,5, p 0,006;
  SPY/IWM artı) → **ama kontrol hücresi tuzağı yakaladı:** coşkusuz Pazartesi aşağı boşluk SAT havuzu +31,0 (11/11). Coşku şartı
  hiçbir şey katmıyor; bu eski "Pazartesi boşluk devamı" etkisi ve broker 2018-26'da dört ABD endeksinde ters (−8…−31 bp).
  **X (karıştırıcı)**. Haftalık coşku ∧ aşağı boşluk (Salı-Cuma) −2,3.

## Tur 3 — büyük boşluk
- **H3 coşku ∧ boşluk ≤ −%1 → SAT:** yabancı 3/10 artı, havuz −10,9, kontrolden −7,1 kötü → X. Yalnız ABD'de kontrolden iyi
  (QQQ +14 vs −33, SPY +54 vs −14, IXIC +31 vs −5) — sonradan görülen, yabancıda yok; kayda geçti, kural değil.

## Anatomi (betimsel) — o gün gerçekte ne oluyor
NAS100 2018-26, coşku ∧ aşağı boşluk (n 69) vs diğer aşağı boşluk günleri (n 505):
| | coşku ∧ G− | diğer G− |
|---|---|---|
| Açılıştan 16:00'ya **medyan** | **+12 bp** (15:00'te +23) | +7 bp |
| Açılıştan 16:00'ya **ortalama** | **−11 bp** | +2 bp |
| Boşluk gün içinde kapandı | %47,8 | %45,5 |
| Dünün kapanışının üstünde bitti | %24,6 | %25,1 |
| Gün dibi ilk saatte | %44,9 | %43,6 |
QQQ 1999-2018: boşluk kapanma %64,4 vs %58,2.

**Okuma:** çoğu gün boşluk kısmen alınıyor (medyan artı) ama nadir günlerde (2020 Şubat, 2022) çöküşe dönüyor ve ortalamayı
eksiye çekiyor — **sol kuyruklu** bir dağılım. "Al" kolu sık küçük kazanıp seyrek büyük kaybediyor, "sat" kolu tersini;
ikisi de net bir şey bırakmıyor. Boşluk kapanma oranı sıradan aşağı boşluk günlerinden farksız → "coşku" bilgisi yok.

## Meta-ders adayı
"Coşku dönmez" (§3-2) coşkunun **kırıldığı** güne taşınmıyor: kırılma günü ne alınıyor ne satılıyor; sonucu kuyruk belirliyor.
Pazartesi/hafta sonu etkisi her "Pazartesi" koşullu hücrede kontrol hücresiyle ayrılmalı (H2f: ölçütü geçti, kontrolle düştü).
