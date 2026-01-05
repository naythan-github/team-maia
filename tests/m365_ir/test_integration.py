#!/usr/bin/env python3
"""
Integration Tests for M365 IR Log Database Pipeline

Phase: P3.5 - Integration Test Design
Requirements: IR_LOG_DATABASE_REQUIREMENTS.md

Tests full pipeline: CSV import → SQLite storage → Query → Results
"""

import pytest
import csv
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from claude.tools.m365_ir import (
    IRLogDatabase,
    LogImporter,
    ImportResult,
    LogQuery,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def sample_exports(temp_dir):
    """Create realistic M365 log exports."""
    exports_dir = temp_dir / "exports"
    exports_dir.mkdir()

    # Create sign-in logs with attack pattern
    signin_path = exports_dir / "1_CustomerSignInLogs.csv"
    with open(signin_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
            'AppDisplayName', 'IPAddress', 'City', 'Country',
            'Browser', 'OS', 'Status', 'RiskState', 'RiskLevelDuringSignIn',
            'ConditionalAccessStatus'
        ])
        writer.writeheader()

        # Normal Australian logins (use valid 12-hour times)
        times = ['9:30:00 AM', '10:30:00 AM', '11:30:00 AM', '12:30:00 PM', '1:30:00 PM']
        for i, time in enumerate(times):
            writer.writerow({
                'CreatedDateTime': f'10/12/2025 {time}',
                'UserPrincipalName': 'victim@customer.com',
                'UserDisplayName': 'Victim User',
                'AppDisplayName': 'Microsoft Office',
                'IPAddress': '203.0.113.100',
                'City': 'Sydney',
                'Country': 'Australia',
                'Browser': 'Chrome',
                'OS': 'Windows',
                'Status': 'Success',
                'RiskState': 'none',
                'RiskLevelDuringSignIn': 'none',
                'ConditionalAccessStatus': 'success'
            })

        # Suspicious foreign login
        writer.writerow({
            'CreatedDateTime': '15/12/2025 3:00:00 AM',
            'UserPrincipalName': 'victim@customer.com',
            'UserDisplayName': 'Victim User',
            'AppDisplayName': 'Exchange Online',
            'IPAddress': '185.234.100.50',
            'City': 'Moscow',
            'Country': 'Russia',
            'Browser': 'Safari',
            'OS': 'Windows',
            'Status': 'Success',
            'RiskState': 'atRisk',
            'RiskLevelDuringSignIn': 'high',
            'ConditionalAccessStatus': 'success'
        })

    # Create UAL with inbox rule
    ual_path = exports_dir / "7_CustomerFullAuditLog.csv"
    with open(ual_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreationDate', 'UserIds', 'Operations', 'Workload',
            'RecordType', 'ResultStatus', 'ClientIP', 'ObjectId', 'AuditData'
        ])
        writer.writeheader()

        # Inbox rule creation (attacker action)
        writer.writerow({
            'CreationDate': '15/12/2025 3:05:00 AM',
            'UserIds': 'victim@customer.com',
            'Operations': 'Set-InboxRule',
            'Workload': 'Exchange',
            'RecordType': '1',
            'ResultStatus': 'Succeeded',
            'ClientIP': '185.234.100.50',
            'ObjectId': 'rule-attacker-001',
            'AuditData': json.dumps({
                'RuleName': 'RSS Feeds',
                'ForwardTo': 'attacker@evil.com',
                'ClientIPAddress': '185.234.100.50'
            })
        })

        # Mail access (data exfil)
        writer.writerow({
            'CreationDate': '15/12/2025 3:10:00 AM',
            'UserIds': 'victim@customer.com',
            'Operations': 'MailItemsAccessed',
            'Workload': 'Exchange',
            'RecordType': '2',
            'ResultStatus': 'Succeeded',
            'ClientIP': '185.234.100.50',
            'ObjectId': '',
            'AuditData': json.dumps({
                'ItemCount': 250,
                'ClientIPAddress': '185.234.100.50'
            })
        })

    return exports_dir


class TestFullPipeline:
    """Integration tests for complete import → query pipeline."""

    def test_import_and_query_by_ip(self, temp_dir, sample_exports):
        """Full pipeline: import logs → query by suspicious IP."""
        # Create case
        db = IRLogDatabase(case_id="PIR-INT-TEST-001", base_path=str(temp_dir))
        db.create()

        # Import all logs
        importer = LogImporter(db)
        results = importer.import_all(sample_exports)

        assert 'sign_in' in results
        assert results['sign_in'].records_imported == 6  # 5 normal + 1 suspicious
        assert 'ual' in results
        assert results['ual'].records_imported == 2

        # Query suspicious IP
        query = LogQuery(db)
        suspicious_activity = query.activity_by_ip('185.234.100.50')

        # Should find signin + UAL entries
        assert len(suspicious_activity) >= 3  # 1 signin + 2 UAL
        sources = set(r['source'] for r in suspicious_activity)
        assert 'sign_in_logs' in sources
        assert 'unified_audit_log' in sources

    def test_import_and_query_user_timeline(self, temp_dir, sample_exports):
        """Full pipeline: import logs → build user timeline."""
        db = IRLogDatabase(case_id="PIR-INT-TEST-002", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)
        importer.import_all(sample_exports)

        query = LogQuery(db)
        timeline = query.activity_by_user('victim@customer.com')

        # Should have all 8 entries
        assert len(timeline) == 8  # 6 signins + 2 UAL

        # Should be sorted chronologically
        timestamps = [r['timestamp'] for r in timeline]
        assert timestamps == sorted(timestamps)

    def test_suspicious_operations_detected(self, temp_dir, sample_exports):
        """Suspicious operations should be detected."""
        db = IRLogDatabase(case_id="PIR-INT-TEST-003", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)
        importer.import_all(sample_exports)

        query = LogQuery(db)
        suspicious = query.suspicious_operations()

        # Should detect Set-InboxRule and MailItemsAccessed
        operations = [r['operation'] for r in suspicious]
        assert 'Set-InboxRule' in operations
        assert 'MailItemsAccessed' in operations

    def test_cross_table_correlation(self, temp_dir, sample_exports):
        """Cross-table queries should correlate data."""
        db = IRLogDatabase(case_id="PIR-INT-TEST-004", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)
        importer.import_all(sample_exports)

        query = LogQuery(db)
        results = query.execute_cross_table(
            tables=['sign_in_logs', 'unified_audit_log'],
            where="ip_address = ? OR client_ip = ?",
            params=('185.234.100.50', '185.234.100.50')
        )

        # Should get results from both tables
        assert len(results) >= 3
        sources = set(r['source'] for r in results)
        assert len(sources) >= 2

    def test_reimport_is_idempotent(self, temp_dir, sample_exports):
        """Reimporting same files should not duplicate data."""
        db = IRLogDatabase(case_id="PIR-INT-TEST-005", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)

        # First import
        results1 = importer.import_all(sample_exports)
        first_count = sum(r.records_imported for r in results1.values())

        # Second import
        results2 = importer.import_all(sample_exports)
        second_count = sum(r.records_imported for r in results2.values())

        # Second import should import 0 records (already imported)
        assert second_count == 0

        # Database should have same count as first import
        stats = db.get_stats()
        total = stats['sign_in_logs'] + stats['unified_audit_log']
        assert total == 8


class TestCaseIsolation:
    """Tests for case data isolation."""

    def test_cases_are_isolated(self, temp_dir, sample_exports):
        """Data from one case should not leak to another."""
        # Create two cases
        db1 = IRLogDatabase(case_id="PIR-CASE-001", base_path=str(temp_dir))
        db2 = IRLogDatabase(case_id="PIR-CASE-002", base_path=str(temp_dir))

        db1.create()
        db2.create()

        # Import to case 1 only
        importer1 = LogImporter(db1)
        importer1.import_all(sample_exports)

        # Query case 2 - should be empty
        query2 = LogQuery(db2)
        results = query2.activity_by_user('victim@customer.com')

        assert results == []

        # Query case 1 - should have data
        query1 = LogQuery(db1)
        results = query1.activity_by_user('victim@customer.com')

        assert len(results) == 8


class TestRawSQLQueries:
    """Tests for raw SQL query capability."""

    def test_complex_sql_query(self, temp_dir, sample_exports):
        """Complex SQL queries should work."""
        db = IRLogDatabase(case_id="PIR-SQL-TEST-001", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)
        importer.import_all(sample_exports)

        query = LogQuery(db)

        # Complex query: signins from non-AU countries
        results = query.execute("""
            SELECT user_principal_name, ip_address, location_country, timestamp
            FROM sign_in_logs
            WHERE location_country != 'Australia'
            ORDER BY timestamp
        """)

        assert len(results) == 1
        assert results[0]['location_country'] == 'Russia'

    def test_aggregation_query(self, temp_dir, sample_exports):
        """Aggregation queries should work."""
        db = IRLogDatabase(case_id="PIR-SQL-TEST-002", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)
        importer.import_all(sample_exports)

        query = LogQuery(db)

        # Count signins by country
        results = query.execute("""
            SELECT location_country, COUNT(*) as count
            FROM sign_in_logs
            GROUP BY location_country
            ORDER BY count DESC
        """)

        assert len(results) == 2
        assert results[0]['location_country'] == 'Australia'
        assert results[0]['count'] == 5


class TestPerformanceBaseline:
    """Basic performance tests."""

    def test_import_performance(self, temp_dir):
        """Import should handle reasonable file sizes."""
        # Create larger test file
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir()

        signin_path = exports_dir / "1_LargeSignInLogs.csv"
        with open(signin_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'CreatedDateTime', 'UserPrincipalName', 'IPAddress', 'Country', 'Status'
            ])
            writer.writeheader()

            for i in range(1000):
                writer.writerow({
                    'CreatedDateTime': f'{(i % 28) + 1}/12/2025 {(i % 12) + 1}:00:00 AM',
                    'UserPrincipalName': f'user{i % 10}@test.com',
                    'IPAddress': f'192.168.{i % 256}.{(i // 256) % 256}',
                    'Country': 'Australia',
                    'Status': 'Success'
                })

        db = IRLogDatabase(case_id="PIR-PERF-TEST-001", base_path=str(temp_dir))
        db.create()

        importer = LogImporter(db)
        result = importer.import_sign_in_logs(signin_path)

        # Should complete in reasonable time
        assert result.duration_seconds < 5.0
        assert result.records_imported == 1000

    def test_query_performance(self, temp_dir):
        """Queries should be fast on indexed columns."""
        db = IRLogDatabase(case_id="PIR-PERF-TEST-002", base_path=str(temp_dir))
        db.create()

        # Insert test data
        conn = db.connect()
        now = datetime.now()
        for i in range(1000):
            conn.execute("""
                INSERT INTO sign_in_logs
                (timestamp, user_principal_name, ip_address, location_country, raw_record, imported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                (now - timedelta(hours=i)).isoformat(),
                f'user{i % 10}@test.com',
                f'192.168.{i % 256}.{(i // 256) % 256}',
                'Australia',
                '{}',
                now.isoformat()
            ))
        conn.commit()
        conn.close()

        query = LogQuery(db)

        import time
        start = time.time()
        for _ in range(100):
            query.activity_by_user('user0@test.com')
        elapsed = time.time() - start

        # 100 queries should complete in < 1 second
        assert elapsed < 1.0
