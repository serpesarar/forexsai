# Sahte Kırılım (Fakeout) Madencilik Raporu — NDX.INDX

Üretim: 2026-07-16T18:48:20.459165+00:00 · Olay: 1005 · Aralık: 2026-03-18 → 2026-07-16

**Taban sahte-kırılım oranı:** train %68.6 · test %64.6

Etiket: kırılım kapanışından ±1.0×ATR iki-hedef yarışı (1m çözünürlük). Devam hedefi önce → GERÇEK; ters hedef önce → SAHTE. Belirsizler atıldı.

## Segmentler

**seviye_türü:**
- channel_lower: n=130, sahte %68.5
- channel_upper: n=105, sahte %78.1
- resistance: n=415, sahte %65.3
- support: n=355, sahte %66.2

**yön:**
- down: n=485, sahte %66.8
- up: n=520, sahte %67.9

## Tekil Koşullar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `pen_atr >= 0.865` | 141 | 80.1 | +11.6pp | 59 | 81.4 | +16.8pp |
| `approach_speed_atr >= 3.198` | 141 | 82.3 | +13.7pp | 57 | 80.7 | +16.1pp |
| `approach_speed_atr <= 0.505` | 141 | 55.3 | -13.2pp | 69 | 49.3 | -15.3pp |
| `rsi14 <= 34.594` | 141 | 81.6 | +13.0pp | 66 | 78.8 | +14.2pp |
| `vol_ratio >= 1.274` | 141 | 77.3 | +8.7pp | 85 | 76.5 | +11.9pp |
| `vwap_dist_atr <= -0.92` | 141 | 56.0 | -12.5pp | 57 | 54.4 | -10.2pp |
| `vol_ratio <= 0.997` | 211 | 58.8 | -9.8pp | 98 | 55.1 | -9.5pp |
| `ema50_slope_atr >= 0.53` | 211 | 77.3 | +8.7pp | 83 | 73.5 | +8.9pp |
| `vwap_dist_atr >= 2.388` | 281 | 78.3 | +9.7pp | 106 | 72.6 | +8.1pp |
| `wick_against_atr <= 0.041` | 141 | 78.7 | +10.2pp | 68 | 72.1 | +7.5pp |
| `with_ema200_trend <= 0.5` | 211 | 59.7 | -8.8pp | 117 | 57.3 | -7.3pp |
| `ema50_slope_atr <= -0.569` | 141 | 58.2 | -10.4pp | 70 | 58.6 | -6.0pp |
| `attempts >= 3.6` | 141 | 56.7 | -11.8pp | 86 | 59.3 | -5.3pp |
| `dist_ema200_atr >= 4.656` | 141 | 77.3 | +8.7pp | 43 | 69.8 | +5.2pp |
| `body_ratio >= 0.781` | 281 | 77.2 | +8.7pp | 115 | 67.8 | +3.3pp |
| `adx14 <= 17.757` | 141 | 59.6 | -9.0pp | 71 | 62.0 | -2.6pp |
| `pen_atr <= 0.207` | 141 | 58.9 | -9.7pp | 70 | 62.9 | -1.7pp |

## Kombinasyonlar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `pen_atr >= 0.865 VE rsi14 <= 34.594` | 41 | 90.2 | +21.7pp | 15 | 100.0 | +35.4pp |
| `vol_ratio >= 1.274 VE ema50_slope_atr >= 0.53` | 44 | 81.8 | +13.3pp | 16 | 100.0 | +35.4pp |
| `approach_speed_atr >= 3.198 VE vol_ratio >= 1.274` | 45 | 88.9 | +20.3pp | 25 | 96.0 | +31.4pp |
| `pen_atr >= 0.865 VE ema50_slope_atr >= 0.53` | 40 | 92.5 | +23.9pp | 13 | 92.3 | +27.7pp |
| `vol_ratio >= 1.274 VE vwap_dist_atr >= 2.388` | 55 | 87.3 | +18.7pp | 24 | 91.7 | +27.1pp |
| `pen_atr >= 0.865 VE wick_against_atr <= 0.041` | 37 | 89.2 | +20.6pp | 20 | 90.0 | +25.4pp |
| `pen_atr >= 0.865 VE vwap_dist_atr >= 2.388` | 71 | 88.7 | +20.2pp | 26 | 88.5 | +23.9pp |
| `vol_ratio <= 0.997 VE ema50_slope_atr <= -0.569` | 50 | 48.0 | -20.6pp | 24 | 41.7 | -22.9pp |
| `approach_speed_atr >= 3.198 VE rsi14 <= 34.594` | 61 | 90.2 | +21.6pp | 20 | 85.0 | +20.4pp |
| `approach_speed_atr >= 3.198 VE ema50_slope_atr >= 0.53` | 39 | 87.2 | +18.6pp | 13 | 84.6 | +20.0pp |
| `approach_speed_atr <= 0.505 VE ema50_slope_atr <= -0.569` | 34 | 47.1 | -21.5pp | 22 | 45.5 | -19.1pp |
| `ema50_slope_atr >= 0.53 VE wick_against_atr <= 0.041` | 49 | 91.8 | +23.3pp | 24 | 83.3 | +18.8pp |
| `approach_speed_atr <= 0.505 VE vol_ratio <= 0.997` | 56 | 44.6 | -23.9pp | 32 | 46.9 | -17.7pp |
| `vol_ratio <= 0.997 VE with_ema200_trend <= 0.5` | 73 | 54.8 | -13.8pp | 40 | 47.5 | -17.1pp |
| `vwap_dist_atr <= -0.92 VE vol_ratio <= 0.997` | 49 | 46.9 | -21.6pp | 23 | 47.8 | -16.7pp |
| `vwap_dist_atr >= 2.388 VE wick_against_atr <= 0.041` | 65 | 87.7 | +19.1pp | 27 | 77.8 | +13.2pp |
| `approach_speed_atr <= 0.505 VE vwap_dist_atr <= -0.92` | 53 | 49.1 | -19.5pp | 32 | 53.1 | -11.4pp |
| `approach_speed_atr <= 0.505 VE with_ema200_trend <= 0.5` | 66 | 50.0 | -18.6pp | 47 | 53.2 | -11.4pp |

## Karar Ağacı Kuralları (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `vwap_dist_atr >= 1.526 VE body_ratio <= 0.846 VE vol_buildup >= 1.193` | 38 | 94.7 | +26.2pp | 26 | 92.3 | +27.7pp |
| `vwap_dist_atr >= 1.526 VE body_ratio >= 0.846 VE vol_ratio >= 1.035` | 77 | 98.7 | +30.1pp | 18 | 88.9 | +24.3pp |
| `vwap_dist_atr <= 1.526 VE adx14 >= 13.17 VE prebreak_range_atr >= 5.46` | 84 | 45.2 | -23.3pp | 51 | 54.9 | -9.7pp |

## Birleşik Kırılım Skoru (GERÇEK-pozitif kalibrasyon)

Bileşenler: `pen_atr >= 0.865` (−1); `approach_speed_atr >= 3.198` (−1); `approach_speed_atr <= 0.505` (+1); `rsi14 <= 34.594` (−1); `vol_ratio >= 1.274` (−1); `vwap_dist_atr <= -0.92` (+1); `vol_ratio <= 0.997` (+1); `ema50_slope_atr >= 0.53` (−1)

| Skor aralığı | Train n | Train gerçek% | Test n | Test gerçek% |
|---|---|---|---|---|
| -99 … -2 | 183 | 16.4 | 88 | 12.5 |
| -1 … -1 | 145 | 26.9 | 57 | 38.6 |
| 0 … 0 | 150 | 31.3 | 59 | 49.2 |
| 1 … 1 | 133 | 43.6 | 53 | 37.7 |
| 2 … 99 | 92 | 51.1 | 45 | 55.6 |

## Teyit Protokolü — Giriş Varyantları (bağımsız backtest)

| Strateji | Train n | Train WR% | Train EV(R) | Test n | Test WR% | Test EV(R) |
|---|---|---|---|---|---|---|
| breakout_bar_1to1 | 703 | 31.4 | -0.372 | 302 | 35.4 | -0.292 |
| next_bar_confirm_1to1 | 545 | 40.9 | -0.182 | 232 | 46.6 | -0.069 |
| next_bar_confirm_1.5to1 | 544 | 30.5 | -0.237 | 232 | 35.3 | -0.116 |
| retest_hold_1to1 | 392 | 43.6 | -0.128 | 166 | 45.2 | -0.096 |
| retest_hold_1.5to1 | 391 | 31.2 | -0.22 | 166 | 35.5 | -0.111 |

**Koşullu bilgi (filtre gücü):** confirm_yes: n=777, orijinal gerçek %38.4; confirm_no: n=228, orijinal gerçek %13.2; retest_hold: n=558, orijinal gerçek %39.1; retest_fail: n=321, orijinal gerçek %17.8; retest_none: n=126, orijinal gerçek %42.1

## Dürüstlük Notları

- Seviyeler yalnızca olay anına kadar TEYİTLENMİŞ pivotlardan kuruldu (lookahead yok).
- Kurallar kronolojik %70/30 ayrımında OOS işaret korumazsa elendi.
- `test_lift_pp` küçük örneklemde gürültülüdür; runtime kapısı yalnızca hem train hem test lifti aynı yönde GÜÇLÜ olan kuralları kullanmalıdır.