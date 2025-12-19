#!/usr/bin/env python3
"""
TDD Tests for IOC Extractor and MITRE Mapper

Run: pytest claude/tools/m365_ir/tests/test_ioc_extractor.py -v

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry, LegacyAuthEntry
from claude.tools.m365_ir.ioc_extractor import (
    IOCExtractor,
    IOC,
    IOCType,
    MitreMapper,
    MitreTechnique,
)


def create_signin_entry(user: str, country: str, ip: str, dt: datetime = None) -> SignInLogEntry:
    """Helper to create sign-in entries"""
    return SignInLogEntry(
        created_datetime=dt or datetime.now(),
        user_principal_name=user,
        user_display_name=user.split("@")[0],
        app_display_name="Test App",
        ip_address=ip,
        city="City",
        country=country,
        device="",
        browser="Chrome 119",
        os="Windows 10",
        status_raw="success",
        status_normalized="success",
        risk_state="none",
        risk_level_during_signin="none",
        risk_level_aggregated="none",
        conditional_access_status="success",
    )


class TestIOCExtraction:
    """Test IOC extraction from logs"""

    @pytest.fixture
    def extractor(self):
        return IOCExtractor()

    def test_extract_ip_addresses(self, extractor):
        """Extract unique IP addresses from logs"""
        entries = [
            create_signin_entry("user@test.com", "RU", "185.234.72.10"),
            create_signin_entry("user@test.com", "RU", "185.234.72.10"),  # Duplicate
            create_signin_entry("user@test.com", "CN", "45.89.123.45"),
        ]

        iocs = extractor.extract(signin_entries=entries)
        ip_iocs = [i for i in iocs if i.ioc_type == IOCType.IP_ADDRESS]

        assert len(ip_iocs) == 2  # Deduplicated
        ip_values = {i.value for i in ip_iocs}
        assert "185.234.72.10" in ip_values
        assert "45.89.123.45" in ip_values

    def test_extract_countries(self, extractor):
        """Extract unique countries from logs"""
        entries = [
            create_signin_entry("user@test.com", "RU", "1.1.1.1"),
            create_signin_entry("user@test.com", "CN", "2.2.2.2"),
            create_signin_entry("user@test.com", "RU", "3.3.3.3"),  # Duplicate country
        ]

        iocs = extractor.extract(signin_entries=entries)
        country_iocs = [i for i in iocs if i.ioc_type == IOCType.COUNTRY]

        assert len(country_iocs) == 2
        countries = {i.value for i in country_iocs}
        assert "RU" in countries
        assert "CN" in countries

    def test_extract_user_agents(self, extractor):
        """Extract browser/OS combinations"""
        entries = [
            create_signin_entry("user@test.com", "RU", "1.1.1.1"),
        ]

        iocs = extractor.extract(signin_entries=entries)
        ua_iocs = [i for i in iocs if i.ioc_type == IOCType.USER_AGENT]

        assert len(ua_iocs) >= 1

    def test_ioc_has_context(self, extractor):
        """IOCs should have context (first seen, count, users)"""
        base = datetime(2025, 12, 3, 10, 0, 0)
        entries = [
            create_signin_entry("user1@test.com", "RU", "185.234.72.10", base),
            create_signin_entry("user2@test.com", "RU", "185.234.72.10", base),
        ]

        iocs = extractor.extract(signin_entries=entries)
        ip_ioc = [i for i in iocs if i.value == "185.234.72.10"][0]

        assert ip_ioc.first_seen == base
        assert ip_ioc.count == 2
        assert len(ip_ioc.affected_users) == 2

    def test_export_iocs_to_csv(self, extractor, tmp_path):
        """Export IOCs to CSV format"""
        entries = [
            create_signin_entry("user@test.com", "RU", "185.234.72.10"),
        ]

        iocs = extractor.extract(signin_entries=entries)
        csv_path = tmp_path / "iocs.csv"
        extractor.export_csv(iocs, csv_path)

        assert csv_path.exists()
        content = csv_path.read_text()
        assert "185.234.72.10" in content


class TestMitreMapping:
    """Test MITRE ATT&CK mapping"""

    @pytest.fixture
    def mapper(self):
        return MitreMapper()

    def test_map_foreign_login_to_valid_accounts(self, mapper):
        """Foreign login maps to T1078.004 Valid Accounts: Cloud"""
        technique = mapper.map_event("Sign-in from RU", "signin")

        assert technique is not None
        assert technique.technique_id == "T1078.004"
        assert "Valid Accounts" in technique.name

    def test_map_legacy_auth_to_valid_accounts(self, mapper):
        """Legacy auth maps to T1078.004"""
        technique = mapper.map_event("IMAP4 login", "legacy_auth")

        assert technique is not None
        assert technique.technique_id == "T1078.004"

    def test_map_inbox_rule_to_email_forwarding(self, mapper):
        """Inbox rule creation maps to T1114.003"""
        technique = mapper.map_event("Set-InboxRule", "audit")

        assert technique is not None
        assert technique.technique_id == "T1114.003"

    def test_map_mailbox_access_to_email_collection(self, mapper):
        """MailItemsAccessed maps to T1114.002"""
        technique = mapper.map_event("MailItemsAccessed", "mailbox")

        assert technique is not None
        assert technique.technique_id == "T1114.002"

    def test_map_password_reset_to_account_manipulation(self, mapper):
        """Password reset maps to T1098"""
        technique = mapper.map_event("Reset user password", "audit")

        assert technique is not None
        assert "T1098" in technique.technique_id

    def test_get_all_techniques_for_incident(self, mapper):
        """Get all MITRE techniques from an incident"""
        events = [
            ("Sign-in from RU", "signin"),
            ("Set-InboxRule", "audit"),
            ("MailItemsAccessed", "mailbox"),
        ]

        techniques = mapper.get_techniques_for_events(events)

        assert len(techniques) >= 2
        technique_ids = {t.technique_id for t in techniques}
        assert "T1078.004" in technique_ids  # Valid Accounts
        assert "T1114.003" in technique_ids  # Email Forwarding


class TestIOCSummary:
    """Test IOC summary generation"""

    @pytest.fixture
    def extractor(self):
        return IOCExtractor()

    def test_get_ioc_summary(self, extractor):
        """Get summary of extracted IOCs"""
        entries = [
            create_signin_entry("user1@test.com", "RU", "1.1.1.1"),
            create_signin_entry("user2@test.com", "CN", "2.2.2.2"),
            create_signin_entry("user1@test.com", "RU", "1.1.1.1"),
        ]

        iocs = extractor.extract(signin_entries=entries)
        summary = extractor.get_summary(iocs)

        assert "total_iocs" in summary
        assert "by_type" in summary
        assert "top_ips" in summary
        assert "top_countries" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
