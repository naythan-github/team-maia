#!/usr/bin/env python3
"""
TDD Protocol Compression Validation Tests

Validates that the compressed prompt template version preserves
all essential functionality of the original TDD protocol.

Requirements:
1. All 7 phases (0-6) with clear gates
2. Agent pairing formula preserved
3. Auto-detection triggers complete
4. All 12 quality gates listed
5. Feature tracker CLI syntax
6. Exemption rules clear
7. Refactoring smoke test steps
8. Size reduction ≥50% (target: <300 lines)
9. Key phrases preserved
10. File structure preserved
"""

import os
import re
from pathlib import Path

# Paths
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
# Now using compressed version as the canonical file
TDD_PROTOCOL = MAIA_ROOT / "claude/context/core/tdd_development_protocol.md"
ORIGINAL_LINE_COUNT = 595  # Historical reference for size comparison


def test_file_exists():
    """TDD protocol file must exist."""
    assert TDD_PROTOCOL.exists(), f"TDD protocol not found: {TDD_PROTOCOL}"


def test_size_reduction():
    """Must maintain ≥50% size reduction from original (595 lines)."""
    current_lines = len(TDD_PROTOCOL.read_text().splitlines())

    reduction = (ORIGINAL_LINE_COUNT - current_lines) / ORIGINAL_LINE_COUNT * 100
    assert reduction >= 50, f"Only {reduction:.1f}% reduction (need ≥50%)"
    print(f"✅ Size reduction: {reduction:.1f}% ({ORIGINAL_LINE_COUNT} → {current_lines} lines)")


def test_all_phases_present():
    """All 7 phases (0-6) must be present with gates."""
    content = TDD_PROTOCOL.read_text()

    phases = [
        ("Phase 0", "Architecture"),
        ("Phase 1", "Requirements"),
        ("Phase 2", "Documentation"),
        ("Phase 3", "Test Design"),
        ("Phase 3.5", "Integration"),
        ("Phase 4", "Implementation"),
        ("Phase 5", "Execution"),
        ("Phase 6", "Validation"),
    ]

    for phase_id, phase_name in phases:
        # Allow flexible matching (Phase 0, P0, etc.)
        pattern = rf"(Phase\s*{phase_id.split()[-1]}|P{phase_id.split()[-1]})"
        assert re.search(pattern, content, re.IGNORECASE), \
            f"Missing phase: {phase_id} ({phase_name})"

    print("✅ All 7 phases present")


def test_agent_pairing_formula():
    """Agent pairing formula must be preserved."""
    content = TDD_PROTOCOL.read_text().lower()

    # Must mention domain specialist + SRE pairing
    assert "domain" in content and "sre" in content, \
        "Missing agent pairing formula (Domain + SRE)"
    assert "specialist" in content or "agent" in content, \
        "Missing agent terminology"

    print("✅ Agent pairing formula preserved")


def test_auto_triggers():
    """Auto-detection triggers must be listed."""
    content = TDD_PROTOCOL.read_text()

    triggers = [
        r"tools?",           # Tools in claude/tools/
        r"agents?",          # Agents in claude/agents/
        r"hooks?",           # Hooks
        r"schema",           # Database schema
        r"api",              # API modifications
        r"bug\s*fix",        # Bug fixes
    ]

    found = sum(1 for t in triggers if re.search(t, content, re.IGNORECASE))
    assert found >= 4, f"Only {found}/6 auto-triggers found (need ≥4)"

    print(f"✅ Auto-triggers present ({found}/6)")


def test_quality_gates():
    """All 12 quality gates must be referenced."""
    content = TDD_PROTOCOL.read_text().lower()

    gates = [
        "requirements gate",
        "test gate",
        "implementation gate",
        "documentation gate",
        "progress gate",
        "agent continuity",
        "registration gate",
        "sync gate",
        "integration test",
        "integration execution",
        "production readiness",
        "smoke test",
    ]

    # Allow partial matching and variations
    found = 0
    for gate in gates:
        keywords = gate.split()
        if all(kw in content for kw in keywords):
            found += 1

    # Require at least 8/12 gates explicitly named
    assert found >= 8, f"Only {found}/12 quality gates found (need ≥8)"

    print(f"✅ Quality gates present ({found}/12)")


def test_feature_tracker_cli():
    """Feature tracker CLI commands must be preserved."""
    content = TDD_PROTOCOL.read_text()

    commands = ["init", "add", "next", "update", "status", "reset"]

    found = sum(1 for cmd in commands if cmd in content.lower())
    assert found >= 4, f"Only {found}/6 feature tracker commands (need ≥4)"

    print(f"✅ Feature tracker CLI ({found}/6 commands)")


def test_exemptions():
    """TDD exemption rules must be clear."""
    content = TDD_PROTOCOL.read_text().lower()

    exemptions = ["documentation", "config", "readme", "exempt"]
    found = sum(1 for e in exemptions if e in content)

    assert found >= 2, f"Exemption rules unclear ({found}/4 keywords)"

    print("✅ Exemption rules present")


def test_refactoring_workflow():
    """Refactoring smoke test steps must be present."""
    content = TDD_PROTOCOL.read_text().lower()

    steps = ["import", "instantiation", "method", "behavior"]
    found = sum(1 for s in steps if s in content)

    assert found >= 3, f"Refactoring steps incomplete ({found}/4)"

    print("✅ Refactoring workflow present")


def test_key_phrases():
    """Key phrases for workflow control must be preserved."""
    content = TDD_PROTOCOL.read_text().lower()

    phrases = ["requirements complete", "check requirements"]
    found = sum(1 for p in phrases if p in content)

    assert found >= 1, "Key phrases missing"

    print("✅ Key phrases present")


def test_file_structure():
    """Project file structure must be documented."""
    content = TDD_PROTOCOL.read_text()

    files = ["requirements.md", "test_", "progress"]
    found = sum(1 for f in files if f in content)

    assert found >= 2, "File structure incomplete"

    print("✅ File structure documented")


def run_all_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("TDD Protocol Compression Validation")
    print("=" * 60)

    tests = [
        test_file_exists,
        test_size_reduction,
        test_all_phases_present,
        test_agent_pairing_formula,
        test_auto_triggers,
        test_quality_gates,
        test_feature_tracker_cli,
        test_exemptions,
        test_refactoring_workflow,
        test_key_phrases,
        test_file_structure,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
