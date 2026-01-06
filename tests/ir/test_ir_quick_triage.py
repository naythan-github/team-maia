#!/usr/bin/env python3
"""
TDD Tests for IR Quick Triage Tool (ir_quick_triage.py)

Tests written BEFORE implementation per TDD methodology.
Phase 224 - IR Automation Tools

Run: python3 -m pytest test_ir_quick_triage.py -v
"""

import pytest
import tempfile
import os
import csv
from datetime import datetime

# Import will fail until implementation exists - this is expected in TDD
try:
    from ir_quick_triage import QuickTriage, TriageResult, RiskLevel
except ImportError:
    QuickTriage = None
    TriageResult = None
    RiskLevel = None

try:
    from ir_knowledge import IRKnowledgeBase
except ImportError:
    IRKnowledgeBase = None


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def kb(temp_db):
    """Create a knowledge base instance with temp database."""
    if IRKnowledgeBase is None:
        pytest.skip("IRKnowledgeBase not yet implemented")
    return IRKnowledgeBase(temp_db)


@pytest.fixture
def triage(kb):
    """Create a QuickTriage instance."""
    if QuickTriage is None:
        pytest.skip("QuickTriage not yet implemented")
    return QuickTriage(knowledge_base=kb)


@pytest.fixture
def sign_in_csv(tmp_path):
    """Create a sample sign-in log CSV."""
    csv_path = tmp_path / "signin_logs.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'userPrincipalName', 'ipAddress', 'location', 'userAgent',
            'appDisplayName', 'createdDateTime', 'status'
        ])
        writer.writeheader()
        writer.writerow({
            'userPrincipalName': 'user@test.com',
            'ipAddress': '10.0.0.1',
            'location': 'AU',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0',
            'appDisplayName': 'Microsoft Office',
            'createdDateTime': '2025-12-18T10:00:00Z',
            'status': 'Success'
        })
    return str(csv_path)


class TestUserAgentDetection:
    """Test user agent detection rules (QT-001, UA-001)."""

    def test_qt_001_detect_safari_on_windows(self, triage):
        """QT-001: Detect Safari on Windows (impossible UA)."""
        log_entry = {
            'userPrincipalName': 'zacd@fyna.com.au',
            'ipAddress': '93.127.215.4',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/605.1.15 Safari/605.1.15',
            'createdDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_sign_in(log_entry)

        assert result.risk_level == RiskLevel.HIGH
        assert 'UA-001' in result.rule_ids
        assert result.confidence >= 1.0

    def test_detect_normal_chrome_windows(self, triage):
        """Normal Chrome on Windows should not flag UA-001."""
        log_entry = {
            'userPrincipalName': 'user@test.com',
            'ipAddress': '10.0.0.1',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0',
            'createdDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_sign_in(log_entry)

        assert 'UA-001' not in result.rule_ids

    def test_detect_safari_on_mac_ok(self, triage):
        """Safari on Mac is normal - should not flag."""
        log_entry = {
            'userPrincipalName': 'user@test.com',
            'ipAddress': '10.0.0.1',
            'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/605.1.15 Safari/605.1.15',
            'createdDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_sign_in(log_entry)

        assert 'UA-001' not in result.rule_ids


class TestIPDetection:
    """Test IP detection rules (QT-002, QT-003, IP-001, IP-002)."""

    def test_qt_002_detect_known_malicious_ip(self, triage, kb):
        """QT-002: Detect known malicious IP from knowledge base."""
        # Add malicious IP to knowledge base
        kb.create_investigation("PIR-TEST-001", "Test", "test.onmicrosoft.com")
        kb.add_ioc("PIR-TEST-001", "ip", "97.93.69.128", "Known attacker", "BLOCKED")

        log_entry = {
            'userPrincipalName': 'victim@test.com',
            'ipAddress': '97.93.69.128',
            'userAgent': 'Mozilla/5.0 Chrome/120.0',
            'createdDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_sign_in(log_entry)

        assert result.risk_level == RiskLevel.HIGH
        assert 'IP-001' in result.rule_ids
        assert 'PIR-TEST-001' in result.context  # Cross-reference

    def test_qt_003_detect_hostinger_ip(self, triage):
        """QT-003: Detect Hostinger (budget VPS) IP."""
        # Note: In real impl, would check ASN/IP ranges
        log_entry = {
            'userPrincipalName': 'user@test.com',
            'ipAddress': '93.127.215.4',  # Hostinger range
            'userAgent': 'Mozilla/5.0 Chrome/120.0',
            'createdDateTime': '2025-12-18T10:00:00Z',
            'asn': 'AS47583'  # Hostinger ASN
        }

        result = triage.analyze_sign_in(log_entry)

        assert result.risk_level == RiskLevel.MEDIUM
        assert 'IP-002' in result.rule_ids
        assert result.confidence >= 0.7


class TestTimeDetection:
    """Test time-based detection rules (QT-004, TIME-001)."""

    def test_qt_004_detect_4am_consent(self, triage):
        """QT-004: Detect OAuth consent at 4AM (off-hours)."""
        consent_entry = {
            'clientId': 'test-app-id',
            'consentType': 'Principal',
            'scope': 'User.Read Mail.Read',
            'principalId': 'user@test.com',
            'activityDateTime': '2025-12-18T04:09:00Z'  # 4:09 AM
        }

        result = triage.analyze_consent(consent_entry)

        assert result.risk_level == RiskLevel.MEDIUM
        assert 'TIME-001' in result.rule_ids
        assert result.confidence >= 0.8

    def test_normal_business_hours_consent(self, triage):
        """Consent during business hours should not flag TIME-001."""
        consent_entry = {
            'clientId': 'test-app-id',
            'consentType': 'Principal',
            'scope': 'User.Read',
            'principalId': 'user@test.com',
            'activityDateTime': '2025-12-18T10:00:00Z'  # 10:00 AM
        }

        result = triage.analyze_consent(consent_entry)

        assert 'TIME-001' not in result.rule_ids


class TestOAuthDetection:
    """Test OAuth detection rules (QT-005, QT-006, OAUTH-001, OAUTH-002)."""

    def test_qt_005_detect_excessive_permissions(self, triage):
        """QT-005: Detect app with 89 permissions (>50 = excessive)."""
        consent_entry = {
            'clientId': '683b8f3c-cc24-4eda-9fd3-bf7f29551704',
            'consentType': 'Principal',
            'scope': ' '.join([f'Permission.{i}' for i in range(89)]),  # 89 permissions
            'principalId': 'user@test.com',
            'activityDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_consent(consent_entry)

        assert result.risk_level == RiskLevel.HIGH
        assert 'OAUTH-001' in result.rule_ids
        assert result.confidence >= 0.9

    def test_qt_006_detect_legacy_protocol(self, triage):
        """QT-006: Detect legacy protocol (IMAP/POP) consent."""
        consent_entry = {
            'clientId': 'test-app-id',
            'consentType': 'Principal',
            'scope': 'IMAP.AccessAsUser.All POP.AccessAsUser.All',
            'principalId': 'user@test.com',
            'activityDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_consent(consent_entry)

        assert result.risk_level == RiskLevel.MEDIUM
        assert 'OAUTH-002' in result.rule_ids
        assert result.confidence >= 0.8


class TestCSVProcessing:
    """Test CSV processing (QT-007, QT-008)."""

    def test_qt_007_process_empty_csv(self, triage, tmp_path):
        """QT-007: Process empty CSV returns empty results, no error."""
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['userPrincipalName', 'ipAddress', 'userAgent', 'createdDateTime'])
            # No data rows

        results = triage.process_sign_in_csv(str(csv_path))

        assert results == []

    def test_qt_008_process_malformed_csv(self, triage, tmp_path):
        """QT-008: Process malformed CSV returns error with line number."""
        csv_path = tmp_path / "malformed.csv"
        with open(csv_path, 'w') as f:
            f.write('userPrincipalName,ipAddress,userAgent,createdDateTime\n')
            f.write('user@test.com,10.0.0.1\n')  # Missing fields (line 2)

        with pytest.raises(ValueError) as exc_info:
            triage.process_sign_in_csv(str(csv_path))

        assert 'line' in str(exc_info.value).lower()


class TestReportGeneration:
    """Test report generation (QT-009)."""

    def test_qt_009_generate_triage_report(self, triage):
        """QT-009: Generate markdown report with HIGH/MEDIUM/LOW sections."""
        # Create some findings
        findings = [
            TriageResult(
                user='zacd@fyna.com.au',
                risk_level=RiskLevel.HIGH,
                rule_ids=['UA-001'],
                confidence=1.0,
                details='Safari on Windows10'
            ),
            TriageResult(
                user='juliang@fyna.com.au',
                risk_level=RiskLevel.MEDIUM,
                rule_ids=['TIME-001'],
                confidence=0.8,
                details='4:09 AM consent'
            ),
        ]

        report = triage.generate_report(
            customer_name='Fyna Foods',
            findings=findings
        )

        # Check report structure
        assert '# Triage Report: Fyna Foods' in report
        assert '## HIGH RISK' in report
        assert '## MEDIUM RISK' in report
        assert 'zacd@fyna.com.au' in report
        assert 'UA-001' in report
        assert 'Safari on Windows10' in report


class TestKnowledgeBaseIntegration:
    """Test knowledge base integration (QT-010)."""

    def test_qt_010_cross_reference_with_kb(self, triage, kb):
        """QT-010: Enrich findings with prior investigation data."""
        # Add prior investigation data
        kb.create_investigation("PIR-PRIOR-001", "Prior Customer", "prior.onmicrosoft.com")
        kb.add_ioc("PIR-PRIOR-001", "ip", "93.127.215.4", "Hostinger - seen in credential stuffing")
        kb.add_pattern("PIR-PRIOR-001", "impossible_ua", "Safari.*Windows", 1.0)

        log_entry = {
            'userPrincipalName': 'newvictim@test.com',
            'ipAddress': '93.127.215.4',  # Same IP as prior investigation
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/605.1.15 Safari/605.1.15',
            'createdDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_sign_in(log_entry)

        # Should have enrichment from prior investigation
        assert 'PIR-PRIOR-001' in result.context
        # Context should reference the prior investigation details
        assert 'credential stuffing' in result.context.lower() or 'hostinger' in result.context.lower()


class TestRiskLevelClassification:
    """Test risk level classification."""

    def test_high_risk_threshold(self, triage):
        """HIGH risk for confidence >= 0.9."""
        log_entry = {
            'userPrincipalName': 'user@test.com',
            'ipAddress': '10.0.0.1',
            'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/605.1.15 Safari/605.1.15',
            'createdDateTime': '2025-12-18T10:00:00Z'
        }

        result = triage.analyze_sign_in(log_entry)

        assert result.risk_level == RiskLevel.HIGH

    def test_multiple_rules_increase_risk(self, triage):
        """Multiple medium-confidence rules should escalate to HIGH."""
        # Entry with both off-hours AND budget VPS
        consent_entry = {
            'clientId': 'test-app-id',
            'consentType': 'Principal',
            'scope': 'User.Read Mail.Read',
            'principalId': 'user@test.com',
            'activityDateTime': '2025-12-18T04:00:00Z',  # Off-hours
            'ipAddress': '93.127.215.4',  # Budget VPS
            'asn': 'AS47583'
        }

        result = triage.analyze_consent(consent_entry)

        # Two medium rules should compound
        assert len(result.rule_ids) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
