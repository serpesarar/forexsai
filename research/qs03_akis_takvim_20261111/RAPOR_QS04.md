# QS-04 — R1 dengeleme kapısının genişletilmesi: rapor (2026-11-11)

Ön kayıt `PROTOCOL_QS04.md`. Kod: `qs04.py` (E1, E2, E3, N5), `qs04_e4.py` (küresel), `qs04_dongu.py` (sonradan teşhis + birleşik),
`qs04_kart.py`. Sonuçlar `results/qs04*.json`; kartlar `go_live_cards/qs04_e2_ay_basi_uzun.json`, `qs04_ay_sonu_dongusu.json`.

## Özet
| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| **E2** | **Ay başı geri tepme:** ay sonu Δ_D ≥ +%2 → yeni ayın ilk 3 günü UZUN (≤ −%2 → KISA) | ön-kayıtlı ölçütler geçti; kazancın tamamı uzun bacakta (kısa üç dönemde de eksi) | **B** (uzun bacak) |
| **E4** | **Küresel taşma:** R1 ABD sinyali yabancı endekslerde | 2002-26 16/16 piyasa artı, havuz +37 bp; 1990-2002 4/15; GER40 broker +6 | **B−** (mekanizma kanıtı; GER40'a taşıma önerilmez) |
| E1 | Çeyrek sonunda çeyrek içi fark | E1 − R1 KEŞİF +0,3, TEST −5,3 bp/ay | X |
| N5 | ABD − uluslararası hisse (EFA) dengelemesi | KEŞİF −8,8, TEST +33 ama R1 ile %74 aynı işaret, yalnız N5 ayları eksi | X |
| **Döngü** | **R1 (D−3→D) + E2 uzun (D→D+3)** | kart **6/6**: QQQ 327 işlem +48,1 bp P 1,00, broker NAS100 104 işlem +41,9 (×1,5 +41,0), aylık Sharpe 0,47 → 0,82 | **GÖLGE önerisi** |

## E2 — ay başı geri tepme
Mekanizma: hisse ay içinde tahvili çok geçerse fonlar ay sonunda hisse satar (R1 kısa bacağı); akış bitince fiyat yeni ayda geri gelir.
| | KEŞİF 2002-13 | TEST 2014-26 | Bağımsız 1990-2002 |
|---|---|---|---|
| E2 iki bacak (QQQ+SPY) | +34,1 (n 93, P 0,93) | +26,2 (n 101, P 0,91) | +4,5 |
| **Uzun bacak** | **+83,3 (n 55, P 1,00)** | **+43,1 (n 68, P 0,97)** | **+47,1 (n 51, P 0,98)** |
| Uzun − ay başı tabanı | +39,3 | +17,4 | +15,3 |
| Kısa bacak | −37,1 | −8,4 | −43,8 |
**Teşhis (sonradan):** TEST'te yalnız-hisse kuralı (SPY ay ≥ +%2) tabandan −18 bp, yalnız-tahvil (TLT ≤ −%2) +17; saf durumlar
"hisse↑ ∧ tahvil yatay" +63 (n 19), "tahvil↓ ∧ hisse yatay" +125 (n 9) → **momentum değil, göreli fark** (dengeleme). KEŞİF'te iki taraf
da katkı veriyor. Broker NAS100 2018-26 E2 uzun +56,1 (n 44, P 0,95); gün gün +34 / +34 / +1 (artı ilk iki günde).
Kart (E2 uzun tek başına): 5/6 — hacim 123 < 150 → SHADOW.

## E4 — küresel taşma
Aynı ABD sinyali (D−3, Δ), yabancı giriş ABD kapanışından sonraki ilk yerel kapanış, çıkış ABD D gününe kadarki son yerel kapanış:
AEX +48,5 · FCHI +46,3 · IBEX +46,6 · SSMI +44,8 · FTSE +48,0 · GDAXI +42,9 · STOXX50E +55,8 · GSPTSE +38,6 · BVSP +40,2 · TWII +36,0 ·
KS11 +30,5 · N225 +29,0 · MXX +29,5 · AXJO +26,3 · BSESN +17,6 · JKSE +15,4 (n ≈ 200 her biri; iki yarı her yerde artı).
→ Akış küresel hisse fiyatına yansıyor, bu mekanizmanın en güçlü bağımsız teyidi. **Ama:** 1990-2002'de 4/15 (havuz −5,9) — etki
2000'lerde (hedef-tarih/60-40 fonların büyümesiyle) doğmuş görünüyor; R1'in 1990-2002 zayıflığıyla tutarlı. Endeksler birbirine bağlı,
16/16 bağımsız 16 sınama değildir. **GER40 broker 2018-26: +6,4 (n 38)**, uzun bacak −89 (n 8), kısa +35; GDAXI 2023-25 ≈ +2…+7 →
bot için GER40'a taşıma önerilmez.

## E1, N5, E3
- E1: çeyrek aylarında R1 KEŞİF −16,7 / TEST +51,9 (dönemler zıt); QTD farkı iyileştirmiyor → R1 aylık kalır.
- N5: EFA farkı Δ ile iki dönemde düşük korelasyonlu (−0,07 / 0,28) ama regresyonda katsayısı anlamsız (t −0,8 / −1,0) → yeni bilgi yok.
- E3 doz (betimsel): R1 kovaları KEŞİF −5 / +54 / +60, TEST +70 / +26 / +31, 1990-2002 +11 / −12 / +17 → **doz eğrisi yok**;
  mekanizma için bir zayıflık (büyük sapma ≠ büyük etki). Eşik ≥ %2 üstünde fark ölçeklenmiyor.

## Ay sonu döngüsü (birleşik; uzun bacak seçimi sonradan)
QQQ 2002-26, ay başına P&L: R1 24,6 bp (Sharpe 0,47, 16/25 yıl) · E2 uzun 29,8 (0,74, 19/25) · **R1 + E2 uzun 54,4 (0,82, 21/25)** ·
R1 uzun + E2 uzun 47,2 (0,83, 22/25). En kötü ay ≈ −630 bp (2002/2008 türü). Broker NAS100 2018-26: R1 0,37 → R1 + E2 uzun 0,64 →
R1 uzun + E2 uzun 0,76 (aylık Sharpe).
**Kart (döngü): 6/6** — hacim 327 · +48,1 bp P 1,00 · yarılar +49,7 / +46,4 · broker × 1,5 spread +41,0 · icra 16:00 → 16:30 farkı 0,3 bp ·
ardışık pencere, çakışma yok.

## Öneri
1. **GÖLGE:** "ay sonu döngüsü" — her ay D−3 16:00 ET'de Δ (SPY − TLT ay içi), D'de Δ_D. R1: Δ ≥ +%2 KISA / ≤ −%2 UZUN (D−3 16:30 → D 16:30);
   E2: Δ_D ≥ +%2 → UZUN (D 16:30 → D+3 16:30). İki bacak ayrı etiketlenir. Veri: yfinance SPY + TLT günlük kapanış.
2. Canlı lot kararı kullanıcıda. Son dönem verisinde güçlü olanlar uzun bacaklar (R1 uzun +104, E2 uzun +56 broker); R1 kısa ≈ 0.
3. GER40 bağlanmaz. E4 yalnız mekanizma teyidi.
4. Risk: bulgu 2023'te yayımlandı; doz eğrisi yok; 1990-2002'de zayıf. Gölge ölçümü n ≈ 30 aydan sonra gözden geçirilir.
