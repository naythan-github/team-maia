"""
Test Suite for ServiceDesk ETL Backup Strategy

TDD Test Suite - Created Before Implementation
Tests verify backup and restore functionality for ETL pipeline safety.
"""

import pytest
import os
import sys
import tempfile
import shutil
import sqlite3
from unittest import mock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBackupCreation:
    """Test backup creation functionality"""

    def test_backup_sqlite_creates_timestamped_copy(self):
        """Verify SQLite backup creates timestamped copy"""
        from claude.tools.sre.servicedesk_etl_backup import backup_sqlite

        # Create source database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        backup_dir = tempfile.mkdtemp()

        try:
            backup_path = backup_sqlite(source_db, backup_dir)

            # Verify backup exists
            assert os.path.exists(backup_path)

            # Verify backup has timestamp in filename
            assert datetime.now().strftime('%Y%m%d') in backup_path

            # Verify backup content matches source
            with open(source_db, 'rb') as src, open(backup_path, 'rb') as bak:
                assert src.read() == bak.read()
        finally:
            os.unlink(source_db)
            shutil.rmtree(backup_dir)

    def test_backup_sqlite_fails_with_missing_source(self):
        """Verify backup fails gracefully when source doesn't exist"""
        from claude.tools.sre.servicedesk_etl_backup import backup_sqlite

        backup_dir = tempfile.mkdtemp()

        try:
            with pytest.raises(FileNotFoundError) as exc:
                backup_sqlite('/nonexistent/database.db', backup_dir)

            assert 'not found' in str(exc.value).lower()
        finally:
            shutil.rmtree(backup_dir)

    def test_backup_sqlite_creates_backup_dir_if_missing(self):
        """Verify backup creates target directory if it doesn't exist"""
        from claude.tools.sre.servicedesk_etl_backup import backup_sqlite

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        backup_dir = os.path.join(tempfile.gettempdir(), 'nonexistent_backup_dir')

        try:
            backup_path = backup_sqlite(source_db, backup_dir)

            # Verify backup directory was created
            assert os.path.exists(backup_dir)
            assert os.path.exists(backup_path)
        finally:
            os.unlink(source_db)
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

    def test_backup_postgres_calls_pg_dump(self):
        """Verify PostgreSQL backup calls pg_dump with correct arguments"""
        from claude.tools.sre.servicedesk_etl_backup import backup_postgres

        backup_dir = tempfile.mkdtemp()

        try:
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value = mock.MagicMock(returncode=0)

                backup_path = backup_postgres(
                    schema='servicedesk',
                    backup_dir=backup_dir,
                    host='localhost',
                    port=5432,
                    dbname='test_db'
                )

                # Verify pg_dump was called
                assert mock_run.called
                call_args = mock_run.call_args[0][0]
                assert 'pg_dump' in call_args
                assert '--schema' in call_args
                assert 'servicedesk' in call_args
                assert '-h' in call_args and 'localhost' in call_args

                # Verify backup path returned
                assert backup_path.endswith('.sql')
                assert 'servicedesk' in backup_path
        finally:
            shutil.rmtree(backup_dir)

    def test_backup_postgres_fails_when_pg_dump_errors(self):
        """Verify PostgreSQL backup raises error when pg_dump fails"""
        from claude.tools.sre.servicedesk_etl_backup import backup_postgres, BackupError

        backup_dir = tempfile.mkdtemp()

        try:
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value = mock.MagicMock(
                    returncode=1,
                    stderr='pg_dump: error: connection failed'
                )

                with pytest.raises(BackupError) as exc:
                    backup_postgres(
                        schema='servicedesk',
                        backup_dir=backup_dir
                    )

                assert 'pg_dump failed' in str(exc.value).lower()
        finally:
            shutil.rmtree(backup_dir)


class TestBackupVerification:
    """Test backup verification functionality"""

    def test_verify_backup_passes_with_valid_backup(self):
        """Verify backup verification passes with valid backup"""
        from claude.tools.sre.servicedesk_etl_backup import verify_backup

        # Create source and backup
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            backup_db = f.name

        try:
            result = verify_backup(source_db, backup_db)

            assert result['verified'] is True
            assert result['size_match'] is True
        finally:
            os.unlink(source_db)
            os.unlink(backup_db)

    def test_verify_backup_fails_with_size_mismatch(self):
        """Verify backup verification fails with different sizes"""
        from claude.tools.sre.servicedesk_etl_backup import verify_backup

        # Create source and backup with different sizes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'different size data here')
            backup_db = f.name

        try:
            result = verify_backup(source_db, backup_db)

            assert result['verified'] is False
            assert result['size_match'] is False
        finally:
            os.unlink(source_db)
            os.unlink(backup_db)

    def test_verify_backup_calculates_checksum(self):
        """Verify backup verification includes checksum"""
        from claude.tools.sre.servicedesk_etl_backup import verify_backup

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            backup_db = f.name

        try:
            result = verify_backup(source_db, backup_db)

            assert 'source_checksum' in result
            assert 'backup_checksum' in result
            assert result['source_checksum'] == result['backup_checksum']
        finally:
            os.unlink(source_db)
            os.unlink(backup_db)


class TestBackupRestore:
    """Test backup restore functionality"""

    def test_restore_sqlite_replaces_target(self):
        """Verify SQLite restore replaces target database"""
        from claude.tools.sre.servicedesk_etl_backup import restore_sqlite

        # Create backup
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'backup data')
            backup_db = f.name

        # Create target (will be replaced)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'old data')
            target_db = f.name

        try:
            restore_sqlite(backup_db, target_db)

            # Verify target has backup data
            with open(target_db, 'rb') as f:
                assert f.read() == b'backup data'
        finally:
            os.unlink(backup_db)
            os.unlink(target_db)

    def test_restore_sqlite_creates_target_if_missing(self):
        """Verify restore creates target file if it doesn't exist"""
        from claude.tools.sre.servicedesk_etl_backup import restore_sqlite

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'backup data')
            backup_db = f.name

        target_db = os.path.join(tempfile.gettempdir(), 'restored.db')

        try:
            restore_sqlite(backup_db, target_db)

            assert os.path.exists(target_db)
            with open(target_db, 'rb') as f:
                assert f.read() == b'backup data'
        finally:
            os.unlink(backup_db)
            if os.path.exists(target_db):
                os.unlink(target_db)

    def test_restore_postgres_calls_psql(self):
        """Verify PostgreSQL restore calls psql with correct arguments"""
        from claude.tools.sre.servicedesk_etl_backup import restore_postgres

        with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as f:
            f.write(b'CREATE TABLE test;')
            backup_sql = f.name

        try:
            with mock.patch('subprocess.run') as mock_run:
                mock_run.return_value = mock.MagicMock(returncode=0)

                restore_postgres(
                    backup_path=backup_sql,
                    host='localhost',
                    port=5432,
                    dbname='test_db'
                )

                # Verify psql was called
                assert mock_run.called
                call_args = mock_run.call_args[0][0]
                assert 'psql' in call_args
                assert '-h' in call_args and 'localhost' in call_args
        finally:
            os.unlink(backup_sql)


class TestBackupRetention:
    """Test backup retention policy"""

    def test_cleanup_old_backups_removes_expired(self):
        """Verify cleanup removes backups older than retention period"""
        from claude.tools.sre.servicedesk_etl_backup import cleanup_old_backups

        backup_dir = tempfile.mkdtemp()

        try:
            # Create old backup (8 days ago)
            old_backup = os.path.join(backup_dir, 'servicedesk_20251010_120000.db')
            with open(old_backup, 'w') as f:
                f.write('old backup')

            # Create recent backup (1 day ago)
            recent_backup = os.path.join(backup_dir, datetime.now().strftime('servicedesk_%Y%m%d_%H%M%S.db'))
            with open(recent_backup, 'w') as f:
                f.write('recent backup')

            # Mock file timestamps
            old_time = (datetime.now() - timedelta(days=8)).timestamp()
            os.utime(old_backup, (old_time, old_time))

            # Cleanup with 7-day retention
            removed = cleanup_old_backups(backup_dir, retention_days=7)

            # Verify old backup removed, recent kept
            assert not os.path.exists(old_backup)
            assert os.path.exists(recent_backup)
            assert len(removed) == 1
        finally:
            shutil.rmtree(backup_dir)

    def test_cleanup_old_backups_preserves_recent(self):
        """Verify cleanup preserves backups within retention period"""
        from claude.tools.sre.servicedesk_etl_backup import cleanup_old_backups

        backup_dir = tempfile.mkdtemp()

        try:
            # Create recent backups
            backups = []
            for i in range(3):
                backup = os.path.join(backup_dir, f'servicedesk_2025101{i}_120000.db')
                with open(backup, 'w') as f:
                    f.write(f'backup {i}')
                backups.append(backup)

            removed = cleanup_old_backups(backup_dir, retention_days=30)

            # All backups should be preserved
            assert len(removed) == 0
            for backup in backups:
                assert os.path.exists(backup)
        finally:
            shutil.rmtree(backup_dir)


class TestBackupCLI:
    """Test backup CLI interface"""

    def test_cli_backup_command_creates_backup(self):
        """Verify CLI backup command creates backup"""
        from claude.tools.sre.servicedesk_etl_backup import main

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        backup_dir = tempfile.mkdtemp()

        try:
            with mock.patch('sys.argv', ['backup.py', 'backup', '--source', source_db, '--output', backup_dir]):
                with pytest.raises(SystemExit) as exc:
                    main()

                assert exc.value.code == 0

            # Verify backup was created (format: filename.db.TIMESTAMP)
            backups = [f for f in os.listdir(backup_dir) if '.db.' in f]
            assert len(backups) >= 1  # At least one backup created
        finally:
            os.unlink(source_db)
            shutil.rmtree(backup_dir)

    def test_cli_restore_command_restores_backup(self):
        """Verify CLI restore command restores from backup"""
        from claude.tools.sre.servicedesk_etl_backup import main

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'backup data')
            backup_db = f.name

        target_db = os.path.join(tempfile.gettempdir(), 'restored.db')

        try:
            with mock.patch('sys.argv', ['backup.py', 'restore', '--backup', backup_db, '--target', target_db]):
                with pytest.raises(SystemExit) as exc:
                    main()

                assert exc.value.code == 0

            # Verify restore succeeded
            assert os.path.exists(target_db)
            with open(target_db, 'rb') as f:
                assert f.read() == b'backup data'
        finally:
            os.unlink(backup_db)
            if os.path.exists(target_db):
                os.unlink(target_db)

    def test_cli_verify_command_checks_backup(self):
        """Verify CLI verify command validates backup"""
        from claude.tools.sre.servicedesk_etl_backup import main
        import json
        from io import StringIO

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            source_db = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'test data')
            backup_db = f.name

        try:
            with mock.patch('sys.argv', ['backup.py', 'verify', '--source', source_db, '--backup', backup_db]), \
                 mock.patch('sys.stdout', new=StringIO()) as mock_stdout:

                with pytest.raises(SystemExit) as exc:
                    main()

                assert exc.value.code == 0

                output = mock_stdout.getvalue()
                result = json.loads(output)
                assert result['verified'] is True
        finally:
            os.unlink(source_db)
            os.unlink(backup_db)


class TestBackupIntegration:
    """Integration tests for backup strategy"""

    def test_backup_restore_roundtrip_preserves_data(self):
        """Verify backup and restore preserves SQLite data"""
        from claude.tools.sre.servicedesk_etl_backup import backup_sqlite, restore_sqlite

        # Create source database with table
        source_db = os.path.join(tempfile.gettempdir(), 'source.db')
        conn = sqlite3.connect(source_db)
        conn.execute('CREATE TABLE test (id INTEGER, value TEXT)')
        conn.execute("INSERT INTO test VALUES (1, 'test data')")
        conn.commit()
        conn.close()

        backup_dir = tempfile.mkdtemp()
        restored_db = os.path.join(tempfile.gettempdir(), 'restored.db')

        try:
            # Backup
            backup_path = backup_sqlite(source_db, backup_dir)

            # Restore
            restore_sqlite(backup_path, restored_db)

            # Verify data preserved
            conn = sqlite3.connect(restored_db)
            cursor = conn.execute('SELECT value FROM test WHERE id = 1')
            result = cursor.fetchone()[0]
            conn.close()

            assert result == 'test data'
        finally:
            os.unlink(source_db)
            shutil.rmtree(backup_dir)
            if os.path.exists(restored_db):
                os.unlink(restored_db)

    def test_backup_completes_in_under_5_seconds(self):
        """Verify backup operation is fast (<5s)"""
        import time
        from claude.tools.sre.servicedesk_etl_backup import backup_sqlite

        # Create 10MB database
        source_db = os.path.join(tempfile.gettempdir(), 'large.db')
        with open(source_db, 'wb') as f:
            f.write(b'0' * 10 * 1024 * 1024)

        backup_dir = tempfile.mkdtemp()

        try:
            start = time.time()
            backup_sqlite(source_db, backup_dir)
            elapsed = time.time() - start

            assert elapsed < 5.0, f"Backup took {elapsed}s (expected <5s)"
        finally:
            os.unlink(source_db)
            shutil.rmtree(backup_dir)
