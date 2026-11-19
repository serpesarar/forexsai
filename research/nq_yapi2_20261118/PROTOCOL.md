# NB-01…04 — NASDAQ'ta yeni yapılar: gece/gün içi çekişmesi, yoğunlaşma, kredi uyumsuzluğu, 0DTE strike çekimi

Ön kayıt: 2026-11-18, sonuçlara bakılmadan yazıldı. Yalnız NASDAQ hedef (QQQ / Dukascopy NDX 1m / MT5 NAS100).

## Defter kontrolü
- Gece/gün içi çekişmesi (Lou–Polk–Skouras, Akbas vd. "tug of war") endeks düzeyinde yok; KSG/NK-06 yalnız gece tutuşu ve günün saati.
- Yoğunlaşma (QQQ − eşit ağırlık QQQE, SPY − RSP) tek başına yok; NK-01 QQEW'i yalnız düşüş günü kapısı olarak kullandı.
- Kredi: DB-05 HYG'yi C3b kapısı olarak sınadı (C); tek başına hisse–kredi uyumsuzluğu yok.
- Strike çekimi / 0DTE: yok. YL-01 yuvarlak NDX seviyeleri (fiyat yarışı) farklı tanım.

## Ortak
Günlük: QQQ temettü düzeltmeli (açılış × AdjClose/Close). Getiri kapanış → h gün sonra kapanış, maliyet 2 bp + uzunda
`FIN_BP_PER_DAY` × takvim günü. Fark = tetik − tüm günler (yönlü), blok bootstrap (blok = h). Yüzdelikler nedensel, son 504 gün
(min 252). KEŞİF verinin başı → 2021-10-31, TEST 2021-11-01 → 2026-11.
Hüküm: TEST'te KEŞİF yönünde fark > 0 ve P ≥ 1 − 0,10/(hücre sayısı) ve bağımsız eşte aynı yön → B; aynı yön P ≥ 0,90 → C+;
aksi X.

## NB-01 — Gece / gün içi çekişmesi (QQQ 1999+, bağımsız SPY 1993+)
ON = ln(açılış_t / kapanış_{t−1}), ID = ln(kapanış_t / açılış_t). Çekişme = Σ20 ON − Σ20 ID. Hücreler: çekişme yüzdelik ≥ 0,80
ve ≤ 0,20 × h ∈ {5, 20} (4 hücre). Yön KEŞİF'te farkın işaretiyle seçilir (yön ön kayıtsız). Ek bilgi: sonraki 20 günün gece
ve gün içi bileşenleri ayrı.

## NB-02 — Yoğunlaşma (QQQ/QQQE 2012+, uzun vekil SPY/RSP 2003+)
rel20 = ln(QQQ/QQQE) 20 günlük değişim (dar liderlik yüksek). Hücreler: rel20 yüzdelik ≥ 0,80 / ≤ 0,20 × h ∈ {5, 20}, hedef QQQ
(SPY/RSP çiftinde hedef SPY). Yön KEŞİF'te seçilir; B için iki çift aynı yön.

## NB-03 — Hisse–kredi uyumsuzluğu (HYG/IEF 2007+, hedef QQQ)
kr20 = ln(HYG/IEF) 20 g değişim, yüzdelik. D1: QQQ r20 > 0 ∧ kr20 yüzdelik ≤ 0,20 (kredi bozulurken hisse yükseliyor) → SAT.
D2: QQQ r20 < 0 ∧ kr20 yüzdelik ≥ 0,80 (kredi güçlü, hisse zayıf) → AL. h ∈ {5, 20}. Yön ön kayıtlı. Bağımsız eş: hedef SPY.

## NB-04 — QQQ strike çekimi, 0DTE çağı (Duka NDX 1m; MT5 NAS100 2m)
QQQ vekili q = NDX × k, k = QQQ kapanışı(d−1) / NDX 16:00(d−1) (nedensel). Strike ızgarası $1; plasebo ızgara $0,5 kaydırılmış.
15:00'te en yakın strike K, uzaklık u = |q − K| ($). Tetik 0,20 ≤ u ≤ 0,45 → K yönünde işlem, çıkış K'ya dokunuş (TP) ya da
16:00 (zaman). Net bp gerçek spread. Ölçü: gerçek ızgara − plasebo ızgara (aynı günler, aynı kural).
Çağlar: ESKİ 2018-04 → 2022-10 (günlük QQQ vadesi yok), 0DTE 2022-11 → 2026-11. Gün tipi: Cuma (iki çağda da vade) / Cuma dışı.
Hipotez: Cuma dışı günlerde çekim yalnız 0DTE çağında. Geçme: 0DTE Cuma dışı gerçek − plasebo > 0, P ≥ 0,95, MT5 aynı yön,
ESKİ Cuma dışı farkı daha küçük. Vekil hatası farkı yalnız seyreltir (plasebo aynı hatayı taşır).
