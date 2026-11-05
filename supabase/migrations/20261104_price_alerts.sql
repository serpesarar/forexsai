-- Fiyat alarmları (day-trader-skill trader-alerts karşılığı, 2026-11-04).
-- Yazar: backend/services/price_alert_service.py (service-role). RLS açık, anon politikası YOK:
-- erişim yalnız backend API (/api/alerts, require_admin) üzerinden.
-- stop/target: seviye ref_price'ın (kurulum anı fiyatı) KARŞI tarafına geçince tetiklenir — yönü ref belirler.
create table if not exists public.price_alerts (
    id               bigserial primary key,
    symbol           text        not null,
    kind             text        not null check (kind in ('above','below','pct_move','time','stop','target')),
    price            double precision,
    pct              double precision,
    ref_price        double precision,
    at_utc           timestamptz,
    label            text,
    source           text        not null default 'manual' check (source in ('manual','plan','signal')),
    status           text        not null default 'active' check (status in ('active','triggered','disabled')),
    one_shot         boolean     not null default true,
    notify_telegram  boolean     not null default true,
    created_at       timestamptz not null default now(),
    triggered_at     timestamptz,
    triggered_price  double precision,
    constraint price_alerts_kind_fields check (
        (kind in ('above','below') and price is not null)
        or (kind in ('stop','target') and price is not null and ref_price is not null)
        or (kind = 'pct_move' and pct is not null and pct > 0 and ref_price is not null)
        or (kind = 'time' and at_utc is not null)
    )
);

create index if not exists price_alerts_status_symbol_idx on public.price_alerts (status, symbol);

alter table public.price_alerts enable row level security;
