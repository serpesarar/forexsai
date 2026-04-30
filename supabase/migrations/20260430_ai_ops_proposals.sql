-- AI-Ops infrastructure: failure clusters + DeepSeek improvement proposals.
-- Layer 1 (programmatic tagger) writes to existing failure_analyses (already exists).
-- Layer 2 (DeepSeek orchestrator) writes to these new tables.

-- Ensure failure_analyses can be upserted by prediction_id (idempotent re-tagging).
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'failure_analyses_prediction_id_unique'
  ) THEN
    ALTER TABLE failure_analyses
      ADD CONSTRAINT failure_analyses_prediction_id_unique UNIQUE (prediction_id);
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS failure_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- What kind of cluster
    symbol VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    direction VARCHAR(10),                  -- BUY / SELL / null=mixed
    -- Group-by signature (tag combination that defines this cluster)
    cluster_signature TEXT NOT NULL,         -- e.g. "regime=ranging|near_resistance=true|rsi_extreme=true"
    common_tags JSONB,                       -- e.g. ["RSI_OVERBOUGHT_BUY","BUY_INTO_RESISTANCE"]
    -- Stats
    sample_size INT NOT NULL,                -- # signals in this cluster
    win_rate NUMERIC(5,2),                   -- 0-100, of resolved
    total_pnl_pips NUMERIC(10,2),            -- summed P/L
    avg_confidence NUMERIC(5,2),
    representative_prediction_ids UUID[],    -- sample 10-20 IDs for inspection
    -- Window
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    -- Status
    sent_to_llm BOOLEAN DEFAULT FALSE,
    proposal_id UUID,                        -- FK to improvement_proposals if LLM was called
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_failure_clusters_symbol_model ON failure_clusters(symbol, model_type);
CREATE INDEX IF NOT EXISTS idx_failure_clusters_window ON failure_clusters(window_end DESC);
CREATE INDEX IF NOT EXISTS idx_failure_clusters_pending ON failure_clusters(sent_to_llm) WHERE sent_to_llm = FALSE;


CREATE TABLE IF NOT EXISTS improvement_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID REFERENCES failure_clusters(id),
    -- Trigger context
    symbol VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),                    -- critical / high / medium / low
    -- LLM analysis
    llm_model VARCHAR(50),                   -- e.g. deepseek-reasoner
    root_cause TEXT,                         -- human-readable hypothesis
    proposed_fixes JSONB,                    -- list of {type, description, implementation_hint, estimated_impact, risk}
    alternative_explanations JSONB,
    requires_data TEXT,
    raw_llm_response TEXT,                   -- for audit
    -- Workflow
    status VARCHAR(30) DEFAULT 'pending',    -- pending / reviewed / approved / rejected / implemented / rolled_back
    reviewed_by VARCHAR(120),
    reviewed_at TIMESTAMPTZ,
    pr_url TEXT,                             -- GitHub PR if implementation auto-opened one
    -- Outcome tracking
    pre_change_metric JSONB,                 -- snapshot of relevant KPIs before change
    post_change_metric JSONB,                -- after deploy
    rollback_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_improvement_proposals_status ON improvement_proposals(status);
CREATE INDEX IF NOT EXISTS idx_improvement_proposals_symbol_model ON improvement_proposals(symbol, model_type);
CREATE INDEX IF NOT EXISTS idx_improvement_proposals_created ON improvement_proposals(created_at DESC);

ALTER TABLE failure_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE improvement_proposals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on failure_clusters" ON failure_clusters
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "Allow service role full access on improvement_proposals" ON improvement_proposals
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE failure_clusters IS 'Groups of similar failed signals — input to LLM-based root cause analysis.';
COMMENT ON TABLE improvement_proposals IS 'DeepSeek-generated improvement suggestions awaiting human review.';
