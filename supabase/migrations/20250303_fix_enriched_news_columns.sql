-- Fix enriched_news table - Add missing columns for RSS aggregation
-- Run this in Supabase SQL Editor

-- Check if columns exist and add them if missing
DO $$
BEGIN
    -- headline_tr column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='enriched_news' AND column_name='headline_tr') THEN
        ALTER TABLE enriched_news ADD COLUMN headline_tr TEXT;
        RAISE NOTICE 'Added headline_tr column';
    END IF;

    -- content_tr column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='enriched_news' AND column_name='content_tr') THEN
        ALTER TABLE enriched_news ADD COLUMN content_tr TEXT;
        RAISE NOTICE 'Added content_tr column';
    END IF;

    -- marker_type column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='enriched_news' AND column_name='marker_type') THEN
        ALTER TABLE enriched_news ADD COLUMN marker_type TEXT DEFAULT 'news';
        RAISE NOTICE 'Added marker_type column';
    END IF;

    -- marker_color column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='enriched_news' AND column_name='marker_color') THEN
        ALTER TABLE enriched_news ADD COLUMN marker_color TEXT DEFAULT '#3B82F6';
        RAISE NOTICE 'Added marker_color column';
    END IF;

    -- show_on_chart column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='enriched_news' AND column_name='show_on_chart') THEN
        ALTER TABLE enriched_news ADD COLUMN show_on_chart BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added show_on_chart column';
    END IF;
END $$;

-- Verify all columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'enriched_news'
ORDER BY ordinal_position;
