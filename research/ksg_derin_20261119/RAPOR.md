# KSG derin araştırma — gece yolu, bilanço gecesi, koşullu çıkış — RAPOR (2026-11-19)

- Ön kayıt `PROTOCOL.md` (+ EK-1 E116 kontrolü, EK-2 betimleyici doz). Kod `src/derin.py`, `src/ek1.py`. Sonuç `results/derin.json`, `ek1.json`, `ek2.json`.
- Geceler canlı KSG koduyla (MT5 NAS100 1.046, Duka 1.034, kör US500/US30/US2000), 2018–2026-11-05; KEŞİF ≤ 2021-10.

## A — Gece yolu (NAS100; dilim toplamı = net, medyan sapma 0,09 bp)
| Dilim | Kazanan ort | Kaybeden ort | Tüm geceler | Kaybedenin en eksi dilimi |
|---|---|---|---|---|
| Kapanış sonrası 16:00→18:00 | +5,4 | −6,2 | +0,3 | %8,5 |
| Asya 18:00→03:00 | +30,0 | −23,1 | **+6,7** | **%38,5** |
| Avrupa 03:00→08:30 | +18,2 | −20,6 | +1,2 | %36,1 |
| ABD sabahı/veri 08:30→09:30 | +10,2 | −10,4 | +1,2 | %16,8 |
- KSG'nin kenarı büyük ölçüde Asya seansında birikiyor. Kaybeden tipleri: **Avrupa'da kayan** (343 gece, −54 bp: Avrupa −34) ve
  **Asya'da çöken** (114 gece, −89 bp: Asya −78, Avrupa'da kısmen toparlanma +21).
- **Grup tablosu (KEŞİF / TEST ort bp, kaybeden %):**

  | Grup | KEŞİF | TEST |
  |---|---|---|
  | FOMC öncesi | +45,9 (%20) | +30,9 (%25) |
  | Ertesi sabah CPI/NFP | +13,1 (%31) | +19,1 (%33) |
  | Bilanço gecesi | +22,5 (%38) | +26,2 (%31) |
  | KORKU-T30 gecesi | +24,8 | +10,9 |
  | KORKU dışı | +0,1 | +5,6 |
  | Vadeye 0–2 gün | −2,9 | +2,2 |
  | Salı | +14 | +13 |
  | Cuma | −6,5 | +1,6 |

  VIX ve son saat derinliği üçte birlikleri dönemler arası tutarsız. **Planlı olay geceleri kaybedenin en az olduğu geceler.**

## B — KSG ∧ mega-cap bilanço gecesi (12 şirket, kapanış sonrası açıklama)
| | Bilanço | Bilançosuz | Fark | P |
|---|---|---|---|---|
| NAS100 KEŞİF / TEST / tüm | +22,5 / +26,2 / +24,7 | +4,5 / +3,9 / +4,2 | +18,0 / +22,3 / +20,5 | 0,88 / 0,99 / 0,996 |
| Duka tüm | +24,8 | +2,8 | +22,1 | 0,998 |
| Kör US500 / US30 / US2000 (tüm) | | | +3,6 / +3,7 / +6,7 | 0,74 / 0,72 / 0,82 |
- Ön kayıt ölçütü **B** (iki dönem, iki besleme aynı işaret, P 0,996, kör 3/3 aynı işaret).
- **EK-1 (E116):** son saati YÜKSELEN bilanço gecesi −0,8 bp (bilançosuz −6,4) → bilanço primi KSG dışında +5,6, KSG içinde +20,2; fark-farkı
  +14,6 bp, **P 0,86** → etkinin bir kısmı genel bilanço gecesi primi; KSG'ye özgü kısmı istatistiksel olarak kanıtlı değil.
  KSG ∧ bilanço yıl yıl MT5 9/9 artı (2026 +19,7), Duka 8/9.
- **EK-2 (doz ×2, betimleyici):** Sharpe TEST 0,82 → 1,08 (Duka 0,72 → 0,99) ama KEŞİF 1,12 → 1,06 (Duka 1,13 → 1,08), KEŞİF maxDD büyür → doz sağlam değil.

## C — Koşullu çıkış (24 hücre)
- Zarardayken kesmek her saatte tabandan kötü (en kötü 20:00 −50 bp → −4,1 bp/gece); kâr almak KEŞİF'te +1,5…+2,4 → TEST NAS100 −0,9 / +0,2,
  Duka −0,9 / +0,8, P < 0,75 → **X**. Kaybeden gece ortasında da tanınmıyor (kesilenlerin çoğu sabaha döner).

## Hüküm
- **A:** KSG Asya seansının primi; kaybedenler iki tipte (Avrupa kayışı, Asya çöküşü), ikisi de girişte tanınmıyor (KA-01).
- **B:** KSG ∧ bilanço gecesi **B (ön kayıt)**, ama E116 kontrolüyle **KSG'ye özgü kısmı C+**; doz Sharpe'ı iki dönemde birden artırmıyor → canlıya doz
  önerilmez; ileri gölge etiketi önerilir (bilanço gecesi bayrağı).
- **C:** koşullu çıkış **X** — "SL'yi gece içinde kesmek" KSG'de de kazananı öldürüyor (§3-48 ile aynı).
- Yeni ilke adayı: KSG'de kaybedenin en az olduğu geceler **planlı olay öncesi geceler** (FOMC, CPI/NFP, bilanço) — olay öncesi gece primi.
