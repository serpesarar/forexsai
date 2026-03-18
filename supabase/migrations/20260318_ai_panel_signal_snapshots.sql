alter table public.prediction_logs
  drop constraint if exists prediction_logs_model_type_check;

alter table public.prediction_logs
  add constraint prediction_logs_model_type_check
  check (
    model_type = any (
      array[
        'ml',
        'ml:main',
        'ml:ultra_safe',
        'ml:balanced',
        'ml:full_power',
        'ml:aggressive',
        'ml:nasdaq_precision',
        'ai_panel',
        'pulse',
        'pulse1',
        'pulse2',
        'pulse3',
        'emel',
        'emel_inverse',
        'smc',
        'hybrid'
      ]
    )
  );

create table if not exists public.ai_panel_signal_snapshots (
    id bigint generated always as identity primary key,
    symbol text not null,
    timeframe text not null default '1h',
    source text not null default 'hourly_scheduler',
    direction text not null,
    confidence double precision not null default 0,
    market_session text,
    market_open boolean not null default false,
    event_risk_level text,
    analysis_model text,
    prompt_version text,
    analysis_generated_at timestamptz,
    actionability text not null default 'standby',
    prediction_log_id uuid references public.prediction_logs(id) on delete set null,
    signal_payload jsonb not null default '{}'::jsonb,
    response_payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_prediction_logs_model_type_created_at
    on public.prediction_logs (model_type, created_at desc);

create index if not exists idx_ai_panel_signal_snapshots_symbol_created_at
    on public.ai_panel_signal_snapshots (symbol, created_at desc);

create index if not exists idx_ai_panel_signal_snapshots_prediction_log_id
    on public.ai_panel_signal_snapshots (prediction_log_id);

create index if not exists idx_ai_panel_signal_snapshots_actionability
    on public.ai_panel_signal_snapshots (actionability, created_at desc);
