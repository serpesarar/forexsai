-- Shadow Pattern Trades — formasyon + fakeout tespitlerinin ileriye dönük
-- sanal işlem (paper-trade) doğrulama kaydı. prediction_logs / signal_lifecycle
-- akışından TAMAMEN İZOLE; shadow_trade_tracker servisi yazar/çözer.
--
-- Sızıntı garantisi tablo sözleşmesiyle: entry_time = karar anındaki son
-- KAPANMIŞ 5m barın kapanışı; çözümleme yalnız entry_time'dan SONRA açılan
-- barların high/low'u ile yapılır. Geçmişe bakan hiçbir alan yoktur.
create table if not exists public.shadow_pattern_trades (
  id             bigint generated always as identity primary key,
  source         text not null check (source in ('pattern','fakeout')),
  symbol         text not null,
  timeframe      text not null,                    -- tespit TF'i (pattern: 4h/1h, fakeout: 5m)
  pattern_type   text not null,                    -- GARTLEY / DOUBLE_TOP / fake_call / genuine_call ...
  pattern_name   text,                             -- insan-okur ad (Boğa Gartley, AI DEDEKTÖR: SAHTE)
  direction      text not null check (direction in ('BUY','SELL')),
  confidence     double precision not null,        -- karar anındaki güven (%). Eşik: >=60
  anchor_time    timestamptz not null,             -- tespitin çapası (D pivotu / kırılım barı) — dedup anahtarı
  entry_time     timestamptz not null,             -- karar anındaki son kapanmış 5m barın kapanış zamanı
  entry_price    double precision not null,
  tp_price       double precision not null,
  sl_price       double precision not null,
  expiry_time    timestamptz not null,             -- bu zamana dek TP/SL yoksa 'expired'
  status         text not null default 'open'
                 check (status in ('open','win','loss','expired','invalid')),
  exit_time      timestamptz,
  exit_price     double precision,
  r_multiple     double precision,                 -- (çıkış-giriş)/|giriş-SL| (yön işaretli)
  ambiguous      boolean not null default false,   -- aynı 5m barda TP+SL birlikte → konservatif LOSS
  details        jsonb,                            -- karar anı ham kanıt (fib oranları / dedektör çıktısı)
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique (source, symbol, pattern_type, direction, anchor_time)
);

create index if not exists idx_shadow_trades_open
  on public.shadow_pattern_trades (status, expiry_time) where status = 'open';
create index if not exists idx_shadow_trades_report
  on public.shadow_pattern_trades (source, symbol, created_at desc);

comment on table public.shadow_pattern_trades is
  'Formasyon (%60+ güven) + fakeout dedektör çağrılarının sızıntısız ileriye-dönük paper-trade doğrulaması. shadow_trade_tracker yazar/çözer; prediction_logs akışından izole.';

-- RLS: tablo varsayılan kilitli. Backend service-role anahtarıyla yazar
-- (service_role RLS'i bypass eder); anon/authenticated için politika YOK →
-- publishable key ile okuma/yazma kapalı. Panel veriyi backend API'sinden alır.
alter table public.shadow_pattern_trades enable row level security;
