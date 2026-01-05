#!/usr/bin/env python3
"""
TDD Tests for Remediation Detector

Tests remediation event detection, phase classification, and dwell time calculation.

Run: pytest claude/tools/m365_ir/tests/test_remediation_detector.py -v

Author: Maia System
Created: 2025-12-19 (Phase 225.1)
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import AuditLogEntry, SignInLogEntry
from claude.tools.m365_ir.remediation_detector import (
    RemediationDetector,
    RemediationEvent,
    RemediationSummary,
    AttackPhase,
    IncidentTimeline,
)


def create_audit_entry(
    activity: str,
    dt: datetime,
    target: str = "user@test.com",
    initiated_by: str = "admin@test.com",
) -> AuditLogEntry:
    """Helper to create audit entries"""
    return AuditLogEntry(
        activity_datetime=dt,
        activity_display_name=activity,
        initiated_by=initiated_by,
        target=target,
        result="success",
        result_reason="",
    )


def create_signin_entry(
    user: str,
    country: str,
    dt: datetime,
    ip: str = "1.2.3.4",
) -> SignInLogEntry:
    """Helper to create sign-in entries"""
    return SignInLogEntry(
        created_datetime=dt,
        user_principal_name=user,
        user_display_name=user.split("@")[0],
        app_display_name="Test App",
        ip_address=ip,
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


class TestRemediationEventDetection:
    """Test detection of remediation events from audit logs"""

    @pytest.fixture
    def detector(self):
        return RemediationDetector()

    def test_detect_token_revocation(self, detector):
        """Detect StsRefreshTokenValidFrom updates as token revocation"""
        entries = [
            create_audit_entry(
                "Update StsRefreshTokenValidFrom Timestamp",
                datetime(2025, 12, 3, 2, 0, 0),
                target="user1@test.com",
            ),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 1
        assert events[0].event_type == "token_revoke"
        assert events[0].user == "user1@test.com"

    def test_detect_password_reset(self, detector):
        """Detect password reset events"""
        entries = [
            create_audit_entry(
                "Reset user password",
                datetime(2025, 12, 3, 2, 0, 0),
                target="user1@test.com",
            ),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 1
        assert events[0].event_type == "password_reset"

    def test_detect_password_profile_update(self, detector):
        """Detect Update PasswordProfile as password change"""
        entries = [
            create_audit_entry(
                "Update PasswordProfile",
                datetime(2025, 12, 3, 2, 0, 0),
                target="user1@test.com",
            ),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 1
        assert events[0].event_type == "password_change"

    def test_detect_mfa_reset(self, detector):
        """Detect admin deleted security info as MFA reset"""
        entries = [
            create_audit_entry(
                "Admin deleted security info",
                datetime(2025, 12, 3, 2, 0, 0),
                target="user1@test.com",
            ),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 1
        assert events[0].event_type == "mfa_reset"

    def test_detect_account_disable(self, detector):
        """Detect account disable events"""
        entries = [
            create_audit_entry(
                "Disable account",
                datetime(2025, 12, 3, 2, 0, 0),
                target="user1@test.com",
            ),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 1
        assert events[0].event_type == "account_disable"

    def test_detect_account_enable(self, detector):
        """Detect account enable events (re-enabling after remediation)"""
        entries = [
            create_audit_entry(
                "Enable account",
                datetime(2025, 12, 3, 2, 0, 0),
                target="user1@test.com",
            ),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 1
        assert events[0].event_type == "account_enable"

    def test_ignore_non_remediation_events(self, detector):
        """Ignore audit events that aren't remediation-related"""
        entries = [
            create_audit_entry("Update device", datetime(2025, 12, 3, 2, 0, 0)),
            create_audit_entry("Add member to group", datetime(2025, 12, 3, 2, 0, 0)),
            create_audit_entry("Update user", datetime(2025, 12, 3, 2, 0, 0)),
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 0

    def test_multiple_remediation_events(self, detector):
        """Detect multiple remediation events"""
        base = datetime(2025, 12, 3, 2, 0, 0)
        entries = [
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base, "user1@test.com"),
            create_audit_entry("Reset user password", base + timedelta(minutes=1), "user1@test.com"),
            create_audit_entry("Admin deleted security info", base + timedelta(minutes=2), "user1@test.com"),
            create_audit_entry("Update device", base + timedelta(minutes=3)),  # Should be ignored
        ]

        events = detector.detect_remediation_events(entries)

        assert len(events) == 3


class TestRemediationSummary:
    """Test remediation summary generation"""

    @pytest.fixture
    def detector(self):
        return RemediationDetector()

    def test_identify_remediation_date(self, detector):
        """Identify the day with most remediation activity"""
        base_dec2 = datetime(2025, 12, 2, 10, 0, 0)
        base_dec3 = datetime(2025, 12, 3, 2, 0, 0)

        entries = [
            # Dec 2 - light activity
            create_audit_entry("Reset user password", base_dec2, "user1@test.com"),
            create_audit_entry("Reset user password", base_dec2 + timedelta(hours=1), "user2@test.com"),
            # Dec 3 - heavy activity (remediation day)
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base_dec3, "user1@test.com"),
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base_dec3, "user2@test.com"),
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base_dec3, "user3@test.com"),
            create_audit_entry("Reset user password", base_dec3 + timedelta(minutes=1), "user1@test.com"),
            create_audit_entry("Reset user password", base_dec3 + timedelta(minutes=1), "user2@test.com"),
            create_audit_entry("Admin deleted security info", base_dec3 + timedelta(minutes=2), "user1@test.com"),
        ]

        summary = detector.get_remediation_summary(entries)

        assert summary.remediation_date == datetime(2025, 12, 3).date()

    def test_count_remediation_by_type(self, detector):
        """Count remediation events by type"""
        base = datetime(2025, 12, 3, 2, 0, 0)
        entries = [
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base, "user1@test.com"),
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base, "user2@test.com"),
            create_audit_entry("Reset user password", base, "user1@test.com"),
            create_audit_entry("Admin deleted security info", base, "user1@test.com"),
        ]

        summary = detector.get_remediation_summary(entries)

        assert summary.by_type["token_revoke"] == 2
        assert summary.by_type["password_reset"] == 1
        assert summary.by_type["mfa_reset"] == 1

    def test_count_unique_users_remediated(self, detector):
        """Count unique users who were remediated"""
        base = datetime(2025, 12, 3, 2, 0, 0)
        entries = [
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base, "user1@test.com"),
            create_audit_entry("Reset user password", base, "user1@test.com"),  # Same user
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base, "user2@test.com"),
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base, "user3@test.com"),
        ]

        summary = detector.get_remediation_summary(entries)

        assert summary.users_remediated == 3
        assert "user1@test.com" in summary.remediated_users
        assert "user2@test.com" in summary.remediated_users
        assert "user3@test.com" in summary.remediated_users

    def test_empty_audit_logs(self, detector):
        """Handle empty audit logs gracefully"""
        summary = detector.get_remediation_summary([])

        assert summary.remediation_date is None
        assert summary.total_events == 0
        assert summary.users_remediated == 0


class TestAttackPhaseDetection:
    """Test attack phase classification"""

    @pytest.fixture
    def detector(self):
        return RemediationDetector()

    def test_detect_attack_start_from_foreign_signin(self, detector):
        """Detect attack start from first foreign (non-AU/US) sign-in"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user2@test.com", "AU", datetime(2025, 11, 2, 10, 0, 0)),
            create_signin_entry("user1@test.com", "NL", datetime(2025, 11, 3, 18, 0, 0)),  # First foreign
            create_signin_entry("user1@test.com", "RU", datetime(2025, 11, 4, 10, 0, 0)),
        ]

        attack_start = detector.detect_attack_start(signin_entries, home_country="AU")

        assert attack_start == datetime(2025, 11, 3, 18, 0, 0)

    def test_attack_start_excludes_us_for_au_company(self, detector):
        """US sign-ins should not be considered attack start for AU company"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user2@test.com", "US", datetime(2025, 11, 2, 10, 0, 0)),  # US - not attack
            create_signin_entry("user1@test.com", "RU", datetime(2025, 11, 3, 18, 0, 0)),  # First attack
        ]

        attack_start = detector.detect_attack_start(signin_entries, home_country="AU")

        assert attack_start == datetime(2025, 11, 3, 18, 0, 0)

    def test_calculate_dwell_time(self, detector):
        """Calculate dwell time from attack start to detection"""
        signin_entries = [
            create_signin_entry("user1@test.com", "NL", datetime(2025, 11, 3, 18, 0, 0)),  # Attack start
        ]

        audit_entries = [
            create_audit_entry(
                "Update StsRefreshTokenValidFrom Timestamp",
                datetime(2025, 12, 3, 2, 0, 0),  # Remediation
                "user1@test.com",
            ),
        ]

        timeline = detector.build_incident_timeline(signin_entries, audit_entries, home_country="AU")

        assert timeline.attack_start_date == datetime(2025, 11, 3).date()
        assert timeline.detection_date == datetime(2025, 12, 3).date()
        assert timeline.dwell_time_days == 30

    def test_classify_attack_phases(self, detector):
        """Classify events into attack phases"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user1@test.com", "NL", datetime(2025, 11, 3, 18, 0, 0)),  # Initial access
            create_signin_entry("user1@test.com", "RU", datetime(2025, 11, 10, 10, 0, 0)),  # Active attack
        ]

        audit_entries = [
            create_audit_entry(
                "Update StsRefreshTokenValidFrom Timestamp",
                datetime(2025, 12, 3, 2, 0, 0),
                "user1@test.com",
            ),
        ]

        timeline = detector.build_incident_timeline(signin_entries, audit_entries, home_country="AU")

        assert AttackPhase.INITIAL_ACCESS in timeline.phases
        assert AttackPhase.ACTIVE_ATTACK in timeline.phases
        assert AttackPhase.CONTAINMENT in timeline.phases


class TestIncidentTimeline:
    """Test incident timeline building"""

    @pytest.fixture
    def detector(self):
        return RemediationDetector()

    def test_build_complete_timeline(self, detector):
        """Build complete incident timeline with all dates"""
        signin_entries = [
            create_signin_entry("user1@test.com", "NL", datetime(2025, 11, 3, 18, 0, 0)),
        ]

        # Dec 2 has 1 event, Dec 3 has bulk (5 events) - Dec 3 should be remediation date
        audit_entries = [
            create_audit_entry(
                "Reset user password",
                datetime(2025, 12, 2, 15, 0, 0),
                "user1@test.com",
            ),
            # Dec 3 bulk activity
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", datetime(2025, 12, 3, 2, 0, 0), "user1@test.com"),
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", datetime(2025, 12, 3, 2, 1, 0), "user2@test.com"),
            create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", datetime(2025, 12, 3, 2, 2, 0), "user3@test.com"),
            create_audit_entry("Reset user password", datetime(2025, 12, 3, 2, 3, 0), "user1@test.com"),
            create_audit_entry("Admin deleted security info", datetime(2025, 12, 3, 2, 4, 0), "user1@test.com"),
        ]

        timeline = detector.build_incident_timeline(signin_entries, audit_entries, home_country="AU")

        assert timeline.attack_start_date == datetime(2025, 11, 3).date()
        assert timeline.first_remediation_date == datetime(2025, 12, 2).date()
        assert timeline.detection_date == datetime(2025, 12, 3).date()  # Bulk remediation
        assert timeline.dwell_time_days == 30

    def test_timeline_summary_string(self, detector):
        """Generate human-readable timeline summary"""
        signin_entries = [
            create_signin_entry("user1@test.com", "NL", datetime(2025, 11, 3, 18, 0, 0)),
        ]

        audit_entries = [
            create_audit_entry(
                "Update StsRefreshTokenValidFrom Timestamp",
                datetime(2025, 12, 3, 2, 0, 0),
                "user1@test.com",
            ),
        ]

        timeline = detector.build_incident_timeline(signin_entries, audit_entries, home_country="AU")
        summary = timeline.get_summary()

        assert "2025-11-03" in summary
        assert "2025-12-03" in summary
        assert "30 days" in summary


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def detector(self):
        return RemediationDetector()

    def test_no_foreign_signins(self, detector):
        """Handle case where no foreign sign-ins exist"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user2@test.com", "AU", datetime(2025, 11, 2, 10, 0, 0)),
        ]

        attack_start = detector.detect_attack_start(signin_entries, home_country="AU")

        assert attack_start is None

    def test_no_remediation_events(self, detector):
        """Handle case where no remediation events exist"""
        audit_entries = [
            create_audit_entry("Update device", datetime(2025, 12, 3, 2, 0, 0)),
        ]

        summary = detector.get_remediation_summary(audit_entries)

        assert summary.remediation_date is None
        assert summary.total_events == 0

    def test_bulk_detection_threshold(self, detector):
        """Remediation date should be based on bulk activity, not first event"""
        base_dec2 = datetime(2025, 12, 2, 10, 0, 0)
        base_dec3 = datetime(2025, 12, 3, 2, 0, 0)

        entries = [
            # Dec 2 - single event (not bulk)
            create_audit_entry("Reset user password", base_dec2, "user1@test.com"),
            # Dec 3 - bulk activity (this should be remediation date)
            *[create_audit_entry("Update StsRefreshTokenValidFrom Timestamp", base_dec3 + timedelta(minutes=i), f"user{i}@test.com") for i in range(10)],
        ]

        summary = detector.get_remediation_summary(entries)

        # Dec 3 should be remediation date (bulk activity) not Dec 2 (single event)
        assert summary.remediation_date == datetime(2025, 12, 3).date()


class TestAttackStartConfidence:
    """Test attack start date confidence calculation based on log visibility window"""

    @pytest.fixture
    def detector(self):
        return RemediationDetector()

    def test_high_confidence_with_clean_baseline(self, detector):
        """HIGH confidence when >=3 days of clean baseline before breach"""
        # Log window: Nov 1-30, Attack: Nov 10 (9 days clean baseline)
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 5, 10, 0, 0)),
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 8, 10, 0, 0)),
            create_signin_entry("user1@test.com", "DE", datetime(2025, 11, 10, 18, 0, 0)),  # Attack
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 30, 10, 0, 0)),
        ]

        timeline = detector.build_incident_timeline(signin_entries, [], home_country="AU")

        assert timeline.attack_start_confidence == "HIGH"
        assert timeline.clean_baseline_days == 9
        assert "Confirmed" in timeline.attack_start_note
        assert timeline.log_window_start == datetime(2025, 11, 1).date()
        assert timeline.log_window_end == datetime(2025, 11, 30).date()

    def test_low_confidence_breach_at_edge(self, detector):
        """LOW confidence when breach at edge of log window (<=1 day baseline)"""
        # Log window starts with attack - no clean baseline
        signin_entries = [
            create_signin_entry("user1@test.com", "DE", datetime(2025, 11, 1, 10, 0, 0)),  # Attack on Day 1
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 15, 10, 0, 0)),
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 30, 10, 0, 0)),
        ]

        timeline = detector.build_incident_timeline(signin_entries, [], home_country="AU")

        assert timeline.attack_start_confidence == "LOW"
        assert timeline.clean_baseline_days == 0
        assert "predates" in timeline.attack_start_note.lower()

    def test_low_confidence_one_day_baseline(self, detector):
        """LOW confidence when only 1 day of baseline"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user1@test.com", "DE", datetime(2025, 11, 2, 10, 0, 0)),  # Attack Day 2
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 30, 10, 0, 0)),
        ]

        timeline = detector.build_incident_timeline(signin_entries, [], home_country="AU")

        assert timeline.attack_start_confidence == "LOW"
        assert timeline.clean_baseline_days == 1

    def test_medium_confidence_limited_baseline(self, detector):
        """MEDIUM confidence when 2 days of baseline"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 2, 10, 0, 0)),
            create_signin_entry("user1@test.com", "DE", datetime(2025, 11, 3, 10, 0, 0)),  # Attack Day 3
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 30, 10, 0, 0)),
        ]

        timeline = detector.build_incident_timeline(signin_entries, [], home_country="AU")

        assert timeline.attack_start_confidence == "MEDIUM"
        assert timeline.clean_baseline_days == 2
        assert "Limited baseline" in timeline.attack_start_note

    def test_unknown_confidence_no_attack(self, detector):
        """UNKNOWN confidence when no attack detected"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 30, 10, 0, 0)),
        ]

        timeline = detector.build_incident_timeline(signin_entries, [], home_country="AU")

        assert timeline.attack_start_confidence == "UNKNOWN"
        assert timeline.attack_start_date is None

    def test_get_summary_includes_confidence(self, detector):
        """get_summary() should include confidence fields"""
        signin_entries = [
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 1, 10, 0, 0)),
            create_signin_entry("user1@test.com", "AU", datetime(2025, 11, 8, 10, 0, 0)),
            create_signin_entry("user1@test.com", "DE", datetime(2025, 11, 10, 18, 0, 0)),
        ]

        timeline = detector.build_incident_timeline(signin_entries, [], home_country="AU")
        summary = detector.get_summary(timeline)

        assert "attack_start_confidence" in summary
        assert summary["attack_start_confidence"] == "HIGH"
        assert "attack_start_note" in summary
        assert "log_window" in summary
        assert summary["log_window"]["start"] == "2025-11-01"
        assert "clean_baseline_days" in summary
        assert summary["clean_baseline_days"] == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
