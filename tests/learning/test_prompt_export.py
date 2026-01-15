"""
Tests for Prompt Export System

Sprint: SPRINT-002-PROMPT-CAPTURE
Stub tests for pre-existing tool.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestPromptExportImports:
    """Verify module can be imported and exports exist."""

    def test_module_imports(self):
        """Module can be imported without error."""
        from claude.tools.learning import prompt_export
        assert prompt_export is not None

    def test_export_session_prompts_exists(self):
        """export_session_prompts function exists."""
        from claude.tools.learning.prompt_export import export_session_prompts
        assert callable(export_session_prompts)

    def test_export_prompts_by_date_range_exists(self):
        """export_prompts_by_date_range function exists."""
        from claude.tools.learning.prompt_export import export_prompts_by_date_range
        assert callable(export_prompts_by_date_range)

    def test_all_exports(self):
        """__all__ exports correct functions."""
        from claude.tools.learning.prompt_export import __all__
        assert 'export_session_prompts' in __all__
        assert 'export_prompts_by_date_range' in __all__


class TestExportFormats:
    """Test export format handling."""

    def test_invalid_format_raises(self):
        """Invalid format raises ValueError."""
        from claude.tools.learning.prompt_export import export_session_prompts

        with patch('claude.tools.learning.prompt_export.get_memory') as mock_memory:
            mock_memory.return_value.get_prompts_for_session.return_value = []

            with pytest.raises(ValueError, match="Unsupported format"):
                export_session_prompts("test_session", format='invalid')
