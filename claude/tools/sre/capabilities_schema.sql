-- Capabilities Database Schema
-- Phase 168: Fast Tool/Agent Discovery for Maia
-- Phase 192: Performance Optimization (WAL mode, tuned cache)
-- Agent: SRE Principal Engineer Agent
-- Date: 2025-11-22

-- Performance PRAGMAs (Phase 192)
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;           -- Write-Ahead Logging for better concurrency
PRAGMA synchronous = NORMAL;          -- Faster writes (still crash-safe with WAL)
PRAGMA cache_size = -2000;            -- 2MB cache
PRAGMA temp_store = MEMORY;           -- Use memory for temp tables
PRAGMA busy_timeout = 5000;           -- 5 second timeout for locks

-- =============================================================================
-- Table: capabilities (Core registry of all tools and agents)
-- =============================================================================
CREATE TABLE IF NOT EXISTS capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- e.g., "system_state_queries.py", "sre_principal_engineer_agent.md"
    type TEXT NOT NULL,                  -- 'tool' or 'agent'
    path TEXT NOT NULL,                  -- relative path from maia root
    category TEXT,                       -- 'sre', 'security', 'data', 'msp', 'integration', etc.
    purpose TEXT,                        -- one-line description
    keywords TEXT,                       -- comma-separated searchable terms
    created_phase TEXT,                  -- phase that created this (e.g., "165", "134.4")
    status TEXT DEFAULT 'production',    -- 'production', 'experimental', 'deprecated'
    last_modified TEXT,                  -- file modification date
    file_size_bytes INTEGER,             -- file size for reference
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_capabilities_type ON capabilities(type);
CREATE INDEX IF NOT EXISTS idx_capabilities_category ON capabilities(category);
CREATE INDEX IF NOT EXISTS idx_capabilities_status ON capabilities(status);
CREATE INDEX IF NOT EXISTS idx_capabilities_name ON capabilities(name);

-- =============================================================================
-- Table: capability_tags (Many-to-many tagging for flexible search)
-- =============================================================================
CREATE TABLE IF NOT EXISTS capability_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capability_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE,
    UNIQUE(capability_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_capability_tags_tag ON capability_tags(tag);

-- =============================================================================
-- Views for common queries
-- =============================================================================

-- View: All agents with their categories
CREATE VIEW IF NOT EXISTS v_agents AS
SELECT name, path, category, purpose, status, keywords
FROM capabilities
WHERE type = 'agent' AND status != 'deprecated'
ORDER BY category, name;

-- View: All tools with their categories
CREATE VIEW IF NOT EXISTS v_tools AS
SELECT name, path, category, purpose, status, keywords
FROM capabilities
WHERE type = 'tool' AND status != 'deprecated'
ORDER BY category, name;

-- View: Capabilities by category (counts)
CREATE VIEW IF NOT EXISTS v_category_summary AS
SELECT
    category,
    type,
    COUNT(*) as count,
    GROUP_CONCAT(name, ', ') as items
FROM capabilities
WHERE status != 'deprecated'
GROUP BY category, type
ORDER BY category, type;

-- =============================================================================
-- Schema version tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial capabilities schema: tools and agents registry');
