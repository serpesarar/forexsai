# Ön kayıt — Gün içi korku, zaman ekseni: sabah / öğle / öğleden sonra korkusu → aynı gün / ertesi gün (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Gerekçe

§2.68–2.71: kapanışa doğru korku (fitil, TWAP altı, son saat satışı) → ertesi gün 16:00 toparlanma (B). Kullanıcı: "başka yapı ara".
**Yeni eksen:** aynı korku ölçüleri günün daha erken saatlerinde. Kenar korkunun kendisinde mi, yoksa kapanış saatinde mi?

## 1. Izgara (NDX, Dukascopy 1m)

- Karar / giriş T ∈ {10:30, 12:00, 14:00} (o dakikanın açılışı + spread).
- Korku ölçüsü (09:30 → T barlarından):
  - K1: TWAP altı ≥ {%0,5, %1,0}.
  - K2: gün içi konum ≤ {0,20, 0,10} ∧ aralık ≥ %1,5.
  - K7: 09:30 açılışından düşüş ≥ {%0,75, %1,5}.
- Çıkış ∈ {aynı gün 15:30, ertesi gün 16:00}.
- 3 × 6 × 2 = **36 hücre**. Taban: aynı T / çıkış, tetiklenmeyen günler.

## 2. Seçim / doğrulama (§2.71 ile aynı yöntem)

**Seçim:**
- ESKİ 2018-01 → 2021-10'da aday: n ≥ 25, tetikli > 0, fark > 0, P ≥ %90.
- Izgara plasebosu: gün kaydırma, 20 kopya.
- Dondurma: en iyi 4 hücre.

**Doğrulama (hepsi) → B:**
1. YENİ tetikli > 0 ve fark P ≥ 1 − 0,10/4 = %97,5.
2. MT5 NAS100 M30, EET30, NQ'nun her birinde tetikli > 0 ve > taban.
3. Spread × 1,5 > 0.
4. n ≥ 150.

**Artımsallık (rapor):** §2.71 K1 akşam kuralıyla aynı günlerin oranı. Ertesi gün çıkışlı hücrelerde akşam kuralının olmadığı günlerdeki
sonuç da raporlanır.

## 3. Taşıma (seçimsiz, bilgi)

§2.71 K1 (16:00 TWAP altı ≥ %0,5 ∧ 15:00 → 16:00 aşağı → 16:00 AL, ertesi 16:00) değiştirilmeden MT5 M30 üzerinde:
- US30, US2000 (2018 →),
- US500 (2021 →, E143),
- XAUUSD (16:00 NY; altın için "kapanış" anlamsız olabilir, yine de mekanizma testi).

Ölçü: tetikli vs taban.
