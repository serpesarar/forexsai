-- 2026-09-30 — indicator_snapshots: yalnız OKUMA izni (anon)
--
-- Neden: Railway backend Supabase'e anon anahtarla bağlanıyor. indicator_snapshots'ta
-- RLS açık ama hiç politika yoktu → backend'in yeni MT5 kaydedici beslemesi
-- (backend/services/mt5_recorder_feed.py) boş okuyordu. Bu tablo kutudaki
-- data_recorder'ın yazdığı broker OHLC + gösterge verisidir (hassas veri yok);
-- candle_cache'te anon okuma izni zaten mevcut.
-- Yazma / güncelleme / silme izni VERİLMEZ — kaydedici servis anahtarıyla yazar.
--
-- Geri alma: drop policy anon_select_indicator_snapshots on public.indicator_snapshots;

create policy anon_select_indicator_snapshots
    on public.indicator_snapshots
    for select
    to anon
    using (true);
