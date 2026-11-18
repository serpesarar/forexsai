# Opsiyon piyasası korkusu (VIX vade eğrisi, VIX sıçraması) → NDX (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/ve.py`, `src/kart.py`. Kart:
`backend/data/evolution/go_live_cards/ndx_vix_ters_egri_5g.json` (SHADOW, C+).

## Sonuç

Fiyat yerine opsiyon piyasasının korkusundan sinyal aradım:
- VIX9D / VIX,
- ters vade eğrisi VIX / VIX3M,
- VIX'in bir günlük sıçraması.

İşlem: ertesi sabah 09:30'da AL; çıkış aynı gün, 1 gün ya da 5 gün sonra 16:00. 18 hücre, seçim 2018–21.

**Ön kayıt ölçütlerini geçen hücre (B), ama kart C+'ya indirildi:**

> **Ters VIX eğrisi → 5 gün tut:** dünkü kapanışta VIX ≥ VIX3M → bugün 09:30 AL, 5. işlem günü 16:00 çık.

| | sinyalli | sinyalsiz |
|---|---|---|
| ESKİ 2018–21 | +95,0 bp (n 99) | +33,4 |
| **YENİ 2021–26 (kör)** | **+137,9** (n 64, P %99,5) | +6,3 |
| MT5 / EET30 / NQ | +96 / +103 / +76 | +17 / +18 / +16 |
| korku gecesi (K1) olmayan günler | +98,7 | +14,4 |

**Ama bağımsız karar sayısı az ve kuyruk riski çok büyük:**

| | tüm sinyaller | tek pozisyon |
|---|---|---|
| işlem | 163 | 55 (37 bağımsız kriz epizotu) |
| ortalama | +111,8 bp | +74,6 bp |
| en iyi 5 hariç | +84,6 | **+13,9** |
| en kötü işlem | −1.578 bp (−%15,8) | aynı |
| birikimli maxDD | −7.301 | **−2.982 bp (−%30)** |
| iki yarı | | +6,4 / +140,4 |
| eksi yıllar | | 2018 (−37), 2020 (−2), 2025 (−89) |

**Hüküm: C+.** Kriz anında 5 gün stopsuz alım ortalamada kazandırıyor. Ama kâr birkaç büyük toparlanmadan geliyor ve tek bir kötü
kriz (2020 Mart tipi) %15'lik kayıp yazıyor. Bu hâliyle canlıya uygun değil. Felaket stoplu / küçük lotlu bir sürüm ayrı bir ön
kayıtla sınanabilir.

## Diğer bulgular

- **VIX sıçraması (≥ +%15) → ertesi gün:**
  - Gün içi toparlanma ESKİ'de +54,5 bp, ama YENİ'de +3,1 (geçmedi).
  - **5 gün tutmak −41 bp:** sıçramadan sonra düşüş günlere yayılıyor.
  - Sıçrama "hemen al" sinyali değil.
- **VIX9D / VIX (çok kısa vadeli panik):** hiçbir tutuşta tabandan iyi değil.
- Ters eğri sinyali korku gecesiyle %30 örtüşüyor; ayrı bir bilgi taşıyor (K1 dışında da +98,7 vs +14,4). Ama riski korku
  gecesininkinden çok daha büyük.
