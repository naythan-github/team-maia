#!/usr/bin/env python3
"""
Comprehensive tests for validate_file_location tool (TDD Compliance).

Run with: pytest tests/test_validate_file_location_comprehensive.py -v
"""

import pytest
from pathlib import Path
import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude.tools.validate_file_location import (
    validate_file_location,
    is_work_output,
    matches_ufc_structure,
    get_ufc_compliant_path,
    infer_project,
    MAIA_ROOT,
    MAX_FILE_SIZE_MB,
    ALLOWED_ROOT_FILES
)


class TestWorkOutputDetection:
    """FR2: Work output detection - All test cases from requirements."""

    def test_purpose_keyword_analysis(self):
        """Keyword 'analysis' in purpose should be detected."""
        assert is_work_output("ServiceDesk analysis report", Path("report.xlsx")) == True

    def test_purpose_keyword_summary(self):
        """Keyword 'summary' in purpose should be detected."""
        assert is_work_output("summary report", Path("data.md")) == True

    def test_purpose_keyword_deliverable(self):
        """Keyword 'deliverable' in purpose should be detected."""
        assert is_work_output("client deliverable", Path("doc.pdf")) == True

    def test_filename_pattern_servicedesk(self):
        """Filename with ServiceDesk should be detected."""
        assert is_work_output("database", Path("ServiceDesk_Analysis.xlsx")) == True

    def test_filename_pattern_infrastructure(self):
        """Filename with Infrastructure should be detected."""
        assert is_work_output("data", Path("Infrastructure_Team_Data.csv")) == True

    def test_filename_pattern_l2(self):
        """Filename with L2_ should be detected."""
        assert is_work_output("test", Path("L2_Test_Results.md")) == True

    def test_maia_system_file_not_work_output(self):
        """Maia system files should NOT be work output."""
        assert is_work_output("Maia tool implementation", Path("tool.py")) == False

    def test_case_insensitive_matching(self):
        """Keyword matching should be case-insensitive."""
        assert is_work_output("ANALYSIS REPORT", Path("file.xlsx")) == True
        assert is_work_output("Summary Data", Path("file.csv")) == True


class TestFileSizeEnforcement:
    """FR3: File size enforcement - All test cases from requirements."""

    def test_large_file_rejected(self):
        """Files >10 MB should be rejected."""
        # Create temporary large file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * (11 * 1024 * 1024))  # 11 MB
            temp_path = f.name

        try:
            result = validate_file_location(temp_path, "test database")
            assert result['valid'] == False
            assert "10 MB" in result['reason']
            assert "11." in result['reason']  # Shows actual size
        finally:
            os.unlink(temp_path)

    def test_rag_database_exemption(self):
        """RAG databases >10 MB should be allowed."""
        # Create temporary large file in rag_databases path
        rag_path = MAIA_ROOT / "claude/data/rag_databases"
        rag_path.mkdir(parents=True, exist_ok=True)

        temp_file = rag_path / "test_vectors.db"
        with open(temp_file, 'wb') as f:
            f.write(b'0' * (50 * 1024 * 1024))  # 50 MB

        try:
            result = validate_file_location(str(temp_file), "RAG vector database")
            # Should not fail on size (other checks may still apply)
            assert "10 MB" not in result['reason'] or result['valid'] == True
        finally:
            temp_file.unlink()

    def test_small_file_accepted(self):
        """Files <10 MB should pass size check."""
        # Create temporary small file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * (5 * 1024 * 1024))  # 5 MB
            temp_path = f.name

        try:
            result = validate_file_location(temp_path, "small database")
            # Should not fail on size (may fail on other checks)
            assert "10 MB" not in result['reason']
        finally:
            os.unlink(temp_path)


class TestUFCStructureValidation:
    """FR4: UFC structure validation - All test cases from requirements."""

    def test_valid_agent_path(self):
        """claude/agents/*.md should be valid."""
        assert matches_ufc_structure(Path("claude/agents/test_agent.md")) == True

    def test_valid_tool_path(self):
        """claude/tools/*.py should be valid."""
        assert matches_ufc_structure(Path("claude/tools/test_tool.py")) == True

    def test_valid_test_path(self):
        """tests/*.py should be valid (exception)."""
        assert matches_ufc_structure(Path("tests/test_something.py")) == True

    def test_invalid_random_file(self):
        """Random files not in UFC should be invalid."""
        assert matches_ufc_structure(Path("random_file.md")) == False

    def test_invalid_second_level(self):
        """Invalid second-level directory should be rejected."""
        assert matches_ufc_structure(Path("claude/invalid/file.py")) == False

    def test_valid_data_subdirectory(self):
        """claude/data/databases/* should be valid."""
        assert matches_ufc_structure(Path("claude/data/databases/system/test.db")) == True

    def test_docs_exception(self):
        """docs/ should be valid (exception)."""
        assert matches_ufc_structure(Path("docs/readme.md")) == True


class TestUFCCompliantPaths:
    """FR5: UFC-compliant path suggestions - All test cases from requirements."""

    def test_agent_file_recommendation(self):
        """*_agent.md should recommend claude/agents/."""
        path = get_ufc_compliant_path(Path("my_agent.md"))
        assert "claude/agents" in str(path)
        assert path.name == "my_agent.md"

    def test_tool_file_recommendation(self):
        """*.py (not test) should recommend claude/tools/."""
        path = get_ufc_compliant_path(Path("my_tool.py"))
        assert "claude/tools" in str(path)
        assert path.name == "my_tool.py"

    def test_test_file_recommendation(self):
        """test_*.py should recommend tests/."""
        path = get_ufc_compliant_path(Path("test_feature.py"))
        assert "tests" in str(path)
        assert path.name == "test_feature.py"

    def test_database_recommendation(self):
        """*.db should recommend claude/data/databases/system/."""
        path = get_ufc_compliant_path(Path("data.db"))
        assert "claude/data/databases/system" in str(path)
        assert path.name == "data.db"

    def test_project_plan_recommendation(self):
        """*_PLAN.md should recommend project_status/active/."""
        path = get_ufc_compliant_path(Path("MY_PROJECT_PLAN.md"))
        assert "project_status/active" in str(path)
        assert path.name == "MY_PROJECT_PLAN.md"

    def test_progress_file_recommendation(self):
        """*_progress.md should recommend project_status/active/."""
        path = get_ufc_compliant_path(Path("project_progress.md"))
        assert "project_status/active" in str(path)

    def test_phase_doc_recommendation(self):
        """PHASE_*.md should recommend project_status/active/."""
        path = get_ufc_compliant_path(Path("PHASE_151_COMPLETE.md"))
        assert "project_status/active" in str(path)


class TestRootDirectoryRestriction:
    """FR6: Root directory restriction - All test cases from requirements."""

    def test_allowed_root_file_claude_md(self):
        """CLAUDE.md should be allowed in root."""
        result = validate_file_location("CLAUDE.md", "System instructions")
        # May fail on other checks, but not root restriction
        assert "root" not in result['reason'].lower() or result['valid'] == True

    def test_allowed_root_file_readme(self):
        """README.md should be allowed in root."""
        result = validate_file_location("README.md", "Project documentation")
        assert "root" not in result['reason'].lower() or result['valid'] == True

    def test_disallowed_root_file(self):
        """Random files in root should be rejected."""
        result = validate_file_location("RANDOM.md", "Random file")
        assert result['valid'] == False
        assert "root" in result['reason'].lower()

    def test_non_root_file_allowed(self):
        """Files not in root should not trigger root restriction."""
        result = validate_file_location("claude/data/file.md", "Data file")
        # May fail on other checks, but not root restriction
        if not result['valid']:
            assert "root" not in result['reason'].lower()


class TestProjectInference:
    """FR7: Project inference - All test cases from requirements."""

    def test_servicedesk_inference(self):
        """Filename with 'servicedesk' should infer servicedesk_analysis."""
        assert infer_project(Path("ServiceDesk_Analysis.xlsx")) == "servicedesk_analysis"

    def test_infrastructure_inference(self):
        """Filename with 'infrastructure' should infer infrastructure_team."""
        assert infer_project(Path("Infrastructure_Data.csv")) == "infrastructure_team"

    def test_recruitment_inference_l2(self):
        """Filename with 'l2_' should infer recruitment."""
        assert infer_project(Path("L2_Test_Questions.md")) == "recruitment"

    def test_recruitment_inference_keyword(self):
        """Filename with 'recruitment' should infer recruitment."""
        assert infer_project(Path("recruitment_data.xlsx")) == "recruitment"

    def test_general_fallback(self):
        """Unknown files should infer 'general'."""
        assert infer_project(Path("random_file.txt")) == "general"

    def test_case_insensitive_inference(self):
        """Project inference should be case-insensitive."""
        assert infer_project(Path("SERVICEDESK_DATA.xlsx")) == "servicedesk_analysis"


class TestValidationIntegration:
    """FR1 + FR8: End-to-end validation - All integration test cases."""

    def test_work_output_rejection_servicedesk(self):
        """ServiceDesk analysis should be rejected with correct recommendation."""
        result = validate_file_location(
            "claude/data/ServiceDesk_Analysis.xlsx",
            "ServiceDesk ticket analysis"
        )
        assert result['valid'] == False
        assert "work_projects" in result['recommended_path']
        assert "servicedesk" in result['recommended_path'].lower()
        assert result['policy_violated'] == "Operational Data Separation Policy"

    def test_work_output_rejection_infrastructure(self):
        """Infrastructure data should be rejected."""
        result = validate_file_location(
            "claude/data/Infrastructure_Team.csv",
            "Infrastructure team analysis"
        )
        assert result['valid'] == False
        assert "work_projects" in result['recommended_path']
        assert "infrastructure" in result['recommended_path'].lower()

    def test_ufc_compliant_agent_acceptance(self):
        """Valid agent path should be accepted."""
        result = validate_file_location(
            "claude/agents/specialist_agent.md",
            "Maia specialist agent definition"
        )
        assert result['valid'] == True
        assert result['policy_violated'] is None

    def test_ufc_compliant_tool_acceptance(self):
        """Valid tool path should be accepted."""
        result = validate_file_location(
            "claude/tools/analysis_tool.py",
            "Maia analysis tool"
        )
        assert result['valid'] == True

    def test_ufc_violation_gets_suggestion(self):
        """UFC violations should get compliant path suggestion."""
        result = validate_file_location(
            "random_agent.md",
            "Agent definition"
        )
        assert result['valid'] == False
        assert "claude/agents" in result['recommended_path']

    def test_multiple_violations_work_output_and_ufc(self):
        """File with multiple issues should report primary violation."""
        result = validate_file_location(
            "ServiceDesk_Analysis.xlsx",
            "ServiceDesk analysis"
        )
        assert result['valid'] == False
        # Could be root violation OR work output, both are correct


class TestEdgeCases:
    """Edge cases from all requirements."""

    def test_relative_path_handling(self):
        """Relative paths should be converted to absolute."""
        result = validate_file_location(
            "claude/agents/test.md",
            "test agent"
        )
        assert MAIA_ROOT in Path(result['recommended_path']).parents or \
               str(MAIA_ROOT) in result['recommended_path']

    def test_absolute_path_handling(self):
        """Absolute paths should work."""
        abs_path = str(MAIA_ROOT / "claude/agents/test.md")
        result = validate_file_location(abs_path, "test agent")
        assert result['valid'] == True

    def test_nonexistent_file(self):
        """Non-existent files should not error (size check skipped)."""
        result = validate_file_location(
            "claude/tools/nonexistent.py",
            "future tool"
        )
        # Should validate path rules, not fail on missing file
        assert result is not None
        assert 'valid' in result

    def test_empty_purpose_string(self):
        """Empty purpose should not crash."""
        result = validate_file_location("claude/agents/test.md", "")
        assert result is not None

    def test_special_characters_in_filename(self):
        """Special characters should be handled."""
        result = validate_file_location(
            "claude/tools/test-tool_v2.py",
            "test tool"
        )
        assert result is not None


class TestPerformanceRequirements:
    """NFR1: Performance requirements."""

    def test_validation_speed(self):
        """Validation should complete in <50ms."""
        import time

        start = time.time()
        for _ in range(100):
            validate_file_location("claude/agents/test.md", "test")
        end = time.time()

        avg_time_ms = ((end - start) / 100) * 1000
        assert avg_time_ms < 50, f"Average validation time: {avg_time_ms:.2f}ms (should be <50ms)"


class TestCLIInterface:
    """FR8: CLI interface requirements."""

    def test_cli_help_message(self):
        """CLI should show help if insufficient arguments."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "claude/tools/validate_file_location.py"],
            capture_output=True,
            text=True
        )
        assert "Usage:" in result.stdout
        assert result.returncode == 1

    def test_cli_valid_output(self):
        """CLI should output ✅ for valid paths."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "claude/tools/validate_file_location.py",
             "claude/agents/test.md", "test agent"],
            capture_output=True,
            text=True
        )
        assert "✅" in result.stdout
        assert result.returncode == 0

    def test_cli_invalid_output(self):
        """CLI should output ❌ for invalid paths and show policy reference."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "claude/tools/validate_file_location.py",
             "claude/data/ServiceDesk.xlsx", "ServiceDesk analysis"],
            capture_output=True,
            text=True
        )
        assert "❌" in result.stdout
        assert "file_organization_policy.md" in result.stdout
        assert result.returncode == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
