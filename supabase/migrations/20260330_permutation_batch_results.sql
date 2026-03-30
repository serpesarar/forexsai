create extension if not exists pgcrypto;

create table if not exists public.permutation_batch_runs (
    id uuid primary key,
    batch_kind text not null check (batch_kind in ('model', 'technical', 'full')),
    status text not null default 'running' check (status in ('running', 'completed', 'failed')),
    symbols jsonb not null default '[]'::jsonb,
    directions jsonb not null default '[]'::jsonb,
    timeframes jsonb not null default '[]'::jsonb,
    parameters jsonb not null default '{}'::jsonb,
    summary jsonb not null default '{}'::jsonb,
    error text,
    started_at timestamptz not null default now(),
    completed_at timestamptz
);

create index if not exists idx_permutation_batch_runs_status on public.permutation_batch_runs(status);
create index if not exists idx_permutation_batch_runs_started_at on public.permutation_batch_runs(started_at desc);

create table if not exists public.model_permutation_batch_results (
    run_id uuid not null references public.permutation_batch_runs(id) on delete cascade,
    symbol text not null,
    direction text not null,
    combination text not null,
    total_signals integer not null default 0,
    wins integer not null default 0,
    losses integer not null default 0,
    win_rate double precision not null default 0,
    profit_factor double precision not null default 0,
    expectancy double precision not null default 0,
    avg_member_alignment double precision,
    unanimous_win_rate double precision,
    lookback_days integer,
    cluster_window_minutes integer,
    insufficient_data boolean not null default false,
    rank integer,
    created_at timestamptz not null default now(),
    primary key (run_id, symbol, direction, combination)
);

create index if not exists idx_model_permutation_batch_results_lookup on public.model_permutation_batch_results(symbol, direction, run_id);
create index if not exists idx_model_permutation_batch_results_rank on public.model_permutation_batch_results(run_id, rank);

create table if not exists public.technical_permutation_batch_results (
    run_id uuid not null references public.permutation_batch_runs(id) on delete cascade,
    symbol text not null,
    direction text not null,
    timeframe text not null,
    rule_key text not null,
    combination_size integer not null,
    rule_definition jsonb not null default '[]'::jsonb,
    occurrences integer not null default 0,
    wins integer not null default 0,
    losses integer not null default 0,
    win_rate double precision not null default 0,
    profit_factor double precision not null default 0,
    expectancy double precision not null default 0,
    avg_forward_return double precision,
    target_move_pct double precision,
    stop_move_pct double precision,
    lookforward_candles integer,
    threshold_quantiles jsonb not null default '[]'::jsonb,
    insufficient_data boolean not null default false,
    rank integer,
    created_at timestamptz not null default now(),
    primary key (run_id, symbol, direction, timeframe, rule_key)
);

create index if not exists idx_technical_permutation_batch_results_lookup on public.technical_permutation_batch_results(symbol, direction, timeframe, run_id);
create index if not exists idx_technical_permutation_batch_results_rank on public.technical_permutation_batch_results(run_id, rank);
