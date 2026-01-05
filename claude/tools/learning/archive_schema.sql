-- Conversation Archive Schema
-- Phase 237: Pre-Compaction Learning Capture
-- Created: 2026-01-06
--
-- Purpose: Archive full conversations before Claude Code compaction
-- to preserve learning context and enable retrieval.

-- Main archive table
CREATE TABLE IF NOT EXISTS conversation_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id TEXT NOT NULL,
    session_id TEXT,
    snapshot_timestamp INTEGER NOT NULL,
    trigger_type TEXT CHECK(trigger_type IN ('auto', 'manual')),

    -- Transcript data
    transcript_path TEXT,
    full_conversation TEXT NOT NULL,  -- Complete JSONL
    message_count INTEGER NOT NULL,
    token_estimate INTEGER,

    -- Learning summary
    learning_count INTEGER DEFAULT 0,
    learning_ids TEXT,  -- JSON array of PAI v2 learning IDs

    -- Metadata
    tool_usage_stats TEXT,  -- JSON: tool frequency map
    agents_used TEXT,  -- JSON: agent list
    error_count INTEGER DEFAULT 0,

    -- Retrieval optimization
    first_message TEXT,  -- First user message (for search)
    last_message TEXT,   -- Last message before compaction
    topics TEXT,  -- JSON: extracted topics/keywords

    -- Unique constraint: one snapshot per context per timestamp
    UNIQUE(context_id, snapshot_timestamp)
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_context_snapshots
ON conversation_snapshots(context_id, snapshot_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_session_snapshots
ON conversation_snapshots(session_id);

CREATE INDEX IF NOT EXISTS idx_snapshot_time
ON conversation_snapshots(snapshot_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_trigger_type
ON conversation_snapshots(trigger_type);

-- Full-text search for conversation content
CREATE VIRTUAL TABLE IF NOT EXISTS conversation_search USING fts5(
    context_id UNINDEXED,
    first_message,
    last_message,
    topics,
    content=conversation_snapshots,
    content_rowid=snapshot_id
);

-- Trigger to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS conversation_search_insert
AFTER INSERT ON conversation_snapshots BEGIN
    INSERT INTO conversation_search(
        rowid,
        context_id,
        first_message,
        last_message,
        topics
    )
    VALUES (
        new.snapshot_id,
        new.context_id,
        new.first_message,
        new.last_message,
        new.topics
    );
END;

CREATE TRIGGER IF NOT EXISTS conversation_search_delete
AFTER DELETE ON conversation_snapshots BEGIN
    DELETE FROM conversation_search WHERE rowid = old.snapshot_id;
END;

CREATE TRIGGER IF NOT EXISTS conversation_search_update
AFTER UPDATE ON conversation_snapshots BEGIN
    DELETE FROM conversation_search WHERE rowid = old.snapshot_id;
    INSERT INTO conversation_search(
        rowid,
        context_id,
        first_message,
        last_message,
        topics
    )
    VALUES (
        new.snapshot_id,
        new.context_id,
        new.first_message,
        new.last_message,
        new.topics
    );
END;

-- Compaction metrics table (for monitoring)
CREATE TABLE IF NOT EXISTS compaction_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id TEXT NOT NULL,
    compaction_timestamp INTEGER NOT NULL,
    trigger_type TEXT CHECK(trigger_type IN ('auto', 'manual')),

    -- Performance metrics
    execution_time_ms INTEGER,
    messages_processed INTEGER,
    learnings_extracted INTEGER,

    -- Status
    success BOOLEAN NOT NULL,
    error_message TEXT,

    -- Snapshot reference
    snapshot_id INTEGER REFERENCES conversation_snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_compaction_metrics_context
ON compaction_metrics(context_id, compaction_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_compaction_metrics_time
ON compaction_metrics(compaction_timestamp DESC);
