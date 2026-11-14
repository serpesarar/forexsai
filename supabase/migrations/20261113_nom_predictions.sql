-- NOM (NASDAQ Olasılık Motoru) gölge tahmin kaydı + canlı kalibrasyon (research/nom_20261113, Faz 8)
-- Tahmin karar anında yazılır (sonuç bilinmeden); sonuç ufuk dolunca AYNI satıra yazılır.
-- prediction_logs / signal_lifecycle'dan tamamen izole. Service-role yazar; anon politikası YOK.
create table if not exists public.nom_predictions (
    id               bigserial primary key,
    created_at       timestamptz not null default now(),
    t_dec            timestamptz not null,              -- karar anı (son kapanmış 1m bar kapanışı)
    horizon          text        not null,              -- 15m | 1h | 4h | session
    geometry         text        not null,              -- TPxSL (ATR), ör. 1.5x1
    model_version    text        not null,
    price            double precision,
    atr              double precision,                  -- ufkun ATR birimi (puan)
    t_end            timestamptz,                       -- ufuk sonu
    p_long_tp        real, p_long_sl real, p_long_to real, exp_r_long real,
    p_short_tp       real, p_short_sl real, p_short_to real, exp_r_short real,
    status           text,                              -- LONG | SHORT | NÖTR / belirsiz
    feature_summary  jsonb,                             -- en etkili 5 faktör + bağlam özeti
    source           text default 'shadow',
    outcome_long_cls  smallint,                         -- 0 TP · 1 SL · 2 zaman aşımı · -1 çözülemedi
    outcome_long_r    real,
    outcome_short_cls smallint,
    outcome_short_r   real,
    outcome_filled_at timestamptz,
    constraint nom_predictions_uniq unique (t_dec, horizon, geometry, model_version)
);
create index if not exists nom_predictions_hg_t on public.nom_predictions (horizon, geometry, t_dec desc);
create index if not exists nom_predictions_pending on public.nom_predictions (t_end) where outcome_filled_at is null;
alter table public.nom_predictions enable row level security;
comment on table public.nom_predictions is 'NOM gölge tahminleri + gerçekleşen sonuç (canlı kalibrasyon). Karar desteği; emir açmaz.';
