# Ön-kayıt — Aile "Çapraz varlık rejimi + çıkış mekaniği + hafta sonu" (BTC, 2026-10-21)

Bu dosya HİÇBİR sonuç hesaplanmadan önce yazıldı. Sonradan düzenlenmez; değişiklik gerekirse en alta
"Amendments" bölümüne gerekçesiyle eklenir.

## 0. Ortak çerçeve (görev protokolü, aynen)

- Veri: `research/btc_5y_20261021/data/` (Binance BTCUSDT spot 1m ve türevleri; `macro_daily.parquet`).
  1m ızgara: 2021-06-01 00:00 UTC'den başlayan yoğun dakika ızgarası; eksik dakika = işlem yok.
  Dışlanan aralık: 2023-03-24 11:28–14:00 UTC (giriş/çıkış/yol kontrolü yapılmaz).
- Makro yalnız `merge_asof(avail_utc ≤ karar anı)` ile (avail_utc = NY işlem günü + 22:30 UTC).
- Dönemler (karar zamanına göre): DISCOVERY 2021-06-01→2023-12-31 · OOS 2024-01-11→2025-06-30 ·
  BLIND 2025-07-01→2026-10-20. 2024-01-01→01-10 hiçbir dönemde yok. Parametre yalnız DISCOVERY'de seçilir.
- İcra: karar = bir barın kapanışı → giriş = sonraki 1m barın open'ı; BUY = open + s/2, SELL = open − s/2.
  Çıkışta tersi (BUY kapanışı = mid − s/2). TP/SL 1m barlarla, girişten sonra; aynı 1m barda TP ve SL → SL.
  Göstergeler yalnız tamamen kapanmış barlarla (bar bitişi ≤ karar anı).
- Maliyet: s = %0,0185 × fiyat (taban); stres s = %0,028 (kart ölçütü 4); varyant s = sabit 15 $.
- Swap: pozisyon broker rollover anını (sunucu 00:00 = New York 17:00 → UTC'de yazın 21:00, kışın 22:00)
  geçerse her geçişte long −0,14/365 × giriş fiyatı, short +0,02/365 × giriş fiyatı (hafta sonu dahil her gece).
- R = net PnL / başlangıç riski (|giriş − SL|).
- Kart (6): (1) ≥150 çözülmüş olay; (2) ortR > 0 ∧ gün-blok bootstrap P(EV>0) ≥ %90; (3) iki kronolojik yarı ≥ 0;
  (4) s ×1,5 (=%0,028) ile ortR > 0; (5) |iyimser − gerçek| ≤ 0,5·|gerçek| (iyimser = sinyal barı kapanışından giriş,
  spread 0, swap aynı); (6) tek-pozisyon ortR > 0. Genişletilmiş: plasebo yüzdeliği (≥200 çekiliş) ve BLIND işareti.
  Her zaman: kapısız taban (aynı pencerelerde hep-long ve rastgele yön) + başabaş WR.

### 0.1 Bu ailede ek icra kuralları (ön-kayıtlı)
- **Broker kapalı dakikaları** (02 notu): her gün rollover−1 dk ve rollover dakikası (UTC 20:59, 21:00 yaz / 21:59, 22:00 kış);
  Cuma ayrıca rollover−5…rollover−1. Bu dakikalarda giriş, çıkış ve TP/SL tetiklenmesi YOK; karar bu dakikaya düşerse
  giriş bir sonraki işlem dakikasına kayar. Kapalı aralıkta fiyat SL'i geçtiyse yeniden açılış barında SL dolumu =
  min(SL, open) (long) / max(SL, open) (short) — boşluk kaybı. TP dolumu her zaman TP'de (muhafazakâr).
  Hafta sonu düzensiz bakım boşlukları modellenmez (veri yok; notta belirtilir).
- Tetik bid/ask ile: long SL tetik = mid_low − s/2 ≤ SL; long TP = mid_high − s/2 ≥ TP; short SL = mid_high + s/2 ≥ SL;
  short TP = mid_low + s/2 ≤ TP. s girişteki fiyattan hesaplanır, işlem boyunca sabit.
- Zaman çıkışı fiyatı = çıkış dakikasının open'ı ∓ s/2 (o dakika kapalıysa sonraki işlem dakikası).
- Bootstrap: gün-blok (karar gününün UTC tarihi), 2.000 tekrar, seed 7. %95 GA = 2,5/97,5 yüzdelik.
- Tek-yönlü p (Holm için) = gün-kümeli t istatistiğinden (günlük ortalamaların t'si) normal yaklaşımla.

## 1. Hipotezler — çapraz varlık rejimi (yön kuralları)

Ortak pencere **"sunucu günü"**: karar = 22:30 UTC (her takvim günü; VIX/QQQ/DXY kapanışının en erken kesin bilindiği an),
giriş = 22:30 dakikasının open'ı (iyimser: 22:29 barının close'u, spread 0), çıkış = bir SONRAKİ rollover − 2 dk'nın open'ı
(yaz 20:58, kış 21:58 UTC). Pencere hiçbir rollover'ı geçmez → swap 0. Felaket SL = giriş × (1 ∓ k·dvol20);
dvol20 = karar anında tamamlanmış son 20 UTC gününün kapanıştan-kapanışa log getirisi std'si. R bu SL mesafesine göre.
Taban: aynı pencerelerde hep-long (k aynı) ve hep-short.

- **C01 — VIXREG günlük (NDX bulgusu aynen).** Son bilinen VIX kapanışı ≥ 18,4 → BUY, < 18,4 → SELL. Eşik DEĞİŞMEZ.
  Izgara: k ∈ {1, 2} (2 hücre). Kollar ayrıca raporlanır: yalnız-BUY kolu (VIX≥18,4 günleri long), yalnız-SELL kolu.
  Hafta içi karar günleri (Pzt–Cum UTC tarihi) ve hafta sonu karar günleri ayrı raporlanır; birincil = 7 gün.
- **C02 — VIXREG nötr giriş filtresi.** Her UTC saat başı (hh:00) karar; yön = VIX rejimi (C01 kuralı); SL = 1×ATR14(1h, son
  kapanmış 1h bar, Wilder); çıkış (a) 4 s zaman çıkışı, (b) 24 s zaman çıkışı (2 hücre). Swap uygulanır. Kıyas: aynı saatlerde
  rejim-karşıtı yön ve hep-long. Örtüşen olaylar → kart ölçüt 6 tek-pozisyon (as-traded: önceki pozisyon kapanmadan gelen
  olay atlanır) ile.
- **C03 — QQQ günü → BTC sunucu günü.** Yalnız yeni bir QQQ kapanışının geldiği günler (ABD işlem günü D, karar D 22:30).
  r = log(QQQ_close_D / QQQ_close_{D−1}) (ham close), σ20 = son 20 QQQ günlük getiri std'si (D dahil, bilinir).
  Izgara: eşik θ ∈ {0, 0,5, 1,0} (|r| > θ·σ20; θ=0 → r≠0) × mod ∈ {takip (r>0 → BUY), ters (r>0 → SELL)} = 6 hücre. k = 2.
- **C04 — QQQ açılış boşluğu → BTC gün-içi.** g = log(QQQ_open_D / QQQ_close_{D−1}). **Kullanılabilirlik:** QQQ açılışı
  ABD açılışında (09:30 ET) gerçekleşir; ön-kayıtlı bilinir anı **10:00 ET** (DST'ye göre 14:00/15:00 UTC) — bu sütun için
  avail = D 10:00 ET (amendment değil, baştan tanım; close'lar için 22:30 kuralı aynen). Karar 10:00 ET, giriş o dakikanın open'ı,
  çıkış aynı günün rollover−2 dk'sı (16:58 ET). Swap 0. SL = giriş × (1 ∓ 1·dvol20) (gün-içi pencere kısa → k=1).
  Izgara: θ ∈ {0, 0,5} (|g| > θ·σ20 of QQQ günlük getirisi) × mod ∈ {takip, ters} = 4 hücre.
- **C05 — Korelasyon koşullayıcı (C03 üzerinde).** ρ60 = BTC–QQQ günlük getiri korelasyonu, son 60 ABD işlem günü; BTC
  getirisi QQQ ile hizalı örneklenir: BTC fiyatı = her ABD işlem günü NY 16:00'daki 1m close (16:00 dakikasının open'ı).
  ρ60 D'nin 22:30'unda bilinir (D dahil). Kural: C03'ün DISCOVERY'de seçilen hücresi yalnız ρ60 > c iken; c ∈ {0,2, 0,4}
  (2 hücre). Tamamlayıcı (ρ60 ≤ c) ayrıca raporlanır.
- **C06 — DXY günlük değişimi.** d = log(DXY_D / DXY_{D−1}); a priori yön: DXY↑ → SELL BTC, DXY↓ → BUY. θ ∈ {0, 0,5}·σ20
  (2 hücre). Sunucu günü penceresi, k = 2. Ters mod yalnız bilgi (karar dışı).
- **C07 — US10Y günlük değişimi.** Δy = y_D − y_{D−1} (yüzde puanı); faiz↑ → SELL, faiz↓ → BUY; θ ∈ {0, 0,5}·σ20 (2 hücre).

**Seçim:** her hipotez için DISCOVERY'de ortR'si en yüksek hücre seçilir (C05 için C03 seçimi + c seçimi). Seçilen hücrenin
OOS, BLIND ve OOS∪BLIND sonuçları raporlanır; TÜM hücreler tüm dönemlerde tabloya yazılır.
**Kart** seçilen hücre için OOS∪BLIND üzerinde hesaplanır (ölçüt 1–6), ayrıca OOS ve BLIND ayrı.
**Plasebo:** yön etiketlerinin yıl-içi permütasyonu (aynı yıl içinde günler arası karıştırma; yıl başına BUY/SELL sayısı korunur),
500 çekiliş; gerçek ortR'nin plasebo dağılımındaki yüzdeliği (OOS∪BLIND). C02'de etiket gün düzeyinde karıştırılır.
**Seçim düzeltmesi:** (i) DISCOVERY ızgarasında max-z: her plasebo çekilişinde hücrelerin max t'si; gerçek max t'nin p_sel'i.
(ii) Holm: 7 hipotezin seçilen hücrelerinin OOS∪BLIND tek-yönlü p'leri üzerinde, α = 0,05.
**GEÇER (kenar):** kart 6/6 (OOS∪BLIND) ∧ plasebo ≥ %95 ∧ Holm ✓ ∧ BLIND ortR > 0 ∧ hep-long tabanını (aynı pencereler)
aşar (ortR − taban > 0). Aksi: SHADOW (kart ≤1 ölçüt düşer ve plasebo ≥ %90) / RED.
Ön beklenti: C01'de BTC'nin 2022 ayısında VIX yüksek olduğundan BUY kolu zarar edebilir; DXY/US10Y zayıf.

## 2. Çıkış mekaniği (kenar değil, yönetim kuralı karşılaştırması)

Girişler:
- **N-L / N-S (nötr):** her UTC saat başı hh:00 karar, long (N-L) ve short (N-S) ayrı.
- **M (bot-tarzı momentum BUY):** kapanmış 15m bar: Stoch %K(14, yavaşlatma 3) > 70 ∧ (close − EMA20)/ATR14(15m) > 0,8 ∧
  son kapanmış 1h barda Parabolic SAR (0,02/0,2) < 1h close; epizod: koşul bir önceki 15m barda yanlışken doğru olan ilk bar.
  Karar = 15m bar kapanışı.
Birim risk: SL = 1×ATR14(1h) (son kapanmış 1h bar). Tüm varyantlarda 24 s tavan (zaman çıkışı), swap uygulanır.

Varyantlar:
- X1 braket TP 1R / SL 1R · X2 braket TP 0,73R / SL 1R (bot 80/110) · X3 braket TP 2R / SL 1R
- X4 zaman 4 s (yalnız SL) · X5 zaman 24 s (yalnız SL)
- X6 = X3 + BE (MFE ≥ 0,5R görüldükten sonraki bardan itibaren SL = giriş) · X7 = X3 + BE @ MFE ≥ 1,0R
- X8 = koştur: X1 gibi başlar; TP1'e (1R) dokununca TP kalkar, SL = giriş + 0,4R (=TP − 0,6R), sonra iz = (önceki barlara kadar
  görülen tepe) − 0,6R; 24 s tavan
- X9 = BE30 + koştur: X8 + giriş+30 dk'da (30. dakikanın kapanışı) fiyat girişin lehindeyse SL = giriş (bot time30 modu)
- X10 = X2 + BE @ MFE ≥ 0,5R (botun şimdiki conditional_mfe modu, bot geometrisinde)

Ön-kayıtlı karşılaştırmalar (eşli, aynı olaylar; Δ = ortR(varyant) − ortR(referans)):
- K1 braket vs zaman: X5 − X1, X5 − X2, X4 − X1 (proje beklentisi: zaman ≥ braket, "braket ≠ zaman").
- K2 BE: X6 − X3, X7 − X3, X10 − X2 (proje beklentisi: Δ ≤ 0, BE REDDEDİLDİ).
- K3 koştur: X8 − X1, X9 − X1 (proje NDX: Δ > 0).
**Benimseme ölçütü (bir yönetim kuralı için):** DISCOVERY'de Δ > 0 ∧ gün-blok P(Δ>0) ≥ %90, OOS ve BLIND'da da Δ > 0, ve
OOS∪BLIND iki yarısında Δ ≥ 0. Reddetme: OOS∪BLIND'da Δ < 0 ∧ P(Δ<0) ≥ %90.
Raporlanan: her varyantın her girişte n, WR, ortR, başabaş WR, ort. tutma süresi, swap payı.

### 2.1 Swap ekonomisi
- Analitik: long gecelik swap = 0,14/365 = 3,84 bp/gece; short +0,55 bp/gece.
- Ampirik: N-L ve N-S girişlerinde salt zaman çıkışı H ∈ {1, 4, 8, 24, 48, 72, 120, 240} s için (SL'siz, nominal % getiri,
  spread dahil) ortalama net getiri, swap payı; dönem bazında. Soru: hangi H'de swap, dönem içi ortalama BTC sürüklenmesinin
  (ve bu ailede bulunan herhangi bir kenarın) önemli bir kesrini (≥ %50) yer?

## 3. Hafta sonu
- Spread: broker tick ölçümünden (02 notu; hafta sonu tw-ort 16,33 $ vs hafta içi 15,85 $; p99 47,5 vs 39,9 $) — yeni ölçüm yok.
- Boşluk riski: Binance verisinde broker kapalı pencereleri (günlük 2 dk; Cuma 6 dk) boyunca |hareket| dağılımı (% ve
  ATR14(1h) biriminde; p50/p90/p99/max); X1–X10 simülasyonlarında boşluktan dolan SL'lerin oranı ve ort. ek kayıp (R).
- Performans: N-L/N-S/M girişleri X1, X5 ile, hafta içi (karar Pzt 00:00 – Cum rollover) vs hafta sonu (Cum rollover – Pzr
  24:00 UTC) ortR; ATR14(1h) / fiyat oranı (E32 sıkışma) ve spread/SL oranı (maliyetin R cinsinden payı).
- **Ön-kayıtlı karar kuralı:** hafta sonu bloğu önerilir ⇔ (M girişinde hafta sonu − hafta içi Δ ortR < 0, DISCOVERY'de
  P(Δ<0) ≥ %90 ve OOS∪BLIND'da aynı işaret) VEYA (hafta sonu medyan spread/SL oranı hafta içinin ≥ 1,5 katı) VEYA
  (hafta sonu boşluk kaybı ortalaması ≥ 0,05R/işlem). Aksi: hafta sonu kapalı tutmak için kanıt yok.

## 4. Raporlama
Her hipotez tablosu: n, WR, ortR, %95 GA, P(EV>0), yarılar, stres, icra farkı, tek-poz, plasebo yüzdeliği, BLIND işareti,
taban (hep-long), başabaş WR. Tüm hücreler `results/` altına CSV/JSON.

## Amendments
(boş)

### A1 (2026-10-21, C01–C07 sonuçları görüldükten SONRA) — yalnız betimsel ek analiz, verdikti değiştirmez
C04 (QQQ açılış boşluğu, ters mod, θ=0,5) DISCOVERY'de +0,21R / max-z p_sel 0,003 verdi, OOS∪BLIND'da +0,034R (kart 5/6,
plasebo %81 → prereg'e göre RED). Mekanizmayı anlamak için şu SONRADAN analizler yapılır ve "post-hoc" etiketlenir:
(a) kollar: boşluk yukarı → SELL vs boşluk aşağı → BUY; (b) yıllık işaret; (c) kontrol: BTC'nin kendi önceki ABD kapanışı
(D−1 16:00 ET) → 10:00 ET hareketi aynı θ (BTC kendi σ20'si, saat-eşli) ile ters çevrilirse ne olur, ve QQQ boşluğu BTC'nin
kendi hareketine eklendiğinde (2×2: QQQ boşluk işareti × BTC gece hareketi işareti) fark nerede. Bu analizlerden çıkan
hiçbir şey kenar olarak raporlanmaz; yalnız yeni bir ön-kayıt için aday notu (C sınıfı) olabilir.

### A2 (2026-10-21, sonuçlardan SONRA) — plasebo duyarlılığı, verdikti değiştirmez
Yıl-içi etiket permütasyonu kalıcı (otokorelasyonlu) VIX rejimini parçalar; BTC trendleri de kalıcı olduğundan bu plasebo
iyimser (anti-konservatif) olabilir (DISC max-z p_sel 0,003 ama OOS∪BLIND'da etki yok). Kontrol için C01 k1'de dairesel
kaydırma plasebosu (VIX serisi ≥60 gün kaydırılır, 1.000 çekiliş) ek olarak raporlanır (`31_circular_placebo.py`).
