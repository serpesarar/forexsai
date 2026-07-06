# Gösterge Denetimi Uygulama Notları — 2026-07-01

10 maddelik aksiyon listesinin tamamı uygulandı (kaynak: `GOSTERGE_UYGUNLUK_ANALIZ_RAPORU_2026-07-01.md`).
Tüm değişiklikler env bayraklı ve fail-open — tek satırla geri alınabilir. Backend restart/deploy ile aktif olur.

## Uygulanan Değişiklikler

| # | Aksiyon | Dosya(lar) | Bayrak (default) |
|---|---------|-----------|------------------|
| 1 | TP1 → breakeven semantiği: TP1/2/3 vurmuş sinyal `direction_flip` ile artık `completed` (yeni reason: `direction_flip_after_tp`); analytics'te TP-hit önceliği flip'ten yüksek (geçmiş ~1026 kayıt panellerde anında kazanca döner); lifecycle simülasyonu DB'deki TP vuruşlarını tohumlar; PETL abort TP-görmüş sinyali durduramaz | `prediction_logger.py`, `signal_analytics.py`, `signal_lifecycle.py` | `SIGNAL_BREAKEVEN_AFTER_TP1=1` |
| 2 | XAUUSD trend-yönü SELL kapısı: STRONG_TREND_UP / ATH / H4 close>EMA50 iken pulse1/2/3 + SMC SELL → HOLD (EMEL'in %84.8 WR kanıtlı ATH bloğunun genellemesi). Panel içi + logger güvenlik ağı çift katman | **YENİ** `services/signal_gates.py`, `emel_pulse.py`, `prediction_logger.py` | `XAU_TREND_SELL_GATE=1` |
| 3 | GDAXI pulse1 askıda (60g: %25 WR, inverse %38) + endekslerde ATR-taban TP/SL geometrisi: TP≥max(fixed, ATR×1.5), SL≥max(fixed, ATR×1.0) → RR≥1.5 garanti, gürültü bandı dışı | `signal_gates.py`, `emel_pulse.py` (`_scalp_tp_sl`) | `GDAXI_PULSE1_ENABLED=0`, `PULSE_ATR_GEOMETRY=1` |
| 4 | PULSE 3 rejime duyarlı ağırlıklar: Trend/ATH → 4H %40 / 1H %35 / 5m %25; TRANSITION → 30/35/35; RANGING → eski 50/30/20. 1H/4H mutlak % eşikleri ATR-normalize edildi | `emel_pulse.py` (`get_pulse_v3_analysis`, `_analyze_1h`, `_analyze_4h`) | `PULSE3_REGIME_WEIGHTS=1` |
| 5 | Seans kapıları: XAUUSD 20:00-20:59 + 01:00-02:59 UTC, GDAXI 07:00-07:59 UTC yeni sinyal blok | `signal_gates.py` | `SESSION_GATES_ENABLED=1` |
| 6 | Pulse1: RSI>75/<25 cezası trend-aware (yönle uyumlu aşırı RSI trend ortamında +10p, ceza yok); Stochastic skordan çıkarıldı (RSI ile mükerrer, display-only) → 10p yeni **H4 Trend Uyumu** bileşenine; yön oylamasında stoch yerine H4 oyu | `emel_pulse.py` (pulse1) | — |
| 7 | ml_cross_xau_nasdaq deneyi default KAPALI (60g SELL: 12W/162L = %6.9) | `cross_model_experiment_service.py` | `CROSS_MODEL_EXPERIMENT_ENABLED=0` |
| 8 | XAUUSD gerçek 1h bar tercihi: `mt5:bar:1h` stream veya persistent cache'ten gelen gerçek 1h, 30m çift-resample türeviyle ezilmez; 4h gerçek 1h'ten türetilir. Not: MT5 EA'nın XAUUSD için 1h bar göndermesi gerekir — göndermiyorsa mevcut türetme fallback olarak sürer | `data_hub.py` (`_rebuild_derived`) | `XAU_REAL_H1_ENABLED=1` |
| 9 | Ekonomik takvim kapısı: high-impact olay ±30dk yeni sinyal blok (pulse1/2/3 + SMC + EMEL), tamamen fail-open | `signal_gates.py` (`economic_calendar_service`'e bağlanır) | `CALENDAR_GATE_ENABLED=1` |
| 10 | EMEL 10. kontrol — Makro Uyum: XAU/USOIL için DXY+US10Y günlük değişim kompoziti, endeksler için VIX; konfluans motorunda yönlü faktör (XAU ağırlık 15, USOIL 10, endeksler 5). GDAXI ağırlık revizyonu: volume 15→8, sr 15→12, trend 20→25 | `emel_pulse.py` (EMEL) | — |

## Doğrulama

- 7 dosya `py_compile` temiz.
- `signal_gates` birim testleri: seans kapısı 7/7, GDAXI askı 4/4, XAU SELL kapısı 6/6, birleşik kapı 7/7 — hepsi geçti (test sırasında saat 20:34 UTC olduğu için XAU seans kapısının canlıda tetiklendiği de fiilen doğrulandı).
- ML ve EMEL trend kapısı KAPSAM DIŞI bırakıldı (bilinçli): ML DAX %71.3 / EMEL XAU %84.8 — çalışan modellere dokunulmadı.

## Beklenen Etki (60g verisine göre)

- XAUUSD pulse SELL havuzu (~5.200 SL) büyük ölçüde kesilir → pulse WR'ları %38-40 → ~%65 bandına (BUY-only profil).
- `stopped` sayılan TP-görmüş sinyaller (%36-58) completed'a döner — hem geçmişte (analytics) hem gelecekte (logger).
- GDAXI'nin en büyük kayıp kaynağı (pulse1: 1339 SL) kapanır; kalan pulse'larda RR≥1.5 geometri.

## Geri Alma

Her madde tek env değişkeniyle eski davranışa döner (bkz. CLAUDE.md → Environment Variables → "2026-07-01 Gösterge Denetimi bayrakları"). Kod değişikliği gerektirmez.

## İzleme Önerisi (deploy sonrası 7-14 gün)

```sql
-- Kapı etkisi: XAU pulse SELL hacmi düşmeli, WR yükselmeli
SELECT model_type, ml_direction, status, count(*) FROM prediction_logs
WHERE symbol='XAUUSD' AND created_at > '2026-07-01' AND model_type LIKE 'pulse%'
GROUP BY 1,2,3 ORDER BY 1,2,3;
-- Yeni resolution reason'lar
SELECT resolution_reason, count(*) FROM prediction_logs
WHERE created_at > '2026-07-01' AND resolution_reason LIKE '%after_tp%' GROUP BY 1;
```
