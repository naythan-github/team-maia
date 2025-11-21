#!/usr/bin/env python3
"""
Orro Application Inventory System

Extracts software applications and SaaS tools from email RAG system
and builds a structured database with vendor and stakeholder relationships.
"""

import os
import sys
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.email_rag_ollama import EmailRAGOllama


class OrroApplicationInventory:
    """Manages application inventory database with vendor and stakeholder relationships"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            maia_root = Path(__file__).parent.parent.parent
            db_path = maia_root / "claude/data/databases/system/orro_application_inventory.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()

    def _initialize_database(self):
        """Create database schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                vendor_id INTEGER,
                category TEXT,
                description TEXT,
                url TEXT,
                status TEXT DEFAULT 'active',
                first_seen DATE,
                last_seen DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(id)
            )
        """)

        # Vendors table
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
                FOREIGN KEY (application_id) REFERENCES applications(id),
                FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id),
                UNIQUE(application_id, stakeholder_id)
            )
        """)

        # Email mentions tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                email_subject TEXT,
                email_from TEXT,
                email_date DATE,
                context_snippet TEXT,
                mention_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_name ON applications(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_vendor ON applications(vendor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendor_name ON vendors(vendor_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stakeholder_email ON stakeholders(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_app ON mentions(application_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_date ON mentions(email_date)")

        self.conn.commit()

    def extract_applications_from_emails(self, limit: int = None) -> Dict[str, List[Dict]]:
        """
        Extract application mentions from email RAG system

        Returns:
            Dict with 'applications', 'vendors', 'stakeholders' lists
        """
        print("🔍 Extracting applications from email RAG system...")

        # Initialize email RAG
        email_rag = EmailRAGOllama()

        # Common SaaS/application keywords to search for
        search_queries = [
            "Microsoft 365",
            "Azure",
            "ServiceNow",
            "Confluence",
            "Jira",
            "Slack",
            "Teams",
            "Salesforce",
            "Zendesk",
            "Datto",
            "ManageEngine",
            "SonicWall",
            "Autotask",
            "IT Glue",
            "PagerDuty",
            "OpsGenie",
            "Airlock",
            "Grafana",
            "monitoring tool",
            "cloud platform",
            "security software",
            "backup solution",
            "collaboration tool",
            "CRM system",
            "PSA tool",
            "RMM platform",
            "firewall",
            "antivirus",
            "email security",
            "documentation platform",
            "project management",
            "ticketing system",
            "password manager",
            "VPN solution"
        ]

        extracted_data = {
            'applications': [],
            'vendors': [],
            'stakeholders': []
        }

        seen_apps = set()
        seen_vendors = set()
        seen_stakeholders = set()

        for query in search_queries:
            print(f"  Searching: {query}...")
            try:
                results = email_rag.semantic_search(query, n_results=20)

                for result in results:
                    # Extract application names from email content
                    apps = self._extract_app_names(result.get('body', ''))

                    for app in apps:
                        if app not in seen_apps:
                            extracted_data['applications'].append({
                                'name': app,
                                'email_subject': result.get('subject', ''),
                                'email_from': result.get('sender', ''),
                                'email_date': result.get('date', ''),
                                'context': result.get('body', '')[:200]
                            })
                            seen_apps.add(app)

                    # Extract sender as potential stakeholder
                    sender = result.get('sender', '')
                    if sender and '@orro.com.au' in sender and sender not in seen_stakeholders:
                        extracted_data['stakeholders'].append({
                            'email': sender,
                            'name': self._extract_name_from_email(sender)
                        })
                        seen_stakeholders.add(sender)

            except Exception as e:
                print(f"    ⚠️  Error searching '{query}': {e}")
                continue

        print(f"\n✅ Extraction complete:")
        print(f"   • Applications found: {len(extracted_data['applications'])}")
        print(f"   • Stakeholders found: {len(extracted_data['stakeholders'])}")

        return extracted_data

    def _extract_app_names(self, text: str) -> List[str]:
        """Extract application names from email text using pattern matching"""
        apps = []

        # Common application name patterns
        patterns = [
            r'\b(Microsoft 365|M365|Office 365|O365)\b',
            r'\b(Azure|Azure AD|Entra ID)\b',
            r'\b(ServiceNow)\b',
            r'\b(Confluence|Atlassian)\b',
            r'\b(Jira|Jira Service Management)\b',
            r'\b(Slack)\b',
            r'\b(Microsoft Teams|Teams)\b',
            r'\b(Salesforce|SFDC)\b',
            r'\b(Zendesk)\b',
            r'\b(Datto RMM|Datto)\b',
            r'\b(ManageEngine|Desktop Central|Patch Manager)\b',
            r'\b(SonicWall)\b',
            r'\b(Autotask|Autotask PSA)\b',
            r'\b(IT Glue|ITGlue)\b',
            r'\b(PagerDuty)\b',
            r'\b(OpsGenie)\b',
            r'\b(Airlock Digital|Airlock)\b',
            r'\b(Grafana)\b',
            r'\b(CrowdStrike)\b',
            r'\b(Duo Security|Duo)\b',
            r'\b(Okta)\b',
            r'\b(1Password|OnePassword)\b',
            r'\b(LastPass)\b',
            r'\b(GitHub|GitLab)\b',
            r'\b(Docker)\b',
            r'\b(Kubernetes|K8s)\b',
            r'\b(Terraform)\b',
            r'\b(Ansible)\b',
            r'\b(Splunk)\b',
            r'\b(Elastic|Elasticsearch)\b',
            r'\b(Datadog)\b',
            r'\b(New Relic)\b',
            r'\b(Power BI|PowerBI)\b',
            r'\b(Tableau)\b',
            r'\b(Snowflake)\b',
            r'\b(OneDrive)\b',
            r'\b(SharePoint)\b',
            r'\b(Exchange Online|Exchange)\b',
            r'\b(Intune)\b',
            r'\b(Defender|Microsoft Defender)\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and match not in apps:
                    apps.append(match)

        return apps

    def _extract_name_from_email(self, email: str) -> str:
        """Extract name from email address"""
        # Try to get name from "Name <email@domain.com>" format
        name_match = re.match(r'^(.+?)\s*<', email)
        if name_match:
            return name_match.group(1).strip()

        # Otherwise extract from email address part before @
        email_part = re.search(r'([^<>]+)@', email)
        if email_part:
            name = email_part.group(1).replace('.', ' ').title()
            return name

        return email

    def populate_database(self, extracted_data: Dict):
        """Populate database with extracted data"""
        print("\n📥 Populating database...")

        cursor = self.conn.cursor()

        # Insert stakeholders
        for stakeholder in extracted_data['stakeholders']:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO stakeholders (name, email)
                    VALUES (?, ?)
                """, (stakeholder['name'], stakeholder['email']))
            except Exception as e:
                print(f"  ⚠️  Error inserting stakeholder: {e}")

        # Insert applications
        for app_data in extracted_data['applications']:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO applications (
                        name, first_seen, last_seen
                    ) VALUES (?, ?, ?)
                """, (
                    app_data['name'],
                    app_data['email_date'],
                    app_data['email_date']
                ))

                # Get application ID
                cursor.execute("SELECT id FROM applications WHERE name = ?", (app_data['name'],))
                app_row = cursor.fetchone()
                if app_row:
                    app_id = app_row[0]

                    # Insert mention
                    cursor.execute("""
                        INSERT INTO mentions (
                            application_id, email_subject, email_from,
                            email_date, context_snippet
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        app_id,
                        app_data['email_subject'],
                        app_data['email_from'],
                        app_data['email_date'],
                        app_data['context']
                    ))

            except Exception as e:
                print(f"  ⚠️  Error inserting application '{app_data['name']}': {e}")

        self.conn.commit()
        print("✅ Database populated successfully")

    def get_stats(self) -> Dict:
        """Get inventory statistics"""
        cursor = self.conn.cursor()

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

    def list_applications(self, limit: int = None) -> List[Dict]:
        """List all applications with details"""
        cursor = self.conn.cursor()

        query = """
            SELECT
                a.id, a.name, a.category, a.status,
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
            query += f" LIMIT {limit}"

        cursor.execute(query)

        apps = []
        for row in cursor.fetchall():
            apps.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'status': row[3],
                'vendor': row[4],
                'mentions': row[5],
                'first_seen': row[6],
                'last_seen': row[7]
            })

        return apps

    def export_to_csv(self, output_file: str):
        """Export inventory to CSV"""
        import csv

        apps = self.list_applications()

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'name', 'category', 'vendor', 'status',
                'mentions', 'first_seen', 'last_seen'
            ])
            writer.writeheader()
            writer.writerows(apps)

        print(f"✅ Exported {len(apps)} applications to {output_file}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Orro Application Inventory System')
    parser.add_argument('command', choices=['extract', 'list', 'stats', 'export'],
                       help='Command to execute')
    parser.add_argument('--output', help='Output file for export command')
    parser.add_argument('--limit', type=int, help='Limit results')

    args = parser.parse_args()

    inventory = OrroApplicationInventory()

    try:
        if args.command == 'extract':
            print("=" * 60)
            print("ORRO APPLICATION INVENTORY - EMAIL EXTRACTION")
            print("=" * 60)

            # Extract from emails
            extracted_data = inventory.extract_applications_from_emails(limit=args.limit)

            # Populate database
            inventory.populate_database(extracted_data)

            # Show stats
            stats = inventory.get_stats()
            print(f"\n📊 Final Database Statistics:")
            print(f"   • Applications: {stats['applications']}")
            print(f"   • Vendors: {stats['vendors']}")
            print(f"   • Stakeholders: {stats['stakeholders']}")
            print(f"   • Email Mentions: {stats['mentions']}")

        elif args.command == 'list':
            apps = inventory.list_applications(limit=args.limit)

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
                print(f"   Last seen: {app['last_seen']}")

            print(f"\n📊 Total: {len(apps)} applications")

        elif args.command == 'stats':
            stats = inventory.get_stats()

            print("\n" + "=" * 60)
            print("INVENTORY STATISTICS")
            print("=" * 60)
            print(f"\n📦 Applications: {stats['applications']}")
            print(f"🏢 Vendors: {stats['vendors']}")
            print(f"👥 Stakeholders: {stats['stakeholders']}")
            print(f"📧 Email Mentions: {stats['mentions']}")
            print(f"\n💾 Database: {inventory.db_path}")

        elif args.command == 'export':
            if not args.output:
                args.output = 'orro_application_inventory.csv'
            inventory.export_to_csv(args.output)

    finally:
        inventory.close()


if __name__ == '__main__':
    main()
