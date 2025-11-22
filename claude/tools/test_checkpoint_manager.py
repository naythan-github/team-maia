#!/usr/bin/env python3
"""
Test Suite for Checkpoint Manager
TDD Phase 3: Tests written BEFORE implementation

Requirements Reference: claude/data/project_status/active/MAIA_CORE_AGENT_requirements.md
Agent: SRE Principal Engineer Agent
Created: 2025-11-22
"""

import json
import os
import tempfile
import shutil
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import will fail until implementation exists - that's TDD
try:
    from checkpoint_manager import (
        CheckpointManager,
        Checkpoint,
        create_checkpoint,
        load_checkpoint,
        load_latest_checkpoint,
        list_checkpoints,
        archive_old_checkpoints,
        get_recovery_context,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


class TestCheckpointSchema(unittest.TestCase):
    """FR-1.2: Checkpoint content structure validation"""

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_checkpoint_has_required_fields(self):
        """Checkpoint contains all required fields from FR-1.2"""
        required_fields = {
            'checkpoint_id',
            'timestamp',
            'session_context_id',
            'current_task',
            'todo_list',
            'key_decisions',
            'files_modified',
            'git_state',
            'recovery_instructions',
            'next_steps',
        }

        checkpoint = Checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test task", "status": "in_progress", "progress_percentage": 50},
            todo_list=[],
            key_decisions=[],
            files_modified=[],
            recovery_instructions="Continue from step 3",
            next_steps=["Complete step 3", "Run tests"],
        )

        checkpoint_dict = checkpoint.to_dict()
        self.assertTrue(required_fields.issubset(checkpoint_dict.keys()))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_checkpoint_id_is_uuid(self):
        """Checkpoint ID is a valid UUID"""
        import uuid

        checkpoint = Checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test", "status": "pending", "progress_percentage": 0},
        )

        # Should not raise
        uuid.UUID(checkpoint.checkpoint_id)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_timestamp_is_iso8601(self):
        """Timestamp is valid ISO8601 format"""
        checkpoint = Checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test", "status": "pending", "progress_percentage": 0},
        )

        # Should not raise
        datetime.fromisoformat(checkpoint.timestamp.replace('Z', '+00:00'))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_current_task_structure(self):
        """Current task has required sub-fields"""
        checkpoint = Checkpoint(
            session_context_id="test_123",
            current_task={
                "description": "Implementing feature X",
                "status": "in_progress",
                "progress_percentage": 75
            },
        )

        task = checkpoint.current_task
        self.assertIn('description', task)
        self.assertIn('status', task)
        self.assertIn('progress_percentage', task)
        self.assertIn(task['status'], ['in_progress', 'blocked', 'pending', 'completed'])
        self.assertGreaterEqual(task['progress_percentage'], 0)
        self.assertLessEqual(task['progress_percentage'], 100)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_git_state_structure(self):
        """Git state has required sub-fields"""
        checkpoint = Checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test", "status": "pending", "progress_percentage": 0},
            git_state={
                "branch": "main",
                "last_commit": "abc123",
                "uncommitted_changes": True
            },
        )

        git_state = checkpoint.git_state
        self.assertIn('branch', git_state)
        self.assertIn('last_commit', git_state)
        self.assertIn('uncommitted_changes', git_state)


class TestCheckpointCreation(unittest.TestCase):
    """FR-1.1: Checkpoint creation"""

    def setUp(self):
        """Create temp directory for test checkpoints"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_create_checkpoint_returns_path(self):
        """create_checkpoint returns path to created file"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        path = manager.create_checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test", "status": "pending", "progress_percentage": 0},
        )

        self.assertIsInstance(path, Path)
        self.assertTrue(path.exists())

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_create_checkpoint_file_is_valid_json(self):
        """Created checkpoint file contains valid JSON"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        path = manager.create_checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test", "status": "pending", "progress_percentage": 0},
        )

        with open(path) as f:
            data = json.load(f)

        self.assertIn('checkpoint_id', data)
        self.assertIn('timestamp', data)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_create_checkpoint_atomic_write(self):
        """Checkpoint write is atomic (temp file + rename)"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        # Mock to verify atomic write pattern
        with patch('checkpoint_manager.Path.rename') as mock_rename:
            with patch('checkpoint_manager.tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp_file = MagicMock()
                mock_temp_file.name = str(self.checkpoints_dir / "temp_checkpoint.json")
                mock_temp.return_value.__enter__.return_value = mock_temp_file

                manager.create_checkpoint(
                    session_context_id="test_123",
                    current_task={"description": "Test", "status": "pending", "progress_percentage": 0},
                )

                # Verify rename was called (atomic pattern)
                mock_rename.assert_called_once()

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_create_checkpoint_filename_format(self):
        """Checkpoint filename follows {date}_{task_id}.json format"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        path = manager.create_checkpoint(
            session_context_id="test_123",
            current_task={"description": "Test task", "status": "pending", "progress_percentage": 0},
            task_id="feature_x",
        )

        # Filename should be like 2025-11-22_feature_x.json
        self.assertRegex(path.name, r'\d{4}-\d{2}-\d{2}_[\w-]+\.json')


class TestCheckpointLoading(unittest.TestCase):
    """FR-2.2: Loading checkpoints for recovery"""

    def setUp(self):
        """Create temp directory with test checkpoints"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    def _create_test_checkpoint(self, filename: str, data: dict):
        """Helper to create test checkpoint file"""
        path = self.checkpoints_dir / filename
        with open(path, 'w') as f:
            json.dump(data, f)
        return path

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_load_checkpoint_by_id(self):
        """Load specific checkpoint by ID"""
        test_data = {
            "checkpoint_id": "abc-123",
            "timestamp": "2025-11-22T10:00:00Z",
            "session_context_id": "test",
            "current_task": {"description": "Test", "status": "pending", "progress_percentage": 0},
        }
        self._create_test_checkpoint("2025-11-22_test.json", test_data)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoint = manager.load_checkpoint("abc-123")

        self.assertEqual(checkpoint.checkpoint_id, "abc-123")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_load_latest_checkpoint(self):
        """Load most recent checkpoint"""
        old_data = {
            "checkpoint_id": "old-123",
            "timestamp": "2025-11-21T10:00:00Z",
            "session_context_id": "test",
            "current_task": {"description": "Old task", "status": "completed", "progress_percentage": 100},
        }
        new_data = {
            "checkpoint_id": "new-456",
            "timestamp": "2025-11-22T10:00:00Z",
            "session_context_id": "test",
            "current_task": {"description": "New task", "status": "in_progress", "progress_percentage": 50},
        }
        self._create_test_checkpoint("2025-11-21_old.json", old_data)
        self._create_test_checkpoint("2025-11-22_new.json", new_data)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoint = manager.load_latest_checkpoint()

        self.assertEqual(checkpoint.checkpoint_id, "new-456")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_load_checkpoint_not_found_returns_none(self):
        """Loading non-existent checkpoint returns None (graceful degradation)"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoint = manager.load_checkpoint("nonexistent-id")

        self.assertIsNone(checkpoint)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_load_corrupted_checkpoint_returns_none(self):
        """Loading corrupted checkpoint returns None (graceful degradation)"""
        path = self.checkpoints_dir / "corrupted.json"
        with open(path, 'w') as f:
            f.write("not valid json {{{")

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoint = manager.load_latest_checkpoint()

        # Should not raise, should return None or skip corrupted
        # (graceful degradation per FR-2.3)


class TestCheckpointListing(unittest.TestCase):
    """List and filter checkpoints"""

    def setUp(self):
        """Create temp directory with test checkpoints"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    def _create_test_checkpoint(self, filename: str, data: dict):
        """Helper to create test checkpoint file"""
        path = self.checkpoints_dir / filename
        with open(path, 'w') as f:
            json.dump(data, f)
        return path

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_list_checkpoints_returns_all(self):
        """list_checkpoints returns all checkpoint files"""
        self._create_test_checkpoint("2025-11-20_a.json", {"checkpoint_id": "a"})
        self._create_test_checkpoint("2025-11-21_b.json", {"checkpoint_id": "b"})
        self._create_test_checkpoint("2025-11-22_c.json", {"checkpoint_id": "c"})

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoints = manager.list_checkpoints()

        self.assertEqual(len(checkpoints), 3)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_list_checkpoints_sorted_by_date(self):
        """Checkpoints returned in chronological order (newest first)"""
        self._create_test_checkpoint("2025-11-20_a.json", {"checkpoint_id": "a", "timestamp": "2025-11-20T10:00:00Z"})
        self._create_test_checkpoint("2025-11-22_c.json", {"checkpoint_id": "c", "timestamp": "2025-11-22T10:00:00Z"})
        self._create_test_checkpoint("2025-11-21_b.json", {"checkpoint_id": "b", "timestamp": "2025-11-21T10:00:00Z"})

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoints = manager.list_checkpoints()

        # Newest first
        self.assertEqual(checkpoints[0].checkpoint_id, "c")
        self.assertEqual(checkpoints[1].checkpoint_id, "b")
        self.assertEqual(checkpoints[2].checkpoint_id, "a")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_list_checkpoints_filter_by_session(self):
        """Filter checkpoints by session context ID"""
        self._create_test_checkpoint("2025-11-22_a.json", {
            "checkpoint_id": "a",
            "session_context_id": "session_1",
            "timestamp": "2025-11-22T10:00:00Z"
        })
        self._create_test_checkpoint("2025-11-22_b.json", {
            "checkpoint_id": "b",
            "session_context_id": "session_2",
            "timestamp": "2025-11-22T11:00:00Z"
        })

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        checkpoints = manager.list_checkpoints(session_context_id="session_1")

        self.assertEqual(len(checkpoints), 1)
        self.assertEqual(checkpoints[0].checkpoint_id, "a")


class TestCheckpointArchiving(unittest.TestCase):
    """FR-1.3: Checkpoint retention and archiving"""

    def setUp(self):
        """Create temp directory with test checkpoints"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    def _create_test_checkpoint(self, filename: str, data: dict, age_days: int = 0):
        """Helper to create test checkpoint file with specific age"""
        path = self.checkpoints_dir / filename
        with open(path, 'w') as f:
            json.dump(data, f)

        # Set modification time to simulate age
        if age_days > 0:
            old_time = time.time() - (age_days * 24 * 60 * 60)
            os.utime(path, (old_time, old_time))

        return path

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_archive_old_checkpoints_moves_to_archive(self):
        """Checkpoints older than 7 days moved to archive"""
        # Recent checkpoint (keep)
        self._create_test_checkpoint("2025-11-22_recent.json", {"checkpoint_id": "recent"}, age_days=1)
        # Old checkpoint (archive)
        self._create_test_checkpoint("2025-11-10_old.json", {"checkpoint_id": "old"}, age_days=12)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        archived_count = manager.archive_old_checkpoints(retention_days=7)

        self.assertEqual(archived_count, 1)
        self.assertFalse((self.checkpoints_dir / "2025-11-10_old.json").exists())
        self.assertTrue((self.archive_dir / "2025-11-10_old.json").exists())

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_archive_preserves_recent_checkpoints(self):
        """Checkpoints within retention period are not archived"""
        self._create_test_checkpoint("2025-11-22_recent.json", {"checkpoint_id": "recent"}, age_days=1)
        self._create_test_checkpoint("2025-11-20_also_recent.json", {"checkpoint_id": "also_recent"}, age_days=3)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        archived_count = manager.archive_old_checkpoints(retention_days=7)

        self.assertEqual(archived_count, 0)
        self.assertEqual(len(list(self.checkpoints_dir.glob("*.json"))), 2)


class TestRecoveryContext(unittest.TestCase):
    """FR-2: Recovery protocol context generation"""

    def setUp(self):
        """Create temp directory for test"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    def _create_test_checkpoint(self, filename: str, data: dict):
        """Helper to create test checkpoint file"""
        path = self.checkpoints_dir / filename
        with open(path, 'w') as f:
            json.dump(data, f)
        return path

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_get_recovery_context_includes_checkpoint(self):
        """Recovery context includes checkpoint data"""
        test_data = {
            "checkpoint_id": "test-123",
            "timestamp": "2025-11-22T10:00:00Z",
            "session_context_id": "test",
            "current_task": {"description": "Building feature X", "status": "in_progress", "progress_percentage": 60},
            "next_steps": ["Complete step 3", "Run tests"],
            "recovery_instructions": "Continue from checkpoint",
        }
        self._create_test_checkpoint("2025-11-22_test.json", test_data)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        context = manager.get_recovery_context()

        self.assertIn('checkpoint', context)
        self.assertEqual(context['checkpoint']['current_task']['description'], "Building feature X")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_get_recovery_context_includes_git_info(self):
        """Recovery context includes git history"""
        test_data = {
            "checkpoint_id": "test-123",
            "timestamp": "2025-11-22T10:00:00Z",
            "session_context_id": "test",
            "current_task": {"description": "Test", "status": "pending", "progress_percentage": 0},
        }
        self._create_test_checkpoint("2025-11-22_test.json", test_data)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        context = manager.get_recovery_context(include_git=True)

        self.assertIn('git_commits', context)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_get_recovery_context_graceful_without_checkpoint(self):
        """Recovery context gracefully handles no checkpoints (FR-2.3)"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        context = manager.get_recovery_context()

        self.assertIsNotNone(context)
        self.assertIsNone(context.get('checkpoint'))
        self.assertIn('message', context)  # Should have helpful message

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_recovery_context_format_for_display(self):
        """Recovery context can be formatted for user display"""
        test_data = {
            "checkpoint_id": "test-123",
            "timestamp": "2025-11-22T10:00:00Z",
            "session_context_id": "test",
            "current_task": {"description": "Building feature X", "status": "in_progress", "progress_percentage": 60},
            "next_steps": ["Complete step 3", "Run tests"],
            "recovery_instructions": "Continue from checkpoint",
        }
        self._create_test_checkpoint("2025-11-22_test.json", test_data)

        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        display_text = manager.format_recovery_for_display()

        self.assertIn("Building feature X", display_text)
        self.assertIn("60%", display_text)
        self.assertIn("Complete step 3", display_text)


class TestPerformanceRequirements(unittest.TestCase):
    """NFR-1: Performance requirements"""

    def setUp(self):
        """Create temp directory for test"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_checkpoint_creation_under_500ms(self):
        """Checkpoint creation completes in <500ms"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        start = time.time()
        manager.create_checkpoint(
            session_context_id="test_123",
            current_task={"description": "Performance test", "status": "pending", "progress_percentage": 0},
            todo_list=[{"content": f"Task {i}", "status": "pending"} for i in range(20)],
            files_modified=[f"file_{i}.py" for i in range(50)],
        )
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.5, f"Checkpoint creation took {elapsed:.3f}s, expected <0.5s")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_checkpoint_loading_under_200ms(self):
        """Checkpoint loading completes in <200ms"""
        # Create a checkpoint first
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)
        manager.create_checkpoint(
            session_context_id="test_123",
            current_task={"description": "Performance test", "status": "pending", "progress_percentage": 0},
        )

        start = time.time()
        manager.load_latest_checkpoint()
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.2, f"Checkpoint loading took {elapsed:.3f}s, expected <0.2s")


class TestStorageRequirements(unittest.TestCase):
    """NFR-3: Storage requirements"""

    def setUp(self):
        """Create temp directory for test"""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoints_dir = Path(self.test_dir) / "checkpoints"
        self.checkpoints_dir.mkdir()
        self.archive_dir = self.checkpoints_dir / "archive"
        self.archive_dir.mkdir()

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.test_dir)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "Implementation not yet created")
    def test_individual_checkpoint_under_50kb(self):
        """Individual checkpoint file is <50KB"""
        manager = CheckpointManager(checkpoints_dir=self.checkpoints_dir)

        # Create a reasonably-sized checkpoint
        path = manager.create_checkpoint(
            session_context_id="test_123",
            current_task={"description": "A typical task description", "status": "in_progress", "progress_percentage": 50},
            todo_list=[{"content": f"Task item {i} with description", "status": "pending"} for i in range(30)],
            key_decisions=["Decision 1: Use approach A", "Decision 2: Prioritize feature B"],
            files_modified=[f"claude/tools/file_{i}.py" for i in range(20)],
            recovery_instructions="Continue from step 5 of the implementation plan",
            next_steps=["Complete implementation", "Write tests", "Update documentation"],
        )

        size_kb = path.stat().st_size / 1024
        self.assertLess(size_kb, 50, f"Checkpoint size {size_kb:.1f}KB exceeds 50KB limit")


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
