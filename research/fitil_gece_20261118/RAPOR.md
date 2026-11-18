# "Fitilli gece" yapısının genişletilmesi (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/gece.py`, `src/gece_run.py`, `src/kart.py`. Kart:
`backend/data/evolution/go_live_cards/ndx_ksg_fitil_genis.json` (SHADOW).

## Sonuç

Fitilli KSG yapısını 324 hücrelik bir ızgarayla genişlettim. Seçim 2018–21'de yapıldı; ızgara şans düzeyinin üstünde (46 aday,
plasebo %95 = 39).

**Önceden yazılmış tüm ölçütleri geçen kural (B):**

> **Geniş fitilli KSG.** Koşullar:
> - son 12 saat içinde kapanmış bir **2 saatlik** mumda büyük alt fitil (alt fitil ≥ fiyatın %0,50'si, üst fitil ≤ alt/2),
> - **ve** 15:00 → 15:30 düşüş.
>
> İşlem: **15:30'da AL, ertesi işlem günü 16:00'da çık.**

| veri | fitilli | fitilsiz (aynı KSG koşulu) |
|---|---|---|
| ESKİ 2018–21 (seçim) | +60,1 bp (n 98) | +0,2 |
| **YENİ 2021–26 (kör)** | **+41,1 bp** (n 115, P %98,8; Bonferroni %98 geçti) | −0,6 |
| **MT5 NAS100** (bağımsız besleme) | **+45,3** (n 215) | +1,0 |
| **EET30** (başka broker) | **+50,5** (n 180) | +1,4 |
| **NQ vadeli** | **+47,1** (n 68) | +9,1 |

**2. KURAL kartı 6/6** (Dukascopy 2018–26, n 215, yılda ~24 işlem):

| ölçü | değer |
|---|---|
| ortalama | +51,8 bp (ay-blok P %100) |
| medyan | +40,4 bp |
| isabet | %63,7 |
| en iyi 5 işlem hariç | +34 bp |
| iki yarı | +52,0 / +51,6 |
| spread × 1,5 | +51,1 |
| 15:31 girişi | +47,0 |
| tek pozisyon | +39,6 (n 189) |

**Yıllar (9/9 artı):** 2018 +42 · 2019 +117 · 2020 +75 · 2021 +25 · 2022 +15 · 2023 +39 · 2024 +48 · 2025 +86 · 2026 +55 bp.

**Risk (stopsuz ~24 sa tutuş):**
- standart sapma 204 bp,
- en kötü işlem **−633 bp**,
- en kötü %5 −235 bp,
- birikimli en büyük düşüş −1.153 bp.

Kâr ortalama +52 bp ama tek bir kötü gün 6 işlemlik kârı silebilir. Lot buna göre küçük tutulmalı. Felaket stopu henüz sınanmadı
(sonraki adım).

**Orijinal fitilli KSG** (1h, 6 sa, 16:00 → 09:30) bu çerçevede de B:
- YENİ +31,4 vs +1,1 (P %99,8),
- MT5 +31,3 / EET30 +31,8 / NQ +27,5, hepsi fitilsizden iyi.

Daha düşük kazanç, daha kısa tutuş (gece).

## Ne öğrenildi (genişletme haritası)

1. **KSG koşulu şart.** Öne çıkan 46 hücrenin hepsinde KSG var. Fitil tek başına gece primini artırmıyor; "gün içi panik fitili
   + kapanışa doğru yeniden düşüş" birlikte çalışıyor.
2. **Ertesi gün 16:00'ya tutmak getiriyi artırıyor** (+31 → +41…+52 bp), riski de artırıyor.
3. **2 saatlik fitil mumu ve 12 saatlik pencere**, 1 saatlik / 6 saatlikten daha çok olay ve benzer beklenti veriyor (yılda 24 vs
   22).
4. **15:30 girişi 16:00'dan iyi** (ertesi gün çıkışında): son yarım saatlik toparlanmanın bir kısmı yakalanıyor.
5. **Eşik:** %0,35 daha çok olay, daha düşük ortalama (+33…+37); %0,50 en iyi denge; %0,75 çok seyrek.
6. **DAX'a taşınmıyor** (G7: −22,7 bp, n 39). Mekanizma ABD endekslerine özgü.

## YENİ'de eşiğin hemen altında kalan, beslemelerde güçlü hücreler (hüküm X, bilgi için)

| hücre | YENİ | MT5 / EET30 / NQ |
|---|---|---|
| 2h, 6 sa, 15:30 → ertesi 16:00 | +39,0 (P 0,975) | +46,7 / +52,6 / +44,1 |
| 1h, 6 sa, 15:30 → ertesi 16:00 | +36,6 (P 0,971) | +48,3 / +43,4 / +95,6 |
| 30m %0,35, 3 sa, 16:00 → ertesi 16:00 | +39,9 (P 0,898) | +54,5 / +54,6 / +98,7 |

Aynı aile, aynı yön. Tek seçilmiş hücrenin şans eseri olmadığını gösteriyor.
