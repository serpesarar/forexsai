# Gün sonu korku göstergeleri → gece / ertesi gün toparlanması (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/korku.py`, `src/kart.py`. Kartlar
`backend/data/evolution/go_live_cards/ndx_korku_twap.json`, `ndx_korku_sonsaat.json` (SHADOW).

## Sonuç

Fitilli KSG'nin mekanizmasını (gün içi korku + kapanışa doğru düşüş → toparlanma) fitil dışındaki altı korku ölçüsüyle aradım:
96 hücre, seçim 2018–21. Izgara şans üstü: 31 aday, plasebo %95 = 21.

**İki yeni B kuralı, fitilden bağımsız.** Fitilli geceler çıkarıldığında da çalışıyorlar; fitilli kuralla örtüşme yalnız %30:

| kural | YENİ 2021–26 (kör) | fitilsiz gecelerde | MT5 / EET30 / NQ | kart (2018–26) |
|---|---|---|---|---|
| **K1 — ortalamanın altında kapanış:** 16:00 fiyatı 09:30'dan beri günün ortalama fiyatının ≥ %0,5 altında ∧ son saat düşüş → **16:00 AL, ertesi gün 16:00 çık** | **+44,1** vs −1,3 bp (n 147, P %99,7) | +42,8 vs −7,3 | +48,5 / +51,6 / +44,4 | n 250, **+53,2 bp**, 6/6, 9/9 yıl |
| **K3 — son saat satışı:** 15:00 → 16:00 ≤ −%0,3 → **16:00 AL, ertesi gün 16:00 çık** | **+27,2** vs −2,1 (n 182, P %98,3) | +25,9 vs −1,4 | +33,5 / +36,4 / +41,9 | n 317, **+36,0 bp**, 6/6, 9/9 yıl |

**Risk** (ikisi de stopsuz ~24 sa):

| | K1 | K3 |
|---|---|---|
| σ | 200 bp | 189 bp |
| en kötü işlem | −612 bp | −612 bp |
| en kötü %5 | −199 bp | −244 bp |
| birikimli en büyük düşüş | −841 bp | −1.260 bp |
| medyan | +44 bp | +29 bp |
| isabet | %60 | %59 |

**Yıllar:**
- K1: 2018 +32 · 2019 +22 · 2020 +112 · 2021 +28 · 2022 +46 · 2023 +10 · 2024 +50 · 2025 +64 · 2026 +86.
- K3: 2018 +19 · 2019 +24 · 2020 +80 · 2021 +18 · 2022 +12 · 2023 +22 · 2024 +16 · 2025 +55 · 2026 +60.

K1 ve K3 aynı ailenin iki ölçüsü (K1'in 250 gecesinin 178'i K3'te de var). K1 daha seçici ve daha güçlü.

## Yeni "korku gecesi" ailesinin haritası

- Bütün güçlü hücreler **16:00 → ertesi gün 16:00**. 09:30 çıkışı daha zayıf: toparlanmanın büyük kısmı ertesi gün seansında.
- Güçlü ölçüler:
  - K1: ortalamanın altında kapanış.
  - K4: gün içi aralık ≥ %2 ∧ açılışın altında. YENİ P 0,971, beslemelerde +54…+57.
  - K3: son saat satışı.
  - K2: günün dibine yakın kapanış.
- Bunlar aynı olayın, yani **kapanışa doğru korku**nun ölçüleri.
- Zayıf ölçüler: aşağı açılış + erime (K5) ve üst üste düşüş günleri (K6).
- **Fitilli KSG ile ilişki:** fitil bu ailenin bir alt kümesi. Fitil ve korku ölçüleri birlikte görüldüğünde etki en güçlü; ama korku
  ölçüleri fitilsiz gecelerde de çalışıyor.

## Ayna (bilgi, seçimsiz tek hücre)

Coşku aynası (2h büyük **üst** fitil ∧ 15:00 → 15:30 yukarı → SAT, ertesi 16:00): **+11,8 bp** (n 127), taban SAT −4,6.
Defterin "coşku dönmez" beklentisinin tersi; doğrulama yapılmadı, yalnız iz (sonraki adım adayı).

## Önemli not — portföy

Fitilli KSG (geniş), K1 ve K3 aynı gecelerde sık sık birlikte tetikleniyor. Hepsini ayrı lotla açmak **aynı riski üç kez almak**
demek. Canlıda tek bir "korku gecesi" pozisyonu, en güçlü tetikle (K1 veya fitil) ve küçük lotla açılmalı. Bu ayrıca ölçülmeli.
