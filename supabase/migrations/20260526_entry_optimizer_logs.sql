-- Entry Optimizer — sinyal-bazlı karar ve outcome logger.
--
-- Her sinyalde Entry Optimizer'ın kararını (action, entry/sl/tp, structure,
-- priority) + market context (ATR, ADX, regime) loglar. Trade kapandığında
-- outcome_backfill ile gerçekleşen sonuç + eski sistemin karşılaştırması
-- doldurulur. A/B mode için kritik veri.
--
-- Shadow mode: enforce_mode=false → optimizer kararı sadece LOGLANIR,
-- gerçek trade eski entry/sl/tp ile yapılır. Enforce'a geçince true olur.

CREATE TABLE IF NOT EXISTS public.entry_optimizer_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- İlişkilendirme — sinyalin prediction_logs ID'si (insert öncesi log ise null)
    prediction_id UUID,
    signal_model TEXT,                 -- emel/pulse2/ml/...

    -- Sinyal bağlamı
    symbol TEXT NOT NULL,
    signal_direction TEXT NOT NULL CHECK (signal_direction IN ('BUY', 'SELL')),
    current_price NUMERIC NOT NULL,
    signal_confidence NUMERIC,

    -- Optimizer kararı
    optimizer_action TEXT NOT NULL CHECK (optimizer_action IN
        ('EXECUTE_NOW', 'LIMIT_ORDER', 'FALLBACK_MARKET', 'PASSTHROUGH')),
    optimizer_entry NUMERIC NOT NULL,
    optimizer_sl NUMERIC NOT NULL,
    optimizer_tp NUMERIC NOT NULL,
    optimizer_priority INT NOT NULL,
    max_wait_candles INT,
    structure_type TEXT,                -- bullish_order_block/bearish_fvg/none
    invalidation_reason TEXT,

    -- Stage 4 sizing (ortogonal)
    stage4_sizing_mult NUMERIC,
    stage4_predicted_r NUMERIC,

    -- Market context (regime / volatility)
    atr_14 NUMERIC,
    atr_50 NUMERIC,
    atr_ratio NUMERIC,                  -- atr_14 / atr_50 — >1.3 = high vol
    adx_14 NUMERIC,
    regime TEXT,                        -- TRENDING_UP/DOWN, RANGING, TRANSITION
    regime_efficiency NUMERIC,

    -- Outcome — backfill: trade kapanınca doldurulur
    optimizer_outcome TEXT CHECK (optimizer_outcome IS NULL OR
        optimizer_outcome IN ('completed', 'stopped', 'expired', 'limit_missed', 'pending')),
    optimizer_exit_price NUMERIC,
    optimizer_realized_pips NUMERIC,
    optimizer_resolved_at TIMESTAMPTZ,

    -- A/B karşılaştırma — eski sistemin (mevcut config) outcome'u
    market_outcome TEXT,
    market_exit_price NUMERIC,
    market_realized_pips NUMERIC,

    -- Mod bilgisi
    enforce_mode BOOLEAN NOT NULL DEFAULT false,   -- false=shadow, true=enforce
    notes JSONB
);

-- Performans index'leri
CREATE INDEX IF NOT EXISTS idx_eol_symbol_created ON
    public.entry_optimizer_logs (symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eol_prediction ON
    public.entry_optimizer_logs (prediction_id)
    WHERE prediction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_eol_action_outcome ON
    public.entry_optimizer_logs (optimizer_action, optimizer_outcome);
CREATE INDEX IF NOT EXISTS idx_eol_unresolved ON
    public.entry_optimizer_logs (created_at DESC)
    WHERE optimizer_outcome IS NULL OR optimizer_outcome = 'pending';

-- RLS: kapalı (service role ile yazılır/okunur)
ALTER TABLE public.entry_optimizer_logs ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.entry_optimizer_logs IS
    'Entry Optimizer kararlari + market context + A/B outcome. '
    'Shadow mode gozlem, sonra enforce karsilastirmasi.';
