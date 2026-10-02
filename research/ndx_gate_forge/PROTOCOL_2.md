# Tur 2 — Başarılı örneklerin ortak mantığı → türev hipotezler (ön-kayıt, 2026-09-30)

## Ortak ilkeler (kanıtlı örneklerden çıkarım)

| İlke | Destekleyen örnekler |
|---|---|
| **P1 Ölçek ayrışması**: kısa ölçekte (dakika–saat) hareket SÜRER, günlük ölçekte GERİ DÖNER | kısa: decider bıçak kapısı (5m kanalda işleme karşı ≥2σ → WR monoton düşer, A−), TREND_GATE (%63 vs %43), DAYCOMBO, momentum filtresi, fakeout "gerçek" çağrısı. günlük: K5 stres→SELL yok, K6 uzama→BUY yok, VIXREG (yüksek VIX→BUY, düşük→SELL; 10 yılda 9/10) |
| **P2 Maruziyet × sürüklenme**: E[PnL]=μ·E[τ]; para girişte değil pozisyonun AÇIK kaldığı sürede kazanılır | Cuma öğleden sonra ve hafta sonu tutma yasağı, ASIA, TQ çukurları, K1 Pazartesi, K3 ay sonu |
| **P3 Teyit > tahmin** | probasyon MOD-E (iki dönemde +), fakeout +1-bar teyidi |
| **P4 SELL vergisi**: yapısal yukarı sürüklenme; NDX'te kazanan kapıların neredeyse hepsi SELL bloklar | Cuma, formasyon SELL %22,6, SMC SELL, USOIL SELL, K1, K5 |
| **P5 Varyans ölçeklemesi**: EV_R ≈ (μ/σ²)·TP | stres günü kapıları işlem düzeyinde söndü |
| **P6 Bilgi şoku**: hacim patlamasında yön öngörülemez | decider vol≥1.5 (A−), bot otopsisi hacim<1,5, fakeout klimaks |

## Türev hipotezler (parametreler sabit, ayar yok)

| # | Hipotez | Tanım | Beklenen |
|---|---|---|---|
| T1 | **Günlük gerilme pusulası** (K5+K6'nın vol-normalize, durağan hâli) | z5 = son 5 işlem günü NDX getirisi / (20g günlük std·√5), önceki kapanıştan. z5 ≤ −1 → SELL yok; z5 ≥ +1 → BUY yok | bloklanan < taban |
| T2 | **Bıçak kapısı → bota transfer** (decider'dan bağımsız popülasyon) | chz_dir = son 50 kapanmış 5m kapanışının linreg kanalında işlem yönüne karşı z ≥ 2,0 → açma | bloklanan < taban |
| T3 | **Hacim patlaması → bota transfer** | son kapanmış 5m hacmi / önceki 20 barın ortalaması ≥ 1,5 → açma | bloklanan < taban |
| T4 | **Teorinin öngörüsü**: günlük kapıların etkisi sakin rejimde büyük | K1/K5/T1 etkisini önceki 20g günlük vol tertiline böl | düşük-vol tertilde en negatif |
| T5 | **Teyitli stres** (P3 × K5) | K5 günlerinde SELL'e yalnız fiyat önceki günün RTH dibinin altındaysa izin ver | izin verilen SELL'ler bloklananlardan iyi |
| T6 | **Sürüklenme penceresine taşıma** (P2 çıkış tarafı) | Pzt–Per NY 16:55'te hâlâ açık SELL kapatılır, BUY taşınır | 16:55'ten sonraki SELL P&L'i < 0 |

Katmanlar: genel 1m (D25a, D25b, C26, M26, S26), 30m 2021-26 / 15m 2023-26 yıl-yıl,
botun kapı evreni (artımsal), botun gerçek 317 kararı. Holm düzeltmesi 6 hipotez üzerinden.

## Ek (tur 2 sonuçları görüldükten sonra, ayna testleri — post-hoc olarak işaretli)
- K6b: K6 günü (NDX 200g +%10) ve fiyat > önceki RTH tepesi → BUY yok ("coşku kovalama").
- K5-ayna: dün NDX ≥ +%1,5 veya 5g ≥ +%4 → BUY yok; ve bunun > önceki tepe alt hücresi.
Beklenti (10 yıl bulgusundan): korku (aşağı stres) geri döner, coşku dönmez → K5-ayna tutmaz.
