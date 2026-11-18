# Ön kayıt — Opsiyon piyasası korkusu (VIX vade eğrisi, VIX sıçraması) → NDX 1 / 2 / 5 gün (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Gerekçe ve defter

Kullanıcı: "başka yapı ara". Fiyat temelli korku ölçüleri (§2.68–2.72) yerine **opsiyon piyasasının korkusu**:
- VIX9D / VIX (çok kısa vadeli panik),
- VIX / VIX3M (eğri ters),
- VIX bir günlük sıçraması.

Defter:
- GF-05: VIX3M gün düzeyi koşul; VIXREG ~0,01R.
- DB-01: C3b × ters eğri, n 14.
- VIX9D oranı ve sıçrama + çok günlük tutuş denenmedi.

## 1. Tasarım (NDX Dukascopy 1m; sinyal VIX'in d−1 kapanışından, d 09:30'da bilinir)

Sinyaller (d−1 kapanış verisi; S3 için d−2 → d−1):
- S1: VIX9D / VIX ≥ {1,00, 1,10}.
- S2: VIX / VIX3M ≥ {1,00, 1,05}.
- S3: VIX bir günlük değişim ≥ {+%15, +%25}.

İşlem: d 09:30 açılışında AL (+spread). Çıkış {d 16:00, d+1 16:00, d+4 16:00} açılışında. Gecelik finansman.

6 × 3 = **18 hücre**. Taban: aynı giriş/çıkış, sinyalsiz günler.

## 2. Seçim / doğrulama

**Seçim:**
- ESKİ 2018-01 → 2021-10'da aday: n ≥ 25, sinyalli > 0, fark > 0, P ≥ %90.
- Izgara plasebosu: sinyal günleri ±1–10 iş günü kaydırma, 20 kopya.
- Dondurma: en iyi 4.

**Doğrulama (hepsi) → B:**
1. YENİ sinyalli > 0 ve fark P ≥ %97,5.
2. MT5 NAS100, EET30, NQ'nun her birinde sinyalli > 0 ve > taban.
3. Spread × 1,5 > 0.
4. n ≥ 150. n 100–150 ise ölçütler geçse de C+.

**Artımsallık (rapor):** sinyal günlerinin bir önceki akşam K1 korku gecesi (§2.71) ya da C3b (RSI2 < 10) ile örtüşme oranı.
Bu günler çıkarıldığında sonuç.
