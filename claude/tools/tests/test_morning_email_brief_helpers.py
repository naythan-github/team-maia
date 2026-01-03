"""
Tests for morning_email_intelligence.py _format_brief helper functions.

TDD: Phase 4 refactoring - decompose _format_brief (130 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    @patch('morning_email_intelligence.anthropic')
    def test_format_urgent_section_exists(self, mock_anthropic):
        """Helper for formatting urgent emails section."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0
        assert hasattr(intel, '_format_urgent_section')
        assert callable(intel._format_urgent_section)

    @patch('morning_email_intelligence.anthropic')
    def test_format_action_items_section_exists(self, mock_anthropic):
        """Helper for formatting action items section."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0
        assert hasattr(intel, '_format_action_items_section')
        assert callable(intel._format_action_items_section)

    @patch('morning_email_intelligence.anthropic')
    def test_format_relationship_section_exists(self, mock_anthropic):
        """Helper for formatting relationship intelligence section."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0
        assert hasattr(intel, '_format_relationship_section')
        assert callable(intel._format_relationship_section)

    @patch('morning_email_intelligence.anthropic')
    def test_format_stats_section_exists(self, mock_anthropic):
        """Helper for formatting processing stats section."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0
        assert hasattr(intel, '_format_stats_section')
        assert callable(intel._format_stats_section)


class TestFormatUrgentSection:
    """Test _format_urgent_section helper."""

    @patch('morning_email_intelligence.anthropic')
    def test_returns_string(self, mock_anthropic):
        """Should return markdown string."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0

        emails = [{"sender": "test@example.com", "subject": "Test", "date": "2025-01-01 09:00:00"}]
        sentiment = {}
        action_items = []

        result = intel._format_urgent_section(emails, sentiment, action_items)
        assert isinstance(result, str)
        assert 'URGENT' in result or 'Test' in result


class TestFormatActionItemsSection:
    """Test _format_action_items_section helper."""

    @patch('morning_email_intelligence.anthropic')
    def test_returns_string(self, mock_anthropic):
        """Should return markdown string."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0

        action_items = [{"task": "Review doc", "sender": "boss@co.com", "deadline": "Today", "priority": "HIGH"}]
        result = intel._format_action_items_section(action_items)
        assert isinstance(result, str)


class TestFormatRelationshipSection:
    """Test _format_relationship_section helper."""

    @patch('morning_email_intelligence.anthropic')
    def test_handles_empty_sentiment(self, mock_anthropic):
        """Should handle empty sentiment dict."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0
        intel.api_calls = 0

        result = intel._format_relationship_section({})
        assert isinstance(result, str)


class TestFormatStatsSection:
    """Test _format_stats_section helper."""

    @patch('morning_email_intelligence.anthropic')
    def test_shows_costs(self, mock_anthropic):
        """Should show processing costs."""
        mock_anthropic.Anthropic.return_value = MagicMock()
        from morning_email_intelligence import MorningEmailIntelligence
        intel = MorningEmailIntelligence.__new__(MorningEmailIntelligence)
        intel.total_cost = 0.05
        intel.api_calls = 10

        categorized = {"urgent": [], "project": [], "fyi": []}
        action_items = []
        sentiment = {}

        result = intel._format_stats_section(categorized, action_items, sentiment)
        assert isinstance(result, str)
        assert 'STATS' in result or 'cost' in result.lower()
