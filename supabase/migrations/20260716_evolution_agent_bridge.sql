-- Evrim Ajanı köprüsü: MT5 kutusu ↔ panel çift yönlü senkron (2026-07-16)
-- Uygulandı: mcp apply_migration "evolution_agent_bridge" (proje xdmtbykebfpqutfgdfqs)

create table if not exists agent_heartbeat (
  host text primary key,
  last_seen timestamptz not null default now(),
  meta jsonb not null default '{}'::jsonb
);

create table if not exists bot_trades (
  ticket bigint primary key,
  host text not null default 'mt5_box',
  symbol text not null,
  direction text not null,
  volume double precision,
  open_time timestamptz,
  close_time timestamptz not null,
  open_price double precision,
  close_price double precision,
  sl double precision,
  tp double precision,
  profit double precision not null default 0,
  commission double precision default 0,
  swap double precision default 0,
  comment text,
  magic bigint,
  raw jsonb,
  inserted_at timestamptz not null default now()
);
create index if not exists idx_bot_trades_close_time on bot_trades (close_time desc);
create index if not exists idx_bot_trades_symbol on bot_trades (symbol, close_time desc);

create table if not exists decider_journal (
  id text primary key,
  host text not null default 'mt5_box',
  ts timestamptz,
  symbol text,
  decision text,
  confidence double precision,
  outcome jsonb,
  raw jsonb not null,
  inserted_at timestamptz not null default now()
);
create index if not exists idx_decider_journal_ts on decider_journal (ts desc);

create table if not exists evolution_commands (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  host text not null default 'mt5_box',
  kind text not null,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'pending',
  started_at timestamptz,
  finished_at timestamptz,
  output text,
  return_code integer,
  requested_by text default 'panel',
  analysis_id text,
  analysis_name text
);
create index if not exists idx_evo_commands_poll on evolution_commands (host, status, created_at);
create index if not exists idx_evo_commands_created on evolution_commands (created_at desc);
