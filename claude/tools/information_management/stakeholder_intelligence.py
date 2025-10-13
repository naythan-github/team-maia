#!/usr/bin/env python3
"""
Stakeholder Relationship Intelligence Agent - Phase 2 Session 1

CRM-style intelligence system providing relationship health monitoring,
sentiment analysis, and automated context assembly for stakeholder interactions.

Author: Maia (My AI Agent)
Created: 2025-10-13
Phase: 115 (Information Management System - Phase 2)
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import subprocess
import importlib.util

# Path setup
MAIA_ROOT = Path(os.environ.get('MAIA_ROOT', Path.home() / 'git' / 'maia' / 'claude'))

def import_module_from_path(module_name: str, file_path: Path):
    """Dynamic module import for cross-directory dependencies"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import email RAG for communication analysis
try:
    email_rag_path = MAIA_ROOT / "tools" / "email_rag_ollama.py"
    email_rag = import_module_from_path("email_rag_ollama", email_rag_path)
    EmailRAGOllama = email_rag.EmailRAGOllama
except Exception as e:
    print(f"⚠️  Warning: Could not import email RAG: {e}")
    EmailRAGOllama = None


class StakeholderIntelligenceAgent:
    """
    CRM-style stakeholder relationship intelligence with health monitoring,
    sentiment analysis, and automated context assembly.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize agent with database connection"""
        self.db_path = db_path or MAIA_ROOT / "data" / "databases" / "stakeholder_intelligence.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

        # Email RAG integration
        self.email_rag = EmailRAGOllama() if EmailRAGOllama else None

    def _init_database(self):
        """Create database schema with 4 tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Stakeholders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stakeholders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                segment TEXT,
                organization TEXT,
                role TEXT,
                first_contact_date TEXT,
                last_contact_date TEXT,
                contact_frequency_days REAL,
                notes TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table 2: Relationship Metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationship_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stakeholder_id INTEGER NOT NULL,
                measured_at TEXT NOT NULL,
                health_score REAL,
                sentiment_score REAL,
                engagement_level TEXT,
                response_time_hours REAL,
                communication_balance REAL,
                sentiment_trend TEXT,
                last_30_days_contacts INTEGER,
                last_60_days_contacts INTEGER,
                last_90_days_contacts INTEGER,
                FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id)
            )
        ''')

        # Table 3: Commitments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commitments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stakeholder_id INTEGER NOT NULL,
                commitment_text TEXT NOT NULL,
                made_by TEXT,
                made_to TEXT,
                commitment_date TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                completed_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id)
            )
        ''')

        # Table 4: Interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stakeholder_id INTEGER NOT NULL,
                interaction_date TEXT NOT NULL,
                interaction_type TEXT,
                subject TEXT,
                sentiment_score REAL,
                key_topics TEXT,
                action_items TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id)
            )
        ''')

        conn.commit()
        conn.close()

        print(f"✅ Database initialized: {self.db_path}")

    def discover_stakeholders_from_email(self, min_email_count: int = 3) -> List[Dict]:
        """
        Discover stakeholders from email patterns using Email RAG.

        Args:
            min_email_count: Minimum email exchanges to qualify as stakeholder

        Returns:
            List of discovered stakeholders with metadata
        """
        if not self.email_rag:
            print("⚠️  Email RAG not available")
            return []

        print("🔍 Discovering stakeholders from email patterns...")

        # Query email RAG for all emails
        try:
            # Get email metadata from RAG system (supports both paths)
            email_rag_db = Path.home() / ".maia" / "email_rag_ollama" / "chroma.sqlite3"
            if not email_rag_db.exists():
                email_rag_db = Path.home() / ".maia" / "email_rag" / "chroma.sqlite3"
            if not email_rag_db.exists():
                print(f"⚠️  Email RAG database not found in ~/.maia/email_rag_ollama/ or ~/.maia/email_rag/")
                return []

            # Connect to ChromaDB SQLite to extract email metadata
            conn = sqlite3.connect(email_rag_db)
            cursor = conn.cursor()

            # Get all email senders/recipients from metadata
            cursor.execute("SELECT key, string_value FROM embedding_metadata WHERE key IN ('sender', 'recipient')")
            email_contacts = {}

            for key, email in cursor.fetchall():
                if email and '@' in email:
                    email = email.lower().strip()
                    if email not in email_contacts:
                        email_contacts[email] = {'count': 0, 'first_seen': None, 'last_seen': None}
                    email_contacts[email]['count'] += 1

            conn.close()

            # Filter to stakeholders (min_email_count threshold)
            stakeholders = []
            for email, data in email_contacts.items():
                if data['count'] >= min_email_count:
                    stakeholders.append({
                        'email': email,
                        'name': self._extract_name_from_email(email),
                        'contact_count': data['count'],
                        'segment': self._auto_classify_segment(email),
                        'organization': self._extract_organization(email)
                    })

            print(f"✅ Discovered {len(stakeholders)} stakeholders from email (threshold: {min_email_count}+ emails)")
            return sorted(stakeholders, key=lambda x: x['contact_count'], reverse=True)

        except Exception as e:
            print(f"⚠️  Error discovering stakeholders: {e}")
            return []

    def _extract_name_from_email(self, email: str) -> str:
        """Extract name from email address"""
        # Simple heuristic: take part before @ and capitalize
        local_part = email.split('@')[0]
        # Replace common separators with space
        name = local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        # Capitalize each word
        return ' '.join(word.capitalize() for word in name.split())

    def _extract_organization(self, email: str) -> str:
        """Extract organization from email domain"""
        domain = email.split('@')[1] if '@' in email else ''
        # Remove common TLDs
        org = domain.replace('.com', '').replace('.com.au', '').replace('.org', '').replace('.net', '')
        return org.capitalize()

    def _auto_classify_segment(self, email: str) -> str:
        """Auto-classify stakeholder segment based on email domain"""
        domain = email.split('@')[1] if '@' in email else ''

        # Orro Group = team members
        if 'orro' in domain.lower():
            return 'team_member'

        # External domains = clients or vendors
        if any(vendor in domain.lower() for vendor in ['microsoft', 'aws', 'azure', 'salesforce']):
            return 'vendor'

        # Default to collaborator
        return 'collaborator'

    def add_stakeholder(self, email: str, name: Optional[str] = None,
                       segment: Optional[str] = None, organization: Optional[str] = None,
                       role: Optional[str] = None, notes: Optional[str] = None) -> int:
        """
        Add new stakeholder to database.

        Returns:
            Stakeholder ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if stakeholder exists
        cursor.execute("SELECT id FROM stakeholders WHERE email = ?", (email,))
        existing = cursor.fetchone()

        if existing:
            print(f"⚠️  Stakeholder already exists: {email} (ID: {existing[0]})")
            conn.close()
            return existing[0]

        # Auto-populate fields if not provided
        name = name or self._extract_name_from_email(email)
        segment = segment or self._auto_classify_segment(email)
        organization = organization or self._extract_organization(email)

        cursor.execute('''
            INSERT INTO stakeholders (email, name, segment, organization, role, notes, first_contact_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email, name, segment, organization, role, notes, datetime.now().isoformat()))

        stakeholder_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Added stakeholder: {name} ({email}) - ID: {stakeholder_id}")
        return stakeholder_id

    def calculate_health_score(self, stakeholder_id: int) -> float:
        """
        Calculate multi-factor relationship health score (0-100).

        Formula:
            health_score = (
                sentiment_score * 0.30 +
                engagement_frequency * 0.25 +
                commitment_delivery * 0.20 +
                response_time_score * 0.15 +
                meeting_attendance * 0.10
            ) * 100

        Returns:
            Health score (0-100)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get latest metrics (with fallback defaults if no metrics yet)
        cursor.execute('''
            SELECT sentiment_score, last_30_days_contacts, response_time_hours
            FROM relationship_metrics
            WHERE stakeholder_id = ?
            ORDER BY measured_at DESC
            LIMIT 1
        ''', (stakeholder_id,))

        metrics = cursor.fetchone()

        # If no metrics, calculate from interactions directly
        if not metrics:
            cursor.execute('''
                SELECT AVG(sentiment_score), COUNT(*)
                FROM interactions
                WHERE stakeholder_id = ? AND interaction_date >= date('now', '-30 days')
            ''', (stakeholder_id,))
            interaction_data = cursor.fetchone()
            sentiment_score = interaction_data[0] if interaction_data[0] is not None else 0
            contacts_30d = interaction_data[1] or 0
            response_time = None
        else:
            sentiment_score, contacts_30d, response_time = metrics

        # Component 1: Sentiment Score (0-30 points)
        sentiment_points = ((sentiment_score or 0) + 1) / 2 * 30  # Convert -1,1 to 0-30

        # Component 2: Engagement Frequency (0-25 points)
        # Ideal: 1 contact per week (4 per month)
        engagement_ratio = min(contacts_30d / 4, 1.0) if contacts_30d else 0
        engagement_points = engagement_ratio * 25

        # Component 3: Commitment Delivery (0-20 points)
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM commitments
            WHERE stakeholder_id = ? AND status != 'cancelled'
        ''', (stakeholder_id,))
        commitment_data = cursor.fetchone()
        commitment_ratio = (commitment_data[1] / commitment_data[0]) if commitment_data[0] > 0 else 1.0
        commitment_points = commitment_ratio * 20

        # Component 4: Response Time Score (0-15 points)
        # Ideal: <24 hours = 15 points, >72 hours = 0 points
        if response_time:
            response_score = max(0, min(1, (72 - response_time) / 48))
            response_points = response_score * 15
        else:
            response_points = 10  # Neutral if no data

        # Component 5: Meeting Attendance (0-10 points)
        # Placeholder for now (requires calendar integration)
        meeting_points = 8  # Neutral assumption

        # Calculate total
        health_score = sentiment_points + engagement_points + commitment_points + response_points + meeting_points

        conn.close()
        return round(health_score, 1)

    def analyze_sentiment_local(self, text: str) -> float:
        """
        Analyze sentiment using local LLM (CodeLlama 13B).

        Returns:
            Sentiment score (-1.0 to +1.0)
        """
        # Placeholder for CodeLlama integration
        # For now, use simple keyword-based sentiment
        positive_keywords = ['great', 'excellent', 'thanks', 'appreciate', 'good', 'perfect', 'happy']
        negative_keywords = ['issue', 'problem', 'concern', 'delay', 'unfortunately', 'apologize', 'sorry']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)

        if positive_count + negative_count == 0:
            return 0.0  # Neutral

        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return round(sentiment, 2)

    def update_metrics_for_stakeholder(self, stakeholder_id: int):
        """
        Update relationship metrics for stakeholder based on recent interactions.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get stakeholder email
        cursor.execute("SELECT email, name FROM stakeholders WHERE id = ?", (stakeholder_id,))
        stakeholder = cursor.fetchone()
        if not stakeholder:
            print(f"⚠️  Stakeholder ID {stakeholder_id} not found")
            conn.close()
            return

        email, name = stakeholder

        # Count interactions in last 30/60/90 days
        now = datetime.now()
        date_30d = (now - timedelta(days=30)).isoformat()
        date_60d = (now - timedelta(days=60)).isoformat()
        date_90d = (now - timedelta(days=90)).isoformat()

        cursor.execute('''
            SELECT
                COUNT(*) FILTER (WHERE interaction_date >= ?) as contacts_30d,
                COUNT(*) FILTER (WHERE interaction_date >= ?) as contacts_60d,
                COUNT(*) FILTER (WHERE interaction_date >= ?) as contacts_90d,
                AVG(sentiment_score) as avg_sentiment
            FROM interactions
            WHERE stakeholder_id = ?
        ''', (date_30d, date_60d, date_90d, stakeholder_id))

        metrics = cursor.fetchone()
        contacts_30d, contacts_60d, contacts_90d, avg_sentiment = metrics

        # Determine engagement level
        if contacts_30d >= 8:
            engagement_level = 'high'
        elif contacts_30d >= 3:
            engagement_level = 'medium'
        else:
            engagement_level = 'low'

        # Calculate sentiment trend
        cursor.execute('''
            SELECT AVG(sentiment_score)
            FROM interactions
            WHERE stakeholder_id = ? AND interaction_date >= ?
        ''', (stakeholder_id, date_30d))
        recent_sentiment = cursor.fetchone()[0] or 0

        if avg_sentiment and recent_sentiment > avg_sentiment + 0.1:
            sentiment_trend = 'improving'
        elif avg_sentiment and recent_sentiment < avg_sentiment - 0.1:
            sentiment_trend = 'declining'
        else:
            sentiment_trend = 'stable'

        # Insert metrics record
        cursor.execute('''
            INSERT INTO relationship_metrics (
                stakeholder_id, measured_at, sentiment_score, engagement_level,
                sentiment_trend, last_30_days_contacts, last_60_days_contacts, last_90_days_contacts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (stakeholder_id, now.isoformat(), avg_sentiment or 0, engagement_level,
              sentiment_trend, contacts_30d or 0, contacts_60d or 0, contacts_90d or 0))

        conn.commit()
        conn.close()

        print(f"✅ Updated metrics for {name}: {engagement_level} engagement, sentiment {sentiment_trend}")

    def generate_health_dashboard(self) -> str:
        """
        Generate terminal-based health dashboard showing all stakeholders.

        Returns:
            Dashboard markdown
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all stakeholders with latest metrics
        cursor.execute('''
            SELECT
                s.id, s.name, s.email, s.segment, s.organization,
                m.sentiment_score, m.engagement_level,
                m.sentiment_trend, m.last_30_days_contacts
            FROM stakeholders s
            LEFT JOIN (
                SELECT stakeholder_id, sentiment_score,
                       engagement_level, sentiment_trend, last_30_days_contacts,
                       ROW_NUMBER() OVER (PARTITION BY stakeholder_id ORDER BY measured_at DESC) as rn
                FROM relationship_metrics
            ) m ON s.id = m.stakeholder_id AND m.rn = 1
            ORDER BY s.name
        ''')

        stakeholder_rows = cursor.fetchall()
        conn.close()

        # Calculate health scores dynamically
        stakeholders = []
        for row in stakeholder_rows:
            sid, name, email, segment, org, sentiment, engagement, trend, contacts = row
            health = self.calculate_health_score(sid)
            stakeholders.append((sid, name, email, segment, org, health, sentiment, engagement, trend, contacts))

        # Sort by health score descending
        stakeholders = sorted(stakeholders, key=lambda x: x[5] if x[5] else 0, reverse=True)

        # Build dashboard
        dashboard = []
        dashboard.append("# Stakeholder Relationship Health Dashboard")
        dashboard.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        dashboard.append(f"**Total Stakeholders**: {len(stakeholders)}\n")

        # Group by health category
        categories = {
            'excellent': [],
            'good': [],
            'needs_attention': [],
            'at_risk': [],
            'no_data': []
        }

        for stakeholder in stakeholders:
            sid, name, email, segment, org, health, sentiment, engagement, trend, contacts = stakeholder

            if health is None:
                categories['no_data'].append(stakeholder)
            elif health >= 90:
                categories['excellent'].append(stakeholder)
            elif health >= 70:
                categories['good'].append(stakeholder)
            elif health >= 50:
                categories['needs_attention'].append(stakeholder)
            else:
                categories['at_risk'].append(stakeholder)

        # Render categories
        for category, label in [
            ('excellent', '🟢 Excellent (90-100)'),
            ('good', '🟡 Good (70-89)'),
            ('needs_attention', '🟠 Needs Attention (50-69)'),
            ('at_risk', '🔴 At Risk (<50)'),
            ('no_data', '⚪ No Data')
        ]:
            stakeholders_in_category = categories[category]
            if not stakeholders_in_category:
                continue

            dashboard.append(f"\n## {label} ({len(stakeholders_in_category)})")
            dashboard.append("\n| Name | Email | Segment | Health | Sentiment | Engagement | Trend | Contacts (30d) |")
            dashboard.append("|------|-------|---------|--------|-----------|------------|-------|----------------|")

            for stakeholder in stakeholders_in_category:
                sid, name, email, segment, org, health, sentiment, engagement, trend, contacts = stakeholder
                health_str = f"{health:.1f}" if health else "N/A"
                sentiment_str = f"{sentiment:+.2f}" if sentiment else "N/A"
                engagement_str = engagement or "N/A"
                trend_str = trend or "N/A"
                contacts_str = str(contacts or 0)

                dashboard.append(f"| {name} | {email} | {segment} | {health_str} | {sentiment_str} | {engagement_str} | {trend_str} | {contacts_str} |")

        return '\n'.join(dashboard)

    def get_stakeholder_context(self, stakeholder_id: int) -> Dict:
        """
        Get complete context for stakeholder (for pre-meeting prep).

        Returns:
            Dict with stakeholder profile, metrics, recent interactions, commitments
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get stakeholder profile
        cursor.execute("SELECT * FROM stakeholders WHERE id = ?", (stakeholder_id,))
        profile = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))

        # Get latest metrics
        cursor.execute('''
            SELECT * FROM relationship_metrics
            WHERE stakeholder_id = ?
            ORDER BY measured_at DESC LIMIT 1
        ''', (stakeholder_id,))
        result = cursor.fetchone()
        metrics = dict(zip([d[0] for d in cursor.description], result)) if result else {}

        # Get recent interactions (last 10)
        cursor.execute('''
            SELECT * FROM interactions
            WHERE stakeholder_id = ?
            ORDER BY interaction_date DESC LIMIT 10
        ''', (stakeholder_id,))
        interactions = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

        # Get pending commitments
        cursor.execute('''
            SELECT * FROM commitments
            WHERE stakeholder_id = ? AND status = 'pending'
            ORDER BY due_date
        ''', (stakeholder_id,))
        commitments = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

        conn.close()

        # Calculate health score
        health_score = self.calculate_health_score(stakeholder_id)

        return {
            'profile': profile,
            'metrics': metrics,
            'health_score': health_score,
            'recent_interactions': interactions,
            'pending_commitments': commitments
        }


def main():
    """CLI for stakeholder intelligence agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Stakeholder Relationship Intelligence Agent")
    parser.add_argument('command', choices=['discover', 'add', 'dashboard', 'context', 'update-metrics'],
                       help='Command to execute')
    parser.add_argument('--email', help='Stakeholder email')
    parser.add_argument('--name', help='Stakeholder name')
    parser.add_argument('--id', type=int, help='Stakeholder ID')
    parser.add_argument('--min-emails', type=int, default=3, help='Minimum email count for discovery')

    args = parser.parse_args()

    # Initialize agent
    agent = StakeholderIntelligenceAgent()

    if args.command == 'discover':
        stakeholders = agent.discover_stakeholders_from_email(min_email_count=args.min_emails)
        print(f"\n📊 Discovered {len(stakeholders)} stakeholders:")
        for s in stakeholders[:10]:  # Show top 10
            print(f"  - {s['name']} ({s['email']}) - {s['contact_count']} emails - {s['segment']}")

    elif args.command == 'add':
        if not args.email:
            print("❌ Error: --email required")
            return
        stakeholder_id = agent.add_stakeholder(args.email, name=args.name)
        print(f"✅ Stakeholder added with ID: {stakeholder_id}")

    elif args.command == 'dashboard':
        dashboard = agent.generate_health_dashboard()
        print(dashboard)

    elif args.command == 'context':
        if not args.id:
            print("❌ Error: --id required")
            return
        context = agent.get_stakeholder_context(args.id)
        print(json.dumps(context, indent=2))

    elif args.command == 'update-metrics':
        if not args.id:
            print("❌ Error: --id required")
            return
        agent.update_metrics_for_stakeholder(args.id)


if __name__ == '__main__':
    main()
