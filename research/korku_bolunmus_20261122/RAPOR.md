# KORKU gecesi × CAPREV dersleri — 5 tur — RAPOR (2026-11-22)

Ön kayıt `PROTOCOL.md` (her tur kendi sonuçlarından önce commit'lendi: 48ad9375, 9935f707, 07123639, Tur 4/5 commit'leri). Kod `src/kr_motor.py`, `src/kr_olcu.py`;
sonuçlar `results/tur1…tur5.json`. Taban = canlı paket (T30 + OPEX vetosu + XP; Duka NDX 324 işlem +74,3 bp, MT5 NAS100 309 +73,9 — kartla birebir).

## Kısa cevap
CAPREV'deki çıkış KORKU'ya taşınmıyor. "Kâra kadar tut" (XU) zaten 2026-11-18'de X'ti (KC-02). Bölünmüş giriş ve yarım tutuş da Tur 1'de X çıktı. Nedeni KORKU'nun kenarının giriş gecesinde olması.
Beş turun bulduğu iyileştirme tersi: **D1 16:00'da 50 bp veya daha fazla zarardaysa bir birim ekle, ana pozisyonla birlikte XP'de çık.** Tur 3 B, Tur 4 dokunulmamış beslemeler + kart 6/6 B.
Bedeli maks. düşüşün ~1,6 kat büyümesi (Tur 5 bunu çıkışla küçültemedi).

| Tur | Fikir | Hüküm | Ana sonuç |
|---|---|---|---|
| 1 | Bölünmüş giriş (yarısı ertesi 16:00) × XP/XU × yarım tutuş | X | KEŞİF 7/7 hücre taban altı (E2 −31…−40); seçilen yarım tutuş TEST −17 |
| 2 | D1 16:00 tutuş şartı (zarar, VIX, kapanış konumu, genişlik, alt dip; 68 hücre) | X | Çöküş D1'de tanınıyor (zarar AUC 0,89 TEST) ama kesmek her hücrede kaybettiriyor (en iyi TEST −10) |
| 3 | D1'de koşullu ekleme (24 hücre) | **B** | D1 zararı ≥ 50 → +1 birim: TEST Duka +22, MT5 +21, kör 3/3, Sharpe 1,97 → 2,10, ek birim +75 / +68 |
| 4 | Donmuş ekleme, dokunulmamış EET30/NQ + kart | **B** | EET30 +23,8, NQ +6,2; kart 6/6 (n 324, ort +94,7, yarılar +23/+18 fark, spread ×1,5 +20, tek poz. +18) |
| 5 | Ek birimin çıkışı (tek gece / kendi XP / D2 kârı) | C | Düşüş TEST'te azalmadı (Duka −2.155 vs −1.966), Sharpe taban altı |

## Önerilen yapı ve bedeli (Duka NDX tüm dönem)
| | Taban (canlı) | Koşullu ekleme |
|---|---|---|
| İşlem başı (ana + ek, tek lot birimi cinsinden) | +74,3 | **+94,7** |
| İsabet | %77 | %82 |
| Sharpe | 2,17 | 2,30 |
| En kötü %5 ort. | −437 | −586 |
| Maks. düşüş | −1.226 | −1.966 |
- İşlemlerin %25'inde ek yapılıyor; ek birimler D1'deki derin zararın ardından gelen dönüşü alıyor (KORKU'da D1 zararlıları ortalamada güçlü dönüyor, Tur 2).
- NQ'da kazanç küçük (+6,2) ve Sharpe düşüyor (1,72 → 1,40); kör US2000 +6,7 ve Sharpe düşüyor. Kazanç NDX'te belirgin.
- KC-03 (ikinci korku günü eklemesi) ile ilişkisi: orada ek tetik yeni bir korku sinyaliydi ve portföy Sharpe'ı düştü; burada ek koşulu D1 zararı ve NDX Sharpe'ı artıyor.

## Kalıcı dersler
1. KORKU'nun kenarı giriş gecesinde; girişi ertelemek ya da ilk kontrolde azaltmak kenarı keser.
2. D1'de çöken işlemler tanınıyor ama derin D1 zararlıları ortalamada en çok dönenler; kesmek yerine eklemek kârlı (ortalama dönüş).
3. Ek birimin riski çıkış kuralıyla azaltılamıyor; risk bir lot kararıdır.
