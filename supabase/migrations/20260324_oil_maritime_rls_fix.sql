do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_positions' and policyname = 'tanker_positions_read_public'
    ) then
        create policy tanker_positions_read_public on public.tanker_positions for select to anon, authenticated using (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_positions' and policyname = 'anon_insert_tanker_positions'
    ) then
        create policy anon_insert_tanker_positions on public.tanker_positions for insert to anon with check (auth.role() = 'anon');
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_state' and policyname = 'tanker_state_read_public'
    ) then
        create policy tanker_state_read_public on public.tanker_state for select to anon, authenticated using (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_state' and policyname = 'anon_insert_tanker_state'
    ) then
        create policy anon_insert_tanker_state on public.tanker_state for insert to anon with check (auth.role() = 'anon');
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'tanker_state' and policyname = 'anon_update_tanker_state'
    ) then
        create policy anon_update_tanker_state on public.tanker_state for update to anon using (auth.role() = 'anon') with check (auth.role() = 'anon');
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'chokepoint_metrics' and policyname = 'anon_insert_chokepoint_metrics'
    ) then
        create policy anon_insert_chokepoint_metrics on public.chokepoint_metrics for insert to anon with check (auth.role() = 'anon');
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'chokepoint_metrics' and policyname = 'anon_update_chokepoint_metrics'
    ) then
        create policy anon_update_chokepoint_metrics on public.chokepoint_metrics for update to anon using (auth.role() = 'anon') with check (auth.role() = 'anon');
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'baltic_index_cache' and policyname = 'anon_insert_baltic_index_cache'
    ) then
        create policy anon_insert_baltic_index_cache on public.baltic_index_cache for insert to anon with check (auth.role() = 'anon');
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'baltic_index_cache' and policyname = 'anon_update_baltic_index_cache'
    ) then
        create policy anon_update_baltic_index_cache on public.baltic_index_cache for update to anon using (auth.role() = 'anon') with check (auth.role() = 'anon');
    end if;
end $$;
