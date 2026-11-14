# FAZ 6 — Fiyat dışı bilgi katmanları (Yön Lab, 2026-11-14)

Kod: `src/faz6_layers.py`, `src/tick_micro.py`, kutu dışa aktarımı `src/kutu_export_m5.py`. Tanımlar PROTOCOL EK-1 (sonuçlardan önce).
Çıktı: `results/faz6_<katman>.csv`, `faz6_ozet.json`.

## Erişim / kapsam / canlı karşılık
| Katman | Erişim | Kapsam | Canlıda | Not |
|---|---|---|---|---|
| L1 SqueezeMetrics DIX + GEX | ✅ ücretsiz CSV | 2011-05 → 2026-11-13 günlük | ✅ ertesi gün | S&P 500 kaynaklı (NDX vekili) |
| L2 Mega-cap (NVDA, AAPL, MSFT, AMZN, META, GOOGL, TSLA, AVGO) + SOXX/QQQ/SPY/IWM + VIX/DXY/TNX | ✅ yfinance 1h | 2023-12 → | ✅ | yalnız NY seans saatleri |
| L3 US500/US30/US2000 M5 → NAS100 | ✅ MT5 kutu (salt okuma, bu oturumda) | 2025-06 → | ✅ | sunucu = NY+7 |
| L4 Tick mikroyapısı | ✅ yerel Dukascopy 2025 bid/ask (hacim yok) | 2025 | ⚠ MT5 tick_recorder farklı besleme | KÖR yok → en çok B |
| Opsiyon strike / gamma flip | ❌ ücretsiz güvenilir kaynak yok | — | — | ücretli: SpotGamma/Cboe DataShop |
| Zorunlu akışlar | ✅ takvim | ana tarama §7 | ✅ | ay sonu/başı, vade, çeyrek sonu, tatil öncesi |
| Haber (`news_stories`) | ✅ | 2026-11-05 → (9 gün) | ✅ | sınanamayacak kadar kısa — ileri not |

## Sonuçlar (KEŞİF; eşik = katman içi dairesel kaydırma max-|t| q95, 200 tekrar)
| Katman | Hücre | Eşik | En büyük |t| | En iyi hücre | Seçilen |
|---|---|---|---|---|---|
| L1 DIX/GEX → NDX seans/gece/ertesi gün | 90 | 2,93 | 2,52 | ΔDIX(5g) alt %20 → gece +5,3 p (n 525 gün) | 0 |
| L2 Saatlik çapraz varlık | 105 | 3,25 | 2,20 | VIX son saat değişimi orta %20 → 15 dk −10 p (n 128) | 0 |
| L3 M5 çapraz endeks | 68 | 3,66 | 2,71 | US500 60 dk göreli güç üst %20 → NDX 1 s +5,2 p (n 1.256) | 0 |
| L4 Tick mikroyapısı | 50 | 3,00 | 2,14 | 60 dk tick dengesizliği alt %20 → 15 dk −2,3 p | 0 |
**Dört katmanın hiçbiri şans eşiğini geçmiyor.** GEX < 0 (GM-01'in koşulu) ve DIX uçları nakit seans/gece/ertesi gün yönünde
eşik altında; mega-cap genişliği, NVDA/SOXX öncülüğü, küçük şirket/geniş endeks göreli gücü ve VIX/DXY/TNX saatlik değişimleri NDX'in
sonraki 15 dk / 1 s / seans yönünü şanstan ayırt edilebilir biçimde söylemiyor; tick-yönü dengesizliği, kotasyon hızı ve spread
genişlemesi de.
