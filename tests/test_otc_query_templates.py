"""
Tests for OTC ServiceDesk query templates.

Part of P3: Pre-built SQL Query Templates
Tests MUST be written first (TDD).
"""

import pytest
from unittest.mock import MagicMock, patch
from claude.tools.collection.otc_query_templates import (
    TEMPLATES,
    describe_templates,
    execute_template,
)


class TestTemplateRegistry:
    """Test that the TEMPLATES registry is properly structured."""

    def test_templates_dict_exists(self):
        """TEMPLATES dictionary is populated."""
        assert isinstance(TEMPLATES, dict)
        assert len(TEMPLATES) >= 10, "Should have at least 10 templates"

    def test_template_structure(self):
        """Each template has name, description, parameters, sql."""
        for template_name, template in TEMPLATES.items():
            assert "description" in template, f"{template_name} missing description"
            assert "parameters" in template, f"{template_name} missing parameters"
            assert "sql" in template, f"{template_name} missing sql"
            assert isinstance(template["description"], str)
            assert isinstance(template["parameters"], list)
            assert isinstance(template["sql"], str)
            assert len(template["sql"]) > 0, f"{template_name} has empty SQL"


class TestTeamTemplates:
    """Test team-focused query templates."""

    def test_team_workload_template(self):
        """team_workload returns open/unassigned counts."""
        template = TEMPLATES["team_workload"]
        assert "team_name" in template["parameters"]
        assert "GROUP BY" in template["sql"].upper()
        assert "status" in template["sql"].lower()

    def test_team_backlog_template(self):
        """team_backlog returns unassigned tickets."""
        template = TEMPLATES["team_backlog"]
        assert "team_name" in template["parameters"]
        assert "PendingAssignment" in template["sql"] or "unassigned" in template["sql"].lower()


class TestUserTemplates:
    """Test user-focused query templates."""

    def test_user_workload_template(self):
        """user_workload returns user's open tickets."""
        template = TEMPLATES["user_workload"]
        assert "user_name" in template["parameters"]
        assert "assignee" in template["sql"].lower()
        assert "status" in template["sql"].lower()

    def test_user_activity_template(self):
        """user_activity returns 30-day summary."""
        template = TEMPLATES["user_activity"]
        assert "user_name" in template["parameters"]
        assert "30" in template["sql"] or "INTERVAL" in template["sql"]
        assert "assignee" in template["sql"].lower()


class TestTicketTemplates:
    """Test ticket analysis query templates."""

    def test_ticket_age_distribution_template(self):
        """ticket_age_distribution buckets by age."""
        template = TEMPLATES["ticket_age_distribution"]
        assert "team_name" in template["parameters"]
        assert "CASE" in template["sql"].upper() or "age" in template["sql"].lower()

    def test_open_tickets_by_priority_template(self):
        """open_tickets_by_priority groups by severity."""
        template = TEMPLATES["open_tickets_by_priority"]
        assert "team_name" in template["parameters"]
        assert "priority" in template["sql"].lower() or "severity" in template["sql"].lower()
        assert "GROUP BY" in template["sql"].upper()


class TestTemplateExecution:
    """Test template execution functionality."""

    def test_templates_execute_without_error(self):
        """All templates execute successfully (mocked)."""
        mock_service = MagicMock()
        mock_service.execute_query.return_value = MagicMock(
            success=True,
            data=[{"count": 5}],
            row_count=1,
            error=None
        )

        # Test each template with appropriate mock parameters
        test_params = {
            "team_workload": {"team_name": "Cloud - Infrastructure"},
            "team_backlog": {"team_name": "Cloud - Infrastructure"},
            "engineering_summary": {},
            "user_workload": {"user_name": "John Doe"},
            "user_activity": {"user_name": "John Doe"},
            "user_hours": {"user_name": "John Doe"},
            "ticket_age_distribution": {"team_name": "Cloud - Infrastructure"},
            "open_tickets_by_priority": {"team_name": "Cloud - Infrastructure"},
            "recent_tickets": {"team_name": "Cloud - Infrastructure", "days": 7},
            "orphaned_data_summary": {},
        }

        for template_name, params in test_params.items():
            result = execute_template(template_name, params, mock_service)
            assert result.success, f"Template {template_name} failed to execute"

    def test_describe_templates_function(self):
        """describe_templates() returns readable summary."""
        description = describe_templates()
        assert isinstance(description, str)
        assert len(description) > 0
        # Should contain template names
        assert "team_workload" in description
        assert "user_workload" in description
        # Should be formatted (markdown or similar)
        assert "\n" in description or "##" in description or "-" in description
