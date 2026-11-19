# VK-01…05 + KM-01 — Varyans primini genişlet + kanıtlı NASDAQ kuralları × yeni boyutlar

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Kullanıcı isteği: farklı bakış açıları, kombinasyonlar, doğru bulunan yolları genişletmek.

## Defter kontrolü
VP1 (§2.85 NA-02) C+: VRP = VXN − 100·RV20 yüzdelik ≥ 0,80 → 20 g AL, KEŞİF +121 bp / TEST +95 bp P 0,90.
Kesişimler daha önce: KS-01 (C3b × S/R/hacim/EMA/mum/stres), DB-03 (VVIX/SKEW/VXN−VIX × C3b), KB (korku içi kesişimler).
Burada yeni boyutlar: varyans primi (NA-02), gece/gün içi çekişmesi (NB-01), yoğunlaşma (NB-02), kredi (NB-03).

## Ortak
Günlük veri, temettü düzeltmeli (QQQ, SPY), maliyet işlem başı 2 bp + uzunda takvim günü × `FIN_BP_PER_DAY`. Yüzdelikler
nedensel 504 g (min 252). KEŞİF → 2021-10-31, TEST 2021-11-01 → 2026-11.

## VK — VP1 genişletme (kural değişmez: yüzdelik ≥ 0,80 → 20 g AL)
- **VK-01 bağımsız dönem:** ^NDX 1990–2000, VXN yokken VIX − 100·RV20(NDX). Geçme: fark > 0, P ≥ 0,90.
- **VK-02 bağımsız varlık:** SPY 1993+, VIX − 100·RV20(SPY); KEŞİF ve TEST ayrı. Geçme: ikisi de fark > 0, TEST P ≥ 0,90.
- **VK-03 örtüşmesiz epizot:** giriş = yüzdelik ≥ 0,80'e geçiş günü (önceki 5 gün < 0,80), 20 g tut, tutuşta yeni giriş yok.
  Epizot sayısı, ortalama, isabet, en kötü; taban = aynı sayıda rastgele başlangıç (aynı yıl) 2.000 kez. Geçme: KEŞİF ve TEST
  ikisinde de gerçek > plasebo %90'ı.
- **VK-04 ufuk haritası:** h ∈ {1, 5, 10, 20, 40, 60} (bilgi; seçim yok).
- **VK-05 zamanlama portföyü:** VP1 sonrası 20 g uzun, aksi nakit; B&H ile yıllık getiri, Sharpe, maxDD (TEST ve tüm dönem).
  Bilgi: maruz kalma oranı.

## KM-01 — kanıtlı kurallar × yeni boyutlar (QQQ 2001+ ana, SPY eş)
Kurallar (günlük vekiller, defterde doğrulanmış):
- **R_C3b:** RSI2(kapanış) < 10 → kapanışta AL, ilk yükselen kapanışta çık (≤ 5 g), tek pozisyon.
- **R_K1:** V1 vekili K ≤ (Y+D)/2 × 0,995 ∧ K < A → kapanış → ertesi kapanış.
- **R_ES:** K1 günü → ertesi gün açılış → kapanış (YK-08 vekili).
Boyutlar (tetik günü D'de, nedensel):
- B1 VP1 (VRP yüzdelik ≥ 0,80) — **yön ön kayıtlı: artı** (prim = korku telafisi)
- B2 VRP yüzdelik ≤ 0,20 — yön ön kayıtlı: eksi
- B3 çekişme üst %20 (NB-01) · B4 dar liderlik QQQ/QQQE üst %20 (2012+) · B5 kredi zayıf HYG/IEF alt %20 · B6 VIX ≥ 18,4 (referans)
  — B3–B6 yönü KEŞİF'te seçilir.
Ölçü: R ∧ B − R ∧ ¬B (net bp), gün-blok bootstrap. Hücre 3 × 6 = 18. Geçme (B adayı): KEŞİF yönünde TEST fark > 0, P ≥ 1 − 0,10/18,
SPY'de aynı yön. Aynı yön ve TEST P ≥ 0,90 → C+.

## EK-1 (2026-11-18, ilk sonuçlardan sonra)
Gözlem: VK-01 (1990–2000) ve VK-03 (örtüşmesiz epizot) VP1'i desteklemedi → VP1 tek başına kural değil (E102 örtüşme şişmesi).
KM-01'de dört hücre aynı yönde: C3b × VP1, K1 × çekişme, ES × kredi zayıf, ve VRP düşük vetosu (C3b/K1/ES). Ek sınamalar:
(a) **kopya:** C3b × VP1 farkı VIX ≥ 18,4 içinde ve dışında ayrı (ikisi de > 0 olmalı);
(b) **bağımsız dönem:** ^NDX 1990–2000 (VIX tabanlı VRP) ve SPY 1993–2000 için C3b/K1 × VP1, × VRP düşük; SPY 1993–2000 için
    K1 × çekişme (kredi verisi 2007 öncesi yok → ES × kredi bağımsız dönemsiz kalır, en fazla C+);
(c) **veto birleşik:** VRP düşük ∧ (C3b ∨ K1) tüm dönem QQQ+SPY birleşik fark.
Geçme: (a) iki alt kümede de artı; (b) yön tutuyor (fark işareti doğru) → hücre C+'dan B'ye yükselebilir, karşı yön → X.
^NDX'te açılış verisi güvenilmez olduğundan ES ve çekişme yalnız SPY'de.

## EK-2 (2026-11-18, EK-1 sonrası) — K1 × çekişme kopya kontrolü
K1 × çekişme (üst %20) dört kesitte artı. Kopya adayları: VIX ≥ 18,4 ve art arda korku (D−1 de K1, GN-05). Fark VIX üstü/altı ve
art arda/tekil alt kümelerinde ayrı ölçülür (QQQ 2001+ ve SPY 1993+). Geçme: dört alt kümenin en az üçünde artı, iki varlıkta da.
Ayrıca çekişme bileşenleri: yalnız Σ20 gece üst %20 ve yalnız −Σ20 gün içi üst %20 ayrı (hangisi taşıyor).

## EK-3 (2026-11-18) — ayı rejimi kopyası mı?
EK-2'de taşıyıcı gün içi satış bileşeni. K1 ayı çağlarında güçlü (UD). Kontrol: K1 × çekişme farkı son 20 g getiri < 0 ve ≥ 0
alt kümelerinde ve fiyat SMA200 altı/üstü alt kümelerinde ayrı (QQQ, SPY). Geçme: dört alt kümenin en az üçünde artı, iki varlıkta.

## EK-4 (2026-11-18) — gerçek gün içi K1 gecelerinde (16:00 → ertesi 16:00)
K1 tanımı canlıdaki gibi (`korku_genislik/gn.py::nts`: 16:00 ≤ TWAP −%0,5 ∧ son saat aşağı). Çekişme QQQ (NAS100, Duka NDX)
ve SPY (MT5 US500) günlüğünden; **birincil: D−1'e kadar** (shift 1, tam nedensel), ikincil D dahil. Dönem ESKİ 2018-04 → 2021-10,
YENİ 2021-11 →. Geçme: birincilde üç beslemede YENİ fark > 0 ve havuz P ≥ 0,90.
