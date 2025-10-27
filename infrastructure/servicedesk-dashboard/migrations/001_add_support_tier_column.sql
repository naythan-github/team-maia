-- Migration: Add support_tier column to tickets table
-- Project: TIER-TRACKER-001
-- Phase: 3 - Database Schema Implementation
-- Date: 2025-10-27
-- Requirements: FR-1, Schema Change 1

-- Purpose:
-- Add support_tier column to track L1/L2/L3 categorization
-- VARCHAR(10) accommodates future tier naming changes (e.g., 'Tier 1', 'L1-Standard')

-- Execution:
-- docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -f /path/to/001_add_support_tier_column.sql

BEGIN;

-- Add support_tier column (initially NULL, populated by backfill script)
ALTER TABLE servicedesk.tickets
ADD COLUMN IF NOT EXISTS support_tier VARCHAR(10);

-- Add comment for documentation
COMMENT ON COLUMN servicedesk.tickets.support_tier IS
'Support tier categorization: L1 (standard requests), L2 (escalated), L3 (critical/architectural). Populated by backfill script.';

COMMIT;

-- Verification:
-- SELECT column_name, data_type, character_maximum_length, is_nullable
-- FROM information_schema.columns
-- WHERE table_schema='servicedesk' AND table_name='tickets' AND column_name='support_tier';
