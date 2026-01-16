"""
Tests for SprintOrchestrator - SPRINT-003 Phase 6

TDD tests for the sprint orchestration system that integrates all components:
- SubagentPromptBuilder
- SpawnDecisionEngine
- SubagentTracker
- SubagentHandoffDetector
"""

import pytest
import tempfile
from pathlib import Path

from claude.tools.orchestration.sprint_orchestrator import (
    SprintOrchestrator,
    SprintTask,
    SprintPlan,
)


@pytest.fixture
def temp_session_dir():
    """Create temporary session directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_agents_dir():
    """Create temporary agents directory with test agent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agents_path = Path(tmpdir)
        # Create a minimal test agent file
        (agents_path / "sre_principal_engineer_agent.md").write_text(
            "# SRE Principal Engineer Agent\n\n"
            "You are an SRE expert specializing in reliability and infrastructure."
        )
        (agents_path / "cloud_security_principal_agent.md").write_text(
            "# Cloud Security Agent\n\n"
            "You are a security expert specializing in cloud security."
        )
        yield agents_path


@pytest.fixture
def orchestrator(temp_session_dir, temp_agents_dir):
    """Create SprintOrchestrator instance with temp directories."""
    return SprintOrchestrator(
        context_id="test_context_123",
        session_dir=temp_session_dir,
        agents_dir=temp_agents_dir,
    )


class TestCreateSprint:
    """Test sprint creation functionality."""

    def test_create_sprint(self, orchestrator):
        """Test that create_sprint creates a plan with tasks."""
        tasks = [
            "Analyze authentication system",
            "Review security configuration",
            "Update monitoring dashboards",
        ]

        plan = orchestrator.create_sprint("sprint_001", tasks)

        # Verify sprint structure
        assert isinstance(plan, SprintPlan)
        assert plan.sprint_id == "sprint_001"
        assert plan.status == "active"
        assert plan.current_task_index == 0
        assert len(plan.tasks) == 3

        # Verify tasks were created correctly
        for i, task in enumerate(plan.tasks):
            assert isinstance(task, SprintTask)
            assert task.task_id == f"sprint_001_task_{i}"
            assert task.description == tasks[i]
            assert task.status == "pending"
            assert task.agent_recommended is not None
            assert isinstance(task.spawn_subagent, bool)


class TestGetCurrentTask:
    """Test current task retrieval."""

    def test_get_current_task(self, orchestrator):
        """Test that get_current_task returns first pending task."""
        tasks = ["Task one", "Task two", "Task three"]
        orchestrator.create_sprint("sprint_001", tasks)

        current = orchestrator.get_current_task()

        assert current is not None
        assert current.description == "Task one"
        assert current.status == "pending"
        assert current.task_id == "sprint_001_task_0"

    def test_get_current_task_empty_sprint(self, orchestrator):
        """Test get_current_task when no sprint exists."""
        result = orchestrator.get_current_task()
        assert result is None


class TestCompleteTask:
    """Test task completion and advancement."""

    def test_complete_task_advances(self, orchestrator):
        """Test that complete_task moves to next task."""
        tasks = ["First task", "Second task", "Third task"]
        orchestrator.create_sprint("sprint_001", tasks)

        # Complete first task
        next_task = orchestrator.complete_task("First task completed successfully")

        # Verify first task is completed
        plan = orchestrator.current_plan
        assert plan.tasks[0].status == "completed"
        assert plan.tasks[0].result_summary == "First task completed successfully"

        # Verify we got the next task
        assert next_task is not None
        assert next_task.description == "Second task"
        assert plan.current_task_index == 1

    def test_complete_last_task(self, orchestrator):
        """Test completing the last task returns None."""
        tasks = ["Only task"]
        orchestrator.create_sprint("sprint_001", tasks)

        next_task = orchestrator.complete_task("Done")

        assert next_task is None
        assert orchestrator.current_plan.status == "completed"


class TestBuildTaskPrompt:
    """Test prompt building with agent injection."""

    def test_build_task_prompt_injects_agent(self, orchestrator):
        """Test that build_task_prompt uses SubagentPromptBuilder."""
        tasks = ["Analyze the infrastructure"]
        orchestrator.create_sprint("sprint_001", tasks)

        current = orchestrator.get_current_task()
        prompt = orchestrator.build_task_prompt(current)

        # Verify prompt contains agent context
        assert "## Agent Context" in prompt
        assert "## Task" in prompt
        assert current.description in prompt
        # Verify agent content is injected
        assert "SRE" in prompt or "security" in prompt.lower()


class TestHandoffDetection:
    """Test handoff detection integration."""

    def test_handoff_detection_integration(self, orchestrator):
        """Test that analyze_result_for_handoff uses SubagentHandoffDetector."""
        # Create result with explicit handoff pattern
        result_with_handoff = """
        Analysis complete. This issue involves security vulnerabilities.
        Recommend security agent for remediation.
        CVE-2024-1234 needs immediate attention.
        """

        handoff_info = orchestrator.analyze_result_for_handoff(result_with_handoff)

        assert isinstance(handoff_info, dict)
        assert "should_handoff" in handoff_info
        assert "target_agent" in handoff_info
        assert "reason" in handoff_info
        assert "confidence" in handoff_info

    def test_no_handoff_for_simple_result(self, orchestrator):
        """Test that simple results don't trigger handoff."""
        simple_result = "Task completed. No issues found."

        handoff_info = orchestrator.analyze_result_for_handoff(simple_result)

        assert handoff_info["should_handoff"] is False


class TestSprintStatus:
    """Test sprint status reporting."""

    def test_sprint_status(self, orchestrator):
        """Test that get_sprint_status reports progress correctly."""
        tasks = ["Task A", "Task B", "Task C"]
        orchestrator.create_sprint("sprint_001", tasks)

        # Complete first task
        orchestrator.complete_task("Done A")

        status = orchestrator.get_sprint_status()

        assert status["sprint_id"] == "sprint_001"
        assert status["total_tasks"] == 3
        assert status["completed_tasks"] == 1
        assert status["pending_tasks"] == 2
        assert status["in_progress_tasks"] == 0
        assert status["progress_percent"] == pytest.approx(33.33, rel=0.1)
        assert status["status"] == "active"

    def test_sprint_status_no_sprint(self, orchestrator):
        """Test status when no sprint exists."""
        status = orchestrator.get_sprint_status()

        assert status["sprint_id"] is None
        assert status["status"] == "no_sprint"


class TestSprintCompletion:
    """Test sprint completion detection."""

    def test_sprint_completion(self, orchestrator):
        """Test that sprint is marked complete when all tasks done."""
        tasks = ["Task 1", "Task 2"]
        orchestrator.create_sprint("sprint_001", tasks)

        # Complete all tasks
        orchestrator.complete_task("Result 1")
        orchestrator.complete_task("Result 2")

        plan = orchestrator.current_plan
        assert plan.status == "completed"

        status = orchestrator.get_sprint_status()
        assert status["status"] == "completed"
        assert status["completed_tasks"] == 2
        assert status["progress_percent"] == 100.0


class TestFullSprintWorkflow:
    """Integration test for complete sprint workflow."""

    def test_full_sprint_workflow(self, orchestrator):
        """Test complete sprint workflow from creation to completion."""
        # 1. Create sprint
        tasks = [
            "Analyze authentication system",
            "Review security logs",
            "Implement fixes",
        ]
        plan = orchestrator.create_sprint("security_audit", tasks)
        assert plan.status == "active"

        # 2. Get first task and build prompt
        task1 = orchestrator.get_current_task()
        assert task1.description == "Analyze authentication system"
        prompt1 = orchestrator.build_task_prompt(task1)
        assert "## Agent Context" in prompt1

        # 3. Complete first task with handoff-suggesting result
        result1 = "Authentication uses outdated methods. Recommend security agent for review."
        handoff = orchestrator.analyze_result_for_handoff(result1)
        assert handoff["should_handoff"] is True

        # 4. Complete task and advance
        task2 = orchestrator.complete_task(result1)
        assert task2.description == "Review security logs"
        assert orchestrator.current_plan.tasks[0].status == "completed"

        # 5. Check status mid-sprint
        status = orchestrator.get_sprint_status()
        assert status["completed_tasks"] == 1
        assert status["pending_tasks"] == 2

        # 6. Complete remaining tasks
        task3 = orchestrator.complete_task("Logs reviewed, no anomalies")
        assert task3.description == "Implement fixes"

        result = orchestrator.complete_task("All fixes implemented")
        assert result is None  # No more tasks

        # 7. Verify sprint completion
        final_status = orchestrator.get_sprint_status()
        assert final_status["status"] == "completed"
        assert final_status["completed_tasks"] == 3
        assert final_status["progress_percent"] == 100.0

        # 8. Verify all task results are stored
        for task in orchestrator.current_plan.tasks:
            assert task.status == "completed"
            assert task.result_summary is not None
