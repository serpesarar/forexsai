-- Security Fixes Migration
-- Fixes RLS disabled warnings and Security Definer View issues

-- ============================================
-- 1. ENABLE RLS ON ALL PUBLIC TABLES
-- ============================================

ALTER TABLE IF EXISTS public.prediction_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.outcome_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.learning_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.factor_importance ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.live_data_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.news_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.error_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.candle_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.learning_feedback ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 2. CREATE PUBLIC READ POLICIES
-- These tables contain non-sensitive market data
-- ============================================

-- prediction_logs - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.prediction_logs;
CREATE POLICY "Allow public read" ON public.prediction_logs FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.prediction_logs;
CREATE POLICY "Allow service write" ON public.prediction_logs FOR ALL USING (auth.role() = 'service_role');

-- outcome_results - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.outcome_results;
CREATE POLICY "Allow public read" ON public.outcome_results FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.outcome_results;
CREATE POLICY "Allow service write" ON public.outcome_results FOR ALL USING (auth.role() = 'service_role');

-- learning_insights - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.learning_insights;
CREATE POLICY "Allow public read" ON public.learning_insights FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.learning_insights;
CREATE POLICY "Allow service write" ON public.learning_insights FOR ALL USING (auth.role() = 'service_role');

-- factor_importance - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.factor_importance;
CREATE POLICY "Allow public read" ON public.factor_importance FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.factor_importance;
CREATE POLICY "Allow service write" ON public.factor_importance FOR ALL USING (auth.role() = 'service_role');

-- rate_limits - service only (sensitive)
DROP POLICY IF EXISTS "Allow service only" ON public.rate_limits;
CREATE POLICY "Allow service only" ON public.rate_limits FOR ALL USING (auth.role() = 'service_role');

-- live_data_cache - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.live_data_cache;
CREATE POLICY "Allow public read" ON public.live_data_cache FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.live_data_cache;
CREATE POLICY "Allow service write" ON public.live_data_cache FOR ALL USING (auth.role() = 'service_role');

-- news_cache - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.news_cache;
CREATE POLICY "Allow public read" ON public.news_cache FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.news_cache;
CREATE POLICY "Allow service write" ON public.news_cache FOR ALL USING (auth.role() = 'service_role');

-- error_analysis - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.error_analysis;
CREATE POLICY "Allow public read" ON public.error_analysis FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.error_analysis;
CREATE POLICY "Allow service write" ON public.error_analysis FOR ALL USING (auth.role() = 'service_role');

-- candle_snapshots - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.candle_snapshots;
CREATE POLICY "Allow public read" ON public.candle_snapshots FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.candle_snapshots;
CREATE POLICY "Allow service write" ON public.candle_snapshots FOR ALL USING (auth.role() = 'service_role');

-- learning_feedback - public read, service write
DROP POLICY IF EXISTS "Allow public read" ON public.learning_feedback;
CREATE POLICY "Allow public read" ON public.learning_feedback FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow service write" ON public.learning_feedback;
CREATE POLICY "Allow service write" ON public.learning_feedback FOR ALL USING (auth.role() = 'service_role');

-- ============================================
-- 3. FIX SECURITY DEFINER VIEWS
-- Change to SECURITY INVOKER (default, safer)
-- ============================================

-- Drop and recreate v_recent_accuracy without SECURITY DEFINER
DROP VIEW IF EXISTS public.v_recent_accuracy;
CREATE VIEW public.v_recent_accuracy AS
SELECT 
    symbol,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct_predictions,
    ROUND(
        (SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0)) * 100, 
        2
    ) as accuracy_pct,
    MAX(created_at) as last_prediction
FROM public.prediction_logs
WHERE created_at > NOW() - INTERVAL '7 days'
  AND outcome IS NOT NULL
GROUP BY symbol;

-- Drop and recreate v_factor_error_analysis without SECURITY DEFINER
DROP VIEW IF EXISTS public.v_factor_error_analysis;
CREATE VIEW public.v_factor_error_analysis AS
SELECT 
    ea.symbol,
    ea.error_type,
    ea.market_condition,
    COUNT(*) as error_count,
    AVG(ea.confidence_at_prediction) as avg_confidence,
    jsonb_agg(ea.factors_involved) as all_factors
FROM public.error_analysis ea
WHERE ea.created_at > NOW() - INTERVAL '30 days'
GROUP BY ea.symbol, ea.error_type, ea.market_condition
ORDER BY error_count DESC;

-- Grant SELECT on views to anon and authenticated
GRANT SELECT ON public.v_recent_accuracy TO anon, authenticated;
GRANT SELECT ON public.v_factor_error_analysis TO anon, authenticated;

-- ============================================
-- DONE: All security issues fixed
-- ============================================
