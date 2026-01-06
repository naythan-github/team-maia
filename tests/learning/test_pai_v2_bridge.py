#!/usr/bin/env python3
"""
Tests for PAI v2 Bridge

Phase 237 Phase 2: Learning ID tracking integration
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from claude.tools.learning.pai_v2_bridge import (
    PAIv2Bridge,
    get_pai_v2_bridge,
    LEARNING_TYPE_MAPPING
)


@pytest.fixture
def temp_db_path():
    """Create temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_learning.db"
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def bridge(temp_db_path, monkeypatch):
    """Create PAI v2 bridge with temporary database."""
    monkeypatch.setattr(
        'claude.tools.learning.pai_v2_bridge.PAIv2Bridge.db_path',
        temp_db_path,
        raising=False
    )
    bridge = PAIv2Bridge()
    bridge.db_path = temp_db_path
    bridge._ensure_initialized()
    return bridge


@pytest.fixture
def sample_learnings():
    """Sample learnings from extraction engine."""
    return [
        {
            'type': 'decision',
            'content': 'chose SQLite over Postgres because simpler deployment',
            'timestamp': '2026-01-06T10:30:00Z',
            'context': {
                'surrounding_messages': [],
                'active_agent': 'sre_principal_engineer_agent',
                'tools_used': ['Read', 'Edit']
            }
        },
        {
            'type': 'solution',
            'content': 'fixed database lock by adding retry logic with exponential backoff',
            'timestamp': '2026-01-06T10:35:00Z',
            'context': {
                'surrounding_messages': [],
                'active_agent': 'sre_principal_engineer_agent',
                'tools_used': ['Edit', 'Bash']
            }
        },
        {
            'type': 'outcome',
            'content': 'tests passing after fix deployment',
            'timestamp': '2026-01-06T10:40:00Z',
            'context': {
                'surrounding_messages': [],
                'active_agent': 'sre_principal_engineer_agent',
                'tools_used': ['Bash']
            }
        }
    ]


class TestLearningTypeMapping:
    """Test learning type to pattern type mapping."""

    def test_decision_maps_to_workflow(self):
        assert LEARNING_TYPE_MAPPING['decision'] == 'workflow'

    def test_solution_maps_to_tool_sequence(self):
        assert LEARNING_TYPE_MAPPING['solution'] == 'tool_sequence'

    def test_outcome_maps_to_workflow(self):
        assert LEARNING_TYPE_MAPPING['outcome'] == 'workflow'

    def test_handoff_maps_to_workflow(self):
        assert LEARNING_TYPE_MAPPING['handoff'] == 'workflow'

    def test_checkpoint_maps_to_workflow(self):
        assert LEARNING_TYPE_MAPPING['checkpoint'] == 'workflow'


class TestPAIv2Bridge:
    """Test PAI v2 bridge functionality."""

    def test_save_empty_learnings(self, bridge):
        """Test saving empty learnings list."""
        pattern_ids = bridge.save_learnings_as_patterns([], 'ctx_123')
        assert pattern_ids == []

    def test_save_single_learning(self, bridge, sample_learnings):
        """Test saving a single learning."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [sample_learnings[0]],
            context_id='ctx_123'
        )

        assert len(pattern_ids) == 1
        assert pattern_ids[0].startswith('pat_')

    def test_save_multiple_learnings(self, bridge, sample_learnings):
        """Test saving multiple learnings."""
        pattern_ids = bridge.save_learnings_as_patterns(
            sample_learnings,
            context_id='ctx_123'
        )

        assert len(pattern_ids) == 3
        assert all(pid.startswith('pat_') for pid in pattern_ids)
        assert len(set(pattern_ids)) == 3  # All unique

    def test_pattern_id_format(self, bridge, sample_learnings):
        """Test pattern ID format."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [sample_learnings[0]],
            context_id='ctx_123'
        )

        pattern_id = pattern_ids[0]
        assert pattern_id.startswith('pat_')
        assert len(pattern_id) == 16  # pat_ + 12 hex chars

    def test_retrieve_saved_pattern(self, bridge, sample_learnings):
        """Test retrieving a saved pattern."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [sample_learnings[0]],
            context_id='ctx_123'
        )

        pattern = bridge.get_pattern(pattern_ids[0])

        assert pattern is not None
        assert pattern['id'] == pattern_ids[0]
        assert pattern['pattern_type'] == 'workflow'  # decision → workflow
        assert pattern['description'] == sample_learnings[0]['content']
        assert pattern['confidence'] == 0.8  # decision confidence

    def test_pattern_contains_context(self, bridge, sample_learnings):
        """Test pattern stores original context."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [sample_learnings[0]],
            context_id='ctx_123'
        )

        pattern = bridge.get_pattern(pattern_ids[0])
        pattern_data = pattern['pattern_data']

        assert pattern_data['context_id'] == 'ctx_123'
        assert pattern_data['original_type'] == 'decision'
        assert 'context' in pattern_data
        assert pattern_data['context']['active_agent'] == 'sre_principal_engineer_agent'

    def test_pattern_confidence_mapping(self, bridge):
        """Test confidence assigned based on learning type."""
        test_cases = [
            ('decision', 0.8),
            ('solution', 0.9),
            ('outcome', 0.7),
            ('handoff', 0.6),
            ('checkpoint', 0.5),
        ]

        for learning_type, expected_confidence in test_cases:
            pattern_ids = bridge.save_learnings_as_patterns(
                [{
                    'type': learning_type,
                    'content': f'test {learning_type}',
                    'timestamp': datetime.now().isoformat(),
                    'context': {}
                }],
                context_id=f'ctx_{learning_type}'
            )

            pattern = bridge.get_pattern(pattern_ids[0])
            assert pattern['confidence'] == expected_confidence, \
                f"Expected confidence {expected_confidence} for {learning_type}"

    def test_get_patterns_for_context(self, bridge, sample_learnings):
        """Test retrieving all patterns for a context."""
        # Save learnings for context_1
        pattern_ids_1 = bridge.save_learnings_as_patterns(
            sample_learnings[:2],
            context_id='ctx_1'
        )

        # Save learnings for context_2
        pattern_ids_2 = bridge.save_learnings_as_patterns(
            [sample_learnings[2]],
            context_id='ctx_2'
        )

        # Retrieve patterns for context_1
        patterns = bridge.get_patterns_for_context('ctx_1')

        assert len(patterns) == 2
        pattern_ids_retrieved = [p['id'] for p in patterns]
        assert set(pattern_ids_retrieved) == set(pattern_ids_1)

    def test_pattern_with_session_id(self, bridge):
        """Test saving pattern with session ID."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [{
                'type': 'decision',
                'content': 'test decision',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }],
            context_id='ctx_123',
            session_id='s_20260106_abc123'
        )

        pattern = bridge.get_pattern(pattern_ids[0])
        assert pattern['pattern_data']['session_id'] == 's_20260106_abc123'

    def test_pattern_with_domain(self, bridge):
        """Test saving pattern with domain."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [{
                'type': 'solution',
                'content': 'implemented retry logic',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }],
            context_id='ctx_123',
            domain='infrastructure'
        )

        pattern = bridge.get_pattern(pattern_ids[0])
        assert pattern['domain'] == 'infrastructure'

    def test_get_nonexistent_pattern(self, bridge):
        """Test retrieving non-existent pattern."""
        pattern = bridge.get_pattern('pat_nonexistent')
        assert pattern is None

    def test_save_learning_error_handling(self, bridge):
        """Test graceful handling of learnings with missing fields."""
        # Learning with missing fields - should handle gracefully
        invalid_learnings = [{}]

        # Should not raise - graceful degradation
        pattern_ids = bridge.save_learnings_as_patterns(
            invalid_learnings,
            context_id='ctx_123'
        )

        assert len(pattern_ids) == 1  # Still creates pattern
        pattern = bridge.get_pattern(pattern_ids[0])
        assert pattern['description'] == ''  # Empty description for missing content

    def test_pattern_timestamps(self, bridge):
        """Test pattern first_seen and last_seen timestamps."""
        pattern_ids = bridge.save_learnings_as_patterns(
            [{
                'type': 'decision',
                'content': 'test decision',
                'timestamp': '2026-01-06T10:30:00Z',
                'context': {}
            }],
            context_id='ctx_123'
        )

        pattern = bridge.get_pattern(pattern_ids[0])
        assert pattern['first_seen'] == '2026-01-06T10:30:00Z'
        assert pattern['last_seen'] == '2026-01-06T10:30:00Z'
        assert pattern['occurrence_count'] == 1

    def test_multiple_patterns_same_context(self, bridge):
        """Test multiple patterns can be saved for same context."""
        # Save first batch
        pattern_ids_1 = bridge.save_learnings_as_patterns(
            [{
                'type': 'decision',
                'content': 'first decision',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }],
            context_id='ctx_123'
        )

        # Save second batch for same context
        pattern_ids_2 = bridge.save_learnings_as_patterns(
            [{
                'type': 'solution',
                'content': 'second solution',
                'timestamp': datetime.now().isoformat(),
                'context': {}
            }],
            context_id='ctx_123'
        )

        # Both should be retrievable
        patterns = bridge.get_patterns_for_context('ctx_123')
        assert len(patterns) == 2


class TestSingleton:
    """Test singleton pattern for bridge."""

    def test_get_pai_v2_bridge_singleton(self):
        """Test bridge singleton returns same instance."""
        bridge1 = get_pai_v2_bridge()
        bridge2 = get_pai_v2_bridge()

        assert bridge1 is bridge2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
