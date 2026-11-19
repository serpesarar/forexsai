# PC / BT / VD — opsiyon duyarlılığı, mega-cap genişlik itkisi, fiyat–VIX ayrışması

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Defter: put/call, genişlik itkisi (Zweig tipi), aynı gün fiyat ↑ ∧ VIX ↑ yok
(AAII anketi indirilemedi — erişim kapalı). Epizot + aynı yıl rastgele başlangıç plasebosu (§3-43); giriş tetik günü kapanışı.
Hedef QQQ (temettü düzeltmeli), eş SPY; maliyet 2 bp + uzunda `FIN_BP_PER_DAY`. Hüküm: KEŞİF'te seçilen yön TEST'te
yüzdelik ≥ 0,95 ve eş aynı yön → B; ≥ 0,90 → C+; aksi X. Yön ön kayıtsızsa KEŞİF'te seçilir.

## PC-01 — CBOE hisse opsiyonu put/call (2006-11 → 2019-10, yalnız bu aralık yayımlı)
P/C5 = 5 g ortalama, yüzdelik (252 g, min 126). Üst %20'ye geçiş → AL (korku, karşıt; yön ön kayıtlı), alt %20 → SAT
(rehavet; yön ön kayıtlı). h ∈ {5, 20}. Dönem: KEŞİF 2006-11 → 2012-12, TEST 2013-01 → 2019-10 (son 5 yıl verisi yok).

## BT-01 — mega-cap genişlik itkisi (12 hisse, §2.88 listesi, 1999+)
g = 10 g SMA üstündeki hisse oranı. BT1 itki: g son 10 günde ≤ 0,25 iken bugün ≥ 0,75 → AL h ∈ {5, 20} (yön ön kayıtlı).
BT2 tükenme: g ≤ 1/12 → AL h ∈ {5, 20} (yön ön kayıtlı, korku dönüşü). KEŞİF → 2021-10, TEST 2021-11 →.

## VD-01 — aynı gün fiyat–VIX ayrışması (VIX 1990+)
VD1: QQQ günü ≥ +%0,75 ∧ VIX günü ≥ +%3 (yükselişte koruma talebi). VD2: QQQ günü ≤ −%0,75 ∧ VIX günü ≤ 0 (korkusuz düşüş).
h ∈ {1, 5}; yön KEŞİF'te seçilir (4 hücre). Bağımsız dönem: ^NDX 1990-01 → 1999-02 (QQQ öncesi) aynı kurallar.

## EK-1 (2026-11-18, ilk sonuçlardan sonra) — BT2 tükenme kopya kontrolü
BT2 (≤ 1/12 hisse 10 g SMA üstünde → 5 g AL) QQQ KEŞİF yüzdelik 1,00 / TEST 0,91. Kopya adayları: C3b (QQQ RSI2 < 10), K1 korku günü,
VIX ≥ 18,4. Ölçüm: (a) BT2 epizotları RSI2 < 10 olan / olmayan; (b) BT2 ∧ RSI2 ≥ 10 tek başına epizot + plasebo; (c) C3b günleri içinde
BT2 olan − olmayan fark (5 g); (d) bağımsız dönem ^NDX 1995-06 → 1999-02 (hisse verisi 1995+). Geçme: (b) KEŞİF ve TEST yüzdelik ≥ 0,90
ve (c) fark > 0 → C3b'ye artımsal (C+ korunur / doz adayı); aksi → kopya, X.
