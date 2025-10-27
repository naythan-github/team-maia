-- Migration: Create tier_cost_config table for dynamic cost management
-- Project: TIER-TRACKER-001
-- Phase: 3 - Database Schema Implementation
-- Date: 2025-10-27
-- Requirements: FR-1.4, NFR-4.1, Schema Change 4

-- Purpose:
-- Store tier costs and target percentages in database (NO hardcoded values)
-- Enables cost updates without code changes (user requirement)
-- Panel 4 (Cost Savings) queries this table dynamically

-- Execution:
-- docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -f /path/to/004_create_tier_cost_config_table.sql

BEGIN;

-- Create tier_cost_config table
CREATE TABLE IF NOT EXISTS servicedesk.tier_cost_config (
    tier VARCHAR(10) PRIMARY KEY,
    cost_per_ticket NUMERIC(10,2) NOT NULL,
    target_percentage NUMERIC(5,2) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_cost_positive CHECK (cost_per_ticket > 0),
    CONSTRAINT chk_target_percentage CHECK (target_percentage >= 0 AND target_percentage <= 100)
);

-- Add comments for documentation
COMMENT ON TABLE servicedesk.tier_cost_config IS
'Tier cost and target configuration. Update costs via SQL (no code deployment needed). Used by Panel 4 for dynamic cost savings calculation.';

COMMENT ON COLUMN servicedesk.tier_cost_config.cost_per_ticket IS
'Average cost per ticket for this tier (USD)';

COMMENT ON COLUMN servicedesk.tier_cost_config.target_percentage IS
'Target percentage for this tier (industry benchmarks: L1=65%, L2=30%, L3=7.5%)';

COMMENT ON COLUMN servicedesk.tier_cost_config.effective_date IS
'Date when this cost/target became active (for historical tracking)';

-- Insert initial configuration (user-confirmed costs)
INSERT INTO servicedesk.tier_cost_config (tier, cost_per_ticket, target_percentage, effective_date)
VALUES
    ('L1', 100.00, 65.0, CURRENT_DATE),  -- L1: $100/ticket, target 65% (industry: 60-70%)
    ('L2', 200.00, 30.0, CURRENT_DATE),  -- L2: $200/ticket, target 30% (industry: 25-35%)
    ('L3', 300.00, 7.5, CURRENT_DATE)    -- L3: $300/ticket, target 7.5% (industry: 5-10%)
ON CONFLICT (tier) DO NOTHING;  -- Skip if already exists (idempotent)

COMMIT;

-- Verification:
-- SELECT tier, cost_per_ticket, target_percentage, effective_date
-- FROM servicedesk.tier_cost_config
-- ORDER BY tier;

-- Usage example (update L1 cost to $120):
-- UPDATE servicedesk.tier_cost_config
-- SET cost_per_ticket = 120.00, effective_date = CURRENT_DATE
-- WHERE tier = 'L1';
