-- Reflex Engine signals: honest mom_cont + 15min time-stop system (NDX).
-- Isolated from prediction_logs/signal_lifecycle. Written by reflex_engine_service,
-- resolved by its own time-stop resolver, read by the panel + MT5 bot.
create table if not exists public.reflex_signals (
  id             bigint generated always as identity primary key,
  symbol         text not null default 'NDX.INDX',
  event_time     timestamptz not null,            -- confirm bar close (detection)
  entry_time     timestamptz,                     -- actual fill time
  direction      text not null check (direction in ('BUY','SELL')),
  family         text not null default 'mom_cont',
  regime         text,                            -- TREND/CHOP/EXPANSION/CONTRACTION
  entry_price    double precision,
  sl_price       double precision,                -- catastrophic backstop (1.5xATR)
  exit_deadline  timestamptz not null,            -- entry_time + 15 min (time-stop)
  status         text not null default 'active',  -- active|closed_win|closed_loss|closed_flat|error
  exit_time      timestamptz,
  exit_price     double precision,
  r_multiple     double precision,                -- pnl / (sl distance)
  pnl_points     double precision,
  atr            double precision,
  stretch        double precision,                -- 15m momentum stretch at trigger
  p_confidence   double precision,                -- calibrated confidence (display only)
  mode           text not null default 'shadow' check (mode in ('shadow','live')),
  explanation    jsonb,
  mt5_ticket     bigint,                          -- broker ticket if executed live
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique (symbol, event_time, direction)
);
create index if not exists idx_reflex_signals_status on public.reflex_signals (status, exit_deadline);
create index if not exists idx_reflex_signals_time on public.reflex_signals (symbol, event_time desc);

comment on table public.reflex_signals is
  'NDX Reflex Engine (mom_cont + 15min time-stop). Leak-free momentum-continuation signals; shadow by default, live-gated. Resolved by reflex_engine_service time-stop resolver, not signal_lifecycle.';
