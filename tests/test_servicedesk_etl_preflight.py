"""
Test Suite for ServiceDesk ETL Pre-Flight Checks

TDD Test Suite - Created Before Implementation
Tests verify pre-flight checks detect environmental issues before ETL execution.
"""

import pytest
import os
import sys
import tempfile
import shutil
from unittest import mock
import psycopg2

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPreFlightChecks:
    """Test pre-flight environmental checks"""

    def test_disk_space_check_passes_with_sufficient_space(self):
        """Verify disk space check passes when ≥2x SQLite size available"""
        from claude.tools.sre.servicedesk_etl_preflight import check_disk_space

        # Create test database (1MB)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * 1024 * 1024)  # 1MB
            test_db = f.name

        try:
            # Mock disk usage to return 5GB free (>2x requirement)
            with mock.patch('shutil.disk_usage') as mock_disk:
                mock_disk.return_value = (1000, 100, 5 * 1024**3)  # 5GB free

                result = check_disk_space(test_db)

                assert result['status'] == 'PASS'
                assert 'GB available' in result['details']
                assert result['required_gb'] == 2.0 / 1024  # 2MB in GB
        finally:
            os.unlink(test_db)

    def test_disk_space_check_fails_with_insufficient_space(self):
        """Verify disk space check fails when <2x SQLite size available"""
        from claude.tools.sre.servicedesk_etl_preflight import check_disk_space

        # Create test database (1GB)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.seek(1024**3 - 1)  # 1GB
            f.write(b'\0')
            test_db = f.name

        try:
            # Mock disk usage to return 1GB free (<2x requirement)
            with mock.patch('shutil.disk_usage') as mock_disk:
                mock_disk.return_value = (1000, 100, 1 * 1024**3)  # 1GB free

                result = check_disk_space(test_db)

                assert result['status'] == 'FAIL'
                assert 'insufficient' in result['details'].lower()
        finally:
            os.unlink(test_db)

    def test_postgres_connection_check_passes_with_valid_connection(self):
        """Verify PostgreSQL check passes with working connection"""
        from claude.tools.sre.servicedesk_etl_preflight import check_postgres_connection

        # Mock successful connection
        with mock.patch('psycopg2.connect') as mock_connect:
            mock_conn = mock.MagicMock()
            mock_conn.server_version = 150000  # PostgreSQL 15
            mock_connect.return_value = mock_conn

            result = check_postgres_connection(
                host='localhost',
                port=5432,
                dbname='servicedesk',
                user='test',
                password='test'
            )

            assert result['status'] == 'PASS'
            assert 'localhost:5432' in result['details']

    def test_postgres_connection_check_fails_with_invalid_connection(self):
        """Verify PostgreSQL check fails with connection error"""
        from claude.tools.sre.servicedesk_etl_preflight import check_postgres_connection

        # Mock connection failure
        with mock.patch('psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("Connection refused")

            result = check_postgres_connection(
                host='localhost',
                port=5432,
                dbname='servicedesk',
                user='test',
                password='test'
            )

            assert result['status'] == 'FAIL'
            assert 'connection' in result['details'].lower()

    def test_backup_tools_check_passes_with_pg_dump_installed(self):
        """Verify backup tools check passes when pg_dump is available"""
        from claude.tools.sre.servicedesk_etl_preflight import check_backup_tools

        # Mock pg_dump exists
        with mock.patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/pg_dump'

            result = check_backup_tools()

            assert result['status'] == 'PASS'
            assert 'pg_dump' in result['details']

    def test_backup_tools_check_warns_when_pg_dump_missing(self):
        """Verify backup tools check warns when pg_dump is missing"""
        from claude.tools.sre.servicedesk_etl_preflight import check_backup_tools

        # Mock pg_dump doesn't exist
        with mock.patch('shutil.which') as mock_which:
            mock_which.return_value = None

            result = check_backup_tools()

            assert result['status'] == 'WARNING'
            assert 'not found' in result['details'].lower()

    def test_memory_check_passes_with_sufficient_memory(self):
        """Verify memory check passes with ≥4GB available"""
        from claude.tools.sre.servicedesk_etl_preflight import check_memory

        # Mock 8GB available
        with mock.patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = mock.MagicMock(
                available=8 * 1024**3,  # 8GB
                percent=40
            )

            result = check_memory()

            assert result['status'] == 'PASS'
            assert '8' in result['details']  # Shows GB available

    def test_memory_check_warns_with_low_memory(self):
        """Verify memory check warns with <4GB available"""
        from claude.tools.sre.servicedesk_etl_preflight import check_memory

        # Mock 2GB available
        with mock.patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = mock.MagicMock(
                available=2 * 1024**3,  # 2GB
                percent=75
            )

            result = check_memory()

            assert result['status'] == 'WARNING'
            assert '2' in result['details']

    def test_dependencies_check_passes_with_all_installed(self):
        """Verify dependencies check passes with all required packages"""
        from claude.tools.sre.servicedesk_etl_preflight import check_dependencies

        required = ['pandas', 'psycopg2', 'psutil']

        # Mock all packages installed
        with mock.patch('importlib.import_module') as mock_import:
            mock_import.return_value = mock.MagicMock()

            result = check_dependencies(required)

            assert result['status'] == 'PASS'
            assert all(pkg in result['details'] for pkg in required)

    def test_dependencies_check_fails_with_missing_package(self):
        """Verify dependencies check fails with missing package"""
        from claude.tools.sre.servicedesk_etl_preflight import check_dependencies

        required = ['pandas', 'psycopg2', 'missing_package']

        # Mock missing package
        def mock_import_side_effect(name):
            if name == 'missing_package':
                raise ImportError(f"No module named '{name}'")
            return mock.MagicMock()

        with mock.patch('importlib.import_module') as mock_import:
            mock_import.side_effect = mock_import_side_effect

            result = check_dependencies(required)

            assert result['status'] == 'FAIL'
            assert 'missing_package' in result['details']

    def test_run_all_preflight_checks_returns_overall_status(self):
        """Verify run_all_preflight_checks aggregates all checks"""
        from claude.tools.sre.servicedesk_etl_preflight import run_all_preflight_checks

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * 1024)  # 1KB
            test_db = f.name

        try:
            # Mock all checks to pass
            with mock.patch('shutil.disk_usage') as mock_disk, \
                 mock.patch('psutil.virtual_memory') as mock_mem, \
                 mock.patch('shutil.which') as mock_which, \
                 mock.patch('psycopg2.connect') as mock_connect:

                mock_disk.return_value = (1000, 100, 10 * 1024**3)  # 10GB
                mock_mem.return_value = mock.MagicMock(available=8 * 1024**3, percent=40)
                mock_which.return_value = '/usr/bin/pg_dump'
                mock_connect.return_value = mock.MagicMock(server_version=150000)

                result = run_all_preflight_checks(test_db)

                assert result['preflight_status'] == 'PASS'
                assert len(result['checks']) >= 4  # disk, postgres, backup, memory
                assert all(check['status'] in ['PASS', 'WARNING'] for check in result['checks'])
        finally:
            os.unlink(test_db)

    def test_run_all_preflight_checks_fails_with_critical_error(self):
        """Verify overall status is FAIL when any CRITICAL check fails"""
        from claude.tools.sre.servicedesk_etl_preflight import run_all_preflight_checks

        # Create 1GB database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.seek(1024**3 - 1)  # 1GB
            f.write(b'\0')
            test_db = f.name

        try:
            # Mock disk check to fail (insufficient space)
            # DB is 1GB, needs 2GB, but only 1GB available
            with mock.patch('shutil.disk_usage') as mock_disk, \
                 mock.patch('psutil.virtual_memory') as mock_mem, \
                 mock.patch('shutil.which') as mock_which, \
                 mock.patch('psycopg2.connect') as mock_connect:

                mock_disk.return_value = (1000, 100, 1 * 1024**3)  # 1GB available (need 2GB)
                mock_mem.return_value = mock.MagicMock(available=8 * 1024**3, percent=40)
                mock_which.return_value = '/usr/bin/pg_dump'
                mock_connect.return_value = mock.MagicMock(server_version=150000)

                result = run_all_preflight_checks(test_db)

                assert result['preflight_status'] == 'FAIL'
                assert any(check['status'] == 'FAIL' for check in result['checks'])
        finally:
            os.unlink(test_db)


class TestPreFlightCLI:
    """Test pre-flight CLI interface"""

    def test_cli_outputs_json_format(self):
        """Verify CLI outputs valid JSON"""
        from claude.tools.sre.servicedesk_etl_preflight import main
        import json
        import sys
        from io import StringIO

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * 1024)
            test_db = f.name

        try:
            # Mock sys.argv and stdout
            with mock.patch('sys.argv', ['preflight.py', '--source', test_db]), \
                 mock.patch('sys.stdout', new=StringIO()) as mock_stdout, \
                 mock.patch('shutil.disk_usage') as mock_disk, \
                 mock.patch('psutil.virtual_memory') as mock_mem, \
                 mock.patch('shutil.which') as mock_which, \
                 mock.patch('psycopg2.connect') as mock_connect:

                mock_disk.return_value = (1000, 100, 10 * 1024**3)
                mock_mem.return_value = mock.MagicMock(available=8 * 1024**3, percent=40)
                mock_which.return_value = '/usr/bin/pg_dump'
                mock_connect.return_value = mock.MagicMock(server_version=150000)

                # main() calls sys.exit(), catch it
                with pytest.raises(SystemExit) as exc:
                    main()

                # Should exit with 0 (success)
                assert exc.value.code == 0

                output = mock_stdout.getvalue()
                result = json.loads(output)  # Should not raise

                assert 'preflight_status' in result
                assert 'checks' in result
        finally:
            os.unlink(test_db)

    def test_cli_exits_with_error_code_on_failure(self):
        """Verify CLI exits with code 1 on pre-flight failure"""
        from claude.tools.sre.servicedesk_etl_preflight import main

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * 1024)
            test_db = f.name

        try:
            with mock.patch('sys.argv', ['preflight.py', '--source', test_db]), \
                 mock.patch('shutil.disk_usage') as mock_disk:

                mock_disk.return_value = (1000, 100, 100 * 1024**2)  # Insufficient

                with pytest.raises(SystemExit) as exc:
                    main()

                assert exc.value.code == 1
        finally:
            os.unlink(test_db)


class TestPreFlightIntegration:
    """Integration tests for pre-flight checks"""

    def test_preflight_detects_missing_source_database(self):
        """Verify pre-flight fails gracefully when source DB doesn't exist"""
        from claude.tools.sre.servicedesk_etl_preflight import run_all_preflight_checks

        with pytest.raises(FileNotFoundError) as exc:
            run_all_preflight_checks('/nonexistent/database.db')

        assert 'not found' in str(exc.value).lower()

    def test_preflight_checks_run_in_under_5_seconds(self):
        """Verify pre-flight checks complete quickly (<5s)"""
        import time
        from claude.tools.sre.servicedesk_etl_preflight import run_all_preflight_checks

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'0' * 1024)
            test_db = f.name

        try:
            with mock.patch('psycopg2.connect') as mock_connect:
                mock_connect.return_value = mock.MagicMock(server_version=150000)

                start = time.time()
                run_all_preflight_checks(test_db)
                elapsed = time.time() - start

                assert elapsed < 5.0, f"Pre-flight checks took {elapsed}s (expected <5s)"
        finally:
            os.unlink(test_db)
