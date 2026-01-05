#!/usr/bin/env python3
"""
Tests for Conversation Archive System
Phase 237: Pre-Compaction Learning Capture

Test Coverage:
- Basic conversation archival
- Duplicate prevention (unique constraint)
- Token estimation accuracy
- Concurrent writes (DB locking)
- Retrieval operations
- Full-text search
- Compaction metrics logging

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import pytest
import sqlite3
import tempfile
import time
from pathlib import Path
from claude.tools.learning.archive import ConversationArchive, get_archive


@pytest.fixture
def temp_archive():
    """Create temporary archive database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    archive = ConversationArchive(db_path)
    yield archive

    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def sample_conversation():
    """Sample JSONL conversation for testing."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Help me implement pre-compaction learning capture',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'I\'ll help you build that. Let me start by creating the DB schema.',
            'timestamp': '2026-01-06T10:00:05Z'
        },
        {
            'type': 'tool_use',
            'tool': 'Write',
            'content': 'Creating archive_schema.sql...',
            'timestamp': '2026-01-06T10:00:10Z'
        },
        {
            'type': 'assistant_message',
            'content': '✅ Schema created. Decided to use SQLite because it\'s simple and requires no external service.',
            'timestamp': '2026-01-06T10:00:15Z'
        }
    ]

    return '\n'.join(json.dumps(msg) for msg in messages)


def test_archive_schema_creation(temp_archive):
    """Test that schema is created correctly."""
    with temp_archive._get_connection() as conn:
        # Check tables exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        assert 'conversation_snapshots' in tables
        assert 'conversation_search' in tables
        assert 'compaction_metrics' in tables


def test_archive_conversation_basic(temp_archive, sample_conversation):
    """Test basic conversation archival."""
    snapshot_id = temp_archive.archive_conversation(
        context_id='test_context_123',
        full_conversation=sample_conversation,
        trigger_type='manual'
    )

    assert snapshot_id > 0

    # Verify snapshot was created
    snapshot = temp_archive.get_conversation('test_context_123')
    assert snapshot is not None
    assert snapshot['context_id'] == 'test_context_123'
    assert snapshot['message_count'] == 4
    assert snapshot['trigger_type'] == 'manual'
    assert len(snapshot['messages']) == 4


def test_archive_with_metadata(temp_archive, sample_conversation):
    """Test archival with learning metadata."""
    metadata = {
        'learning_count': 1,
        'learning_ids': ['learn_001'],
        'tool_usage': {'Write': 1, 'Read': 0},
        'agents_used': ['sre_principal_engineer_agent'],
        'error_count': 0,
        'topics': ['database', 'schema', 'sqlite']
    }

    snapshot_id = temp_archive.archive_conversation(
        context_id='test_context_456',
        full_conversation=sample_conversation,
        trigger_type='auto',
        session_id='session_123',
        metadata=metadata
    )

    snapshot = temp_archive.get_conversation('test_context_456')
    assert snapshot['learning_count'] == 1
    assert snapshot['learning_ids'] == ['learn_001']
    assert snapshot['tool_usage_stats'] == {'Write': 1, 'Read': 0}
    assert snapshot['agents_used'] == ['sre_principal_engineer_agent']
    assert snapshot['topics'] == ['database', 'schema', 'sqlite']


def test_archive_duplicate_prevention(temp_archive, sample_conversation):
    """Test unique constraint on (context_id, timestamp)."""
    # First archive succeeds
    snapshot_id1 = temp_archive.archive_conversation(
        context_id='test_context_789',
        full_conversation=sample_conversation
    )
    assert snapshot_id1 > 0

    # Second archive with same context but different timestamp should succeed
    time.sleep(1)  # Ensure different timestamp
    snapshot_id2 = temp_archive.archive_conversation(
        context_id='test_context_789',
        full_conversation=sample_conversation
    )
    assert snapshot_id2 > snapshot_id1

    # Verify both snapshots exist
    history = temp_archive.get_compaction_history('test_context_789')
    assert len(history) == 2


def test_token_estimation(temp_archive):
    """Test token count estimation accuracy."""
    # Create conversations of known size
    short_conversation = '\n'.join([
        json.dumps({'type': 'user_message', 'content': 'Hello'}),
        json.dumps({'type': 'assistant_message', 'content': 'Hi there!'})
    ])

    snapshot_id = temp_archive.archive_conversation(
        context_id='test_tokens',
        full_conversation=short_conversation
    )

    snapshot = temp_archive.get_conversation('test_tokens')

    # Rough approximation: 1 token ≈ 4 chars
    expected_tokens = len(short_conversation) // 4
    assert abs(snapshot['token_estimate'] - expected_tokens) < 10


def test_get_conversation_latest(temp_archive, sample_conversation):
    """Test retrieval of latest snapshot."""
    # Create multiple snapshots
    for i in range(3):
        temp_archive.archive_conversation(
            context_id='test_latest',
            full_conversation=sample_conversation
        )
        time.sleep(1)

    # Get latest should return most recent
    latest = temp_archive.get_conversation('test_latest')
    history = temp_archive.get_compaction_history('test_latest')

    assert latest['snapshot_timestamp'] == history[-1]['snapshot_timestamp']


def test_get_conversation_by_timestamp(temp_archive, sample_conversation):
    """Test retrieval of specific snapshot by time."""
    timestamps = []

    # Create 3 snapshots
    for i in range(3):
        temp_archive.archive_conversation(
            context_id='test_time_filter',
            full_conversation=sample_conversation
        )
        timestamps.append(int(time.time() * 1000))  # Millisecond precision
        time.sleep(1)

    # Get snapshot before middle timestamp
    snapshot = temp_archive.get_conversation(
        'test_time_filter',
        before_timestamp=timestamps[2]
    )

    # Should get the second snapshot
    assert snapshot['snapshot_timestamp'] < timestamps[2]
    assert snapshot['snapshot_timestamp'] >= timestamps[0]


def test_get_conversation_not_found(temp_archive):
    """Test retrieval of non-existent conversation."""
    snapshot = temp_archive.get_conversation('nonexistent_context')
    assert snapshot is None


def test_search_conversations(temp_archive):
    """Test full-text search."""
    # Create conversations with different content
    conversations = [
        {
            'context_id': 'search_test_1',
            'content': [
                {'type': 'user_message', 'content': 'Help me with database schema'},
                {'type': 'assistant_message', 'content': 'I\'ll create a SQLite schema for you'}
            ]
        },
        {
            'context_id': 'search_test_2',
            'content': [
                {'type': 'user_message', 'content': 'Write Python code for API'},
                {'type': 'assistant_message', 'content': 'Creating Flask API endpoint'}
            ]
        },
        {
            'context_id': 'search_test_3',
            'content': [
                {'type': 'user_message', 'content': 'Fix database connection error'},
                {'type': 'assistant_message', 'content': 'Debugging SQLite connection'}
            ]
        }
    ]

    for conv in conversations:
        jsonl = '\n'.join(json.dumps(msg) for msg in conv['content'])
        temp_archive.archive_conversation(
            context_id=conv['context_id'],
            full_conversation=jsonl
        )

    # Search for "database"
    results = temp_archive.search_conversations('database')
    assert len(results) >= 2

    # Search for "API"
    results = temp_archive.search_conversations('API')
    assert len(results) >= 1


def test_compaction_history(temp_archive, sample_conversation):
    """Test timeline view of compactions."""
    # Create multiple compactions
    for i in range(5):
        temp_archive.archive_conversation(
            context_id='history_test',
            full_conversation=sample_conversation,
            trigger_type='auto' if i % 2 == 0 else 'manual'
        )
        time.sleep(0.5)

    history = temp_archive.get_compaction_history('history_test')

    assert len(history) == 5
    # Should be ordered chronologically
    for i in range(len(history) - 1):
        assert history[i]['snapshot_timestamp'] <= history[i + 1]['snapshot_timestamp']


def test_compaction_metrics_logging(temp_archive):
    """Test compaction performance metrics logging."""
    temp_archive.log_compaction_metric(
        context_id='metrics_test',
        trigger_type='auto',
        execution_time_ms=150,
        messages_processed=100,
        learnings_extracted=5,
        success=True,
        snapshot_id=1
    )

    # Verify metric was logged
    with temp_archive._get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM compaction_metrics
            WHERE context_id = ?
        """, ('metrics_test',))
        row = cursor.fetchone()

    assert row is not None
    assert row['execution_time_ms'] == 150
    assert row['messages_processed'] == 100
    assert row['learnings_extracted'] == 5
    assert row['success'] == 1


def test_compaction_metrics_failure(temp_archive):
    """Test logging of failed compaction."""
    temp_archive.log_compaction_metric(
        context_id='failure_test',
        trigger_type='auto',
        execution_time_ms=50,
        messages_processed=0,
        learnings_extracted=0,
        success=False,
        error_message='Database connection timeout'
    )

    with temp_archive._get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM compaction_metrics
            WHERE context_id = ?
        """, ('failure_test',))
        row = cursor.fetchone()

    assert row['success'] == 0
    assert row['error_message'] == 'Database connection timeout'


def test_parse_conversation_malformed_jsonl(temp_archive):
    """Test handling of corrupted JSONL."""
    malformed = """
{"type": "user_message", "content": "Hello"}
This is not JSON
{"type": "assistant_message", "content": "Hi"}
{invalid json
{"type": "assistant_message", "content": "Valid message"}
"""

    messages = temp_archive._parse_conversation(malformed)

    # Should skip malformed lines
    assert len(messages) == 3
    assert messages[0]['content'] == 'Hello'
    assert messages[1]['content'] == 'Hi'
    assert messages[2]['content'] == 'Valid message'


def test_singleton_pattern():
    """Test that get_archive returns same instance."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Clear any existing singleton
    if hasattr(get_archive, '_instance'):
        delattr(get_archive, '_instance')

    archive1 = get_archive(db_path)
    archive2 = get_archive(db_path)

    assert archive1 is archive2

    db_path.unlink(missing_ok=True)


def test_concurrent_writes(temp_archive, sample_conversation):
    """Test handling of concurrent archival (DB locking)."""
    import threading

    results = []
    errors = []

    def archive_worker(context_id):
        try:
            snapshot_id = temp_archive.archive_conversation(
                context_id=context_id,
                full_conversation=sample_conversation
            )
            results.append(snapshot_id)
        except Exception as e:
            errors.append(e)

    # Create 5 threads writing simultaneously
    threads = []
    for i in range(5):
        t = threading.Thread(target=archive_worker, args=(f'concurrent_test_{i}',))
        threads.append(t)
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # All should succeed (no DB lock errors)
    assert len(results) == 5
    assert len(errors) == 0


def test_empty_conversation_archival(temp_archive):
    """Test archival of empty conversation."""
    empty_conversation = ""

    snapshot_id = temp_archive.archive_conversation(
        context_id='empty_test',
        full_conversation=empty_conversation
    )

    snapshot = temp_archive.get_conversation('empty_test')
    assert snapshot['message_count'] == 0
    assert len(snapshot['messages']) == 0
