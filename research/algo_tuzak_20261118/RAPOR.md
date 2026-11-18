# "Algoları ters köşeye yatıran" tuzak yapıları, son 5 yıl odaklı (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md) (+ EK-1 devam aynası), kod `src/at.py` (`AT_MODE=1` tuzak / `-1` devam).
Dönemler: ESKİ YAPI 2018-04 → 2021-10 · KEŞİF 2021-11 → 2024-06 · TEST 2024-07 → 2026-11.

## Sonuç 1: son 5 yılda tuzak (dönüş) yapısı yok → 14/14 X
KEŞİF'te 14 tuzak hücresinin 13'ü eksi:
| tuzak | KEŞİF ort (bp) |
|---|---|
| sabah trendini 13:00'te tersle | −8,9 (P 0,048) |
| dün tepesi "başarısız kırılımında" SAT | −21,5 vs taban −3,9 |
| sakin ralliyi SAT, 5 / 10 gün | −113 / −221 (taban −25 / −50) |
| günün trendini 15:00'te tersle | −4,5 |
Son 5 yılda baskın yapı devam: "her şey yolunda" görüntüsünün ardından gelen ters dönüş, sınanan biçimlerin hiçbirinde ortalamada yok.

## Sonuç 2 (EK-1): devam aynası, TEST'te çoğu düştü
| hücre | ESKİ | KEŞİF | TEST (kör) | MT5 TEST | hüküm |
|---|---|---|---|---|---|
| sakin rallide AL, 10 gün | −39 vs +90 | **+167** vs −3 | +31 vs +37 | −35 | X |
| sakin rallide AL, 5 gün | −60 vs +47 | +86 vs −2 | −52 vs +22 | −96 | X |
| sahte başarısız PDH kırılımında AL | +11 | +20 | −5 | +0,9 | X |
| **sabah trendine 13:00'te katıl** | +3,8 | +7,6 | **+7,2** (P 0,86) | +7,2 | **C+** |

- **Sakin ralli rejimi üç dönemde yön değiştirdi:** 2018–21'de döndü, 2021–24'te sürdü, 2024–26'da yine döndü (5 gün). Kural yok.
- Sabah trendine katılmak dört dönemde de küçük artı (+4…+8 bp): gün içi momentumun bilinen hâli (ME-06/QS-09 yakını).
