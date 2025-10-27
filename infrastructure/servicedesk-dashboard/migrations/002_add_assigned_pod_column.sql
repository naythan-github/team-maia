-- Migration: Add assigned_pod column to tickets table
-- Project: TIER-TRACKER-001
-- Phase: 3 - Database Schema Implementation
-- Date: 2025-10-27
-- Requirements: FR-4.3, Schema Change 2, User Q1

-- Purpose:
-- Add assigned_pod column to track pod assignments for Panel 11 (L1 Rate by Pod)
-- NULL allowed for historical tickets (before pod structure implemented)
-- Supports future AI-based routing by complexity

-- Execution:
-- docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -f /path/to/002_add_assigned_pod_column.sql

BEGIN;

-- Add assigned_pod column (NULL for historical tickets, populated for future tickets)
ALTER TABLE servicedesk.tickets
ADD COLUMN IF NOT EXISTS assigned_pod VARCHAR(50);

-- Add comment for documentation
COMMENT ON COLUMN servicedesk.tickets.assigned_pod IS
'Pod assignment for ticket (e.g., "Cloud Pod", "Security Pod", "Infrastructure Pod"). NULL for historical tickets before pod structure. Future: AI-based routing by complexity.';

COMMIT;

-- Verification:
-- SELECT column_name, data_type, character_maximum_length, is_nullable
-- FROM information_schema.columns
-- WHERE table_schema='servicedesk' AND table_name='tickets' AND column_name='assigned_pod';
