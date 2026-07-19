# Sahte Kırılım (Fakeout) Madencilik Raporu — USOIL.FOREX

Üretim: 2026-07-16T23:19:20.593611+00:00 · Olay: 891 · Aralık: 2026-04-07 → 2026-07-16

**Taban sahte-kırılım oranı:** train %53.5 · test %56.0

Etiket: kırılım kapanışından ±1.0×ATR iki-hedef yarışı (1m çözünürlük). Devam hedefi önce → GERÇEK; ters hedef önce → SAHTE. Belirsizler atıldı.

## Segmentler

**seviye_türü:**
- channel_lower: n=90, sahte %67.8
- channel_upper: n=85, sahte %50.6
- resistance: n=345, sahte %42.6
- support: n=371, sahte %62.5

**yön:**
- down: n=461, sahte %63.6
- up: n=430, sahte %44.2

## Tekil Koşullar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `vol_ratio >= 2.297` | 124 | 71.0 | +17.5pp | 42 | 73.8 | +17.8pp |
| `vwap_dist_atr <= -1.114` | 125 | 33.6 | -19.9pp | 36 | 38.9 | -17.1pp |
| `with_ema200_trend <= 0.5` | 180 | 40.6 | -12.9pp | 58 | 43.1 | -12.9pp |
| `approach_speed_atr >= 3.314` | 125 | 65.6 | +12.1pp | 50 | 68.0 | +12.0pp |
| `level_age_bars >= 756.2` | 125 | 39.2 | -14.3pp | 64 | 46.9 | -9.1pp |
| `ema50_slope_atr <= -0.596` | 125 | 37.6 | -15.9pp | 50 | 50.0 | -6.0pp |
| `wick_against_atr >= 0.473` | 125 | 68.8 | +15.3pp | 26 | 61.5 | +5.6pp |
| `rsi14 <= 38.974` | 187 | 69.0 | +15.5pp | 83 | 61.4 | +5.5pp |
| `adx14 <= 16.931` | 126 | 43.7 | -9.8pp | 67 | 52.2 | -3.7pp |
| `vwap_dist_atr >= 1.399` | 312 | 64.7 | +11.3pp | 153 | 58.8 | +2.9pp |

## Kombinasyonlar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `vol_ratio >= 2.297 VE vwap_dist_atr >= 1.399` | 79 | 75.9 | +22.5pp | 22 | 86.4 | +30.4pp |
| `vol_ratio >= 2.297 VE wick_against_atr >= 0.473` | 56 | 80.4 | +26.9pp | 11 | 81.8 | +25.8pp |
| `with_ema200_trend <= 0.5 VE level_age_bars >= 756.2` | 58 | 25.9 | -27.6pp | 18 | 38.9 | -17.1pp |
| `vol_ratio >= 2.297 VE rsi14 <= 38.974` | 59 | 86.4 | +33.0pp | 25 | 72.0 | +16.0pp |
| `wick_against_atr >= 0.473 VE rsi14 <= 38.974` | 49 | 83.7 | +30.2pp | 10 | 70.0 | +14.0pp |
| `approach_speed_atr >= 3.314 VE vwap_dist_atr >= 1.399` | 93 | 68.8 | +15.4pp | 33 | 69.7 | +13.7pp |
| `level_age_bars >= 756.2 VE ema50_slope_atr <= -0.596` | 49 | 30.6 | -22.8pp | 16 | 43.8 | -12.2pp |
| `approach_speed_atr >= 3.314 VE rsi14 <= 38.974` | 68 | 72.1 | +18.6pp | 23 | 60.9 | +4.9pp |
| `rsi14 <= 38.974 VE vwap_dist_atr >= 1.399` | 126 | 75.4 | +21.9pp | 53 | 58.5 | +2.5pp |

## Karar Ağacı Kuralları (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `vwap_dist_atr >= 0.336 VE rsi14 <= 49.599 VE vol_ratio >= 2.535` | 47 | 97.9 | +44.4pp | 19 | 73.7 | +17.7pp |
| `vwap_dist_atr <= 0.336 VE level_age_bars >= 905.5 VE atr_pct <= 0.32` | 25 | 0.0 | -53.5pp | 19 | 47.4 | -8.6pp |
| `vwap_dist_atr >= 0.336 VE rsi14 >= 49.599 VE approach_speed_atr >= 4.005` | 32 | 81.2 | +27.8pp | 10 | 60.0 | +4.0pp |
| `vwap_dist_atr >= 0.336 VE rsi14 <= 49.599 VE vol_ratio <= 2.535` | 147 | 67.3 | +13.9pp | 75 | 57.3 | +1.4pp |

## Birleşik Kırılım Skoru (GERÇEK-pozitif kalibrasyon)

Bileşenler: `vol_ratio >= 2.297` (−1); `vwap_dist_atr <= -1.114` (+1); `with_ema200_trend <= 0.5` (+1); `approach_speed_atr >= 3.314` (−1); `level_age_bars >= 756.2` (+1); `ema50_slope_atr <= -0.596` (+1); `wick_against_atr >= 0.473` (−1); `rsi14 <= 38.974` (−1)

| Skor aralığı | Train n | Train gerçek% | Test n | Test gerçek% |
|---|---|---|---|---|
| -99 … -2 | 129 | 23.3 | 36 | 30.6 |
| -1 … -1 | 122 | 40.2 | 64 | 34.4 |
| 0 … 0 | 166 | 47.0 | 84 | 44.0 |
| 1 … 1 | 77 | 63.6 | 44 | 54.5 |
| 2 … 99 | 129 | 65.1 | 40 | 60.0 |

## Teyit Protokolü — Giriş Varyantları (bağımsız backtest)

| Strateji | Train n | Train WR% | Train EV(R) | Test n | Test WR% | Test EV(R) |
|---|---|---|---|---|---|---|
| breakout_bar_1to1 | 623 | 46.5 | -0.07 | 268 | 44.0 | -0.12 |
| next_bar_confirm_1to1 | 466 | 45.5 | -0.09 | 189 | 49.2 | -0.016 |
| next_bar_confirm_1.5to1 | 466 | 41.6 | 0.041 | 189 | 37.6 | -0.061 |
| retest_hold_1to1 | 332 | 45.5 | -0.09 | 144 | 45.1 | -0.097 |
| retest_hold_1.5to1 | 332 | 42.2 | 0.054 | 144 | 36.1 | -0.097 |

**Koşullu bilgi (filtre gücü):** confirm_yes: n=655, orijinal gerçek %49.8; confirm_no: n=236, orijinal gerçek %34.7; retest_hold: n=476, orijinal gerçek %46.0; retest_fail: n=302, orijinal gerçek %38.7; retest_none: n=113, orijinal gerçek %63.7

## Dürüstlük Notları

- Seviyeler yalnızca olay anına kadar TEYİTLENMİŞ pivotlardan kuruldu (lookahead yok).
- Kurallar kronolojik %70/30 ayrımında OOS işaret korumazsa elendi.
- `test_lift_pp` küçük örneklemde gürültülüdür; runtime kapısı yalnızca hem train hem test lifti aynı yönde GÜÇLÜ olan kuralları kullanmalıdır.