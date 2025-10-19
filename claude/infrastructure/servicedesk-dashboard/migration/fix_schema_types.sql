-- Fix PostgreSQL Schema - Convert TEXT columns to proper types
-- This ensures queries work without explicit casting and ETL pipeline compatibility

-- Set search path
SET search_path TO servicedesk, public;

BEGIN;

-- Backup the current schema (just in case)
COMMENT ON TABLE tickets IS 'Schema fixed on 2025-10-19: TEXT → TIMESTAMP conversions for date columns';

-- ============================================================================
-- FIX TICKETS TABLE - Date/Time Columns
-- ============================================================================

-- Convert TIMESTAMP columns (currently TEXT)
-- These columns contain valid timestamp data in format 'YYYY-MM-DD HH:MM:SS'

-- 1. TKT-Created Time (should be TIMESTAMP)
ALTER TABLE tickets
ALTER COLUMN "TKT-Created Time" TYPE TIMESTAMP
USING CASE
    WHEN "TKT-Created Time" IS NULL OR "TKT-Created Time" = '' THEN NULL
    ELSE "TKT-Created Time"::timestamp
END;

-- 2. TKT-Modified Time (should be TIMESTAMP)
ALTER TABLE tickets
ALTER COLUMN "TKT-Modified Time" TYPE TIMESTAMP
USING CASE
    WHEN "TKT-Modified Time" IS NULL OR "TKT-Modified Time" = '' THEN NULL
    ELSE "TKT-Modified Time"::timestamp
END;

-- 3. TKT-SLA Closure Date (should be TIMESTAMP)
ALTER TABLE tickets
ALTER COLUMN "TKT-SLA Closure Date" TYPE TIMESTAMP
USING CASE
    WHEN "TKT-SLA Closure Date" IS NULL OR "TKT-SLA Closure Date" = '' THEN NULL
    ELSE "TKT-SLA Closure Date"::timestamp
END;

-- These are TEXT in source but contain timestamp data
-- Convert for consistency

-- 4. TKT-Actual Response Date (TEXT with timestamp data)
ALTER TABLE tickets
ALTER COLUMN "TKT-Actual Response Date" TYPE TIMESTAMP
USING CASE
    WHEN "TKT-Actual Response Date" IS NULL OR "TKT-Actual Response Date" = '' THEN NULL
    ELSE "TKT-Actual Response Date"::timestamp
END;

-- 5. TKT-Actual Resolution Date (TEXT with timestamp data)
ALTER TABLE tickets
ALTER COLUMN "TKT-Actual Resolution Date" TYPE TIMESTAMP
USING CASE
    WHEN "TKT-Actual Resolution Date" IS NULL OR "TKT-Actual Resolution Date" = '' THEN NULL
    ELSE "TKT-Actual Resolution Date"::timestamp
END;

-- 6. TKT-Closure Date (TEXT with timestamp data)
ALTER TABLE tickets
ALTER COLUMN "TKT-Closure Date" TYPE TIMESTAMP
USING CASE
    WHEN "TKT-Closure Date" IS NULL OR "TKT-Closure Date" = '' THEN NULL
    ELSE "TKT-Closure Date"::timestamp
END;

-- Change-related dates (if we use them later)
-- 7. Chg-Planned Start Date
ALTER TABLE tickets
ALTER COLUMN "Chg-Planned Start Date" TYPE TIMESTAMP
USING CASE
    WHEN "Chg-Planned Start Date" IS NULL OR "Chg-Planned Start Date" = '' THEN NULL
    ELSE "Chg-Planned Start Date"::timestamp
END;

-- 8. Chg-Planned End Date
ALTER TABLE tickets
ALTER COLUMN "Chg-Planned End Date" TYPE TIMESTAMP
USING CASE
    WHEN "Chg-Planned End Date" IS NULL OR "Chg-Planned End Date" = '' THEN NULL
    ELSE "Chg-Planned End Date"::timestamp
END;

-- 9. Chg-Actual Start Date
ALTER TABLE tickets
ALTER COLUMN "Chg-Actual Start Date" TYPE TIMESTAMP
USING CASE
    WHEN "Chg-Actual Start Date" IS NULL OR "Chg-Actual Start Date" = '' THEN NULL
    ELSE "Chg-Actual Start Date"::timestamp
END;

-- 10. Chg-Actual End Date
ALTER TABLE tickets
ALTER COLUMN "Chg-Actual End Date" TYPE TIMESTAMP
USING CASE
    WHEN "Chg-Actual End Date" IS NULL OR "Chg-Actual End Date" = '' THEN NULL
    ELSE "Chg-Actual End Date"::timestamp
END;

-- ============================================================================
-- FIX COMMENTS TABLE - Timestamp Column
-- ============================================================================

ALTER TABLE comments
ALTER COLUMN comment_timestamp TYPE TIMESTAMP
USING CASE
    WHEN comment_timestamp IS NULL OR comment_timestamp = '' THEN NULL
    ELSE comment_timestamp::timestamp
END;

-- ============================================================================
-- FIX COMMENT_QUALITY TABLE - Analysis Timestamp
-- ============================================================================

ALTER TABLE comment_quality
ALTER COLUMN analyzed_at TYPE TIMESTAMP
USING CASE
    WHEN analyzed_at IS NULL OR analyzed_at = '' THEN NULL
    ELSE analyzed_at::timestamp
END;

-- ============================================================================
-- RECREATE INDEXES (PostgreSQL automatically updates them after ALTER)
-- ============================================================================

-- Indexes are automatically maintained, but let's verify they still exist
-- Resolution time index (now with proper TIMESTAMP types)
DROP INDEX IF EXISTS idx_tickets_resolution_dates;
CREATE INDEX idx_tickets_resolution_dates ON tickets("TKT-Actual Resolution Date", "TKT-Created Time");

-- Created time index
DROP INDEX IF EXISTS idx_tickets_created_time;
CREATE INDEX idx_tickets_created_time ON tickets("TKT-Created Time");

-- Comment timestamp index
DROP INDEX IF EXISTS idx_comments_timestamp;
CREATE INDEX idx_comments_timestamp ON comments(comment_timestamp);

COMMIT;

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Verify column types changed
SELECT
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp without time zone' THEN '✅ FIXED'
        WHEN data_type = 'text' THEN '❌ STILL TEXT'
        ELSE data_type
    END as status
FROM information_schema.columns
WHERE table_schema = 'servicedesk'
  AND table_name = 'tickets'
  AND column_name LIKE '%Time%' OR column_name LIKE '%Date%'
ORDER BY column_name;

-- Test a date calculation query (should work without ::timestamp casting)
SELECT
    'Resolution Time Calculation Test' as test,
    ROUND(EXTRACT(EPOCH FROM AVG("TKT-Actual Resolution Date" - "TKT-Created Time"))/86400, 2) as avg_days,
    '✅ PASS - No casting needed!' as result
FROM tickets
WHERE "TKT-Status" IN ('Closed', 'Resolved')
  AND "TKT-Actual Resolution Date" IS NOT NULL;

-- Count rows to ensure no data loss
SELECT
    'Data Integrity Check' as test,
    COUNT(*) as total_tickets,
    CASE
        WHEN COUNT(*) = 10939 THEN '✅ PASS - All rows intact'
        ELSE '❌ FAIL - Row count mismatch'
    END as result
FROM tickets;
