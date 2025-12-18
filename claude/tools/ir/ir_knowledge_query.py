#!/usr/bin/env python3
"""
IR Knowledge Query Tool - CLI for quick lookups against the knowledge base.

Phase 224 - IR Automation Tools

Usage:
    ir_knowledge_query.py ip <ip_address> [--db <path>]
    ir_knowledge_query.py app <app_id> [--db <path>]
    ir_knowledge_query.py pattern <signature> [--db <path>]
    ir_knowledge_query.py service <customer> <service_name> [--db <path>]
    ir_knowledge_query.py stats [--db <path>]

Examples:
    ir_knowledge_query.py ip 93.127.215.4
    ir_knowledge_query.py app 683b8f3c-cc24-4eda-9fd3-bf7f29551704
    ir_knowledge_query.py pattern "Safari.*Windows"
    ir_knowledge_query.py service "Fyna Foods" "Usemotion"
    ir_knowledge_query.py stats
"""

import argparse
import os
import sys

from ir_knowledge import IRKnowledgeBase

# Default database location
DEFAULT_DB_PATH = os.path.expanduser("~/maia/claude/data/databases/intelligence/ir_knowledge.db")


def query_ip(ip_address: str, db_path: str = DEFAULT_DB_PATH) -> str:
    """Query an IP address against the knowledge base.

    Args:
        ip_address: IP address to look up
        db_path: Path to the knowledge base

    Returns:
        Formatted string with query results
    """
    kb = IRKnowledgeBase(db_path)
    results = kb.query_ioc("ip", ip_address)

    if not results:
        return f"UNKNOWN - IP {ip_address} not found in knowledge base"

    lines = []
    for result in results:
        status = result.get('status', 'UNKNOWN')
        context = result.get('context', '')
        inv_id = result.get('investigation_id', '')
        customer = result.get('customer', '')

        if status == 'BLOCKED':
            status_str = "MALICIOUS/BLOCKED"
        else:
            status_str = status

        lines.append(f"{status_str} - {context} - seen in {inv_id} ({customer})")

    return "\n".join(lines)


def query_app(app_id: str, db_path: str = DEFAULT_DB_PATH) -> str:
    """Query an OAuth app against the knowledge base.

    Args:
        app_id: Application ID (GUID) to look up
        db_path: Path to the knowledge base

    Returns:
        Formatted string with query results
    """
    kb = IRKnowledgeBase(db_path)
    result = kb.is_app_verified(app_id)

    if result['verified']:
        name = result.get('name', 'Unknown')
        owner = result.get('owner', 'Unknown')
        permissions = result.get('permissions', [])
        perm_count = len(permissions) if permissions else 0

        return f"VERIFIED - {name} by {owner} - {perm_count} permissions"
    else:
        return f"UNKNOWN - App {app_id} not found in verified apps - INVESTIGATE"


def query_pattern(signature: str, db_path: str = DEFAULT_DB_PATH) -> str:
    """Query a pattern against the knowledge base.

    Args:
        signature: Pattern signature/regex to look up
        db_path: Path to the knowledge base

    Returns:
        Formatted string with query results
    """
    kb = IRKnowledgeBase(db_path)

    # Get all patterns and search for matching signature
    conn = kb._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM patterns WHERE signature = ? OR signature LIKE ?
    """, (signature, f"%{signature}%"))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"UNKNOWN - Pattern '{signature}' not found in knowledge base"

    lines = []
    for row in rows:
        pattern_type = row['pattern_type']
        sig = row['signature']
        confidence = row['confidence']
        description = row['description'] or ''

        conf_pct = f"{confidence * 100:.0f}%"
        lines.append(f"Known {pattern_type} pattern - {conf_pct} confidence - {description}")

    return "\n".join(lines)


def query_service(customer: str, service_name: str, db_path: str = DEFAULT_DB_PATH) -> str:
    """Query a customer service against the knowledge base.

    Args:
        customer: Customer name
        service_name: Service name
        db_path: Path to the knowledge base

    Returns:
        Formatted string with query results
    """
    kb = IRKnowledgeBase(db_path)

    conn = kb._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM customer_services
        WHERE customer = ? AND service_name = ?
    """, (customer, service_name))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return f"UNKNOWN - Service '{service_name}' for '{customer}' not found"

    verified = bool(row['verified'])
    notes = row['notes'] or ''

    if verified:
        return f"VERIFIED - {service_name} for {customer} - {notes}"
    else:
        return f"UNVERIFIED - {service_name} for {customer} - {notes}"


def get_stats(db_path: str = DEFAULT_DB_PATH) -> str:
    """Get statistics from the knowledge base.

    Args:
        db_path: Path to the knowledge base

    Returns:
        Formatted string with statistics
    """
    kb = IRKnowledgeBase(db_path)

    conn = kb._get_connection()
    cursor = conn.cursor()

    # Count investigations
    cursor.execute("SELECT COUNT(*) FROM investigations")
    inv_count = cursor.fetchone()[0]

    # Count IOCs
    cursor.execute("SELECT COUNT(*) FROM iocs")
    ioc_count = cursor.fetchone()[0]

    # Count patterns
    cursor.execute("SELECT COUNT(*) FROM patterns")
    pattern_count = cursor.fetchone()[0]

    # Count verified apps
    cursor.execute("SELECT COUNT(*) FROM verified_apps")
    app_count = cursor.fetchone()[0]

    # Count customer services
    cursor.execute("SELECT COUNT(*) FROM customer_services")
    service_count = cursor.fetchone()[0]

    conn.close()

    return (
        f"Investigations: {inv_count}, "
        f"IOCs: {ioc_count}, "
        f"Patterns: {pattern_count}, "
        f"Verified Apps: {app_count}, "
        f"Customer Services: {service_count}"
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="IR Knowledge Query Tool - Quick lookups against the knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s ip 93.127.215.4
    %(prog)s app 683b8f3c-cc24-4eda-9fd3-bf7f29551704
    %(prog)s pattern "Safari.*Windows"
    %(prog)s service "Fyna Foods" "Usemotion"
    %(prog)s stats
        """
    )

    parser.add_argument(
        '--db',
        default=DEFAULT_DB_PATH,
        help=f"Path to knowledge base (default: {DEFAULT_DB_PATH})"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # IP command
    ip_parser = subparsers.add_parser('ip', help='Query an IP address')
    ip_parser.add_argument('ip_address', help='IP address to look up')

    # App command
    app_parser = subparsers.add_parser('app', help='Query an OAuth app')
    app_parser.add_argument('app_id', help='Application ID (GUID) to look up')

    # Pattern command
    pattern_parser = subparsers.add_parser('pattern', help='Query a detection pattern')
    pattern_parser.add_argument('signature', help='Pattern signature to look up')

    # Service command
    service_parser = subparsers.add_parser('service', help='Query a customer service')
    service_parser.add_argument('customer', help='Customer name')
    service_parser.add_argument('service_name', help='Service name')

    # Stats command
    subparsers.add_parser('stats', help='Get knowledge base statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'ip':
            print(query_ip(args.ip_address, args.db))
        elif args.command == 'app':
            print(query_app(args.app_id, args.db))
        elif args.command == 'pattern':
            print(query_pattern(args.signature, args.db))
        elif args.command == 'service':
            print(query_service(args.customer, args.service_name, args.db))
        elif args.command == 'stats':
            print(get_stats(args.db))
        else:
            print(f"Invalid command: {args.command}")
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
