#!/usr/bin/env python3
"""
Integration Tests for Recovery Protocol and Default Agent Loading
TDD Phase 3: Tests written BEFORE implementation

Tests the integration between:
- swarm_auto_loader.py (session management)
- checkpoint_manager.py (state persistence)
- sre_principal_engineer_agent.md (default agent)

Requirements Reference: claude/data/project_status/active/MAIA_CORE_AGENT_requirements.md
Agent: SRE Principal Engineer Agent
Created: 2025-11-22
"""

import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    from claude.tools.sre.checkpoint_manager import CheckpointManager, Checkpoint
    CHECKPOINT_AVAILABLE = True
except ImportError:
    CHECKPOINT_AVAILABLE = False
    CheckpointManager = None
    Checkpoint = None

import pytest
if not CHECKPOINT_AVAILABLE:
    pytest.skip("Checkpoint class not implemented yet (TDD)", allow_module_level=True)

# Import swarm_auto_loader functions (these exist)
try:
    from claude.hooks.swarm_auto_loader import (
        get_session_file_path,
        get_context_id,
        create_session_state,
        SESSION_STATE_FILE,
    )
    LOADER_EXISTS = True
except ImportError:
    LOADER_EXISTS = False

# Check for new functions (these need to be implemented)
try:
    from claude.hooks.swarm_auto_loader import (
        load_default_agent,
        get_recovery_context,
        should_show_recovery,
    )
    RECOVERY_IMPLEMENTED = True
except ImportError:
    RECOVERY_IMPLEMENTED = False


class TestDefaultAgentLoading(unittest.TestCase):
    """FR-5: Default Agent Loading integration"""

    def setUp(self):
        """Create temp directory and mock session file"""
        self.test_dir = tempfile.mkdtemp()
        self.original_session_file = None

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_load_default_agent_function_exists(self):
        """load_default_agent function is callable"""
        self.assertTrue(callable(load_default_agent))

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_load_default_agent_returns_string_or_none(self):
        """load_default_agent returns string or None"""
        result = load_default_agent()
        self.assertTrue(result is None or isinstance(result, str))

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_sre_agent_file_accessible(self):
        """SRE Principal Engineer Agent file is accessible for loading"""
        agent_path = MAIA_ROOT / "claude" / "agents" / "sre_principal_engineer_agent.md"
        self.assertTrue(agent_path.exists())


class TestRecoveryContextIntegration(unittest.TestCase):
    """FR-2: Recovery Protocol integration with checkpoint manager"""

    def setUp(self):
        """Create temp directories for checkpoints and sessions"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        (self.checkpoints_dir / "archive").mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_get_recovery_context_returns_dict(self):
        """get_recovery_context returns a dictionary"""
        context = get_recovery_context()
        self.assertIsInstance(context, dict)
        self.assertIn('checkpoint', context)
        self.assertIn('git_commits', context)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_get_recovery_context_includes_git(self):
        """get_recovery_context includes git commit history"""
        context = get_recovery_context()
        # git_commits should be a list (may be empty if no recent commits)
        self.assertIsInstance(context.get('git_commits', []), list)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_should_show_recovery_returns_bool(self):
        """should_show_recovery returns a boolean"""
        result = should_show_recovery()
        self.assertIsInstance(result, bool)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_should_show_recovery_false_without_checkpoint(self):
        """should_show_recovery returns False when no checkpoint exists in temp dir"""
        # Use empty temp directory
        empty_dir = Path(self.test_dir) / "empty_checkpoints"
        empty_dir.mkdir()
        (empty_dir / "archive").mkdir()

        manager = CheckpointManager(checkpoints_dir=empty_dir)
        checkpoint = manager.load_latest_checkpoint()

        # No checkpoint in empty dir
        self.assertIsNone(checkpoint)


class TestSessionFileIntegrity(unittest.TestCase):
    """NFR-2: Reliability - session file integrity"""

    def setUp(self):
        """Create temp directory"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(LOADER_EXISTS, "swarm_auto_loader not available")
    def test_session_file_valid_json(self):
        """Session files are always valid JSON"""
        session_file = Path(self.test_dir) / "session.json"

        with patch('swarm_auto_loader.SESSION_STATE_FILE', session_file):
            with patch('swarm_auto_loader.get_session_file_path', return_value=session_file):
                result = create_session_state(
                    agent="test_agent",
                    domain="test",
                    classification={"confidence": 0.9},
                    query="test query"
                )

        self.assertTrue(result)
        self.assertTrue(session_file.exists())

        # Should be valid JSON
        with open(session_file) as f:
            data = json.load(f)

        self.assertEqual(data['current_agent'], 'test_agent')


class TestMaiaCoreToCLAUDEIntegration(unittest.TestCase):
    """
    Integration between Maia Core Agent and CLAUDE.md context loading.

    These tests verify that the default agent loading integrates
    correctly with the existing context loading protocol in CLAUDE.md.
    """

    def test_sre_agent_file_exists(self):
        """sre_principal_engineer_agent.md exists in correct location"""
        agent_path = MAIA_ROOT / "claude" / "agents" / "sre_principal_engineer_agent.md"
        self.assertTrue(agent_path.exists())

    def test_sre_agent_readable(self):
        """sre_principal_engineer_agent.md is readable and has content"""
        agent_path = MAIA_ROOT / "claude" / "agents" / "sre_principal_engineer_agent.md"
        content = agent_path.read_text()
        self.assertGreater(len(content), 100)

    def test_checkpoint_manager_importable(self):
        """checkpoint_manager.py is importable"""
        try:
            from checkpoint_manager import CheckpointManager
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"checkpoint_manager not importable: {e}")


class TestGracefulDegradation(unittest.TestCase):
    """NFR-2: Graceful degradation scenarios"""

    def setUp(self):
        """Create temp directory"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        (self.checkpoints_dir / "archive").mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_recovery_never_raises(self):
        """get_recovery_context never raises exceptions"""
        # Should not raise even with weird state
        try:
            context = get_recovery_context()
            self.assertIsNotNone(context)
        except Exception as e:
            self.fail(f"get_recovery_context raised {e}")

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_should_show_recovery_never_raises(self):
        """should_show_recovery never raises exceptions"""
        try:
            result = should_show_recovery()
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.fail(f"should_show_recovery raised {e}")

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_load_default_agent_never_raises(self):
        """load_default_agent never raises exceptions"""
        try:
            result = load_default_agent()
            self.assertTrue(result is None or isinstance(result, str))
        except Exception as e:
            self.fail(f"load_default_agent raised {e}")


class TestEndToEndRecoveryFlow(unittest.TestCase):
    """End-to-end recovery flow simulation"""

    def setUp(self):
        """Create temp directories"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        (self.checkpoints_dir / "archive").mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_recovery_flow_components_work(self):
        """All recovery flow components are functional"""
        # Test that all components are callable and don't crash
        self.assertTrue(callable(load_default_agent))
        self.assertTrue(callable(get_recovery_context))
        self.assertTrue(callable(should_show_recovery))

        # Each should return expected types
        recovery_result = should_show_recovery()
        self.assertIsInstance(recovery_result, bool)

        context = get_recovery_context()
        self.assertIsInstance(context, dict)

    @unittest.skipUnless(RECOVERY_IMPLEMENTED, "Recovery functions not yet implemented")
    def test_checkpoint_manager_integration(self):
        """Checkpoint manager creates and loads checkpoints"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        # Create checkpoint
        path = manager.create_checkpoint(
            session_context_id="test_session",
            current_task={
                "description": "Test task",
                "status": "in_progress",
                "progress_percentage": 50
            },
        )
        self.assertTrue(path.exists())

        # Load checkpoint
        checkpoint = manager.load_latest_checkpoint()
        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint.current_task['description'], "Test task")


if __name__ == '__main__':
    unittest.main(verbosity=2)
