-- vix_live — Pepperstone canlı VIX (vix_recorder.py UPSERT eder, backend macro_data_service okur).
-- Tek satır (symbol PK = 'VIX'), her 60s güncellenir. Bulut backend yerel MT5'e bağlanamadığı için
-- bu tablo köprü görevi görür. Recorder kapalıysa backend yfinance'e düşer (fallback).

create table if not exists public.vix_live (
    symbol   text primary key,                     -- 'VIX' (tek satır, upsert)
    value    double precision not null,            -- canlı VIX değeri (Pepperstone futures ~spot)
    ts_utc   timestamptz not null default now(),   -- yazılma anı (UTC) — backend tazelik kontrolü
    source   text                                  -- 'pepperstone:<symbol>'
);

alter table public.vix_live enable row level security;

-- service-role key RLS'i bypass eder (recorder + backend onu kullanır). Frontend okuması
-- gerekiyorsa anon read policy ekle (şu an gerekmez):
-- create policy "vix_live anon read" on public.vix_live for select to anon using (true);

comment on table public.vix_live is 'Canlı VIX (Pepperstone MT5 → vix_recorder.py). Backend macro_data_service okur; yfinance fallback.';
