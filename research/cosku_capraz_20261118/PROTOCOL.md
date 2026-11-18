# Ön kayıt — Coşku gecesi (SAT) ve çapraz piyasa korkusu → NDX (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Gerekçe

§2.68–2.72: kapanışa doğru korku → ertesi gün toparlanma (B / B+). Kullanıcı: "başka yapı ara". İki yeni bakış açısı:

**A. Coşku gecesi (SAT).** KG-05 iz verdi: 2h büyük üst fitil ∧ son yarım saat yukarı → SAT +11,8 bp (n 127). Defter §3-2 "coşku
dönmez" diyor. Bu iz gerçek mi?

**B. Çapraz piyasa korkusu.** Russell (küçük şirket) ya da DAX'taki gün sonu korkusu, NDX'in kendi korku sinyali olmadığı gecelerde
NDX'in ertesi günü hakkında bilgi taşıyor mu?

## 1. A — Coşku gecesi (SAT, NDX Dukascopy 1m)

Tetikler (girişe kadarki barlardan; ayna tanımlar):
- C1: giriş fiyatı TWAP'ın ≥ {%0,5, %1,0} üstünde ∧ 15:00 → giriş yukarı.
- C2: gün içi konum ≥ {0,80, 0,90} ∧ aralık ≥ %1,5.
- C3: son saat (giriş − 60 dk → giriş) ≥ {+%0,3, +%0,6}.
- C4: son {6, 12} sa içinde kapanmış 2h mumda üst fitil ≥ %0,50 ∧ alt ≤ üst/2 ∧ 15:00 → giriş yukarı.

Giriş: 16:00 (C4'te 15:30) bid. Çıkış: ertesi gün {09:30, 16:00} ask.

8 tetik × 2 çıkış = **16 hücre**. Taban: aynı giriş/çıkış, tetiklenmeyen geceler (SAT).

## 2. B — Çapraz piyasa korkusu → NDX AL

- **X1 Russell:** MT5 US2000 M30. 16:00'da TWAP'ın ≥ %0,5 altı ∧ 15:00 → 16:00 aşağı.
  NDX 16:00 AL, ertesi gün {09:30, 16:00}. **Yalnız NDX'in kendi K1'i olmayan geceler.**
- **X2 DAX:** Dukascopy DAX 1m. Berlin 17:30 (= NY 11:30 ya da 12:30, DST'ye göre) DAX fiyatı 09:00 Berlin'den beri TWAP'ın ≥ %0,5
  altı ∧ 16:30 → 17:30 Berlin aşağı. NDX DAX kapanış dakikasında AL, çıkış {aynı gün 16:00, ertesi gün 16:00}.

X1 × 2 + X2 × 2 = **4 hücre**. Taban: aynı kümede tetiklenmeyen geceler / günler.

## 3. Seçim ve doğrulama

**Seçim:**
- Toplam 20 hücre. ESKİ 2018-01 → 2021-10'da aday: n ≥ 25, tetikli > 0, fark > 0, P ≥ %90.
- Izgara plasebosu: tetik kaydırma, 20 kopya.
- Dondurma: en iyi 4 hücre.

**Doğrulama (hepsi) → B:**
1. YENİ tetikli > 0 ve fark P ≥ 1 − 0,10/4 = %97,5.
2. MT5 NAS100, EET30, NQ'nun her birinde tetikli > 0 ve > taban. X1 / X2'de tetik günleri kaynak piyasadan, işlem fiyatları
   beslemeden.
3. Spread × 1,5 > 0.
4. n ≥ 150.
