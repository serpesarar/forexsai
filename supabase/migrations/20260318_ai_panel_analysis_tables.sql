create table if not exists public.ai_panel_prompt_versions (
    version text primary key,
    provider text not null,
    model text not null,
    prompt_template text not null,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.ai_panel_analysis_cache (
    symbol text primary key,
    analysis_version text not null,
    prompt_version text not null,
    provider text not null,
    model text not null,
    market_session text,
    market_open boolean not null default false,
    expires_at timestamptz not null,
    context_fingerprint text,
    context_summary jsonb not null default '{}'::jsonb,
    response_payload jsonb not null,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.ai_panel_analysis_history (
    id bigint generated always as identity primary key,
    symbol text not null,
    analysis_version text not null,
    prompt_version text not null,
    provider text not null,
    model text not null,
    cache_hit boolean not null default false,
    market_open boolean not null default false,
    market_session text,
    direction text,
    confidence numeric,
    event_risk_level text,
    context_fingerprint text,
    signal_snapshot jsonb not null default '{}'::jsonb,
    context_payload jsonb not null default '{}'::jsonb,
    response_payload jsonb not null,
    outcome_status text,
    outcome_score numeric,
    outcome_notes text,
    resolved_at timestamptz,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_ai_panel_analysis_cache_expires_at on public.ai_panel_analysis_cache (expires_at desc);
create index if not exists idx_ai_panel_analysis_cache_prompt_version on public.ai_panel_analysis_cache (prompt_version);
create index if not exists idx_ai_panel_analysis_history_symbol_created_at on public.ai_panel_analysis_history (symbol, created_at desc);
create index if not exists idx_ai_panel_analysis_history_prompt_version on public.ai_panel_analysis_history (prompt_version);
create index if not exists idx_ai_panel_analysis_history_context_fingerprint on public.ai_panel_analysis_history (context_fingerprint);
