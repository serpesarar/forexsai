-- ============================================================================
-- Enable Row-Level Security on all public tables
-- 2026-06-02 — Supabase güvenlik uyarısı: rls_disabled_in_public
--
-- Backend SUPABASE_SERVICE_KEY ile çalışır (service_role rolü RLS'i bypass eder).
-- Bu yüzden backend etkilenmez. Sadece anon/authenticated rolleri kısıtlanır.
--
-- Eğer ileride frontend doğrudan Supabase'e (anon key) yazacaksa, her tablo için
-- özel policy eklenmelidir. Şu an default: anon ve authenticated ERİŞEMEZ.
-- ============================================================================

DO $$
DECLARE
    t text;
    tables text[] := ARRAY[
        'ai_panel_analysis_cache',
        'ai_panel_analysis_history',
        'ai_panel_prompt_versions',
        'ai_panel_signal_snapshots',
        'baltic_index_cache',
        'candle_cache',
        'candle_cache_meta',
        'candle_snapshots',
        'chokepoint_metrics',
        'claude_usage',
        'email_verifications',
        'enriched_news',
        'entry_optimizer_logs',
        'error_analysis',
        'failure_analyses',
        'failure_clusters',
        'improvement_proposals',
        'learning_feedback',
        'learning_insights',
        'live_data_cache',
        'mapbox_usage_counters',
        'meta_combination_stats',
        'meta_signals',
        'model_permutation_batch_results',
        'mt5_trade_logs',
        'multi_target_outcomes',
        'multi_target_predictions',
        'outcome_results',
        'pattern_mining_runs',
        'permutation_batch_runs',
        'prediction_logs',
        'prediction_replay_corrections',
        'referrals',
        'scheduler_state',
        'signal_aborts',
        'signal_checks',
        'signal_failures',
        'signal_trajectory_snapshots',
        'signal_vetoes',
        'subscription_packages',
        'tanker_positions',
        'tanker_state',
        'technical_permutation_batch_results',
        'tp_sl_recommendations',
        'user_credentials',
        'user_notification_settings',
        'user_profiles',
        'user_reports',
        'user_sessions',
        'user_subscriptions',
        'users'
    ];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        -- Tablo gerçekten var mı? (eksik tablo varsa atla)
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = t
        ) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
            EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY;', t);

            -- service_role için tam yetki (backend kullanır)
            EXECUTE format(
                'DROP POLICY IF EXISTS service_role_all ON public.%I;', t
            );
            EXECUTE format(
                'CREATE POLICY service_role_all ON public.%I '
                'FOR ALL TO service_role USING (true) WITH CHECK (true);', t
            );

            RAISE NOTICE 'RLS enabled + service_role policy created on %', t;
        ELSE
            RAISE NOTICE 'Table % does not exist, skipped', t;
        END IF;
    END LOOP;
END$$;

-- ============================================================================
-- Kullanıcı tablolarına ek policy (kullanıcı yalnızca kendi satırlarını görür)
-- Eğer frontend authenticated kullanıyorsa lazım. Şimdilik yorum.
-- ============================================================================
-- CREATE POLICY user_own_profile ON public.user_profiles
--     FOR ALL TO authenticated
--     USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
--
-- CREATE POLICY user_own_subscription ON public.user_subscriptions
--     FOR ALL TO authenticated
--     USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
