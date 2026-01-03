"""
Tests for automated_daily_briefing.py HTML formatting helper functions.

TDD: Phase 4 refactoring - decompose format_html_briefing (145 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_build_html_header_exists(self, mock_meeting, mock_email, mock_morning):
        """Helper for HTML header and CSS."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing = AutomatedDailyBriefing()
        assert hasattr(briefing, '_build_html_header')
        assert callable(briefing._build_html_header)

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_build_calendar_section_exists(self, mock_meeting, mock_email, mock_morning):
        """Helper for calendar section."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing = AutomatedDailyBriefing()
        assert hasattr(briefing, '_build_calendar_section')
        assert callable(briefing._build_calendar_section)

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_build_email_section_exists(self, mock_meeting, mock_email, mock_morning):
        """Helper for email triage section."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing = AutomatedDailyBriefing()
        assert hasattr(briefing, '_build_email_section')
        assert callable(briefing._build_email_section)

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_build_meeting_section_exists(self, mock_meeting, mock_email, mock_morning):
        """Helper for meeting prep section."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing = AutomatedDailyBriefing()
        assert hasattr(briefing, '_build_meeting_section')
        assert callable(briefing._build_meeting_section)

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_build_followup_section_exists(self, mock_meeting, mock_email, mock_morning):
        """Helper for follow-up reminders section."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing = AutomatedDailyBriefing()
        assert hasattr(briefing, '_build_followup_section')
        assert callable(briefing._build_followup_section)

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_build_html_footer_exists(self, mock_meeting, mock_email, mock_morning):
        """Helper for HTML footer."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing = AutomatedDailyBriefing()
        assert hasattr(briefing, '_build_html_footer')
        assert callable(briefing._build_html_footer)


class TestBuildHtmlHeader:
    """Test _build_html_header helper."""

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_returns_html_with_style_tag(self, mock_meeting, mock_email, mock_morning):
        """Should return HTML with style tag."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing_system = AutomatedDailyBriefing()
        html = briefing_system._build_html_header("Monday, January 1, 2026")
        assert '<html>' in html
        assert '<style>' in html
        assert 'Daily Intelligence Briefing' in html


class TestBuildCalendarSection:
    """Test _build_calendar_section helper."""

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_returns_html_section(self, mock_meeting, mock_email, mock_morning):
        """Should return HTML calendar section."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing_system = AutomatedDailyBriefing()

        calendar = {'has_events_today': False, 'today_count': 0, 'today_events': []}
        html = briefing_system._build_calendar_section(calendar)

        assert 'Schedule' in html or 'schedule' in html.lower()
        assert 'section' in html


class TestBuildEmailSection:
    """Test _build_email_section helper."""

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_returns_html_section(self, mock_meeting, mock_email, mock_morning):
        """Should return HTML email section."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing_system = AutomatedDailyBriefing()

        triage = {'high_priority_messages': [], 'high_priority_count': 0, 'threshold': 5}
        email_data = {'unread_count': 10}
        html = briefing_system._build_email_section(triage, email_data)

        assert 'Email' in html
        assert 'section' in html


class TestBuildHtmlFooter:
    """Test _build_html_footer helper."""

    @patch('automated_daily_briefing.UnifiedMorningBriefing')
    @patch('automated_daily_briefing.EnhancedEmailTriage')
    @patch('automated_daily_briefing.MeetingPrepAutomation')
    def test_returns_html_footer(self, mock_meeting, mock_email, mock_morning):
        """Should return HTML footer."""
        from automated_daily_briefing import AutomatedDailyBriefing
        briefing_system = AutomatedDailyBriefing()
        html = briefing_system._build_html_footer()

        assert '</html>' in html
        assert 'Maia' in html
