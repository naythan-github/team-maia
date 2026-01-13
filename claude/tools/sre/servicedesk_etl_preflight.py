#!/usr/bin/env python3
"""
ServiceDesk ETL Pre-Flight Checks

Validates environment before ETL execution to prevent failures.
Part of Phase 0 - Prerequisites for V2 SRE-Hardened ETL Pipeline.

Usage:
    python3 servicedesk_etl_preflight.py --source servicedesk_tickets.db

Checks:
    1. Disk space (≥2x SQLite DB size)
    2. PostgreSQL connection
    3. Backup tools availability (pg_dump)
    4. Memory availability (≥4GB recommended)
    5. Python dependencies

Exit Codes:
    0 - All checks passed
    1 - One or more CRITICAL checks failed
    2 - Only WARNING checks failed
"""

import argparse
import json
import os
import shutil
import sys
import importlib
from typing import Dict, List, Any

# Optional dependencies - graceful degradation for importability
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None


def _check_preflight_deps():
    """Raise ImportError if required dependencies are missing."""
    missing = []
    if not PSUTIL_AVAILABLE:
        missing.append("psutil")
    if not PSYCOPG2_AVAILABLE:
        missing.append("psycopg2-binary")
    if missing:
        raise ImportError(f"Missing dependencies: {', '.join(missing)}. Install with: pip3 install {' '.join(missing)}")


def check_disk_space(source_db: str) -> Dict[str, Any]:
    """
    Check if sufficient disk space available.

    Requirement: ≥2x SQLite database size

    Args:
        source_db: Path to SQLite database

    Returns:
        Check result dict with status, details, required_gb, available_gb
    """
    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Source database not found: {source_db}")

    # Get database size
    db_size_bytes = os.path.getsize(source_db)
    db_size_gb = db_size_bytes / (1024**3)
    required_gb = db_size_gb * 2  # 2x database size

    # Get available disk space
    db_dir = os.path.dirname(os.path.abspath(source_db))
    disk_usage = shutil.disk_usage(db_dir)
    # Handle both named tuple and regular tuple (for mocking)
    available_bytes = disk_usage.free if hasattr(disk_usage, 'free') else disk_usage[2]
    available_gb = available_bytes / (1024**3)

    # Check threshold
    if available_gb >= required_gb:
        return {
            'name': 'disk_space',
            'status': 'PASS',
            'details': f'{available_gb:.2f}GB available, {required_gb:.2f}GB required',
            'required_gb': required_gb,
            'available_gb': available_gb
        }
    else:
        return {
            'name': 'disk_space',
            'status': 'FAIL',
            'details': f'Insufficient disk space: {available_gb:.2f}GB available, {required_gb:.2f}GB required',
            'required_gb': required_gb,
            'available_gb': available_gb
        }


def check_postgres_connection(
    host: str = 'localhost',
    port: int = 5432,
    dbname: str = 'servicedesk',
    user: str = None,
    password: str = None
) -> Dict[str, Any]:
    """
    Check PostgreSQL connection.

    Args:
        host: PostgreSQL host
        port: PostgreSQL port
        dbname: Database name
        user: Username (default: from env POSTGRES_USER)
        password: Password (default: from env POSTGRES_PASSWORD)

    Returns:
        Check result dict with status, details
    """
    # Get credentials from environment if not provided
    user = user or os.getenv('POSTGRES_USER', 'postgres')
    password = password or os.getenv('POSTGRES_PASSWORD', '')

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=5
        )

        version = conn.server_version
        version_str = f"{version // 10000}.{(version // 100) % 100}"

        conn.close()

        return {
            'name': 'postgres_connection',
            'status': 'PASS',
            'details': f'Connected to {host}:{port}, PostgreSQL {version_str}',
            'host': host,
            'port': port,
            'version': version_str
        }

    except psycopg2.OperationalError as e:
        return {
            'name': 'postgres_connection',
            'status': 'FAIL',
            'details': f'Connection failed: {str(e)}',
            'host': host,
            'port': port,
            'error': str(e)
        }


def check_backup_tools() -> Dict[str, Any]:
    """
    Check backup tools availability.

    Required: pg_dump (for PostgreSQL backups)

    Returns:
        Check result dict with status, details
    """
    pg_dump_path = shutil.which('pg_dump')

    if pg_dump_path:
        return {
            'name': 'backup_tools',
            'status': 'PASS',
            'details': f'pg_dump found at {pg_dump_path}',
            'pg_dump_path': pg_dump_path
        }
    else:
        return {
            'name': 'backup_tools',
            'status': 'WARNING',
            'details': 'pg_dump not found, PostgreSQL backups will fail',
            'pg_dump_path': None
        }


def check_memory(recommended_gb: float = 4.0) -> Dict[str, Any]:
    """
    Check available memory.

    Recommended: ≥4GB available

    Args:
        recommended_gb: Recommended memory in GB

    Returns:
        Check result dict with status, details, available_gb
    """
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)

    if available_gb >= recommended_gb:
        return {
            'name': 'memory',
            'status': 'PASS',
            'details': f'{available_gb:.2f}GB available, {recommended_gb:.1f}GB recommended',
            'available_gb': available_gb,
            'percent_used': mem.percent
        }
    else:
        return {
            'name': 'memory',
            'status': 'WARNING',
            'details': f'{available_gb:.2f}GB available, {recommended_gb:.1f}GB recommended (low memory may impact performance)',
            'available_gb': available_gb,
            'percent_used': mem.percent
        }


def check_dependencies(required: List[str] = None) -> Dict[str, Any]:
    """
    Check Python dependencies.

    Args:
        required: List of required package names

    Returns:
        Check result dict with status, details
    """
    if required is None:
        required = ['pandas', 'psycopg2', 'psutil', 'sqlite3']

    missing = []
    installed = []

    for package in required:
        try:
            # Special case for sqlite3 (built-in)
            if package == 'sqlite3':
                import sqlite3
            else:
                importlib.import_module(package)
            installed.append(package)
        except ImportError:
            missing.append(package)

    if not missing:
        return {
            'name': 'dependencies',
            'status': 'PASS',
            'details': f'All required packages installed: {", ".join(installed)}',
            'installed': installed,
            'missing': []
        }
    else:
        return {
            'name': 'dependencies',
            'status': 'FAIL',
            'details': f'Missing packages: {", ".join(missing)}. Run: pip3 install {" ".join(missing)}',
            'installed': installed,
            'missing': missing
        }


def run_all_preflight_checks(
    source_db: str,
    postgres_host: str = 'localhost',
    postgres_port: int = 5432,
    postgres_dbname: str = 'servicedesk',
    postgres_user: str = None,
    postgres_password: str = None
) -> Dict[str, Any]:
    """
    Run all pre-flight checks.

    Args:
        source_db: Path to SQLite database
        postgres_host: PostgreSQL host
        postgres_port: PostgreSQL port
        postgres_dbname: PostgreSQL database name
        postgres_user: PostgreSQL username
        postgres_password: PostgreSQL password

    Returns:
        Overall result dict with preflight_status and checks list
    """
    checks = []

    # Check 1: Disk space (CRITICAL)
    checks.append(check_disk_space(source_db))

    # Check 2: PostgreSQL connection (CRITICAL)
    checks.append(check_postgres_connection(
        host=postgres_host,
        port=postgres_port,
        dbname=postgres_dbname,
        user=postgres_user,
        password=postgres_password
    ))

    # Check 3: Backup tools (WARNING)
    checks.append(check_backup_tools())

    # Check 4: Memory (WARNING)
    checks.append(check_memory())

    # Check 5: Dependencies (CRITICAL)
    checks.append(check_dependencies())

    # Determine overall status
    has_failures = any(check['status'] == 'FAIL' for check in checks)
    has_warnings = any(check['status'] == 'WARNING' for check in checks)

    if has_failures:
        overall_status = 'FAIL'
    elif has_warnings:
        overall_status = 'WARNING'
    else:
        overall_status = 'PASS'

    return {
        'preflight_status': overall_status,
        'checks': checks,
        'summary': {
            'total_checks': len(checks),
            'passed': sum(1 for c in checks if c['status'] == 'PASS'),
            'warnings': sum(1 for c in checks if c['status'] == 'WARNING'),
            'failed': sum(1 for c in checks if c['status'] == 'FAIL')
        }
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ServiceDesk ETL Pre-Flight Checks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all pre-flight checks
  python3 servicedesk_etl_preflight.py --source servicedesk_tickets.db

  # Custom PostgreSQL connection
  python3 servicedesk_etl_preflight.py --source servicedesk_tickets.db \\
    --postgres-host db.example.com --postgres-port 5433

Exit Codes:
  0 - All checks passed
  1 - One or more CRITICAL checks failed
  2 - Only WARNING checks failed
        """
    )

    parser.add_argument(
        '--source',
        required=True,
        help='Path to SQLite database'
    )

    parser.add_argument(
        '--postgres-host',
        default='localhost',
        help='PostgreSQL host (default: localhost)'
    )

    parser.add_argument(
        '--postgres-port',
        type=int,
        default=5432,
        help='PostgreSQL port (default: 5432)'
    )

    parser.add_argument(
        '--postgres-dbname',
        default='servicedesk',
        help='PostgreSQL database name (default: servicedesk)'
    )

    parser.add_argument(
        '--postgres-user',
        help='PostgreSQL username (default: from POSTGRES_USER env)'
    )

    parser.add_argument(
        '--postgres-password',
        help='PostgreSQL password (default: from POSTGRES_PASSWORD env)'
    )

    parser.add_argument(
        '--output',
        help='Output file for JSON results (default: stdout)'
    )

    args = parser.parse_args()

    # Run pre-flight checks
    try:
        result = run_all_preflight_checks(
            source_db=args.source,
            postgres_host=args.postgres_host,
            postgres_port=args.postgres_port,
            postgres_dbname=args.postgres_dbname,
            postgres_user=args.postgres_user,
            postgres_password=args.postgres_password
        )

        # Output results
        json_output = json.dumps(result, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Pre-flight results written to {args.output}", file=sys.stderr)
        else:
            print(json_output)

        # Exit based on status
        if result['preflight_status'] == 'FAIL':
            print("\n❌ PRE-FLIGHT CHECKS FAILED", file=sys.stderr)
            print("Fix the issues above before running ETL pipeline", file=sys.stderr)
            sys.exit(1)
        elif result['preflight_status'] == 'WARNING':
            print("\n⚠️  PRE-FLIGHT CHECKS PASSED WITH WARNINGS", file=sys.stderr)
            print("Pipeline may run but performance could be affected", file=sys.stderr)
            sys.exit(2)
        else:
            print("\n✅ PRE-FLIGHT CHECKS PASSED", file=sys.stderr)
            print("Environment ready for ETL pipeline", file=sys.stderr)
            sys.exit(0)

    except Exception as e:
        print(f"ERROR: Pre-flight checks failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
