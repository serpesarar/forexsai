# Petrol EIA haftalık envanter tepkisi (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/pe.py`. MT5 SpotCrude M30, tek besleme.

## Sonuç: büyük tepkiler sürüyor (C); habersiz büyük hareketler dönüyor (iz)
| hücre | ESKİ devam (n) | YENİ devam (n) | tüm P | aynı saat, EIA'sız günler |
|---|---|---|---|---|
| ≥ %1 tepki → 14:30 | +5 (33) | +35 (34) | 0,76 | +12 |
| ≥ %1 tepki → ertesi 14:30 | +29 (33) | +36 (33) | 0,81 | **−100 / −47** |
| ≥ %0,5 → 14:30 / ertesi | −16 / +41 | +2 / −11 | 0,32 / 0,72 | |

- EIA'nın ilk 30 dakikasındaki ≥ %1'lik tepki iki dönemde de devam ediyor (+20…+33 bp), istatistik zayıf → C.
- **Yan bulgu (ön kayıtlı değil):** EIA olmayan günlerde 10:30'da 30 dakikada ≥ %1 hareket ertesi güne kadar dönüyor
  (devam ESKİ −100, YENİ −47 bp). "Habere dayanan hareket sürer, habersiz hareket döner." Başka bir petrol beslemesinde ön kayıtla
  sınanmalı (backlog). NDX'te aynı ayrım `haber_korku_20261118`'de sınandı (C+).
