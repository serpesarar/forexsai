# Ön kayıt — Emtia uzlaşma (settlement) korkusu: altın 13:30, petrol 14:30 ET (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
Korku gecesi (K1/K3) ABD hisse endekslerinde B, Avrupa'da X (GN-06). Altında **16:00 NY** sınaması X'ti (GI-02). Emtiada günün resmî
kapanışı vadeli uzlaşmasıdır: COMEX altın 13:30 ET, NYMEX WTI 14:30 ET. Kapanışa doğru emilen korku bu saatlerde aranmalı (yeni tanım).

## Veri
- Altın: Dukascopy XAU 1m (`fibo_altin_bolge_20261116/cache`, spread 2025 ASK medyanı) seçim/ana; kör MT5 XAUUSD M30 (spread puan × 0,01).
- Petrol: MT5 SpotCrude M30 (spread puan × 0,001), tek besleme → en fazla C+.

## Tanımlar (uzlaşma saati U; altın U = 13:30, seans 08:20 → 13:30; petrol U = 14:30, seans 09:00 → 14:30; NY saati)
- **K1(e):** P(U) ≤ seans TWAP × (1 − e) ∧ P(U) < P(U − 60 dk); e ∈ {%0,5, %1,0}.
- **K3(e):** P(U) / P(U − 60) − 1 ≤ −e; e ∈ {%0,3, %0,6}.
- U'da AL (ask), ertesi işlem günü U'da çık (bid); finansman `lib.FIN_BP_PER_DAY` (yaklaşık).
- 2 emtia × 4 = 8 hücre; taban = tetiksiz günler.

## Ölçüt (hücre başına)
1. ESKİ (→ 2021-10) ve YENİ'de ikisinde de tetik ort > 0 ∧ > taban.
2. Tüm dönem P ≥ 1 − 0,05/8 = 0,994.
3. Altın için kör MT5'te tetik ort > taban.
Altın: hepsi → B; 1+3 → C+; yalnız 1 → C; değilse X. Petrol: 1+2 → C+; yalnız 1 → C; değilse X.
