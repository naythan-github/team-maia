#!/usr/bin/env python3
"""
Personal Assistant Startup Routine
Comprehensive initialization with health checks, status summary, and daily briefing
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from automation_health_monitor import AutomationHealthMonitor
from macos_calendar_bridge import MacOSCalendarBridge
from trello_fast import TrelloFast


class PersonalAssistantStartup:
    def __init__(self):
        self.health_monitor = AutomationHealthMonitor()
        self.calendar = MacOSCalendarBridge()
        self.trello = TrelloFast()

    def check_dashboard_running(self) -> Dict:
        """Check if executive dashboard is running"""
        try:
            result = subprocess.run(
                ['lsof', '-ti', ':8070'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                return {
                    "running": True,
                    "pid": result.stdout.strip(),
                    "url": "http://127.0.0.1:8070"
                }
            else:
                return {"running": False}
        except Exception as e:
            return {"running": False, "error": str(e)}

    def start_dashboard(self) -> Dict:
        """Start executive dashboard if not running"""
        dashboard_script = Path(__file__).parent / "executive_command_dashboard.py"

        try:
            process = subprocess.Popen(
                ['python3', str(dashboard_script), '--port', '8070'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # Give it a moment to start
            import time
            time.sleep(2)

            # Verify it started
            check = self.check_dashboard_running()
            if check.get("running"):
                return {
                    "started": True,
                    "pid": check.get("pid"),
                    "url": "http://127.0.0.1:8070"
                }
            else:
                return {"started": False, "error": "Dashboard failed to start"}

        except Exception as e:
            return {"started": False, "error": str(e)}

    def get_todays_meetings(self) -> List[Dict]:
        """Get today's meetings from calendar"""
        try:
            events = self.calendar.get_today_events()
            # Filter out holidays and all-day events
            meetings = [e for e in events if not e.get('all_day')]
            return sorted(meetings, key=lambda x: x.get('start_date', ''))
        except Exception as e:
            return []

    def get_trello_summary(self) -> Dict:
        """Get Trello card summary"""
        try:
            everything = self.trello.get_everything()
            boards = everything.get('boards', [])

            total_cards = 0
            my_cards = 0

            for board in boards:
                lists = self.trello.get_lists(board['id'])
                for lst in lists:
                    cards = self.trello.get_cards(lst['id'])
                    total_cards += len(cards)

                    # Count cards in user's personal list (configurable via MAIA_TRELLO_LIST)
                    user_list = os.environ.get('MAIA_TRELLO_LIST', 'To Do').lower()
                    if lst['name'].lower() == user_list:
                        my_cards = len(cards)

            return {
                "total_cards": total_cards,
                "my_cards": my_cards,
                "boards_count": len(boards)
            }
        except Exception as e:
            return {"error": str(e)}

    def get_email_rag_status(self) -> Dict:
        """Get email RAG system status"""
        try:
            state_file = Path.home() / ".maia" / "email_rag_ollama" / "index_state.json"
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)
                indexed_count = len(state.get('indexed_emails', {}))
                return {
                    "indexed": indexed_count,
                    "last_index": state.get('last_index_time', 'Unknown')
                }
            return {"indexed": 0, "last_index": "Not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def get_vtt_intelligence_status(self) -> Dict:
        """Get VTT intelligence status"""
        try:
            intel_file = Path.home() / "git" / "maia" / "claude" / "data" / "vtt_intelligence.json"
            if intel_file.exists():
                with open(intel_file) as f:
                    intel = json.load(f)

                actions = intel.get('action_items', [])
                decisions = intel.get('decisions', [])
                meetings = intel.get('meetings', [])

                return {
                    "action_items": len(actions),
                    "decisions": len(decisions),
                    "meetings_processed": len(meetings)
                }
            return {"action_items": 0, "decisions": 0, "meetings_processed": 0}
        except Exception as e:
            return {"error": str(e)}

    def print_banner(self):
        """Print startup banner"""
        print("\n" + "="*80)
        print("🤖 PERSONAL ASSISTANT STARTUP")
        print("="*80)
        print(f"⏰ {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
        print()

    def print_health_status(self, health: Dict):
        """Print health status summary"""
        status = health.get('overall_status', 'unknown')
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'critical': '🔴'
        }

        print(f"🏥 SYSTEM HEALTH: {status_emoji.get(status, '❓')} {status.upper()}")
        print("-"*80)

        if health.get('alerts'):
            print(f"\n⚠️  Active Alerts: {len(health['alerts'])}")
            for alert in health['alerts'][:3]:  # Show top 3
                severity = alert.get('severity', 'UNKNOWN')
                automation = alert.get('automation', alert.get('data_file', 'Unknown'))
                issue = alert.get('issue', 'No details')
                print(f"   [{severity}] {automation}: {issue}")
        else:
            print("✅ All automations operational")

        print()

    def print_meetings_today(self, meetings: List[Dict]):
        """Print today's meetings"""
        print("📅 TODAY'S MEETINGS")
        print("-"*80)

        if not meetings:
            print("   No meetings scheduled today")
        else:
            for meeting in meetings[:5]:  # Show next 5
                subject = meeting.get('summary', 'No title')
                time = meeting.get('start_date', 'Unknown time')
                location = meeting.get('location', '')

                print(f"   • {subject}")
                print(f"     {time}")
                if location and 'Teams' in location:
                    print(f"     💻 Microsoft Teams")
                elif location:
                    print(f"     📍 {location[:50]}")
                print()

        print()

    def print_task_summary(self, trello: Dict, vtt: Dict):
        """Print task and intelligence summary"""
        print("📋 TASKS & INTELLIGENCE")
        print("-"*80)

        my_cards = trello.get('my_cards', 0)
        print(f"   Trello Cards (Your List): {my_cards}")

        action_items = vtt.get('action_items', 0)
        decisions = vtt.get('decisions', 0)
        meetings = vtt.get('meetings_processed', 0)

        print(f"   VTT Action Items: {action_items}")
        print(f"   VTT Decisions Tracked: {decisions}")
        print(f"   Meetings Processed: {meetings}")

        print()

    def print_email_status(self, email_rag: Dict):
        """Print email system status"""
        print("📧 EMAIL SYSTEM")
        print("-"*80)

        indexed = email_rag.get('indexed', 0)
        last_index = email_rag.get('last_index', 'Unknown')

        print(f"   Emails Indexed: {indexed}")
        if last_index != 'Unknown':
            try:
                # Parse timestamp
                last_time = datetime.fromisoformat(last_index)
                time_ago = datetime.now() - last_time
                hours_ago = time_ago.total_seconds() / 3600
                print(f"   Last Indexed: {hours_ago:.1f}h ago")
            except ValueError:
                print(f"   Last Indexed: {last_index}")

        print()

    def print_dashboard_status(self, dashboard: Dict):
        """Print dashboard status"""
        print("📊 EXECUTIVE DASHBOARD")
        print("-"*80)

        if dashboard.get('running'):
            print(f"   Status: ✅ Running (PID: {dashboard.get('pid')})")
            print(f"   URL: {dashboard.get('url')}")
        elif dashboard.get('started'):
            print(f"   Status: ✅ Started (PID: {dashboard.get('pid')})")
            print(f"   URL: {dashboard.get('url')}")
        else:
            print(f"   Status: ❌ Not running")
            if dashboard.get('error'):
                print(f"   Error: {dashboard.get('error')}")

        print()

    def run_startup(self):
        """Run complete startup routine"""
        self.print_banner()

        # 1. Health Check
        print("Running health check...")
        health = self.health_monitor.run_health_check()
        self.print_health_status(health)

        # 2. Dashboard Check
        dashboard = self.check_dashboard_running()
        if not dashboard.get('running'):
            print("Starting executive dashboard...")
            dashboard = self.start_dashboard()
        self.print_dashboard_status(dashboard)

        # 3. Today's Meetings
        meetings = self.get_todays_meetings()
        self.print_meetings_today(meetings)

        # 4. Email Status
        email_rag = self.get_email_rag_status()
        self.print_email_status(email_rag)

        # 5. Tasks & Intelligence
        trello = self.get_trello_summary()
        vtt = self.get_vtt_intelligence_status()
        self.print_task_summary(trello, vtt)

        # 6. Quick Actions
        print("🚀 QUICK ACTIONS")
        print("-"*80)
        print("   • Dashboard: http://127.0.0.1:8070")
        print("   • Health Check: claude/commands/check_automations.sh")
        print("   • Email Questions: claude/commands/check_email_questions.sh")
        print()

        print("="*80)
        print("✅ Personal Assistant Ready")
        print("="*80)
        print()


def main():
    startup = PersonalAssistantStartup()
    startup.run_startup()


if __name__ == '__main__':
    main()
