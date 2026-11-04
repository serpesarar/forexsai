-- Close anon-key exposure on 13 legacy tables flagged by the Supabase advisor.
--
-- SAFE: the frontend never queries Supabase directly (it goes through the
-- backend API, which uses the service_role key and therefore BYPASSES RLS).
-- So enabling RLS + a service_role policy keeps backend access intact while
-- removing the unintended anon/authenticated access. Idempotent.

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'scheduler_state','enriched_news','ai_panel_prompt_versions',
    'ai_panel_analysis_cache','ai_panel_analysis_history','ai_panel_signal_snapshots',
    'tanker_positions','tanker_state','chokepoint_metrics',
    'permutation_batch_runs','model_permutation_batch_results',
    'technical_permutation_batch_results','news_chart_impacts'
  ] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
    EXECUTE format('DROP POLICY IF EXISTS "Service role full access %s" ON public.%I;', t, t);
    EXECUTE format(
      'CREATE POLICY "Service role full access %s" ON public.%I FOR ALL '
      'USING (auth.role() = ''service_role'') WITH CHECK (auth.role() = ''service_role'');',
      t, t);
  END LOOP;
END $$;
