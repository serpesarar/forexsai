create table if not exists public.tanker_positions (
    id bigserial primary key,
    mmsi bigint not null,
    imo bigint,
    vessel_name text,
    ship_type_code integer,
    ship_category text,
    lat double precision not null,
    lon double precision not null,
    speed_knots double precision,
    heading double precision,
    draught_meters double precision,
    destination text,
    nav_status text,
    region text not null default 'transit',
    status text not null default 'transit',
    idle_days numeric(10,2) not null default 0,
    is_dark boolean not null default false,
    estimated_barrels bigint,
    observed_at timestamptz not null,
    data_source text not null default 'aisstream',
    raw_payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (mmsi, observed_at)
);

create table if not exists public.tanker_state (
    mmsi bigint primary key,
    imo bigint,
    vessel_name text,
    ship_type_code integer,
    ship_category text,
    region text not null default 'transit',
    status text not null default 'transit',
    lat double precision,
    lon double precision,
    speed_knots double precision,
    heading double precision,
    draught_meters double precision,
    destination text,
    nav_status text,
    estimated_barrels bigint,
    first_seen_at timestamptz,
    first_stationary_at timestamptz,
    last_movement_at timestamptz,
    last_seen_at timestamptz not null default now(),
    idle_days numeric(10,2) not null default 0,
    is_dark boolean not null default false,
    movement_bias text not null default 'neutral',
    meta jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create table if not exists public.chokepoint_metrics (
    region text primary key,
    vessel_count integer not null default 0,
    floating_storage_vessels integer not null default 0,
    anchored_vessels integer not null default 0,
    inbound_vessels integer not null default 0,
    outbound_vessels integer not null default 0,
    avg_speed numeric(10,2) not null default 0,
    congestion_score numeric(10,2) not null default 0,
    storage_estimate_mm_bbl numeric(12,2) not null default 0,
    pressure_bias text not null default 'neutral',
    signal text not null default 'watch',
    source text not null default 'aisstream',
    meta jsonb not null default '{}'::jsonb,
    last_updated timestamptz not null default now()
);

create table if not exists public.baltic_index_cache (
    index_type text primary key,
    value numeric(14,2),
    change_day numeric(14,2),
    change_percent numeric(10,2),
    as_of_date date,
    source text not null,
    status text not null default 'stale',
    note text,
    raw_payload jsonb not null default '{}'::jsonb,
    fetched_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_tanker_positions_region_observed_at on public.tanker_positions (region, observed_at desc);
create index if not exists idx_tanker_positions_status_observed_at on public.tanker_positions (status, observed_at desc);
create index if not exists idx_tanker_state_region_status on public.tanker_state (region, status);
create index if not exists idx_chokepoint_metrics_last_updated on public.chokepoint_metrics (last_updated desc);
create index if not exists idx_baltic_index_cache_fetched_at on public.baltic_index_cache (fetched_at desc);

alter table public.tanker_positions enable row level security;
alter table public.tanker_state enable row level security;
alter table public.chokepoint_metrics enable row level security;
alter table public.baltic_index_cache enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_positions' and policyname = 'tanker_positions_read_authenticated'
    ) then
        create policy tanker_positions_read_authenticated on public.tanker_positions for select to authenticated using (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_state' and policyname = 'tanker_state_read_authenticated'
    ) then
        create policy tanker_state_read_authenticated on public.tanker_state for select to authenticated using (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'chokepoint_metrics' and policyname = 'chokepoint_metrics_read_public'
    ) then
        create policy chokepoint_metrics_read_public on public.chokepoint_metrics for select to anon, authenticated using (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'baltic_index_cache' and policyname = 'baltic_index_cache_read_public'
    ) then
        create policy baltic_index_cache_read_public on public.baltic_index_cache for select to anon, authenticated using (true);
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_publication_tables
        where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'chokepoint_metrics'
    ) then
        alter publication supabase_realtime add table public.chokepoint_metrics;
    end if;
    if not exists (
        select 1
        from pg_publication_tables
        where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'baltic_index_cache'
    ) then
        alter publication supabase_realtime add table public.baltic_index_cache;
    end if;
end $$;
