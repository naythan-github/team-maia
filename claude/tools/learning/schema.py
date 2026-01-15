#!/usr/bin/env python3
"""
Database schemas for Personal PAI v2.

Two databases:
- memory.db: Session summaries with full-text search (Maia Memory)
- learning.db: Patterns, preferences, and metrics
"""

import sqlite3
from pathlib import Path

MEMORY_SCHEMA = """
-- Maia Memory: Session summaries
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    context_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    initial_query TEXT,
    agent_used TEXT,
    domain TEXT,
    status TEXT CHECK(status IN ('active', 'completed', 'abandoned', 'error')),

    -- Summary (populated on session end)
    summary_text TEXT,
    key_decisions TEXT,          -- JSON array
    tools_used TEXT,             -- JSON: {tool: count}
    files_touched TEXT,          -- JSON array

    -- VERIFY results
    verify_success BOOLEAN,
    verify_confidence REAL,
    verify_metrics TEXT,         -- JSON

    -- LEARN results
    learn_insights TEXT,         -- JSON array
    patterns_extracted INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_domain ON sessions(domain);

-- Full-text search for summaries
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    id, initial_query, summary_text, key_decisions,
    content=sessions, content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
    INSERT INTO sessions_fts(rowid, id, initial_query, summary_text, key_decisions)
    VALUES (new.rowid, new.id, new.initial_query, new.summary_text, new.key_decisions);
END;

CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, id, initial_query, summary_text, key_decisions)
    VALUES ('delete', old.rowid, old.id, old.initial_query, old.summary_text, old.key_decisions);
    INSERT INTO sessions_fts(rowid, id, initial_query, summary_text, key_decisions)
    VALUES (new.rowid, new.id, new.initial_query, new.summary_text, new.key_decisions);
END;
"""

PROMPTS_SCHEMA = """
-- Session Prompts: Captures all user prompts during sessions
-- Sprint: SPRINT-002-PROMPT-CAPTURE
CREATE TABLE IF NOT EXISTS session_prompts (
    prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    prompt_index INTEGER NOT NULL,  -- 0-indexed within session
    prompt_text TEXT NOT NULL,
    timestamp TEXT NOT NULL,        -- ISO 8601 format
    char_count INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    agent_active TEXT,              -- Which agent was active
    prompt_hash TEXT,               -- SHA256 hash for dedup

    UNIQUE(session_id, prompt_index)
);

CREATE INDEX IF NOT EXISTS idx_prompts_session ON session_prompts(session_id);
CREATE INDEX IF NOT EXISTS idx_prompts_context ON session_prompts(context_id);
CREATE INDEX IF NOT EXISTS idx_prompts_timestamp ON session_prompts(timestamp DESC);

-- Full-text search for prompts
CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
    prompt_text,
    content=session_prompts,
    content_rowid=prompt_id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS prompts_fts_ai AFTER INSERT ON session_prompts BEGIN
    INSERT INTO prompts_fts(rowid, prompt_text)
    VALUES (new.prompt_id, new.prompt_text);
END;

CREATE TRIGGER IF NOT EXISTS prompts_fts_au AFTER UPDATE ON session_prompts BEGIN
    INSERT INTO prompts_fts(prompts_fts, rowid, prompt_text)
    VALUES ('delete', old.prompt_id, old.prompt_text);
    INSERT INTO prompts_fts(rowid, prompt_text)
    VALUES (new.prompt_id, new.prompt_text);
END;

CREATE TRIGGER IF NOT EXISTS prompts_fts_ad AFTER DELETE ON session_prompts BEGIN
    INSERT INTO prompts_fts(prompts_fts, rowid, prompt_text)
    VALUES ('delete', old.prompt_id, old.prompt_text);
END;
"""

LEARNING_SCHEMA = """
-- Patterns: Extracted from sessions
CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT CHECK(pattern_type IN ('workflow', 'tool_sequence', 'preference', 'correction')),
    domain TEXT,
    description TEXT NOT NULL,
    pattern_data TEXT,           -- JSON: specific pattern details
    confidence REAL DEFAULT 0.5,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TEXT,
    last_seen TEXT,
    decayed_confidence REAL      -- Computed: confidence * decay_factor
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_domain ON patterns(domain);

-- Preferences: Inferred from corrections
CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,      -- 'coding_style', 'tool_choice', 'communication', etc.
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    source_sessions TEXT,        -- JSON: [session_ids that contributed]
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(category, key)
);

CREATE INDEX IF NOT EXISTS idx_preferences_category ON preferences(category);

-- Metrics: Session success tracking
CREATE TABLE IF NOT EXISTS metrics (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,   -- 'tool_success', 'task_completion', 'user_correction'
    value REAL NOT NULL,
    metadata TEXT,               -- JSON
    recorded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type, recorded_at);
"""


def init_memory_db(db_path: Path) -> sqlite3.Connection:
    """
    Initialize Maia Memory database.

    Args:
        db_path: Path to memory.db file

    Returns:
        Open connection to initialized database
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(MEMORY_SCHEMA)
    conn.commit()
    return conn


def init_learning_db(db_path: Path) -> sqlite3.Connection:
    """
    Initialize learning database.

    Args:
        db_path: Path to learning.db file

    Returns:
        Open connection to initialized database
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(LEARNING_SCHEMA)
    conn.commit()
    return conn


def init_prompts_db(db_path: Path) -> sqlite3.Connection:
    """
    Initialize prompts tables in memory database.

    Args:
        db_path: Path to memory.db file

    Returns:
        Open connection to initialized database
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(PROMPTS_SCHEMA)
    conn.commit()
    return conn


__all__ = ["init_memory_db", "init_learning_db", "init_prompts_db",
           "MEMORY_SCHEMA", "LEARNING_SCHEMA", "PROMPTS_SCHEMA"]
