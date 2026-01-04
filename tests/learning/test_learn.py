#!/usr/bin/env python3
"""
Tests for Phase 5: LEARN Phase (TDD)

Tests pattern extraction and preference learning.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch


class TestLearnPhaseBasic:
    """Tests for basic LEARN functionality."""

    def test_learn_returns_insights_list(self):
        """Test that learn returns a list of LearningInsight."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
                }

                insights = learn.learn(
                    session_id="test_session",
                    uocs_summary=uocs_summary,
                    session_data={'domain': 'sre', 'agent_used': 'sre_agent'},
                    verify_success=True
                )

                assert isinstance(insights, list)

    def test_learn_only_from_successful_sessions(self):
        """Test that learn only extracts from successful sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 10}
                }

                # Failed session should not produce insights
                insights = learn.learn(
                    session_id="failed_session",
                    uocs_summary=uocs_summary,
                    session_data={},
                    verify_success=False
                )

                assert len(insights) == 0

    def test_learn_extracts_from_successful_sessions(self):
        """Test that learn extracts insights from successful sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
                }

                insights = learn.learn(
                    session_id="success_session",
                    uocs_summary=uocs_summary,
                    session_data={'domain': 'sre'},
                    verify_success=True
                )

                assert len(insights) > 0


class TestToolSequencePatterns:
    """Tests for tool sequence pattern extraction."""

    def test_extracts_tool_sequence_pattern(self):
        """Test that tool sequence patterns are extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
                }

                insights = learn.learn(
                    session_id="test",
                    uocs_summary=uocs_summary,
                    session_data={},
                    verify_success=True
                )

                tool_sequence_insights = [i for i in insights if i.insight_type == 'tool_sequence']
                assert len(tool_sequence_insights) > 0

    def test_tool_sequence_contains_tools(self):
        """Test that tool sequence pattern contains tool list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
                }

                insights = learn.learn(
                    session_id="test",
                    uocs_summary=uocs_summary,
                    session_data={},
                    verify_success=True
                )

                tool_sequence = next((i for i in insights if i.insight_type == 'tool_sequence'), None)
                assert tool_sequence is not None
                assert 'sequence' in tool_sequence.data
                assert 'bash' in tool_sequence.data['sequence']


class TestDomainPatterns:
    """Tests for domain pattern extraction."""

    def test_extracts_domain_pattern(self):
        """Test that domain workflow patterns are extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5}
                }

                insights = learn.learn(
                    session_id="test",
                    uocs_summary=uocs_summary,
                    session_data={'domain': 'security', 'agent_used': 'security_agent'},
                    verify_success=True
                )

                workflow_insights = [i for i in insights if i.insight_type == 'workflow']
                assert len(workflow_insights) > 0
                assert workflow_insights[0].domain == 'security'


class TestPatternStorage:
    """Tests for pattern storage in database."""

    def test_patterns_stored_in_database(self):
        """Test that patterns are stored in the learning database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5, 'read': 3}
                }

                learn.learn(
                    session_id="test",
                    uocs_summary=uocs_summary,
                    session_data={'domain': 'sre'},
                    verify_success=True
                )

                # Check patterns are retrievable
                patterns = learn.get_patterns()
                assert len(patterns) > 0

    def test_pattern_confidence_increases_with_occurrences(self):
        """Test that pattern confidence increases with repeated occurrences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5}
                }

                # Learn from first session
                learn.learn("s1", uocs_summary, {'domain': 'sre'}, True)
                patterns_1 = learn.get_patterns(domain='sre')
                conf_1 = patterns_1[0]['confidence'] if patterns_1 else 0

                # Learn from second session (same pattern)
                learn.learn("s2", uocs_summary, {'domain': 'sre'}, True)
                patterns_2 = learn.get_patterns(domain='sre')
                conf_2 = patterns_2[0]['confidence'] if patterns_2 else 0

                assert conf_2 > conf_1


class TestPreferences:
    """Tests for preference recording."""

    def test_record_preference(self):
        """Test that preferences can be recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                learn.record_preference(
                    category='coding_style',
                    key='indentation',
                    value='4 spaces',
                    session_id='test_session'
                )

                prefs = learn.get_preferences(category='coding_style')
                assert 'coding_style' in prefs
                assert 'indentation' in prefs['coding_style']
                assert prefs['coding_style']['indentation']['value'] == '4 spaces'

    def test_preference_confidence_increases(self):
        """Test that preference confidence increases with more evidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                # Record same preference multiple times
                learn.record_preference('style', 'tabs', 'spaces', 's1')
                prefs_1 = learn.get_preferences('style')
                conf_1 = prefs_1['style']['tabs']['confidence']

                learn.record_preference('style', 'tabs', 'spaces', 's2')
                prefs_2 = learn.get_preferences('style')
                conf_2 = prefs_2['style']['tabs']['confidence']

                assert conf_2 > conf_1


class TestLearnToDict:
    """Tests for LearningInsight serialization."""

    def test_to_dict_returns_list(self):
        """Test that to_dict returns a list of dicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5}
                }

                insights = learn.learn("test", uocs_summary, {'domain': 'sre'}, True)
                result = learn.to_dict(insights)

                assert isinstance(result, list)
                if result:
                    assert isinstance(result[0], dict)

    def test_to_dict_serializable(self):
        """Test that to_dict result is JSON serializable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.learn import LearnPhase

                learn = LearnPhase()

                uocs_summary = {
                    'total_captures': 10,
                    'success_rate': 0.9,
                    'tools_used': {'bash': 5}
                }

                insights = learn.learn("test", uocs_summary, {}, True)
                result = learn.to_dict(insights)

                # Should not raise
                json_str = json.dumps(result)
                assert json_str is not None


class TestLearnSingleton:
    """Tests for LEARN singleton pattern."""

    def test_get_learn_returns_singleton(self):
        """Test that get_learn returns same instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                import claude.tools.learning.learn as learn_module
                learn_module._learn = None  # Reset singleton

                from claude.tools.learning.learn import get_learn

                l1 = get_learn()
                l2 = get_learn()

                assert l1 is l2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
