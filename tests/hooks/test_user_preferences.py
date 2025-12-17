#!/usr/bin/env python3
"""
Test suite for Phase 207: User-Specific Default Agent Preferences

Tests the user preference loading and default agent selection logic.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add claude/hooks to path for imports
_maia_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_maia_root / "claude" / "hooks"))

# Import functions to test
from swarm_auto_loader import load_user_preferences, MAIA_ROOT


def test_load_user_preferences_valid():
    """Test loading valid user preferences."""
    print("\n1. Testing valid user preferences...")

    prefs = load_user_preferences()

    # Should load the actual user_preferences.json
    assert prefs["default_agent"] == "sre_principal_engineer_agent", \
        f"Expected SRE agent, got {prefs['default_agent']}"
    assert prefs["fallback_agent"] == "sre_principal_engineer_agent", \
        f"Expected SRE fallback, got {prefs['fallback_agent']}"

    print("   ✅ Valid preferences loaded correctly")


def test_load_user_preferences_missing_file():
    """Test graceful fallback when preferences file missing."""
    print("\n2. Testing missing preferences file...")

    # Temporarily rename the preferences file
    prefs_file = MAIA_ROOT / "claude" / "data" / "user_preferences.json"
    backup_file = prefs_file.with_suffix(".json.backup")

    file_existed = False
    if prefs_file.exists():
        file_existed = True
        prefs_file.rename(backup_file)

    try:
        prefs = load_user_preferences()

        # Should fall back to defaults
        assert prefs["default_agent"] == "sre_principal_engineer_agent", \
            f"Expected SRE fallback, got {prefs['default_agent']}"
        assert prefs["fallback_agent"] == "sre_principal_engineer_agent", \
            f"Expected SRE fallback, got {prefs['fallback_agent']}"

        print("   ✅ Graceful fallback to defaults works")

    finally:
        # Restore original file
        if file_existed:
            backup_file.rename(prefs_file)


def test_load_user_preferences_malformed_json():
    """Test graceful fallback with malformed JSON."""
    print("\n3. Testing malformed JSON...")

    prefs_file = MAIA_ROOT / "claude" / "data" / "user_preferences.json"
    backup_file = prefs_file.with_suffix(".json.backup")

    # Backup original
    if prefs_file.exists():
        prefs_file.rename(backup_file)

    try:
        # Write malformed JSON
        with open(prefs_file, 'w') as f:
            f.write("{ invalid json }")

        prefs = load_user_preferences()

        # Should fall back to defaults
        assert prefs["default_agent"] == "sre_principal_engineer_agent", \
            f"Expected SRE fallback, got {prefs['default_agent']}"

        print("   ✅ Graceful fallback with malformed JSON works")

    finally:
        # Restore original
        prefs_file.unlink(missing_ok=True)
        if backup_file.exists():
            backup_file.rename(prefs_file)


def test_load_user_preferences_missing_field():
    """Test graceful fallback when default_agent field missing."""
    print("\n4. Testing missing required field...")

    prefs_file = MAIA_ROOT / "claude" / "data" / "user_preferences.json"
    backup_file = prefs_file.with_suffix(".json.backup")

    # Backup original
    if prefs_file.exists():
        prefs_file.rename(backup_file)

    try:
        # Write preferences without default_agent field
        with open(prefs_file, 'w') as f:
            json.dump({"version": "1.0"}, f)

        prefs = load_user_preferences()

        # Should fall back to defaults
        assert prefs["default_agent"] == "sre_principal_engineer_agent", \
            f"Expected SRE fallback, got {prefs['default_agent']}"

        print("   ✅ Graceful fallback with missing field works")

    finally:
        # Restore original
        prefs_file.unlink(missing_ok=True)
        if backup_file.exists():
            backup_file.rename(prefs_file)


def test_agent_file_existence():
    """Test that configured default agent file exists."""
    print("\n5. Testing agent file existence...")

    prefs = load_user_preferences()
    default_agent = prefs["default_agent"]

    # Check for agent file (with or without _agent suffix)
    agent_file = MAIA_ROOT / "claude" / "agents" / f"{default_agent}.md"
    if not agent_file.exists():
        agent_file = MAIA_ROOT / "claude" / "agents" / f"{default_agent}_agent.md"

    assert agent_file.exists(), \
        f"Agent file not found: {agent_file}"

    print(f"   ✅ Agent file exists: {agent_file.name}")


def test_fallback_agent_file_existence():
    """Test that configured fallback agent file exists."""
    print("\n6. Testing fallback agent file existence...")

    prefs = load_user_preferences()
    fallback_agent = prefs["fallback_agent"]

    # Check for agent file
    agent_file = MAIA_ROOT / "claude" / "agents" / f"{fallback_agent}.md"
    if not agent_file.exists():
        agent_file = MAIA_ROOT / "claude" / "agents" / f"{fallback_agent}_agent.md"

    assert agent_file.exists(), \
        f"Fallback agent file not found: {agent_file}"

    print(f"   ✅ Fallback agent file exists: {agent_file.name}")


def run_all_tests():
    """Run all test cases."""
    print("=" * 60)
    print("Phase 207: User Preferences Test Suite")
    print("=" * 60)

    tests = [
        test_load_user_preferences_valid,
        test_load_user_preferences_missing_file,
        test_load_user_preferences_malformed_json,
        test_load_user_preferences_missing_field,
        test_agent_file_existence,
        test_fallback_agent_file_existence,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
