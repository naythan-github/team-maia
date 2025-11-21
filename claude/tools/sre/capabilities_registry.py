#!/usr/bin/env python3
"""
Capabilities Registry - Fast Tool/Agent Discovery for Maia

Scans claude/tools/ and claude/agents/ directories, extracts metadata,
and provides fast query interface for capability discovery.

Phase 168: Capabilities Database

Usage:
    # Scan and populate database
    python3 capabilities_registry.py scan

    # Find tools
    python3 capabilities_registry.py find security
    python3 capabilities_registry.py find --type tool sre
    python3 capabilities_registry.py find --type agent snowflake

    # List all by category
    python3 capabilities_registry.py list --category sre
    python3 capabilities_registry.py list --type agent

    # Show summary
    python3 capabilities_registry.py summary
"""

import sqlite3
import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Capability:
    """A tool or agent capability"""
    name: str
    type: str  # 'tool' or 'agent'
    path: str
    category: Optional[str] = None
    purpose: Optional[str] = None
    keywords: Optional[str] = None
    created_phase: Optional[str] = None
    status: str = 'production'
    last_modified: Optional[str] = None
    file_size_bytes: Optional[int] = None


class CapabilitiesRegistry:
    """
    Registry for Maia tools and agents.

    Provides fast discovery queries replacing 1,224-line capability_index.md.
    """

    # Category inference from path and content
    CATEGORY_PATTERNS = {
        'sre': ['sre', 'reliability', 'monitoring', 'health', 'etl', 'database'],
        'security': ['security', 'forensic', 'pir', 'vulnerability', 'audit'],
        'msp': ['msp', 'datto', 'autotask', 'connectwise', 'itglue', 'pagerduty', 'sonicwall'],
        'data': ['data', 'analyst', 'snowflake', 'analytics', 'rag', 'chromadb'],
        'integration': ['confluence', 'jira', 'teams', 'm365', 'azure', 'graph'],
        'document': ['document', 'docx', 'pdf', 'conversion', 'template'],
        'automation': ['automation', 'workflow', 'orchestrat'],
    }

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize registry with database path."""
        if db_path is None:
            maia_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = maia_root / "claude" / "data" / "databases" / "system" / "capabilities.db"

        self.db_path = Path(db_path)
        self.maia_root = Path(__file__).resolve().parent.parent.parent.parent

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database if needed
        if not self.db_path.exists():
            self._init_database()

    def _init_database(self):
        """Create database with schema."""
        schema_path = Path(__file__).parent / "capabilities_schema.sql"
        conn = sqlite3.connect(self.db_path)

        if schema_path.exists():
            conn.executescript(schema_path.read_text())
        else:
            # Inline schema if file not found
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS capabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    category TEXT,
                    purpose TEXT,
                    keywords TEXT,
                    created_phase TEXT,
                    status TEXT DEFAULT 'production',
                    last_modified TEXT,
                    file_size_bytes INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_capabilities_type ON capabilities(type);
                CREATE INDEX IF NOT EXISTS idx_capabilities_category ON capabilities(category);
            """)

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _infer_category(self, name: str, content: str) -> Optional[str]:
        """Infer category from filename and content."""
        text = (name + ' ' + content[:2000]).lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return category

        return 'general'

    def _extract_purpose(self, content: str) -> Optional[str]:
        """Extract purpose from file content."""
        # Try to find purpose in docstring or markdown
        patterns = [
            r'"""([^"]+)"""',  # Python docstring
            r"'''([^']+)'''",  # Python docstring alt
            r'\*\*Purpose\*\*:?\s*([^\n]+)',  # Markdown **Purpose**:
            r'Purpose:?\s*([^\n]+)',  # Plain Purpose:
            r'^#[^#].*\n+([^\n#]+)',  # First line after markdown title
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                purpose = match.group(1).strip()
                # Clean up and truncate
                purpose = re.sub(r'\s+', ' ', purpose)[:200]
                if len(purpose) > 20:
                    return purpose

        return None

    def _extract_keywords(self, name: str, content: str) -> str:
        """Extract searchable keywords from content."""
        keywords = set()

        # Add name parts
        name_parts = re.split(r'[_\-.]', name.lower())
        keywords.update(name_parts)

        # Extract from content
        text = content[:5000].lower()

        # Find capitalized terms (likely important)
        caps = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', content[:5000])
        keywords.update(c.lower() for c in caps)

        # Technology terms
        tech_terms = re.findall(r'\b(azure|aws|snowflake|chromadb|sqlite|postgres|api|rest|graphql|python|bash)\b', text)
        keywords.update(tech_terms)

        # Remove common words
        stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'are', 'was', 'been'}
        keywords -= stopwords

        return ','.join(sorted(keywords)[:20])

    def scan_directory(self, directory: str, cap_type: str) -> List[Capability]:
        """Scan a directory for capabilities."""
        capabilities = []
        dir_path = self.maia_root / directory

        if not dir_path.exists():
            return capabilities

        # Determine file patterns
        if cap_type == 'agent':
            patterns = ['*.md']
        else:
            patterns = ['*.py', '*.sh']

        for pattern in patterns:
            for file_path in dir_path.rglob(pattern):
                # Skip test files, __pycache__, etc.
                if '__pycache__' in str(file_path):
                    continue
                if file_path.name.startswith('test_'):
                    continue
                if file_path.name.startswith('.'):
                    continue

                try:
                    content = file_path.read_text(errors='ignore')
                    stat = file_path.stat()

                    rel_path = file_path.relative_to(self.maia_root)

                    cap = Capability(
                        name=file_path.name,
                        type=cap_type,
                        path=str(rel_path),
                        category=self._infer_category(file_path.name, content),
                        purpose=self._extract_purpose(content),
                        keywords=self._extract_keywords(file_path.name, content),
                        status='production',
                        last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        file_size_bytes=stat.st_size
                    )
                    capabilities.append(cap)

                except Exception as e:
                    print(f"  ⚠️ Error scanning {file_path}: {e}")

        return capabilities

    def scan_all(self) -> Tuple[int, int]:
        """Scan all tools and agents, populate database."""
        print("🔍 Scanning Maia capabilities...")

        # Clear existing data
        conn = self._get_connection()
        conn.execute("DELETE FROM capabilities")
        conn.commit()

        all_caps = []

        # Scan agents
        print("\n📦 Scanning agents...")
        agents = self.scan_directory("claude/agents", "agent")
        all_caps.extend(agents)
        print(f"   Found {len(agents)} agents")

        # Scan tools (multiple directories)
        print("\n🔧 Scanning tools...")
        tool_dirs = [
            "claude/tools/sre",
            "claude/tools/security",
            "claude/tools/monitoring",
            "claude/tools/mcp",
            "claude/tools/fobs",
            "claude/tools/services",
            "claude/tools/rag",
        ]

        total_tools = 0
        for tool_dir in tool_dirs:
            tools = self.scan_directory(tool_dir, "tool")
            all_caps.extend(tools)
            if tools:
                print(f"   {tool_dir}: {len(tools)} tools")
                total_tools += len(tools)

        # Insert into database
        print(f"\n💾 Inserting {len(all_caps)} capabilities into database...")

        for cap in all_caps:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO capabilities
                    (name, type, path, category, purpose, keywords, status, last_modified, file_size_bytes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (cap.name, cap.type, cap.path, cap.category, cap.purpose,
                      cap.keywords, cap.status, cap.last_modified, cap.file_size_bytes))
            except Exception as e:
                print(f"   ⚠️ Error inserting {cap.name}: {e}")

        conn.commit()
        conn.close()

        agent_count = len([c for c in all_caps if c.type == 'agent'])
        tool_count = len([c for c in all_caps if c.type == 'tool'])

        print(f"\n✅ Scan complete: {agent_count} agents, {tool_count} tools")
        return agent_count, tool_count

    def find(self, query: str, cap_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Find capabilities matching query.

        Searches name, category, purpose, and keywords.
        """
        conn = self._get_connection()

        sql = """
            SELECT name, type, path, category, purpose
            FROM capabilities
            WHERE (name LIKE ? OR category LIKE ? OR purpose LIKE ? OR keywords LIKE ?)
        """
        params = [f'%{query}%'] * 4

        if cap_type:
            sql += " AND type = ?"
            params.append(cap_type)

        sql += " ORDER BY type, category, name LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def list_by_category(self, category: Optional[str] = None, cap_type: Optional[str] = None) -> List[Dict]:
        """List capabilities by category."""
        conn = self._get_connection()

        sql = "SELECT name, type, path, category, purpose FROM capabilities WHERE 1=1"
        params = []

        if category:
            sql += " AND category = ?"
            params.append(category)

        if cap_type:
            sql += " AND type = ?"
            params.append(cap_type)

        sql += " ORDER BY category, type, name"

        cursor = conn.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        conn = self._get_connection()

        summary = {
            'total': 0,
            'agents': 0,
            'tools': 0,
            'by_category': {}
        }

        # Total counts
        cursor = conn.execute("SELECT type, COUNT(*) FROM capabilities GROUP BY type")
        for row in cursor:
            if row[0] == 'agent':
                summary['agents'] = row[1]
            else:
                summary['tools'] = row[1]
            summary['total'] += row[1]

        # By category
        cursor = conn.execute("""
            SELECT category, type, COUNT(*)
            FROM capabilities
            GROUP BY category, type
            ORDER BY category
        """)
        for row in cursor:
            cat = row[0] or 'uncategorized'
            if cat not in summary['by_category']:
                summary['by_category'][cat] = {'agents': 0, 'tools': 0}
            summary['by_category'][cat][row[1] + 's'] = row[2]

        conn.close()
        return summary

    def generate_markdown_table(self) -> str:
        """Generate markdown lookup table for capability_index.md."""
        conn = self._get_connection()

        output = []
        output.append("# Maia Capability Registry")
        output.append("")
        output.append(f"**Auto-generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append(f"**Query tool**: `python3 claude/tools/sre/capabilities_registry.py find <query>`")
        output.append("")

        # Agents table
        output.append("## Agents")
        output.append("")
        output.append("| Name | Category | Purpose |")
        output.append("|------|----------|---------|")

        cursor = conn.execute("""
            SELECT name, category, purpose, path
            FROM capabilities
            WHERE type = 'agent'
            ORDER BY category, name
        """)
        for row in cursor:
            purpose = (row[2] or '')[:60] + ('...' if row[2] and len(row[2]) > 60 else '')
            output.append(f"| {row[0]} | {row[1] or '-'} | {purpose} |")

        output.append("")

        # Tools by category
        output.append("## Tools")
        output.append("")

        cursor = conn.execute("SELECT DISTINCT category FROM capabilities WHERE type = 'tool' ORDER BY category")
        categories = [row[0] for row in cursor]

        for category in categories:
            output.append(f"### {category.title() if category else 'General'}")
            output.append("")
            output.append("| Tool | Purpose |")
            output.append("|------|---------|")

            cursor = conn.execute("""
                SELECT name, purpose, path
                FROM capabilities
                WHERE type = 'tool' AND category = ?
                ORDER BY name
            """, (category,))

            for row in cursor:
                purpose = (row[1] or '')[:80] + ('...' if row[1] and len(row[1]) > 80 else '')
                output.append(f"| {row[0]} | {purpose} |")

            output.append("")

        conn.close()
        return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='Maia Capabilities Registry')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    subparsers.add_parser('scan', help='Scan and populate database')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find capabilities')
    find_parser.add_argument('query', help='Search query')
    find_parser.add_argument('--type', choices=['tool', 'agent'], help='Filter by type')

    # List command
    list_parser = subparsers.add_parser('list', help='List capabilities')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--type', choices=['tool', 'agent'], help='Filter by type')

    # Summary command
    subparsers.add_parser('summary', help='Show summary statistics')

    # Generate command
    subparsers.add_parser('generate', help='Generate markdown table')

    args = parser.parse_args()

    registry = CapabilitiesRegistry()

    if args.command == 'scan':
        registry.scan_all()

    elif args.command == 'find':
        results = registry.find(args.query, cap_type=args.type)
        if results:
            print(f"\n🔍 Found {len(results)} results for '{args.query}':\n")
            for r in results:
                purpose = (r['purpose'] or '')[:60]
                print(f"  [{r['type']:5}] {r['name']}")
                print(f"         Path: {r['path']}")
                print(f"         Category: {r['category'] or '-'}")
                if purpose:
                    print(f"         Purpose: {purpose}...")
                print()
        else:
            print(f"❌ No results for '{args.query}'")

    elif args.command == 'list':
        results = registry.list_by_category(category=args.category, cap_type=args.type)
        if results:
            print(f"\n📋 {len(results)} capabilities:\n")
            current_cat = None
            for r in results:
                if r['category'] != current_cat:
                    current_cat = r['category']
                    print(f"\n### {current_cat or 'General'}")
                print(f"  [{r['type']:5}] {r['name']}")
        else:
            print("❌ No capabilities found")

    elif args.command == 'summary':
        summary = registry.get_summary()
        print(f"\n📊 Maia Capabilities Summary")
        print(f"{'='*40}")
        print(f"Total: {summary['total']}")
        print(f"  Agents: {summary['agents']}")
        print(f"  Tools: {summary['tools']}")
        print(f"\nBy Category:")
        for cat, counts in sorted(summary['by_category'].items()):
            print(f"  {cat}: {counts['agents']} agents, {counts['tools']} tools")

    elif args.command == 'generate':
        markdown = registry.generate_markdown_table()
        print(markdown)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
