#!/usr/bin/env python3
"""
Weekly Backlog Review - Surface backlog items and suggest prioritization
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from trello_fast import TrelloFast


class WeeklyBacklogReview:
    def __init__(self):
        self.trello = TrelloFast()
        self.board_id = "68de069e996bf03442ae5eea"

    def get_backlog_items(self) -> List[Dict]:
        """Get all items from Backlog list"""
        lists = self.trello.get_lists(self.board_id)

        backlog_list = None
        for lst in lists:
            if lst['name'].lower() == 'backlog':
                backlog_list = lst
                break

        if not backlog_list:
            return []

        cards = self.trello.get_cards(backlog_list['id'])
        return cards

    def categorize_backlog(self, items: List[Dict]) -> Dict:
        """Categorize backlog items by type"""
        categories = {
            'strategic': [],
            'technical': [],
            'operational': [],
            'documentation': [],
            'other': []
        }

        for item in items:
            name = item.get('name', '').lower()
            desc = item.get('desc', '').lower()

            if any(word in name or word in desc for word in ['strategic', 'evaluate', 'decision', 'event']):
                categories['strategic'].append(item)
            elif any(word in name or word in desc for word in ['fix', 'technical', 'enhancement', 'self-healing']):
                categories['technical'].append(item)
            elif any(word in name or word in desc for word in ['audit', 'meeting', 'review', 'boundary']):
                categories['operational'].append(item)
            elif any(word in name or word in desc for word in ['document', 'architecture', 'runbook']):
                categories['documentation'].append(item)
            else:
                categories['other'].append(item)

        return categories

    def generate_review_report(self) -> str:
        """Generate weekly backlog review report"""
        items = self.get_backlog_items()

        if not items:
            return "📋 Backlog is empty - all clear!"

        categories = self.categorize_backlog(items)

        report = []
        report.append("\n" + "="*80)
        report.append("📋 WEEKLY BACKLOG REVIEW")
        report.append("="*80)
        report.append(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
        report.append(f"📊 Total Items: {len(items)}\n")

        # Strategic items (highest priority)
        if categories['strategic']:
            report.append("🎯 STRATEGIC ITEMS (High Priority)")
            report.append("-"*80)
            for i, item in enumerate(categories['strategic'], 1):
                report.append(f"{i}. {item['name']}")
                # Extract first line of description
                desc_lines = item.get('desc', '').split('\n')
                first_line = next((line for line in desc_lines if line.strip()), '')
                if first_line:
                    report.append(f"   {first_line[:70]}")
            report.append("")

        # Operational items
        if categories['operational']:
            report.append("📊 OPERATIONAL FOLLOW-UPS")
            report.append("-"*80)
            for i, item in enumerate(categories['operational'], 1):
                report.append(f"{i}. {item['name']}")
            report.append("")

        # Technical debt
        if categories['technical']:
            report.append("🔧 TECHNICAL DEBT")
            report.append("-"*80)
            for i, item in enumerate(categories['technical'], 1):
                report.append(f"{i}. {item['name']}")
            report.append("")

        # Documentation
        if categories['documentation']:
            report.append("📚 DOCUMENTATION")
            report.append("-"*80)
            for i, item in enumerate(categories['documentation'], 1):
                report.append(f"{i}. {item['name']}")
            report.append("")

        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-"*80)

        if categories['strategic']:
            report.append("• Focus on strategic items this week - highest business impact")

        if len(categories['operational']) > 3:
            report.append("• Operational backlog growing - schedule time to clear action items")

        if len(categories['technical']) > 2:
            report.append("• Technical debt accumulating - allocate time for system improvements")

        if len(items) > 10:
            report.append(f"• Backlog has {len(items)} items - consider archiving completed or deprioritized tasks")

        report.append("\n" + "="*80)
        report.append("💬 Review these items and move high-priority ones to 'This Week' or 'Today'")
        report.append("="*80 + "\n")

        return '\n'.join(report)

    def suggest_this_week(self) -> List[Dict]:
        """Suggest items to move to 'This Week'"""
        items = self.get_backlog_items()
        categories = self.categorize_backlog(items)

        suggestions = []

        # Always suggest strategic items
        suggestions.extend(categories['strategic'][:2])  # Top 2 strategic

        # Suggest oldest operational items
        operational_sorted = sorted(
            categories['operational'],
            key=lambda x: x.get('dateLastActivity', ''),
            reverse=False  # Oldest first
        )
        suggestions.extend(operational_sorted[:1])  # Top 1 operational

        return suggestions

    def run_review(self, show_suggestions: bool = True):
        """Run weekly backlog review"""
        print(self.generate_review_report())

        if show_suggestions:
            suggestions = self.suggest_this_week()
            if suggestions:
                print("\n🎯 SUGGESTED FOR THIS WEEK:")
                print("-"*80)
                for i, item in enumerate(suggestions, 1):
                    print(f"{i}. {item['name']}")
                print("\nUse these as starting points for weekly planning.")
                print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Weekly backlog review")
    parser.add_argument('--no-suggestions', action='store_true', help='Skip suggestions')

    args = parser.parse_args()

    review = WeeklyBacklogReview()
    review.run_review(show_suggestions=not args.no_suggestions)


if __name__ == '__main__':
    main()
