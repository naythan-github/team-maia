#!/usr/bin/env python3
"""
Orro Application Inventory - Direct Email Scanner (No RAG Dependency)

Bypasses broken Ollama embedding service by scanning emails directly via MacOS Mail Bridge.
Production-grade with all SRE features intact.

Author: SRE Principal Engineer Agent
Created: 2025-11-21
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.orro_app_inventory_v2 import (
    ApplicationInventoryDB,
    ApplicationPatternMatcher,
    logger
)
from claude.tools.macos_mail_bridge import MacOSMailBridge
import time
from datetime import datetime, timedelta


class DirectEmailScanner:
    """Scan emails directly without RAG/Ollama dependency"""

    def __init__(self, db: ApplicationInventoryDB = None, matcher: ApplicationPatternMatcher = None):
        self.db = db or ApplicationInventoryDB()
        self.matcher = matcher or ApplicationPatternMatcher()
        self.mail_bridge = MacOSMailBridge()

    def extract_from_emails(self, days_back: int = 365) -> dict:
        """
        Scan emails directly from Mail.app

        Args:
            days_back: How many days of email history to scan (default: 1 year)

        Returns:
            Statistics dictionary
        """
        logger.info(f"Starting direct email scan (last {days_back} days)")

        # Get emails from Inbox and Sent folders
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')

        logger.info("Fetching Inbox messages...")
        # Use hours_ago to calculate hours from cutoff date
        hours_ago = days_back * 24
        inbox_msgs = self.mail_bridge.get_inbox_messages(
            limit=10000,  # Large limit to get all
            hours_ago=hours_ago
        )

        logger.info("Fetching Sent messages...")
        sent_msgs = self.mail_bridge.get_sent_messages(
            limit=10000,
            hours_ago=hours_ago
        )

        all_messages = inbox_msgs + sent_msgs
        logger.info(f"Total messages to scan: {len(all_messages)}")

        total_apps_found = 0
        total_errors = 0
        processed = 0

        for idx, msg in enumerate(all_messages, 1):
            if idx % 50 == 0:
                logger.info(f"Progress: {idx}/{len(all_messages)} messages ({idx/len(all_messages)*100:.1f}%)")

            try:
                apps_found = self._process_message(msg)
                total_apps_found += apps_found
                processed += 1

                # Rate limiting to avoid overwhelming Mail.app
                if idx % 100 == 0:
                    time.sleep(0.5)

            except Exception as e:
                total_errors += 1
                logger.warning(f"Error processing message {idx}: {e}")
                continue

        stats = self.db.get_stats()
        stats['total_errors'] = total_errors
        stats['messages_processed'] = processed

        logger.info(f"Scan complete: {stats}")
        return stats

    def _process_message(self, msg: dict) -> int:
        """Process a single email message"""
        body = msg.get('body', '')
        subject = msg.get('subject', '')
        combined_text = f"{subject} {body}"

        # Extract applications
        canonical_apps = self.matcher.extract_applications(combined_text)

        apps_found = 0

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
                first_seen=msg.get('date', '')
            )

            # Insert mention
            snippet = body[:500] if body else subject[:200]
            inserted = self.db.insert_mention(
                app_id=app_id,
                subject=subject,
                sender=msg.get('sender', ''),
                date=msg.get('date', ''),
                snippet=snippet,
                message_id=msg.get('id', '')
            )

            if inserted:
                apps_found += 1

            # Extract stakeholder
            sender = msg.get('sender', '')
            if sender and '@orro.com.au' in sender.lower():
                self._extract_stakeholder(sender)

        return apps_found

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
        description='Orro Application Inventory - Direct Email Scanner (No Ollama)'
    )
    parser.add_argument('command', choices=['extract', 'list', 'stats'],
                       help='Command to execute')
    parser.add_argument('--days', type=int, default=365,
                       help='Days of email history to scan (default: 365)')
    parser.add_argument('--limit', type=int, help='Limit results for list command')

    args = parser.parse_args()

    scanner = DirectEmailScanner()

    if args.command == 'extract':
        print("=" * 70)
        print("ORRO APPLICATION INVENTORY - DIRECT EMAIL SCANNER")
        print("(Bypassing broken Ollama - scanning Mail.app directly)")
        print("=" * 70)

        stats = scanner.extract_from_emails(days_back=args.days)

        print(f"\n📊 Scan Complete:")
        print(f"   • Messages Processed: {stats.get('messages_processed', 0)}")
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
