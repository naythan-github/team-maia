#!/usr/bin/env python3
"""
TDD Tests for IR Log Database Compression - Phase 229

Tests written BEFORE implementation per TDD protocol.
These tests verify zlib compression of raw_record and audit_data columns.
"""

import json
import pytest
import tempfile
import shutil
import csv
from pathlib import Path

# Import will fail until implementation exists (expected RED state)
try:
    from claude.tools.m365_ir.compression import (
        compress_json,
        decompress_json,
        is_compressed,
        COMPRESSION_LEVEL,
    )
except ImportError:
    compress_json = None
    decompress_json = None
    is_compressed = None
    COMPRESSION_LEVEL = None

try:
    from claude.tools.m365_ir.log_database import IRLogDatabase
    from claude.tools.m365_ir.log_importer import LogImporter
    from claude.tools.m365_ir.log_query import LogQuery
except ImportError:
    IRLogDatabase = None
    LogImporter = None
    LogQuery = None


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test databases."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def db(temp_dir):
    """Create IRLogDatabase instance for testing."""
    if IRLogDatabase is None:
        pytest.skip("IRLogDatabase not yet implemented")
    db = IRLogDatabase(case_id="PIR-COMPRESS-TEST-001", base_path=str(temp_dir))
    db.create()
    return db


@pytest.fixture
def importer(db):
    """Create LogImporter instance for testing."""
    if LogImporter is None:
        pytest.skip("LogImporter not yet implemented")
    return LogImporter(db)


@pytest.fixture
def query(db):
    """Create LogQuery instance for testing."""
    if LogQuery is None:
        pytest.skip("LogQuery not yet implemented")
    return LogQuery(db)


@pytest.fixture
def sample_signin_csv(temp_dir):
    """Create sample sign-in logs CSV with enough data to show compression benefit."""
    csv_path = temp_dir / "sample_signin.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreatedDateTime', 'UserPrincipalName', 'UserDisplayName',
            'AppDisplayName', 'IPAddress', 'City', 'Country',
            'Browser', 'OS', 'Status', 'CorrelationId',
            'ConditionalAccessStatus', 'RiskLevelDuringSignIn', 'RiskState'
        ])
        writer.writeheader()
        writer.writerow({
            'CreatedDateTime': '15/12/2025 9:30:00 AM',
            'UserPrincipalName': 'user1@example.com',
            'UserDisplayName': 'User One',
            'AppDisplayName': 'Microsoft Office 365',
            'IPAddress': '203.0.113.1',
            'City': 'Sydney',
            'Country': 'Australia',
            'Browser': 'Chrome 120.0.0.0',
            'OS': 'Windows 11',
            'Status': 'Success',
            'CorrelationId': 'abc-123-def-456',
            'ConditionalAccessStatus': 'success',
            'RiskLevelDuringSignIn': 'none',
            'RiskState': 'none'
        })
    return csv_path


@pytest.fixture
def sample_ual_csv(temp_dir):
    """Create sample UAL CSV with AuditData JSON."""
    csv_path = temp_dir / "sample_ual.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'CreationDate', 'UserIds', 'Operations', 'Workload',
            'RecordType', 'ResultStatus', 'ClientIP', 'ObjectId', 'AuditData'
        ])
        writer.writeheader()
        writer.writerow({
            'CreationDate': '15/12/2025 11:00:00 AM',
            'UserIds': 'user1@example.com',
            'Operations': 'Set-InboxRule',
            'Workload': 'Exchange',
            'RecordType': '1',
            'ResultStatus': 'Succeeded',
            'ClientIP': '185.234.100.50',
            'ObjectId': 'rule-123',
            'AuditData': json.dumps({
                'RuleName': 'Forward External',
                'ForwardTo': 'attacker@evil.com',
                'ClientIPAddress': '185.234.100.50',
                'CreationTime': '2025-12-15T11:00:00',
                'UserId': 'user1@example.com',
                'Operation': 'Set-InboxRule',
                'OrganizationId': 'org-abc-123',
                'RecordType': 1,
                'ResultStatus': 'Succeeded',
                'UserKey': 'user-key-xyz',
                'UserType': 0,
                'Version': 1,
                'Workload': 'Exchange'
            })
        })
    return csv_path


@pytest.fixture
def sample_json_data():
    """Sample JSON data for compression testing."""
    return {
        'CreatedDateTime': '15/12/2025 9:30:00 AM',
        'UserPrincipalName': 'user1@example.com',
        'UserDisplayName': 'User One',
        'AppDisplayName': 'Microsoft Office 365',
        'IPAddress': '203.0.113.1',
        'City': 'Sydney',
        'Country': 'Australia',
        'Browser': 'Chrome 120.0.0.0',
        'OS': 'Windows 11',
        'Status': 'Success',
        'CorrelationId': 'abc-123-def-456-ghi-789',
        'ConditionalAccessStatus': 'success',
        'RiskLevelDuringSignIn': 'none',
        'RiskState': 'none'
    }


# ============================================================================
# Compression Module Tests
# ============================================================================

class TestCompressionModule:
    """Tests for the compression utility module."""

    def test_compress_json_string(self, sample_json_data):
        """compress_json should accept JSON string and return bytes."""
        if compress_json is None:
            pytest.skip("compression module not yet implemented")

        json_str = json.dumps(sample_json_data)
        result = compress_json(json_str)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_compress_json_dict(self, sample_json_data):
        """compress_json should accept dict and return bytes."""
        if compress_json is None:
            pytest.skip("compression module not yet implemented")

        result = compress_json(sample_json_data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_decompress_returns_string(self, sample_json_data):
        """decompress_json should return JSON string."""
        if compress_json is None or decompress_json is None:
            pytest.skip("compression module not yet implemented")

        compressed = compress_json(sample_json_data)
        result = decompress_json(compressed)

        assert isinstance(result, str)

    def test_roundtrip_preserves_data(self, sample_json_data):
        """Compress then decompress should preserve original data."""
        if compress_json is None or decompress_json is None:
            pytest.skip("compression module not yet implemented")

        original = json.dumps(sample_json_data)
        compressed = compress_json(original)
        decompressed = decompress_json(compressed)

        assert decompressed == original
        assert json.loads(decompressed) == sample_json_data

    def test_compression_reduces_size(self, sample_json_data):
        """Compressed data should be smaller than original."""
        if compress_json is None:
            pytest.skip("compression module not yet implemented")

        original = json.dumps(sample_json_data)
        compressed = compress_json(original)

        # JSON data typically compresses well (50%+ reduction)
        assert len(compressed) < len(original.encode('utf-8'))

    def test_is_compressed_detects_zlib(self, sample_json_data):
        """is_compressed should detect zlib compressed data."""
        if compress_json is None or is_compressed is None:
            pytest.skip("compression module not yet implemented")

        compressed = compress_json(sample_json_data)

        assert is_compressed(compressed) is True

    def test_is_compressed_returns_false_for_string(self):
        """is_compressed should return False for plain string."""
        if is_compressed is None:
            pytest.skip("compression module not yet implemented")

        assert is_compressed("not compressed") is False
        assert is_compressed('{"json": "string"}') is False

    def test_decompress_handles_uncompressed_string(self):
        """decompress_json should pass through uncompressed strings (backwards compat)."""
        if decompress_json is None:
            pytest.skip("compression module not yet implemented")

        plain_string = '{"key": "value"}'
        result = decompress_json(plain_string)

        assert result == plain_string

    def test_compression_level_is_6(self):
        """Default compression level should be 6 (balanced)."""
        if COMPRESSION_LEVEL is None:
            pytest.skip("compression module not yet implemented")

        assert COMPRESSION_LEVEL == 6


# ============================================================================
# Compressed Import Tests
# ============================================================================

class TestCompressedImport:
    """Tests for compression during log import."""

    def test_signin_raw_record_is_blob(self, importer, db, sample_signin_csv):
        """Sign-in logs raw_record should be stored as compressed BLOB."""
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        # Query raw bytes without Row factory conversion
        conn.row_factory = None
        cursor = conn.execute("SELECT raw_record FROM sign_in_logs LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        raw_record = row[0]

        # Should be bytes, not string
        assert isinstance(raw_record, bytes), f"Expected bytes, got {type(raw_record)}"

        # Should be zlib compressed (starts with x\x9c for level 6)
        if is_compressed is not None:
            assert is_compressed(raw_record), "raw_record should be zlib compressed"

    def test_ual_audit_data_is_blob(self, importer, db, sample_ual_csv):
        """UAL audit_data should be stored as compressed BLOB."""
        importer.import_ual(sample_ual_csv)

        conn = db.connect()
        conn.row_factory = None
        cursor = conn.execute("SELECT audit_data FROM unified_audit_log LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        audit_data = row[0]

        assert isinstance(audit_data, bytes), f"Expected bytes, got {type(audit_data)}"

        if is_compressed is not None:
            assert is_compressed(audit_data), "audit_data should be zlib compressed"

    def test_ual_raw_record_is_blob(self, importer, db, sample_ual_csv):
        """UAL raw_record should also be stored as compressed BLOB."""
        importer.import_ual(sample_ual_csv)

        conn = db.connect()
        conn.row_factory = None
        cursor = conn.execute("SELECT raw_record FROM unified_audit_log LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        raw_record = row[0]

        assert isinstance(raw_record, bytes), f"Expected bytes, got {type(raw_record)}"

    def test_compressed_data_smaller_than_original(self, importer, db, sample_signin_csv):
        """Compressed raw_record should be smaller than uncompressed JSON."""
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        conn.row_factory = None
        cursor = conn.execute("SELECT raw_record FROM sign_in_logs LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        compressed_size = len(row[0])

        # Read original CSV to get approximate uncompressed size
        with open(sample_signin_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row_data in reader:
                original_json = json.dumps(row_data)
                original_size = len(original_json.encode('utf-8'))
                break

        # Compressed should be smaller
        assert compressed_size < original_size, \
            f"Compressed ({compressed_size}) should be smaller than original ({original_size})"


# ============================================================================
# Compressed Query Tests
# ============================================================================

class TestCompressedQuery:
    """Tests for transparent decompression during queries."""

    def test_activity_by_ip_decompresses_raw_record(self, importer, query, sample_signin_csv):
        """activity_by_ip should return decompressed raw_record."""
        importer.import_sign_in_logs(sample_signin_csv)

        results = query.activity_by_ip("203.0.113.1")

        assert len(results) > 0

        raw_record = results[0].get('raw_record')
        assert raw_record is not None

        # Should be a valid JSON string, not bytes
        assert isinstance(raw_record, str), f"Expected str, got {type(raw_record)}"

        # Should be valid JSON
        parsed = json.loads(raw_record)
        assert 'UserPrincipalName' in parsed

    def test_activity_by_user_decompresses_raw_record(self, importer, query, sample_signin_csv):
        """activity_by_user should return decompressed raw_record."""
        importer.import_sign_in_logs(sample_signin_csv)

        results = query.activity_by_user("user1@example.com")

        assert len(results) > 0

        raw_record = results[0].get('raw_record')
        assert isinstance(raw_record, str)

        parsed = json.loads(raw_record)
        assert parsed['UserPrincipalName'] == 'user1@example.com'

    def test_suspicious_operations_decompresses_audit_data(self, importer, query, sample_ual_csv):
        """suspicious_operations should return decompressed audit_data."""
        importer.import_ual(sample_ual_csv)

        results = query.suspicious_operations()

        assert len(results) > 0

        audit_data = results[0].get('audit_data')
        assert audit_data is not None

        # Should be a valid JSON string
        assert isinstance(audit_data, str), f"Expected str, got {type(audit_data)}"

        parsed = json.loads(audit_data)
        assert 'ForwardTo' in parsed

    def test_execute_returns_decompressed_data(self, importer, query, sample_signin_csv):
        """execute() raw SQL should return decompressed fields."""
        importer.import_sign_in_logs(sample_signin_csv)

        results = query.execute("SELECT raw_record FROM sign_in_logs")

        assert len(results) > 0

        raw_record = results[0]['raw_record']
        assert isinstance(raw_record, str)

        # Should be valid JSON
        json.loads(raw_record)

    def test_backwards_compat_with_text_data(self, db, query):
        """Query layer should handle uncompressed TEXT data (backwards compat)."""
        # Manually insert uncompressed data (simulating old database)
        conn = db.connect()
        plain_json = '{"UserPrincipalName": "old@example.com", "test": "uncompressed"}'

        conn.execute("""
            INSERT INTO sign_in_logs
            (timestamp, user_principal_name, ip_address, raw_record, imported_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            '2025-12-15T09:00:00',
            'old@example.com',
            '1.2.3.4',
            plain_json,  # Uncompressed TEXT
            '2025-12-15T09:00:00'
        ))
        conn.commit()
        conn.close()

        # Query should still work and return the string
        results = query.activity_by_ip("1.2.3.4")

        assert len(results) > 0
        raw_record = results[0].get('raw_record')

        # Should handle uncompressed data gracefully
        assert raw_record is not None
        assert 'old@example.com' in raw_record


# ============================================================================
# Integration Tests
# ============================================================================

class TestCompressionIntegration:
    """End-to-end integration tests for compression."""

    def test_full_import_query_cycle(self, importer, query, sample_signin_csv, sample_ual_csv):
        """Full cycle: import compressed -> query decompressed."""
        # Import both log types
        importer.import_sign_in_logs(sample_signin_csv)
        importer.import_ual(sample_ual_csv)

        # Query sign-in logs
        signin_results = query.activity_by_ip("203.0.113.1")
        assert len(signin_results) > 0
        assert isinstance(signin_results[0]['raw_record'], str)

        # Query UAL
        ual_results = query.suspicious_operations()
        assert len(ual_results) > 0
        assert isinstance(ual_results[0]['audit_data'], str)

    def test_existing_tests_still_pass(self, importer, db, sample_signin_csv):
        """Verify existing test patterns still work with compression."""
        # This mirrors TestImportSignInLogs.test_import_stores_raw_record
        importer.import_sign_in_logs(sample_signin_csv)

        conn = db.connect()
        cursor = conn.execute("SELECT raw_record FROM sign_in_logs LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        # The key difference: with Row factory, we expect string back
        # (the query layer should decompress transparently)
        assert row['raw_record'] is not None
