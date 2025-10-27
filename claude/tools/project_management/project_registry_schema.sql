-- Maia Project Registry Database Schema
-- Project: PROJ-REG-001
-- Purpose: Production-grade project backlog tracking
-- Created: 2025-10-27
-- SRE Design: ACID guarantees, WAL mode, performance indexes

-- ============================================================================
-- PRAGMA Configuration (Performance + Reliability)
-- ============================================================================

-- Enable Write-Ahead Logging (WAL mode) for crash recovery
PRAGMA journal_mode = WAL;

-- Enable foreign key constraints (referential integrity)
PRAGMA foreign_keys = ON;

-- Optimize for performance (but maintain ACID guarantees)
PRAGMA synchronous = NORMAL;  -- Balanced safety/performance
PRAGMA cache_size = -64000;   -- 64MB cache

-- ============================================================================
-- Table: projects (Primary Registry)
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    -- Identity
    id TEXT PRIMARY KEY,                    -- e.g., "REPO-GOV-001"
    name TEXT NOT NULL,                     -- "Git Repository Governance"

    -- Status & Priority
    status TEXT NOT NULL                    -- planned/active/blocked/completed/archived
        CHECK(status IN ('planned', 'active', 'blocked', 'completed', 'archived')),
    priority TEXT NOT NULL DEFAULT 'medium' -- critical/high/medium/low
        CHECK(priority IN ('critical', 'high', 'medium', 'low')),

    -- Effort & Impact
    effort_hours INTEGER,                   -- estimated hours (null if unknown)
    actual_hours INTEGER,                   -- tracked hours (null until completed)
    impact TEXT                             -- high/medium/low
        CHECK(impact IN ('high', 'medium', 'low')),

    -- Categorization
    category TEXT,                          -- SRE/DevOps/Security/ServiceDesk/Agent/etc.
    tags TEXT,                              -- JSON array: ["performance", "monitoring"]

    -- Timeline
    created_date TEXT NOT NULL,             -- ISO 8601: "2025-10-27T10:30:00Z"
    started_date TEXT,                      -- when status → active
    completed_date TEXT,                    -- when status → completed

    -- References
    project_plan_path TEXT,                 -- path to detailed plan (md file)
    confluence_url TEXT,                    -- optional Confluence page
    github_issue_url TEXT,                  -- optional GitHub issue

    -- Notes
    description TEXT,                       -- brief summary
    notes TEXT,                             -- detailed notes, constraints, context

    -- Metadata
    created_by TEXT DEFAULT 'maia',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Performance indexes for common queries
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_priority ON projects(priority);
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_date DESC);
CREATE INDEX IF NOT EXISTS idx_projects_status_priority ON projects(status, priority);

-- ============================================================================
-- Table: project_updates (Audit Log)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),

    -- Change tracking
    field_changed TEXT,                     -- "status", "priority", etc.
    old_value TEXT,
    new_value TEXT,

    -- Context
    change_reason TEXT,                     -- why was this changed?
    updated_by TEXT DEFAULT 'maia',

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Index for audit queries (most recent first)
CREATE INDEX IF NOT EXISTS idx_updates_project ON project_updates(project_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_updates_timestamp ON project_updates(timestamp DESC);

-- ============================================================================
-- Table: deliverables (Project Outputs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,

    -- Deliverable info
    name TEXT NOT NULL,                     -- "validate_core_schema.py"
    type TEXT NOT NULL                      -- tool/agent/documentation/infrastructure
        CHECK(type IN ('tool', 'agent', 'documentation', 'infrastructure', 'database', 'workflow', 'config')),
    status TEXT NOT NULL DEFAULT 'planned'  -- planned/in_progress/completed
        CHECK(status IN ('planned', 'in_progress', 'completed')),

    -- References
    file_path TEXT,                         -- actual location if created
    description TEXT,                       -- brief description

    -- Timeline
    created_date TEXT NOT NULL DEFAULT (datetime('now')),
    completed_date TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Indexes for deliverable queries
CREATE INDEX IF NOT EXISTS idx_deliverables_project ON deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(type);

-- ============================================================================
-- Table: dependencies (Project Relationships)
-- ============================================================================

CREATE TABLE IF NOT EXISTS dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relationship
    project_id TEXT NOT NULL,               -- dependent project
    depends_on_project_id TEXT NOT NULL,    -- dependency (must complete first)

    -- Metadata
    dependency_type TEXT DEFAULT 'blocks'   -- blocks/optional/enhances
        CHECK(dependency_type IN ('blocks', 'optional', 'enhances')),
    notes TEXT,                             -- why is this a dependency?

    created_date TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_project_id) REFERENCES projects(id) ON DELETE CASCADE,

    -- Prevent duplicate dependencies
    UNIQUE(project_id, depends_on_project_id)
);

-- Indexes for dependency graph queries
CREATE INDEX IF NOT EXISTS idx_deps_project ON dependencies(project_id);
CREATE INDEX IF NOT EXISTS idx_deps_depends_on ON dependencies(depends_on_project_id);

-- ============================================================================
-- Views (Convenient Queries)
-- ============================================================================

-- View: Active projects with deliverable counts
CREATE VIEW IF NOT EXISTS v_active_projects AS
SELECT
    p.id,
    p.name,
    p.status,
    p.priority,
    p.effort_hours,
    p.started_date,
    COUNT(d.id) as deliverable_count,
    SUM(CASE WHEN d.status = 'completed' THEN 1 ELSE 0 END) as completed_deliverables
FROM projects p
LEFT JOIN deliverables d ON p.id = d.project_id
WHERE p.status IN ('active', 'blocked')
GROUP BY p.id;

-- View: Planned projects prioritized by effort and priority
CREATE VIEW IF NOT EXISTS v_backlog AS
SELECT
    p.id,
    p.name,
    p.priority,
    p.effort_hours,
    p.impact,
    p.category,
    COUNT(dep.id) as dependency_count,
    p.created_date
FROM projects p
LEFT JOIN dependencies dep ON p.id = dep.project_id AND dep.dependency_type = 'blocks'
WHERE p.status = 'planned'
ORDER BY
    CASE p.priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    p.effort_hours ASC;

-- View: Project completion statistics
CREATE VIEW IF NOT EXISTS v_project_stats AS
SELECT
    status,
    priority,
    COUNT(*) as count,
    SUM(effort_hours) as total_effort,
    AVG(effort_hours) as avg_effort,
    SUM(CASE WHEN actual_hours IS NOT NULL THEN actual_hours - effort_hours ELSE 0 END) as total_variance
FROM projects
GROUP BY status, priority;

-- ============================================================================
-- Triggers (Automatic Audit Logging)
-- ============================================================================

-- Trigger: Log status changes
CREATE TRIGGER IF NOT EXISTS trg_audit_status_change
AFTER UPDATE OF status ON projects
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO project_updates (project_id, field_changed, old_value, new_value, change_reason)
    VALUES (NEW.id, 'status', OLD.status, NEW.status, 'Status updated');
END;

-- Trigger: Log priority changes
CREATE TRIGGER IF NOT EXISTS trg_audit_priority_change
AFTER UPDATE OF priority ON projects
FOR EACH ROW
WHEN NEW.priority != OLD.priority
BEGIN
    INSERT INTO project_updates (project_id, field_changed, old_value, new_value, change_reason)
    VALUES (NEW.id, 'priority', OLD.priority, NEW.priority, 'Priority updated');
END;

-- Trigger: Set started_date when status becomes active
CREATE TRIGGER IF NOT EXISTS trg_set_started_date
AFTER UPDATE OF status ON projects
FOR EACH ROW
WHEN NEW.status = 'active' AND OLD.status != 'active' AND NEW.started_date IS NULL
BEGIN
    UPDATE projects SET started_date = datetime('now') WHERE id = NEW.id;
END;

-- Trigger: Set completed_date when status becomes completed
CREATE TRIGGER IF NOT EXISTS trg_set_completed_date
AFTER UPDATE OF status ON projects
FOR EACH ROW
WHEN NEW.status = 'completed' AND OLD.status != 'completed' AND NEW.completed_date IS NULL
BEGIN
    UPDATE projects SET completed_date = datetime('now') WHERE id = NEW.id;
END;

-- Trigger: Update updated_at timestamp on any change
CREATE TRIGGER IF NOT EXISTS trg_update_timestamp
AFTER UPDATE ON projects
FOR EACH ROW
BEGIN
    UPDATE projects SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- Initial Data Validation
-- ============================================================================

-- Insert test project to validate schema
INSERT OR IGNORE INTO projects (
    id, name, status, priority, effort_hours, impact, category,
    description, created_date, project_plan_path
) VALUES (
    'PROJ-REG-001',
    'Maia Project Registry System',
    'active',
    'high',
    4,
    'high',
    'SRE',
    'Production-grade SQLite project backlog tracking system',
    datetime('now'),
    'claude/data/MAIA_PROJECT_REGISTRY_SYSTEM.md'
);

-- Insert test deliverables
INSERT OR IGNORE INTO deliverables (project_id, name, type, status, description) VALUES
    ('PROJ-REG-001', 'project_registry.db', 'database', 'in_progress', 'SQLite database schema'),
    ('PROJ-REG-001', 'project_registry.py', 'tool', 'planned', 'CLI tool for project management'),
    ('PROJ-REG-001', 'migrate_existing_projects.py', 'tool', 'planned', 'Migration script for existing projects'),
    ('PROJ-REG-001', 'MAIA_PROJECT_BACKLOG.md', 'documentation', 'planned', 'Auto-generated backlog markdown');

-- ============================================================================
-- Schema Validation Queries
-- ============================================================================

-- Verify tables created
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Verify indexes created
SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;

-- Verify views created
SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;

-- Verify triggers created
SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name;

-- Test query performance (should be <100ms)
SELECT COUNT(*) as project_count FROM projects;
SELECT * FROM v_backlog LIMIT 10;
SELECT * FROM v_active_projects;
SELECT * FROM v_project_stats;

-- Verify WAL mode enabled
PRAGMA journal_mode;

-- Verify foreign keys enabled
PRAGMA foreign_keys;

-- Check database integrity
PRAGMA integrity_check;

-- ============================================================================
-- Database Statistics
-- ============================================================================

-- Show database page size and cache
PRAGMA page_size;
PRAGMA cache_size;

-- ============================================================================
-- End of Schema
-- ============================================================================
