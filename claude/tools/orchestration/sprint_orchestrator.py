"""
Sprint Orchestrator - SPRINT-003 Phase 6

Integrates all orchestration components to manage sprint-based task execution:
- SubagentPromptBuilder: Builds Task tool prompts with agent context
- SpawnDecisionEngine: Determines when to delegate to subagents
- SubagentTracker: Records subagent executions in session files
- SubagentHandoffDetector: Analyzes results for handoff patterns

Usage:
    from claude.tools.orchestration.sprint_orchestrator import (
        SprintOrchestrator, SprintTask, SprintPlan
    )

    orchestrator = SprintOrchestrator(context_id="session_123")
    plan = orchestrator.create_sprint("sprint_001", ["task1", "task2"])

    while (task := orchestrator.get_current_task()):
        prompt = orchestrator.build_task_prompt(task)
        # Execute task with Task tool using prompt
        result = "..."  # Task result
        handoff = orchestrator.analyze_result_for_handoff(result)
        orchestrator.complete_task(result)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

from .subagent_prompt_builder import SubagentPromptBuilder
from .spawn_decision import SpawnDecisionEngine
from .subagent_tracker import SubagentTracker
from .subagent_handoff import SubagentHandoffDetector


@dataclass
class SprintTask:
    """Represents a single task within a sprint."""

    task_id: str
    description: str
    status: str  # pending | in_progress | completed | blocked
    agent_recommended: str
    spawn_subagent: bool
    result_summary: Optional[str] = None


@dataclass
class SprintPlan:
    """Represents a sprint plan with multiple tasks."""

    sprint_id: str
    name: str
    tasks: List[SprintTask] = field(default_factory=list)
    current_task_index: int = 0
    status: str = "active"  # active | completed | paused


class SprintOrchestrator:
    """
    Orchestrates sprint execution using all orchestration components.

    This class integrates:
    - SubagentPromptBuilder: For building Task tool prompts with agent context
    - SpawnDecisionEngine: For determining when to delegate to subagents
    - SubagentTracker: For recording subagent executions
    - SubagentHandoffDetector: For analyzing results for handoff patterns
    """

    def __init__(
        self,
        context_id: str,
        session_dir: Optional[Path] = None,
        agents_dir: Optional[Path] = None,
    ):
        """
        Initialize the Sprint Orchestrator with all component instances.

        Args:
            context_id: Session context ID for tracking
            session_dir: Directory for session files (defaults to ~/.maia/sessions/)
            agents_dir: Directory for agent files (defaults to MAIA_ROOT/claude/agents/)
        """
        self.context_id = context_id

        # Initialize all orchestration components
        self.prompt_builder = SubagentPromptBuilder(agents_dir=agents_dir)
        self.spawn_engine = SpawnDecisionEngine()
        self.tracker = SubagentTracker(context_id=context_id, session_dir=session_dir)
        self.handoff_detector = SubagentHandoffDetector()

        # Current sprint plan
        self.current_plan: Optional[SprintPlan] = None

        # Store the agents directory for reference
        self._agents_dir = agents_dir

    def create_sprint(self, sprint_id: str, tasks: List[str]) -> SprintPlan:
        """
        Create a sprint plan from task descriptions.

        Analyzes each task to determine:
        - Recommended agent for execution
        - Whether to spawn a subagent

        Args:
            sprint_id: Unique identifier for the sprint
            tasks: List of task descriptions

        Returns:
            SprintPlan with analyzed tasks
        """
        sprint_tasks: List[SprintTask] = []

        for i, task_description in enumerate(tasks):
            # Use spawn decision engine to analyze task
            decision = self.spawn_engine.analyze(
                query=task_description,
                session_context={"sprint_mode": True},
                files_mentioned=[]
            )

            sprint_task = SprintTask(
                task_id=f"{sprint_id}_task_{i}",
                description=task_description,
                status="pending",
                agent_recommended=decision.recommended_agent or "sre_principal_engineer_agent",
                spawn_subagent=decision.should_spawn,
                result_summary=None,
            )
            sprint_tasks.append(sprint_task)

        # Create sprint plan
        self.current_plan = SprintPlan(
            sprint_id=sprint_id,
            name=sprint_id,
            tasks=sprint_tasks,
            current_task_index=0,
            status="active",
        )

        return self.current_plan

    def get_current_task(self) -> Optional[SprintTask]:
        """
        Get the current task with spawn recommendation.

        Returns:
            Current SprintTask or None if no sprint or all tasks complete
        """
        if self.current_plan is None:
            return None

        if self.current_plan.current_task_index >= len(self.current_plan.tasks):
            return None

        task = self.current_plan.tasks[self.current_plan.current_task_index]

        # Only return pending tasks
        if task.status != "pending":
            # Find next pending task
            for i, t in enumerate(self.current_plan.tasks):
                if t.status == "pending":
                    self.current_plan.current_task_index = i
                    return t
            return None

        return task

    def build_task_prompt(self, task: SprintTask) -> str:
        """
        Build Task tool prompt for a task using SubagentPromptBuilder.

        Args:
            task: SprintTask to build prompt for

        Returns:
            Complete prompt string with agent context injected
        """
        result = self.prompt_builder.build(
            agent_name=task.agent_recommended,
            task=task.description,
        )

        return result.prompt

    def complete_task(self, result_summary: str) -> Optional[SprintTask]:
        """
        Complete the current task and return the next task.

        Args:
            result_summary: Summary of task completion result

        Returns:
            Next SprintTask or None if no more tasks
        """
        if self.current_plan is None:
            return None

        # Mark current task as completed
        current_idx = self.current_plan.current_task_index
        if current_idx < len(self.current_plan.tasks):
            task = self.current_plan.tasks[current_idx]
            task.status = "completed"
            task.result_summary = result_summary

        # Advance to next task
        self.current_plan.current_task_index += 1

        # Check if sprint is complete
        if self.current_plan.current_task_index >= len(self.current_plan.tasks):
            self.current_plan.status = "completed"
            return None

        # Return next task
        next_task = self.current_plan.tasks[self.current_plan.current_task_index]
        return next_task

    def analyze_result_for_handoff(self, result: str) -> Dict[str, Any]:
        """
        Check if result suggests a handoff to another agent.

        Args:
            result: Text result from task execution

        Returns:
            Dictionary with handoff analysis:
            - should_handoff: bool
            - target_agent: Optional[str]
            - reason: str
            - confidence: float
            - context_to_pass: Optional[str]
        """
        # Determine current agent
        current_agent = "sre_principal_engineer_agent"
        if self.current_plan and self.current_plan.current_task_index < len(self.current_plan.tasks):
            current_task = self.current_plan.tasks[self.current_plan.current_task_index]
            current_agent = current_task.agent_recommended

        # Use handoff detector
        recommendation = self.handoff_detector.analyze(
            subagent_result=result,
            current_agent=current_agent,
        )

        return {
            "should_handoff": recommendation.should_handoff,
            "target_agent": recommendation.target_agent,
            "reason": recommendation.reason,
            "confidence": recommendation.confidence,
            "context_to_pass": recommendation.context_to_pass,
            "detected_patterns": recommendation.detected_patterns,
        }

    def get_sprint_status(self) -> Dict[str, Any]:
        """
        Get current sprint progress status.

        Returns:
            Dictionary with sprint status:
            - sprint_id: Optional[str]
            - status: str (active | completed | paused | no_sprint)
            - total_tasks: int
            - completed_tasks: int
            - pending_tasks: int
            - in_progress_tasks: int
            - blocked_tasks: int
            - progress_percent: float
            - current_task: Optional[str]
        """
        if self.current_plan is None:
            return {
                "sprint_id": None,
                "status": "no_sprint",
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "in_progress_tasks": 0,
                "blocked_tasks": 0,
                "progress_percent": 0.0,
                "current_task": None,
            }

        # Count tasks by status
        completed = sum(1 for t in self.current_plan.tasks if t.status == "completed")
        pending = sum(1 for t in self.current_plan.tasks if t.status == "pending")
        in_progress = sum(1 for t in self.current_plan.tasks if t.status == "in_progress")
        blocked = sum(1 for t in self.current_plan.tasks if t.status == "blocked")
        total = len(self.current_plan.tasks)

        # Calculate progress
        progress = (completed / total * 100) if total > 0 else 0.0

        # Get current task description
        current_task_desc = None
        current = self.get_current_task()
        if current:
            current_task_desc = current.description

        return {
            "sprint_id": self.current_plan.sprint_id,
            "status": self.current_plan.status,
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "blocked_tasks": blocked,
            "progress_percent": progress,
            "current_task": current_task_desc,
        }
