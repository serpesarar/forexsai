-- Çok kaynaklı haber beslemesi (2026-11-05). Yazar: backend/services/newsfeed (service-role, tek yazar).
-- RLS açık, anon politikası YOK: erişim yalnız backend API (/api/newsfeed) üzerinden.
-- Saklama: engine NEWSFEED_RETENTION_DAYS (varsayılan 90 gün) sonra siler; yalnız ilgi puanı ≥ 50 hikâyeler yazılır.
create table if not exists public.news_stories (
    id            text primary key,
    headline      text not null,
    url           text,
    first_seen_at timestamptz not null,
    first_source  text not null,
    tier          text,
    event_type    text,
    symbols       text[] not null default '{}',
    urgency       text,
    relevance     integer,
    confirmation  text,
    is_opinion    boolean not null default false,
    n_sources     integer not null default 1,
    published_at  timestamptz,
    seeded        boolean not null default false,
    created_at    timestamptz not null default now()
);
create index if not exists news_stories_seen_idx on public.news_stories (first_seen_at desc);
create index if not exists news_stories_symbols_idx on public.news_stories using gin (symbols);

-- Kaynak başına ilk görülme: hız yarışının ham verisi. Yarış ölçümü seeded = false satırlardan yapılır.
create table if not exists public.news_sightings (
    story_id        text not null references public.news_stories(id) on delete cascade,
    source_id       text not null,
    first_seen_at   timestamptz not null,
    published_at    timestamptz,
    lag_s           real,
    poll_interval_s real,
    seeded          boolean not null default false,
    primary key (story_id, source_id)
);
create index if not exists news_sightings_source_seen_idx on public.news_sightings (source_id, first_seen_at desc);

alter table public.news_stories enable row level security;
alter table public.news_sightings enable row level security;
