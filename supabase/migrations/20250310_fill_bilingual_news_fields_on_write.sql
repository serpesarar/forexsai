CREATE OR REPLACE FUNCTION public.fill_enriched_news_bilingual_fields()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.summary_en := COALESCE(NULLIF(NEW.summary_en, ''), NULLIF(NEW.headline, ''));
  NEW.summary_tr := COALESCE(NULLIF(NEW.summary_tr, ''), NULLIF(NEW.headline_tr, ''), NULLIF(NEW.headline, ''));
  NEW.analysis_en := COALESCE(NULLIF(NEW.analysis_en, ''), NULLIF(NEW.content, ''), NULLIF(NEW.headline, ''));
  NEW.analysis_tr := COALESCE(
    NULLIF(NEW.analysis_tr, ''),
    NULLIF(NEW.content_tr, ''),
    NULLIF(NEW.headline_tr, ''),
    NULLIF(NEW.content, ''),
    NULLIF(NEW.headline, '')
  );

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_fill_enriched_news_bilingual_fields ON public.enriched_news;

CREATE TRIGGER trg_fill_enriched_news_bilingual_fields
BEFORE INSERT OR UPDATE OF headline, headline_tr, content, content_tr, summary_en, summary_tr, analysis_en, analysis_tr
ON public.enriched_news
FOR EACH ROW
EXECUTE FUNCTION public.fill_enriched_news_bilingual_fields();

UPDATE public.enriched_news
SET
  summary_en = COALESCE(NULLIF(summary_en, ''), NULLIF(headline, '')),
  summary_tr = COALESCE(NULLIF(summary_tr, ''), NULLIF(headline_tr, ''), NULLIF(headline, '')),
  analysis_en = COALESCE(NULLIF(analysis_en, ''), NULLIF(content, ''), NULLIF(headline, '')),
  analysis_tr = COALESCE(
    NULLIF(analysis_tr, ''),
    NULLIF(content_tr, ''),
    NULLIF(headline_tr, ''),
    NULLIF(content, ''),
    NULLIF(headline, '')
  )
WHERE
  summary_en IS NULL OR summary_en = '' OR
  summary_tr IS NULL OR summary_tr = '' OR
  analysis_en IS NULL OR analysis_en = '' OR
  analysis_tr IS NULL OR analysis_tr = '';

COMMENT ON FUNCTION public.fill_enriched_news_bilingual_fields() IS
'Keeps enriched_news bilingual summary and analysis fields populated from headline/content fallback values on insert and update.';