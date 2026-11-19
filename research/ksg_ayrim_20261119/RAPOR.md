# KSG kaybeden/kazanan ayrımı — RAPOR (2026-11-19)

- Ön kayıt `PROTOCOL.md`; kod `src/ksg_ayrim.py` (geceler canlı kodla: ksg_opex_canli_20261119/oynat.py; özellikler xp_paket_ayrim motor.py).
- Sonuç `results/ksg_ayrim.json` (özellik tablosu parquet, git dışı).

## Veri
NAS100 1.046 gece (KEŞİF 439 / TEST 607, kaybeden %43 / %44, ort +7,1 / +7,3 bp); Duka 1.034; kör US500 790, US30 1.050, US2000 1.060.
543 özellik: 6 TF (30 dk–hafta) × 4 kanal uzunluğu + `ta` 86 gösterge + hizalanma + dünkü VIX, vadeye gün, haftanın günü.

## Sonuçlar
| Adım | Sonuç |
|---|---|
| Tek tek (aile eşiği \|AUC−0,5\| ≥ 0,097) | **0 özellik geçti.** En güçlüler KEŞİF 0,43–0,56 → TEST 0,49–0,52 (dünkü VIX 0,434 → 0,502; 4 sa kanal R² 0,562 → 0,518). KEŞİF↔TEST r 0,30 |
| L1 (C seçimli) | TEST AUC 0,522; vetolanan %15 **+16,0** vs +6,0 bp (ters), Sharpe 0,893 → 0,691 → X |
| LightGBM | TEST AUC 0,490; %15 veto −0,2 vs +8,1 (P 0,56), Duka −10,2 vs +7,7; Sharpe 0,893 → 0,955 ama P < 0,9 ve kör 1/3 → X |
| LightGBM regresyon | TEST AUC 0,493; vetolanan +9,5 vs +6,8 → X |
| Kümeleme | 2 küme, kaybeden %43 / %43 (TEST %45 / %43); tek fark ortalama +5 vs +12 bp, kaybeden oranı aynı |

## Hüküm
- **X.** KSG'de kaybeden gece girişte kazanandan ayrılmıyor; korku paketindekinden (§2.99/§2.100, AUC ≈ 0,6) de zayıf. Neden: gece başına
  kenar +7 bp, gece oynaklığı ≈ 100 bp → kazanıp kaybetmek büyük ölçüde gece haberine bağlı.
- **"SL olanları çıkarmak" için kanıtlı tek yol, sıfır beklentili geceleri önceden kanıtlanmış kapılarla atmak:**
  - OPEX vetosu (GX-05/06, B, bağlama onayı bekliyor): Sharpe 0,875 → 0,947.
  - Fitilli KSG (§2.68 FK-01…03, B): fitilli +28,6 / fitilsiz +1,9 bp (MT5 +38,4 / +3,7). Bunu kural olarak kullanmak gecelerin ≈ %83'ünü atar.
  - VIX ≥ 25 dozu (canlı) ve FOMC öncesi gece (B).
  Bunlar kaybedeni değil, sıfır beklentili geceyi ayırır.
