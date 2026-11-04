-- 2026-11-04 — candle_cache kaynak etiketi
--
-- Neden (analyst_reports/candle_cache_karisik_besleme_2026-11-04.md): tabloda hangi
-- yazarın hangi satırı ürettiği görülemiyordu.
-- source: mt5_box (kaydedici) | mt5_repair (onarım) | mt5_upload | mt5_redis | upstream_eod.
-- NULL = bu migration öncesi, kaynak bilinmiyor.
-- Yazarlar kolonu çalışma anında yoklar: uygulanınca kendiliğinden kullanılmaya başlar.
--
-- Geri alma: alter table public.candle_cache drop column source;

alter table public.candle_cache add column if not exists source text;
