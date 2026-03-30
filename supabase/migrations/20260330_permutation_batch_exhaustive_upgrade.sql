alter table if exists public.technical_permutation_batch_results
    add column if not exists profile_key text not null default 'lf5_tp0p3_sl0p3_wf0',
    add column if not exists train_occurrences integer not null default 0,
    add column if not exists train_wins integer not null default 0,
    add column if not exists train_win_rate double precision not null default 0,
    add column if not exists train_expectancy double precision not null default 0,
    add column if not exists validation_occurrences integer not null default 0,
    add column if not exists validation_wins integer not null default 0,
    add column if not exists validation_win_rate double precision not null default 0,
    add column if not exists validation_expectancy double precision not null default 0,
    add column if not exists walk_forward_splits integer not null default 0,
    add column if not exists walk_forward_passes integer not null default 0,
    add column if not exists walk_forward_folds integer not null default 0;

do $$
begin
    if exists (
        select 1
        from pg_constraint
        where conname = 'technical_permutation_batch_results_pkey'
          and conrelid = 'public.technical_permutation_batch_results'::regclass
    ) then
        alter table public.technical_permutation_batch_results
            drop constraint technical_permutation_batch_results_pkey;
    end if;
end $$;

alter table public.technical_permutation_batch_results
    add constraint technical_permutation_batch_results_pkey
    primary key (run_id, symbol, direction, timeframe, profile_key, rule_key);

create index if not exists idx_technical_permutation_batch_results_profile_lookup
    on public.technical_permutation_batch_results(symbol, direction, timeframe, profile_key, run_id);
