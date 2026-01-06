#!/usr/bin/env python3
"""
Test Suite: Save State System State DB Sync
Phase: 233.2 - Automation Gap Fix

Tests for the sync_system_state_db() method and integration into save_state.py.
Following TDD methodology: RED → GREEN → REFACTOR

Requirements from problem document:
1. Auto-run system_state_etl.py when SYSTEM_STATE.md is modified
2. Skip ETL when SYSTEM_STATE.md unchanged (optimization)
3. Handle ETL failures gracefully (non-blocking, like capabilities sync)
4. Both databases sync in single run

Agent: SRE Principal Engineer Agent
Date: 2026-01-06
"""

import pytest
import subprocess
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.sre.save_state import SaveState, ChangeAnalysis


class TestSystemStateDBSync:
    """Test suite for system_state.db synchronization"""

    @pytest.fixture
    def temp_maia_root(self, tmp_path):
        """Create temporary MAIA directory structure"""
        # Create directory structure
        tools_dir = tmp_path / "claude" / "tools" / "sre"
        tools_dir.mkdir(parents=True)

        agents_dir = tmp_path / "claude" / "agents"
        agents_dir.mkdir(parents=True)

        commands_dir = tmp_path / "claude" / "commands"
        commands_dir.mkdir(parents=True)

        db_dir = tmp_path / "claude" / "data" / "databases" / "system"
        db_dir.mkdir(parents=True)

        # Create mock system_state_etl.py
        etl_script = tools_dir / "system_state_etl.py"
        etl_script.write_text("""#!/usr/bin/env python3
import sys
print("ETL pipeline executed successfully")
print("Phases processed: 5")
sys.exit(0)
""")
        etl_script.chmod(0o755)

        # Create mock capabilities_registry.py
        registry_script = tools_dir / "capabilities_registry.py"
        registry_script.write_text("""#!/usr/bin/env python3
import sys
if len(sys.argv) > 1 and sys.argv[1] == "scan":
    print("Capabilities DB synced")
    print("Tools: 50, Agents: 10")
    sys.exit(0)
sys.exit(1)
""")
        registry_script.chmod(0o755)

        # Create SYSTEM_STATE.md
        system_state = tmp_path / "SYSTEM_STATE.md"
        system_state.write_text("""# SYSTEM_STATE.md

## 📄 PHASE 233: Save State Enforcement (2025-12-01) **COMPLETE**

### Achievement
Automated documentation sync.
""")

        return tmp_path

    @pytest.fixture
    def save_state(self, temp_maia_root):
        """Create SaveState instance with temp directory"""
        return SaveState(maia_root=temp_maia_root)

    # ========================================================================
    # TEST 1: SYSTEM_STATE.md Modified → ETL Runs
    # ========================================================================
    def test_system_state_sync_when_modified(self, save_state, temp_maia_root):
        """
        Test Case 1: When SYSTEM_STATE.md is modified, system_state_etl.py should execute.

        Given: SYSTEM_STATE.md has uncommitted changes
        When: save_state.py runs
        Then: system_state_etl.py executed, system_state.db synced
        """
        # Arrange: Create mock analysis showing SYSTEM_STATE.md modified
        analysis = ChangeAnalysis(
            new_tools=[],
            new_agents=[],
            new_commands=[],
            modified_files=["SYSTEM_STATE.md"],
            deleted_files=[],
            capability_index_modified=False,
            agents_md_modified=False,
            system_state_modified=True,  # Key: SYSTEM_STATE.md was modified
            claude_md_modified=False
        )

        # Act: Call sync_system_state_db method
        success, message = save_state.sync_system_state_db()

        # Assert: Method exists and returns success
        assert success is True, f"Expected success=True, got {success}"
        assert "System State DB synced" in message or "synced" in message.lower(), \
            f"Expected sync success message, got: {message}"

        # Verify ETL script was executed (check for output indicators)
        assert "ETL" in message or "Phases" in message or "processed" in message, \
            f"Expected ETL output in message, got: {message}"

    # ========================================================================
    # TEST 2: SYSTEM_STATE.md NOT Modified → ETL Skipped
    # ========================================================================
    def test_system_state_sync_skipped_when_not_modified(self, save_state, temp_maia_root):
        """
        Test Case 2: When SYSTEM_STATE.md is unchanged, ETL should be skipped.

        Given: SYSTEM_STATE.md unchanged
        When: save_state.py runs
        Then: system_state_etl.py NOT executed (optimization)
        """
        # Arrange: Create mock analysis showing SYSTEM_STATE.md NOT modified
        analysis = ChangeAnalysis(
            new_tools=["claude/tools/sre/new_tool.py"],
            new_agents=[],
            new_commands=[],
            modified_files=["claude/tools/sre/new_tool.py"],
            deleted_files=[],
            capability_index_modified=True,
            agents_md_modified=False,
            system_state_modified=False,  # Key: SYSTEM_STATE.md was NOT modified
            claude_md_modified=False
        )

        # Act: Run save_state with --check flag (don't actually commit)
        # We'll verify that sync_system_state_db is NOT called when system_state_modified=False
        # This will be tested via integration with run() method

        # For now, verify that the method CAN be called but returns gracefully
        success, message = save_state.sync_system_state_db()

        # Assert: Method works even when called unnecessarily
        # (actual skip logic will be in run() method via if analysis.system_state_modified check)
        assert isinstance(success, bool), "sync_system_state_db should return bool success status"
        assert isinstance(message, str), "sync_system_state_db should return string message"

    # ========================================================================
    # TEST 3: ETL Failure → Non-Blocking Warning
    # ========================================================================
    def test_system_state_sync_failure_is_non_blocking(self, save_state, temp_maia_root):
        """
        Test Case 3: When ETL fails, it should warn but not block commit.

        Given: system_state_etl.py returns non-zero exit code
        When: save_state.py runs
        Then: Warning displayed, commit proceeds (like capabilities sync)
        """
        # Arrange: Replace ETL script with one that fails
        etl_script = temp_maia_root / "claude" / "tools" / "sre" / "system_state_etl.py"
        etl_script.write_text("""#!/usr/bin/env python3
import sys
print("ETL ERROR: Database locked", file=sys.stderr)
sys.exit(1)
""")
        etl_script.chmod(0o755)

        # Act: Call sync_system_state_db
        success, message = save_state.sync_system_state_db()

        # Assert: Returns failure but in a non-blocking way (similar to capabilities sync)
        assert success is False, "Expected success=False when ETL fails"
        assert "warning" in message.lower() or "error" in message.lower(), \
            f"Expected warning/error message, got: {message}"

        # Verify message format matches capabilities sync pattern (has warning symbol)
        assert "⚠️" in message or "❌" in message, \
            f"Expected warning emoji in message, got: {message}"

    # ========================================================================
    # TEST 4: Both DBs Sync Together
    # ========================================================================
    def test_both_databases_sync_in_single_run(self, save_state, temp_maia_root):
        """
        Test Case 4: When both new tools and SYSTEM_STATE.md are modified, both DBs sync.

        Given: New tool added + SYSTEM_STATE.md updated
        When: save_state.py runs
        Then: Both capabilities.db AND system_state.db synced
        """
        # Arrange: Create analysis showing both conditions
        analysis = ChangeAnalysis(
            new_tools=["claude/tools/sre/new_monitoring_tool.py"],
            new_agents=[],
            new_commands=[],
            modified_files=[
                "claude/tools/sre/new_monitoring_tool.py",
                "SYSTEM_STATE.md",
                "claude/context/core/capability_index.md"
            ],
            deleted_files=[],
            capability_index_modified=True,
            agents_md_modified=False,
            system_state_modified=True,  # Key: Both conditions true
            claude_md_modified=False
        )

        # Act: Call both sync methods
        cap_success, cap_msg = save_state.sync_capabilities_db()
        state_success, state_msg = save_state.sync_system_state_db()

        # Assert: Both syncs succeed
        assert cap_success is True, f"Capabilities sync failed: {cap_msg}"
        assert state_success is True, f"System state sync failed: {state_msg}"

        # Verify both messages indicate success
        assert "Capabilities DB synced" in cap_msg or "synced" in cap_msg.lower(), \
            f"Expected capabilities sync message, got: {cap_msg}"
        assert "System State DB synced" in state_msg or "synced" in state_msg.lower(), \
            f"Expected system state sync message, got: {state_msg}"

    # ========================================================================
    # TEST 5: ETL Script Not Found → Graceful Handling
    # ========================================================================
    def test_system_state_sync_handles_missing_etl_script(self, save_state, temp_maia_root):
        """
        Test Case 5: When system_state_etl.py is missing, handle gracefully.

        Given: system_state_etl.py does not exist
        When: sync_system_state_db() is called
        Then: Returns failure with clear error message (non-blocking)
        """
        # Arrange: Remove ETL script
        etl_script = temp_maia_root / "claude" / "tools" / "sre" / "system_state_etl.py"
        etl_script.unlink()

        # Act: Call sync
        success, message = save_state.sync_system_state_db()

        # Assert: Returns failure with helpful message
        assert success is False, "Expected success=False when ETL script missing"
        assert "not found" in message.lower(), \
            f"Expected 'not found' in message, got: {message}"

    # ========================================================================
    # TEST 6: ETL Timeout → Graceful Handling
    # ========================================================================
    def test_system_state_sync_handles_timeout(self, save_state, temp_maia_root):
        """
        Test Case 6: When ETL times out, handle gracefully.

        Given: system_state_etl.py takes too long to execute
        When: sync_system_state_db() is called
        Then: Times out gracefully with warning message
        """
        # Arrange: Replace ETL script with one that sleeps
        etl_script = temp_maia_root / "claude" / "tools" / "sre" / "system_state_etl.py"
        etl_script.write_text("""#!/usr/bin/env python3
import time
time.sleep(120)  # Sleep longer than timeout
""")
        etl_script.chmod(0o755)

        # Act: Call sync (should timeout after 60s based on proposed implementation)
        success, message = save_state.sync_system_state_db()

        # Assert: Returns failure with timeout message
        # Note: This test may take up to 60s to run
        assert success is False, "Expected success=False when ETL times out"
        assert "timeout" in message.lower() or "timed out" in message.lower(), \
            f"Expected timeout message, got: {message}"


# ============================================================================
# INTEGRATION TESTS: run() Method Integration
# ============================================================================
class TestSaveStateRunIntegration:
    """Integration tests for sync_system_state_db in run() method"""

    @pytest.fixture
    def temp_git_repo(self, tmp_path):
        """Create temporary git repo with MAIA structure"""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)

        # Create MAIA structure
        tools_dir = tmp_path / "claude" / "tools" / "sre"
        tools_dir.mkdir(parents=True)

        # Create mock scripts
        etl_script = tools_dir / "system_state_etl.py"
        etl_script.write_text("""#!/usr/bin/env python3
print("ETL executed")
print("Phases: 5")
""")
        etl_script.chmod(0o755)

        registry_script = tools_dir / "capabilities_registry.py"
        registry_script.write_text("""#!/usr/bin/env python3
import sys
if len(sys.argv) > 1 and sys.argv[1] == "scan":
    print("Capabilities synced")
    sys.exit(0)
sys.exit(1)
""")
        registry_script.chmod(0o755)

        # Create and commit SYSTEM_STATE.md
        system_state = tmp_path / "SYSTEM_STATE.md"
        system_state.write_text("# SYSTEM_STATE\n\n## PHASE 233: Test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True)

        return tmp_path

    def test_run_calls_system_state_sync_when_modified(self, temp_git_repo, capsys, monkeypatch):
        """
        Integration Test: run() method calls sync_system_state_db when SYSTEM_STATE.md modified.

        Given: SYSTEM_STATE.md has uncommitted changes
        When: save_state.run() executes (mocked commit/push)
        Then: sync_system_state_db is called and output shows sync
        """
        # Arrange: Modify SYSTEM_STATE.md and stage it
        system_state = temp_git_repo / "SYSTEM_STATE.md"
        system_state.write_text("# SYSTEM_STATE\n\n## PHASE 234: New Phase")
        subprocess.run(["git", "add", "SYSTEM_STATE.md"], cwd=temp_git_repo, check=True)

        # Create capability_index.md to prevent blocking
        cap_index_dir = temp_git_repo / "claude" / "context" / "core"
        cap_index_dir.mkdir(parents=True, exist_ok=True)
        cap_index = cap_index_dir / "capability_index.md"
        cap_index.write_text("# Capability Index\n\n**Total**: 0 tools, 0 agents")

        # Mock commit_changes and push_changes to prevent actual git operations
        def mock_commit(self, message):
            return True, "✅ Mock commit"

        def mock_push(self):
            return True, "✅ Mock push"

        monkeypatch.setattr(SaveState, "commit_changes", mock_commit)
        monkeypatch.setattr(SaveState, "push_changes", mock_push)

        # Act: Run save_state (not check-only, so syncs will run)
        save_state = SaveState(maia_root=temp_git_repo)
        exit_code = save_state.run(check_only=False)

        # Capture output
        captured = capsys.readouterr()

        # Assert: System state sync was called
        assert "Syncing system state database" in captured.out or \
               "System State DB" in captured.out, \
            f"Expected system state sync output, got:\n{captured.out}"

    def test_run_skips_system_state_sync_when_not_modified(self, temp_git_repo, capsys, monkeypatch):
        """
        Integration Test: run() skips sync_system_state_db when SYSTEM_STATE.md not modified.

        Given: SYSTEM_STATE.md unchanged, other files modified
        When: save_state.run() executes (mocked commit/push)
        Then: sync_system_state_db is NOT called
        """
        # Arrange: Modify a non-tool file to avoid documentation checks
        # Create a simple README instead of a tool
        readme_file = temp_git_repo / "TEST_README.md"
        readme_file.write_text("# Test Documentation")

        # Stage the file so git sees it as modified
        subprocess.run(["git", "add", str(readme_file)], cwd=temp_git_repo, check=True)

        # Mock commit_changes and push_changes to prevent actual git operations
        def mock_commit(self, message):
            return True, "✅ Mock commit"

        def mock_push(self):
            return True, "✅ Mock push"

        monkeypatch.setattr(SaveState, "commit_changes", mock_commit)
        monkeypatch.setattr(SaveState, "push_changes", mock_push)

        # Act: Run save_state (not check-only, so syncs will run)
        save_state = SaveState(maia_root=temp_git_repo)
        exit_code = save_state.run(check_only=False)

        # Capture output
        captured = capsys.readouterr()

        # Assert: Capabilities sync was called (always runs)
        assert "Syncing capabilities database" in captured.out, \
            "Expected capabilities sync in output"

        # System state sync should be skipped (no mention of it, since SYSTEM_STATE.md not modified)
        assert "Syncing system state database" not in captured.out, \
            "System state sync should be skipped when SYSTEM_STATE.md not modified"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
