#!/usr/bin/env python3
"""
Orro Application Inventory System v2.0 - Production Grade

SRE-hardened application extraction from email with:
- Transaction safety
- Rate limiting
- Progress checkpointing
- Full email body extraction
- Application normalization
- Comprehensive error handling

Author: SRE Principal Engineer Agent
Created: 2025-11-21
"""

import os
import sys
import json
import sqlite3
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.email_rag_ollama import EmailRAGOllama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApplicationInventoryDB:
    """Production-grade database layer with transaction safety"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            maia_root = Path(__file__).parent.parent.parent
            db_path = maia_root / "claude/data/databases/system/orro_application_inventory_v2.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
        logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with transaction safety"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # ✅ CRITICAL: Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            conn.close()

    def _initialize_database(self):
        """Create database schema with proper constraints"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Vendors table (create first - referenced by applications)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_name TEXT NOT NULL UNIQUE,
                    website TEXT,
                    contact_name TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    canonical_name TEXT NOT NULL,
                    vendor_id INTEGER,
                    category TEXT,
                    description TEXT,
                    url TEXT,
                    status TEXT DEFAULT 'active',
                    first_seen DATE,
                    last_seen DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL
                )
            """)

            # Stakeholders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stakeholders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    role TEXT,
                    department TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Application-Stakeholder relationship table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_stakeholders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    stakeholder_id INTEGER NOT NULL,
                    relationship_type TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
                    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
                    UNIQUE(application_id, stakeholder_id)
                )
            """)

            # Email mentions tracking table with deduplication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    email_subject TEXT,
                    email_from TEXT,
                    email_date DATE,
                    context_snippet TEXT,
                    message_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
                    UNIQUE(application_id, message_id)
                )
            """)

            # Extraction progress tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extraction_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_index INTEGER NOT NULL,
                    total_queries INTEGER NOT NULL,
                    apps_found INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create performance indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_name ON applications(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_canonical ON applications(canonical_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_vendor ON applications(vendor_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendor_name ON vendors(vendor_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stakeholder_email ON stakeholders(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_app ON mentions(application_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_date ON mentions(email_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_msgid ON mentions(message_id)")

            logger.info("Database schema created successfully")

    def insert_vendor(self, vendor_name: str) -> int:
        """Insert vendor and return ID (idempotent)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO vendors (vendor_name)
                VALUES (?)
            """, (vendor_name,))
            cursor.execute("SELECT id FROM vendors WHERE vendor_name = ?", (vendor_name,))
            return cursor.fetchone()[0]

    def insert_application(self, name: str, canonical_name: str, vendor_id: Optional[int],
                          category: str, first_seen: str) -> int:
        """Insert application and return ID (idempotent)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO applications (
                    name, canonical_name, vendor_id, category, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (name, canonical_name, vendor_id, category, first_seen, first_seen))

            cursor.execute("SELECT id FROM applications WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            raise ValueError(f"Failed to insert application: {name}")

    def insert_stakeholder(self, name: str, email: str) -> int:
        """Insert stakeholder and return ID (idempotent)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO stakeholders (name, email)
                VALUES (?, ?)
            """, (name, email))
            cursor.execute("SELECT id FROM stakeholders WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return row[0]
            raise ValueError(f"Failed to insert stakeholder: {email}")

    def insert_mention(self, app_id: int, subject: str, sender: str,
                      date: str, snippet: str, message_id: str) -> bool:
        """Insert mention (returns False if duplicate, True if inserted)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mentions (
                        application_id, email_subject, email_from,
                        email_date, context_snippet, message_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (app_id, subject, sender, date, snippet, message_id))
                return True
        except sqlite3.IntegrityError:
            # Duplicate mention (app_id + message_id already exists)
            return False

    def record_progress(self, query: str, query_index: int, total_queries: int,
                       apps_found: int, errors: int, completed: bool = False):
        """Record extraction progress for checkpoint resume"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO extraction_progress (
                    query, query_index, total_queries, apps_found, errors, completed
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (query, query_index, total_queries, apps_found, errors, completed))

    def get_last_checkpoint(self) -> Optional[int]:
        """Get last completed query index for resume"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(query_index) FROM extraction_progress WHERE completed = 1
            """)
            row = cursor.fetchone()
            return row[0] if row[0] is not None else -1

    def get_stats(self) -> Dict:
        """Get inventory statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM applications")
            app_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vendors")
            vendor_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM stakeholders")
            stakeholder_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM mentions")
            mention_count = cursor.fetchone()[0]

            return {
                'applications': app_count,
                'vendors': vendor_count,
                'stakeholders': stakeholder_count,
                'mentions': mention_count
            }

    def list_applications(self, limit: Optional[int] = None) -> List[Dict]:
        """List all applications with details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # ✅ FIXED: Use parameterized query for LIMIT
            query = """
                SELECT
                    a.id, a.name, a.canonical_name, a.category, a.status,
                    v.vendor_name,
                    COUNT(DISTINCT m.id) as mention_count,
                    a.first_seen, a.last_seen
                FROM applications a
                LEFT JOIN vendors v ON a.vendor_id = v.id
                LEFT JOIN mentions m ON a.id = m.application_id
                GROUP BY a.id
                ORDER BY mention_count DESC, a.name
            """

            if limit:
                query += " LIMIT ?"
                cursor.execute(query, (limit,))
            else:
                cursor.execute(query)

            apps = []
            for row in cursor.fetchall():
                apps.append({
                    'id': row[0],
                    'name': row[1],
                    'canonical_name': row[2],
                    'category': row[3],
                    'status': row[4],
                    'vendor': row[5],
                    'mentions': row[6],
                    'first_seen': row[7],
                    'last_seen': row[8]
                })

            return apps


class ApplicationPatternMatcher:
    """Pattern matching and normalization for application names"""

    def __init__(self, patterns_file: str = None):
        if patterns_file is None:
            maia_root = Path(__file__).parent.parent.parent
            patterns_file = maia_root / "claude/data/application_patterns.json"

        with open(patterns_file, 'r') as f:
            data = json.load(f)
            self.applications = data['applications']

        # Build lookup maps for fast matching
        self.alias_to_canonical = {}
        self.vendor_map = {}
        self.category_map = {}
        self.compiled_patterns = []

        for app in self.applications:
            canonical = app['canonical_name']

            # Map all aliases to canonical name
            for alias in app['aliases']:
                self.alias_to_canonical[alias.lower()] = canonical

            # Store vendor and category
            self.vendor_map[canonical] = app['vendor']
            self.category_map[canonical] = app['category']

            # Compile regex patterns
            for pattern in app['patterns']:
                self.compiled_patterns.append({
                    'regex': re.compile(pattern, re.IGNORECASE),
                    'canonical': canonical
                })

        logger.info(f"Loaded {len(self.applications)} application patterns")

    def extract_applications(self, text: str) -> Set[str]:
        """Extract canonical application names from text"""
        found = set()

        for pattern_dict in self.compiled_patterns:
            if pattern_dict['regex'].search(text):
                found.add(pattern_dict['canonical'])

        return found

    def normalize(self, app_name: str) -> str:
        """Normalize application name to canonical form"""
        return self.alias_to_canonical.get(app_name.lower(), app_name)

    def get_vendor(self, canonical_name: str) -> Optional[str]:
        """Get vendor for canonical application name"""
        return self.vendor_map.get(canonical_name)

    def get_category(self, canonical_name: str) -> Optional[str]:
        """Get category for canonical application name"""
        return self.category_map.get(canonical_name)


class OrroApplicationInventoryV2:
    """Production-grade application inventory extractor"""

    def __init__(self, db: ApplicationInventoryDB = None, matcher: ApplicationPatternMatcher = None):
        self.db = db or ApplicationInventoryDB()
        self.matcher = matcher or ApplicationPatternMatcher()
        self.email_rag = None
        self.rate_limit_delay = 1.5  # seconds between Ollama queries

    def _initialize_email_rag(self):
        """Lazy initialization of email RAG"""
        if self.email_rag is None:
            self.email_rag = EmailRAGOllama()
            logger.info("Email RAG initialized")

    def extract_from_emails(self, resume: bool = True) -> Dict:
        """
        Extract applications from all emails with checkpointing

        Args:
            resume: If True, resume from last checkpoint

        Returns:
            Statistics dictionary
        """
        self._initialize_email_rag()

        # Define search queries
        search_queries = [
            "Microsoft", "Azure", "Office 365", "Teams",
            "Salesforce", "ServiceNow", "Zendesk",
            "Confluence", "Jira", "Slack",
            "Datto", "ManageEngine", "SonicWall", "Autotask", "IT Glue",
            "PagerDuty", "OpsGenie", "Grafana",
            "CrowdStrike", "Duo", "Okta", "1Password",
            "GitHub", "GitLab", "Docker", "Kubernetes",
            "Terraform", "Ansible", "Splunk", "Elasticsearch",
            "Datadog", "New Relic", "Power BI", "Tableau", "Snowflake"
        ]

        total_queries = len(search_queries)
        start_index = 0

        # Resume from checkpoint if requested
        if resume:
            last_checkpoint = self.db.get_last_checkpoint()
            if last_checkpoint is not None and last_checkpoint >= 0:
                start_index = last_checkpoint + 1
                logger.info(f"Resuming from query index {start_index}")

        total_apps_found = 0
        total_errors = 0

        logger.info(f"Starting extraction: {total_queries} queries, starting at index {start_index}")

        for idx, query in enumerate(search_queries[start_index:], start=start_index):
            logger.info(f"[{idx+1}/{total_queries}] Searching: {query}")

            try:
                apps_found = self._process_query(query, idx, total_queries)
                total_apps_found += apps_found

                # Record progress checkpoint
                self.db.record_progress(query, idx, total_queries, apps_found, 0, completed=True)

                logger.info(f"  ✅ Found {apps_found} applications")

                # Rate limiting
                if idx < total_queries - 1:
                    time.sleep(self.rate_limit_delay)

            except Exception as e:
                total_errors += 1
                logger.error(f"  ❌ Error processing query '{query}': {e}")
                self.db.record_progress(query, idx, total_queries, 0, 1, completed=False)
                continue

        stats = self.db.get_stats()
        stats['total_errors'] = total_errors

        logger.info(f"Extraction complete: {stats}")
        return stats

    def _process_query(self, query: str, query_index: int, total_queries: int) -> int:
        """Process a single search query and extract applications"""
        # Search emails
        results = self.email_rag.semantic_search(query, n_results=20)

        apps_found = 0

        for result in results:
            message_id = result.get('message_id')
            if not message_id:
                continue

            try:
                # ✅ CRITICAL: Get full email body, not 200-char preview
                full_email = self.email_rag.mail_bridge.get_message_by_id(message_id)
                body = full_email.get('body', '')

                # Extract applications from full body
                canonical_apps = self.matcher.extract_applications(body)

                for canonical_name in canonical_apps:
                    # Get or create vendor
                    vendor_name = self.matcher.get_vendor(canonical_name)
                    vendor_id = None
                    if vendor_name:
                        vendor_id = self.db.insert_vendor(vendor_name)

                    # Get category
                    category = self.matcher.get_category(canonical_name)

                    # Insert application
                    app_id = self.db.insert_application(
                        name=canonical_name,
                        canonical_name=canonical_name,
                        vendor_id=vendor_id,
                        category=category,
                        first_seen=result.get('date', '')
                    )

                    # Insert mention
                    snippet = body[:500] if body else result.get('preview', '')
                    inserted = self.db.insert_mention(
                        app_id=app_id,
                        subject=result.get('subject', ''),
                        sender=result.get('sender', ''),
                        date=result.get('date', ''),
                        snippet=snippet,
                        message_id=message_id
                    )

                    if inserted:
                        apps_found += 1

                    # Extract stakeholder
                    sender = result.get('sender', '')
                    if sender and '@orro.com.au' in sender.lower():
                        self._extract_stakeholder(sender)

            except Exception as e:
                logger.warning(f"  Error processing message {message_id}: {e}")
                continue

        return apps_found

    def _extract_stakeholder(self, sender: str):
        """Extract stakeholder from email sender"""
        # Extract name from "Name <email@domain.com>" format
        name_match = re.match(r'^(.+?)\s*<', sender)
        if name_match:
            name = name_match.group(1).strip()
        else:
            # Extract from email address
            email_part = re.search(r'([^<>]+)@', sender)
            if email_part:
                name = email_part.group(1).replace('.', ' ').title()
            else:
                name = sender

        # Extract email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', sender)
        if email_match:
            email = email_match.group(1)
            try:
                self.db.insert_stakeholder(name, email)
            except Exception as e:
                logger.debug(f"Could not insert stakeholder {email}: {e}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Orro Application Inventory System v2.0')
    parser.add_argument('command', choices=['extract', 'list', 'stats'],
                       help='Command to execute')
    parser.add_argument('--no-resume', action='store_true',
                       help='Start extraction from beginning (ignore checkpoint)')
    parser.add_argument('--limit', type=int, help='Limit results for list command')

    args = parser.parse_args()

    inventory = OrroApplicationInventoryV2()

    if args.command == 'extract':
        print("=" * 70)
        print("ORRO APPLICATION INVENTORY v2.0 - PRODUCTION EXTRACTION")
        print("=" * 70)

        stats = inventory.extract_from_emails(resume=not args.no_resume)

        print(f"\n📊 Extraction Complete:")
        print(f"   • Applications: {stats['applications']}")
        print(f"   • Vendors: {stats['vendors']}")
        print(f"   • Stakeholders: {stats['stakeholders']}")
        print(f"   • Email Mentions: {stats['mentions']}")
        print(f"   • Errors: {stats.get('total_errors', 0)}")

    elif args.command == 'list':
        apps = inventory.db.list_applications(limit=args.limit)

        print("\n" + "=" * 80)
        print("APPLICATION INVENTORY")
        print("=" * 80)

        for app in apps:
            print(f"\n📦 {app['name']}")
            if app['vendor']:
                print(f"   Vendor: {app['vendor']}")
            if app['category']:
                print(f"   Category: {app['category']}")
            print(f"   Status: {app['status']}")
            print(f"   Mentions: {app['mentions']}")
            print(f"   First seen: {app['first_seen']}")

        print(f"\n📊 Total: {len(apps)} applications")

    elif args.command == 'stats':
        stats = inventory.db.get_stats()

        print("\n" + "=" * 60)
        print("INVENTORY STATISTICS")
        print("=" * 60)
        print(f"\n📦 Applications: {stats['applications']}")
        print(f"🏢 Vendors: {stats['vendors']}")
        print(f"👥 Stakeholders: {stats['stakeholders']}")
        print(f"📧 Email Mentions: {stats['mentions']}")


if __name__ == '__main__':
    main()
