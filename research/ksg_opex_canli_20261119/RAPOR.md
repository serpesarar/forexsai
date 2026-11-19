# KSG OPEX vetosu — canlı kodla yeniden oynatma — RAPOR (2026-11-19)

- Ön kayıt `PROTOCOL.md`; kod `src/oynat.py` (yeni deneme/ksg_live.find_signal + 09:30 çıkışı + VIX ≥ 25 çift lot; veto korku_live.opex_veto).
- Sonuç `results/oynat.json` (gece listeleri git dışı CSV).

| | MT5 NAS100 | Duka NDX |
|---|---|---|
| KSG gecesi (2018-05 → 2026-11-05) | 1.046, +7,2 bp | 1.034, +6,1 bp |
| Vetolanan (vadeye 0–2 işlem günü) | 158 | 155 |
| Vetolanan ort. ham / lot ağırlıklı | −0,1 / −1,8 bp (P eksi 0,51) | −4,5 / −6,6 bp (P 0,79) |
| Çift lotlu vetolanan | 22 gece, −13,6 bp | 23 gece, −21,0 bp |
| Yarılar (lot ağırlıklı) | −1,4 / −2,3 | −5,5 / −8,1 |
| Kalan ort. | +8,5 | +8,0 |
| Kitap Sharpe (yıllık) | 0,875 → 0,947 | 0,771 → 0,905 |
| Yıllık toplam bp | 1.322 → 1.359 | 1.166 → 1.298 |
| Maks. düşüş bp | −2.165 → −2.145 | −2.884 → −2.443 |

- Vetolanan geceler yıl yıl (MT5): 2018 −12, 2019 −4, 2020 +21, 2021 −13, 2022 −24, 2023 −16, 2024 +31, 2025 +15, 2026 −2 → 6/9 eksi.
- Vadeye gün (MT5 / Duka): 0 gün −4,3 / −7,1; 1 gün +9,5 / +5,4; 2 gün −4,4 / −10,3; 3 gün +0,3 / −2,5; 4 gün +42 / +41 (bilgi; pencere değiştirilmedi).
- **Hüküm:** ön kayıtlı dört ölçüt iki beslemede sağlandı → **bağlama önerilir.** Etki küçük: canlı brokerde vetolananlar ≈ 0; kazanç sıfır beklentili
  geceleri ve çift lotlu kayıpları atmaktan. Bağımsız kanıt §2.94 GX-05 (6/6 besleme, havuz P 1,00).
- Yoğunlaşma: canlı KORKU (T30) aynı vetoyu taşıdığı için bu gecelerde ikisi birlikte kapalı kalır; NAS100'de korku gecesi yığılması azalır.
