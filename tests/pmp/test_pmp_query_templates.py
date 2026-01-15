"""
Tests for PMP Query Templates

Sprint: SPRINT-PMP-INTEL-001
Stub tests for pre-existing tool.
"""

import pytest


class TestPMPQueryTemplatesImports:
    """Verify module can be imported and exports exist."""

    def test_module_imports(self):
        """Module can be imported without error."""
        from claude.tools.pmp import pmp_query_templates
        assert pmp_query_templates is not None

    def test_query_template_dataclass_exists(self):
        """QueryTemplate dataclass exists."""
        from claude.tools.pmp.pmp_query_templates import QueryTemplate
        assert QueryTemplate is not None

    def test_templates_dict_exists(self):
        """TEMPLATES dictionary exists and is populated."""
        from claude.tools.pmp.pmp_query_templates import TEMPLATES
        assert isinstance(TEMPLATES, dict)
        assert len(TEMPLATES) > 0

    def test_get_template_exists(self):
        """get_template function exists."""
        from claude.tools.pmp.pmp_query_templates import get_template
        assert callable(get_template)

    def test_list_templates_exists(self):
        """list_templates function exists."""
        from claude.tools.pmp.pmp_query_templates import list_templates
        assert callable(list_templates)

    def test_describe_templates_exists(self):
        """describe_templates function exists."""
        from claude.tools.pmp.pmp_query_templates import describe_templates
        assert callable(describe_templates)


class TestTemplateRegistry:
    """Test template registry contents."""

    def test_org_systems_template_exists(self):
        """org_systems template is defined."""
        from claude.tools.pmp.pmp_query_templates import TEMPLATES
        assert 'org_systems' in TEMPLATES

    def test_failed_patches_template_exists(self):
        """failed_patches template is defined."""
        from claude.tools.pmp.pmp_query_templates import TEMPLATES
        assert 'failed_patches' in TEMPLATES

    def test_get_template_returns_template(self):
        """get_template returns QueryTemplate or None."""
        from claude.tools.pmp.pmp_query_templates import get_template, QueryTemplate

        result = get_template('org_systems')
        assert isinstance(result, QueryTemplate)

        result_none = get_template('nonexistent')
        assert result_none is None

    def test_list_templates_returns_list(self):
        """list_templates returns list of strings."""
        from claude.tools.pmp.pmp_query_templates import list_templates

        result = list_templates()
        assert isinstance(result, list)
        assert all(isinstance(t, str) for t in result)

    def test_describe_templates_returns_string(self):
        """describe_templates returns non-empty string."""
        from claude.tools.pmp.pmp_query_templates import describe_templates

        result = describe_templates()
        assert isinstance(result, str)
        assert len(result) > 100  # Should have meaningful content
