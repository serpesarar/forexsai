drop index if exists public.idx_prediction_logs_active_dedup;

create unique index if not exists idx_prediction_logs_active_dedup
    on public.prediction_logs (symbol, model_type, ml_direction)
    where status = 'active' and model_type not in ('smc', 'meta');

create unique index if not exists idx_prediction_logs_active_smc_dedup
    on public.prediction_logs (symbol, model_type, timeframe, ml_direction)
    where status = 'active' and model_type = 'smc';

create index if not exists idx_prediction_logs_active_meta_timeframe
    on public.prediction_logs (symbol, model_type, timeframe, created_at desc)
    where status = 'active' and model_type = 'meta';
