#!/usr/bin/env python3
"""
Post-Compaction Restore Hook
Phase 264: Auto-Resume System for Compaction Survival

This hook is triggered by Claude Code after context compaction via the
SessionStart event with "compact" matcher. It restores context and agent
identity to enable seamless resumption of work.

Hook Lifecycle:
1. Claude Code performs context compaction
2. SessionStart hook fires with trigger="compact"
3. This script reads checkpoint and session data
4. Outputs restoration context to stdout (injected into Claude's context)
5. Claude resumes with full awareness of prior work

Input (from Claude Code via stdin):
{
    "session_id": "12345",
    "hook_event_name": "SessionStart",
    "trigger": "compact",
    "permission_mode": "default"
}

Output:
- Markdown-formatted context printed to stdout
- Injected into Claude's context window

Design Principles:
- Non-blocking: Complete in <2s
- Graceful degradation: Always produce some output
- Agent restoration: Force SRE for code projects
- TDD reminder: Include testing discipline prompt

Author: Maia (Phase 264)
Created: 2026-01-11
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


# Directory constants
DURABLE_CHECKPOINT_DIR = Path.home() / ".maia" / "checkpoints"
SESSIONS_DIR = Path.home() / ".maia" / "sessions"
LOG_DIR = Path.home() / ".maia" / "logs"


def _setup_paths():
    """Set up Python paths for MAIA imports."""
    maia_root = Path(__file__).parent.parent.parent
    if str(maia_root) not in sys.path:
        sys.path.insert(0, str(maia_root))


_setup_paths()


def load_latest_checkpoint(context_id: str) -> Optional[Dict[str, Any]]:
    """
    Load most recent checkpoint for a context.

    Args:
        context_id: Claude context window ID

    Returns:
        Checkpoint dictionary or None if not found
    """
    try:
        context_dir = DURABLE_CHECKPOINT_DIR / context_id

        if not context_dir.exists():
            return None

        # Get all checkpoint files, sorted by modification time (newest first)
        checkpoint_files = sorted(
            context_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not checkpoint_files:
            return None

        # Load the most recent one
        with open(checkpoint_files[0]) as f:
            return json.load(f)

    except Exception as e:
        _log_error(f"Failed to load checkpoint: {e}")
        return None


def load_session(context_id: str) -> Optional[Dict[str, Any]]:
    """
    Load session file for a context.

    Args:
        context_id: Claude context window ID

    Returns:
        Session dictionary or None if not found
    """
    try:
        session_file = SESSIONS_DIR / f"swarm_session_{context_id}.json"

        if not session_file.exists():
            return None

        with open(session_file) as f:
            return json.load(f)

    except Exception as e:
        _log_error(f"Failed to load session: {e}")
        return None


def determine_agent(
    checkpoint: Optional[Dict[str, Any]],
    session: Optional[Dict[str, Any]]
) -> str:
    """
    Determine which agent to restore.

    Priority order:
    1. Checkpoint's recommended_agent (if code project, forces SRE)
    2. Session's current_agent
    3. Default: sre_principal_engineer_agent

    Args:
        checkpoint: Checkpoint data (may be None)
        session: Session data (may be None)

    Returns:
        Agent name to restore
    """
    # Priority 1: Checkpoint recommended agent
    if checkpoint:
        recommended = checkpoint.get("recommended_agent")
        if recommended:
            return recommended

    # Priority 2: Session current agent
    if session:
        current = session.get("current_agent")
        if current:
            return current

    # Priority 3: Default to SRE agent
    return "sre_principal_engineer_agent"


def format_restoration_context(
    agent: str,
    checkpoint: Optional[Dict[str, Any]],
    session: Optional[Dict[str, Any]]
) -> str:
    """
    Generate markdown restoration context for injection.

    Args:
        agent: Agent name to restore
        checkpoint: Checkpoint data (may be None)
        session: Session data (may be None)

    Returns:
        Markdown-formatted context string
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("POST-COMPACTION CONTEXT RESTORED")
    lines.append("=" * 60)
    lines.append("")

    # Agent restoration
    lines.append(f"## Agent: {agent}")
    lines.append(_get_agent_mandate_excerpt(agent))
    lines.append("")

    # Checkpoint context
    if checkpoint:
        lines.append("## Checkpoint Context")
        lines.append(f"- Phase: {checkpoint.get('phase_name', 'Unknown')}")
        lines.append(f"- Progress: {checkpoint.get('percent_complete', 0)}%")
        lines.append(f"- Tests: {checkpoint.get('tests_passing', 0)}/{checkpoint.get('tests_total', 0)}")
        lines.append(f"- TDD Phase: {checkpoint.get('tdd_phase', 'Unknown')}")
        lines.append("")

        # Next action
        next_action = checkpoint.get("next_action")
        if next_action:
            lines.append("### Next Action")
            lines.append(next_action)
            lines.append("")

        # Files modified
        modified = checkpoint.get("modified_files", [])
        if modified:
            lines.append("### Files Modified")
            for f in modified[:10]:
                lines.append(f"- {f}")
            if len(modified) > 10:
                lines.append(f"- ... and {len(modified) - 10} more")
            lines.append("")
    else:
        lines.append("## Checkpoint Context")
        lines.append("_No checkpoint found. Starting fresh context._")
        lines.append("")

    # TDD reminder
    lines.append("## TDD Protocol Active")
    lines.append("- Tests MUST pass before proceeding")
    lines.append("- Follow P0-P6.5 gate sequence")
    lines.append("- Run `pytest tests/ -v` to verify test state")
    lines.append("")

    # Footer
    lines.append("=" * 60)

    return "\n".join(lines)


def _get_agent_mandate_excerpt(agent: str) -> str:
    """
    Get first 30 lines of agent mandate.

    Args:
        agent: Agent name

    Returns:
        Excerpt of agent mandate or placeholder
    """
    try:
        # Try to find agent file
        maia_root = Path(__file__).parent.parent.parent
        agent_file = maia_root / "claude" / "agents" / f"{agent}.md"

        if not agent_file.exists():
            # Try without _agent suffix
            agent_file = maia_root / "claude" / "agents" / f"{agent}_agent.md"

        if agent_file.exists():
            content = agent_file.read_text()
            lines = content.split("\n")[:30]
            return "\n".join(lines)

        return f"_Agent mandate for {agent} not found._"

    except Exception:
        return f"_Failed to load agent mandate for {agent}._"


def _log_error(message: str):
    """Log error message."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        error_log = LOG_DIR / "post_compaction_errors.log"

        timestamp = datetime.now().isoformat()
        with open(error_log, 'a') as f:
            f.write(f"{timestamp} [ERROR] {message}\n")
    except Exception:
        pass  # Never fail on logging


def _log_debug(message: str):
    """Log debug message."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        debug_log = LOG_DIR / "post_compaction_debug.log"

        timestamp = datetime.now().isoformat()
        with open(debug_log, 'a') as f:
            f.write(f"{timestamp} [DEBUG] {message}\n")
    except Exception:
        pass  # Never fail on logging


class PostCompactionRestore:
    """
    Post-compaction restore hook handler.

    Restores context and agent identity after compaction.
    """

    def __init__(self):
        """Initialize hook handler."""
        self.checkpoint_dir = DURABLE_CHECKPOINT_DIR
        self.sessions_dir = SESSIONS_DIR

    def restore(self, hook_input: Dict[str, Any]) -> str:
        """
        Process post-compaction restoration.

        Args:
            hook_input: Hook data from Claude Code

        Returns:
            Markdown context for injection
        """
        context_id = hook_input.get("session_id", "unknown")

        _log_debug(f"Restoring context for {context_id}")

        # Load checkpoint
        checkpoint = load_latest_checkpoint(context_id)
        if checkpoint:
            _log_debug(f"Loaded checkpoint: {checkpoint.get('phase_name')}")
        else:
            _log_debug("No checkpoint found")

        # Load session
        session = load_session(context_id)
        if session:
            _log_debug(f"Loaded session: {session.get('current_agent')}")
        else:
            _log_debug("No session found")

        # Determine agent
        agent = determine_agent(checkpoint, session)
        _log_debug(f"Determined agent: {agent}")

        # Format restoration context
        context = format_restoration_context(agent, checkpoint, session)

        return context


def main():
    """
    Main entry point for hook.

    Reads hook input from stdin, processes, and outputs to stdout.
    """
    try:
        # Read hook input from stdin
        hook_input = json.load(sys.stdin)

        # Process restoration
        hook = PostCompactionRestore()
        context = hook.restore(hook_input)

        # Output to stdout for injection into Claude's context
        print(context)

        sys.exit(0)

    except Exception as e:
        # Emergency error logging
        _log_error(f"Hook crashed: {type(e).__name__}: {e}")

        # Output minimal context anyway (graceful degradation)
        print("=" * 60)
        print("POST-COMPACTION CONTEXT RESTORED")
        print("=" * 60)
        print("")
        print("## Agent: sre_principal_engineer_agent")
        print("_Context restoration encountered an error. Defaulting to SRE agent._")
        print("")
        print("## TDD Protocol Active")
        print("- Tests MUST pass before proceeding")
        print("=" * 60)

        sys.exit(0)  # Never fail - always produce some output


if __name__ == "__main__":
    main()
