#!/usr/bin/env python3
"""
Tests for Phase 261.3 - Post-Compromise Validator

Tests the compromise_validator module which validates whether a successful
authentication represents actual account compromise by analyzing 11 indicators:

1. mailbox_access_from_ip - Mailbox access from the IP
2. ual_operations_from_ip - UAL operations from the IP
3. inbox_rules_created - Inbox rules created after login
4. password_changed - Password changed after login
5. follow_on_signins - Follow-on sign-ins from same IP
6. persistence_mechanisms - MFA/auth method changes
7. data_exfiltration - Large file downloads/shares
8. oauth_app_consents - OAuth app consents from IP
9. mfa_modifications - MFA registration changes
10. delegate_access_changes - Mailbox delegate access changes
11. orphan_ual_activity - UAL activity without sign-in (token theft)

Critical requirements:
- User matching MUST be exact UPN (WHERE user_principal_name = ?)
- Extended window = 72 hours (not 24)
- NO_COMPROMISE confidence capped at 80% (not 100%)

Author: Maia System
Created: 2025-01-09
Phase: 261.3
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

# Import will be available after implementation
from claude.tools.m365_ir.compromise_validator import (
    validate_compromise,
    check_mailbox_access_from_ip,
    check_ual_operations_from_ip,
    check_inbox_rules_created,
    check_password_changed,
    check_follow_on_signins,
    check_persistence_mechanisms,
    check_data_exfiltration,
    check_oauth_app_consents,
    check_mfa_modifications,
    check_delegate_access_changes,
    check_orphan_ual_activity,
)


@pytest.fixture
def test_db():
    """Create a temporary test database with schema."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create sign_in_logs table
    cursor.execute("""
        CREATE TABLE sign_in_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_principal_name TEXT NOT NULL,
            user_display_name TEXT,
            ip_address TEXT,
            location_city TEXT,
            location_country TEXT,
            client_app TEXT,
            status_error_code INTEGER,
            status_failure_reason TEXT,
            conditional_access_status TEXT,
            mfa_detail TEXT,
            risk_level TEXT,
            raw_record BLOB,
            imported_at TEXT NOT NULL
        )
    """)

    # Create unified_audit_log table
    cursor.execute("""
        CREATE TABLE unified_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT,
            operation TEXT NOT NULL,
            workload TEXT,
            record_type INTEGER,
            result_status TEXT,
            client_ip TEXT,
            user_agent TEXT,
            object_id TEXT,
            item_type TEXT,
            audit_data BLOB,
            raw_record BLOB,
            imported_at TEXT NOT NULL
        )
    """)

    # Create mailbox_audit_log table
    cursor.execute("""
        CREATE TABLE mailbox_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user TEXT NOT NULL,
            operation TEXT NOT NULL,
            log_on_type TEXT,
            client_ip TEXT,
            client_info TEXT,
            item_id TEXT,
            folder_path TEXT,
            subject TEXT,
            result TEXT,
            raw_record BLOB,
            imported_at TEXT NOT NULL
        )
    """)

    # Create inbox_rules table
    cursor.execute("""
        CREATE TABLE inbox_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user TEXT NOT NULL,
            operation TEXT,
            rule_name TEXT,
            rule_id TEXT,
            forward_to TEXT,
            forward_as_attachment_to TEXT,
            redirect_to TEXT,
            delete_message INTEGER,
            move_to_folder TEXT,
            conditions TEXT,
            client_ip TEXT,
            raw_record BLOB,
            imported_at TEXT NOT NULL
        )
    """)

    # Create oauth_consents table
    cursor.execute("""
        CREATE TABLE oauth_consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_principal_name TEXT,
            app_id TEXT NOT NULL,
            app_display_name TEXT,
            permissions TEXT,
            consent_type TEXT,
            client_ip TEXT,
            risk_score REAL,
            raw_record BLOB,
            imported_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink()


class TestMailboxAccessFromIP:
    """Test check_mailbox_access_from_ip indicator."""

    def test_mailbox_access_found(self, test_db):
        """Test mailbox access from IP is detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Insert sign-in
        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Insert mailbox access within 72h
        access_time = signin_time + timedelta(hours=2)
        cursor.execute("""
            INSERT INTO mailbox_audit_log (timestamp, user, operation, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (access_time.isoformat(), 'user@example.com', 'MailItemsAccessed', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_mailbox_access_from_ip(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is True
        assert result['count'] == 1
        assert result['confidence'] >= 0.80
        assert 'operations' in result

    def test_mailbox_access_different_ip(self, test_db):
        """Test mailbox access from different IP is not counted."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        access_time = signin_time + timedelta(hours=2)
        cursor.execute("""
            INSERT INTO mailbox_audit_log (timestamp, user, operation, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (access_time.isoformat(), 'user@example.com', 'MailItemsAccessed', '5.6.7.8', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_mailbox_access_from_ip(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is False
        assert result['count'] == 0

    def test_mailbox_access_outside_window(self, test_db):
        """Test mailbox access outside 72h window is not counted."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Access 73 hours later (outside window)
        access_time = signin_time + timedelta(hours=73)
        cursor.execute("""
            INSERT INTO mailbox_audit_log (timestamp, user, operation, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (access_time.isoformat(), 'user@example.com', 'MailItemsAccessed', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_mailbox_access_from_ip(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is False
        assert result['count'] == 0

    def test_exact_upn_matching(self, test_db):
        """Test that UPN matching is exact, not partial."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        access_time = signin_time + timedelta(hours=2)
        # Different user with similar name
        cursor.execute("""
            INSERT INTO mailbox_audit_log (timestamp, user, operation, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (access_time.isoformat(), 'otheruser@example.com', 'MailItemsAccessed', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_mailbox_access_from_ip(test_db, 'user@example.com', '1.2.3.4', signin_time)

        # Should NOT match otheruser@example.com
        assert result['detected'] is False
        assert result['count'] == 0


class TestUALOperationsFromIP:
    """Test check_ual_operations_from_ip indicator."""

    def test_ual_operations_found(self, test_db):
        """Test UAL operations from IP are detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Insert UAL operation within 72h
        op_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, client_ip, workload, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (op_time.isoformat(), 'user@example.com', 'FileAccessed', '1.2.3.4', 'SharePoint', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_ual_operations_from_ip(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is True
        assert result['count'] == 1
        assert result['confidence'] >= 0.75
        assert 'operations' in result

    def test_ual_operations_different_user(self, test_db):
        """Test UAL operations for different user are not counted."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        op_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, client_ip, workload, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (op_time.isoformat(), 'different@example.com', 'FileAccessed', '1.2.3.4', 'SharePoint', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_ual_operations_from_ip(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is False
        assert result['count'] == 0


class TestInboxRulesCreated:
    """Test check_inbox_rules_created indicator."""

    def test_inbox_rule_created(self, test_db):
        """Test inbox rule creation is detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Create inbox rule within 72h
        rule_time = signin_time + timedelta(hours=3)
        cursor.execute("""
            INSERT INTO inbox_rules (timestamp, user, operation, rule_name, forward_to, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (rule_time.isoformat(), 'user@example.com', 'New-InboxRule', 'Forward all', 'attacker@evil.com', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_inbox_rules_created(test_db, 'user@example.com', signin_time)

        assert result['detected'] is True
        assert result['count'] == 1
        assert result['confidence'] >= 0.90
        assert 'rules' in result

    def test_no_forwarding_rules_lower_confidence(self, test_db):
        """Test non-forwarding rules have lower confidence."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        rule_time = signin_time + timedelta(hours=3)
        cursor.execute("""
            INSERT INTO inbox_rules (timestamp, user, operation, rule_name, move_to_folder, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rule_time.isoformat(), 'user@example.com', 'New-InboxRule', 'Organize', 'Archive', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_inbox_rules_created(test_db, 'user@example.com', signin_time)

        assert result['detected'] is True
        assert result['confidence'] < 0.90  # Lower than forwarding rules


class TestPasswordChanged:
    """Test check_password_changed indicator."""

    def test_password_changed_detected(self, test_db):
        """Test password change is detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Password change within 72h
        pw_time = signin_time + timedelta(hours=4)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, workload, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (pw_time.isoformat(), 'user@example.com', 'Change user password', 'AzureActiveDirectory', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_password_changed(test_db, 'user@example.com', signin_time)

        assert result['detected'] is True
        assert result['confidence'] >= 0.85

    def test_password_reset_also_detected(self, test_db):
        """Test password reset is also detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        pw_time = signin_time + timedelta(hours=4)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, workload, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (pw_time.isoformat(), 'user@example.com', 'Reset user password', 'AzureActiveDirectory', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_password_changed(test_db, 'user@example.com', signin_time)

        assert result['detected'] is True


class TestFollowOnSignIns:
    """Test check_follow_on_signins indicator."""

    def test_follow_on_signins_detected(self, test_db):
        """Test follow-on sign-ins from same IP are detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Follow-on sign-in within 72h
        followon_time = signin_time + timedelta(hours=5)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, status_error_code, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (followon_time.isoformat(), 'user@example.com', '1.2.3.4', 0, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_follow_on_signins(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is True
        assert result['count'] >= 1
        assert result['confidence'] >= 0.70


class TestOAuthAppConsents:
    """Test check_oauth_app_consents indicator (NEW in v2.0)."""

    def test_oauth_consent_detected(self, test_db):
        """Test OAuth app consent is detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # OAuth consent within 72h
        consent_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO oauth_consents (timestamp, user_principal_name, app_id, app_display_name, permissions, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (consent_time.isoformat(), 'user@example.com', 'app-123', 'Suspicious App', 'Mail.Read,Mail.Send', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_oauth_app_consents(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['detected'] is True
        assert result['count'] == 1
        assert result['confidence'] >= 0.85
        assert 'apps' in result


class TestMFAModifications:
    """Test check_mfa_modifications indicator (NEW in v2.0)."""

    def test_mfa_registration_detected(self, test_db):
        """Test MFA registration change is detected."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # MFA modification within 72h
        mfa_time = signin_time + timedelta(hours=2)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, workload, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (mfa_time.isoformat(), 'user@example.com', 'User registered security info', 'AzureActiveDirectory', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_mfa_modifications(test_db, 'user@example.com', signin_time)

        assert result['detected'] is True
        assert result['confidence'] >= 0.90


class TestOrphanUALActivity:
    """Test check_orphan_ual_activity indicator (NEW in v2.0) - token theft detection."""

    def test_orphan_activity_detected(self, test_db):
        """Test UAL activity without corresponding sign-in is detected (token theft indicator)."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)

        # UAL activity from IP with NO sign-in record
        activity_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, client_ip, workload, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (activity_time.isoformat(), 'user@example.com', 'FileDownloaded', '5.6.7.8', 'SharePoint', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_orphan_ual_activity(test_db, 'user@example.com', signin_time)

        assert result['detected'] is True
        assert result['count'] >= 1
        assert result['confidence'] >= 0.95  # Very high confidence for token theft
        assert 'orphan_activities' in result

    def test_no_orphan_when_signin_exists(self, test_db):
        """Test that activity with matching sign-in is NOT counted as orphan."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)

        # Sign-in exists
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '5.6.7.8', datetime.now().isoformat()))

        # UAL activity from same IP
        activity_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, client_ip, workload, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (activity_time.isoformat(), 'user@example.com', 'FileDownloaded', '5.6.7.8', 'SharePoint', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = check_orphan_ual_activity(test_db, 'user@example.com', signin_time)

        # Should NOT be detected as orphan since sign-in exists
        assert result['detected'] is False


class TestValidateCompromise:
    """Test main validate_compromise function."""

    def test_no_compromise_clean_login(self, test_db):
        """Test clean login returns NO_COMPROMISE with max 80% confidence."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = validate_compromise(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['verdict'] == 'NO_COMPROMISE'
        assert result['confidence'] <= 0.80  # Capped at 80%
        assert 'indicators' in result
        assert result['indicators_detected'] == 0

    def test_likely_compromise_multiple_indicators(self, test_db):
        """Test multiple indicators result in LIKELY_COMPROMISE."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Add inbox rule
        rule_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO inbox_rules (timestamp, user, operation, rule_name, forward_to, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rule_time.isoformat(), 'user@example.com', 'New-InboxRule', 'Forward', 'attacker@evil.com', datetime.now().isoformat()))

        # Add mailbox access
        access_time = signin_time + timedelta(hours=2)
        cursor.execute("""
            INSERT INTO mailbox_audit_log (timestamp, user, operation, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (access_time.isoformat(), 'user@example.com', 'MailItemsAccessed', '1.2.3.4', datetime.now().isoformat()))

        # Add OAuth consent
        consent_time = signin_time + timedelta(hours=3)
        cursor.execute("""
            INSERT INTO oauth_consents (timestamp, user_principal_name, app_id, app_display_name, permissions, client_ip, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (consent_time.isoformat(), 'user@example.com', 'app-123', 'Suspicious', 'Mail.Read', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = validate_compromise(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['verdict'] == 'LIKELY_COMPROMISE'
        assert result['indicators_detected'] >= 3
        assert result['confidence'] >= 0.85

    def test_confirmed_compromise_high_confidence_indicators(self, test_db):
        """Test high-confidence indicators result in CONFIRMED_COMPROMISE."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        signin_time = datetime(2025, 11, 25, 4, 55, 50)
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (signin_time.isoformat(), 'user@example.com', '1.2.3.4', datetime.now().isoformat()))

        # Add orphan UAL activity (very high confidence indicator - token theft)
        activity_time = signin_time + timedelta(hours=1)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, client_ip, workload, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (activity_time.isoformat(), 'user@example.com', 'FileDownloaded', '5.6.7.8', 'SharePoint', datetime.now().isoformat()))

        # Add inbox forwarding rule
        rule_time = signin_time + timedelta(hours=2)
        cursor.execute("""
            INSERT INTO inbox_rules (timestamp, user, operation, rule_name, forward_to, imported_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rule_time.isoformat(), 'user@example.com', 'New-InboxRule', 'Forward', 'attacker@evil.com', datetime.now().isoformat()))

        # Add MFA modification
        mfa_time = signin_time + timedelta(hours=3)
        cursor.execute("""
            INSERT INTO unified_audit_log (timestamp, user_id, operation, workload, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (mfa_time.isoformat(), 'user@example.com', 'User registered security info', 'AzureActiveDirectory', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = validate_compromise(test_db, 'user@example.com', '1.2.3.4', signin_time)

        assert result['verdict'] == 'CONFIRMED_COMPROMISE'
        assert result['confidence'] >= 0.95
        assert result['indicators_detected'] >= 3


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_database(self):
        """Test handling of nonexistent database."""
        with pytest.raises(Exception):
            validate_compromise('/nonexistent/path.db', 'user@example.com', '1.2.3.4', datetime.now())

    def test_empty_database(self, test_db):
        """Test handling of empty database (no records)."""
        result = validate_compromise(test_db, 'user@example.com', '1.2.3.4', datetime.now())

        assert result['verdict'] == 'NO_COMPROMISE'
        assert result['indicators_detected'] == 0

    def test_user_not_found(self, test_db):
        """Test handling of user that doesn't exist in database."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Add data for different user
        cursor.execute("""
            INSERT INTO sign_in_logs (timestamp, user_principal_name, ip_address, imported_at)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), 'other@example.com', '1.2.3.4', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        result = validate_compromise(test_db, 'notfound@example.com', '1.2.3.4', datetime.now())

        assert result['verdict'] == 'NO_COMPROMISE'
        assert result['indicators_detected'] == 0
