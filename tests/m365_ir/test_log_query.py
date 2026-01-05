#!/usr/bin/env python3
"""
TDD Tests for LogQuery - Query interface for investigation database

Phase: P3 - Test Design (RED)
Requirements: IR_LOG_DATABASE_REQUIREMENTS.md

Tests written BEFORE implementation per TDD protocol.
"""

import pytest
import sqlite3
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

# Import will fail until implementation exists (expected RED state)
try:
    from claude.tools.m365_ir.log_database import IRLogDatabase
    from claude.tools.m365_ir.log_query import LogQuery
except ImportError:
    IRLogDatabase = None
    LogQuery = None


@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def db(temp_dir):
    """Create IRLogDatabase instance with test data."""
    if IRLogDatabase is None:
        pytest.skip("IRLogDatabase not yet implemented")

    db = IRLogDatabase(case_id="PIR-QUERY-TEST-001", base_path=str(temp_dir))
    db.create()

    # Populate with test data
    conn = db.connect()
    now = datetime.now()

    # Sign-in logs - mix of normal and suspicious
    signin_data = [
        (now - timedelta(hours=4), 'victim@example.com', '203.0.113.1', 'Sydney', 'Australia', 'success'),
        (now - timedelta(hours=3), 'victim@example.com', '203.0.113.1', 'Sydney', 'Australia', 'success'),
        (now - timedelta(hours=2), 'victim@example.com', '185.234.100.50', 'Moscow', 'Russia', 'success'),  # Suspicious
        (now - timedelta(hours=1), 'victim@example.com', '185.234.100.50', 'Moscow', 'Russia', 'success'),  # Suspicious
        (now, 'other@example.com', '203.0.113.2', 'Melbourne', 'Australia', 'success'),
    ]

    for ts, user, ip, city, country, status in signin_data:
        conn.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, location_city, location_country,
             status_error_code, raw_record, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts.isoformat(), user, ip, city, country, 0 if status == 'success' else 1,
              json.dumps({'test': True}), now.isoformat()))

    # UAL entries
    ual_data = [
        (now - timedelta(hours=2), 'victim@example.com', 'Set-InboxRule', 'Exchange', '185.234.100.50'),
        (now - timedelta(hours=1, minutes=30), 'victim@example.com', 'MailItemsAccessed', 'Exchange', '185.234.100.50'),
        (now - timedelta(hours=1), 'victim@example.com', 'Send', 'Exchange', '185.234.100.50'),
    ]

    for ts, user, op, workload, ip in ual_data:
        conn.execute("""
            INSERT INTO unified_audit_log
            (timestamp, user_id, operation, workload, client_ip, audit_data, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ts.isoformat(), user, op, workload, ip, json.dumps({'test': True}), now.isoformat()))

    # Mailbox audit
    conn.execute("""
        INSERT INTO mailbox_audit_log
        (timestamp, user, operation, client_ip, raw_record, imported_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ((now - timedelta(hours=1, minutes=45)).isoformat(), 'victim@example.com',
          'FolderBind', '185.234.100.50', json.dumps({'test': True}), now.isoformat()))

    # Inbox rules
    conn.execute("""
        INSERT INTO inbox_rules
        (timestamp, user, operation, rule_name, forward_to, client_ip, raw_record, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ((now - timedelta(hours=2)).isoformat(), 'victim@example.com', 'Set-InboxRule',
          'Forward External', 'attacker@evil.com', '185.234.100.50',
          json.dumps({'test': True}), now.isoformat()))

    conn.commit()
    conn.close()

    return db


@pytest.fixture
def query(db):
    """Create LogQuery instance."""
    if LogQuery is None:
        pytest.skip("LogQuery not yet implemented")
    return LogQuery(db)


class TestLogQueryCreation:
    """Tests for LogQuery instantiation."""

    def test_create_with_database(self, db):
        """LogQuery should accept IRLogDatabase."""
        if LogQuery is None:
            pytest.skip("LogQuery not yet implemented")
        query = LogQuery(db)
        assert query is not None


class TestActivityByIP:
    """Tests for IP-based activity queries."""

    def test_activity_by_ip_returns_list(self, query):
        """activity_by_ip should return list of dicts."""
        results = query.activity_by_ip('185.234.100.50')
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], dict)

    def test_activity_by_ip_includes_all_tables(self, query):
        """Should include results from all log types."""
        results = query.activity_by_ip('185.234.100.50')

        # Should have sign-in, UAL, and mailbox entries
        sources = set(r.get('source', r.get('log_type', '')) for r in results)
        assert 'sign_in_logs' in sources or 'signin' in sources
        assert 'unified_audit_log' in sources or 'ual' in sources

    def test_activity_by_ip_no_results(self, query):
        """Should return empty list for unknown IP."""
        results = query.activity_by_ip('10.0.0.1')
        assert results == []

    def test_activity_by_ip_sorted_chronologically(self, query):
        """Results should be sorted by timestamp."""
        results = query.activity_by_ip('185.234.100.50')

        timestamps = [r['timestamp'] for r in results]
        assert timestamps == sorted(timestamps)


class TestActivityByUser:
    """Tests for user-based activity queries."""

    def test_activity_by_user_returns_list(self, query):
        """activity_by_user should return list of dicts."""
        results = query.activity_by_user('victim@example.com')
        assert isinstance(results, list)
        assert len(results) > 0

    def test_activity_by_user_all_entries(self, query):
        """Should return all activity for user."""
        results = query.activity_by_user('victim@example.com')
        # Should have signin (4) + UAL (3) + mailbox (1) = 8+ entries
        assert len(results) >= 8

    def test_activity_by_user_with_time_filter(self, query):
        """Should filter by start/end time."""
        now = datetime.now()
        results = query.activity_by_user(
            'victim@example.com',
            start=now - timedelta(hours=3),
            end=now - timedelta(hours=1)
        )

        # All results should be within time range
        for r in results:
            ts = datetime.fromisoformat(r['timestamp'])
            assert ts >= now - timedelta(hours=3)
            assert ts <= now - timedelta(hours=1)

    def test_activity_by_user_unknown_user(self, query):
        """Should return empty list for unknown user."""
        results = query.activity_by_user('nonexistent@example.com')
        assert results == []


class TestSuspiciousOperations:
    """Tests for pre-filtered suspicious operation queries."""

    def test_suspicious_operations_returns_list(self, query):
        """suspicious_operations should return list of dicts."""
        results = query.suspicious_operations()
        assert isinstance(results, list)

    def test_suspicious_operations_includes_inbox_rules(self, query):
        """Should include inbox rule changes."""
        results = query.suspicious_operations()

        operations = [r.get('operation', '') for r in results]
        assert any('InboxRule' in op for op in operations)

    def test_suspicious_operations_includes_mail_access(self, query):
        """Should include bulk mail access."""
        results = query.suspicious_operations()

        operations = [r.get('operation', '') for r in results]
        assert any('MailItemsAccessed' in op for op in operations)


class TestInboxRulesSummary:
    """Tests for inbox rules summary."""

    def test_inbox_rules_summary_returns_list(self, query):
        """inbox_rules_summary should return list of dicts."""
        results = query.inbox_rules_summary()
        assert isinstance(results, list)

    def test_inbox_rules_summary_includes_forwarding(self, query):
        """Should include forwarding targets."""
        results = query.inbox_rules_summary()

        assert len(results) >= 1
        rule = results[0]
        assert 'forward_to' in rule or 'forwardTo' in rule


class TestOAuthConsentsSummary:
    """Tests for OAuth consents summary."""

    def test_oauth_consents_summary_returns_list(self, query):
        """oauth_consents_summary should return list."""
        results = query.oauth_consents_summary()
        assert isinstance(results, list)


class TestRawSQLExecution:
    """Tests for raw SQL query execution."""

    def test_execute_returns_list(self, query):
        """execute should return list of dicts."""
        results = query.execute("SELECT * FROM sign_in_logs LIMIT 2")
        assert isinstance(results, list)
        assert len(results) == 2
        assert isinstance(results[0], dict)

    def test_execute_with_params(self, query):
        """execute should handle parameterized queries."""
        results = query.execute(
            "SELECT * FROM sign_in_logs WHERE ip_address = ?",
            ('185.234.100.50',)
        )
        assert len(results) == 2  # Two suspicious logins

    def test_execute_prevents_injection(self, query):
        """Should use parameterized queries, not string interpolation."""
        # This should not cause SQL injection
        results = query.execute(
            "SELECT * FROM sign_in_logs WHERE user_principal_name = ?",
            ("'; DROP TABLE sign_in_logs; --",)
        )
        # Should return empty (no match), not error or drop table
        assert results == []

        # Table should still exist
        results = query.execute("SELECT COUNT(*) as cnt FROM sign_in_logs")
        assert results[0]['cnt'] > 0


class TestCrossTableQueries:
    """Tests for cross-table correlation queries."""

    def test_execute_cross_table(self, query):
        """execute_cross_table should query multiple tables."""
        results = query.execute_cross_table(
            tables=['sign_in_logs', 'unified_audit_log'],
            where="ip_address = ? OR client_ip = ?",
            params=('185.234.100.50', '185.234.100.50')
        )

        assert isinstance(results, list)
        # Should have results from both tables
        assert len(results) >= 4  # 2 signins + 3 UAL from that IP

    def test_execute_cross_table_unified_format(self, query):
        """Cross-table results should have unified format."""
        results = query.execute_cross_table(
            tables=['sign_in_logs', 'unified_audit_log'],
            where="ip_address = ? OR client_ip = ?",
            params=('185.234.100.50', '185.234.100.50')
        )

        # Each result should have source/log_type indicator
        for r in results:
            assert 'source' in r or 'log_type' in r


class TestTimelineGeneration:
    """Tests for timeline generation."""

    def test_timeline_all_user_activity(self, query):
        """Should generate complete timeline for user."""
        # This is really just activity_by_user sorted, but explicit method
        results = query.activity_by_user('victim@example.com')

        # Verify chronological order
        timestamps = [r['timestamp'] for r in results]
        assert timestamps == sorted(timestamps)

    def test_timeline_includes_source(self, query):
        """Timeline entries should indicate source."""
        results = query.activity_by_user('victim@example.com')

        for r in results:
            assert 'source' in r or 'log_type' in r


class TestQueryPerformance:
    """Tests for query performance (informational, not strict)."""

    def test_indexed_query_fast(self, query):
        """Indexed queries should be fast."""
        import time

        start = time.time()
        for _ in range(100):
            query.activity_by_ip('185.234.100.50')
        elapsed = time.time() - start

        # 100 queries should complete in < 1 second
        assert elapsed < 1.0

    def test_user_query_fast(self, query):
        """User queries should be fast."""
        import time

        start = time.time()
        for _ in range(100):
            query.activity_by_user('victim@example.com')
        elapsed = time.time() - start

        # 100 queries should complete in < 1 second
        assert elapsed < 1.0
