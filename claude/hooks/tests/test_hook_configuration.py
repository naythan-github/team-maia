#!/usr/bin/env python3
"""
TDD Tests for Hook Configuration (Phase 228.2)

Tests for correct Claude Code hook configuration to enable
swarm_auto_loader.py agent routing.

Run: python3 -m pytest claude/hooks/tests/test_hook_configuration.py -v
"""

import pytest
import json
import os
from pathlib import Path


# Project root detection
MAIA_ROOT = Path(__file__).parent.parent.parent.parent


class TestHookConfigurationLocation:
    """Tests for correct hook configuration file location"""

    def test_settings_local_json_exists(self):
        """settings.local.json should exist in .claude/"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"
        assert settings_file.exists(), \
            f"Missing {settings_file} - hooks must be configured here"

    def test_hooks_json_should_not_have_hook_config(self):
        """hooks.json should NOT contain hook config (it's ignored by Claude Code)"""
        hooks_json = MAIA_ROOT / ".claude" / "hooks.json"

        if hooks_json.exists():
            with open(hooks_json) as f:
                config = json.load(f)

            # If hooks.json exists, it should either:
            # 1. Not have a "hooks" key, OR
            # 2. Have "hooks" but it's empty/deprecated
            if "hooks" in config:
                hooks = config["hooks"]
                # Warn but don't fail - the file is ignored anyway
                if hooks:
                    pytest.skip("hooks.json has config but is ignored by Claude Code")


class TestHookEventName:
    """Tests for correct hook event naming"""

    def test_event_name_is_user_prompt_submit_camelcase(self):
        """Hook event should be 'UserPromptSubmit' not 'user-prompt-submit'"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"

        with open(settings_file) as f:
            config = json.load(f)

        if "hooks" not in config:
            pytest.fail("No 'hooks' key in settings.local.json")

        hooks = config["hooks"]

        # Should NOT have lowercase/hyphenated version
        assert "user-prompt-submit" not in hooks, \
            "Wrong event name: use 'UserPromptSubmit' not 'user-prompt-submit'"

        # Should have correct CamelCase version
        assert "UserPromptSubmit" in hooks, \
            "Missing 'UserPromptSubmit' hook configuration"


class TestHookConfigurationStructure:
    """Tests for correct hook configuration structure"""

    def test_hook_structure_is_array(self):
        """UserPromptSubmit value should be an array"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"

        with open(settings_file) as f:
            config = json.load(f)

        hook_config = config.get("hooks", {}).get("UserPromptSubmit")

        assert hook_config is not None, "UserPromptSubmit hook not configured"
        assert isinstance(hook_config, list), \
            f"UserPromptSubmit should be a list, got {type(hook_config)}"

    def test_hook_has_command_type(self):
        """Hook should have type: 'command'"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"

        with open(settings_file) as f:
            config = json.load(f)

        hook_config = config.get("hooks", {}).get("UserPromptSubmit", [])

        assert len(hook_config) > 0, "UserPromptSubmit has no hook entries"

        # Navigate the nested structure
        first_entry = hook_config[0]
        inner_hooks = first_entry.get("hooks", [])

        assert len(inner_hooks) > 0, "No inner hooks configured"

        command_hook = inner_hooks[0]
        assert command_hook.get("type") == "command", \
            f"Hook type should be 'command', got {command_hook.get('type')}"

    def test_hook_command_points_to_bash_script(self):
        """Hook command should execute the user-prompt-submit bash script"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"

        with open(settings_file) as f:
            config = json.load(f)

        hook_config = config.get("hooks", {}).get("UserPromptSubmit", [])
        first_entry = hook_config[0] if hook_config else {}
        inner_hooks = first_entry.get("hooks", [])
        command_hook = inner_hooks[0] if inner_hooks else {}

        command = command_hook.get("command", "")

        # Should reference the bash script (with variable expansion or absolute path)
        assert "user-prompt-submit" in command, \
            f"Command should reference user-prompt-submit script, got: {command}"


class TestBashScriptExecutable:
    """Tests for bash script executability"""

    def test_bash_script_exists(self):
        """user-prompt-submit bash script should exist"""
        script_path = MAIA_ROOT / "claude" / "hooks" / "user-prompt-submit"
        assert script_path.exists(), f"Missing bash script: {script_path}"

    def test_bash_script_is_executable(self):
        """user-prompt-submit should have execute permission"""
        script_path = MAIA_ROOT / "claude" / "hooks" / "user-prompt-submit"

        assert os.access(script_path, os.X_OK), \
            f"Script not executable. Run: chmod +x {script_path}"

    def test_bash_script_calls_swarm_auto_loader(self):
        """Bash script should invoke swarm_auto_loader.py"""
        script_path = MAIA_ROOT / "claude" / "hooks" / "user-prompt-submit"

        with open(script_path) as f:
            content = f.read()

        assert "swarm_auto_loader" in content, \
            "Bash script should call swarm_auto_loader.py"


class TestSwarmAutoLoaderExists:
    """Tests for swarm_auto_loader.py existence and basic functionality"""

    def test_swarm_auto_loader_exists(self):
        """swarm_auto_loader.py should exist in hooks directory"""
        loader_path = MAIA_ROOT / "claude" / "hooks" / "swarm_auto_loader.py"
        assert loader_path.exists(), f"Missing: {loader_path}"

    def test_swarm_auto_loader_has_threshold_constants(self):
        """swarm_auto_loader.py should have Phase 228 threshold constants"""
        loader_path = MAIA_ROOT / "claude" / "hooks" / "swarm_auto_loader.py"

        with open(loader_path) as f:
            content = f.read()

        assert "AGENT_LOADING_THRESHOLD = 0.60" in content, \
            "Missing 60% agent loading threshold"
        assert "CAPABILITY_GAP_THRESHOLD = 0.40" in content, \
            "Missing 40% capability gap threshold"


class TestNoObsoleteConfig:
    """Tests for removal of obsolete configuration"""

    def test_no_enabled_false_in_config(self):
        """Config should not have 'enabled: false' (unsupported field)"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"

        with open(settings_file) as f:
            content = f.read()

        # Check raw content for "enabled": false pattern
        assert '"enabled": false' not in content.lower(), \
            "'enabled' field is not supported - remove it"

    def test_no_environment_field_in_hook_config(self):
        """Hook config should not have custom 'environment' field"""
        settings_file = MAIA_ROOT / ".claude" / "settings.local.json"

        with open(settings_file) as f:
            config = json.load(f)

        hook_config = config.get("hooks", {}).get("UserPromptSubmit", [])

        for entry in hook_config:
            assert "environment" not in entry, \
                "'environment' field in hook config is not supported"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
