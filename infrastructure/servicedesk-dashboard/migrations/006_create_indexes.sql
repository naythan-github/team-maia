-- Migration: Create performance indexes for query optimization
-- Project: TIER-TRACKER-001
-- Phase: 3 - Database Schema Implementation
-- Date: 2025-10-27
-- Requirements: NFR-1.1, Schema Change 6

-- Purpose:
-- Ensure <100ms query latency (P95) for all dashboard panels
-- Indexes on: support_tier, assigned_pod, created_time

-- Execution:
-- docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -f /path/to/006_create_indexes.sql

BEGIN;

-- Index 1: support_tier (used in all dashboard queries)
CREATE INDEX IF NOT EXISTS idx_tickets_support_tier
ON servicedesk.tickets(support_tier);

COMMENT ON INDEX servicedesk.idx_tickets_support_tier IS
'Performance index for tier filtering (all dashboard queries). Target: <100ms P95 latency.';

-- Index 2: assigned_pod (used in Panel 11: L1 Rate by Pod)
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_pod
ON servicedesk.tickets(assigned_pod);

COMMENT ON INDEX servicedesk.idx_tickets_assigned_pod IS
'Performance index for pod filtering (Panel 11). Filters WHERE assigned_pod IS NOT NULL.';

-- Index 3: TKT-Created Time (used in time-range filters)
CREATE INDEX IF NOT EXISTS idx_tickets_created_time
ON servicedesk.tickets("TKT-Created Time");

COMMENT ON INDEX servicedesk.idx_tickets_created_time IS
'Performance index for date range filtering (current month, last 12 months). Used in all panels.';

-- Composite index: support_tier + created_time (optimized for common query pattern)
CREATE INDEX IF NOT EXISTS idx_tickets_tier_created
ON servicedesk.tickets(support_tier, "TKT-Created Time");

COMMENT ON INDEX servicedesk.idx_tickets_tier_created IS
'Composite index for tier + date filtering. Optimizes queries like: WHERE support_tier=X AND created_time > Y';

-- Composite index: assigned_pod + support_tier (optimized for Panel 11)
CREATE INDEX IF NOT EXISTS idx_tickets_pod_tier
ON servicedesk.tickets(assigned_pod, support_tier)
WHERE assigned_pod IS NOT NULL;  -- Partial index (excludes NULL pods)

COMMENT ON INDEX servicedesk.idx_tickets_pod_tier IS
'Partial composite index for pod + tier filtering (Panel 11). Only indexes non-NULL pods for efficiency.';

COMMIT;

-- Verification:
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE schemaname='servicedesk'
--   AND tablename='tickets'
--   AND indexname LIKE '%tier%' OR indexname LIKE '%pod%'
-- ORDER BY indexname;

-- Performance validation:
-- EXPLAIN ANALYZE
-- SELECT support_tier, COUNT(*)
-- FROM servicedesk.tickets
-- WHERE "TKT-Created Time"::timestamp >= CURRENT_DATE - INTERVAL '12 months'
-- GROUP BY support_tier;
--
-- Expected: Index Scan on idx_tickets_tier_created (not Seq Scan)
