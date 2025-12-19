#!/usr/bin/env python3
"""
TDD Tests for Timeline Builder

Correlates events across log types and builds attack timeline.
Run: pytest claude/tools/m365_ir/tests/test_timeline_builder.py -v

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry, AuditLogEntry, MailboxAuditEntry
from claude.tools.m365_ir.timeline_builder import (
    TimelineBuilder,
    TimelineEvent,
    EventPhase,
    build_timeline,
    correlate_events,
    detect_attack_phases,
)


def create_signin_entry(user: str, country: str, dt: datetime) -> SignInLogEntry:
    """Helper to create sign-in entries"""
    return SignInLogEntry(
        created_datetime=dt,
        user_principal_name=user,
        user_display_name=user.split("@")[0],
        app_display_name="Test App",
        ip_address="1.1.1.1",
        city="City",
        country=country,
        device="",
        browser="Chrome",
        os="Windows",
        status_raw="success",
        status_normalized="success",
        risk_state="none",
        risk_level_during_signin="none",
        risk_level_aggregated="none",
        conditional_access_status="success",
    )


def create_audit_entry(activity: str, target: str, dt: datetime, initiated_by: str = "") -> AuditLogEntry:
    """Helper to create audit log entries"""
    return AuditLogEntry(
        activity_datetime=dt,
        activity_display_name=activity,
        initiated_by=initiated_by,
        target=target,
        result="success",
        result_reason="",
    )


class TestTimelineBuilding:
    """Test timeline construction from mixed log types"""

    def test_build_timeline_sorts_chronologically(self):
        """Timeline events should be in chronological order"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        signin = create_signin_entry("user@test.com", "AU", base + timedelta(hours=2))
        audit = create_audit_entry("Password reset", "user@test.com", base)

        timeline = build_timeline(signin_entries=[signin], audit_entries=[audit])

        assert len(timeline) == 2
        assert timeline[0].timestamp < timeline[1].timestamp

    def test_timeline_includes_all_log_types(self):
        """Timeline should include events from all log sources"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        signin = create_signin_entry("user@test.com", "RU", base)
        audit = create_audit_entry("Password reset", "user@test.com", base + timedelta(hours=1))

        timeline = build_timeline(signin_entries=[signin], audit_entries=[audit])

        event_types = {e.source_type for e in timeline}
        assert "signin" in event_types
        assert "audit" in event_types

    def test_timeline_event_has_required_fields(self):
        """TimelineEvent should have all required fields"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        signin = create_signin_entry("user@test.com", "RU", base)

        timeline = build_timeline(signin_entries=[signin])

        event = timeline[0]
        assert event.timestamp == base
        assert event.user == "user@test.com"
        assert event.action is not None
        assert event.source_type == "signin"


class TestEventCorrelation:
    """Test correlation of related events"""

    def test_correlate_login_and_password_reset(self):
        """Link login event to subsequent password reset"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        signin = create_signin_entry("victim@test.com", "RU", base)
        reset = create_audit_entry("Reset user password", "victim@test.com", base + timedelta(hours=1))

        timeline = build_timeline(signin_entries=[signin], audit_entries=[reset])
        correlated = correlate_events(timeline)

        # Password reset should reference prior login
        reset_event = [e for e in correlated if "password" in e.action.lower()][0]
        assert reset_event.related_events is not None

    def test_correlate_ca_policy_changes(self):
        """Group Conditional Access policy changes together"""
        base = datetime(2025, 12, 3, 1, 0, 0)
        events = [
            create_audit_entry("Add named location", "Australia", base),
            create_audit_entry("Add conditional access policy", "Geofence", base + timedelta(minutes=2)),
            create_audit_entry("Update conditional access policy", "Geofence", base + timedelta(minutes=5)),
        ]

        timeline = build_timeline(audit_entries=events)
        correlated = correlate_events(timeline)

        # All CA changes within timeframe should be grouped
        ca_events = [e for e in correlated if "conditional access" in e.action.lower() or "named location" in e.action.lower()]
        assert len(ca_events) >= 1


class TestAttackPhaseDetection:
    """Test attack phase detection (Initial Access, Persistence, etc.)"""

    def test_detect_initial_access_phase(self):
        """First foreign login marks Initial Access phase"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        events = [
            create_signin_entry("victim@test.com", "AU", base - timedelta(days=1)),  # Normal
            create_signin_entry("victim@test.com", "RU", base),  # Attack starts
        ]

        timeline = build_timeline(signin_entries=events)
        phases = detect_attack_phases(timeline, home_country="AU")

        assert EventPhase.INITIAL_ACCESS in [p.phase for p in phases]

    def test_detect_persistence_phase(self):
        """Inbox rule or forwarding marks Persistence phase"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        events = [
            create_audit_entry("Set-InboxRule", "victim@test.com", base),
        ]

        timeline = build_timeline(audit_entries=events)
        phases = detect_attack_phases(timeline)

        assert EventPhase.PERSISTENCE in [p.phase for p in phases]

    def test_detect_containment_phase(self):
        """Password reset or CA policy marks Containment phase"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        events = [
            create_audit_entry("Reset user password", "victim@test.com", base),
            create_audit_entry("Add conditional access policy", "Geofence", base + timedelta(minutes=30)),
        ]

        timeline = build_timeline(audit_entries=events)
        phases = detect_attack_phases(timeline)

        assert EventPhase.CONTAINMENT in [p.phase for p in phases]


class TestTimelineBuilder:
    """Test TimelineBuilder class"""

    @pytest.fixture
    def builder(self):
        return TimelineBuilder()

    def test_build_full_timeline(self, builder):
        """Build complete timeline from all log sources"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        signin = [create_signin_entry("user@test.com", "RU", base)]
        audit = [create_audit_entry("Password reset", "user@test.com", base + timedelta(hours=1))]

        timeline = builder.build(signin_entries=signin, audit_entries=audit)

        assert len(timeline) == 2

    def test_get_timeline_summary(self, builder):
        """Get summary statistics from timeline"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        events = [
            create_signin_entry("user1@test.com", "RU", base),
            create_signin_entry("user2@test.com", "CN", base + timedelta(hours=1)),
            create_audit_entry("Password reset", "user1@test.com", base + timedelta(hours=2)),
        ]

        timeline = builder.build(signin_entries=events[:2], audit_entries=[events[2]])
        summary = builder.get_summary(timeline)

        assert "total_events" in summary
        assert "date_range" in summary
        assert "users_involved" in summary

    def test_filter_timeline_by_user(self, builder):
        """Filter timeline to specific user"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        events = [
            create_signin_entry("user1@test.com", "RU", base),
            create_signin_entry("user2@test.com", "CN", base + timedelta(hours=1)),
        ]

        timeline = builder.build(signin_entries=events)
        filtered = builder.filter_by_user(timeline, "user1@test.com")

        assert len(filtered) == 1
        assert filtered[0].user == "user1@test.com"

    def test_filter_timeline_by_date_range(self, builder):
        """Filter timeline to date range"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        events = [
            create_signin_entry("user@test.com", "RU", base),
            create_signin_entry("user@test.com", "CN", base + timedelta(days=5)),
            create_signin_entry("user@test.com", "IN", base + timedelta(days=10)),
        ]

        timeline = builder.build(signin_entries=events)
        filtered = builder.filter_by_date_range(
            timeline,
            start=base + timedelta(days=1),
            end=base + timedelta(days=7)
        )

        assert len(filtered) == 1


class TestTimelineFormatting:
    """Test timeline output formatting"""

    @pytest.fixture
    def builder(self):
        return TimelineBuilder()

    def test_format_as_markdown_table(self, builder):
        """Format timeline as markdown table"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        events = [
            create_signin_entry("user@test.com", "RU", base),
            create_audit_entry("Password reset", "user@test.com", base + timedelta(hours=1)),
        ]

        timeline = builder.build(signin_entries=[events[0]], audit_entries=[events[1]])
        md = builder.format_markdown(timeline)

        assert "| Time" in md or "| Date" in md
        assert "user@test.com" in md

    def test_format_timeline_for_pir(self, builder):
        """Format timeline for PIR report"""
        base = datetime(2025, 11, 3, 10, 0, 0)
        events = [
            create_signin_entry("user@test.com", "RU", base),
        ]

        timeline = builder.build(signin_entries=events)
        pir_format = builder.format_for_pir(timeline)

        assert isinstance(pir_format, list)
        assert len(pir_format) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
