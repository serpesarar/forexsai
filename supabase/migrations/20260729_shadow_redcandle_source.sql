-- Shadow Trade Tracker'a 'redcandle' kaynağı (2026-07-29)
--
-- Kaynak: büyük kırmızı 5m mum + teyit mumu (kapanış önceki mumun dibinin altında)
-- → SELL. 17 aylık ölçüm (research/RAPOR_SELL_MUM_DESTEK_2026-07-28.md EK bölümü)
-- bu ailenin tek hayatta kalan aday olduğunu gösterdi (TP 120/SL 25 ve TP 80/SL 30,
-- kör testte +0,150R / +0,079R, tabanı iki dönemde de yeniyor) AMA kenarın
-- tamamı zaman-stopu çıkışlarından geliyor ve 3 puanlık kaymada ölüyor.
-- Bu yüzden CANLIYA DEĞİL, yalnız gölgeye alınıyor: gerçek fiyatla ileriye dönük
-- doğrulama biriksin diye. shadow_pattern_trades tablosu prediction_logs ve
-- signal_lifecycle akışından tamamen izoledir.

alter table public.shadow_pattern_trades
  drop constraint if exists shadow_pattern_trades_source_check;

alter table public.shadow_pattern_trades
  add constraint shadow_pattern_trades_source_check
  check (source in ('pattern', 'fakeout', 'meta', 'redcandle'));
