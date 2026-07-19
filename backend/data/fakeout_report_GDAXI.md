# Sahte Kırılım (Fakeout) Madencilik Raporu — GDAXI.INDX

Üretim: 2026-07-16T23:12:31.867752+00:00 · Olay: 1006 · Aralık: 2026-03-18 → 2026-07-16

**Taban sahte-kırılım oranı:** train %53.6 · test %52.6

Etiket: kırılım kapanışından ±1.0×ATR iki-hedef yarışı (1m çözünürlük). Devam hedefi önce → GERÇEK; ters hedef önce → SAHTE. Belirsizler atıldı.

## Segmentler

**seviye_türü:**
- channel_lower: n=93, sahte %60.2
- channel_upper: n=93, sahte %50.5
- resistance: n=367, sahte %55.0
- support: n=453, sahte %51.0

**yön:**
- down: n=546, sahte %52.6
- up: n=460, sahte %54.1

## Tekil Koşullar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `prebreak_range_atr >= 6.302` | 141 | 44.7 | -8.9pp | 56 | 39.3 | -13.4pp |
| `prebreak_range_atr <= 3.616` | 141 | 63.8 | +10.3pp | 58 | 58.6 | +6.0pp |
| `vol_ratio >= 1.345` | 262 | 44.7 | -8.9pp | 86 | 48.8 | -3.8pp |

## Kombinasyonlar (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `prebreak_range_atr >= 6.302 VE vol_ratio >= 1.345` | 44 | 38.6 | -14.9pp | 16 | 37.5 | -15.1pp |

## Karar Ağacı Kuralları (OOS doğrulanmış)

| Kural | Train n | Train sahte% | Lift | Test n | Test sahte% | OOS Lift |
|---|---|---|---|---|---|---|
| `vol_ratio <= 1.305 VE prebreak_range_atr >= 3.63 VE bb_width_rank <= 25.174` | 38 | 28.9 | -24.6pp | 22 | 40.9 | -11.7pp |
| `vol_ratio <= 1.305 VE prebreak_range_atr <= 3.63 VE rsi14 >= 38.331` | 46 | 69.6 | +16.0pp | 20 | 55.0 | +2.4pp |

## Birleşik Kırılım Skoru (GERÇEK-pozitif kalibrasyon)

Bileşenler: `prebreak_range_atr >= 6.302` (+1); `prebreak_range_atr <= 3.616` (−1); `vol_ratio >= 1.345` (+1)

| Skor aralığı | Train n | Train gerçek% | Test n | Test gerçek% |
|---|---|---|---|---|
| -99 … -2 | 0 | None | 0 | None |
| -1 … -1 | 75 | 22.7 | 37 | 35.1 |
| 0 … 0 | 338 | 44.4 | 160 | 45.6 |
| 1 … 1 | 247 | 53.8 | 89 | 52.8 |
| 2 … 99 | 44 | 61.4 | 16 | 62.5 |

## Teyit Protokolü — Giriş Varyantları (bağımsız backtest)

| Strateji | Train n | Train WR% | Train EV(R) | Test n | Test WR% | Test EV(R) |
|---|---|---|---|---|---|---|
| breakout_bar_1to1 | 704 | 46.4 | -0.072 | 302 | 47.4 | -0.052 |
| next_bar_confirm_1to1 | 528 | 47.3 | -0.053 | 223 | 48.0 | -0.04 |
| next_bar_confirm_1.5to1 | 527 | 36.6 | -0.084 | 223 | 37.2 | -0.07 |
| retest_hold_1to1 | 376 | 46.8 | -0.064 | 158 | 46.8 | -0.063 |
| retest_hold_1.5to1 | 376 | 36.7 | -0.082 | 158 | 37.3 | -0.066 |

**Koşullu bilgi (filtre gücü):** confirm_yes: n=754, orijinal gerçek %57.4; confirm_no: n=252, orijinal gerçek %14.7; retest_hold: n=534, orijinal gerçek %53.9; retest_fail: n=340, orijinal gerçek %22.9; retest_none: n=132, orijinal gerçek %78.8

## Dürüstlük Notları

- Seviyeler yalnızca olay anına kadar TEYİTLENMİŞ pivotlardan kuruldu (lookahead yok).
- Kurallar kronolojik %70/30 ayrımında OOS işaret korumazsa elendi.
- `test_lift_pp` küçük örneklemde gürültülüdür; runtime kapısı yalnızca hem train hem test lifti aynı yönde GÜÇLÜ olan kuralları kullanmalıdır.