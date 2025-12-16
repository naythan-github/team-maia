#!/usr/bin/env python3
"""
ServiceDesk ETL Backup Strategy

Provides backup and restore functionality for ETL pipeline safety.
Part of Phase 0 - Prerequisites for V2 SRE-Hardened ETL Pipeline.

Features:
    - SQLite database backups with timestamped copies
    - PostgreSQL schema backups using pg_dump
    - Backup verification with checksums
    - Restore functionality
    - Retention policy management

Usage:
    # Backup SQLite database
    python3 servicedesk_etl_backup.py backup --source servicedesk_tickets.db --output backups/

    # Restore from backup
    python3 servicedesk_etl_backup.py restore --backup backups/servicedesk_tickets.db.20251019_143022 --target servicedesk_tickets.db

    # Verify backup
    python3 servicedesk_etl_backup.py verify --source servicedesk_tickets.db --backup backups/servicedesk_tickets.db.20251019_143022

    # Cleanup old backups
    python3 servicedesk_etl_backup.py cleanup --backup-dir backups/ --retention-days 7
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any


class BackupError(Exception):
    """Raised when backup operation fails"""
    pass


def backup_sqlite(source_db: str, backup_dir: str) -> str:
    """
    Create timestamped backup of SQLite database.

    Args:
        source_db: Path to source SQLite database
        backup_dir: Directory to store backup

    Returns:
        Path to created backup file

    Raises:
        FileNotFoundError: If source database doesn't exist
        BackupError: If backup creation fails
    """
    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Source database not found: {source_db}")

    # Create backup directory if needed
    os.makedirs(backup_dir, exist_ok=True)

    # Generate timestamped backup filename
    db_name = os.path.basename(source_db)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{db_name}.{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        # Copy database file
        shutil.copy2(source_db, backup_path)
        return backup_path

    except Exception as e:
        raise BackupError(f"Failed to create backup: {e}")


def backup_postgres(
    schema: str,
    backup_dir: str,
    host: str = 'localhost',
    port: int = 5432,
    dbname: str = 'servicedesk',
    user: str = None,
    password: str = None
) -> str:
    """
    Create PostgreSQL schema backup using pg_dump.

    Args:
        schema: PostgreSQL schema name
        backup_dir: Directory to store backup
        host: PostgreSQL host
        port: PostgreSQL port
        dbname: Database name
        user: Username (default: from env POSTGRES_USER)
        password: Password (default: from env POSTGRES_PASSWORD)

    Returns:
        Path to created backup file

    Raises:
        BackupError: If pg_dump fails
    """
    # Create backup directory if needed
    os.makedirs(backup_dir, exist_ok=True)

    # Generate timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{schema}_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, backup_name)

    # Get credentials from environment if not provided
    user = user or os.getenv('POSTGRES_USER', 'postgres')
    password = password or os.getenv('POSTGRES_PASSWORD', '')

    # Build pg_dump command
    cmd = [
        'pg_dump',
        '-h', host,
        '-p', str(port),
        '-U', user,
        '-d', dbname,
        '--schema', schema,
        '-f', backup_path
    ]

    # Set password in environment
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise BackupError(f"pg_dump failed: {result.stderr}")

        return backup_path

    except subprocess.TimeoutExpired:
        raise BackupError("pg_dump timeout (>5 minutes)")
    except Exception as e:
        raise BackupError(f"Failed to create PostgreSQL backup: {e}")


def calculate_checksum(file_path: str) -> str:
    """
    Calculate MD5 checksum of file.

    Args:
        file_path: Path to file

    Returns:
        MD5 checksum hex string
    """
    md5 = hashlib.md5(usedforsecurity=False)  # B324: Non-cryptographic checksum
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def verify_backup(source_db: str, backup_db: str) -> Dict[str, Any]:
    """
    Verify backup matches source database.

    Args:
        source_db: Path to source database
        backup_db: Path to backup database

    Returns:
        Verification result dict with verified, size_match, checksums
    """
    # Check sizes
    source_size = os.path.getsize(source_db)
    backup_size = os.path.getsize(backup_db)
    size_match = source_size == backup_size

    # Calculate checksums
    source_checksum = calculate_checksum(source_db)
    backup_checksum = calculate_checksum(backup_db)
    checksum_match = source_checksum == backup_checksum

    verified = size_match and checksum_match

    return {
        'verified': verified,
        'size_match': size_match,
        'checksum_match': checksum_match,
        'source_size': source_size,
        'backup_size': backup_size,
        'source_checksum': source_checksum,
        'backup_checksum': backup_checksum
    }


def restore_sqlite(backup_db: str, target_db: str):
    """
    Restore SQLite database from backup.

    Args:
        backup_db: Path to backup database
        target_db: Path to target database (will be replaced)

    Raises:
        FileNotFoundError: If backup doesn't exist
        BackupError: If restore fails
    """
    if not os.path.exists(backup_db):
        raise FileNotFoundError(f"Backup not found: {backup_db}")

    try:
        # Copy backup to target
        shutil.copy2(backup_db, target_db)

    except Exception as e:
        raise BackupError(f"Failed to restore backup: {e}")


def restore_postgres(
    backup_path: str,
    host: str = 'localhost',
    port: int = 5432,
    dbname: str = 'servicedesk',
    user: str = None,
    password: str = None
):
    """
    Restore PostgreSQL schema from backup.

    Args:
        backup_path: Path to SQL backup file
        host: PostgreSQL host
        port: PostgreSQL port
        dbname: Database name
        user: Username (default: from env POSTGRES_USER)
        password: Password (default: from env POSTGRES_PASSWORD)

    Raises:
        FileNotFoundError: If backup doesn't exist
        BackupError: If psql fails
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    # Get credentials from environment if not provided
    user = user or os.getenv('POSTGRES_USER', 'postgres')
    password = password or os.getenv('POSTGRES_PASSWORD', '')

    # Build psql command
    cmd = [
        'psql',
        '-h', host,
        '-p', str(port),
        '-U', user,
        '-d', dbname,
        '-f', backup_path
    ]

    # Set password in environment
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise BackupError(f"psql failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise BackupError("psql timeout (>5 minutes)")
    except Exception as e:
        raise BackupError(f"Failed to restore PostgreSQL backup: {e}")


def cleanup_old_backups(backup_dir: str, retention_days: int = 7) -> List[str]:
    """
    Remove backups older than retention period.

    Args:
        backup_dir: Directory containing backups
        retention_days: Keep backups newer than this many days

    Returns:
        List of removed backup paths
    """
    if not os.path.exists(backup_dir):
        return []

    cutoff_time = datetime.now() - timedelta(days=retention_days)
    removed = []

    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)

        # Skip non-files
        if not os.path.isfile(file_path):
            continue

        # Skip non-backup files (must be .db or .sql file with timestamp pattern)
        if not (filename.endswith('.db') or filename.endswith('.sql')):
            continue

        # Must have timestamp pattern (YYYYMMDD_HHMMSS)
        import re
        if not re.search(r'\d{8}_\d{6}', filename):
            continue

        # Check file modification time
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

        if mtime < cutoff_time:
            os.unlink(file_path)
            removed.append(file_path)

    return removed


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ServiceDesk ETL Backup Strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    backup_parser.add_argument('--source', required=True, help='Source database path')
    backup_parser.add_argument('--output', required=True, help='Backup directory')
    backup_parser.add_argument('--type', choices=['sqlite', 'postgres'], default='sqlite', help='Database type')
    backup_parser.add_argument('--schema', help='PostgreSQL schema name (for postgres type)')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('--backup', required=True, help='Backup file path')
    restore_parser.add_argument('--target', required=True, help='Target database path')
    restore_parser.add_argument('--type', choices=['sqlite', 'postgres'], default='sqlite', help='Database type')

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify backup')
    verify_parser.add_argument('--source', required=True, help='Source database path')
    verify_parser.add_argument('--backup', required=True, help='Backup file path')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old backups')
    cleanup_parser.add_argument('--backup-dir', required=True, help='Backup directory')
    cleanup_parser.add_argument('--retention-days', type=int, default=7, help='Retention period in days (default: 7)')

    args = parser.parse_args()

    try:
        if args.command == 'backup':
            if args.type == 'sqlite':
                backup_path = backup_sqlite(args.source, args.output)
                print(json.dumps({
                    'status': 'success',
                    'backup_path': backup_path,
                    'timestamp': datetime.now().isoformat()
                }))
            else:  # postgres
                if not args.schema:
                    print("ERROR: --schema required for postgres backup", file=sys.stderr)
                    sys.exit(1)
                backup_path = backup_postgres(args.schema, args.output)
                print(json.dumps({
                    'status': 'success',
                    'backup_path': backup_path,
                    'timestamp': datetime.now().isoformat()
                }))

        elif args.command == 'restore':
            if args.type == 'sqlite':
                restore_sqlite(args.backup, args.target)
            else:  # postgres
                restore_postgres(args.backup)

            print(json.dumps({
                'status': 'success',
                'restored_to': args.target,
                'timestamp': datetime.now().isoformat()
            }))

        elif args.command == 'verify':
            result = verify_backup(args.source, args.backup)
            print(json.dumps(result, indent=2))

            if not result['verified']:
                sys.exit(1)

        elif args.command == 'cleanup':
            removed = cleanup_old_backups(args.backup_dir, args.retention_days)
            print(json.dumps({
                'status': 'success',
                'removed_count': len(removed),
                'removed_files': removed,
                'retention_days': args.retention_days
            }))

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except BackupError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
