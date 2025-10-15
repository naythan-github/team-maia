#!/usr/bin/env python3
"""
Executive Information Manager Agent - Phase 2 Session 2

Complete GTD workflow orchestration with cross-system prioritization,
5-tier filtering, and intelligent morning ritual for executive efficiency.

Author: Maia (My AI Agent)
Created: 2025-10-13
Phase: 115 (Information Management System - Phase 2)
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import importlib.util

logger = logging.getLogger(__name__)

# Path setup
MAIA_ROOT = Path(os.environ.get('MAIA_ROOT', Path.home() / 'git' / 'maia' / 'claude'))

def import_module_from_path(module_name: str, file_path: Path):
    """Dynamic module import for cross-directory dependencies"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import Phase 1 systems
try:
    strategic_briefing_path = MAIA_ROOT / "tools" / "information_management" / "enhanced_daily_briefing_strategic.py"
    strategic_briefing = import_module_from_path("enhanced_daily_briefing_strategic", strategic_briefing_path)
    StrategicBriefing = strategic_briefing.StrategicDailyBriefing
except Exception as e:
    print(f"⚠️  Warning: Could not import strategic briefing: {e}")
    StrategicBriefing = None

try:
    action_tracker_path = MAIA_ROOT / "tools" / "productivity" / "unified_action_tracker_gtd.py"
    action_tracker = import_module_from_path("unified_action_tracker_gtd", action_tracker_path)
    GTDActionTracker = action_tracker.UnifiedActionTrackerGTD
except Exception as e:
    print(f"⚠️  Warning: Could not import GTD action tracker: {e}")
    GTDActionTracker = None


class ExecutiveInformationManager:
    """
    Complete GTD workflow orchestration with cross-system prioritization,
    5-tier filtering, and morning ritual automation.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize manager with integrations"""
        self.db_path = db_path or MAIA_ROOT / "data" / "databases" / "executive_information.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Phase 1 system integrations
        self.strategic_briefing = StrategicBriefing() if StrategicBriefing else None
        self.action_tracker = GTDActionTracker() if GTDActionTracker else None

    def _init_database(self):
        """Create database schema for information management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table 1: Information Items (unified inbox)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS information_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT,
                item_type TEXT,
                title TEXT,
                content TEXT,
                captured_at TEXT NOT NULL,
                processed_at TEXT,
                relevance_score REAL,
                priority_tier INTEGER,
                time_sensitivity TEXT,
                decision_impact TEXT,
                stakeholder_importance TEXT,
                strategic_alignment TEXT,
                gtd_status TEXT DEFAULT 'inbox',
                action_taken TEXT,
                routed_to TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table 2: Processing History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT NOT NULL,
                items_processed INTEGER,
                items_actioned INTEGER,
                items_delegated INTEGER,
                items_deferred INTEGER,
                items_archived INTEGER,
                processing_time_minutes INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table 3: Priority Rules (learned preferences)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS priority_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                adjustment_value REAL,
                confidence REAL,
                usage_count INTEGER DEFAULT 1,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        print(f"✅ Database initialized: {self.db_path}")

    def calculate_priority_score(self, item: Dict) -> Tuple[float, int]:
        """
        Calculate multi-factor priority score (0-100) and tier (1-5).

        Scoring Algorithm:
            - Decision impact: 0-30 points (high=30, medium=20, low=10, none=0)
            - Time urgency: 0-25 points (today=25, week=20, month=10, later=5)
            - Stakeholder tier: 0-25 points (executive=25, client=20, team=15, vendor=10, external=5)
            - Strategic alignment: 0-15 points (core=15, supporting=10, tangential=5, unrelated=0)
            - Potential value: 0-5 points (estimated business impact)

        Tiers:
            - Tier 1 (90-100): Critical - Immediate action required
            - Tier 2 (70-89): High - Schedule today/tomorrow
            - Tier 3 (50-69): Medium - This week
            - Tier 4 (30-49): Low - This month
            - Tier 5 (0-29): Noise - Archive/someday

        Returns:
            (score, tier)
        """
        score = 0.0

        # Component 1: Decision Impact (0-30 points)
        impact = item.get('decision_impact', 'none').lower()
        decision_points = {
            'high': 30,
            'strategic': 30,
            'medium': 20,
            'tactical': 20,
            'low': 10,
            'operational': 10,
            'none': 0
        }
        score += decision_points.get(impact, 0)

        # Component 2: Time Urgency (0-25 points)
        time_sensitivity = item.get('time_sensitivity', 'later').lower()
        if 'urgent' in time_sensitivity or 'today' in time_sensitivity:
            score += 25
        elif 'soon' in time_sensitivity or 'week' in time_sensitivity:
            score += 20
        elif 'month' in time_sensitivity:
            score += 10
        else:
            score += 5

        # Component 3: Stakeholder Importance (0-25 points)
        stakeholder = item.get('stakeholder_importance', 'external').lower()
        stakeholder_points = {
            'executive': 25,
            'ceo': 25,
            'leadership': 25,
            'client': 20,
            'customer': 20,
            'team': 15,
            'direct_report': 18,
            'vendor': 10,
            'partner': 10,
            'external': 5
        }
        score += max([v for k, v in stakeholder_points.items() if k in stakeholder] or [5])

        # Component 4: Strategic Alignment (0-15 points)
        alignment = item.get('strategic_alignment', 'unrelated').lower()
        alignment_points = {
            'core': 15,
            'primary': 15,
            'supporting': 10,
            'secondary': 10,
            'tangential': 5,
            'unrelated': 0
        }
        score += alignment_points.get(alignment, 0)

        # Component 5: Potential Value (0-5 points)
        # Simple heuristic based on keywords
        content = (item.get('title', '') + ' ' + item.get('content', '')).lower()
        if any(word in content for word in ['budget', 'revenue', 'cost', 'savings', 'efficiency']):
            score += 5
        elif any(word in content for word in ['improve', 'optimize', 'enhance']):
            score += 3

        # Apply learned rules (if any)
        score = self._apply_priority_rules(item, score)

        # Normalize to 0-100
        score = min(100, max(0, score))

        # Determine tier
        if score >= 90:
            tier = 1
        elif score >= 70:
            tier = 2
        elif score >= 50:
            tier = 3
        elif score >= 30:
            tier = 4
        else:
            tier = 5

        return round(score, 1), tier

    def _apply_priority_rules(self, item: Dict, base_score: float) -> float:
        """Apply learned priority rules to adjust score"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT rule_type, pattern, adjustment_value, confidence
            FROM priority_rules
            WHERE confidence > 0.5
            ORDER BY usage_count DESC
            LIMIT 20
        ''')

        rules = cursor.fetchall()
        conn.close()

        adjusted_score = base_score
        for rule_type, pattern, adjustment, confidence in rules:
            # Apply pattern matching
            if rule_type == 'keyword' and pattern.lower() in item.get('content', '').lower():
                adjusted_score += adjustment * confidence
            elif rule_type == 'sender' and pattern.lower() in item.get('source', '').lower():
                adjusted_score += adjustment * confidence

        return adjusted_score

    def capture_item(self, source: str, item_type: str, title: str,
                    content: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """
        Capture item into unified inbox with deduplication.

        Args:
            source: Where item came from (email, calendar, confluence, manual)
            item_type: Type of item (email, meeting, task, decision, question)
            title: Item title/subject
            content: Item content/body
            metadata: Additional metadata

        Returns:
            Item ID (or existing ID if duplicate)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        metadata = metadata or {}
        source_id = metadata.get('source_id')

        # Check for duplicates using source + source_id
        if source_id:
            cursor.execute('''
                SELECT id FROM information_items
                WHERE source = ? AND source_id = ?
                LIMIT 1
            ''', (source, source_id))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                # print(f"⏭️  Skipped duplicate: {title} (ID: {existing[0]})")
                return existing[0]

        cursor.execute('''
            INSERT INTO information_items (
                source, source_id, item_type, title, content, captured_at,
                time_sensitivity, decision_impact, stakeholder_importance, strategic_alignment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            source,
            metadata.get('source_id'),
            item_type,
            title,
            content,
            datetime.now().isoformat(),
            metadata.get('time_sensitivity', 'later'),
            metadata.get('decision_impact', 'none'),
            metadata.get('stakeholder_importance', 'external'),
            metadata.get('strategic_alignment', 'unrelated')
        ))

        item_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ Captured: {title} (ID: {item_id})")
        return item_id

    def process_inbox(self, max_items: int = 50) -> Dict:
        """
        Process items in inbox (GTD Clarify stage).

        Returns:
            Processing statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get unprocessed items
        cursor.execute('''
            SELECT id, source, item_type, title, content,
                   time_sensitivity, decision_impact, stakeholder_importance, strategic_alignment
            FROM information_items
            WHERE gtd_status = 'inbox'
            ORDER BY captured_at DESC
            LIMIT ?
        ''', (max_items,))

        items = cursor.fetchall()
        print(f"\n📥 Processing {len(items)} items from inbox...")

        stats = {
            'processed': 0,
            'actioned': 0,
            'delegated': 0,
            'deferred': 0,
            'archived': 0
        }

        for item in items:
            item_id = item[0]
            item_dict = {
                'id': item_id,
                'source': item[1],
                'item_type': item[2],
                'title': item[3],
                'content': item[4],
                'time_sensitivity': item[5],
                'decision_impact': item[6],
                'stakeholder_importance': item[7],
                'strategic_alignment': item[8]
            }

            # Calculate priority
            score, tier = self.calculate_priority_score(item_dict)

            # Update item with scores
            cursor.execute('''
                UPDATE information_items
                SET relevance_score = ?, priority_tier = ?, processed_at = ?
                WHERE id = ?
            ''', (score, tier, datetime.now().isoformat(), item_id))

            # Determine action based on tier
            if tier == 1:
                action = 'action_now'
                stats['actioned'] += 1
            elif tier == 2:
                action = 'schedule_today'
                stats['actioned'] += 1
            elif tier == 3:
                action = 'schedule_week'
                stats['deferred'] += 1
            elif tier == 4:
                action = 'schedule_month'
                stats['deferred'] += 1
            else:
                action = 'archive'
                stats['archived'] += 1

            # Update status
            cursor.execute('''
                UPDATE information_items
                SET gtd_status = 'processed', action_taken = ?
                WHERE id = ?
            ''', (action, item_id))

            stats['processed'] += 1

        conn.commit()
        conn.close()

        print(f"✅ Processed {stats['processed']} items: {stats['actioned']} actioned, {stats['deferred']} deferred, {stats['archived']} archived")
        return stats

    def generate_morning_ritual(self) -> str:
        """
        Generate 15-30 min morning ritual with tiered information.

        Morning Ritual Structure:
            1. Tier 1 (Critical): Immediate action items
            2. Tier 2 (High): Today's priorities
            3. Today's meetings with context
            4. Tier 3 (Medium): This week's items
            5. Quick wins (@quick-wins context)
            6. Waiting for updates (@waiting-for)

        Returns:
            Markdown ritual document
        """
        print("🌅 Generating morning ritual...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        ritual = []
        ritual.append("# Morning Ritual")
        ritual.append(f"\n**Generated**: {datetime.now().strftime('%A, %B %d, %Y at %H:%M')}")
        ritual.append(f"**Duration**: 15-30 minutes\n")

        ritual.append("---\n")

        # Section 1: Tier 1 - Critical Items (Immediate Action)
        cursor.execute('''
            SELECT id, source, title, relevance_score, action_taken
            FROM information_items
            WHERE priority_tier = 1 AND gtd_status != 'archived'
            ORDER BY relevance_score DESC
            LIMIT 10
        ''')
        tier1_items = cursor.fetchall()

        ritual.append("## 🔴 Tier 1: Critical - Immediate Action")
        ritual.append(f"**Count**: {len(tier1_items)} items\n")

        if tier1_items:
            for item in tier1_items:
                ritual.append(f"- [ ] **{item[2]}** (Score: {item[3]:.1f}) - *{item[1]}*")
                ritual.append(f"  - Action: {item[4]}")
        else:
            ritual.append("*No critical items - excellent!*")

        ritual.append("")

        # Section 2: Tier 2 - High Priority (Today)
        cursor.execute('''
            SELECT id, source, title, relevance_score, action_taken
            FROM information_items
            WHERE priority_tier = 2 AND gtd_status != 'archived'
            ORDER BY relevance_score DESC
            LIMIT 15
        ''')
        tier2_items = cursor.fetchall()

        ritual.append("\n## 🟡 Tier 2: High Priority - Schedule Today")
        ritual.append(f"**Count**: {len(tier2_items)} items\n")

        if tier2_items:
            for item in tier2_items:
                ritual.append(f"- [ ] {item[2]} (Score: {item[3]:.1f})")
        else:
            ritual.append("*All clear*")

        ritual.append("")

        # Section 3: Today's Meetings
        ritual.append("\n## 📅 Today's Meetings")

        # Get today's meetings from calendar
        try:
            calendar_bridge_path = MAIA_ROOT / "tools" / "macos_calendar_bridge.py"
            calendar_module = import_module_from_path("macos_calendar_bridge", calendar_bridge_path)
            calendar_bridge = calendar_module.MacOSCalendarBridge()

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            meetings = calendar_bridge.get_events_in_range(
                start=today_start.isoformat(),
                end=today_end.isoformat()
            )

            if meetings:
                ritual.append(f"**Count**: {len(meetings)} meetings\n")
                for meeting in meetings[:8]:  # Limit to 8
                    start_time = meeting.get('start', 'Unknown')
                    if 'T' in start_time:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        start_time = start_dt.strftime('%H:%M')

                    ritual.append(f"- **{start_time}** - {meeting.get('summary', 'Untitled')}")

                    # Show attendees if available
                    attendees = meeting.get('attendees', [])
                    if attendees:
                        attendee_names = [a.split('@')[0].replace('.', ' ').title() for a in attendees[:3]]
                        ritual.append(f"  - With: {', '.join(attendee_names)}")
            else:
                ritual.append("*No meetings scheduled - focus time available*")
        except Exception as e:
            logger.warning(f"Could not load today's meetings: {e}")
            ritual.append("*Meeting context unavailable*")

        ritual.append("")

        # Section 4: Tier 3 - Medium Priority (This Week)
        cursor.execute('''
            SELECT COUNT(*) FROM information_items
            WHERE priority_tier = 3 AND gtd_status != 'archived'
        ''')
        tier3_count = cursor.fetchone()[0]

        ritual.append(f"\n## 🟢 Tier 3: Medium Priority - This Week")
        ritual.append(f"**Count**: {tier3_count} items")
        ritual.append("*Review during weekly planning*\n")

        # Section 5: Quick Wins
        ritual.append("\n## ⚡ Quick Wins (<15 min)")
        ritual.append("*Items from GTD @quick-wins context*")
        ritual.append("*Perfect for between-meeting gaps*\n")

        # Section 6: Waiting For
        ritual.append("\n## ⏳ Waiting For")
        ritual.append("*Items from GTD @waiting-for context*")
        ritual.append("*Follow up on blocked items*\n")

        # Section 7: Daily Summary
        cursor.execute('SELECT COUNT(*) FROM information_items WHERE gtd_status = "inbox"')
        inbox_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM information_items WHERE priority_tier <= 3 AND gtd_status != "archived"')
        active_count = cursor.fetchone()[0]

        ritual.append("\n---")
        ritual.append("\n## 📊 System Status")
        ritual.append(f"- **Inbox**: {inbox_count} unprocessed items")
        ritual.append(f"- **Active Items**: {active_count} (Tiers 1-3)")
        ritual.append(f"- **Critical**: {len(tier1_items)} items")
        ritual.append(f"- **High Priority**: {len(tier2_items)} items")

        conn.close()

        return '\n'.join(ritual)

    def generate_batch_recommendations(self, available_time_min: int = 60,
                                       energy_level: str = 'medium') -> List[Dict]:
        """
        Generate batch processing recommendations based on available time and energy.

        Args:
            available_time_min: Available time in minutes
            energy_level: Current energy level (high, medium, low)

        Returns:
            List of recommended batches
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        recommendations = []

        # High energy = Tier 1 + 2 items (deep work)
        if energy_level == 'high':
            cursor.execute('''
                SELECT id, title, relevance_score, priority_tier
                FROM information_items
                WHERE priority_tier IN (1, 2) AND gtd_status != 'archived'
                ORDER BY relevance_score DESC
                LIMIT ?
            ''', (available_time_min // 15,))  # Assume 15 min per item

            items = cursor.fetchall()
            if items:
                recommendations.append({
                    'batch_name': 'High-Impact Deep Work',
                    'energy': 'high',
                    'estimated_time': len(items) * 15,
                    'items': [{'id': i[0], 'title': i[1], 'score': i[2]} for i in items]
                })

        # Medium energy = Tier 2 + 3 items (regular work)
        elif energy_level == 'medium':
            cursor.execute('''
                SELECT id, title, relevance_score, priority_tier
                FROM information_items
                WHERE priority_tier IN (2, 3) AND gtd_status != 'archived'
                ORDER BY relevance_score DESC
                LIMIT ?
            ''', (available_time_min // 12,))

            items = cursor.fetchall()
            if items:
                recommendations.append({
                    'batch_name': 'Regular Priority Work',
                    'energy': 'medium',
                    'estimated_time': len(items) * 12,
                    'items': [{'id': i[0], 'title': i[1], 'score': i[2]} for i in items]
                })

        # Low energy = Quick wins (administrative tasks)
        else:
            cursor.execute('''
                SELECT id, title, relevance_score, priority_tier
                FROM information_items
                WHERE priority_tier >= 3 AND gtd_status != 'archived'
                ORDER BY relevance_score ASC
                LIMIT ?
            ''', (available_time_min // 5,))  # 5 min quick tasks

            items = cursor.fetchall()
            if items:
                recommendations.append({
                    'batch_name': 'Quick Wins & Admin',
                    'energy': 'low',
                    'estimated_time': len(items) * 5,
                    'items': [{'id': i[0], 'title': i[1], 'score': i[2]} for i in items]
                })

        conn.close()

        print(f"💡 Generated {len(recommendations)} batch recommendations for {available_time_min} min at {energy_level} energy")
        return recommendations

    def get_tier_summary(self) -> Dict:
        """Get summary of items by tier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT priority_tier, COUNT(*), AVG(relevance_score)
            FROM information_items
            WHERE gtd_status != 'archived'
            GROUP BY priority_tier
            ORDER BY priority_tier
        ''')

        tiers = {}
        for tier, count, avg_score in cursor.fetchall():
            tier_name = {
                1: 'Critical',
                2: 'High',
                3: 'Medium',
                4: 'Low',
                5: 'Noise'
            }.get(tier, 'Unknown')

            tiers[tier] = {
                'name': tier_name,
                'count': count,
                'avg_score': round(avg_score, 1) if avg_score else 0
            }

        conn.close()
        return tiers


def main():
    """CLI for executive information manager"""
    import argparse

    parser = argparse.ArgumentParser(description="Executive Information Manager")
    parser.add_argument('command', choices=['capture', 'process', 'morning', 'batch', 'summary'],
                       help='Command to execute')
    parser.add_argument('--title', help='Item title (for capture)')
    parser.add_argument('--content', help='Item content (for capture)')
    parser.add_argument('--source', default='manual', help='Item source')
    parser.add_argument('--type', default='task', help='Item type')
    parser.add_argument('--time', type=int, default=60, help='Available time in minutes (for batch)')
    parser.add_argument('--energy', default='medium', choices=['high', 'medium', 'low'],
                       help='Energy level (for batch)')

    args = parser.parse_args()

    # Initialize manager
    manager = ExecutiveInformationManager()

    if args.command == 'capture':
        if not args.title:
            print("❌ Error: --title required")
            return
        item_id = manager.capture_item(args.source, args.type, args.title, args.content)
        print(f"✅ Item captured with ID: {item_id}")

    elif args.command == 'process':
        stats = manager.process_inbox()
        print(f"\n📊 Processing complete:")
        print(f"  - Processed: {stats['processed']}")
        print(f"  - Actioned: {stats['actioned']}")
        print(f"  - Deferred: {stats['deferred']}")
        print(f"  - Archived: {stats['archived']}")

    elif args.command == 'morning':
        ritual = manager.generate_morning_ritual()
        print(ritual)

    elif args.command == 'batch':
        recommendations = manager.generate_batch_recommendations(args.time, args.energy)
        for rec in recommendations:
            print(f"\n💼 {rec['batch_name']}")
            print(f"   Energy: {rec['energy']}, Time: {rec['estimated_time']} min")
            print(f"   Items: {len(rec['items'])}")

    elif args.command == 'summary':
        tiers = manager.get_tier_summary()
        print("\n📊 Tier Summary:")
        for tier_num, data in tiers.items():
            print(f"  Tier {tier_num} ({data['name']}): {data['count']} items (avg score: {data['avg_score']})")


if __name__ == '__main__':
    main()
