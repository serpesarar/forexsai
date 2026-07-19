# Sahte Kırılım (Fakeout) Madencilik Raporu — XAUUSD

Üretim: 2026-07-16T23:16:35.292104+00:00 · Olay: 964 · Aralık: 2026-04-07 → 2026-07-16

**Taban sahte-kırılım oranı:** train %56.5 · test %61.0

Etiket: kırılım kapanışından ±1.0×ATR iki-hedef yarışı (1m çözünürlük). Devam hedefi önce → GERÇEK; ters hedef önce → SAHTE. Belirsizler atıldı.

## Segmentler

**seviye_türü:**
- channel_lower: n=78, sahte %44.9
- channel_upper: n=84, sahte %61.9
- resistance: n=316, sahte %67.7
- support: n=486, sahte %52.9

**yön:**
- down: n=564, sahte %51.8
- up: n=400, sahte %66.5

## Tekil Koşullar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `vwap_dist_atr <= -0.181` | 202 | 48.0 | -8.5pp | 69 | 52.2 | -8.9pp |
| `approach_speed_atr >= 2.4` | 202 | 64.9 | +8.3pp | 63 | 66.7 | +5.6pp |
| `approach_speed_atr <= -0.071` | 135 | 45.9 | -10.6pp | 49 | 59.2 | -1.9pp |
| `hour_utc >= 18.0` | 142 | 64.8 | +8.3pp | 61 | 62.3 | +1.3pp |

## Kombinasyonlar (OOS doğrulanmış)

_(OOS'ta ayakta kalan kural yok)_

## Karar Ağacı Kuralları (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `rsi14 >= 59.356 VE bb_width_rank <= 74.132 VE rsi14 <= 65.872` | 60 | 71.7 | +15.1pp | 24 | 75.0 | +14.0pp |
| `rsi14 <= 59.356 VE rsi14 >= 37.45 VE vol_ratio >= 1.418` | 60 | 23.3 | -33.2pp | 57 | 59.6 | -1.4pp |

## Birleşik Kırılım Skoru (GERÇEK-pozitif kalibrasyon)

Bileşenler: `vwap_dist_atr <= -0.181` (+1); `approach_speed_atr >= 2.4` (−1); `approach_speed_atr <= -0.071` (+1); `hour_utc >= 18.0` (−1)

| Skor aralığı | Train n | Train gerçek% | Test n | Test gerçek% |
|---|---|---|---|---|
| -99 … -2 | 48 | 39.6 | 7 | 42.9 |
| -1 … -1 | 187 | 32.1 | 75 | 33.3 |
| 0 … 0 | 239 | 43.1 | 139 | 36.0 |
| 1 … 1 | 124 | 54.0 | 55 | 54.5 |
| 2 … 99 | 76 | 57.9 | 14 | 35.7 |

## Teyit Protokolü — Giriş Varyantları (bağımsız backtest)

| Strateji | Train n | Train WR% | Train EV(R) | Test n | Test WR% | Test EV(R) |
|---|---|---|---|---|---|---|
| breakout_bar_1to1 | 674 | 43.5 | -0.13 | 290 | 39.0 | -0.22 |
| next_bar_confirm_1to1 | 499 | 44.5 | -0.11 | 154 | 51.3 | 0.026 |
| next_bar_confirm_1.5to1 | 500 | 36.6 | -0.085 | 150 | 40.7 | 0.017 |
| retest_hold_1to1 | 374 | 45.5 | -0.091 | 113 | 52.2 | 0.044 |
| retest_hold_1.5to1 | 375 | 36.3 | -0.093 | 109 | 41.3 | 0.032 |

**Koşullu bilgi (filtre gücü):** confirm_yes: n=656, orijinal gerçek %53.0; confirm_no: n=308, orijinal gerçek %18.8; retest_hold: n=490, orijinal gerçek %49.6; retest_fail: n=374, orijinal gerçek %23.0; retest_none: n=100, orijinal gerçek %77.0

## Dürüstlük Notları

- Seviyeler yalnızca olay anına kadar TEYİTLENMİŞ pivotlardan kuruldu (lookahead yok).
- Kurallar kronolojik %70/30 ayrımında OOS işaret korumazsa elendi.
- `test_lift_pp` küçük örneklemde gürültülüdür; runtime kapısı yalnızca hem train hem test lifti aynı yönde GÜÇLÜ olan kuralları kullanmalıdır.