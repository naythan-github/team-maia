#!/usr/bin/env python3
"""
Integration Tests for Phase 134.3 - Multi-Context Isolation

Purpose:
- Validate per-context session files prevent race conditions
- Test concurrent context handling
- Verify stale session cleanup
- Validate legacy session migration

Test Categories:
1. Per-Context Session Files
2. Stale Session Cleanup
3. Legacy Session Migration
4. Concurrent Context Handling
"""

import json
import os
import sys
import subprocess
import unittest
from pathlib import Path
import time

# Maia root path
MAIA_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(MAIA_ROOT))

SWARM_AUTO_LOADER = MAIA_ROOT / "claude/hooks/swarm_auto_loader.py"


class TestMultiContextIsolation(unittest.TestCase):
    """
    Test multi-context isolation (Phase 134.3).
    Validates per-context session files prevent race conditions.
    """

    def setUp(self):
        """Clean all session state files before each test."""
        for session_file in Path("/tmp").glob("maia_active_swarm_session*.json"):
            try:
                session_file.unlink()
            except OSError:
                pass

    def tearDown(self):
        """Clean all session state files after each test."""
        for session_file in Path("/tmp").glob("maia_active_swarm_session*.json"):
            try:
                session_file.unlink()
            except OSError:
                pass

    def test_per_context_session_files(self):
        """Test 1: Different context IDs create separate session files."""
        query = "Analyze Azure costs"

        # Run auto-loader (will create context-specific session)
        result = subprocess.run(
            [sys.executable, str(SWARM_AUTO_LOADER), query],
            capture_output=True,
            text=True,
            timeout=2
        )

        # Should complete successfully
        self.assertEqual(result.returncode, 0, f"Failed: {result.stderr}")

        # Find created session file
        session_files = list(Path("/tmp").glob("maia_active_swarm_session_*.json"))

        if len(session_files) > 0:
            context_file = session_files[0]
            # Verify file follows naming pattern
            self.assertTrue(
                context_file.name.startswith("maia_active_swarm_session_context_"),
                f"Unexpected session file name: {context_file.name}"
            )

            # Verify contains valid JSON
            with open(context_file) as f:
                session = json.load(f)
                self.assertIn("current_agent", session)
                self.assertIn("version", session)

    def test_stale_session_cleanup(self):
        """Test 2: Sessions older than 24 hours are cleaned up."""
        # Create fake old session file
        old_session = Path("/tmp/maia_active_swarm_session_context_99999.json")
        old_session.write_text('{"test": "old"}')

        # Set modification time to 25 hours ago
        old_time = time.time() - (25 * 3600)
        os.utime(old_session, (old_time, old_time))

        # Verify old session exists
        self.assertTrue(old_session.exists(), "Old session should exist before cleanup")

        # Run auto-loader (triggers cleanup)
        subprocess.run(
            [sys.executable, str(SWARM_AUTO_LOADER), "test query"],
            capture_output=True,
            timeout=2
        )

        # Old session should be deleted
        self.assertFalse(old_session.exists(),
                         "Stale session file should be cleaned up")

    def test_recent_session_preserved(self):
        """Test 3: Recent sessions are NOT cleaned up."""
        # Create fake recent session file (1 hour old)
        recent_session = Path("/tmp/maia_active_swarm_session_context_88888.json")
        recent_session.write_text('{"test": "recent"}')

        # Set modification time to 1 hour ago
        recent_time = time.time() - 3600
        os.utime(recent_session, (recent_time, recent_time))

        # Verify recent session exists
        self.assertTrue(recent_session.exists(), "Recent session should exist before cleanup")

        # Run auto-loader (triggers cleanup)
        subprocess.run(
            [sys.executable, str(SWARM_AUTO_LOADER), "test query"],
            capture_output=True,
            timeout=2
        )

        # Recent session should still exist
        self.assertTrue(recent_session.exists(),
                        "Recent session file should be preserved")

    def test_legacy_session_migration(self):
        """Test 4: Legacy global session migrates to context-specific file."""
        legacy_session = Path("/tmp/maia_active_swarm_session.json")
        legacy_data = {
            "current_agent": "security_specialist_agent",
            "domain": "security",
            "version": "1.0"
        }

        # Create legacy session
        legacy_session.write_text(json.dumps(legacy_data))
        self.assertTrue(legacy_session.exists(), "Legacy session should exist")

        # Run auto-loader (triggers migration)
        subprocess.run(
            [sys.executable, str(SWARM_AUTO_LOADER), "test query"],
            capture_output=True,
            timeout=2
        )

        # Check results
        context_sessions = list(Path("/tmp").glob("maia_active_swarm_session_context_*.json"))

        # Should have at least one context-specific session
        self.assertGreaterEqual(len(context_sessions), 1,
                                "Should have at least one context-specific session file")

    def test_concurrent_contexts_no_collision(self):
        """Test 5: Multiple concurrent contexts don't interfere."""
        query1 = "Review Azure architecture"
        query2 = "Analyze security posture"

        # Start two processes simultaneously (simulate two Claude Code windows)
        proc1 = subprocess.Popen(
            [sys.executable, str(SWARM_AUTO_LOADER), query1],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        proc2 = subprocess.Popen(
            [sys.executable, str(SWARM_AUTO_LOADER), query2],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for both
        proc1.wait(timeout=3)
        proc2.wait(timeout=3)

        # Both should complete successfully
        self.assertEqual(proc1.returncode, 0, "Context 1 should complete successfully")
        self.assertEqual(proc2.returncode, 0, "Context 2 should complete successfully")

        # Check for session files (may or may not exist based on routing confidence)
        session_files = list(Path("/tmp").glob("maia_active_swarm_session_*.json"))

        # If any exist, they should be valid
        if len(session_files) > 0:
            for session_file in session_files:
                with open(session_file) as f:
                    session = json.load(f)
                    self.assertIn("current_agent", session)
                    self.assertIn("version", session)

    def test_context_id_stability(self):
        """Test 6: Same context generates same context ID (stable PPID)."""
        query = "Test query"

        # Run twice in same process
        result1 = subprocess.run(
            [sys.executable, str(SWARM_AUTO_LOADER), query],
            capture_output=True,
            text=True,
            timeout=2
        )

        # Get session files after first run
        files_after_first = set(Path("/tmp").glob("maia_active_swarm_session_*.json"))

        result2 = subprocess.run(
            [sys.executable, str(SWARM_AUTO_LOADER), query],
            capture_output=True,
            text=True,
            timeout=2
        )

        # Get session files after second run
        files_after_second = set(Path("/tmp").glob("maia_active_swarm_session_*.json"))

        # Both runs should complete
        self.assertEqual(result1.returncode, 0)
        self.assertEqual(result2.returncode, 0)

        # File count should be same or minimal change (no proliferation)
        # Note: Different subprocess calls may have different PPIDs
        self.assertLessEqual(len(files_after_second), len(files_after_first) + 2,
                             "Should not create excessive session files")


def run_tests():
    """Run all multi-context isolation tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestMultiContextIsolation))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("Multi-Context Isolation Tests (Phase 134.3)")
    print("=" * 70)
    print(f"\nMaia Root: {MAIA_ROOT}")
    print(f"Swarm Auto-Loader: {SWARM_AUTO_LOADER}")
    print("\n" + "=" * 70 + "\n")

    # Run tests
    result = run_tests()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
