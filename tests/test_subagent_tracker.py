"""Tests for SubagentTracker - SPRINT-003 Phase 3."""

import json
import pytest
import time
from pathlib import Path
from claude.tools.orchestration.subagent_tracker import (
    SubagentExecution,
    SubagentChain,
    SubagentTracker,
)


class TestSubagentTracker:
    """Unit tests for SubagentTracker."""

    def test_start_execution_creates_record(self, tmp_path):
        """Test that starting an execution creates a record."""
        tracker = SubagentTracker(context_id="test_001", session_dir=tmp_path)
        exec_id = tracker.start_execution(
            agent="security_analyst_agent",
            task="Analyze authentication flow",
            model="sonnet",
        )

        assert exec_id.startswith("exec_")
        assert len(exec_id) == 13  # exec_ + 8 char uuid

        chain = tracker.get_chain()
        assert chain.total_executions == 1
        assert len(chain.executions) == 1
        assert chain.executions[0].agent_injected == "security_analyst_agent"
        assert chain.executions[0].task_summary == "Analyze authentication flow"
        assert chain.executions[0].model_used == "sonnet"

    def test_complete_execution_updates_record(self, tmp_path):
        """Test that completing an execution updates the record."""
        tracker = SubagentTracker(context_id="test_002", session_dir=tmp_path)
        exec_id = tracker.start_execution(
            agent="sre_principal_engineer_agent",
            task="Deploy infrastructure",
            model="opus",
        )

        tracker.complete_execution(
            exec_id=exec_id,
            result_summary="Infrastructure deployed successfully",
            handoff_target=None,
            duration_seconds=45.2,
        )

        chain = tracker.get_chain()
        execution = chain.executions[0]
        assert execution.result_summary == "Infrastructure deployed successfully"
        assert execution.duration_seconds == 45.2
        assert execution.handoff_detected is False
        assert execution.handoff_target is None

    def test_execution_id_unique(self, tmp_path):
        """Test that execution IDs are unique."""
        tracker = SubagentTracker(context_id="test_003", session_dir=tmp_path)
        exec_id_1 = tracker.start_execution(
            agent="agent_1", task="Task 1", model="sonnet"
        )
        exec_id_2 = tracker.start_execution(
            agent="agent_2", task="Task 2", model="sonnet"
        )

        assert exec_id_1 != exec_id_2
        assert tracker.get_chain().total_executions == 2

    def test_get_chain_returns_all_executions(self, tmp_path):
        """Test that get_chain returns all executions."""
        tracker = SubagentTracker(context_id="test_004", session_dir=tmp_path)

        exec_1 = tracker.start_execution("agent_1", "Task 1", "sonnet")
        tracker.complete_execution(exec_1, "Result 1")

        exec_2 = tracker.start_execution("agent_2", "Task 2", "opus")
        tracker.complete_execution(exec_2, "Result 2", handoff_target="agent_3")

        exec_3 = tracker.start_execution("agent_3", "Task 3", "sonnet")
        tracker.complete_execution(exec_3, "Result 3")

        chain = tracker.get_chain()
        assert chain.total_executions == 3
        assert chain.handoffs_performed == 1
        assert len(chain.executions) == 3
        assert chain.executions[0].agent_injected == "agent_1"
        assert chain.executions[1].agent_injected == "agent_2"
        assert chain.executions[2].agent_injected == "agent_3"

    def test_get_last_execution(self, tmp_path):
        """Test that get_last_execution returns the most recent execution."""
        tracker = SubagentTracker(context_id="test_005", session_dir=tmp_path)

        exec_1 = tracker.start_execution("agent_1", "Task 1", "sonnet")
        tracker.complete_execution(exec_1, "Result 1")

        exec_2 = tracker.start_execution("agent_2", "Task 2", "opus")
        tracker.complete_execution(exec_2, "Result 2")

        last_exec = tracker.get_last_execution()
        assert last_exec is not None
        assert last_exec.execution_id == exec_2
        assert last_exec.agent_injected == "agent_2"
        assert last_exec.result_summary == "Result 2"

    def test_get_last_execution_empty(self, tmp_path):
        """Test that get_last_execution returns None when no executions."""
        tracker = SubagentTracker(context_id="test_006", session_dir=tmp_path)
        assert tracker.get_last_execution() is None

    def test_session_file_updated(self, tmp_path):
        """Test that session file is updated with execution data."""
        context_id = "test_007"
        tracker = SubagentTracker(context_id=context_id, session_dir=tmp_path)

        exec_id = tracker.start_execution(
            agent="test_agent", task="Test task", model="sonnet"
        )
        tracker.complete_execution(exec_id, "Test result")

        # Read session file
        session_file = tmp_path / f"swarm_session_{context_id}.json"
        assert session_file.exists()

        with open(session_file, "r") as f:
            session_data = json.load(f)

        assert "subagent_executions" in session_data
        subagent_data = session_data["subagent_executions"]
        assert subagent_data["total_executions"] == 1
        assert subagent_data["handoffs_performed"] == 0
        assert len(subagent_data["executions"]) == 1
        assert subagent_data["executions"][0]["agent_injected"] == "test_agent"

    def test_backward_compatible_session(self, tmp_path):
        """Test that tracker works with sessions lacking subagent_executions."""
        context_id = "test_008"
        session_file = tmp_path / f"swarm_session_{context_id}.json"

        # Create a legacy session file without subagent_executions
        legacy_session = {
            "context_id": context_id,
            "current_agent": "sre_principal_engineer_agent",
            "started_at": "2026-01-16T10:00:00",
            "interactions": [],
        }
        with open(session_file, "w") as f:
            json.dump(legacy_session, f)

        # Initialize tracker with existing session
        tracker = SubagentTracker(context_id=context_id, session_dir=tmp_path)

        exec_id = tracker.start_execution(
            agent="test_agent", task="Test task", model="sonnet"
        )
        tracker.complete_execution(exec_id, "Test result")

        # Verify session file now has subagent_executions
        with open(session_file, "r") as f:
            session_data = json.load(f)

        assert "subagent_executions" in session_data
        assert session_data["current_agent"] == "sre_principal_engineer_agent"  # Legacy data preserved
        assert session_data["subagent_executions"]["total_executions"] == 1


class TestSubagentTrackerIntegration:
    """Integration tests for SubagentTracker."""

    def test_integration_with_existing_session(self, tmp_path):
        """Test integration with existing session file."""
        context_id = "integration_001"
        session_file = tmp_path / f"swarm_session_{context_id}.json"

        # Create realistic session file
        session_data = {
            "context_id": context_id,
            "current_agent": "sre_principal_engineer_agent",
            "started_at": "2026-01-16T10:00:00",
            "last_activity": "2026-01-16T10:30:00",
            "interactions": [
                {"role": "user", "content": "Deploy infrastructure"},
                {"role": "assistant", "content": "Deploying..."},
            ],
            "working_directory": "/Users/test/maia",
            "git_remote_url": "https://github.com/test/maia.git",
            "git_branch": "main",
        }
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        # Use tracker
        tracker = SubagentTracker(context_id=context_id, session_dir=tmp_path)
        exec_id = tracker.start_execution(
            agent="security_analyst_agent",
            task="Security review",
            model="opus",
        )
        tracker.complete_execution(
            exec_id, "Security review complete", handoff_target="sre_principal_engineer_agent"
        )

        # Verify all data is preserved
        with open(session_file, "r") as f:
            updated_data = json.load(f)

        assert updated_data["current_agent"] == "sre_principal_engineer_agent"
        assert len(updated_data["interactions"]) == 2
        assert updated_data["working_directory"] == "/Users/test/maia"
        assert "subagent_executions" in updated_data
        assert updated_data["subagent_executions"]["total_executions"] == 1
        assert updated_data["subagent_executions"]["handoffs_performed"] == 1

    def test_multiple_executions_chain(self, tmp_path):
        """Test chaining multiple executions with handoffs."""
        context_id = "integration_002"
        tracker = SubagentTracker(context_id=context_id, session_dir=tmp_path)

        # Simulate execution chain
        exec_1 = tracker.start_execution(
            "sre_principal_engineer_agent",
            "Diagnose infrastructure issue",
            "sonnet",
        )
        time.sleep(0.01)  # Small delay
        tracker.complete_execution(
            exec_1,
            "Issue identified: security vulnerability",
            handoff_target="security_analyst_agent",
            duration_seconds=12.5,
        )

        exec_2 = tracker.start_execution(
            "security_analyst_agent",
            "Analyze security vulnerability",
            "opus",
        )
        time.sleep(0.01)
        tracker.complete_execution(
            exec_2,
            "Vulnerability analyzed: CVE-2024-1234",
            handoff_target="sre_principal_engineer_agent",
            duration_seconds=25.3,
        )

        exec_3 = tracker.start_execution(
            "sre_principal_engineer_agent",
            "Apply security patch",
            "sonnet",
        )
        time.sleep(0.01)
        tracker.complete_execution(
            exec_3, "Patch applied successfully", duration_seconds=18.7
        )

        # Verify chain
        chain = tracker.get_chain()
        assert chain.total_executions == 3
        assert chain.handoffs_performed == 2
        assert len(chain.executions) == 3

        # Verify execution order
        assert chain.executions[0].agent_injected == "sre_principal_engineer_agent"
        assert chain.executions[1].agent_injected == "security_analyst_agent"
        assert chain.executions[2].agent_injected == "sre_principal_engineer_agent"

        # Verify handoffs
        assert chain.executions[0].handoff_detected is True
        assert chain.executions[0].handoff_target == "security_analyst_agent"
        assert chain.executions[1].handoff_detected is True
        assert chain.executions[1].handoff_target == "sre_principal_engineer_agent"
        assert chain.executions[2].handoff_detected is False
        assert chain.executions[2].handoff_target is None

        # Verify last execution
        last_exec = tracker.get_last_execution()
        assert last_exec.execution_id == exec_3
        assert last_exec.result_summary == "Patch applied successfully"
