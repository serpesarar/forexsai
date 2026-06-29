# Decider REGIME — güncel piyasa bağlamı

> Decider'ın her kararda okuduğu güncel makro/rejim notu. Yavaş değişir; haftalık
> re-damıtma veya elle güncellenir. "Şu an piyasa nasıl davranıyor" özeti.

## Güncel (2026-06-27)
- **VIX rejimi:** eşik 18.4. VIX<18.4 (sakin) → NDX **SELL** favored; ≥18.4 (stres) → NDX **BUY** favored.
  (canlı VIX kararda `/api/macro-gauges`'tan = Yahoo `^VIX`, saatlik)
- **VIX FRESHNESS (kritik):** `^VIX` yalnız US RTH'de (16:30–23:15 EEST) canlı; dışında DONUK. Decider
  VIX yönünü YALNIZ US RTH açıkken kullanır (`vix.fresh=true`); off-hours/weekend → bayat, yön VERME.
  Eşik ±0.4 bandında (18.0–18.8) → neutral, bıçak-sırtı flip yok. vix.fresh=false ise yalnız fiyat-kanıtı.
- **Sembol trend bağlamı (base-rate-drift uyarısı):**
  - USOIL: dönem **düşüş** trendi → SELL base'i yüksek (%80). Trend dönerse SELL güveni düşür.
  - XAU: dönem **yükseliş** + yapısal BUY-bias (%78) → BUY base'i yüksek. SELL kalıcı yasak.
  - NDX/GDAXI: iki yön de dengeli (base ~%50), kapı lift'i temiz (+25-38pp).
- **Aktif yasaklar:** XAUUSD SELL (kalıcı), USOIL BUY (mean-rev çöker — momentum scope ayrı).

## 🔄 Güncelleme tetikleyicileri
- Bir sembolde canlı WR base'inin >15pp altına inerse → trend flip şüphesi, ilgili yön güvenini düşür.
- VIX eşik bölgesinde (17-19) uzun süre takılırsa → NDX yön sinyali zayıf, BEKLE'ye meyilli ol.
- Yüksek-etkili olay haftası (FOMC/CPI/NFP/EIA) → o sembolde boyut küçült.
