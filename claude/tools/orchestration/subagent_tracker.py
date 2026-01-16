"""SubagentTracker - Records subagent executions in session files.

SPRINT-003 Phase 3: Session Tracking

This module provides tracking for subagent executions, recording each
execution in the session file for analysis and debugging.
"""

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class SubagentExecution:
    """Record of a single subagent execution."""

    execution_id: str
    timestamp: str
    agent_injected: str
    task_summary: str
    model_used: str
    result_summary: str = ""
    handoff_detected: bool = False
    handoff_target: Optional[str] = None
    tokens_estimated: int = 0
    duration_seconds: Optional[float] = None


@dataclass
class SubagentChain:
    """Chain of subagent executions in a session."""

    session_id: str
    started_at: str
    executions: List[SubagentExecution] = field(default_factory=list)
    total_executions: int = 0
    handoffs_performed: int = 0


class SubagentTracker:
    """Tracks subagent executions and persists them to session files."""

    def __init__(self, context_id: str, session_dir: Optional[Path] = None):
        """Initialize tracker.

        Args:
            context_id: The session context ID
            session_dir: Directory for session files (defaults to ~/.maia/sessions/)
        """
        self.context_id = context_id

        if session_dir is None:
            session_dir = Path.home() / ".maia" / "sessions"
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.session_file = self.session_dir / f"swarm_session_{context_id}.json"

        # Load existing chain or create new one
        self._chain = self._load_chain()

    def _load_chain(self) -> SubagentChain:
        """Load existing chain from session file or create new one."""
        if not self.session_file.exists():
            # Create new session file with minimal structure
            session_data = {
                "context_id": self.context_id,
                "started_at": datetime.utcnow().isoformat(),
            }
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            return SubagentChain(
                session_id=self.context_id,
                started_at=session_data["started_at"],
            )

        # Load existing session
        with open(self.session_file, "r") as f:
            try:
                session_data = json.load(f)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Corrupted session file {self.session_file}: {e}")

        # Check if subagent_executions exists
        if "subagent_executions" not in session_data:
            # Backward compatible: create new chain
            return SubagentChain(
                session_id=self.context_id,
                started_at=datetime.utcnow().isoformat(),
            )

        # Load existing chain
        chain_data = session_data["subagent_executions"]
        executions = []
        for exec_data in chain_data["executions"]:
            try:
                executions.append(SubagentExecution(**exec_data))
            except TypeError as e:
                # Skip malformed records, log warning
                import warnings
                warnings.warn(f"Skipping malformed execution record: {e}")

        return SubagentChain(
            session_id=chain_data.get("chain_id", self.context_id),
            started_at=chain_data["started_at"],
            executions=executions,
            total_executions=chain_data["total_executions"],
            handoffs_performed=chain_data["handoffs_performed"],
        )

    def start_execution(
        self, agent: str, task: str, model: str = "sonnet"
    ) -> str:
        """Start tracking an execution.

        Args:
            agent: Agent name being executed
            task: Task summary
            model: Model being used (sonnet/opus)

        Returns:
            Execution ID (e.g., 'exec_a1b2c3d4')
        """
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"

        execution = SubagentExecution(
            execution_id=exec_id,
            timestamp=datetime.utcnow().isoformat(),
            agent_injected=agent,
            task_summary=task,
            model_used=model,
        )

        self._chain.executions.append(execution)
        self._chain.total_executions += 1

        self._update_session_file()

        return exec_id

    def complete_execution(
        self,
        exec_id: str,
        result_summary: str,
        handoff_target: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Complete an execution record.

        Args:
            exec_id: Execution ID returned from start_execution
            result_summary: Summary of execution result
            handoff_target: Target agent if handoff occurred
            duration_seconds: Execution duration in seconds
        """
        # Find execution
        execution = None
        for exec in self._chain.executions:
            if exec.execution_id == exec_id:
                execution = exec
                break

        if execution is None:
            raise ValueError(f"Execution {exec_id} not found")

        # Update execution
        execution.result_summary = result_summary
        execution.duration_seconds = duration_seconds

        if handoff_target:
            execution.handoff_detected = True
            execution.handoff_target = handoff_target
            self._chain.handoffs_performed += 1

        self._update_session_file()

    def get_chain(self) -> SubagentChain:
        """Get the full execution chain.

        Returns:
            SubagentChain with all executions
        """
        return self._chain

    def get_last_execution(self) -> Optional[SubagentExecution]:
        """Get the most recent execution.

        Returns:
            Most recent SubagentExecution or None if no executions
        """
        if not self._chain.executions:
            return None
        return self._chain.executions[-1]

    def _update_session_file(self) -> None:
        """Write executions to session JSON file atomically."""
        # Load existing session data
        if self.session_file.exists():
            with open(self.session_file, "r") as f:
                try:
                    session_data = json.load(f)
                except json.JSONDecodeError:
                    # If corrupted, start fresh
                    session_data = {
                        "context_id": self.context_id,
                        "started_at": datetime.utcnow().isoformat(),
                    }
        else:
            session_data = {
                "context_id": self.context_id,
                "started_at": datetime.utcnow().isoformat(),
            }

        # Convert executions to dicts
        executions_data = [asdict(exec) for exec in self._chain.executions]

        # Update subagent_executions
        session_data["subagent_executions"] = {
            "chain_id": self._chain.session_id,
            "started_at": self._chain.started_at,
            "executions": executions_data,
            "total_executions": self._chain.total_executions,
            "handoffs_performed": self._chain.handoffs_performed,
        }

        # Atomic write: write to temp file first, then rename
        dir_name = self.session_file.parent
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dir_name, delete=False, suffix=".tmp"
        ) as tmp:
            json.dump(session_data, tmp, indent=2)
            tmp_path = tmp.name

        # Atomic rename (POSIX guarantees atomicity)
        os.replace(tmp_path, self.session_file)
