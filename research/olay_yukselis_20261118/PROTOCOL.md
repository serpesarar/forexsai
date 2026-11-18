# Ön kayıt — NASDAQ makro olay günü yükselişi: devam eder mi? (2026-11-18)

Sonuçlara bakılmadan yazıldı. Gerekçe: §3-38 (habere dayanan hareket sürer). NDX'te olay günü düşüşü SAT C+ (UD-07); FX'te olay günü
büyük hareket iki yönde de sürüyor (UD-05). NDX'te olay günü YÜKSELİŞİ hiç sınanmadı. Coşku sınamaları (CC-01, YK-01) habersiz/koşulsuz
yükselişe baktı: "coşku ne döner ne sürer".

## Bölüm 1 — gün içi (NDX Duka 1m 2018 →; MT5 NAS100 M30 ve NQ 5m besleme teyidi)
Olay günü (CPI/NFP/FOMC/JH, → 2026-10-02), 10:00–15:30 arası ilk 30 dk bar ≥ +e, e ∈ {%0,6, %1,0} → sonraki açılışta AL → aynı gün 16:00
veya ertesi 16:00 (4 hücre). Taban: olay günlerinde rastgele 30 dk bar sonrası AL. Kontrol: habersiz günlerde aynı tetik.

## Bölüm 2 — günlük (^NDX 2008 → 2026-10, yfinance)
Olay günü kapanışı / önceki kapanış − 1 ≥ +k·σ20 (k ∈ {1, 1,5}) → kapanışta AL → ertesi kapanış (2 hücre). Taban: tüm olay günleri.
Kontrol: habersiz günlerde aynı tetik.

## Ölçüt
Bölüm 1: NDX Duka ESKİ (→ 2021-10) ve YENİ'de ort > taban ∧ > 0; MT5 ve NQ'da ort > taban; P ≥ 1 − 0,05/6 = 0,992 → B; P altı → C+.
Bölüm 2: 2008–2015 / 2016–2021 / 2022–2026 üçünde ort > taban ∧ > 0; P ≥ 0,992 → B; P altı → C+. Değilse X.
Bilgi: olay − habersiz farkı (ilke).

## EK-1 — Ters çıkan sonuçtan iki yeni hipotez (ilk koşu görüldükten sonra; kör sınav US30, US2000 (2018 →), US500 (2021 →) MT5 M30)
Gözlem (kanıt sayılmaz): olay günü sert yükselişten sonra ertesi 16:00 NDX −71, MT5 −75, NQ −123; habersiz günde +44.
- **H-a (SAT):** olay günü 10:00–15:30 ilk 30 dk bar ≥ +%0,6 → sonraki açılışta SAT → ertesi 16:00 kapat (finansman düşülür).
  Taban: olay günü rastgele 30 dk bar sonrası SAT.
- **H-b (AL):** habersiz gün aynı tetik → AL → ertesi 16:00. Taban: habersiz gün rastgele bar sonrası AL.
- **Ölçüt (her hipotez):** kör 3 endeksin ≥ 2'sinde ort > 0 ∧ > taban ∧ havuz (tarih kümeli) P ≥ 0,975 → B; P altı → C+; değilse X.
  Yıl dağılımı zorunlu (§3-37 SAT uyarısı).
