# Ön kayıt — Büyük alt fitil × kanıtlı NDX kuralları (kesişim) (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe

Kullanıcı: "büyük fitil bıraktıktan sonra kâr yakala; bakış açını değiştir."

Fitil tek başına sinyal olarak 4 ailede (~3.600 hücre: §2.65–2.67, FR) kâr kapısı vermedi. Ama yön bilgisi gerçek:
- FZ-02: fitil sonrası SAT, rastgele SAT'tan çok kötü.
- FR-06: fitilin ret bilgisi plasebo üstü.

**Yeni bakış açısı:** fitili tek başına giriş değil, **zaten kâr eden kanıtlı kurallara filtre** olarak kullanmak (KS-01 kesişim yöntemi).
Kuralların kendisi canlıda ya da kanıtlı (NX-01).

## Kurallar (değiştirilmeden; `research/ndx_10y_1m_20261116/src/rules.py`, Dukascopy NDX 1m 2018-01 → 2026-11)

| kural | tanım | ölçü |
|---|---|---|
| C3b | RSI2(günlük 15:30) < 10 → 15:30'da AL, yükselen ilk 15:30'da çık (≤ 5 gün) | net bp |
| ORB × VIX | 09:30 ilk 15 dk aralığı, dünkü VIX ≥ 18,4, 5m kapanış aralık tepesi üstü → AL, stop aralık ortası, TP 3R | R |
| KSG | son nakit saati aşağı → 16:00 AL, ertesi 09:30 çık | net bp |
| CAPREV | stres ∧ VIX ≥ 18,4, önceki RTH dibi altı ilk 1h kapanış → AL | R |

## Fitil etiketi

İşlemin girişinden önceki W saat içinde kapanmış bir 1h mum varsa işlem "fitilli" sayılır. Mumun koşulu: alt fitil ≥ fiyatın %0,50'si
ve üst fitil ≤ alt/2 (kullanıcı kuralı). W ∈ {6 sa, 24 sa}. Mumun kapanışı girişten önce ya da girişle aynı anda olmalı.

**Hücre:** 4 kural × 2 W = 8.

## Dönemler

ESKİ 2018-01 → 2021-10, YENİ 2021-11 → 2026-11 (`lib.era`). Seçim yok: 8 hücrenin hepsi raporlanır.

## Geçme ölçütü (hücre başına, hepsi)

1. Fitilli alt küme ortalaması iki dönemde de > 0.
2. Fitilli − fitilsiz farkı iki dönemde de > 0.
3. Fark için gün-küme bootstrap P ≥ 1 − 0,10/8 = %98,75 (tüm dönem).
4. Fitilli n ≥ 30.

Geçen hücre "fitil-filtreli kanıtlı kural" olur (B−, SHADOW). Kart ve canlı kararı kullanıcıdadır.
Geçen yoksa: fitil kanıtlı kurallara katkı yapmıyor (X). Aile kapanır.

## Sonuç (ana tablo) ve EK-1 — KSG × fitil doğrulaması (doğrulama sonuçlarından önce yazıldı)

**Ana tablo:**
- KSG × fitil (W 6 sa): fitilli n 183, +28,6 bp vs fitilsiz +1,9 bp. ESKİ +22,9 vs +3,4, YENİ +33,1 vs +0,6. P 0,996 → **geçti**.
- W 24 sa da geçti (P 0,989).
- Diğer 6 hücre geçmedi: C3b P 0,60/0,93; ORB × VIX fitilliyle daha kötü; CAPREV n 15/41.

"Kâr kapısı" (B) demek için ek ölçütler (hepsi, KSG × fitil W 6 sa):

| # | ölçüt | geçme koşulu |
|---|---|---|
| (a) | **bağımsız besleme:** MT5 NAS100 M30 2018-05 → 2026-11, aynı kural (O15 / O16 30m açılışları, 1h fitil mumları 30m çiftlerinden) | fitilli ort > 0 ve fitilsizden büyük, P ≥ %90 |
| (b) | **bağımsız piyasalar:** MT5 US500 (2021-01 →, E143), US30, US2000 M30 | fitilli − fitilsiz > 0 en az 2/3'te; havuz P ≥ %90 |
| (c) | **oynaklık plasebosu (Dukascopy):** fitil koşulu yerine "son 6 sa içinde aralığı ≥ fitil mumlarının medyan aralığı olan, alt fitili < %0,20 bir 1h mum" etiketi | fitilli ort > oynaklık-etiketli ort, P ≥ %90 |
| (d) | **2. KURAL kartı** (Dukascopy) | 6/6. İcra: 16:00 açılışı yerine 16:01 açılışı |

Hepsi geçerse **B** ("fitilli KSG"): kart SHADOW, canlı kararı kullanıcıda. (a) + (c) geçip (b) düşerse C+. Aksi hâlde C.

## EK-2 (2026-11-18, sonuçlardan önce) — fitilli KSG'nin dokunulmamış veride sınaması

Kural aynen: 15:00 → 16:00 aşağı ∧ son 6 sa içinde kapanmış 1h mumda alt fitil ≥ %0,50 ve üst ≤ alt/2 → 16:00 AL, ertesi 09:30 çık.
1h fitil mumları 30m / 5m çiftlerinden kurulur.

Veriler:
- **Dukascopy NDX M30 dışa aktarımı 2016-03 → 2017-12.** Bu dönem hiç kullanılmadı. Not: NK-01'de KSG'nin kendisi 2016–18'de geçmemişti.
- **EET30** (başka MT broker'ı, 30m, 2016-11 → 2025-10, haftalık kalibre).
- **NQ vadeli 5m** (2019-08 → 2024-08).

Spread sabit: NDX 1,5 puan, NQ 0,25.

**Geçme:** üç verinin her birinde fitilli ort > 0 ve fitilli > fitilsiz; havuz (gün-küme) fark P ≥ %90.
- Geçerse C+ → **B**.
- 2016–17 tek başına eksiyse C+ kalır ("2020 sonrası çağ" notu).
