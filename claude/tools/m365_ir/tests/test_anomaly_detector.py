#!/usr/bin/env python3
"""
TDD Tests for Anomaly Detector

Detects impossible travel, legacy auth abuse, and suspicious patterns.
Run: pytest claude/tools/m365_ir/tests/test_anomaly_detector.py -v

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry, LegacyAuthEntry
from claude.tools.m365_ir.anomaly_detector import (
    AnomalyDetector,
    Anomaly,
    AnomalyType,
    detect_impossible_travel,
    detect_legacy_auth_abuse,
    detect_high_risk_country_login,
    calculate_travel_distance,
)


def create_signin_entry(
    user: str,
    country: str,
    city: str = "City",
    ip: str = "1.1.1.1",
    dt: datetime = None,
    app: str = "Test App",
) -> SignInLogEntry:
    """Helper to create test sign-in entries"""
    return SignInLogEntry(
        created_datetime=dt or datetime.now(),
        user_principal_name=user,
        user_display_name=user.split("@")[0],
        app_display_name=app,
        ip_address=ip,
        city=city,
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


def create_legacy_auth_entry(
    user: str,
    country: str,
    client_app: str = "IMAP4",
    status: str = "failure",
    failure_reason: str = "Error validating credentials",
    dt: datetime = None,
) -> LegacyAuthEntry:
    """Helper to create legacy auth entries"""
    return LegacyAuthEntry(
        created_datetime=dt or datetime.now(),
        user_principal_name=user,
        user_display_name=user.split("@")[0],
        client_app_used=client_app,
        app_display_name="Office 365 Exchange Online",
        ip_address="1.1.1.1",
        city="City",
        country=country,
        status=status,
        status_normalized="failure" if "Error" in failure_reason else "success",
        failure_reason=failure_reason,
        conditional_access_status="notApplied",
    )


class TestImpossibleTravel:
    """Test impossible travel detection"""

    def test_no_impossible_travel_same_location(self):
        """Sequential logins from same city - not impossible"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user@test.com", "AU", "Melbourne", dt=base_time),
            create_signin_entry("user@test.com", "AU", "Melbourne", dt=base_time + timedelta(hours=1)),
        ]
        anomalies = detect_impossible_travel(entries)
        assert len(anomalies) == 0

    def test_impossible_travel_different_countries(self):
        """Login from AU then RU within 1 hour - impossible"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user@test.com", "AU", "Melbourne", dt=base_time),
            create_signin_entry("user@test.com", "RU", "Moscow", dt=base_time + timedelta(hours=1)),
        ]
        anomalies = detect_impossible_travel(entries)
        assert len(anomalies) == 1
        assert anomalies[0].anomaly_type == AnomalyType.IMPOSSIBLE_TRAVEL

    def test_possible_travel_long_time_gap(self):
        """Login from AU then US with 24 hour gap - possible (flight)"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user@test.com", "AU", "Melbourne", dt=base_time),
            create_signin_entry("user@test.com", "US", "Los Angeles", dt=base_time + timedelta(hours=24)),
        ]
        anomalies = detect_impossible_travel(entries)
        assert len(anomalies) == 0  # 24 hours is enough for AU->US flight

    def test_impossible_travel_multiple_users(self):
        """Only detect impossible travel for same user"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user1@test.com", "AU", "Melbourne", dt=base_time),
            create_signin_entry("user2@test.com", "RU", "Moscow", dt=base_time + timedelta(minutes=30)),
        ]
        anomalies = detect_impossible_travel(entries)
        assert len(anomalies) == 0  # Different users

    def test_impossible_travel_returns_both_entries(self):
        """Anomaly should reference both the source and destination logins"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user@test.com", "AU", "Melbourne", dt=base_time),
            create_signin_entry("user@test.com", "CN", "Beijing", dt=base_time + timedelta(hours=2)),
        ]
        anomalies = detect_impossible_travel(entries)
        assert len(anomalies) == 1
        assert anomalies[0].source_location == "Melbourne, AU"
        assert anomalies[0].dest_location == "Beijing, CN"


class TestLegacyAuthAbuse:
    """Test legacy authentication abuse detection"""

    def test_detect_legacy_auth_from_foreign_country(self):
        """Legacy auth from foreign country is suspicious"""
        entries = [
            create_legacy_auth_entry("user@test.com", "RU", "IMAP4"),
            create_legacy_auth_entry("user@test.com", "CN", "Authenticated SMTP"),
        ]
        anomalies = detect_legacy_auth_abuse(entries, home_country="AU")
        assert len(anomalies) == 2
        assert all(a.anomaly_type == AnomalyType.LEGACY_AUTH_ABUSE for a in anomalies)

    def test_legacy_auth_from_home_country_not_flagged(self):
        """Legacy auth from home country is less suspicious"""
        entries = [
            create_legacy_auth_entry("user@test.com", "AU", "IMAP4"),
        ]
        anomalies = detect_legacy_auth_abuse(entries, home_country="AU")
        assert len(anomalies) == 0

    def test_detect_credential_stuffing_pattern(self):
        """Multiple failed legacy auth attempts = credential stuffing"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_legacy_auth_entry("user@test.com", "CN", "IMAP4",
                                     dt=base_time + timedelta(minutes=i))
            for i in range(10)  # 10 attempts in 10 minutes
        ]
        anomalies = detect_legacy_auth_abuse(entries, home_country="AU")
        # Should detect both individual attempts AND the pattern
        assert any(a.anomaly_type == AnomalyType.CREDENTIAL_STUFFING for a in anomalies)

    def test_detect_successful_legacy_auth_high_severity(self):
        """Successful legacy auth from foreign country is high severity"""
        entries = [
            create_legacy_auth_entry("user@test.com", "RU", "IMAP4",
                                     status="0", failure_reason=""),
        ]
        anomalies = detect_legacy_auth_abuse(entries, home_country="AU")
        assert len(anomalies) == 1
        assert anomalies[0].severity == "HIGH"


class TestHighRiskCountryLogin:
    """Test high-risk country login detection"""

    def test_detect_login_from_high_risk_country(self):
        """Logins from known high-risk countries are flagged"""
        entries = [
            create_signin_entry("user@test.com", "RU"),
            create_signin_entry("user@test.com", "CN"),
            create_signin_entry("user@test.com", "KP"),
            create_signin_entry("user@test.com", "IR"),
        ]
        anomalies = detect_high_risk_country_login(entries)
        assert len(anomalies) == 4
        assert all(a.anomaly_type == AnomalyType.HIGH_RISK_COUNTRY for a in anomalies)

    def test_login_from_normal_country_not_flagged(self):
        """Logins from normal countries are not flagged"""
        entries = [
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "US"),
            create_signin_entry("user@test.com", "NZ"),
            create_signin_entry("user@test.com", "GB"),
        ]
        anomalies = detect_high_risk_country_login(entries)
        assert len(anomalies) == 0


class TestAnomalyDetectorIntegration:
    """Test full anomaly detector integration"""

    @pytest.fixture
    def detector(self):
        return AnomalyDetector()

    def test_detect_all_anomalies(self, detector):
        """Detector should find all types of anomalies"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)

        signin_entries = [
            # Normal login
            create_signin_entry("normal@test.com", "AU", "Melbourne", dt=base_time),
            # Impossible travel
            create_signin_entry("compromised@test.com", "AU", "Sydney", dt=base_time),
            create_signin_entry("compromised@test.com", "RU", "Moscow", dt=base_time + timedelta(hours=1)),
        ]

        legacy_entries = [
            # Legacy auth abuse
            create_legacy_auth_entry("compromised@test.com", "CN", "IMAP4", dt=base_time),
        ]

        anomalies = detector.detect_all(
            signin_entries=signin_entries,
            legacy_auth_entries=legacy_entries,
        )

        # Should find impossible travel + high-risk country + legacy auth
        assert len(anomalies) >= 2
        anomaly_types = {a.anomaly_type for a in anomalies}
        assert AnomalyType.IMPOSSIBLE_TRAVEL in anomaly_types or AnomalyType.HIGH_RISK_COUNTRY in anomaly_types

    def test_anomaly_severity_ranking(self, detector):
        """Anomalies should have severity levels"""
        entries = [
            create_signin_entry("user@test.com", "RU"),  # High risk country
        ]
        anomalies = detector.detect_all(signin_entries=entries)

        assert len(anomalies) == 1
        assert anomalies[0].severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_get_anomaly_summary(self, detector):
        """Detector should provide summary statistics"""
        base_time = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user1@test.com", "RU", dt=base_time),
            create_signin_entry("user2@test.com", "CN", dt=base_time),
            create_signin_entry("user1@test.com", "AU", dt=base_time),
            create_signin_entry("user1@test.com", "KP", dt=base_time + timedelta(hours=1)),
        ]

        anomalies = detector.detect_all(signin_entries=entries)
        summary = detector.get_summary(anomalies)

        assert "total_anomalies" in summary
        assert "by_type" in summary
        assert "by_user" in summary
        assert "by_severity" in summary


class TestTravelDistanceCalculation:
    """Test geographic distance calculations"""

    def test_same_city_zero_distance(self):
        """Same city should have ~0 distance"""
        dist = calculate_travel_distance("Melbourne", "AU", "Melbourne", "AU")
        assert dist < 100  # km

    def test_au_to_russia_large_distance(self):
        """AU to Russia should be >10000 km"""
        dist = calculate_travel_distance("Melbourne", "AU", "Moscow", "RU")
        assert dist > 10000

    def test_au_to_nz_moderate_distance(self):
        """AU to NZ should be ~2000-3000 km"""
        dist = calculate_travel_distance("Sydney", "AU", "Auckland", "NZ")
        assert 1500 < dist < 3500


class TestAnomalyDataclass:
    """Test Anomaly dataclass structure"""

    def test_anomaly_has_required_fields(self):
        """Anomaly should have all required fields"""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.IMPOSSIBLE_TRAVEL,
            user_principal_name="user@test.com",
            timestamp=datetime.now(),
            description="Test anomaly",
            severity="HIGH",
            evidence={"key": "value"},
        )

        assert anomaly.anomaly_type == AnomalyType.IMPOSSIBLE_TRAVEL
        assert anomaly.user_principal_name == "user@test.com"
        assert anomaly.severity == "HIGH"
        assert "key" in anomaly.evidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
