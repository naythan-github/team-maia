#!/usr/bin/env python3
"""
Context File Compression Validation Tests

Validates that compressed versions of core context files preserve
essential functionality while achieving significant size reduction.

Files tested:
1. capability_index.md - Tool/agent registry
2. agents.md - Agent catalog
3. architecture_standards.md - Architecture documentation standards
4. development_workflow_protocol.md - Development workflow
"""

import re
from pathlib import Path

MAIA_ROOT = Path(__file__).parent.parent.parent.parent

# Original line counts for comparison
ORIGINALS = {
    "capability_index.md": 1599,
    "agents.md": 875,
    "architecture_standards.md": 663,
    "development_workflow_protocol.md": 403,
}


def get_file(name: str) -> Path:
    return MAIA_ROOT / "claude/context/core" / name


def test_all_files_exist():
    """All context files must exist."""
    for name in ORIGINALS:
        path = get_file(name)
        assert path.exists(), f"Missing: {path}"
    print("✅ All 4 files exist")


def test_size_reductions():
    """All files must achieve ≥40% size reduction."""
    results = []
    for name, original in ORIGINALS.items():
        current = len(get_file(name).read_text().splitlines())
        reduction = (original - current) / original * 100
        results.append((name, original, current, reduction))

    all_pass = True
    for name, orig, curr, red in results:
        status = "✅" if red >= 40 else "❌"
        if red < 40:
            all_pass = False
        print(f"{status} {name}: {red:.1f}% ({orig} → {curr})")

    assert all_pass, "Some files didn't achieve 40% reduction"


# === capability_index.md tests ===

def test_capability_index_has_tools():
    """Capability index must list tools."""
    content = get_file("capability_index.md").read_text().lower()
    tools = ["canonical_datetime", "feature_tracker", "email_rag", "pmp"]
    found = sum(1 for t in tools if t in content)
    assert found >= 3, f"Only {found}/4 key tools found"
    print(f"✅ capability_index: Tools present ({found}/4)")


def test_capability_index_has_agents():
    """Capability index must list agents."""
    content = get_file("capability_index.md").read_text().lower()
    agents = ["sre", "security", "azure", "data"]
    found = sum(1 for a in agents if a in content)
    assert found >= 3, f"Only {found}/4 key agents found"
    print(f"✅ capability_index: Agents present ({found}/4)")


def test_capability_index_has_locations():
    """Capability index must have file locations."""
    content = get_file("capability_index.md").read_text()
    assert "claude/tools/" in content, "Missing tool locations"
    assert "claude/agents/" in content, "Missing agent locations"
    print("✅ capability_index: File locations present")


def test_capability_index_complete():
    """Capability index must include all tools and agents from database."""
    content = get_file("capability_index.md").read_text()
    # Check for v3.0 Complete header
    assert "v3.0" in content, "Missing v3.0 version"
    assert "Complete" in content, "Missing 'Complete' marker"
    # Check tool count (should have 487 tools)
    assert "487 tools" in content, "Missing tool count"
    # Check agent count (should have 94 agents)
    assert "94 agents" in content, "Missing agent count"
    # Verify table rows exist (counting | patterns)
    table_rows = content.count("| `")
    assert table_rows >= 500, f"Only {table_rows} table entries, expected 500+"
    print(f"✅ capability_index: Complete ({table_rows} entries)")


# === agents.md tests ===

def test_agents_has_agent_list():
    """Agents file must list key agents."""
    content = get_file("agents.md").read_text().lower()
    agents = ["sre principal", "security", "azure", "devops", "data"]
    found = sum(1 for a in agents if a in content)
    assert found >= 4, f"Only {found}/5 key agents found"
    print(f"✅ agents.md: Key agents present ({found}/5)")


def test_agents_has_capabilities():
    """Agents file must describe capabilities."""
    content = get_file("agents.md").read_text().lower()
    keywords = ["capabilities", "purpose", "commands", "integration"]
    found = sum(1 for k in keywords if k in content)
    assert found >= 2, f"Only {found}/4 capability keywords found"
    print(f"✅ agents.md: Capability descriptions ({found}/4)")


# === architecture_standards.md tests ===

def test_architecture_has_template():
    """Architecture standards must have ARCHITECTURE.md template."""
    content = get_file("architecture_standards.md").read_text()
    assert "ARCHITECTURE.md" in content, "Missing ARCHITECTURE.md reference"
    sections = ["deployment", "topology", "integration", "operational"]
    found = sum(1 for s in sections if s.lower() in content.lower())
    assert found >= 3, f"Only {found}/4 template sections found"
    print(f"✅ architecture_standards: Template sections ({found}/4)")


def test_architecture_has_adr():
    """Architecture standards must have ADR template."""
    content = get_file("architecture_standards.md").read_text()
    assert "ADR" in content, "Missing ADR reference"
    adr_parts = ["context", "decision", "consequences", "alternatives"]
    found = sum(1 for p in adr_parts if p.lower() in content.lower())
    assert found >= 3, f"Only {found}/4 ADR sections found"
    print(f"✅ architecture_standards: ADR sections ({found}/4)")


def test_architecture_has_triggers():
    """Architecture standards must have documentation triggers."""
    content = get_file("architecture_standards.md").read_text().lower()
    triggers = ["infrastructure", "integration", "deployment", "multi-component"]
    found = sum(1 for t in triggers if t in content)
    assert found >= 3, f"Only {found}/4 triggers found"
    print(f"✅ architecture_standards: Triggers ({found}/4)")


# === development_workflow_protocol.md tests ===

def test_workflow_has_experimental():
    """Development workflow must reference experimental directory."""
    content = get_file("development_workflow_protocol.md").read_text()
    assert "experimental" in content.lower(), "Missing experimental reference"
    print("✅ development_workflow: Experimental directory")


def test_workflow_has_graduation():
    """Development workflow must have graduation process."""
    content = get_file("development_workflow_protocol.md").read_text().lower()
    keywords = ["graduation", "production", "archive"]
    found = sum(1 for k in keywords if k in content)
    assert found >= 2, f"Only {found}/3 workflow keywords"
    print(f"✅ development_workflow: Graduation process ({found}/3)")


def test_workflow_has_decision_tree():
    """Development workflow must have decision guidance."""
    content = get_file("development_workflow_protocol.md").read_text().lower()
    keywords = ["new", "modify", "test", "prototype"]
    found = sum(1 for k in keywords if k in content)
    assert found >= 3, f"Only {found}/4 decision keywords"
    print(f"✅ development_workflow: Decision guidance ({found}/4)")


def run_all_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("Context Compression Validation")
    print("=" * 60)

    tests = [
        test_all_files_exist,
        test_size_reductions,
        # capability_index.md
        test_capability_index_has_tools,
        test_capability_index_has_agents,
        test_capability_index_has_locations,
        test_capability_index_complete,
        # agents.md
        test_agents_has_agent_list,
        test_agents_has_capabilities,
        # architecture_standards.md
        test_architecture_has_template,
        test_architecture_has_adr,
        test_architecture_has_triggers,
        # development_workflow_protocol.md
        test_workflow_has_experimental,
        test_workflow_has_graduation,
        test_workflow_has_decision_tree,
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
