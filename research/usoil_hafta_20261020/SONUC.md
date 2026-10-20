# Sonuç — USOIL son 1 hafta otopsisi + düzeltme adayları (2026-10-20)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) (+ `kapilar.py` başlığındaki ek). Otopsi: `output/islem_otopsi/2026-10-20_2222_usoil/rapor.md`.

## Son hafta (10-13 → 10-20): 5 işlem, hepsi MOMSR BUY 10 lot
| giriş (UTC) | sonuç | $ | not |
|---|---|---|---|
| 10-13 18:28 | TP | +1.147 | temiz |
| 10-18 22:09 | SL | −1.486 | hiç çalışmadı; Asya açılışı |
| 10-19 12:13 | TP | +1.032 | |
| 10-19 18:27 | TP | +1.196 | |
| 10-20 12:15 | SL | −1.515 | hiç çalışmadı; yön yanlış |
Hafta toplamı **+374 $**. WR %60 (başabaş ≈%59, RR ≈0,70). Hafta ortalamadan kötü değil; iki SL de "hiç çalışmadı" tipi
(giriş anı rastgele düzeyinde; otopsi §2b: botun USOIL girişi rastgeleden −0,06R, P %23).
120 gün: 157 işlem ortR −0,10; zararın kaynağı kapanmış/gölgedeki aileler (USOIL_BRK −9,1R, CHREV SELL, MOMSR SELL —
SELL artık yasak B1). Canlı tek scope MOMSR BUY: 92 işlem +0,01R (başabaş).

## Adaylar (eşikler sonuçtan önce) — `results/rapor.md`
| aday | bot keşif (<09-30) | bot ileri (09-30→) | engellenen 398 | panel 9.153 (02→10) | panel bot dönemi | hüküm |
|---|---|---|---|---|---|---|
| C1 13 UTC öncesi BUY yok (B15) | +3,5R, P %78 | −0,4R | −6,6R | −65R | +1R | GEÇMEDİ |
| C2 uzama ≥3,0 ATR | −2,4R | — | −4,4R | +0,6R | −17R | GEÇMEDİ |
| C3 dar stop ≤2,71×ATR5 | +0,6R | — | — | −30R | −3,7R | GEÇMEDİ |
| C4 C1∨C2 | +0,3R | −0,4R | −11R | −114R | +15R | GEÇMEDİ |
| C5 C1∧C2 | +0,8R | — | +0,2R | +49R (rastgele %99,9) | **−32R** | GEÇMEDİ (dönem tersine) |
Son haftanın SL'leri EMA50'nin 2,3–2,9 ATR üstündeydi ama bu botun USOIL BUY'ları için normal (üst tertil 3,0 ATR).

## Canlı kapılar doğru mu engelliyor? — `results/kapilar.md` (aynı geometri, 07-29 → 10-20)
Açılan 42 MOMSR BUY +0,051R · konum kapısının engellediği 280 +0,031R (fark −0,02 [−0,37…+0,34]) · trend kapısının
engellediği 118 −0,058R (fark −0,11 [−0,51…+0,35]). Kapılar ne belirgin kazandırıyor ne kaybettiriyor; trend kapısı doğru
yönde. Değişiklik önerilmez.

## Hüküm
**Kanıtlı düzeltme YOK.** B15 (seans) gölgede kalmalı — ileri dönemde de tutmadı. Geometri/çıkış değişiklikleri defterde
zaten elendi (M9, M11, OLD-20) ve bu turda aday yapılmadı. USOIL'de bekleyen tek risk konusu lot (10 lot, SL ≈1.500 $):
bu kenar değil risk kararı. NASDAQ'taki fren hatası (B20) USOIL_BRK magic'ini de kapsıyordu ve düzeltildi.
