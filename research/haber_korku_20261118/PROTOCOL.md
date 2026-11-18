# Ön kayıt — Habere dayanan korku ve habersiz korku (2026-11-18)

Yazılış: petrol EIA sınamasının yan bulgusu görüldükten sonra (habersiz büyük hareket döndü, EIA hareketi sürdü). NDX için bu soruya
hiç bakılmadı.

## Hipotez
Korku gecesi (K1, §2.71) habersiz günde (akış kaynaklı) daha çok döner. Makro olay gününde (CPI/NFP/FOMC; bilgi kaynaklı) daha az döner.
E116 karıştırıcısı: her grubun kendi tabanı (aynı tür günlerin K1'siz geceleri) ile kıyaslanır.

## Veri
Takvim `xau_best_days_20261015/makro/out/calendar.csv` (CPI, NFP, FOMC, Jackson Hole; → 2026-10-02, analiz bu tarihe kadar).
NDX Duka, MT5 NAS100; kör US30, US2000 (MT5 M30).

## Ölçüt
Fark-in-fark DD = (K1 − taban)_habersiz − (K1 − taban)_olay. NDX'te ESKİ ve YENİ'de ikisinde de DD > 0 ∧ kör US30 ve US2000'de DD > 0
→ C+ (habersiz korku daha güçlü; olay gününde lot düşürme etiketi). Ters yönde aynısı → C+ (ters). Değilse X.
Olay günü K1 sayısı küçük beklenir (~30); bu yüzden en fazla C+.
