#!/usr/bin/env python3
"""
Tests for validate_file_location tool.

Run with: pytest tests/test_validate_file_location.py
"""

import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude.tools.validate_file_location import (
    validate_file_location,
    is_work_output,
    matches_ufc_structure,
    get_ufc_compliant_path,
    infer_project,
    MAIA_ROOT
)

class TestWorkOutputDetection:
    """Test detection of work output vs. Maia system files."""

    def test_servicedesk_analysis_is_work_output(self):
        """ServiceDesk analysis should be detected as work output."""
        assert is_work_output("ServiceDesk analysis report", Path("report.xlsx")) == True

    def test_tool_implementation_not_work_output(self):
        """Maia tool implementation should NOT be work output."""
        assert is_work_output("Maia tool implementation", Path("tool.py")) == False

    def test_filename_pattern_detection(self):
        """Test filename pattern detection for work outputs."""
        assert is_work_output("Database", Path("ServiceDesk_Analysis.xlsx")) == True
        assert is_work_output("Database", Path("Infrastructure_Team_Data.csv")) == True
        assert is_work_output("Database", Path("L2_Test_Results.md")) == True

    def test_purpose_keyword_detection(self):
        """Test purpose keyword detection."""
        assert is_work_output("analysis of tickets", Path("data.xlsx")) == True
        assert is_work_output("client deliverable", Path("report.pdf")) == True
        assert is_work_output("summary report", Path("summary.md")) == True


class TestUFCStructureValidation:
    """Test UFC directory structure validation."""

    def test_valid_agent_path(self):
        """Agent files in claude/agents/ should be valid."""
        assert matches_ufc_structure(Path("claude/agents/test_agent.md")) == True

    def test_valid_tool_path(self):
        """Tool files in claude/tools/ should be valid."""
        assert matches_ufc_structure(Path("claude/tools/test_tool.py")) == True

    def test_valid_test_path(self):
        """Test files in tests/ should be valid."""
        assert matches_ufc_structure(Path("tests/test_something.py")) == True

    def test_invalid_random_path(self):
        """Random files not in UFC structure should be invalid."""
        assert matches_ufc_structure(Path("random_file.md")) == False

    def test_valid_data_subdirectory(self):
        """Files in claude/data/ subdirectories should be valid."""
        assert matches_ufc_structure(Path("claude/data/databases/system/test.db")) == True


class TestRecommendedPaths:
    """Test recommended path suggestions."""

    def test_agent_recommendation(self):
        """Agent files should recommend claude/agents/."""
        path = get_ufc_compliant_path(Path("my_agent.md"))
        assert "claude/agents" in str(path)

    def test_tool_recommendation(self):
        """Tool files should recommend claude/tools/."""
        path = get_ufc_compliant_path(Path("my_tool.py"))
        assert "claude/tools" in str(path)

    def test_test_recommendation(self):
        """Test files should recommend tests/."""
        path = get_ufc_compliant_path(Path("test_my_feature.py"))
        assert "tests" in str(path)

    def test_database_recommendation(self):
        """Database files should recommend claude/data/databases/."""
        path = get_ufc_compliant_path(Path("my_data.db"))
        assert "claude/data/databases" in str(path)

    def test_project_plan_recommendation(self):
        """Project plans should recommend claude/data/project_status/active/."""
        path = get_ufc_compliant_path(Path("MY_PROJECT_PLAN.md"))
        assert "project_status/active" in str(path)


class TestProjectInference:
    """Test project name inference."""

    def test_servicedesk_inference(self):
        """ServiceDesk files should infer servicedesk_analysis project."""
        assert infer_project(Path("ServiceDesk_Analysis.xlsx")) == "servicedesk_analysis"

    def test_infrastructure_inference(self):
        """Infrastructure files should infer infrastructure_team project."""
        assert infer_project(Path("Infrastructure_Data.csv")) == "infrastructure_team"

    def test_recruitment_inference(self):
        """Recruitment files should infer recruitment project."""
        assert infer_project(Path("L2_Test_Questions.md")) == "recruitment"

    def test_general_fallback(self):
        """Unknown files should infer general project."""
        assert infer_project(Path("random_file.txt")) == "general"


class TestValidationIntegration:
    """Test end-to-end validation."""

    def test_work_output_rejection(self):
        """Work outputs should be rejected with recommendation."""
        result = validate_file_location("claude/data/ServiceDesk_Analysis.xlsx", "ServiceDesk analysis")
        assert result['valid'] == False
        assert "work_projects" in result['recommended_path']
        assert result['policy_violated'] == "Operational Data Separation Policy"

    def test_ufc_compliant_acceptance(self):
        """UFC-compliant paths should be accepted."""
        result = validate_file_location("claude/agents/my_agent.md", "Maia agent definition")
        assert result['valid'] == True
        assert result['policy_violated'] is None

    def test_root_directory_rejection(self):
        """Non-core files in root should be rejected."""
        result = validate_file_location("RANDOM_FILE.md", "Random documentation")
        assert result['valid'] == False
        assert result['policy_violated'] == "Root Directory Policy"

    def test_ufc_violation_gets_suggestion(self):
        """UFC violations should get compliant path suggestion."""
        result = validate_file_location("random_agent.md", "Agent definition")
        assert result['valid'] == False
        assert "claude/agents" in result['recommended_path']


class TestCLIInterface:
    """Test CLI interface functionality."""

    def test_cli_with_valid_path(self, capsys):
        """Test CLI with valid path."""
        # Would need to mock sys.argv for proper CLI testing
        pass

    def test_cli_with_invalid_path(self, capsys):
        """Test CLI with invalid path."""
        # Would need to mock sys.argv for proper CLI testing
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
