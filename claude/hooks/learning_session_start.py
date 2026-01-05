#!/usr/bin/env python3
"""
Learning Session Start - Unconditional PAI v2 Session Initialization

Phase 236: Fixes learning not capturing by starting sessions unconditionally.

This hook runs as Stage 0.1 in user-prompt-submit, before all other stages.
It ensures every session captures learning data, regardless of agent routing.

Design Principles (from PAI v2):
- Non-blocking: Fire-and-forget, <50ms
- Idempotent: Safe to call multiple times
- Silent: No output by default

Usage:
    # From user-prompt-submit hook (Stage 0.1):
    python3 learning_session_start.py "$CLAUDE_USER_MESSAGE"

Environment Variables:
    CLAUDE_CONTEXT_ID - Context window ID (required for session tracking)
    MAIA_SESSIONS_DIR - Override sessions directory (for testing)

Author: Maia (Phase 236 - Unconditional Learning)
Created: 2026-01-05
"""

import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class LearningSessionStarter:
    """Starts PAI v2 learning sessions unconditionally."""

    def __init__(
        self,
        maia_root: Optional[Path] = None,
        sessions_dir: Optional[Path] = None
    ):
        """
        Initialize the session starter.

        Args:
            maia_root: MAIA root directory (auto-detected if None)
            sessions_dir: Override sessions directory (for testing)
        """
        if maia_root is None:
            # Find maia root by looking for CLAUDE.md
            current = Path(__file__).parent
            while current != current.parent:
                if (current / 'CLAUDE.md').exists():
                    maia_root = current
                    break
                current = current.parent
            if maia_root is None:
                maia_root = Path.cwd()

        self.maia_root = maia_root

        # Sessions directory - can be overridden via env or parameter
        if sessions_dir is not None:
            self.sessions_dir = sessions_dir
        elif os.environ.get("MAIA_SESSIONS_DIR"):
            self.sessions_dir = Path(os.environ["MAIA_SESSIONS_DIR"])
        else:
            self.sessions_dir = Path.home() / ".maia" / "sessions"

    def _get_session_file(self, context_id: str) -> Path:
        """Get path to learning session file for context."""
        return self.sessions_dir / f"learning_session_{context_id}.json"

    def _session_exists(self, context_id: str) -> bool:
        """Check if a learning session already exists for this context."""
        return self._get_session_file(context_id).exists()

    def _generate_session_id(self) -> str:
        """Generate a PAI v2 format session ID."""
        return f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def start_if_needed(
        self,
        context_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Start a learning session if one doesn't exist.

        Args:
            context_id: Claude context window ID
            user_message: The user's first message

        Returns:
            Dict with:
                - started: bool (True if new session created)
                - session_id: str or None
                - reason: str (why session wasn't started, if applicable)
        """
        # Check if session already exists
        if self._session_exists(context_id):
            return {
                "started": False,
                "session_id": None,
                "reason": "session_exists"
            }

        # Create sessions directory if needed
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Generate session ID
        session_id = self._generate_session_id()

        # Create session data
        session_data = {
            "session_id": session_id,
            "context_id": context_id,
            "initial_query": user_message[:500],  # Truncate long messages
            "started_at": datetime.now().isoformat(),
            "status": "active",
            "learning_enabled": True
        }

        # Write session file
        session_file = self._get_session_file(context_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Initialize PAI v2 session manager (non-blocking)
        try:
            self._init_pai_session(session_id, context_id, user_message)
        except Exception:
            # Non-blocking - don't fail if PAI v2 init fails
            pass

        return {
            "started": True,
            "session_id": session_id,
            "reason": None
        }

    def _init_pai_session(
        self,
        session_id: str,
        context_id: str,
        user_message: str
    ):
        """
        Initialize PAI v2 session manager.

        This starts UOCS capture and Maia Memory tracking.
        """
        try:
            from claude.tools.learning.session import get_session_manager

            manager = get_session_manager()
            manager.start_session(
                context_id=context_id,
                initial_query=user_message[:500],
                agent_used=None,  # Agent determined later
                domain=None  # Domain determined later
            )
        except ImportError:
            # PAI v2 not available - session file still created
            pass


def _log_debug(message: str, error: bool = False):
    """Log debug info to file (non-blocking, never fails)."""
    try:
        log_dir = Path.home() / ".maia" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "learning_session_debug.log"
        timestamp = datetime.now().isoformat()
        level = "ERROR" if error else "DEBUG"
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} [{level}] {message}\n")
    except Exception:
        pass  # Never fail on logging


def main():
    """CLI entry point for hook integration."""
    # Get context ID from environment
    context_id = os.environ.get("CLAUDE_CONTEXT_ID")
    if not context_id:
        # Try to get from swarm_auto_loader method
        try:
            maia_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(maia_root))
            from claude.hooks.swarm_auto_loader import get_context_id
            context_id = get_context_id()
        except Exception as e:
            _log_debug(f"Failed to get context_id: {type(e).__name__}: {e}", error=True)
            sys.exit(0)

    # Get user message
    user_message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not user_message:
        user_message = os.environ.get("CLAUDE_USER_MESSAGE", "")

    if not user_message:
        _log_debug(f"No user message provided (context_id={context_id})")
        sys.exit(0)

    # Start session if needed
    try:
        starter = LearningSessionStarter()
        result = starter.start_if_needed(
            context_id=context_id,
            user_message=user_message
        )
        if result.get('started'):
            _log_debug(f"Session started: {result.get('session_id')} (context={context_id})")
        else:
            _log_debug(f"Session skipped: {result.get('reason')} (context={context_id})")
    except Exception as e:
        _log_debug(f"Failed to start session: {type(e).__name__}: {e}", error=True)

    # Silent by default - no output
    sys.exit(0)


if __name__ == "__main__":
    main()
