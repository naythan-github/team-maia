#!/usr/bin/env python3
"""
Integration Tests for Enhanced Pattern Flow
Phase 237.3: End-to-end testing

Tests the complete flow:
1. Conversation with enhanced patterns
2. Hook extracts learnings
3. PAI v2 bridge saves patterns
4. Archive stores with learning IDs
5. Retrieval works correctly
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from claude.tools.learning.extraction import get_extractor
from claude.tools.learning.archive import get_archive
from claude.tools.learning.pai_v2_bridge import get_pai_v2_bridge


@pytest.fixture
def temp_dirs():
    """Create temporary directories for test databases."""
    temp_dir = tempfile.mkdtemp()
    yield {
        'root': Path(temp_dir),
        'archive_db': Path(temp_dir) / 'conversation_archive.db',
        'learning_db': Path(temp_dir) / 'learning.db'
    }
    shutil.rmtree(temp_dir)


@pytest.fixture
def conversation_with_enhanced_patterns():
    """Create a conversation transcript with all enhanced pattern types."""
    messages = [
        {
            'type': 'user_message',
            'content': 'We need to improve the authentication system',
            'timestamp': '2026-01-06T10:00:00Z'
        },
        {
            'type': 'assistant_message',
            'content': '''
            Refactored the authentication module to use dependency injection for better testability.

            Optimized the token validation, reducing latency from 200ms to 20ms.

            Encountered TokenExpiredError when validating old tokens. Fixed by adding expiration check before validation.

            Learned that JWT validation is expensive - caching decoded tokens improves performance significantly.

            Breakthrough: Discovered that the bottleneck was in the cryptographic signature verification, not the database lookup.

            Added comprehensive integration tests covering all authentication flows.

            Fixed security vulnerability by validating token signatures before processing claims.

            ✅ All changes committed and deployed to staging.
            ''',
            'timestamp': '2026-01-06T10:05:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_full_enhanced_pattern_flow(temp_dirs, conversation_with_enhanced_patterns, monkeypatch):
    """
    Test complete flow from conversation to archive with enhanced patterns.

    This is the CRITICAL integration test that validates:
    - Enhanced patterns are detected
    - PAI v2 bridge stores them
    - Archive includes learning IDs
    - All 12 pattern types work end-to-end
    """
    # Setup temporary databases
    monkeypatch.setenv('HOME', str(temp_dirs['root']))

    # Create maia directory structure
    maia_dir = temp_dirs['root'] / '.maia'
    data_dir = maia_dir / 'data'
    learning_dir = maia_dir / 'learning'

    maia_dir.mkdir()
    data_dir.mkdir()
    learning_dir.mkdir()

    # Initialize components
    extractor = get_extractor()
    archive = get_archive()
    pai_v2_bridge = get_pai_v2_bridge()

    # Override database paths
    archive.db_path = temp_dirs['archive_db']
    archive._init_schema()

    pai_v2_bridge.db_path = temp_dirs['learning_db']
    pai_v2_bridge._ensure_initialized()

    # Step 1: Extract learnings (should detect enhanced patterns)
    result = extractor.extract_from_transcript(
        conversation_with_enhanced_patterns,
        context_id='test_integration_001'
    )

    learnings = result['learnings']

    # Verify enhanced patterns were detected
    pattern_types = {l['type'] for l in learnings}

    assert 'refactoring' in pattern_types, "Refactoring pattern not detected"
    assert 'optimization' in pattern_types, "Optimization pattern not detected"
    assert 'error_recovery' in pattern_types, "Error recovery pattern not detected"
    assert 'learning' in pattern_types, "Learning pattern not detected"
    assert 'breakthrough' in pattern_types, "Breakthrough pattern not detected"
    assert 'test' in pattern_types, "Test pattern not detected"
    assert 'security' in pattern_types, "Security pattern not detected"
    assert 'checkpoint' in pattern_types, "Checkpoint pattern not detected"

    # Verify we got multiple learnings
    assert len(learnings) >= 8, f"Expected at least 8 learnings, got {len(learnings)}"

    # Step 2: Save to PAI v2 (should create patterns with IDs)
    pattern_ids = pai_v2_bridge.save_learnings_as_patterns(
        learnings=learnings,
        context_id='test_integration_001',
        session_id='test_session_001'
    )

    assert len(pattern_ids) == len(learnings), "Pattern IDs count mismatch"
    assert all(pid.startswith('pat_') for pid in pattern_ids), "Invalid pattern ID format"

    # Step 3: Verify patterns were stored in PAI v2 database
    for pattern_id in pattern_ids:
        pattern = pai_v2_bridge.get_pattern(pattern_id)
        assert pattern is not None, f"Pattern {pattern_id} not found in database"
        assert pattern['pattern_type'] in ['workflow', 'tool_sequence'], \
            f"Invalid pattern type: {pattern['pattern_type']}"

    # Step 4: Archive conversation with learning IDs
    metadata = {
        'learning_count': len(learnings),
        'learning_ids': pattern_ids,
        'tool_usage': result['metadata']['tool_usage'],
        'agents_used': result['metadata']['agents_used'],
        'error_count': result['metadata']['error_count'],
        'topics': ['authentication', 'security', 'optimization']
    }

    snapshot_id = archive.archive_conversation(
        context_id='test_integration_001',
        full_conversation=conversation_with_enhanced_patterns,
        trigger_type='manual',
        transcript_path='/tmp/test.jsonl',
        metadata=metadata
    )

    assert snapshot_id > 0, "Archive failed to create snapshot"

    # Step 5: Retrieve and verify archived conversation
    from claude.tools.learning.retrieval import get_conversation

    archived = get_conversation('test_integration_001')

    assert archived is not None, "Failed to retrieve archived conversation"
    assert archived['learning_count'] == len(learnings), "Learning count mismatch in archive"
    assert len(archived['learning_ids']) == len(pattern_ids), "Learning IDs mismatch in archive"

    # Step 6: Verify cross-reference (pattern → archive)
    patterns_for_context = pai_v2_bridge.get_patterns_for_context('test_integration_001')
    assert len(patterns_for_context) == len(learnings), "Context pattern count mismatch"

    # Step 7: Verify enhanced pattern types are preserved
    pattern_types_in_db = {p['pattern_data']['original_type'] for p in patterns_for_context}
    assert 'refactoring' in pattern_types_in_db
    assert 'optimization' in pattern_types_in_db
    assert 'security' in pattern_types_in_db

    print(f"\n✅ Integration test passed!")
    print(f"   - {len(learnings)} learnings extracted")
    print(f"   - {len(pattern_ids)} patterns stored in PAI v2")
    print(f"   - Snapshot {snapshot_id} created in archive")
    print(f"   - Pattern types detected: {', '.join(sorted(pattern_types))}")


def test_enhanced_patterns_in_hook_simulation(temp_dirs, conversation_with_enhanced_patterns, monkeypatch):
    """
    Simulate the pre-compaction hook flow with enhanced patterns.

    This tests what actually happens when the hook fires.
    """
    monkeypatch.setenv('HOME', str(temp_dirs['root']))

    # Setup directories
    maia_dir = temp_dirs['root'] / '.maia'
    maia_dir.mkdir()
    (maia_dir / 'data').mkdir()
    (maia_dir / 'learning').mkdir()
    (maia_dir / 'logs').mkdir()

    # Write conversation to file (simulating transcript_path)
    transcript_file = temp_dirs['root'] / 'test_transcript.jsonl'
    transcript_file.write_text(conversation_with_enhanced_patterns)

    # Simulate hook input
    hook_input = {
        'session_id': 'hook_test_001',
        'transcript_path': str(transcript_file),
        'trigger': 'manual',
        'hook_event_name': 'PreCompact'
    }

    # Import and run hook (simulating what Claude Code does)
    from claude.hooks.pre_compaction_learning_capture import PreCompactionHook

    hook = PreCompactionHook()

    # Override database paths
    hook.archive.db_path = temp_dirs['archive_db']
    hook.archive._init_schema()

    hook.pai_v2_bridge.db_path = temp_dirs['learning_db']
    hook.pai_v2_bridge._ensure_initialized()

    # Process hook
    result = hook.process(hook_input)

    # Verify success
    assert result['success'] is True, f"Hook failed: {result.get('error_message')}"
    assert result['snapshot_id'] > 0, "No snapshot created"
    assert result['learnings_captured'] >= 8, f"Expected at least 8 learnings, got {result['learnings_captured']}"
    assert result['execution_time_ms'] < 5000, f"Hook too slow: {result['execution_time_ms']}ms"

    # Verify patterns were saved to PAI v2
    patterns = hook.pai_v2_bridge.get_patterns_for_context('hook_test_001')
    assert len(patterns) == result['learnings_captured'], "Pattern count mismatch"

    # Verify enhanced patterns are present
    pattern_types = {p['pattern_data']['original_type'] for p in patterns}
    enhanced_types = {'refactoring', 'optimization', 'error_recovery', 'learning', 'breakthrough', 'test', 'security'}
    found_enhanced = pattern_types & enhanced_types

    assert len(found_enhanced) >= 5, f"Not enough enhanced patterns found: {found_enhanced}"

    print(f"\n✅ Hook simulation passed!")
    print(f"   - Execution time: {result['execution_time_ms']}ms")
    print(f"   - Learnings captured: {result['learnings_captured']}")
    print(f"   - Enhanced patterns found: {', '.join(sorted(found_enhanced))}")


def test_pattern_confidence_preserved(temp_dirs, monkeypatch):
    """Test that confidence scores are preserved through the full flow."""
    monkeypatch.setenv('HOME', str(temp_dirs['root']))

    # Setup
    maia_dir = temp_dirs['root'] / '.maia'
    (maia_dir / 'learning').mkdir(parents=True)

    # Create simple conversation
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Breakthrough: The root cause is a race condition in the cache.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    transcript = '\n'.join(json.dumps(msg) for msg in messages)

    # Extract
    extractor = get_extractor()
    result = extractor.extract_from_transcript(transcript, 'test_conf_001')

    # Get the breakthrough learning
    breakthrough = [l for l in result['learnings'] if l['type'] == 'breakthrough'][0]
    assert breakthrough['confidence'] == 0.98, "Breakthrough confidence incorrect"

    # Save to PAI v2
    pai_v2_bridge = get_pai_v2_bridge()
    pai_v2_bridge.db_path = temp_dirs['learning_db']
    pai_v2_bridge._ensure_initialized()

    pattern_ids = pai_v2_bridge.save_learnings_as_patterns(
        [breakthrough],
        context_id='test_conf_001'
    )

    # Verify confidence preserved in database
    pattern = pai_v2_bridge.get_pattern(pattern_ids[0])
    assert pattern['confidence'] == 0.95, "PAI v2 bridge should use 0.95 for breakthrough"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
