#!/usr/bin/env python3
"""
Trello Action Status Tracker
Syncs Trello card completion status back to intelligence databases

Author: Maia Personal Assistant Agent
Phase: 88 - Personal Assistant Automation Expansion
Date: 2025-10-03
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.trello_fast import TrelloFast


class TrelloStatusTracker:
    """Track Trello card completion and update intelligence databases"""

    def __init__(self):
        """Initialize status tracker"""
        self.trello = TrelloFast()
        self.vtt_intel_file = MAIA_ROOT / "claude" / "data" / "vtt_intelligence.json"
        self.conf_intel_file = MAIA_ROOT / "claude" / "data" / "confluence_intelligence.json"
        self.metrics_file = MAIA_ROOT / "claude" / "data" / "action_completion_metrics.json"

    def _load_vtt_intelligence(self) -> dict:
        """Load VTT intelligence database"""
        if self.vtt_intel_file.exists():
            with open(self.vtt_intel_file) as f:
                return json.load(f)
        return {"meetings": {}}

    def _save_vtt_intelligence(self, data: dict):
        """Save VTT intelligence database"""
        with open(self.vtt_intel_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_confluence_intelligence(self) -> dict:
        """Load Confluence intelligence database"""
        if self.conf_intel_file.exists():
            with open(self.conf_intel_file) as f:
                return json.load(f)
        return {"pages": {}}

    def _save_confluence_intelligence(self, data: dict):
        """Save Confluence intelligence database"""
        with open(self.conf_intel_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_metrics(self) -> dict:
        """Load completion metrics"""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                return json.load(f)
        return {
            "tracking_started": datetime.now().isoformat(),
            "weekly_completion": [],
            "overdue_alerts": []
        }

    def _save_metrics(self, metrics: dict):
        """Save completion metrics"""
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    def sync_board_status(self, board_id: str) -> dict:
        """Sync board card statuses back to intelligence databases"""
        print(f"🔄 Syncing Trello board {board_id}...")

        # Get all lists
        lists = self.trello.get_lists(board_id)

        # Load intelligence databases
        vtt_intel = self._load_vtt_intelligence()
        conf_intel = self._load_confluence_intelligence()
        metrics = self._load_metrics()

        updates = {
            "vtt_actions": {"completed": 0, "pending": 0, "overdue": 0},
            "confluence_actions": {"completed": 0, "pending": 0, "overdue": 0}
        }

        # Check each list
        for lst in lists:
            list_name = lst['name']
            cards = self.trello.get_cards_on_list(lst['id'])

            print(f"  📋 Processing list: {list_name} ({len(cards)} cards)")

            for card in cards:
                card_name = card['name']
                card_id = card['id']
                is_completed = card.get('dueComplete', False) or list_name.lower() in ['done', 'completed']
                due_date = card.get('due')

                # Auto-complete cards in "Done" list
                if list_name.lower() == 'done' and not card.get('closed', False):
                    completion_time = datetime.now().isoformat()
                    try:
                        # Update card: set due date to completion time, mark complete, archive
                        self.trello.update_card(
                            card_id=card_id,
                            due=completion_time,
                            dueComplete=True
                        )
                        self.trello.archive_card(card_id)
                        print(f"    📦 Auto-completed and archived: {card_name[:60]}")
                    except Exception as e:
                        print(f"    ⚠️  Failed to auto-complete {card_name[:40]}: {e}")

                # Try to match with VTT actions
                for meeting_key, meeting in vtt_intel.get("meetings", {}).items():
                    for action in meeting.get("results", {}).get("action_items", []):
                        if action['action'] in card_name:
                            old_status = action.get('status', 'pending')
                            if is_completed and old_status != 'completed':
                                action['status'] = 'completed'
                                action['completed_at'] = datetime.now().isoformat()
                                updates["vtt_actions"]["completed"] += 1
                                print(f"    ✅ Completed: {card_name[:60]}")
                            elif not is_completed:
                                action['status'] = 'pending'
                                updates["vtt_actions"]["pending"] += 1

                                # Check overdue
                                if due_date:
                                    from dateutil import parser
                                    import pytz
                                    due_dt = parser.parse(due_date)
                                    now = datetime.now(pytz.UTC) if due_dt.tzinfo else datetime.now()
                                    if due_dt < now and not is_completed:
                                        updates["vtt_actions"]["overdue"] += 1
                                        metrics["overdue_alerts"].append({
                                            "action": card_name,
                                            "due_date": due_date,
                                            "owner": action.get('owner'),
                                            "source": "vtt",
                                            "checked_at": datetime.now().isoformat()
                                        })

                # Try to match with Confluence actions
                for page_key, page in conf_intel.get("pages", {}).items():
                    for action in page.get("results", {}).get("action_items", []):
                        if action['action'] in card_name:
                            old_status = action.get('status', 'pending')
                            if is_completed and old_status != 'completed':
                                action['status'] = 'completed'
                                action['completed_at'] = datetime.now().isoformat()
                                updates["confluence_actions"]["completed"] += 1
                                print(f"    ✅ Completed: {card_name[:60]}")
                            elif not is_completed:
                                action['status'] = 'pending'
                                updates["confluence_actions"]["pending"] += 1

        # Save updated databases
        self._save_vtt_intelligence(vtt_intel)
        self._save_confluence_intelligence(conf_intel)

        # Update weekly metrics
        weekly_summary = {
            "week_of": datetime.now().strftime("%Y-%m-%d"),
            "synced_at": datetime.now().isoformat(),
            "vtt": updates["vtt_actions"],
            "confluence": updates["confluence_actions"],
            "total_completed": updates["vtt_actions"]["completed"] + updates["confluence_actions"]["completed"],
            "total_pending": updates["vtt_actions"]["pending"] + updates["confluence_actions"]["pending"],
            "total_overdue": updates["vtt_actions"]["overdue"] + updates["confluence_actions"]["overdue"]
        }

        metrics["weekly_completion"].append(weekly_summary)

        # Keep only last 12 weeks
        if len(metrics["weekly_completion"]) > 12:
            metrics["weekly_completion"] = metrics["weekly_completion"][-12:]

        # Keep only recent 50 overdue alerts
        if len(metrics["overdue_alerts"]) > 50:
            metrics["overdue_alerts"] = metrics["overdue_alerts"][-50:]

        self._save_metrics(metrics)

        return {
            "synced_at": datetime.now().isoformat(),
            "updates": updates,
            "weekly_summary": weekly_summary,
            "overdue_count": len([a for a in metrics["overdue_alerts"]
                                 if a.get('checked_at', '').startswith(datetime.now().strftime("%Y-%m-%d"))])
        }

    def get_completion_report(self) -> dict:
        """Generate completion report"""
        metrics = self._load_metrics()

        if not metrics.get("weekly_completion"):
            return {"error": "No tracking data available"}

        latest = metrics["weekly_completion"][-1]

        # Calculate trends
        if len(metrics["weekly_completion"]) >= 2:
            prev = metrics["weekly_completion"][-2]
            completion_trend = latest["total_completed"] - prev["total_completed"]
        else:
            completion_trend = 0

        return {
            "current_week": latest,
            "completion_trend": completion_trend,
            "overdue_actions": len([a for a in metrics.get("overdue_alerts", [])
                                   if not a.get('resolved')]),
            "total_weeks_tracked": len(metrics["weekly_completion"]),
            "average_weekly_completion": sum(w["total_completed"] for w in metrics["weekly_completion"]) / len(metrics["weekly_completion"])
        }


def main():
    """CLI entry"""
    import argparse
    parser = argparse.ArgumentParser(description="Trello action status tracker")
    parser.add_argument('--board', type=str, default="68de069e996bf03442ae5eea",
                       help='Trello board ID')
    parser.add_argument('--report', action='store_true', help='Show completion report')
    args = parser.parse_args()

    tracker = TrelloStatusTracker()

    if args.report:
        report = tracker.get_completion_report()
        print("\n" + "="*70)
        print("📊 ACTION COMPLETION REPORT")
        print("="*70)

        if "error" not in report:
            print(f"\n📅 Current Week: {report['current_week']['week_of']}")
            print(f"  ✅ Completed: {report['current_week']['total_completed']}")
            print(f"  ⏳ Pending: {report['current_week']['total_pending']}")
            print(f"  ⚠️  Overdue: {report['current_week']['total_overdue']}")
            print(f"\n📈 Trend: {'+' if report['completion_trend'] >= 0 else ''}{report['completion_trend']} from last week")
            print(f"📊 Average Weekly: {report['average_weekly_completion']:.1f} actions")
            print(f"🔍 Weeks Tracked: {report['total_weeks_tracked']}")
        else:
            print(f"\n⚠️  {report['error']}")
    else:
        result = tracker.sync_board_status(args.board)
        print("\n" + "="*70)
        print("📊 SYNC SUMMARY")
        print("="*70)
        print(f"\n✅ VTT Actions:")
        print(f"  • Completed: {result['updates']['vtt_actions']['completed']}")
        print(f"  • Pending: {result['updates']['vtt_actions']['pending']}")
        print(f"  • Overdue: {result['updates']['vtt_actions']['overdue']}")
        print(f"\n✅ Confluence Actions:")
        print(f"  • Completed: {result['updates']['confluence_actions']['completed']}")
        print(f"  • Pending: {result['updates']['confluence_actions']['pending']}")
        print(f"\n⚠️  Overdue Alerts Today: {result['overdue_count']}")
        print(f"\n💾 Metrics saved to: {tracker.metrics_file}")


if __name__ == "__main__":
    main()
