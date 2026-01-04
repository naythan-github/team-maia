"""
TDD Tests for CLAUDE.md v2.0 Compression

Validates that compressed CLAUDE.md retains all critical information.
Phase 234: CLAUDE.md compression validation
"""

import pytest
from pathlib import Path

MAIA_ROOT = Path(__file__).parent.parent
CLAUDE_MD = MAIA_ROOT / "CLAUDE.md"


@pytest.fixture
def claude_md_content():
    """Load CLAUDE.md content."""
    return CLAUDE_MD.read_text()


class TestQuickStart:
    """Verify Quick Start section exists and has key commands."""

    def test_init_command_present(self, claude_md_content):
        """Must have /init command documented."""
        assert "/init" in claude_md_content

    def test_close_session_command_present(self, claude_md_content):
        """Must have /close-session command documented."""
        assert "/close-session" in claude_md_content

    def test_quick_start_section_exists(self, claude_md_content):
        """Must have Quick Start section."""
        assert "## Quick Start" in claude_md_content


class TestContextLoadingProtocol:
    """Verify context loading protocol is documented."""

    def test_ufc_system_path(self, claude_md_content):
        """Must reference UFC system path."""
        assert "claude/context/ufc_system.md" in claude_md_content

    def test_context_id_method(self, claude_md_content):
        """Must document context ID retrieval."""
        assert "get_context_id" in claude_md_content

    def test_session_file_path(self, claude_md_content):
        """Must document session file location."""
        assert "swarm_session_" in claude_md_content

    def test_mandatory_ufc_loading(self, claude_md_content):
        """Must emphasize UFC loads first."""
        assert "MANDATORY" in claude_md_content or "mandatory" in claude_md_content.lower()


class TestWorkingPrinciples:
    """Verify all critical working principles are present."""

    CRITICAL_PRINCIPLES = [
        ("Read Context First", "context loading principle"),
        ("Execution State Machine", "discovery/execution mode"),
        ("Save State", "save state protocol"),
        ("TDD", "test-driven development"),
        ("Agent Persistence", "agent session management"),
        ("Local LLM", "cost savings with local models"),
        ("Experimental First", "experimental workflow"),
        ("integration", "integration testing requirement"),
    ]

    @pytest.mark.parametrize("principle,description", CRITICAL_PRINCIPLES)
    def test_critical_principle_present(self, claude_md_content, principle, description):
        """Each critical principle must be documented."""
        assert principle.lower() in claude_md_content.lower(), f"Missing: {description}"

    def test_working_principles_section_exists(self, claude_md_content):
        """Must have Working Principles section."""
        assert "## Working Principles" in claude_md_content


class TestKeyPaths:
    """Verify key file paths are documented."""

    CRITICAL_PATHS = [
        "claude/context/ufc_system.md",
        "claude/agents/",
        "claude/commands/",
        "claude/tools/",
        "claude/data/databases/",
        "user_preferences.json",
        "capability_index.md",
        "capabilities.db",  # DB-first principle
    ]

    @pytest.mark.parametrize("path", CRITICAL_PATHS)
    def test_critical_path_documented(self, claude_md_content, path):
        """Each critical path must be documented."""
        assert path in claude_md_content, f"Missing path: {path}"


class TestReferences:
    """Verify key reference documents are linked."""

    CRITICAL_REFS = [
        "smart_context_loading.md",
        "development_workflow_protocol.md",
        "tdd_development_protocol.md",
        "file_organization_policy.md",
    ]

    @pytest.mark.parametrize("ref", CRITICAL_REFS)
    def test_critical_reference_linked(self, claude_md_content, ref):
        """Each critical reference must be linked."""
        assert ref in claude_md_content, f"Missing reference: {ref}"


class TestSecurity:
    """Verify security section is present."""

    def test_security_section_exists(self, claude_md_content):
        """Must have Security section."""
        assert "## Security" in claude_md_content or "security" in claude_md_content.lower()

    def test_defensive_only_mentioned(self, claude_md_content):
        """Must mention defensive security only."""
        assert "defensive" in claude_md_content.lower()


class TestSystemIdentity:
    """Verify system identity is documented."""

    def test_maia_name_present(self, claude_md_content):
        """Must identify as Maia."""
        assert "Maia" in claude_md_content or "MAIA" in claude_md_content

    def test_system_identity_section(self, claude_md_content):
        """Must have System Identity section."""
        assert "System Identity" in claude_md_content


class TestVersioning:
    """Verify version is documented."""

    def test_version_present(self, claude_md_content):
        """Must have version number."""
        assert "v2.0" in claude_md_content or "v2" in claude_md_content


class TestNoRegressions:
    """Verify no critical content was lost."""

    def test_no_phase_references(self, claude_md_content):
        """Phase references should NOT be in CLAUDE.md.

        Design decision: Phase numbers are historical metadata that don't
        help Claude operate. They add noise without actionable information.
        Historical traceability belongs in SYSTEM_STATE.md, not CLAUDE.md.
        """
        import re
        phase_refs = re.findall(r'Phase \d+', claude_md_content)
        assert len(phase_refs) == 0, f"Found Phase references that should be removed: {phase_refs}"
