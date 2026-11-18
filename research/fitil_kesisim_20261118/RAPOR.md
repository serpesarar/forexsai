# Büyük alt fitil × kanıtlı NDX kuralları — "fitilli KSG" (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md) (+ EK-1). Kod: `src/kesisim.py`, `src/ksg_dogrulama.py`. Kart:
`backend/data/evolution/go_live_cards/ndx_ksg_fitil.json` (SHADOW).

## Sonuç

Fitili tek başına sinyal olarak kullanan dört aile (~3.600 hücre) kâr kapısı vermemişti. Bakış açısını değiştirdim: fitili zaten kâr eden
kanıtlı kurallara **filtre** olarak koydum.

**Bulunan:**

> **Fitilli KSG:** NASDAQ'ın son nakit saati (15:00 → 16:00) düşerse **ve** son 6 saat içinde büyük alt fitilli bir 1 saatlik mum
> oluştuysa (alt fitil ≥ %0,50, üst fitil ≤ alt/2) → 16:00'da AL, ertesi sabah 09:30'da çık.

| | n | ortalama | not |
|---|---|---|---|
| Dukascopy 2018–26, fitilli | 183 | **+28,6 bp** | 2018–21 +22,9 · 2021–26 +33,1 |
| Dukascopy, fitilsiz KSG | 895 | +1,9 bp | fark P %99,6 (Bonferroni %98,75 geçti) |
| **MT5 NAS100 (bağımsız besleme)**, fitilli | 149 | **+38,4 bp** | fitilsiz +3,7; P %99,9 |
| oynaklık plasebosu (fitilsiz ama hareketli saat) | 154 | +8,8 bp | fitil daha iyi, P %93 |
| 2. KURAL kartı | 183 | 6/6 | yıllar: 2018 −6 · 2019 +2 · 2020 +39 · 2021 +21 · 2022 +15 · 2023 +43 · 2024 +81 · 2025 +31 · 2026 +59 |

**Her VIX bandında ayrı ayrı çalışıyor**, yani korku rejiminin kopyası değil:

| VIX | fitilli | fitilsiz |
|---|---|---|
| < 18,4 | +33,4 bp (n 46) | +0,2 |
| 18,4–25 | +20,9 (n 57) | −0,4 |
| ≥ 25 | +31,3 (n 80) | +15,3 |

**Başka piyasalar:**
- US30: +25,2 vs −0,4.
- US2000: +14,3 vs +6,7.
- US500 (2021+): −9,2 vs +3,7 (n 36).
- 3 piyasanın 2'sinde artı; havuz P %88,6, eşik %90'ın hemen altında.

**Hüküm (ön kayıttan): C+.** Bu araştırma dizisindeki en güçlü sonuç. NASDAQ'ta iki bağımsız beslemede ve 9 yılın 8'inde sağlam,
plasebo ve VIX'e dayanıklı. Başka ABD endekslerine genellemesi kıl payı eksik. Kart SHADOW yazıldı. Canlıya bağlanmadı; kararı
sizin.

## Nasıl kullanılabilir

KSG zaten canlı (lot 0,5). Fitilli KSG onun alt kümesi. İki kullanım var:
1. **Doz:** fitilli gecelerde KSG lotu artırılır (VIX25 çift lot dozu gibi).
2. **Filtre:** yalnız fitilli gecelerde KSG açılır. Yılda ~20 işlem, ortalama +29 bp.

Fitilsiz KSG ortalaması +1,9 bp ≈ 0. KSG'nin kârının büyük kısmı bu gecelerden geliyor.

## Diğer kesişimler (8 hücre, seçim yok)

| kural | fitilli vs fitilsiz (W 6 sa / 24 sa) | hüküm |
|---|---|---|
| C3b | +77 vs +65 bp / +105 vs +52 (P 0,60 / 0,93) | iz, Bonferroni altı |
| ORB × VIX | fitilliyle **daha kötü** (+0,02 vs +0,23R) | fitil ORB'ye ters |
| CAPREV | +0,50 vs +0,24R / +0,43 vs +0,18 (n 15 / 41) | iz, n küçük |
| **KSG** | **+28,6 vs +1,9 / +22,9 vs +2,3** | **geçti** |

## Mekanizma

Gün içinde büyük alt fitil (panik satış ve hızlı geri alım) ile kapanışa doğru yeniden düşüş birleşince gece kısa pozisyonlar
kapanıyor ve fiyat toparlanıyor. Bu, defterin "korku döner" ilkesinin gecelik hâli. Fitil olmadan, kapanıştaki düşüş tek başına
çok az şey söylüyor (+1,9 bp).

## Ek doğrulama (EK-2) — dokunulmamış ve bağımsız veri

| veri | fitilli | fitilsiz | P | yıllar |
|---|---|---|---|---|
| EET30 (başka broker, 2016–25) | **+33,7 bp** (n 131) | +4,4 | %99,5 | olaylı 8 yılın 7'si artı |
| NQ vadeli (2019–24) | **+26,4 bp** (n 67) | +8,4 | %89,6 | 5/5 |
| Dukascopy 2016–17 | n 2 | — | — | 2016–17'de büyük fitilli saat yok, sınanamıyor |
| havuz | +30,3 | +5,4 | %99,7 | |

Fitilli KSG dört bağımsız beslemede aynı yönde: Dukascopy, MT5 NAS100, EET30, NQ. Ön kayıttaki "her veride artı" koşulu, 2016–17'nin
2 olayı yüzünden düştü; bu nedenle sınıf C+ kalıyor.

Sakin yıllarda kural hiç tetiklenmiyor. Bu bir sınır: piyasa uzun süre sakin kalırsa işlem de olmaz.
