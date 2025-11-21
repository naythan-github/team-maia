-- SYSTEM_STATE Hybrid Database Schema
-- Phase 164: Migration from markdown to structured SQLite
-- Agent: SRE Principal Engineer Agent
-- Date: 2025-11-21

-- Enable foreign key constraints (CRITICAL for data integrity)
PRAGMA foreign_keys = ON;

-- =============================================================================
-- Table: phases (Core phase metadata)
-- =============================================================================
CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_number INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    date TEXT NOT NULL,  -- ISO 8601 format: YYYY-MM-DD
    status TEXT,  -- e.g., "PRODUCTION READY", "COMPLETE", "IN PROGRESS"
    achievement TEXT,  -- Brief summary of what was accomplished
    agent_team TEXT,  -- Comma-separated agent names
    git_commits TEXT,  -- Comma-separated commit hashes
    narrative_text TEXT,  -- Full markdown content for this phase (backup/fallback)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups by phase number
CREATE INDEX IF NOT EXISTS idx_phases_phase_number ON phases(phase_number);
-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_phases_date ON phases(date);
-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_phases_status ON phases(status);

-- =============================================================================
-- Table: problems (Problems solved in each phase)
-- =============================================================================
CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    problem_category TEXT,  -- e.g., "SQL injection", "performance", "reliability"
    before_state TEXT,  -- Description of problem before fix
    root_cause TEXT,  -- Why did this happen?
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
);

-- Index for pattern analysis queries
CREATE INDEX IF NOT EXISTS idx_problems_category ON problems(problem_category);
CREATE INDEX IF NOT EXISTS idx_problems_phase_id ON problems(phase_id);

-- =============================================================================
-- Table: solutions (How problems were solved)
-- =============================================================================
CREATE TABLE IF NOT EXISTS solutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    solution_category TEXT,  -- e.g., "architecture", "refactor", "tooling"
    after_state TEXT,  -- Description after fix
    architecture TEXT,  -- Architectural approach
    implementation_approach TEXT,  -- How it was built
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
);

-- Index for solution category analysis
CREATE INDEX IF NOT EXISTS idx_solutions_category ON solutions(solution_category);
CREATE INDEX IF NOT EXISTS idx_solutions_phase_id ON solutions(phase_id);

-- =============================================================================
-- Table: metrics (Quantitative measurements)
-- =============================================================================
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,  -- e.g., "time_savings_hours", "performance_improvement_percent"
    value REAL NOT NULL,
    unit TEXT,  -- e.g., "hours", "percent", "seconds"
    baseline TEXT,  -- What was it before?
    target TEXT,  -- What was the goal?
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
);

-- Index for metric aggregation queries
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_phase_id ON metrics(phase_id);

-- =============================================================================
-- Table: files_created (Deliverables from each phase)
-- =============================================================================
CREATE TABLE IF NOT EXISTS files_created (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,  -- e.g., "tool", "agent", "database", "documentation"
    purpose TEXT,  -- What does this file do?
    status TEXT,  -- e.g., "production", "deprecated", "experimental"
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
);

-- Index for file type queries
CREATE INDEX IF NOT EXISTS idx_files_type ON files_created(file_type);
CREATE INDEX IF NOT EXISTS idx_files_phase_id ON files_created(phase_id);
-- Index for file path lookups
CREATE INDEX IF NOT EXISTS idx_files_path ON files_created(file_path);

-- =============================================================================
-- Table: tags (Categorization for pattern analysis)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    tag TEXT NOT NULL,  -- e.g., "security", "performance", "TDD", "agent-enhancement"
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE,
    UNIQUE(phase_id, tag)  -- Prevent duplicate tags for same phase
);

-- Index for tag-based queries
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_phase_id ON tags(phase_id);

-- =============================================================================
-- Views for common queries
-- =============================================================================

-- View: Recent phases with full context
CREATE VIEW IF NOT EXISTS v_recent_phases AS
SELECT
    p.phase_number,
    p.title,
    p.date,
    p.status,
    p.achievement,
    p.agent_team,
    COUNT(DISTINCT pr.id) as problem_count,
    COUNT(DISTINCT s.id) as solution_count,
    COUNT(DISTINCT m.id) as metric_count,
    COUNT(DISTINCT f.id) as file_count
FROM phases p
LEFT JOIN problems pr ON p.id = pr.phase_id
LEFT JOIN solutions s ON p.id = s.phase_id
LEFT JOIN metrics m ON p.id = m.phase_id
LEFT JOIN files_created f ON p.id = f.phase_id
GROUP BY p.id
ORDER BY p.phase_number DESC;

-- View: Metric summary by metric name
CREATE VIEW IF NOT EXISTS v_metric_summary AS
SELECT
    metric_name,
    COUNT(*) as occurrence_count,
    SUM(value) as total_value,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    unit
FROM metrics
GROUP BY metric_name, unit;

-- View: Problem categories summary
CREATE VIEW IF NOT EXISTS v_problem_categories AS
SELECT
    problem_category,
    COUNT(*) as occurrence_count,
    GROUP_CONCAT(DISTINCT p.phase_number) as phase_numbers
FROM problems pr
JOIN phases p ON pr.phase_id = p.id
WHERE problem_category IS NOT NULL
GROUP BY problem_category
ORDER BY occurrence_count DESC;

-- View: File types summary
CREATE VIEW IF NOT EXISTS v_file_types AS
SELECT
    file_type,
    COUNT(*) as file_count,
    status,
    COUNT(*) as status_count
FROM files_created
WHERE file_type IS NOT NULL
GROUP BY file_type, status
ORDER BY file_count DESC;

-- =============================================================================
-- Metadata tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial schema version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial schema: phases, problems, solutions, metrics, files_created, tags');

-- =============================================================================
-- Validation queries (for testing data integrity)
-- =============================================================================

-- Check for orphaned records (should return 0 if foreign keys working)
-- SELECT COUNT(*) FROM problems WHERE phase_id NOT IN (SELECT id FROM phases);
-- SELECT COUNT(*) FROM solutions WHERE phase_id NOT IN (SELECT id FROM phases);
-- SELECT COUNT(*) FROM metrics WHERE phase_id NOT IN (SELECT id FROM phases);
-- SELECT COUNT(*) FROM files_created WHERE phase_id NOT IN (SELECT id FROM phases);
-- SELECT COUNT(*) FROM tags WHERE phase_id NOT IN (SELECT id FROM phases);
