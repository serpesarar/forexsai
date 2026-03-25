create table if not exists public.mapbox_usage_counters (
    metric_name text not null,
    period_type text not null,
    period_key text not null,
    usage_count bigint not null default 0,
    limit_count bigint not null default 0,
    updated_at timestamptz not null default now(),
    primary key (metric_name, period_type, period_key),
    constraint mapbox_usage_counters_period_type_check check (period_type in ('day', 'month'))
);

create table if not exists public.mapbox_usage_claims (
    metric_name text not null,
    period_key text not null,
    session_key text not null,
    claimed_at timestamptz not null default now(),
    primary key (metric_name, period_key, session_key)
);

create index if not exists idx_mapbox_usage_counters_updated_at on public.mapbox_usage_counters (updated_at desc);
create index if not exists idx_mapbox_usage_claims_claimed_at on public.mapbox_usage_claims (claimed_at desc);

alter table public.mapbox_usage_counters enable row level security;
alter table public.mapbox_usage_claims enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'mapbox_usage_counters' and policyname = 'mapbox_usage_counters_service_role_all'
    ) then
        create policy mapbox_usage_counters_service_role_all on public.mapbox_usage_counters for all to service_role using (true) with check (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'mapbox_usage_claims' and policyname = 'mapbox_usage_claims_service_role_all'
    ) then
        create policy mapbox_usage_claims_service_role_all on public.mapbox_usage_claims for all to service_role using (true) with check (true);
    end if;
end $$;

create or replace function public.claim_mapbox_web_load(
    p_metric_name text,
    p_month_key text,
    p_day_key text,
    p_month_limit bigint,
    p_day_limit bigint,
    p_session_key text default ''
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_month_used bigint := 0;
    v_day_used bigint := 0;
    v_reason text := 'within_budget';
    v_claimed boolean := false;
    v_allowed boolean := false;
    v_has_existing_claim boolean := false;
begin
    if coalesce(nullif(trim(p_session_key), ''), '') <> '' then
        select exists(
            select 1
            from public.mapbox_usage_claims
            where metric_name = p_metric_name
              and period_key = p_month_key
              and session_key = p_session_key
        ) into v_has_existing_claim;
    end if;

    insert into public.mapbox_usage_counters(metric_name, period_type, period_key, usage_count, limit_count)
    values (p_metric_name, 'month', p_month_key, 0, p_month_limit)
    on conflict (metric_name, period_type, period_key)
    do update set limit_count = excluded.limit_count, updated_at = now();

    insert into public.mapbox_usage_counters(metric_name, period_type, period_key, usage_count, limit_count)
    values (p_metric_name, 'day', p_day_key, 0, p_day_limit)
    on conflict (metric_name, period_type, period_key)
    do update set limit_count = excluded.limit_count, updated_at = now();

    select usage_count
    into v_month_used
    from public.mapbox_usage_counters
    where metric_name = p_metric_name
      and period_type = 'month'
      and period_key = p_month_key
    for update;

    select usage_count
    into v_day_used
    from public.mapbox_usage_counters
    where metric_name = p_metric_name
      and period_type = 'day'
      and period_key = p_day_key
    for update;

    if v_has_existing_claim then
        v_allowed := true;
        v_reason := 'already_claimed_session';
        return jsonb_build_object(
            'allowed', v_allowed,
            'claimed', v_claimed,
            'reason', v_reason,
            'month_used', v_month_used,
            'day_used', v_day_used
        );
    end if;

    if v_month_used >= p_month_limit then
        v_allowed := false;
        v_reason := 'monthly_cap_reached';
        return jsonb_build_object(
            'allowed', v_allowed,
            'claimed', v_claimed,
            'reason', v_reason,
            'month_used', v_month_used,
            'day_used', v_day_used
        );
    end if;

    if v_day_used >= p_day_limit then
        v_allowed := false;
        v_reason := 'daily_budget_exhausted';
        return jsonb_build_object(
            'allowed', v_allowed,
            'claimed', v_claimed,
            'reason', v_reason,
            'month_used', v_month_used,
            'day_used', v_day_used
        );
    end if;

    update public.mapbox_usage_counters
    set usage_count = usage_count + 1,
        limit_count = p_month_limit,
        updated_at = now()
    where metric_name = p_metric_name
      and period_type = 'month'
      and period_key = p_month_key;

    update public.mapbox_usage_counters
    set usage_count = usage_count + 1,
        limit_count = p_day_limit,
        updated_at = now()
    where metric_name = p_metric_name
      and period_type = 'day'
      and period_key = p_day_key;

    if coalesce(nullif(trim(p_session_key), ''), '') <> '' then
        insert into public.mapbox_usage_claims(metric_name, period_key, session_key)
        values (p_metric_name, p_month_key, p_session_key)
        on conflict do nothing;
    end if;

    select usage_count
    into v_month_used
    from public.mapbox_usage_counters
    where metric_name = p_metric_name
      and period_type = 'month'
      and period_key = p_month_key;

    select usage_count
    into v_day_used
    from public.mapbox_usage_counters
    where metric_name = p_metric_name
      and period_type = 'day'
      and period_key = p_day_key;

    v_allowed := true;
    v_claimed := true;
    return jsonb_build_object(
        'allowed', v_allowed,
        'claimed', v_claimed,
        'reason', v_reason,
        'month_used', v_month_used,
        'day_used', v_day_used
    );
end;
$$;

revoke all on function public.claim_mapbox_web_load(text, text, text, bigint, bigint, text) from public;
grant execute on function public.claim_mapbox_web_load(text, text, text, bigint, bigint, text) to service_role;
