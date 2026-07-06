-- indicator_snapshots: her kapalı mum için tam indicator seti (data_recorder.py yazar)
-- Bir kez Supabase SQL editöründe çalıştır (MCP read-only olduğu için elle uygula).
CREATE TABLE IF NOT EXISTS indicator_snapshots (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  symbol      TEXT NOT NULL,
  timeframe   TEXT NOT NULL,
  candle_time TIMESTAMPTZ NOT NULL,
  open        DOUBLE PRECISION,
  high        DOUBLE PRECISION,
  low         DOUBLE PRECISION,
  close       DOUBLE PRECISION,
  volume      DOUBLE PRECISION,
  ind         JSONB NOT NULL,          -- tüm indicator değerleri (esnek)
  created_at  TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT indicator_snapshots_uniq UNIQUE (symbol, timeframe, candle_time)
);

CREATE INDEX IF NOT EXISTS idx_indsnap_sym_tf_time
  ON indicator_snapshots (symbol, timeframe, candle_time DESC);

-- JSONB içinde indicator'a göre sorgu için (ör. ind->>'rsi14')
CREATE INDEX IF NOT EXISTS idx_indsnap_ind_gin
  ON indicator_snapshots USING GIN (ind);

COMMENT ON TABLE indicator_snapshots IS
  'Her kapalı mum için tam indicator seti. data_recorder.py (MT5 kutusu) yazar.';
