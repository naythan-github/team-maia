#!/usr/bin/env python3
"""
find_capability.py - DB-first capability lookup tool.

Enforces Principle 18 (DB-First Queries) by making database queries
easier than Grep/Glob for finding tools and agents.

Usage:
    python3 claude/tools/core/find_capability.py "keyword"
    python3 claude/tools/core/find_capability.py --category sre
    python3 claude/tools/core/find_capability.py --type agent "security"
    python3 claude/tools/core/find_capability.py --category sre --type tool "state"

Examples:
    # Find anything related to trello
    python3 claude/tools/core/find_capability.py trello

    # List all SRE tools
    python3 claude/tools/core/find_capability.py --category sre --type tool

    # Find security agents
    python3 claude/tools/core/find_capability.py --type agent security
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Import paths - handle both direct execution and module import
try:
    from claude.tools.core.paths import DATABASES_DIR
except ImportError:
    # Direct execution - derive path
    SCRIPT_DIR = Path(__file__).parent
    DATABASES_DIR = SCRIPT_DIR.parent.parent / "data" / "databases"

DB_PATH = DATABASES_DIR / "system" / "capabilities.db"


def get_connection():
    """Get database connection."""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


def search_capabilities(
    keyword: str = None,
    category: str = None,
    cap_type: str = None
) -> list:
    """
    Search capabilities database.

    Args:
        keyword: Search term (matches name, purpose, keywords)
        category: Filter by category (sre, security, data, etc.)
        cap_type: Filter by type ('tool' or 'agent')

    Returns:
        List of matching capabilities as dicts
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query dynamically
    conditions = ["status != 'deprecated'"]
    params = []

    if keyword:
        # Case-insensitive search across multiple fields
        conditions.append(
            "(LOWER(name) LIKE ? OR LOWER(purpose) LIKE ? OR LOWER(keywords) LIKE ?)"
        )
        keyword_pattern = f"%{keyword.lower()}%"
        params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

    if category:
        conditions.append("LOWER(category) = ?")
        params.append(category.lower())

    if cap_type:
        conditions.append("LOWER(type) = ?")
        params.append(cap_type.lower())

    query = f"""
        SELECT name, type, path, category, purpose, status
        FROM capabilities
        WHERE {' AND '.join(conditions)}
        ORDER BY category, type, name
    """

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


def format_results(results: list, verbose: bool = False) -> str:
    """Format results for display."""
    if not results:
        return "No capabilities found matching your criteria."

    lines = []
    current_category = None

    for r in results:
        # Group by category
        if r['category'] != current_category:
            current_category = r['category']
            lines.append(f"\n[{current_category.upper()}]")

        # Format each result
        type_indicator = "T" if r['type'] == 'tool' else "A"
        if verbose:
            lines.append(f"  [{type_indicator}] {r['name']}")
            lines.append(f"      Path: {r['path']}")
            if r['purpose']:
                lines.append(f"      Purpose: {r['purpose']}")
        else:
            purpose_snippet = ""
            if r['purpose']:
                purpose_snippet = f" - {r['purpose'][:50]}..." if len(r['purpose']) > 50 else f" - {r['purpose']}"
            lines.append(f"  [{type_indicator}] {r['path']}{purpose_snippet}")

    # Summary
    tools = sum(1 for r in results if r['type'] == 'tool')
    agents = sum(1 for r in results if r['type'] == 'agent')
    lines.append(f"\nFound: {tools} tools, {agents} agents ({len(results)} total)")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search Maia capabilities database (DB-first principle)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s trello                    # Find anything related to trello
  %(prog)s --category sre            # List all SRE capabilities
  %(prog)s --type tool email         # Find tools related to email
  %(prog)s -c security -t agent      # List security agents
        """
    )
    parser.add_argument(
        "keyword",
        nargs="?",
        default=None,
        help="Search term (searches name, purpose, keywords)"
    )
    parser.add_argument(
        "-c", "--category",
        help="Filter by category (sre, security, data, msp, etc.)"
    )
    parser.add_argument(
        "-t", "--type",
        choices=["tool", "agent"],
        help="Filter by type (tool or agent)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available categories"
    )

    args = parser.parse_args()

    # Handle --list-categories
    if args.list_categories:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM capabilities
            WHERE status != 'deprecated'
            GROUP BY category
            ORDER BY count DESC
        """)
        print("Available categories:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} capabilities")
        conn.close()
        return

    # If no filters provided, show summary
    if not args.keyword and not args.category and not args.type:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM capabilities
            WHERE status != 'deprecated'
            GROUP BY type
        """)
        print("Maia Capabilities Summary:")
        for row in cursor.fetchall():
            print(f"  {row[0]}s: {row[1]}")
        print("\nUse --help for search options, or --list-categories to see categories.")
        conn.close()
        return

    # Perform search
    results = search_capabilities(
        keyword=args.keyword,
        category=args.category,
        cap_type=args.type
    )

    print(format_results(results, verbose=args.verbose))


if __name__ == "__main__":
    main()
