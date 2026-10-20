# Ön-kayıt — USOIL son 1 hafta otopsisi → düzeltme adayları ve sınaması (2026-10-20)

Otopsi: `output/islem_otopsi/2026-10-20_2222_usoil/` (120 gün 157 işlem, ortR −0,10; son hafta 5 MOMSR BUY 10 lot: 3 TP /
2 SL; iki SL de "hiç çalışmadı", fiyat 1h EMA50'nin 2,3 ve 2,9 ATR üstünde; biri 12:15 UTC). Canlı USOIL = yalnız
MOMSR BUY (SELL yasak B1, breakout gölge B17). Defter: B15 USOIL_SESSION_GATE (13 UTC öncesi BUY, GÖLGE, B, 2026-09-30
gölgeye alındı → 09-30 sonrası ileri dönem), IO-06 DAR_STOP (X; etkinin çoğu USOIL_BRK), IO-22 (USOIL'de SQZ ters),
M9/M11/OLD-20 (geometri/çıkış değişiklikleri — burada aday DEĞİL), TREND_GATE/POSITION_GATE zaten canlı.

## Adaylar (eşikler sonuca bakmadan; tertiller botun 10-13 öncesi MOMSR BUY işlemlerinden)
- C1 seans: UTC saat < 13 → açma (B15 birebir).
- C2 uzama: (fiyat − EMA50 1h) / ATR14 1h ≥ üst tertil → açma (son haftanın iki SL'si).
- C3 dar stop: SL mesafesi / ATR14(5m) ≤ alt tertil → açma (otopsi §10 en güçlü keşif adayı; IO-06 yakını).
- C4 = C1 ∨ C2 · C5 = C1 ∧ C2.
Tanımlar yalnız kapanmış barlarla (1h EMA span 50, ATR Wilder 14; islem_otopsi `pre_dist_ema50_1h` ile aynı).

## Kaynaklar
- K1 bot MOMSR USOIL BUY gerçek işlemleri (R gerçek): keşif < 2026-09-30, **ileri ≥ 09-30** (B15 gölgeye alındığı
  tarih; C1 için seçimde hiç kullanılmamış), son hafta ≥ 10-13 ayrıca.
- K2 botun ENGELLENEN USOIL BUY sinyalleri (kutu gate_skipped; position/trend kapısı; "shadow" ve breakout nedenleri
  hariç), 30 dk'da bir.
- K3 panel USOIL BUY sinyalleri 02-18 → 10-20 (7 model, model başına 30 dk'da bir).
K2/K3 simülasyonu: sonraki 1m açılış + spread 0,03, sabit referans geometri TP %1,04 / SL %1,49 (config), aynı barda iki
bariyer → SL, 360 dk tavan (çözülmeyen = son kapanış R). Barlar: 05-20 öncesi `wti_transfer_20261002/data/clean_1m`,
sonrası indicator_snapshots (broker).

## Ölçü ve geçme
Her aday × kaynak: engellenen n, ortR(engel) vs ortR(kalan), kurtarılan R, gün-blok P(kurt>0), aynı sayıda rastgele
engellemeye göre yüzdelik (C2/C3 için ayrıca saat-eşli), 4 kronolojik çeyrek.
**Düzeltme adayı (gölge → kart):** K1 keşifte kurt_R > 0 ve P ≥ %90 · K3'te aynı işaret, P ≥ %90 ve ≥3/4 çeyrek ·
K2'de aynı işaret · K1 ileride aynı işaret. 5 aday × 3 kaynak denendi (çoklu test notu). Geometri/çıkış önerilmez.
