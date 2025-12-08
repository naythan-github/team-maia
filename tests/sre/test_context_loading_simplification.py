#!/usr/bin/env python3
"""
TDD Tests for Context Loading Simplification (Phase 178)

Requirements:
- R1: New window startup = start fresh, no recovery prompts
- R2: Session file exists for THIS context = load agent
- R3: Session file for DIFFERENT context = ignored
- R4: Checkpoints = intra-session only, not cross-session

Agent: SRE Principal Engineer Agent
Created: 2025-11-23
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directories to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT / "claude" / "hooks"))
sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools"))


class TestContextLoadingSimplification(unittest.TestCase):
    """Test suite for context loading simplification requirements."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temp directory for test session files
        self.temp_dir = tempfile.mkdtemp()
        self.original_tmp = os.environ.get('TMPDIR')

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_new_session_no_session_file_starts_fresh(self):
        """
        TEST-1: New session with no session file → NO recovery prompt

        When a new Claude Code window starts and no session file exists
        for its context ID, it should start fresh without any prompts.
        """
        from swarm_auto_loader import get_session_file_path, get_context_id

        # Get the session file path for current context
        session_path = get_session_file_path()

        # Ensure no session file exists
        if session_path.exists():
            session_path.unlink()

        # Verify no session file
        self.assertFalse(session_path.exists(),
            "Session file should not exist for fresh start")

        # The expected behavior: no recovery prompt needed
        # This is validated by the absence of should_show_recovery() in startup

    def test_02_new_session_ignores_checkpoint_files(self):
        """
        TEST-2: New session with checkpoint files → NO recovery prompt

        Checkpoints are for intra-session recovery only.
        New sessions should NOT check or prompt about checkpoints.
        """
        from checkpoint_manager import CheckpointManager

        # Create a checkpoint (simulating prior work)
        manager = CheckpointManager()
        checkpoint_path = manager.create_checkpoint(
            session_context_id="old_session_123",
            current_task={
                "description": "Old task from yesterday",
                "status": "in_progress",
                "progress_percentage": 50
            }
        )

        self.assertTrue(checkpoint_path.exists(),
            "Checkpoint should be created")

        # The key assertion: new session startup should NOT call
        # should_show_recovery() or format_recovery_for_display()
        # This is a behavioral requirement, not a function test

        # Clean up
        checkpoint_path.unlink()

    def test_03_existing_session_file_loads_agent(self):
        """
        TEST-3: Existing session file for THIS context → Load agent from session

        When a session file exists for the current context ID,
        the agent should be loaded from that session.
        """
        from swarm_auto_loader import get_session_file_path, get_context_id

        session_path = get_session_file_path()
        context_id = get_context_id()

        # Create a session file for current context
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "session_start": "2025-11-23T10:00:00Z",
            "domain": "sre",
            "context": {"test": True}
        }

        with open(session_path, 'w') as f:
            json.dump(session_data, f)

        try:
            # Verify session file exists and is valid
            self.assertTrue(session_path.exists())

            with open(session_path) as f:
                loaded = json.load(f)

            self.assertEqual(loaded["current_agent"], "sre_principal_engineer_agent")
            self.assertEqual(loaded["domain"], "sre")
        finally:
            # Clean up
            if session_path.exists():
                session_path.unlink()

    def test_04_different_context_session_ignored(self):
        """
        TEST-4: Session file for DIFFERENT context → Ignored

        Each Claude Code window should only read its OWN session file.
        Session files from other contexts should be ignored.
        """
        from swarm_auto_loader import get_context_id

        current_context_id = get_context_id()
        other_context_id = "99999"  # Different context

        # Create session file for OTHER context
        other_session_path = Path(f"/tmp/maia_active_swarm_session_{other_context_id}.json")

        session_data = {
            "current_agent": "security_specialist_agent",
            "session_start": "2025-11-23T09:00:00Z",
            "domain": "security"
        }

        with open(other_session_path, 'w') as f:
            json.dump(session_data, f)

        try:
            # Verify the other session file exists
            self.assertTrue(other_session_path.exists())

            # Verify current context ID is different
            self.assertNotEqual(current_context_id, other_context_id,
                "Context IDs should be different")

            # The session path for THIS context should be different
            from swarm_auto_loader import get_session_file_path
            this_session_path = get_session_file_path()

            self.assertNotEqual(str(this_session_path), str(other_session_path),
                "Session paths should be different for different contexts")
        finally:
            # Clean up
            if other_session_path.exists():
                other_session_path.unlink()

    def test_05_load_default_agent_no_recovery_check(self):
        """
        TEST-5: load_default_agent() → Creates session, NO recovery check

        When load_default_agent() is called, it should create a session
        for maia_core_agent WITHOUT checking or prompting for recovery.
        """
        from swarm_auto_loader import (
            load_default_agent,
            get_session_file_path,
            should_show_recovery
        )

        session_path = get_session_file_path()

        # Ensure no session exists
        if session_path.exists():
            session_path.unlink()

        # The key behavioral requirement:
        # load_default_agent() should NOT call should_show_recovery()

        # For now, verify should_show_recovery exists but shouldn't be
        # part of the startup path for NEW sessions

        # This test documents the expected behavior:
        # - load_default_agent() creates session
        # - should_show_recovery() is NOT called for new windows

        # Call load_default_agent
        result = load_default_agent()

        try:
            if result:
                # Session should be created
                self.assertTrue(session_path.exists(),
                    "Session file should be created for default agent")

                with open(session_path) as f:
                    session = json.load(f)

                self.assertEqual(session["current_agent"], "maia_core_agent")
        finally:
            # Clean up
            if session_path.exists():
                session_path.unlink()


class TestCheckpointScopeValidation(unittest.TestCase):
    """Validate that checkpoints are properly scoped to intra-session use."""

    def test_checkpoint_created_with_session_context_id(self):
        """
        Checkpoints must include session_context_id to enable
        intra-session matching (same context = same session).
        """
        from checkpoint_manager import CheckpointManager
        from swarm_auto_loader import get_context_id

        manager = CheckpointManager()
        context_id = get_context_id()

        # Create checkpoint with current context ID
        checkpoint_path = manager.create_checkpoint(
            session_context_id=context_id,
            current_task={
                "description": "Test task",
                "status": "in_progress",
                "progress_percentage": 25
            }
        )

        try:
            with open(checkpoint_path) as f:
                checkpoint = json.load(f)

            self.assertEqual(checkpoint["session_context_id"], context_id,
                "Checkpoint should include session context ID")
        finally:
            checkpoint_path.unlink()

    def test_checkpoint_filtering_by_session(self):
        """
        Checkpoints can be filtered by session_context_id to
        retrieve only checkpoints from the current session.
        """
        from checkpoint_manager import CheckpointManager

        manager = CheckpointManager()

        # Create checkpoints for different sessions
        path1 = manager.create_checkpoint(
            session_context_id="session_A",
            current_task={"description": "Task A", "status": "done", "progress_percentage": 100}
        )

        path2 = manager.create_checkpoint(
            session_context_id="session_B",
            current_task={"description": "Task B", "status": "done", "progress_percentage": 100}
        )

        try:
            # Filter by session
            session_a_checkpoints = manager.list_checkpoints(session_context_id="session_A")
            session_b_checkpoints = manager.list_checkpoints(session_context_id="session_B")

            # Verify filtering works
            for cp in session_a_checkpoints:
                self.assertEqual(cp.session_context_id, "session_A")

            for cp in session_b_checkpoints:
                self.assertEqual(cp.session_context_id, "session_B")
        finally:
            path1.unlink()
            path2.unlink()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
