"""
Tests for SubagentPromptBuilder - TDD first.

Sprint: SPRINT-003-SWARM-TASK-ORCHESTRATION
Phase: P1 - Subagent Prompt Builder

These tests define the expected behavior before implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSubagentPromptBuilder:
    """Unit tests for SubagentPromptBuilder."""

    def test_build_basic_prompt(self, tmp_path):
        """Test basic prompt building with agent injection."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
            SubagentPrompt,
        )

        # Create a mock agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test_agent.md").write_text(
            "# Test Agent\n\n## Purpose\nTest agent for testing."
        )

        # Given: agent name and task
        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # When: build() called
        result = builder.build("test_agent", "analyze the codebase")

        # Then: prompt contains agent content + task
        assert isinstance(result, SubagentPrompt)
        assert "Test Agent" in result.prompt
        assert "analyze the codebase" in result.prompt
        assert result.agent_name == "test_agent"
        assert result.total_tokens > 0

    def test_build_with_additional_context(self, tmp_path):
        """Test prompt with extra context included."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create a mock agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test_agent.md").write_text("# Test Agent\n\nAgent content.")

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # When: build with additional context
        result = builder.build(
            "test_agent",
            "analyze this file",
            additional_context="File content:\n```\ndef foo(): pass\n```",
        )

        # Then: prompt contains additional context
        assert "def foo(): pass" in result.prompt
        assert "analyze this file" in result.prompt

    def test_build_with_output_format(self, tmp_path):
        """Test prompt with specified output format."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create a mock agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test_agent.md").write_text("# Test Agent\n\nAgent content.")

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # When: build with output format
        result = builder.build(
            "test_agent", "list all functions", output_format="JSON array"
        )

        # Then: prompt contains output format instruction
        assert "JSON array" in result.prompt

    def test_agent_not_found_error(self, tmp_path):
        """Test graceful error when agent doesn't exist."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
            AgentNotFoundError,
        )

        # Create empty agents dir
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # When/Then: non-existent agent raises error
        with pytest.raises(AgentNotFoundError) as exc_info:
            builder.build("nonexistent_agent", "do something")

        assert "nonexistent_agent" in str(exc_info.value)

    def test_agent_name_normalization(self, tmp_path):
        """Test that agent name variants resolve correctly."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create agent files
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "sre_principal_engineer_agent.md").write_text(
            "# SRE Principal Engineer\n\nSRE content."
        )

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # Test various name formats all resolve
        result1 = builder.build("sre_principal_engineer_agent", "test task")
        result2 = builder.build("sre_principal_engineer", "test task")
        result3 = builder.build("sre", "test task")

        # All should find the same agent
        assert "SRE Principal Engineer" in result1.prompt
        assert "SRE Principal Engineer" in result2.prompt
        # Note: "sre" alone may not resolve - depends on implementation choice
        # This test documents expected behavior

    def test_token_estimation(self, tmp_path):
        """Test token count estimation is reasonable."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create agent file with known content
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent_content = "# Test\n" * 100  # ~700 chars
        (agents_dir / "test_agent.md").write_text(agent_content)

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        result = builder.build("test_agent", "short task")

        # Token estimate should be roughly chars/4
        # Agent ~700 chars + task ~10 chars + template overhead
        assert result.agent_tokens > 100  # Agent content
        assert result.task_tokens > 0  # Task content
        assert result.total_tokens == result.agent_tokens + result.task_tokens

    def test_model_recommendation_small_task(self, tmp_path):
        """Test haiku recommended for small tasks."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create small agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test_agent.md").write_text("# Small Agent\nMinimal content.")

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        result = builder.build("test_agent", "list files")

        # Small task + small agent should recommend haiku
        assert result.model_recommendation == "haiku"

    def test_model_recommendation_large_task(self, tmp_path):
        """Test sonnet/opus for large tasks."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create large agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        large_content = "# Large Agent\n\n" + ("## Section\n" + "Content.\n" * 100) * 20
        (agents_dir / "large_agent.md").write_text(large_content)

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # Large task
        large_task = "Analyze " + "the system " * 500

        result = builder.build("large_agent", large_task)

        # Large task should recommend sonnet or opus
        assert result.model_recommendation in ["sonnet", "opus"]

    def test_prompt_structure(self, tmp_path):
        """Test prompt has correct sections: Agent Context, Task, Output Format."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test_agent.md").write_text("# Test Agent\n\nAgent content here.")

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        result = builder.build(
            "test_agent", "analyze the code", output_format="markdown report"
        )

        # Verify structural markers exist
        assert "## Agent Context" in result.prompt or "# Agent Context" in result.prompt
        assert "## Task" in result.prompt or "# Task" in result.prompt
        # Output format section should be present when specified
        assert "markdown report" in result.prompt

    def test_agent_is_directory_error(self, tmp_path):
        """Test graceful error when agent path is a directory."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
            AgentNotFoundError,
        )

        # Create agents dir with a directory named like an agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "dir_agent.md").mkdir()  # Directory, not file

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # Should raise AgentNotFoundError (not IsADirectoryError)
        with pytest.raises(AgentNotFoundError) as exc_info:
            builder.build("dir_agent", "do something")

        assert "directory" in str(exc_info.value).lower()

    def test_agent_permission_error(self, tmp_path):
        """Test graceful error when agent file has permission issues."""
        import os
        import stat
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
            AgentNotFoundError,
        )

        # Create agents dir with unreadable file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent_file = agents_dir / "unreadable_agent.md"
        agent_file.write_text("# Unreadable Agent")

        # Remove read permissions
        original_mode = agent_file.stat().st_mode
        try:
            agent_file.chmod(0o000)

            builder = SubagentPromptBuilder(agents_dir=agents_dir)

            # Should raise AgentNotFoundError (not PermissionError)
            with pytest.raises(AgentNotFoundError) as exc_info:
                builder.build("unreadable_agent", "do something")

            assert "permission" in str(exc_info.value).lower()
        finally:
            # Restore permissions for cleanup
            agent_file.chmod(original_mode)

    def test_agent_empty_file(self, tmp_path):
        """Test handling of empty agent files."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        # Create empty agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "empty_agent.md").write_text("")

        builder = SubagentPromptBuilder(agents_dir=agents_dir)

        # Should succeed but with minimal content
        result = builder.build("empty_agent", "do something")

        # Prompt should still have structure
        assert "## Agent Context" in result.prompt
        assert "## Task" in result.prompt
        assert "do something" in result.prompt
        # Agent tokens should be minimal (empty content = 1 token minimum)
        assert result.agent_tokens >= 1


class TestSubagentPromptBuilderIntegration:
    """Integration tests with real agent files."""

    @pytest.fixture
    def real_agents_dir(self):
        """Return the real agents directory."""
        # Use MAIA_ROOT to find agents
        from claude.tools.core.paths import MAIA_ROOT

        return MAIA_ROOT / "claude" / "agents"

    def test_build_with_real_sre_agent(self, real_agents_dir):
        """Test building prompt with actual SRE agent file."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        if not real_agents_dir.exists():
            pytest.skip("Agents directory not found")

        builder = SubagentPromptBuilder(agents_dir=real_agents_dir)

        result = builder.build(
            "sre_principal_engineer_agent", "analyze the monitoring setup"
        )

        # Should contain SRE-specific content
        assert "SRE" in result.prompt or "reliability" in result.prompt.lower()
        assert "analyze the monitoring setup" in result.prompt
        assert result.total_tokens > 1000  # SRE agent is substantial

    def test_build_with_real_security_agent(self, real_agents_dir):
        """Test building prompt with actual security agent file."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        if not real_agents_dir.exists():
            pytest.skip("Agents directory not found")

        builder = SubagentPromptBuilder(agents_dir=real_agents_dir)

        result = builder.build(
            "cloud_security_principal_agent", "review authentication flow"
        )

        # Should contain security-specific content
        assert "security" in result.prompt.lower()
        assert "review authentication flow" in result.prompt

    def test_all_agents_loadable(self, real_agents_dir):
        """Test that all agents in directory can be loaded."""
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        if not real_agents_dir.exists():
            pytest.skip("Agents directory not found")

        builder = SubagentPromptBuilder(agents_dir=real_agents_dir)

        # Get all agent files
        agent_files = list(real_agents_dir.glob("*_agent.md"))

        # Should have agents
        assert len(agent_files) > 0, "No agent files found"

        # Try loading each one
        errors = []
        for agent_file in agent_files:
            agent_name = agent_file.stem  # e.g., "sre_principal_engineer_agent"
            try:
                result = builder.build(agent_name, "test task")
                assert result.prompt, f"Empty prompt for {agent_name}"
            except Exception as e:
                errors.append(f"{agent_name}: {e}")

        # Report any errors
        if errors:
            pytest.fail(f"Failed to load agents:\n" + "\n".join(errors[:5]))


class TestSubagentPromptIntegrationStructure:
    """Integration test validating prompt structure works with Task tool."""

    @pytest.fixture
    def real_agents_dir(self):
        """Return the real agents directory."""
        from claude.tools.core.paths import MAIA_ROOT

        return MAIA_ROOT / "claude" / "agents"

    def test_integration_task_prompt_works(self, real_agents_dir):
        """
        Integration test: Built prompt works with Task tool.

        NOTE: This test validates the prompt structure.
        Actual Task execution happens in Claude, not pytest.
        """
        from claude.tools.orchestration.subagent_prompt_builder import (
            SubagentPromptBuilder,
        )

        if not real_agents_dir.exists():
            pytest.skip("Agents directory not found")

        builder = SubagentPromptBuilder(agents_dir=real_agents_dir)
        result = builder.build(
            agent_name="sre_principal_engineer_agent",
            task="List the top 3 Python files by size in claude/tools/",
            output_format="JSON array of {file, size_bytes}",
        )

        # Validate structure
        assert "SRE" in result.prompt or "Principal" in result.prompt
        assert "List the top 3 Python files" in result.prompt
        assert "JSON array" in result.prompt
        assert result.model_recommendation in ["haiku", "sonnet", "opus"]
        assert result.total_tokens > 0
