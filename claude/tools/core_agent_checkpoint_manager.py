#!/usr/bin/env python3
"""
Checkpoint Manager - State Persistence for Maia Core Agent

Provides reliable state checkpointing and recovery for Maia sessions.
Designed for operational reliability in MSP engineering environments.

Requirements: claude/data/project_status/active/MAIA_CORE_AGENT_requirements.md
Agent: SRE Principal Engineer Agent
Created: 2025-11-22

Performance SLAs:
- Checkpoint creation: <500ms
- Checkpoint loading: <200ms
- Recovery context generation: <5s

Reliability SLAs:
- Atomic writes (no partial checkpoints)
- Graceful degradation on errors
- No blocking on missing state
"""

import json
import os
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


# Default paths
MAIA_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CHECKPOINTS_DIR = MAIA_ROOT / "claude" / "data" / "checkpoints"


@dataclass
class Checkpoint:
    """
    Checkpoint data structure per FR-1.2

    Contains all state needed to recover a Maia session after
    context compaction or session restart.
    """
    session_context_id: str
    current_task: Dict[str, Any]

    # Optional fields with defaults
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    todo_list: List[Dict[str, Any]] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    git_state: Dict[str, Any] = field(default_factory=lambda: {
        "branch": "",
        "last_commit": "",
        "uncommitted_changes": False
    })
    recovery_instructions: str = ""
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create Checkpoint from dictionary"""
        return cls(
            checkpoint_id=data.get('checkpoint_id', str(uuid.uuid4())),
            timestamp=data.get('timestamp', datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
            session_context_id=data.get('session_context_id', ''),
            current_task=data.get('current_task', {"description": "", "status": "pending", "progress_percentage": 0}),
            todo_list=data.get('todo_list', []),
            key_decisions=data.get('key_decisions', []),
            files_modified=data.get('files_modified', []),
            git_state=data.get('git_state', {"branch": "", "last_commit": "", "uncommitted_changes": False}),
            recovery_instructions=data.get('recovery_instructions', ''),
            next_steps=data.get('next_steps', []),
        )


class CheckpointManager:
    """
    Manages checkpoint creation, loading, and recovery.

    Thread-safe through atomic file operations.
    Graceful degradation on all error paths.
    """

    def __init__(self, checkpoints_dir: Optional[Path] = None):
        """
        Initialize CheckpointManager.

        Args:
            checkpoints_dir: Directory for checkpoint storage.
                           Defaults to claude/data/checkpoints/
        """
        self.checkpoints_dir = Path(checkpoints_dir) if checkpoints_dir else DEFAULT_CHECKPOINTS_DIR
        self.archive_dir = self.checkpoints_dir / "archive"

        # Ensure directories exist
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        session_context_id: str,
        current_task: Dict[str, Any],
        task_id: Optional[str] = None,
        todo_list: Optional[List[Dict[str, Any]]] = None,
        key_decisions: Optional[List[str]] = None,
        files_modified: Optional[List[str]] = None,
        git_state: Optional[Dict[str, Any]] = None,
        recovery_instructions: str = "",
        next_steps: Optional[List[str]] = None,
    ) -> Path:
        """
        Create a new checkpoint with atomic write.

        Args:
            session_context_id: Current session identifier
            current_task: Task being worked on
            task_id: Optional task identifier for filename
            todo_list: Current todo list state
            key_decisions: Decisions made during session
            files_modified: Files changed during session
            git_state: Current git repository state
            recovery_instructions: How to continue from this point
            next_steps: What needs to be done next

        Returns:
            Path to created checkpoint file

        Performance: <500ms (NFR-1)
        """
        # Create checkpoint object
        checkpoint = Checkpoint(
            session_context_id=session_context_id,
            current_task=current_task,
            todo_list=todo_list or [],
            key_decisions=key_decisions or [],
            files_modified=files_modified or [],
            git_state=git_state or self._get_git_state(),
            recovery_instructions=recovery_instructions,
            next_steps=next_steps or [],
        )

        # Generate filename: {date}_{task_id}.json
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_task_id = task_id or checkpoint.checkpoint_id[:8]
        safe_task_id = "".join(c if c.isalnum() or c in '-_' else '_' for c in safe_task_id)
        filename = f"{date_str}_{safe_task_id}.json"
        target_path = self.checkpoints_dir / filename

        # Atomic write: write to temp file, then rename
        # This prevents partial/corrupted checkpoints on crash
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.json',
            prefix='checkpoint_',
            dir=self.checkpoints_dir
        )

        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(checkpoint.to_dict(), f, indent=2)

            # Atomic rename
            Path(temp_path).rename(target_path)

        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

        return target_path

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Load a specific checkpoint by ID.

        Args:
            checkpoint_id: UUID of checkpoint to load

        Returns:
            Checkpoint object or None if not found/corrupted

        Performance: <200ms (NFR-1)
        Graceful: Returns None on any error (FR-2.3)
        """
        try:
            for path in self.checkpoints_dir.glob("*.json"):
                if path.name == "archive":
                    continue
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if data.get('checkpoint_id') == checkpoint_id:
                        return Checkpoint.from_dict(data)
                except (json.JSONDecodeError, KeyError):
                    continue
        except Exception:
            pass

        return None

    def load_latest_checkpoint(self) -> Optional[Checkpoint]:
        """
        Load the most recent checkpoint.

        Returns:
            Most recent Checkpoint or None if none exist/all corrupted

        Performance: <200ms (NFR-1)
        Graceful: Skips corrupted files (FR-2.3)
        """
        checkpoints = self._load_all_checkpoints()
        if not checkpoints:
            return None

        # Sort by timestamp, newest first
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)
        return checkpoints[0]

    def list_checkpoints(
        self,
        session_context_id: Optional[str] = None
    ) -> List[Checkpoint]:
        """
        List all checkpoints, optionally filtered by session.

        Args:
            session_context_id: Optional filter by session

        Returns:
            List of Checkpoints, newest first
        """
        checkpoints = self._load_all_checkpoints()

        if session_context_id:
            checkpoints = [c for c in checkpoints if c.session_context_id == session_context_id]

        # Sort by timestamp, newest first
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)
        return checkpoints

    def archive_old_checkpoints(self, retention_days: int = 7) -> int:
        """
        Move checkpoints older than retention period to archive.

        Args:
            retention_days: Days to retain checkpoints (default: 7)

        Returns:
            Number of checkpoints archived
        """
        archived_count = 0
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)

        for path in self.checkpoints_dir.glob("*.json"):
            if path.is_file():
                try:
                    if path.stat().st_mtime < cutoff_time:
                        archive_path = self.archive_dir / path.name
                        path.rename(archive_path)
                        archived_count += 1
                except OSError:
                    continue

        return archived_count

    def get_recovery_context(self, include_git: bool = True) -> Dict[str, Any]:
        """
        Get recovery context for session restoration.

        Combines checkpoint data with git history per FR-2.2.

        Args:
            include_git: Include recent git commits

        Returns:
            Recovery context dictionary
        """
        context: Dict[str, Any] = {}

        # Load latest checkpoint
        checkpoint = self.load_latest_checkpoint()
        if checkpoint:
            context['checkpoint'] = checkpoint.to_dict()
        else:
            context['checkpoint'] = None
            context['message'] = "No checkpoints found. Starting fresh session."

        # Include git history
        if include_git:
            context['git_commits'] = self._get_recent_commits()

        return context

    def format_recovery_for_display(self) -> str:
        """
        Format recovery context for user display.

        Returns:
            Formatted string for terminal display
        """
        context = self.get_recovery_context()

        lines = ["RECOVERY DETECTED:", ""]

        checkpoint = context.get('checkpoint')
        if checkpoint:
            task = checkpoint.get('current_task', {})
            lines.append(f"- Last work: {task.get('description', 'Unknown')}")
            lines.append(f"- Progress: {task.get('progress_percentage', 0)}%")
            lines.append(f"- Status: {task.get('status', 'unknown')}")

            if checkpoint.get('next_steps'):
                lines.append("- Next steps:")
                for step in checkpoint['next_steps'][:3]:
                    lines.append(f"  - {step}")

            if checkpoint.get('recovery_instructions'):
                lines.append(f"- Recovery: {checkpoint['recovery_instructions']}")
        else:
            lines.append("- No checkpoint found")

        # Add git commits
        commits = context.get('git_commits', [])
        if commits:
            lines.append("")
            lines.append("- Recent commits:")
            for commit in commits[:3]:
                lines.append(f"  - {commit}")

        lines.append("")
        lines.append("Is this context correct? [confirm/update/start fresh]")

        return "\n".join(lines)

    def _load_all_checkpoints(self) -> List[Checkpoint]:
        """Load all valid checkpoints from directory"""
        checkpoints = []

        for path in self.checkpoints_dir.glob("*.json"):
            if path.is_file():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    checkpoints.append(Checkpoint.from_dict(data))
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Skip corrupted files - graceful degradation
                    continue

        return checkpoints

    def _get_git_state(self) -> Dict[str, Any]:
        """Get current git repository state"""
        state = {
            "branch": "",
            "last_commit": "",
            "uncommitted_changes": False
        }

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=MAIA_ROOT
            )
            if result.returncode == 0:
                state["branch"] = result.stdout.strip()

            # Get last commit
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=MAIA_ROOT
            )
            if result.returncode == 0:
                state["last_commit"] = result.stdout.strip()

            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=MAIA_ROOT
            )
            if result.returncode == 0:
                state["uncommitted_changes"] = bool(result.stdout.strip())

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return state

    def _get_recent_commits(self, count: int = 5, hours: int = 24) -> List[str]:
        """Get recent git commits"""
        commits = []

        try:
            result = subprocess.run(
                ["git", "log", f"--since={hours} hours ago", f"-{count}", "--oneline"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=MAIA_ROOT
            )
            if result.returncode == 0:
                commits = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return commits


# Convenience functions for direct import
def create_checkpoint(**kwargs) -> Path:
    """Create checkpoint using default manager"""
    manager = CheckpointManager()
    return manager.create_checkpoint(**kwargs)


def load_checkpoint(checkpoint_id: str) -> Optional[Checkpoint]:
    """Load checkpoint using default manager"""
    manager = CheckpointManager()
    return manager.load_checkpoint(checkpoint_id)


def load_latest_checkpoint() -> Optional[Checkpoint]:
    """Load latest checkpoint using default manager"""
    manager = CheckpointManager()
    return manager.load_latest_checkpoint()


def list_checkpoints(**kwargs) -> List[Checkpoint]:
    """List checkpoints using default manager"""
    manager = CheckpointManager()
    return manager.list_checkpoints(**kwargs)


def archive_old_checkpoints(**kwargs) -> int:
    """Archive old checkpoints using default manager"""
    manager = CheckpointManager()
    return manager.archive_old_checkpoints(**kwargs)


def get_recovery_context(**kwargs) -> Dict[str, Any]:
    """Get recovery context using default manager"""
    manager = CheckpointManager()
    return manager.get_recovery_context(**kwargs)


if __name__ == '__main__':
    # CLI for manual testing
    import argparse

    parser = argparse.ArgumentParser(description='Maia Checkpoint Manager')
    parser.add_argument('command', choices=['create', 'load', 'list', 'archive', 'recover'])
    parser.add_argument('--task', help='Task description for create')
    parser.add_argument('--id', help='Checkpoint ID for load')
    parser.add_argument('--days', type=int, default=7, help='Retention days for archive')

    args = parser.parse_args()
    manager = CheckpointManager()

    if args.command == 'create':
        path = manager.create_checkpoint(
            session_context_id="cli_test",
            current_task={"description": args.task or "CLI test", "status": "pending", "progress_percentage": 0},
        )
        print(f"Created: {path}")

    elif args.command == 'load':
        if args.id:
            checkpoint = manager.load_checkpoint(args.id)
        else:
            checkpoint = manager.load_latest_checkpoint()
        if checkpoint:
            print(json.dumps(checkpoint.to_dict(), indent=2))
        else:
            print("No checkpoint found")

    elif args.command == 'list':
        for cp in manager.list_checkpoints():
            print(f"{cp.timestamp} | {cp.checkpoint_id[:8]} | {cp.current_task.get('description', 'No description')}")

    elif args.command == 'archive':
        count = manager.archive_old_checkpoints(retention_days=args.days)
        print(f"Archived {count} checkpoints")

    elif args.command == 'recover':
        print(manager.format_recovery_for_display())
