#!/usr/bin/env python3
"""
TDD Tests for setup.sh post-clone configuration requirements.

These tests verify that all necessary components are properly configured
after running setup.sh on a fresh clone.

Run with: pytest tests/test_setup_requirements.py -v
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Get MAIA_ROOT from environment or calculate from test location
MAIA_ROOT = Path(os.environ.get('MAIA_ROOT', Path(__file__).parent.parent))
HOME = Path.home()
MAIA_USER_DIR = HOME / '.maia'


class TestUserDirectoryStructure:
    """Test ~/.maia/ directory structure creation."""

    def test_maia_user_dir_exists(self):
        """~/.maia/ directory should exist."""
        assert MAIA_USER_DIR.exists(), f"Missing: {MAIA_USER_DIR}"

    def test_maia_data_dir_exists(self):
        """~/.maia/data/ directory should exist."""
        assert (MAIA_USER_DIR / 'data').exists()

    def test_maia_sessions_dir_exists(self):
        """~/.maia/sessions/ directory should exist."""
        assert (MAIA_USER_DIR / 'sessions').exists()

    def test_maia_context_personal_dir_exists(self):
        """~/.maia/context/personal/ directory should exist."""
        assert (MAIA_USER_DIR / 'context' / 'personal').exists()

    def test_maia_checkpoints_dir_exists(self):
        """~/.maia/data/checkpoints/ directory should exist."""
        assert (MAIA_USER_DIR / 'data' / 'checkpoints').exists()


class TestUserPreferences:
    """Test user preferences initialization."""

    def test_user_preferences_file_exists(self):
        """User preferences file should exist."""
        prefs_path = MAIA_USER_DIR / 'data' / 'user_preferences.json'
        assert prefs_path.exists(), f"Missing: {prefs_path}"

    def test_user_preferences_valid_json(self):
        """User preferences should be valid JSON."""
        prefs_path = MAIA_USER_DIR / 'data' / 'user_preferences.json'
        if prefs_path.exists():
            with open(prefs_path) as f:
                prefs = json.load(f)
            assert isinstance(prefs, dict)

    def test_user_preferences_has_default_agent(self):
        """User preferences should have default_agent key."""
        prefs_path = MAIA_USER_DIR / 'data' / 'user_preferences.json'
        if prefs_path.exists():
            with open(prefs_path) as f:
                prefs = json.load(f)
            assert 'default_agent' in prefs

    def test_user_preferences_has_handoffs_enabled(self):
        """User preferences should have handoffs_enabled key."""
        prefs_path = MAIA_USER_DIR / 'data' / 'user_preferences.json'
        if prefs_path.exists():
            with open(prefs_path) as f:
                prefs = json.load(f)
            assert 'handoffs_enabled' in prefs


class TestPersonalProfile:
    """Test personal profile template creation."""

    def test_personal_profile_exists(self):
        """Personal profile template should exist."""
        profile_path = MAIA_USER_DIR / 'context' / 'personal' / 'profile.md'
        assert profile_path.exists(), f"Missing: {profile_path}"

    def test_personal_profile_has_content(self):
        """Personal profile should have template content."""
        profile_path = MAIA_USER_DIR / 'context' / 'personal' / 'profile.md'
        if profile_path.exists():
            content = profile_path.read_text()
            assert len(content) > 50, "Profile should have meaningful content"
            assert 'Profile' in content or 'Identity' in content


class TestClaudeCodeHooks:
    """Test Claude Code hooks configuration."""

    def test_claude_dir_exists(self):
        """Project .claude/ directory should exist."""
        claude_dir = MAIA_ROOT / '.claude'
        assert claude_dir.exists(), f"Missing: {claude_dir}"

    def test_settings_local_exists(self):
        """Claude Code settings.local.json should exist."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        assert settings_path.exists(), f"Missing: {settings_path}"

    def test_settings_local_valid_json(self):
        """settings.local.json should be valid JSON."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            assert isinstance(settings, dict)

    def test_settings_has_hooks_section(self):
        """settings.local.json should have hooks section."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            assert 'hooks' in settings, "Missing 'hooks' section"

    def test_user_prompt_submit_hook_configured(self):
        """UserPromptSubmit hook should be configured."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            hooks = settings.get('hooks', {})
            assert 'UserPromptSubmit' in hooks, "Missing UserPromptSubmit hook"

    def test_post_tool_use_hook_configured(self):
        """PostToolUse hook should be configured."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            hooks = settings.get('hooks', {})
            assert 'PostToolUse' in hooks, "Missing PostToolUse hook"

    def test_session_start_hook_configured(self):
        """SessionStart hook should be configured."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            hooks = settings.get('hooks', {})
            assert 'SessionStart' in hooks, "Missing SessionStart hook"

    def test_pre_compact_hook_configured(self):
        """PreCompact hook should be configured."""
        settings_path = MAIA_ROOT / '.claude' / 'settings.local.json'
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            hooks = settings.get('hooks', {})
            assert 'PreCompact' in hooks, "Missing PreCompact hook"


class TestClaudeCodeSkills:
    """Test Claude Code skills (commands) setup."""

    def test_commands_dir_exists(self):
        """Project .claude/commands/ directory should exist."""
        commands_dir = MAIA_ROOT / '.claude' / 'commands'
        assert commands_dir.exists(), f"Missing: {commands_dir}"

    def test_init_skill_exists(self):
        """/init skill should be available."""
        init_path = MAIA_ROOT / '.claude' / 'commands' / 'init.md'
        assert init_path.exists(), f"Missing: {init_path}"

    def test_init_skill_is_symlink_or_file(self):
        """/init skill should be a symlink to claude/commands/init.md or a file."""
        init_path = MAIA_ROOT / '.claude' / 'commands' / 'init.md'
        if init_path.exists():
            # Either symlink or regular file is acceptable
            assert init_path.is_file() or init_path.is_symlink()

    def test_close_session_skill_exists(self):
        """/close-session skill should be available."""
        skill_path = MAIA_ROOT / '.claude' / 'commands' / 'close-session.md'
        assert skill_path.exists(), f"Missing: {skill_path}"

    def test_handoff_status_skill_exists(self):
        """/handoff-status skill should be available."""
        skill_path = MAIA_ROOT / '.claude' / 'commands' / 'handoff-status.md'
        assert skill_path.exists(), f"Missing: {skill_path}"

    def test_capture_skill_exists(self):
        """/capture skill should be available."""
        skill_path = MAIA_ROOT / '.claude' / 'commands' / 'capture.md'
        assert skill_path.exists(), f"Missing: {skill_path}"

    def test_checkpoint_skill_exists(self):
        """/checkpoint skill should be available."""
        skill_path = MAIA_ROOT / '.claude' / 'commands' / 'checkpoint.md'
        assert skill_path.exists(), f"Missing: {skill_path}"


class TestGitHooks:
    """Test Git hooks installation."""

    def test_git_hooks_dir_exists(self):
        """.git/hooks/ directory should exist."""
        hooks_dir = MAIA_ROOT / '.git' / 'hooks'
        assert hooks_dir.exists(), f"Missing: {hooks_dir}"

    def test_pre_commit_hook_exists(self):
        """pre-commit hook should be installed."""
        hook_path = MAIA_ROOT / '.git' / 'hooks' / 'pre-commit'
        assert hook_path.exists(), f"Missing: {hook_path}"

    def test_pre_commit_hook_executable(self):
        """pre-commit hook should be executable."""
        hook_path = MAIA_ROOT / '.git' / 'hooks' / 'pre-commit'
        if hook_path.exists():
            assert os.access(hook_path, os.X_OK), "pre-commit hook not executable"


class TestDatabaseInitialization:
    """Test database initialization."""

    def test_system_databases_dir_exists(self):
        """System databases directory should exist."""
        db_dir = MAIA_ROOT / 'claude' / 'data' / 'databases' / 'system'
        assert db_dir.exists(), f"Missing: {db_dir}"

    def test_intelligence_databases_dir_exists(self):
        """Intelligence databases directory should exist."""
        db_dir = MAIA_ROOT / 'claude' / 'data' / 'databases' / 'intelligence'
        assert db_dir.exists(), f"Missing: {db_dir}"

    def test_capabilities_db_exists(self):
        """capabilities.db should exist."""
        db_path = MAIA_ROOT / 'claude' / 'data' / 'databases' / 'system' / 'capabilities.db'
        assert db_path.exists(), f"Missing: {db_path}"

    def test_capabilities_db_has_data(self):
        """capabilities.db should have data."""
        import sqlite3
        db_path = MAIA_ROOT / 'claude' / 'data' / 'databases' / 'system' / 'capabilities.db'
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM capabilities")
            count = cursor.fetchone()[0]
            conn.close()
            assert count > 0, "capabilities.db has no data"


class TestEnvironmentSetup:
    """Test environment variable setup."""

    def test_maia_root_in_environment(self):
        """MAIA_ROOT should be set in environment."""
        assert 'MAIA_ROOT' in os.environ or MAIA_ROOT.exists()

    def test_pythonpath_includes_maia(self):
        """PYTHONPATH should include MAIA_ROOT for imports."""
        # Test by trying to import a core module
        try:
            from claude.tools.core.paths import MAIA_ROOT as imported_root
            assert imported_root is not None
        except ImportError:
            pytest.fail("Cannot import claude.tools.core.paths - PYTHONPATH may not be set")


class TestHealthChecks:
    """Test overall health of setup."""

    def test_core_paths_importable(self):
        """Core paths module should be importable."""
        try:
            from claude.tools.core.paths import MAIA_ROOT
            assert MAIA_ROOT is not None
        except ImportError:
            pytest.fail("Cannot import claude.tools.core.paths")

    def test_swarm_auto_loader_importable(self):
        """Swarm auto loader should be importable."""
        try:
            from claude.hooks.swarm_auto_loader import get_context_id
            assert callable(get_context_id)
        except ImportError:
            pytest.fail("Cannot import claude.hooks.swarm_auto_loader")

    def test_learning_session_importable(self):
        """Learning session module should be importable."""
        try:
            from claude.tools.learning.session import get_session_manager
            assert callable(get_session_manager)
        except ImportError:
            pytest.fail("Cannot import claude.tools.learning.session")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
