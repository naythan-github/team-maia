#!/usr/bin/env python3
"""
Tests for Conversation Retrieval Tools
Phase 237: Pre-Compaction Learning Capture

Test Coverage:
- get_conversation()
- search_conversations()
- get_compaction_history()
- export_conversation() (markdown, json, text)
- get_conversation_stats()

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
import pytest
import tempfile
from pathlib import Path
from claude.tools.learning import retrieval
from claude.tools.learning.archive import ConversationArchive


@pytest.fixture
def temp_archive():
    """Create temporary archive for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    archive = ConversationArchive(db_path)

    # Populate with test data
    conversation1 = '\n'.join([
        json.dumps({'type': 'user_message', 'content': 'Help with database schema', 'timestamp': '2026-01-06T10:00:00Z'}),
        json.dumps({'type': 'assistant_message', 'content': 'I decided to use SQLite for simplicity', 'timestamp': '2026-01-06T10:00:05Z'}),
    ])

    conversation2 = '\n'.join([
        json.dumps({'type': 'user_message', 'content': 'Write Python API', 'timestamp': '2026-01-06T11:00:00Z'}),
        json.dumps({'type': 'tool_use', 'tool': 'Write', 'content': 'Creating API', 'timestamp': '2026-01-06T11:00:05Z'}),
        json.dumps({'type': 'assistant_message', 'content': '✅ API complete', 'timestamp': '2026-01-06T11:00:10Z'}),
    ])

    archive.archive_conversation(
        context_id='test_context_1',
        full_conversation=conversation1,
        metadata={'learning_count': 1, 'learning_ids': ['learn_001']}
    )

    archive.archive_conversation(
        context_id='test_context_2',
        full_conversation=conversation2,
        metadata={'learning_count': 1, 'tool_usage': {'Write': 1}}
    )

    # Override singleton
    retrieval.get_archive._instance = archive

    yield archive

    db_path.unlink(missing_ok=True)


def test_get_conversation_basic(temp_archive):
    """Test basic conversation retrieval."""
    conversation = retrieval.get_conversation('test_context_1')

    assert conversation is not None
    assert conversation['context_id'] == 'test_context_1'
    assert conversation['message_count'] == 2
    assert len(conversation['messages']) == 2


def test_get_conversation_not_found(temp_archive):
    """Test retrieval of non-existent conversation."""
    conversation = retrieval.get_conversation('nonexistent_context')
    assert conversation is None


def test_get_conversation_with_timestamp_filter(temp_archive):
    """Test retrieval with timestamp filtering."""
    import time

    # Archive another snapshot for same context
    conversation = '\n'.join([
        json.dumps({'type': 'user_message', 'content': 'Follow-up message', 'timestamp': '2026-01-06T12:00:00Z'}),
    ])

    time.sleep(1)
    temp_archive.archive_conversation(
        context_id='test_context_1',
        full_conversation=conversation
    )

    # Get all snapshots for this context
    history = temp_archive.get_compaction_history('test_context_1')
    assert len(history) == 2

    # Get snapshot before latest
    earlier_snapshot = retrieval.get_conversation(
        'test_context_1',
        before_timestamp=history[1]['snapshot_timestamp']
    )

    assert earlier_snapshot is not None
    assert earlier_snapshot['snapshot_id'] == history[0]['snapshot_id']


def test_search_conversations(temp_archive):
    """Test full-text search."""
    results = retrieval.search_conversations('database')

    assert len(results) >= 1
    # Should find test_context_1 which mentions "database schema"
    found = any(r['context_id'] == 'test_context_1' for r in results)
    assert found


def test_search_conversations_no_results(temp_archive):
    """Test search with no matches."""
    results = retrieval.search_conversations('nonexistent_keyword_xyz')
    assert len(results) == 0


def test_search_conversations_limit(temp_archive):
    """Test search result limiting."""
    # Archive multiple conversations
    for i in range(5):
        conv = json.dumps({'type': 'user_message', 'content': f'database query {i}'})
        temp_archive.archive_conversation(
            context_id=f'search_test_{i}',
            full_conversation=conv
        )

    results = retrieval.search_conversations('database', limit=3)
    assert len(results) <= 3


def test_get_compaction_history(temp_archive):
    """Test compaction history retrieval."""
    import time

    # Create multiple compactions for same context
    for i in range(3):
        conv = json.dumps({'type': 'user_message', 'content': f'message {i}'})
        temp_archive.archive_conversation(
            context_id='history_test',
            full_conversation=conv
        )
        time.sleep(0.1)  # Ensure different timestamps

    history = retrieval.get_compaction_history('history_test')

    assert len(history) == 3
    # Should be chronologically ordered
    for i in range(len(history) - 1):
        assert history[i]['snapshot_timestamp'] <= history[i + 1]['snapshot_timestamp']


def test_export_conversation_markdown(temp_archive):
    """Test markdown export."""
    markdown = retrieval.export_conversation('test_context_1', format='markdown')

    assert markdown != ""
    assert 'test_context_1' in markdown
    assert '##' in markdown  # Should have headers
    assert 'User' in markdown or 'user' in markdown.lower()
    assert 'database' in markdown.lower()


def test_export_conversation_json(temp_archive):
    """Test JSON export."""
    json_output = retrieval.export_conversation('test_context_1', format='json')

    assert json_output != ""

    # Should be valid JSON
    parsed = json.loads(json_output)
    assert parsed['context_id'] == 'test_context_1'
    assert 'messages' in parsed


def test_export_conversation_text(temp_archive):
    """Test plain text export."""
    text = retrieval.export_conversation('test_context_1', format='text')

    assert text != ""
    assert 'test_context_1' in text
    assert 'USER:' in text or 'ASSISTANT:' in text


def test_export_conversation_invalid_format(temp_archive):
    """Test export with invalid format."""
    with pytest.raises(ValueError):
        retrieval.export_conversation('test_context_1', format='invalid_format')


def test_export_conversation_to_file(temp_archive):
    """Test exporting to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'conversation.md'

        markdown = retrieval.export_conversation(
            'test_context_1',
            format='markdown',
            output_path=output_path
        )

        # File should be created
        assert output_path.exists()

        # Content should match
        with open(output_path) as f:
            file_content = f.read()

        assert file_content == markdown


def test_export_nonexistent_conversation(temp_archive):
    """Test exporting conversation that doesn't exist."""
    output = retrieval.export_conversation('nonexistent_context')
    assert output == ""


def test_get_conversation_stats_global(temp_archive):
    """Test global conversation statistics."""
    stats = retrieval.get_conversation_stats()

    assert stats['total_snapshots'] >= 2
    assert stats['total_messages'] >= 5  # test_context_1 + test_context_2
    assert stats['total_learnings'] >= 2
    assert stats['unique_contexts'] >= 2


def test_get_conversation_stats_specific_context(temp_archive):
    """Test statistics for specific context."""
    stats = retrieval.get_conversation_stats(context_id='test_context_1')

    assert stats['context_id'] == 'test_context_1'
    assert stats['total_snapshots'] == 1
    assert stats['total_messages'] == 2
    assert stats['total_learnings'] == 1


def test_get_conversation_stats_empty_context(temp_archive):
    """Test stats for context with no snapshots."""
    stats = retrieval.get_conversation_stats(context_id='nonexistent_context')

    assert stats['total_snapshots'] == 0
    assert stats['total_messages'] == 0
    assert stats['total_learnings'] == 0


def test_markdown_export_with_tools(temp_archive):
    """Test markdown export includes tool usage."""
    markdown = retrieval.export_conversation('test_context_2', format='markdown')

    assert 'Tools Used' in markdown or 'tool' in markdown.lower()
    assert 'Write' in markdown


def test_markdown_export_with_learnings(temp_archive):
    """Test markdown export includes learnings."""
    markdown = retrieval.export_conversation('test_context_1', format='markdown')

    assert 'learning' in markdown.lower()
    assert 'learn_001' in markdown


def test_text_export_formatting(temp_archive):
    """Test text export has proper formatting."""
    text = retrieval.export_conversation('test_context_1', format='text')

    lines = text.split('\n')

    # Should have header separator
    assert any('===' in line for line in lines)

    # Should have timestamps
    assert any('2026-01-06' in line for line in lines)


def test_retrieval_with_multiple_messages(temp_archive):
    """Test retrieval of conversation with many messages."""
    # Create conversation with many messages
    messages = []
    for i in range(50):
        messages.append(json.dumps({
            'type': 'user_message' if i % 2 == 0 else 'assistant_message',
            'content': f'Message {i}',
            'timestamp': f'2026-01-06T10:{i:02d}:00Z'
        }))

    temp_archive.archive_conversation(
        context_id='large_conversation',
        full_conversation='\n'.join(messages)
    )

    conversation = retrieval.get_conversation('large_conversation')

    assert conversation['message_count'] == 50
    assert len(conversation['messages']) == 50


def test_export_preserves_message_order(temp_archive):
    """Test that export maintains message chronological order."""
    json_output = retrieval.export_conversation('test_context_1', format='json')
    parsed = json.loads(json_output)

    messages = parsed['messages']

    # Check timestamps are in order
    for i in range(len(messages) - 1):
        time1 = messages[i].get('timestamp', '')
        time2 = messages[i + 1].get('timestamp', '')
        assert time1 <= time2
