#!/usr/bin/env python3
"""
Test: Context ID Stability (Phase 134.4)

Purpose:
- Verify context ID is stable across multiple subprocess invocations
- Ensure same Claude Code window always gets same context ID
- Validate session file path consistency

Root Cause:
- PPID varies between bash shells, python scripts, and different invocations
- Original implementation used os.getppid() which changes per subprocess

Fix:
- Walk process tree to find stable Claude Code binary PID
- This PID is constant for entire Claude Code window lifecycle
"""

import sys
import subprocess
from pathlib import Path

# Add hooks to path for import
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT / "claude/hooks"))

from swarm_auto_loader import get_context_id, get_session_file_path


def test_context_id_stability():
    """Test: Context ID is stable across multiple invocations."""
    print("TEST: Context ID stability across 10 invocations")

    context_ids = []

    # Run 10 separate Python processes
    for i in range(10):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, 'claude/hooks'); "
                "from swarm_auto_loader import get_context_id; "
                "print(get_context_id())"
            ],
            capture_output=True,
            text=True,
            cwd=MAIA_ROOT
        )

        if result.returncode != 0:
            print(f"  ❌ Run {i+1} failed: {result.stderr}")
            return False

        context_id = result.stdout.strip()
        context_ids.append(context_id)
        print(f"  Run {i+1:2d}: {context_id}")

    # Check all IDs are identical
    unique_ids = set(context_ids)

    if len(unique_ids) == 1:
        print(f"  ✅ All 10 runs returned same context ID: {context_ids[0]}")
        return True
    else:
        print(f"  ❌ Found {len(unique_ids)} different context IDs: {unique_ids}")
        return False


def test_session_file_path_consistency():
    """Test: Session file path is consistent across invocations."""
    print("\nTEST: Session file path consistency")

    # Get session path from current process
    path1 = get_session_file_path()

    # Get session path from subprocess
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'claude/hooks'); "
            "from swarm_auto_loader import get_session_file_path; "
            "print(get_session_file_path())"
        ],
        capture_output=True,
        text=True,
        cwd=MAIA_ROOT
    )

    if result.returncode != 0:
        print(f"  ❌ Subprocess failed: {result.stderr}")
        return False

    path2 = Path(result.stdout.strip())

    print(f"  Current process: {path1}")
    print(f"  Subprocess:      {path2}")

    if path1 == path2:
        print(f"  ✅ Session file paths match")
        return True
    else:
        print(f"  ❌ Session file paths differ")
        return False


def test_context_id_format():
    """Test: Context ID is numeric (PID)."""
    print("\nTEST: Context ID format validation")

    context_id = get_context_id()
    print(f"  Context ID: {context_id}")

    # Should be numeric (PID)
    try:
        pid = int(context_id)
        if pid > 0:
            print(f"  ✅ Valid PID: {pid}")
            return True
        else:
            print(f"  ❌ Invalid PID (not positive): {pid}")
            return False
    except ValueError:
        print(f"  ❌ Not a valid PID (not numeric): {context_id}")
        return False


def test_multiple_bash_invocations():
    """Test: Context ID stable across bash subprocess invocations."""
    print("\nTEST: Context ID stability from bash commands")

    context_ids = []

    # Run 5 separate bash invocations
    for i in range(5):
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"cd {MAIA_ROOT} && python3 -c \"import sys; sys.path.insert(0, 'claude/hooks'); from swarm_auto_loader import get_context_id; print(get_context_id())\""
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"  ❌ Bash run {i+1} failed: {result.stderr}")
            return False

        context_id = result.stdout.strip()
        context_ids.append(context_id)
        print(f"  Bash run {i+1}: {context_id}")

    # Check all IDs are identical
    unique_ids = set(context_ids)

    if len(unique_ids) == 1:
        print(f"  ✅ All bash runs returned same context ID: {context_ids[0]}")
        return True
    else:
        print(f"  ❌ Found {len(unique_ids)} different context IDs from bash: {unique_ids}")
        return False


def main():
    """Run all context ID stability tests."""
    print("=" * 70)
    print("CONTEXT ID STABILITY TESTS (Phase 134.4)")
    print("=" * 70)

    tests = [
        test_context_id_stability,
        test_session_file_path_consistency,
        test_context_id_format,
        test_multiple_bash_invocations,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test.__name__}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL TESTS PASSED - Context ID stability verified")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Context ID may be unstable")
        return 1


if __name__ == "__main__":
    sys.exit(main())
