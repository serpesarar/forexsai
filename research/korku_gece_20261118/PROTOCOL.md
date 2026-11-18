# Ön kayıt — Gün sonu korku göstergeleri → gece / ertesi gün toparlanması (fitilden bağımsız yapı arama) (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Gerekçe

§2.68–2.70'te fitilli KSG ve geniş hâli B çıktı. Mekanizma hipotezi: **gün içi korkunun emilmesi + kapanışa doğru yeniden düşüş →
gece sürüklenmesi**.

Kullanıcı: "başka yapı ara". Aynı mekanizmayı fitil dışındaki korku ölçüleriyle sınıyorum. Yeni yapı, **fitilli geceler
çıkarıldığında da** çalışmalı; yoksa yeni değil, aynı yapının başka bir ölçüsüdür.

## 1. Veri ve dönemler

- Seçim ESKİ 2018-01 → 2021-10, kör doğrulama YENİ 2021-11 → 2026-11 (Dukascopy NDX 1m).
- Bağımsız beslemeler: MT5 NAS100 M30, EET30 30m, NQ 5m. Göstergelerin hepsi 30m barlarla hesaplanabilir.
- Gecelik finansman; spread modeli ya da sabit (§2.70 ile aynı).

## 2. Korku göstergeleri (karar anı = giriş; yalnız o ana kadarki barlar)

| kod | gösterge | eşikler |
|---|---|---|
| K1 | giriş fiyatı, 09:30'dan beri TWAP'ın altında (%) | ≤ −%0,5 · ≤ −%1,0 |
| K2 | gün içi konum (P − dip)/(tepe − dip) (09:30'dan beri), aralık ≥ %1,5 | ≤ 0,20 · ≤ 0,10 |
| K3 | son saat satışı: giriş − 60 dk → giriş getirisi | ≤ −%0,3 · ≤ −%0,6 |
| K4 | gün içi derinlik: (tepe − dip)/açılış ≥ X ∧ P < 09:30 açılışı | X %2 · %3 |
| K5 | aşağı boşluk + erime: 09:30 açılışı / dünkü 16:00 − 1 ≤ −g ∧ P < 09:30 açılışı | g %0,5 · %1,0 |
| K6 | üst üste düşüş: son 3 gün (16:00 → 16:00) aşağı ∧ bugün de (dünkü 16:00 → giriş) aşağı | — · (son 2 gün) |

Izgara: 6 × 2 eşik × giriş {15:30, 16:00} × çıkış {ertesi 09:30, ertesi 16:00} × KSG koşulu {var (15:00 → giriş aşağı), yok} =
**96 hücre**.

Taban: aynı giriş/çıkış/KSG ile göstergesi tetiklenmeyen geceler.

## 3. Seçim (ESKİ)

Aday hücre:
- n ≥ 25,
- tetikli ort > 0,
- tetikli − taban > 0, P ≥ %90.

Izgara plasebosu: tetik günleri ±1–10 işlem günü kaydırılır, 20 kopya.

Dondurma: fark t'sine göre en iyi 5 hücre; aynı göstergeden en fazla 2.

## 4. Doğrulama (hepsi) → "yeni yapı" B

1. YENİ tetikli > 0 ve fark P ≥ %98.
2. MT5, EET30, NQ'nun her birinde tetikli > 0 ve > taban.
3. **Fitilden bağımsızlık:** §2.70 geniş fitil etiketi (2h, %0,50, 12 sa) taşıyan geceler çıkarılınca Dukascopy tüm dönemde tetikli > 0
   ve > taban, P ≥ %90.
4. Spread × 1,5 > 0.
5. n ≥ 150.

**Hüküm:**
- Hepsi → B (yeni yapı).
- 1–2 geçip 3 düşerse "fitilin başka ölçüsü" (C, yeni değil).
- Aksi hâlde X.

## 5. Ayna kontrolü (tek hücre, seçimsiz)

Coşku aynası: son 6 sa içinde 2h büyük **üst** fitil (≥ %0,50, alt ≤ üst/2) ∧ 15:00 → 15:30 yukarı → 15:30 SAT, ertesi 16:00.
Defter §3-2 "coşku dönmez" der; beklenti X. Sonuç bilgi için raporlanır.
