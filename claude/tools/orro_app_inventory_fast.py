#!/usr/bin/env python3
"""
Orro Application Inventory - Fast RAG Database Scanner

Queries email RAG ChromaDB directly without Ollama embeddings (pure SQL).
Fastest possible extraction from 1,415 indexed emails.

Author: SRE Principal Engineer Agent
Created: 2025-11-21
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.orro_app_inventory_v2 import (
    ApplicationInventoryDB,
    ApplicationPatternMatcher,
    logger
)


class FastRAGScanner:
    """Fast scanner that queries RAG database directly via SQL"""

    def __init__(self, db: ApplicationInventoryDB = None, matcher: ApplicationPatternMatcher = None):
        self.db = db or ApplicationInventoryDB()
        self.matcher = matcher or ApplicationPatternMatcher()

        # Path to email RAG database
        maia_root = Path(__file__).parent.parent.parent
        self.rag_db_path = maia_root / "claude/data/rag_databases/email_rag_ollama/chroma.sqlite3"

        if not self.rag_db_path.exists():
            raise FileNotFoundError(f"Email RAG database not found: {self.rag_db_path}")

    def extract_from_rag(self) -> dict:
        """
        Extract applications by querying RAG database directly (no embeddings)

        Returns:
            Statistics dictionary
        """
        logger.info("Connecting to email RAG database...")

        # Connect to ChromaDB SQLite database
        conn = sqlite3.connect(str(self.rag_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query email metadata from ChromaDB
        # ChromaDB stores documents and metadata in embedding_metadata table
        cursor.execute("""
            SELECT
                em.id,
                em.key,
                em.string_value
            FROM embedding_metadata em
            JOIN embeddings e ON em.id = e.id
            WHERE em.key IN ('chroma:document', 'subject', 'sender', 'date', 'message_id')
            ORDER BY em.id
            LIMIT 50000
        """)

        metadata_rows = cursor.fetchall()
        logger.info(f"Found {len(metadata_rows)} metadata entries")

        # Build metadata map
        metadata_map = {}
        for row in metadata_rows:
            doc_id = row['id']
            if doc_id not in metadata_map:
                metadata_map[doc_id] = {}

            key = row['key']
            if key == 'chroma:document':
                metadata_map[doc_id]['body'] = row['string_value']
            else:
                metadata_map[doc_id][key] = row['string_value']

        logger.info(f"Loaded metadata for {len(metadata_map)} emails")

        # Process each email
        total_apps_found = 0
        total_errors = 0
        processed = 0

        for doc_id, metadata in metadata_map.items():
            if processed % 100 == 0:
                logger.info(f"Progress: {processed}/{len(metadata_map)} emails ({processed/len(metadata_map)*100:.1f}%)")

            try:
                subject = metadata.get('subject', '')
                body = metadata.get('body', '')
                combined_text = f"{subject} {body}"

                # Extract applications
                canonical_apps = self.matcher.extract_applications(combined_text)

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
                        first_seen=metadata.get('date', '')
                    )

                    # Insert mention
                    snippet = body[:500] if body else subject[:200]
                    inserted = self.db.insert_mention(
                        app_id=app_id,
                        subject=subject,
                        sender=metadata.get('sender', ''),
                        date=metadata.get('date', ''),
                        snippet=snippet,
                        message_id=metadata.get('message_id', doc_id)
                    )

                    if inserted:
                        total_apps_found += 1

                    # Extract stakeholder
                    sender = metadata.get('sender', '')
                    if sender and '@orro.com.au' in sender.lower():
                        self._extract_stakeholder(sender)

                processed += 1

            except Exception as e:
                total_errors += 1
                logger.warning(f"Error processing email {doc_id}: {e}")
                continue

        conn.close()

        stats = self.db.get_stats()
        stats['total_errors'] = total_errors
        stats['emails_processed'] = processed

        logger.info(f"Extraction complete: {stats}")
        return stats

    def _extract_stakeholder(self, sender: str):
        """Extract stakeholder from email sender"""
        import re

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

    parser = argparse.ArgumentParser(
        description='Orro Application Inventory - Fast RAG Scanner'
    )
    parser.add_argument('command', choices=['extract', 'list', 'stats'],
                       help='Command to execute')
    parser.add_argument('--limit', type=int, help='Limit results for list command')

    args = parser.parse_args()

    scanner = FastRAGScanner()

    if args.command == 'extract':
        print("=" * 70)
        print("ORRO APPLICATION INVENTORY - FAST RAG SCANNER")
        print("(Direct ChromaDB query - No Ollama required)")
        print("=" * 70)

        stats = scanner.extract_from_rag()

        print(f"\n📊 Extraction Complete:")
        print(f"   • Emails Processed: {stats.get('emails_processed', 0)}")
        print(f"   • Applications Found: {stats['applications']}")
        print(f"   • Vendors: {stats['vendors']}")
        print(f"   • Stakeholders: {stats['stakeholders']}")
        print(f"   • Email Mentions: {stats['mentions']}")
        print(f"   • Errors: {stats.get('total_errors', 0)}")

    elif args.command == 'list':
        apps = scanner.db.list_applications(limit=args.limit)

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
        stats = scanner.db.get_stats()

        print("\n" + "=" * 60)
        print("INVENTORY STATISTICS")
        print("=" * 60)
        print(f"\n📦 Applications: {stats['applications']}")
        print(f"🏢 Vendors: {stats['vendors']}")
        print(f"👥 Stakeholders: {stats['stakeholders']}")
        print(f"📧 Email Mentions: {stats['mentions']}")


if __name__ == '__main__':
    main()
