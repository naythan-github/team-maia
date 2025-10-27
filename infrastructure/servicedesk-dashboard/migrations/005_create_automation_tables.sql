-- Migration: Create automation tables for Phase 2 (future automation panels)
-- Project: TIER-TRACKER-001
-- Phase: 3 - Database Schema Implementation
-- Date: 2025-10-27
-- Requirements: NFR-5.2, Schema Change 5, User Q3 (automation in 1-2 months)

-- Purpose:
-- Prepare tables for Panels 12-13 (automation impact tracking)
-- Tables created now (empty), populated in Phase 2 when automation data available
-- Timeline: 1-2 months (user-confirmed)

-- Execution:
-- docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -f /path/to/005_create_automation_tables.sql

BEGIN;

-- Table 1: automation_metrics
-- Tracks automated ticket reduction (SSL alerts, patch management, etc.)
CREATE TABLE IF NOT EXISTS servicedesk.automation_metrics (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL,
    automation_type VARCHAR(100) NOT NULL,  -- 'SSL Alerts', 'Password Reset', 'Patch Management', etc.
    tickets_automated INTEGER NOT NULL,
    hours_saved NUMERIC(10,2),
    cost_saved NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_automation_tickets_positive CHECK (tickets_automated >= 0),
    CONSTRAINT chk_automation_hours_positive CHECK (hours_saved >= 0),
    CONSTRAINT chk_automation_cost_positive CHECK (cost_saved >= 0)
);

-- Add comments for documentation
COMMENT ON TABLE servicedesk.automation_metrics IS
'Automation impact tracking for Panel 12. Populated when automation data available (Phase 2, 1-2 months). Tracks ticket volume reduction from automation initiatives.';

COMMENT ON COLUMN servicedesk.automation_metrics.automation_type IS
'Type of automation (e.g., "SSL Certificate Renewal", "Password Reset Automation", "Patch Management")';

COMMENT ON COLUMN servicedesk.automation_metrics.tickets_automated IS
'Number of tickets automated/deflected this month';

-- Create index for query performance
CREATE INDEX IF NOT EXISTS idx_automation_month
ON servicedesk.automation_metrics(month);

-- Table 2: self_service_metrics
-- Tracks self-service portal usage and deflection rate
CREATE TABLE IF NOT EXISTS servicedesk.self_service_metrics (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL,
    service_type VARCHAR(100) NOT NULL,  -- 'Password Reset', 'Account Access', 'Config Change', etc.
    deflected_tickets INTEGER NOT NULL,
    success_rate NUMERIC(5,2),  -- Percentage (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_selfservice_deflected_positive CHECK (deflected_tickets >= 0),
    CONSTRAINT chk_selfservice_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Add comments for documentation
COMMENT ON TABLE servicedesk.self_service_metrics IS
'Self-service portal impact tracking for Panel 13. Populated when self-service data available (Phase 2, 1-2 months). Tracks ticket deflection from self-service options.';

COMMENT ON COLUMN servicedesk.self_service_metrics.deflected_tickets IS
'Number of tickets deflected via self-service (users resolved issue without ticket)';

COMMENT ON COLUMN servicedesk.self_service_metrics.success_rate IS
'Self-service success rate percentage (0-100)';

-- Create index for query performance
CREATE INDEX IF NOT EXISTS idx_selfservice_month
ON servicedesk.self_service_metrics(month);

COMMIT;

-- Verification:
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_schema='servicedesk'
--   AND table_name IN ('automation_metrics', 'self_service_metrics');

-- Note: Tables are EMPTY initially (Phase 2 population when automation data available)
