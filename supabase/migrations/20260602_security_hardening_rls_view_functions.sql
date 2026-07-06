-- ============================================================================
-- Security hardening — RLS + SECURITY DEFINER view + function search_path
-- 2026-06-02 — Supabase Security Advisor düzeltmeleri
--
-- Bağlam:
--   * Backend SUPABASE_SERVICE_ROLE_KEY ile çalışır (service_role RLS'i bypass eder).
--   * Frontend Supabase'e DOĞRUDAN bağlanmaz (her şey FastAPI üzerinden geçer).
--   => RLS açmak / sıkılaştırmak backend'i ETKİLEMEZ.
--
-- Karar: Mevcut anon/authenticated policy'lerine DOKUNULMAZ (kullanıcı isteği).
--   Anon policy'si olan tablolarda (tanker_*, chokepoint_metrics, mt5_trade_logs,
--   meta_*) RLS aktifleşince o policy'ler çalışmaya devam eder; anon erişimi korunur.
--   Policy'si olmayan tablolar service_role-only olur.
--
-- NOT: 20260602_enable_rls_all_tables.sql commit edilmiş ama prod'a hiç
--      uygulanmamıştı (advisor hâlâ RLS-disabled gösteriyordu). Bu migration
--      onu tamamlar + idempotenttir + news_chart_impacts'i de kapsar.
-- ============================================================================

-- 1) RLS aç (advisor'ın RLS-disabled bulduğu 13 tablo) -----------------------
DO $$
DECLARE
    t text;
    tables text[] := ARRAY[
        'scheduler_state',
        'enriched_news',
        'ai_panel_prompt_versions',
        'ai_panel_analysis_cache',
        'ai_panel_analysis_history',
        'ai_panel_signal_snapshots',
        'tanker_positions',
        'tanker_state',
        'chokepoint_metrics',
        'permutation_batch_runs',
        'model_permutation_batch_results',
        'technical_permutation_batch_results',
        'news_chart_impacts'
    ];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = t
        ) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);

            -- service_role için tam yetki (backend kullanır). Mevcut anon
            -- policy'lerine dokunmaz; yalnızca service_role policy'sini idempotent kurar.
            EXECUTE format('DROP POLICY IF EXISTS service_role_all ON public.%I;', t);
            EXECUTE format(
                'CREATE POLICY service_role_all ON public.%I '
                'FOR ALL TO service_role USING (true) WITH CHECK (true);', t
            );

            RAISE NOTICE 'RLS enabled + service_role policy on %', t;
        ELSE
            RAISE NOTICE 'Table % does not exist, skipped', t;
        END IF;
    END LOOP;
END$$;

-- 2) SECURITY DEFINER view -> security_invoker -------------------------------
-- View, çağıran rolün yetki/RLS'iyle çalışsın (creator'ın değil).
-- Yalnızca backend (service_role) sorguladığı için erişim kesilmez.
ALTER VIEW public.signal_veto_summary SET (security_invoker = on);

-- 3) Function search_path sabitleme (search_path hijack koruması) ------------
-- Tüm overload'ları kapsar.
DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT p.oid::regprocedure AS sig
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND p.proname IN ('fill_enriched_news_bilingual_fields', 'claim_active_signals')
    LOOP
        EXECUTE format('ALTER FUNCTION %s SET search_path = public, pg_catalog', r.sig);
        RAISE NOTICE 'search_path pinned on %', r.sig;
    END LOOP;
END$$;
