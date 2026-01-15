-- Finish Checker Schema Extension
-- Extends project_tracking.db with completion_records table
--
-- Sprint: /finish Skill Implementation
-- Phase: P2 - Database Schema
-- Created: 2026-01-15
--
-- Usage:
--   sqlite3 claude/data/databases/system/project_tracking.db < claude/tools/sre/finish_schema.sql

-- Completion Records Table
-- Stores completion verification records from /finish skill
CREATE TABLE IF NOT EXISTS completion_records (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Session linkage (audit trail)
    session_id TEXT NOT NULL,           -- Links to learning session
    context_id TEXT NOT NULL,           -- Claude Code context ID

    -- Project metadata
    project_name TEXT,                  -- Optional project name
    agent_used TEXT NOT NULL,           -- Agent that performed completion

    -- Timestamps
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Check results (JSON)
    -- Format: {"git_status": "PASS", "capability": "WARN", ...}
    check_results TEXT NOT NULL,

    -- Interactive review responses (JSON)
    -- Format: {"claude_md": "No change needed", "dependent_systems": "..."}
    review_responses TEXT NOT NULL,

    -- Files touched during session (JSON array)
    -- Format: ["claude/tools/sre/file.py", ...]
    files_touched TEXT,

    -- Summary metrics
    total_checks INTEGER,
    passed_checks INTEGER,
    failed_checks INTEGER,
    warned_checks INTEGER,

    -- Status: COMPLETE, BLOCKED, ESCALATED
    status TEXT NOT NULL DEFAULT 'COMPLETE'
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_completion_session
    ON completion_records(session_id);

CREATE INDEX IF NOT EXISTS idx_completion_context
    ON completion_records(context_id);

CREATE INDEX IF NOT EXISTS idx_completion_date
    ON completion_records(completed_at);

CREATE INDEX IF NOT EXISTS idx_completion_agent
    ON completion_records(agent_used);

CREATE INDEX IF NOT EXISTS idx_completion_project
    ON completion_records(project_name);

CREATE INDEX IF NOT EXISTS idx_completion_status
    ON completion_records(status);

-- View for quick completion summary
CREATE VIEW IF NOT EXISTS v_completion_summary AS
SELECT
    date(completed_at) as completion_date,
    agent_used,
    COUNT(*) as total_completions,
    SUM(CASE WHEN status = 'COMPLETE' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked,
    SUM(CASE WHEN status = 'ESCALATED' THEN 1 ELSE 0 END) as escalated,
    AVG(passed_checks * 1.0 / NULLIF(total_checks, 0)) as avg_pass_rate
FROM completion_records
GROUP BY date(completed_at), agent_used
ORDER BY completion_date DESC;

-- View for recent completions
CREATE VIEW IF NOT EXISTS v_recent_completions AS
SELECT
    id,
    session_id,
    context_id,
    project_name,
    agent_used,
    completed_at,
    status,
    passed_checks || '/' || total_checks as check_summary
FROM completion_records
ORDER BY completed_at DESC
LIMIT 20;
