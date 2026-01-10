#!/usr/bin/env python3
"""
Phase 3: Incremental Extraction - TDD Tests

Tests for IncrementalExtractor that processes only new messages
since the last capture (high-water mark).
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from claude.tools.learning.continuous_capture.incremental_extractor import IncrementalExtractor


class TestIncrementalExtractor:
    """Test incremental extraction of learnings from transcripts."""

    def test_extracts_only_messages_after_high_water_mark(self, tmp_path):
        """Should extract learnings only from messages after high-water mark."""
        # Create mock transcript
        transcript = tmp_path / "transcript.jsonl"
        messages = [
            {"type": "user_message", "content": "old message 1"},
            {"type": "assistant_message", "content": "decided to use SQLite because it is simpler."},
            {"type": "user_message", "content": "new message 1"},
            {"type": "assistant_message", "content": "fixed the bug by adding validation."},
            {"type": "user_message", "content": "new message 2"},
            {"type": "assistant_message", "content": "discovered that hooks don't fire."}
        ]

        with open(transcript, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        # Extract from high-water mark 2 (skip first 2 messages)
        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=2,
            end_index=6
        )

        # Should only extract from messages 2-5 (new messages)
        assert len(learnings) > 0, "Should extract learnings from new messages"

        # Verify no learnings from old messages
        contents = [l['content'] for l in learnings]
        assert not any('SQLite' in c for c in contents), "Should not extract from old messages"

        # Verify learnings from new messages
        assert any('bug' in c or 'validation' in c for c in contents), "Should extract from new message 1"

    def test_returns_empty_when_no_new_messages(self, tmp_path):
        """Should return empty list when high-water mark equals end index."""
        transcript = tmp_path / "transcript.jsonl"
        messages = [
            {"type": "user_message", "content": "message 1"},
            {"type": "assistant_message", "content": "response 1"}
        ]

        with open(transcript, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        extractor = IncrementalExtractor()

        # Start == End (no new messages)
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=2,
            end_index=2
        )

        assert learnings == [], "Should return empty when no new messages"

    def test_handles_empty_transcript(self, tmp_path):
        """Should handle empty transcript gracefully."""
        transcript = tmp_path / "empty.jsonl"
        transcript.touch()  # Create empty file

        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=0,
            end_index=10
        )

        assert learnings == [], "Should return empty for empty transcript"

    def test_handles_malformed_messages_gracefully(self, tmp_path):
        """Should skip malformed messages without crashing."""
        transcript = tmp_path / "malformed.jsonl"

        with open(transcript, 'w') as f:
            f.write('{"type": "user_message", "content": "valid message"}\n')
            f.write('not valid json\n')  # Malformed
            f.write('{"type": "assistant_message"}\n')  # Missing content
            f.write('{"type": "assistant_message", "content": "fixed by retry logic"}\n')

        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=0,
            end_index=10
        )

        # Should extract from valid messages, skip malformed
        assert isinstance(learnings, list), "Should return list"
        # May or may not have learnings, but shouldn't crash

    def test_handles_nonexistent_transcript(self, tmp_path):
        """Should handle missing transcript file gracefully."""
        nonexistent = tmp_path / "does_not_exist.jsonl"

        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=nonexistent,
            start_index=0,
            end_index=10
        )

        assert learnings == [], "Should return empty for nonexistent file"


class TestExtractionPatternIntegration:
    """Test integration with existing extraction patterns."""

    def test_uses_all_12_pattern_types(self, tmp_path):
        """Should use all 12 pattern types from extraction.py."""
        from claude.tools.learning.continuous_capture.incremental_extractor import PATTERN_TYPES

        # Verify all 12 types are available
        expected_types = {
            'decision', 'solution', 'outcome', 'handoff', 'checkpoint',
            'refactoring', 'error_recovery', 'optimization', 'learning',
            'breakthrough', 'test', 'security'
        }

        assert set(PATTERN_TYPES) == expected_types, "Should have all 12 pattern types"

    def test_extraction_returns_structured_learnings(self, tmp_path):
        """Extracted learnings should have proper structure."""
        transcript = tmp_path / "structured.jsonl"

        # Create transcript with different pattern types
        messages = [
            {"type": "assistant_message", "content": "decided to use queue-based architecture"},
            {"type": "assistant_message", "content": "fixed the bug by adding retry logic"},
            {"type": "assistant_message", "content": "discovered that PreCompact hooks don't work"},
            {"type": "assistant_message", "content": "optimized from 2s to 50ms by using index"},
        ]

        with open(transcript, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=0,
            end_index=len(messages)
        )

        # Verify structure
        for learning in learnings:
            assert 'type' in learning, "Learning should have 'type'"
            assert 'content' in learning, "Learning should have 'content'"
            assert 'timestamp' in learning, "Learning should have 'timestamp'"
            assert 'context' in learning, "Learning should have 'context'"

            # Type should be one of the 12 pattern types
            assert learning['type'] in {
                'decision', 'solution', 'outcome', 'handoff', 'checkpoint',
                'refactoring', 'error_recovery', 'optimization', 'learning',
                'breakthrough', 'test', 'security'
            }

    def test_extracts_multiple_pattern_types(self, tmp_path):
        """Should detect and extract multiple different pattern types."""
        transcript = tmp_path / "multi_pattern.jsonl"

        messages = [
            {"type": "assistant_message", "content": "Decided to implement continuous capture instead of hook-based"},  # decision
            {"type": "assistant_message", "content": "Fixed the sqlite3.Connection bug by using connect()"},  # solution
            {"type": "assistant_message", "content": "Discovered that learning capture rate was only 1.9%"},  # breakthrough/learning
            {"type": "assistant_message", "content": "Optimized extraction from 2s to 100ms using incremental approach"},  # optimization
            {"type": "assistant_message", "content": "Tests passed: 11/11 in test_state_manager.py"},  # test
        ]

        with open(transcript, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=0,
            end_index=len(messages)
        )

        # Should extract multiple types
        assert len(learnings) > 0, "Should extract learnings"

        # Check variety of types
        types_found = {l['type'] for l in learnings}
        assert len(types_found) > 1, "Should extract multiple pattern types"

    def test_context_metadata_included(self, tmp_path):
        """Extracted learnings should include context metadata."""
        transcript = tmp_path / "context_test.jsonl"

        messages = [
            {"type": "assistant_message", "content": "fixed issue with TDD implementation"}
        ]

        with open(transcript, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')

        extractor = IncrementalExtractor()
        learnings = extractor.extract_from_transcript(
            transcript_path=transcript,
            start_index=0,
            end_index=1,
            context_id="test_ctx_789",
            agent="sre_principal_engineer_agent"
        )

        if learnings:
            learning = learnings[0]
            assert 'context' in learning
            # Context may contain agent, context_id, etc
            context = learning['context']
            assert isinstance(context, dict)
