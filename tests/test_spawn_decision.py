"""
Tests for spawn decision engine.

Tests spawn logic that determines when to delegate to a subagent.
"""

import pytest
from pathlib import Path
from claude.tools.orchestration.spawn_decision import (
    SpawnDecisionEngine,
    SpawnReason,
    NoSpawnReason,
    SpawnDecision,
)


class TestSpawnDecisionEngine:
    """Unit tests for SpawnDecisionEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = SpawnDecisionEngine()

    def test_exploration_query_spawns(self):
        """Test that 'how does X work' triggers spawn."""
        query = "how does the authentication system work?"
        result = self.engine.analyze(query, {}, [])

        assert result.should_spawn is True
        assert result.reason == SpawnReason.MULTI_FILE_EXPLORATION
        assert result.confidence >= 0.7
        assert "how does" in result.explanation.lower()

    def test_find_query_spawns(self):
        """Test that 'find all X' triggers spawn."""
        query = "find all database connection files"
        result = self.engine.analyze(query, {}, [])

        assert result.should_spawn is True
        assert result.reason == SpawnReason.MULTI_FILE_EXPLORATION
        assert result.confidence >= 0.7
        assert "find" in result.explanation.lower()

    def test_analyze_query_spawns(self):
        """Test that 'analyze X' triggers spawn."""
        query = "analyze the API error handling patterns"
        result = self.engine.analyze(query, {}, [])

        assert result.should_spawn is True
        assert result.reason == SpawnReason.MULTI_FILE_EXPLORATION
        assert result.confidence >= 0.7
        assert "analyze" in result.explanation.lower()

    def test_simple_edit_no_spawn(self):
        """Test that 'edit file X' does NOT spawn."""
        query = "edit the config.py file to add new setting"
        result = self.engine.analyze(query, {}, ["config.py"])

        assert result.should_spawn is False
        assert result.reason == NoSpawnReason.DIRECT_EDIT
        assert result.confidence >= 0.7
        assert "edit" in result.explanation.lower()

    def test_read_specific_file_no_spawn(self):
        """Test that 'read file X' does NOT spawn."""
        query = "read the README.md file"
        result = self.engine.analyze(query, {}, ["README.md"])

        assert result.should_spawn is False
        assert result.reason == NoSpawnReason.SPECIFIC_FILE_KNOWN
        assert result.confidence >= 0.7

    def test_single_command_no_spawn(self):
        """Test that 'run pytest' does NOT spawn."""
        query = "run pytest on the tests directory"
        result = self.engine.analyze(query, {}, [])

        assert result.should_spawn is False
        assert result.reason == NoSpawnReason.SINGLE_COMMAND
        assert result.confidence >= 0.7
        assert "command" in result.explanation.lower()

    def test_sprint_mode_biases_spawn(self):
        """Test that sprint_mode=True increases spawn likelihood."""
        query = "update the database schema"

        # Without sprint mode
        result_no_sprint = self.engine.analyze(query, {}, [])

        # With sprint mode
        result_with_sprint = self.engine.analyze(
            query,
            {"sprint_mode": True},
            []
        )

        assert result_with_sprint.should_spawn is True
        assert result_with_sprint.reason == SpawnReason.SPRINT_MODE_ACTIVE
        assert result_with_sprint.confidence >= 0.8

    def test_multiple_files_triggers_spawn(self):
        """Test that >3 files mentioned triggers spawn."""
        query = "update these files for consistency"
        files = ["file1.py", "file2.py", "file3.py", "file4.py"]
        result = self.engine.analyze(query, {}, files)

        assert result.should_spawn is True
        assert result.reason == SpawnReason.MULTI_FILE_EXPLORATION
        assert result.confidence >= 0.7
        assert "multiple files" in result.explanation.lower()

    def test_agent_recommendation_sre_for_infra(self):
        """Test that infrastructure queries recommend SRE agent."""
        query = "analyze the terraform infrastructure setup"
        result = self.engine.analyze(query, {}, [])

        assert result.should_spawn is True
        assert "sre" in result.recommended_agent.lower()

    def test_agent_recommendation_security_for_auth(self):
        """Test that auth/security queries recommend security agent."""
        query = "review the authentication and authorization flow"
        result = self.engine.analyze(query, {}, [])

        assert result.should_spawn is True
        assert "security" in result.recommended_agent.lower()

    def test_confidence_high_for_clear_patterns(self):
        """Test that clear patterns have high confidence."""
        query = "how does the system work?"
        result = self.engine.analyze(query, {}, [])

        assert result.confidence >= 0.8
        assert result.should_spawn is True

    def test_confidence_medium_for_ambiguous(self):
        """Test that ambiguous queries have medium confidence."""
        query = "what about the configuration?"
        result = self.engine.analyze(query, {}, [])

        # This is ambiguous - could go either way
        # Confidence should reflect uncertainty
        assert 0.4 <= result.confidence <= 0.7


class TestSpawnDecisionIntegration:
    """Integration tests for spawn decision with real session data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = SpawnDecisionEngine()

    def test_with_real_session_file(self):
        """Test with actual session state structure."""
        session_context = {
            "session_id": "test-session-123",
            "agent_used": "sre_principal_engineer_agent",
            "initial_query": "analyze system architecture",
            "sprint_mode": False,
            "working_directory": "/Users/test/maia",
        }

        query = "how does the learning system work?"
        result = self.engine.analyze(query, session_context, [])

        assert result.should_spawn is True
        assert result.recommended_agent is not None
        assert result.explanation is not None

    def test_sprint_mode_from_session(self):
        """Test sprint mode detection from session context."""
        session_context = {
            "session_id": "test-session-456",
            "sprint_mode": True,
        }

        query = "implement new feature"
        result = self.engine.analyze(query, session_context, [])

        assert result.should_spawn is True
        assert result.reason == SpawnReason.SPRINT_MODE_ACTIVE
        assert "sprint" in result.explanation.lower()
