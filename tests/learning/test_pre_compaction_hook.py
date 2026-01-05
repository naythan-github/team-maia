#!/usr/bin/env python3
"""
Tests for Pre-Compaction Learning Capture Hook
Phase 237: Pre-Compaction Learning Capture

Test Coverage:
- Hook input parsing
- Full processing flow
- Retry logic (3 attempts with exponential backoff)
- Graceful degradation on failure
- Performance (<5s requirement)
- Error logging
- Metrics logging

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude.hooks.pre_compaction_learning_capture import PreCompactionHook


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    db_path.unlink(missing_ok=True)


@pytest.fixture
def sample_transcript():
    """Create sample JSONL transcript."""
    messages = [
        {
            'type': 'user_message',
            'content': 'Help me implement learning capture',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': 'I decided to use SQLite because it requires no external service.',
            'timestamp': '2026-01-06T10:00:05Z'
        },
        {
            'type': 'tool_use',
            'tool': 'Write',
            'content': 'Creating schema...',
            'timestamp': '2026-01-06T10:00:10Z'
        },
        {
            'type': 'assistant_message',
            'content': '✅ Schema created successfully',
            'timestamp': '2026-01-06T10:00:15Z'
        }
    ]

    return '\n'.join(json.dumps(msg) for msg in messages)


@pytest.fixture
def hook(temp_db):
    """Create hook instance with temp database."""
    from claude.tools.learning.archive import ConversationArchive

    # Override archive to use temp DB
    with patch('claude.hooks.pre_compaction_learning_capture.get_archive') as mock_get_archive:
        archive = ConversationArchive(temp_db)
        mock_get_archive.return_value = archive

        hook = PreCompactionHook()
        hook.archive = archive

        yield hook


def test_hook_process_success(hook, sample_transcript):
    """Test successful hook processing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'test_context_123',
            'transcript_path': str(transcript_path),
            'trigger': 'auto',
            'hook_event_name': 'PreCompact'
        }

        result = hook.process(hook_input)

        assert result['success'] is True
        assert result['snapshot_id'] is not None
        assert result['learnings_captured'] > 0
        assert result['messages_processed'] == 4
        assert result['execution_time_ms'] > 0
        assert result.get('error_message') is None

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_process_missing_transcript(hook):
    """Test handling of missing transcript file."""
    hook_input = {
        'session_id': 'test_context_456',
        'transcript_path': '/nonexistent/path/transcript.jsonl',
        'trigger': 'auto'
    }

    result = hook.process(hook_input)

    # Should fail gracefully
    assert result['success'] is False
    assert result['snapshot_id'] is None
    assert result['error_message'] is not None
    assert 'FileNotFoundError' in result['error_message']


def test_hook_retry_logic(hook, sample_transcript):
    """Test retry mechanism with transient failures."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        # Mock archive to fail twice, then succeed
        original_archive = hook.archive.archive_conversation
        call_count = [0]

        def failing_archive(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Transient DB error")
            return original_archive(*args, **kwargs)

        hook.archive.archive_conversation = failing_archive

        hook_input = {
            'session_id': 'retry_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto'
        }

        result = hook.process(hook_input, max_retries=3)

        # Should succeed on 3rd attempt
        assert result['success'] is True
        assert call_count[0] == 3

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_graceful_degradation(hook, sample_transcript):
    """Test graceful degradation after all retries fail."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        # Mock archive to always fail
        hook.archive.archive_conversation = Mock(side_effect=Exception("Permanent failure"))

        hook_input = {
            'session_id': 'failure_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto'
        }

        result = hook.process(hook_input, max_retries=3)

        # Should fail gracefully
        assert result['success'] is False
        assert result['snapshot_id'] is None
        assert result['learnings_captured'] == 0
        assert 'Permanent failure' in result['error_message']

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_performance(hook):
    """Test hook meets <5s performance requirement."""
    # Create large conversation (1000 messages)
    messages = []
    for i in range(1000):
        messages.append(json.dumps({
            'type': 'assistant_message' if i % 2 else 'user_message',
            'content': f'Message {i}: I decided to implement approach {i % 10}',
            'timestamp': f'2026-01-06T10:{i // 60:02d}:{i % 60:02d}Z'
        }))

    large_transcript = '\n'.join(messages)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(large_transcript)
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'perf_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto'
        }

        start_time = time.time()
        result = hook.process(hook_input)
        execution_time = time.time() - start_time

        assert result['success'] is True
        assert execution_time < 5.0  # Must complete in <5s
        assert result['execution_time_ms'] < 5000

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_extracts_topics(hook):
    """Test topic extraction from learnings."""
    learnings = [
        {'content': 'Decided to use SQLite database for simplicity'},
        {'content': 'Fixed authentication bug by updating token validation'},
        {'content': 'Implemented caching to improve performance'}
    ]

    topics = hook._extract_topics(learnings)

    assert isinstance(topics, list)
    assert len(topics) <= 10
    # Should extract meaningful words
    assert any('sqlite' in topic.lower() for topic in topics) or \
           any('database' in topic.lower() for topic in topics) or \
           any('authentication' in topic.lower() for topic in topics)


def test_hook_logging_error(hook, sample_transcript):
    """Test error logging."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        hook.archive.archive_conversation = Mock(side_effect=Exception("Test error"))

        hook_input = {
            'session_id': 'error_log_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto'
        }

        hook.process(hook_input)

        # Check error log exists
        assert hook.error_log.exists()

        # Check error was logged
        with open(hook.error_log) as f:
            log_content = f.read()

        assert 'Test error' in log_content

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_logging_metric(hook, sample_transcript):
    """Test metrics logging to database."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'metric_test',
            'transcript_path': str(transcript_path),
            'trigger': 'manual'
        }

        result = hook.process(hook_input)

        # Verify metric was logged
        with hook.archive._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM compaction_metrics
                WHERE context_id = ?
            """, ('metric_test',))
            row = cursor.fetchone()

        assert row is not None
        assert row['success'] == 1
        assert row['trigger_type'] == 'manual'
        assert row['execution_time_ms'] > 0
        assert row['learnings_extracted'] > 0

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_auto_trigger(hook, sample_transcript):
    """Test auto-triggered compaction."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'auto_trigger_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto',
            'hook_event_name': 'PreCompact'
        }

        result = hook.process(hook_input)

        # Verify snapshot created with auto trigger
        snapshot = hook.archive.get_conversation('auto_trigger_test')
        assert snapshot['trigger_type'] == 'auto'

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_manual_trigger(hook, sample_transcript):
    """Test manually-triggered compaction (/compact command)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(sample_transcript)
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'manual_trigger_test',
            'transcript_path': str(transcript_path),
            'trigger': 'manual',
            'hook_event_name': 'PreCompact'
        }

        result = hook.process(hook_input)

        # Verify snapshot created with manual trigger
        snapshot = hook.archive.get_conversation('manual_trigger_test')
        assert snapshot['trigger_type'] == 'manual'

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_empty_transcript(hook):
    """Test handling of empty transcript."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write("")  # Empty file
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'empty_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto'
        }

        result = hook.process(hook_input)

        # Should succeed but with 0 learnings
        assert result['success'] is True
        assert result['learnings_captured'] == 0
        assert result['messages_processed'] == 0

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_malformed_transcript(hook):
    """Test handling of corrupted transcript."""
    malformed = """
{"type": "user_message", "content": "Valid message"}
This is not JSON
{"type": "assistant_message", "content": "Another valid message"}
{invalid json}
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(malformed)
        transcript_path = Path(f.name)

    try:
        hook_input = {
            'session_id': 'malformed_test',
            'transcript_path': str(transcript_path),
            'trigger': 'auto'
        }

        result = hook.process(hook_input)

        # Should succeed (extraction handles malformed lines)
        assert result['success'] is True
        assert result['messages_processed'] == 2  # Only valid messages

    finally:
        transcript_path.unlink(missing_ok=True)


def test_hook_concurrent_processing(hook, sample_transcript):
    """Test thread-safety of concurrent hook executions."""
    import threading

    results = []
    errors = []

    def process_hook(context_id):
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                f.write(sample_transcript)
                transcript_path = Path(f.name)

            hook_input = {
                'session_id': context_id,
                'transcript_path': str(transcript_path),
                'trigger': 'auto'
            }

            result = hook.process(hook_input)
            results.append(result)

            transcript_path.unlink(missing_ok=True)

        except Exception as e:
            errors.append(e)

    # Run 5 hooks concurrently
    threads = []
    for i in range(5):
        t = threading.Thread(target=process_hook, args=(f'concurrent_test_{i}',))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All should succeed
    assert len(errors) == 0
    assert len(results) == 5
    assert all(r['success'] for r in results)
