"""
Phase 1.3: Status Code Lookup Tables - TDD Tests

Test Objective:
    Validate status code lookup functionality with automatic unknown code detection.

Key Features:
    1. Lookup known status codes from database
    2. Detect and alert on unknown status codes
    3. Add new codes to database with proper metadata
    4. Track Microsoft API schema changes
    5. Support multiple log types and field names

Expected Behavior:
    - Known codes: Return human-readable meaning + severity
    - Unknown codes: Log warning, return "UNKNOWN", optionally email SRE
    - Deprecated codes: Return meaning but flag as deprecated
    - Performance: Lookup should be <10ms (indexed)

Phase: PHASE_1_FOUNDATION (Phase 1.3 - Status Code Lookup Tables)
Status: In Progress (TDD Red Phase)
TDD Cycle: Red → Green → Refactor
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime


@pytest.mark.phase_1_3
class TestStatusCodeLookup:
    """Test status code lookup functionality."""

    def test_lookup_known_status_code(self):
        """
        Test that lookup returns correct meaning and severity for known codes.

        Given: status_code_reference populated with known codes
        When: lookup_status_code() called with known code
        Then: Return StatusCodeInfo with meaning, severity, deprecated=False
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager, StatusCodeInfo
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            # Create database with status code tables
            db = IRLogDatabase(case_id="TEST-STATUS-CODES", base_path=tmpdir)
            db.create()

            # Insert known status code
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO status_code_reference
                (log_type, field_name, code_value, meaning, severity, first_seen, last_validated, deprecated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'sign_in_logs',
                'status_error_code',
                '0',
                'Success - No error',
                'INFO',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                0
            ))
            conn.commit()
            conn.close()

            # Test lookup
            manager = StatusCodeManager(db.db_path)
            result = manager.lookup_status_code(
                log_type='sign_in_logs',
                field_name='status_error_code',
                code_value='0'
            )

            # Validate result
            assert isinstance(result, StatusCodeInfo), "Should return StatusCodeInfo object"
            assert result.code_value == '0', "Code value should match"
            assert result.meaning == 'Success - No error', "Meaning should match"
            assert result.severity == 'INFO', "Severity should match"
            assert result.is_known is True, "Code should be marked as known"
            assert result.deprecated is False, "Code should not be deprecated"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_lookup_unknown_status_code(self):
        """
        Test that lookup detects unknown codes and returns UNKNOWN status.

        Given: status_code_reference does NOT contain code
        When: lookup_status_code() called with unknown code
        Then: Return StatusCodeInfo with is_known=False, meaning='UNKNOWN'
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager, StatusCodeInfo
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-UNKNOWN-CODE", base_path=tmpdir)
            db.create()

            manager = StatusCodeManager(db.db_path)
            result = manager.lookup_status_code(
                log_type='sign_in_logs',
                field_name='status_error_code',
                code_value='99999'  # Unknown code
            )

            # Validate unknown code handling
            assert isinstance(result, StatusCodeInfo), "Should return StatusCodeInfo object"
            assert result.code_value == '99999', "Code value should match"
            assert result.is_known is False, "Code should be marked as unknown"
            assert result.meaning == 'UNKNOWN', "Meaning should be UNKNOWN"
            assert result.severity == 'WARNING', "Unknown codes should have WARNING severity"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_lookup_deprecated_status_code(self):
        """
        Test that lookup flags deprecated codes.

        Given: status_code_reference contains deprecated code (deprecated=1)
        When: lookup_status_code() called
        Then: Return StatusCodeInfo with deprecated=True
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager, StatusCodeInfo
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-DEPRECATED-CODE", base_path=tmpdir)
            db.create()

            # Insert deprecated status code
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO status_code_reference
                (log_type, field_name, code_value, meaning, severity, first_seen, last_validated, deprecated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'sign_in_logs',
                'status_error_code',
                '50001',
                'Legacy error code (use conditional_access_status instead)',
                'WARNING',
                '2020-01-01T00:00:00',
                datetime.now().isoformat(),
                1  # Deprecated
            ))
            conn.commit()
            conn.close()

            manager = StatusCodeManager(db.db_path)
            result = manager.lookup_status_code(
                log_type='sign_in_logs',
                field_name='status_error_code',
                code_value='50001'
            )

            # Validate deprecated code handling
            assert result.is_known is True, "Deprecated codes are still known"
            assert result.deprecated is True, "Should be flagged as deprecated"
            assert 'legacy' in result.meaning.lower() or 'deprecated' in result.meaning.lower(), \
                "Meaning should indicate deprecation"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_batch_lookup_status_codes(self):
        """
        Test batch lookup for performance optimization.

        Given: Multiple status codes need lookup
        When: lookup_batch() called with list of codes
        Then: Return dict of {code_value: StatusCodeInfo} in single DB query
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-BATCH-LOOKUP", base_path=tmpdir)
            db.create()

            # Insert multiple known codes
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            codes = [
                ('0', 'Success', 'INFO'),
                ('50126', 'Invalid username or password', 'WARNING'),
                ('50053', 'Account locked', 'CRITICAL'),
            ]
            for code_value, meaning, severity in codes:
                cursor.execute("""
                    INSERT INTO status_code_reference
                    (log_type, field_name, code_value, meaning, severity, first_seen, last_validated, deprecated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'sign_in_logs',
                    'status_error_code',
                    code_value,
                    meaning,
                    severity,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    0
                ))
            conn.commit()
            conn.close()

            # Test batch lookup
            manager = StatusCodeManager(db.db_path)
            results = manager.lookup_batch(
                log_type='sign_in_logs',
                field_name='status_error_code',
                code_values=['0', '50126', '50053', '99999']  # Last one unknown
            )

            # Validate results
            assert len(results) == 4, "Should return result for each code"
            assert results['0'].meaning == 'Success', "Code 0 should be Success"
            assert results['50126'].meaning == 'Invalid username or password', "Code 50126 should match"
            assert results['50053'].severity == 'CRITICAL', "Code 50053 should be CRITICAL"
            assert results['99999'].is_known is False, "Code 99999 should be unknown"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_1_3
class TestUnknownCodeDetection:
    """Test unknown code detection and alerting."""

    def test_detect_unknown_codes_in_dataset(self):
        """
        Test scanning a dataset for unknown status codes.

        Given: sign_in_logs table with mix of known/unknown codes
        When: scan_for_unknown_codes() called
        Then: Return list of unknown codes with counts
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager
        import tempfile
        import csv

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-UNKNOWN-DETECTION", base_path=tmpdir)
            db.create()

            # Populate status_code_reference with some known codes
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO status_code_reference
                (log_type, field_name, code_value, meaning, severity, first_seen, last_validated, deprecated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'sign_in_logs',
                'status_error_code',
                '0',
                'Success',
                'INFO',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                0
            ))

            # Insert test data with mix of known/unknown codes
            for i in range(50):
                cursor.execute("""
                    INSERT INTO sign_in_logs
                    (timestamp, user_principal_name, ip_address, status_error_code,
                     conditional_access_status, location_country, imported_at, raw_record)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f'2025-11-04T10:{i:02d}:00Z',
                    f'user{i}@test.com',
                    f'203.0.113.{i}',
                    '0' if i < 40 else '99999',  # 40 known, 10 unknown
                    'success',
                    'AU',
                    datetime.now().isoformat(),
                    '{}'
                ))

            conn.commit()
            conn.close()

            # Scan for unknown codes
            manager = StatusCodeManager(db.db_path)
            unknown_codes = manager.scan_for_unknown_codes(
                log_type='sign_in_logs',
                field_name='status_error_code'
            )

            # Validate results
            assert len(unknown_codes) == 1, "Should find 1 unknown code"
            assert unknown_codes[0]['code_value'] == '99999', "Unknown code should be 99999"
            assert unknown_codes[0]['count'] == 10, "Unknown code should appear 10 times"
            assert unknown_codes[0]['field_name'] == 'status_error_code', "Field name should match"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_add_unknown_code_to_reference(self):
        """
        Test adding newly discovered code to reference table.

        Given: Unknown code detected
        When: add_status_code() called
        Then: Code added to status_code_reference with proper metadata
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager
        import tempfile

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-ADD-CODE", base_path=tmpdir)
            db.create()

            manager = StatusCodeManager(db.db_path)

            # Add new status code
            manager.add_status_code(
                log_type='sign_in_logs',
                field_name='status_error_code',
                code_value='50126',
                meaning='Invalid username or password',
                severity='WARNING'
            )

            # Verify code was added
            result = manager.lookup_status_code(
                log_type='sign_in_logs',
                field_name='status_error_code',
                code_value='50126'
            )

            assert result.is_known is True, "Code should now be known"
            assert result.meaning == 'Invalid username or password', "Meaning should match"
            assert result.severity == 'WARNING', "Severity should match"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.phase_1_3
class TestStatusCodePerformance:
    """Test status code lookup performance."""

    def test_lookup_performance_with_large_dataset(self):
        """
        Test that lookups remain fast with large reference table.

        Given: status_code_reference with 100+ codes
        When: 1000 lookups performed
        Then: Average lookup time <10ms (indexed queries)
        """
        from claude.tools.m365_ir.log_database import IRLogDatabase
        from claude.tools.m365_ir.status_code_manager import StatusCodeManager
        import tempfile
        import time

        tmpdir = tempfile.mkdtemp()

        try:
            db = IRLogDatabase(case_id="TEST-PERFORMANCE", base_path=tmpdir)
            db.create()

            # Populate 100 status codes
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            for i in range(100):
                cursor.execute("""
                    INSERT INTO status_code_reference
                    (log_type, field_name, code_value, meaning, severity, first_seen, last_validated, deprecated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'sign_in_logs',
                    'status_error_code',
                    str(i),
                    f'Status code {i}',
                    'INFO',
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    0
                ))
            conn.commit()
            conn.close()

            # Benchmark lookups
            manager = StatusCodeManager(db.db_path)
            start_time = time.time()

            for i in range(1000):
                code = str(i % 100)
                result = manager.lookup_status_code(
                    log_type='sign_in_logs',
                    field_name='status_error_code',
                    code_value=code
                )

            duration = time.time() - start_time
            avg_lookup_time_ms = (duration / 1000) * 1000

            print(f"\n⏱️  Performance: 1000 lookups in {duration:.3f}s")
            print(f"   Average: {avg_lookup_time_ms:.2f}ms per lookup")

            # Validate performance
            assert avg_lookup_time_ms < 10, \
                f"Lookup performance too slow: {avg_lookup_time_ms:.2f}ms (target: <10ms)"

        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# Mark all tests as Phase 1.3
pytestmark = pytest.mark.phase_1_3
