-- Migration: Create tier_history table for weekly trend tracking
-- Project: TIER-TRACKER-001
-- Phase: 3 - Database Schema Implementation
-- Date: 2025-10-27
-- Requirements: FR-6.1, Schema Change 3, User Q3 (Weekly snapshots)

-- Purpose:
-- Track tier distribution snapshots weekly (every Sunday)
-- Enables historical trend visualization (Panel 5: Tier Distribution Over Time)
-- Storage: 52 snapshots/year × 3 tiers = 156 rows/year

-- Execution:
-- docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -f /path/to/003_create_tier_history_table.sql

BEGIN;

-- Create tier_history table
CREATE TABLE IF NOT EXISTS servicedesk.tier_history (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    support_tier VARCHAR(10) NOT NULL,
    ticket_count INTEGER NOT NULL,
    percentage NUMERIC(5,2) NOT NULL,
    category VARCHAR(100),  -- Optional: future category breakdown
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comments for documentation
COMMENT ON TABLE servicedesk.tier_history IS
'Weekly tier distribution snapshots for trend tracking. Populated by capture_tier_snapshot.py cron job (every Sunday 00:00).';

COMMENT ON COLUMN servicedesk.tier_history.snapshot_date IS
'Week ending date (Sunday) for this snapshot';

COMMENT ON COLUMN servicedesk.tier_history.percentage IS
'Tier percentage for this snapshot (0-100)';

-- Create indexes for query performance
CREATE INDEX IF NOT EXISTS idx_tier_history_date
ON servicedesk.tier_history(snapshot_date);

CREATE INDEX IF NOT EXISTS idx_tier_history_tier
ON servicedesk.tier_history(support_tier);

-- Create unique constraint to prevent duplicate snapshots
CREATE UNIQUE INDEX IF NOT EXISTS idx_tier_history_unique_snapshot
ON servicedesk.tier_history(snapshot_date, support_tier, category);

COMMIT;

-- Verification:
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_schema='servicedesk' AND table_name='tier_history'
-- ORDER BY ordinal_position;
