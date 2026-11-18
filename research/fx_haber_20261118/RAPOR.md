# FX: habere dayanan ve habersiz büyük günlük hareket (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md) (+ EK-1), kod `src/fh.py`, `src/od.py`. Pepperstone D1 2008 → 2026-10, 7 USD majör + 14 kör çapraz.

## Sonuç: ilke teyit (üç dönem), işlem kuralı yok
| dönüş işlemi ort bp (net), k 2σ | KEŞİF 08–15 | TEST 16–21 | YENİ 21–26 |
|---|---|---|---|
| majörler, habersiz gün | −0,1 | −4,1 | +3,9 |
| **majörler, ABD olay günü** | **−8,8** | **−15,8** | **−18,0** |
| çaprazlar, habersiz | +3,0 | +2,3 | +0,8 |
| çaprazlar, olay günü | −21,0 | −10,1 | −3,2 |

- **H-dönüş (habersiz hareketi geri al) X:** maliyet sonrası ≈ 0.
- **İlke (DD > 0) üç dönemde de teyit:** ABD olay günündeki büyük hareket ertesi gün sürüyor, habersiz hareket sürmüyor. FX-01 H4'teki
  "uçlar devam ediyor" bulgusu ağırlıkla olay günlerinden geliyor.
- **EK-1 olay günü devam kuralı (kör USD egzotikleri MXN/NOK/SEK/ZAR, bugünkü swap ile):** 2σ +3,3 bp, 3/4 çift artı, P 0,69 → **C+**
  (zayıf); 1,5σ −0,3 → X. Habersiz kontrol −8…−10 bp, ilke egzotiklerde de geçerli. Egzotik maliyeti (≈ 7 bp) kazancın çoğunu yiyor.
