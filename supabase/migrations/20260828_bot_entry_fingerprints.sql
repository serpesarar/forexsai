-- Bot giriş "parmak izi" köprüsü (2026-08-28)
--
-- yeni deneme/forexsai_demo_bot.py::record_fingerprint() her MOM/SR girişinde
-- entry_fingerprints.jsonl'e giriş bağlamını (voters, mom_stretch/threshold,
-- backend confidence, session, rr...) yazar — sl_forensics.py bunu şimdiye
-- kadar yalnız kutuda offline analiz için okuyordu. Bu tablo aynı veriyi
-- panele taşır: "bu işlem HANGİ KURALA göre açıldı" sorusunun cevabı.
--
-- Kapsam notu: yalnız MAGIC_NUMBER (base, momentum/SR) scope'u fingerprint
-- yazıyor — CHREV/VIXREG/DAYCOMBO/USOIL_BREAKOUT/reflex/reentry için bu
-- tabloda satır OLMAYACAK (backend bunu ticket eşleşmemesiyle ayırt eder,
-- magic-numaralı strateji-ailesi etiketine düşer). Bkz. backend/services/
-- evolution_remote.py::MAGIC_STRATEGY_MAP.
--
-- ticket = bot_trades.raw->>'position_id' ile eşleşir (MT5'te taze piyasa
-- emrinde result.order == pozisyon ticket'ı).

create table if not exists bot_entry_fingerprints (
  ticket bigint primary key,
  host text not null default 'mt5_box',
  ts timestamptz,
  scope text,
  symbol text,
  mt5_symbol text,
  direction text,
  entry double precision,
  tp double precision,
  sl double precision,
  lot double precision,
  rr double precision,
  entry_type text,
  tp_source text,
  voters jsonb default '[]'::jsonb,
  raw jsonb not null default '{}'::jsonb,
  inserted_at timestamptz not null default now()
);
create index if not exists idx_bot_fp_symbol on bot_entry_fingerprints (symbol, ts desc);

alter table bot_entry_fingerprints enable row level security;
-- Bilinçli olarak politika YOK — bot_trades/decider_journal ile aynı kalıp:
-- yalnız service-role (backend + ajan) okur/yazar, anon/authenticated'a kapalı.
