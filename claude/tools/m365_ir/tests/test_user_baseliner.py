#!/usr/bin/env python3
"""
TDD Tests for User Baseliner

Tests written FIRST per TDD methodology.
Run: pytest claude/tools/m365_ir/tests/test_user_baseliner.py -v

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry
from claude.tools.m365_ir.user_baseliner import (
    UserBaseliner,
    UserBaseline,
    calculate_user_baseline,
    is_foreign_login,
)


def create_signin_entry(
    user: str,
    country: str,
    ip: str = "1.1.1.1",
    datetime_obj: datetime = None
) -> SignInLogEntry:
    """Helper to create test sign-in entries"""
    return SignInLogEntry(
        created_datetime=datetime_obj or datetime.now(),
        user_principal_name=user,
        user_display_name=user.split("@")[0],
        app_display_name="Test App",
        ip_address=ip,
        city="Test City",
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


class TestUserBaselineCalculation:
    """Test user baseline calculation from login history"""

    def test_single_country_user(self):
        """User with all logins from one country → primary_country = that country"""
        entries = [
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
        ]
        baseline = calculate_user_baseline("user@test.com", entries)

        assert baseline.primary_country == "AU"
        assert baseline.confidence >= 0.9

    def test_majority_country_is_primary(self):
        """User with >50% logins from one country → that country is primary"""
        entries = [
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "US"),  # 20% from US
        ]
        baseline = calculate_user_baseline("user@test.com", entries)

        assert baseline.primary_country == "AU"
        assert baseline.confidence == pytest.approx(0.8, abs=0.01)

    def test_us_based_user(self):
        """User primarily in US should have US as primary"""
        entries = [
            create_signin_entry("user@test.com", "US"),
            create_signin_entry("user@test.com", "US"),
            create_signin_entry("user@test.com", "US"),
            create_signin_entry("user@test.com", "AU"),  # Travel to AU
        ]
        baseline = calculate_user_baseline("user@test.com", entries)

        assert baseline.primary_country == "US"
        assert "AU" in baseline.secondary_countries

    def test_secondary_countries_tracked(self):
        """Secondary locations should be tracked for travel patterns"""
        entries = [
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "NZ"),  # Trip to NZ
            create_signin_entry("user@test.com", "SG"),  # Trip to SG
        ]
        baseline = calculate_user_baseline("user@test.com", entries)

        assert baseline.primary_country == "AU"
        assert "NZ" in baseline.secondary_countries
        assert "SG" in baseline.secondary_countries

    def test_confidence_calculation(self):
        """Confidence should reflect how dominant the primary country is"""
        # 90% from AU = 0.9 confidence
        entries = [create_signin_entry("user@test.com", "AU") for _ in range(9)]
        entries.append(create_signin_entry("user@test.com", "US"))

        baseline = calculate_user_baseline("user@test.com", entries)
        assert baseline.confidence == pytest.approx(0.9, abs=0.01)

    def test_no_logins_returns_unknown(self):
        """User with no logins should return unknown baseline"""
        baseline = calculate_user_baseline("user@test.com", [])

        assert baseline.primary_country == "UNKNOWN"
        assert baseline.confidence == 0.0

    def test_suspicious_user_no_home_country(self):
        """User with logins from many countries but no clear home"""
        entries = [
            create_signin_entry("user@test.com", "RU"),
            create_signin_entry("user@test.com", "CN"),
            create_signin_entry("user@test.com", "IN"),
            create_signin_entry("user@test.com", "KR"),
            create_signin_entry("user@test.com", "US"),
        ]
        baseline = calculate_user_baseline("user@test.com", entries)

        # No country > 50% → low confidence
        assert baseline.confidence < 0.5
        assert baseline.is_suspicious


class TestForeignLoginDetection:
    """Test foreign login detection against baseline"""

    def test_login_from_primary_country_not_foreign(self):
        """Login from primary country is not foreign"""
        baseline = UserBaseline(
            user_principal_name="user@test.com",
            primary_country="AU",
            secondary_countries=["NZ"],
            confidence=0.9,
            total_logins=100,
            country_distribution={"AU": 90, "NZ": 10},
        )
        entry = create_signin_entry("user@test.com", "AU")

        assert not is_foreign_login(entry, baseline)

    def test_login_from_secondary_country_not_foreign(self):
        """Login from known secondary country (travel) is not foreign"""
        baseline = UserBaseline(
            user_principal_name="user@test.com",
            primary_country="AU",
            secondary_countries=["NZ", "SG"],
            confidence=0.9,
            total_logins=100,
            country_distribution={"AU": 85, "NZ": 10, "SG": 5},
        )
        entry = create_signin_entry("user@test.com", "NZ")

        assert not is_foreign_login(entry, baseline)

    def test_login_from_unknown_country_is_foreign(self):
        """Login from country not in baseline is foreign"""
        baseline = UserBaseline(
            user_principal_name="user@test.com",
            primary_country="AU",
            secondary_countries=["NZ"],
            confidence=0.9,
            total_logins=100,
            country_distribution={"AU": 90, "NZ": 10},
        )
        entry = create_signin_entry("user@test.com", "RU")

        assert is_foreign_login(entry, baseline)

    def test_login_from_suspicious_country_always_foreign(self):
        """Login from known malicious country should always be flagged"""
        baseline = UserBaseline(
            user_principal_name="user@test.com",
            primary_country="AU",
            secondary_countries=[],
            confidence=0.9,
            total_logins=100,
            country_distribution={"AU": 100},
        )

        # These countries are commonly associated with attacks
        for country in ["RU", "CN", "KP", "IR"]:
            entry = create_signin_entry("user@test.com", country)
            assert is_foreign_login(entry, baseline)


class TestUserBaselinerBulk:
    """Test bulk baseline calculation for all users"""

    @pytest.fixture
    def baseliner(self):
        return UserBaseliner()

    def test_calculate_all_baselines(self, baseliner):
        """Calculate baselines for all users from login entries"""
        entries = [
            # User 1: AU based
            create_signin_entry("user1@test.com", "AU"),
            create_signin_entry("user1@test.com", "AU"),
            create_signin_entry("user1@test.com", "AU"),
            # User 2: US based
            create_signin_entry("user2@test.com", "US"),
            create_signin_entry("user2@test.com", "US"),
            # User 3: Mixed/suspicious
            create_signin_entry("user3@test.com", "RU"),
            create_signin_entry("user3@test.com", "CN"),
        ]

        baselines = baseliner.calculate_all_baselines(entries)

        assert len(baselines) == 3
        assert baselines["user1@test.com"].primary_country == "AU"
        assert baselines["user2@test.com"].primary_country == "US"
        assert baselines["user3@test.com"].is_suspicious

    def test_identify_compromised_vs_false_positives(self, baseliner):
        """Distinguish compromised AU users from legitimate US users"""
        entries = [
            # AU user with foreign logins (compromised)
            create_signin_entry("au_user@test.com", "AU"),
            create_signin_entry("au_user@test.com", "AU"),
            create_signin_entry("au_user@test.com", "AU"),
            create_signin_entry("au_user@test.com", "RU"),  # Attack!
            create_signin_entry("au_user@test.com", "CN"),  # Attack!

            # US user with US logins (false positive)
            create_signin_entry("us_user@test.com", "US"),
            create_signin_entry("us_user@test.com", "US"),
            create_signin_entry("us_user@test.com", "US"),
        ]

        baselines = baseliner.calculate_all_baselines(entries)

        # AU user's RU/CN logins should be flagged as foreign
        au_baseline = baselines["au_user@test.com"]
        ru_entry = create_signin_entry("au_user@test.com", "RU")
        assert is_foreign_login(ru_entry, au_baseline)

        # US user's US logins should NOT be flagged
        us_baseline = baselines["us_user@test.com"]
        us_entry = create_signin_entry("us_user@test.com", "US")
        assert not is_foreign_login(us_entry, us_baseline)

    def test_find_anomalous_logins(self, baseliner):
        """Find all anomalous logins across all users"""
        entries = [
            # Normal AU user
            create_signin_entry("normal@test.com", "AU"),
            create_signin_entry("normal@test.com", "AU"),
            create_signin_entry("normal@test.com", "AU"),

            # Compromised AU user
            create_signin_entry("compromised@test.com", "AU"),
            create_signin_entry("compromised@test.com", "AU"),
            create_signin_entry("compromised@test.com", "RU"),  # Anomaly!
        ]

        baselines = baseliner.calculate_all_baselines(entries)
        anomalies = baseliner.find_anomalous_logins(entries, baselines)

        assert len(anomalies) == 1
        assert anomalies[0].user_principal_name == "compromised@test.com"
        assert anomalies[0].country == "RU"


class TestBaselineThresholds:
    """Test configurable thresholds for baseline calculation"""

    def test_secondary_country_threshold(self):
        """Countries with <5% logins should not be secondary"""
        entries = [
            *[create_signin_entry("user@test.com", "AU") for _ in range(95)],
            create_signin_entry("user@test.com", "NZ"),  # 1% - too low
        ]
        baseline = calculate_user_baseline(
            "user@test.com",
            entries,
            secondary_threshold=0.05  # 5% minimum
        )

        assert baseline.primary_country == "AU"
        assert "NZ" not in baseline.secondary_countries

    def test_primary_country_minimum_threshold(self):
        """Primary country must have minimum percentage to be confident"""
        entries = [
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "AU"),
            create_signin_entry("user@test.com", "US"),
            create_signin_entry("user@test.com", "NZ"),
        ]
        baseline = calculate_user_baseline(
            "user@test.com",
            entries,
            primary_threshold=0.6  # Need 60% to be confident
        )

        # AU is 50%, below threshold → suspicious
        assert baseline.confidence < 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
