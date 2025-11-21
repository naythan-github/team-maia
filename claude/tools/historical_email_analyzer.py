#!/usr/bin/env python3
"""
Historical Email Analyzer - One-time Gemma2 9B Analysis
Analyze last N days of emails to find missed action items and baseline sentiment

Usage:
    python3 historical_email_analyzer.py --days 30
    python3 historical_email_analyzer.py --days 7 --output report.md

Author: Maia System
Created: 2025-11-21
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.morning_email_intelligence_local import MorningEmailIntelligence
from claude.tools.macos_mail_bridge import MacOSMailBridge


class HistoricalEmailAnalyzer:
    """One-time analysis of historical emails with Gemma2 9B"""

    def __init__(self, days: int = 30):
        """Initialize analyzer"""
        self.days = days
        self.intelligence = MorningEmailIntelligence()
        self.mail_bridge = MacOSMailBridge()

        print(f"\n{'='*70}")
        print(f"📧 Historical Email Analyzer - Last {days} Days")
        print(f"{'='*70}")
        print(f"Model: Gemma2 9B (Local)")
        print(f"Cost: $0.00")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def fetch_historical_emails(self) -> List[Dict[str, Any]]:
        """Fetch emails from last N days"""
        print(f"📥 Fetching emails from last {self.days} days...")

        emails = []
        hours_ago = self.days * 24

        # Fetch Inbox
        try:
            inbox = self.mail_bridge.get_inbox_messages(limit=500, hours_ago=hours_ago)
            print(f"   Inbox: {len(inbox)} emails")
            emails.extend(inbox)
        except Exception as e:
            print(f"   ⚠️  Inbox fetch error: {e}")

        # Fetch Sent
        try:
            sent = self.mail_bridge.get_sent_messages(limit=500, hours_ago=hours_ago)
            print(f"   Sent: {len(sent)} emails")
            emails.extend(sent)
        except Exception as e:
            print(f"   ⚠️  Sent fetch error: {e}")

        # Sort by date (newest first)
        emails.sort(key=lambda e: e.get("date", ""), reverse=True)

        print(f"\n✅ Total emails retrieved: {len(emails)}")
        return emails

    def analyze_batch(self, emails: List[Dict], batch_size: int = 50) -> Dict:
        """Analyze emails in batches to show progress"""
        total = len(emails)
        results = {
            "categorized": {"urgent": [], "project": [], "fyi": []},
            "action_items": [],
            "sentiment": {}
        }

        print(f"\n🤖 Analyzing {total} emails with Gemma2 9B...")
        print(f"   Batch size: {batch_size} emails")
        print(f"   Estimated time: {(total / batch_size) * 15:.0f}-{(total / batch_size) * 25:.0f} seconds\n")

        for i in range(0, total, batch_size):
            batch = emails[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} emails)...")

            # Categorize
            categorized = self.intelligence._categorize_with_gemma2(batch)
            results["categorized"]["urgent"].extend(categorized["urgent"])
            results["categorized"]["project"].extend(categorized["project"])
            results["categorized"]["fyi"].extend(categorized["fyi"])

            # Extract action items from urgent emails
            if categorized["urgent"]:
                actions = self.intelligence._extract_action_items_with_gemma2(categorized["urgent"])
                results["action_items"].extend(actions)

            # Analyze sentiment for all emails in batch
            sentiment = self.intelligence._analyze_sentiment_with_gemma2(batch)
            results["sentiment"].update(sentiment)

        print(f"\n✅ Analysis complete!")
        print(f"   URGENT: {len(results['categorized']['urgent'])}")
        print(f"   PROJECT: {len(results['categorized']['project'])}")
        print(f"   FYI: {len(results['categorized']['fyi'])}")
        print(f"   Action Items: {len(results['action_items'])}")
        print(f"   Sentiment Analyzed: {len(results['sentiment'])} senders")

        return results

    def generate_report(self, results: Dict, emails: List[Dict]) -> str:
        """Generate comprehensive markdown report"""
        now = datetime.now()
        cutoff = now - timedelta(days=self.days)

        report = f"""# Historical Email Analysis Report

**Analysis Period**: {cutoff.strftime('%B %d, %Y')} → {now.strftime('%B %d, %Y')} ({self.days} days)
**Generated**: {now.strftime('%A, %B %d, %Y at %I:%M %p')}
**Model**: Gemma2 9B (Local)
**Emails Analyzed**: {len(emails)}
**Cost**: $0.00

---

## 📊 Executive Summary

### Email Distribution
- 🚨 **URGENT**: {len(results['categorized']['urgent'])} emails ({len(results['categorized']['urgent'])/len(emails)*100:.1f}%)
- 📊 **PROJECT**: {len(results['categorized']['project'])} emails ({len(results['categorized']['project'])/len(emails)*100:.1f}%)
- 📨 **FYI**: {len(results['categorized']['fyi'])} emails ({len(results['categorized']['fyi'])/len(emails)*100:.1f}%)

### Key Findings
- 📋 **Action Items Extracted**: {len(results['action_items'])}
- 😊 **Relationships Tracked**: {len(results['sentiment'])} key contacts
- 🔴 **At-Risk Relationships**: {len([s for s, d in results['sentiment'].items() if d.get('relationship_health', 75) < 60])}

---

## 🚨 URGENT EMAILS FOUND ({len(results['categorized']['urgent'])})

"""

        # Show urgent emails (up to 20)
        for i, email in enumerate(results['categorized']['urgent'][:20], 1):
            sender = email.get("sender", "Unknown")
            subject = email.get("subject", "No Subject")
            date = email.get("date", "")[:19]

            report += f"""{i}. **{subject}**
   From: {sender} | {date}

"""

        if len(results['categorized']['urgent']) > 20:
            report += f"\n... and {len(results['categorized']['urgent']) - 20} more urgent emails\n"

        # Action items section
        if results['action_items']:
            report += f"""
---

## 📋 ACTION ITEMS FOUND ({len(results['action_items'])})

**⚠️ Review these for missed commitments:**

"""
            for i, action in enumerate(results['action_items'][:30], 1):
                priority_emoji = "🔴" if action.get("priority") == "HIGH" else "🟡"
                report += f"""{i}. {priority_emoji} **{action['task']}**
   - Requested by: {action['sender']}
   - Deadline: {action['deadline']}
   - Priority: {action['priority']}
   - Context: {action.get('context', 'N/A')}

"""

            if len(results['action_items']) > 30:
                report += f"\n... and {len(results['action_items']) - 30} more action items\n"

        # Relationship health section
        if results['sentiment']:
            report += f"""
---

## 📈 RELATIONSHIP HEALTH ANALYSIS

**Baseline sentiment scores for key stakeholders:**

"""
            # Sort by health score (lowest first - most at risk)
            sorted_sentiment = sorted(
                results['sentiment'].items(),
                key=lambda x: x[1].get('relationship_health', 75)
            )

            for sender, data in sorted_sentiment[:20]:
                health = data.get("relationship_health", 75)
                health_emoji = "🟢" if health >= 75 else "🟡" if health >= 60 else "🔴"
                sentiment = data.get("sentiment", "NEUTRAL")
                signals = data.get("signals", [])

                report += f"""### {sender}
{health_emoji} **Health Score**: {health}/100 | Sentiment: {sentiment}

**Signals Detected**:
{chr(10).join(f'- {signal}' for signal in signals) if signals else '- No specific signals'}

**Recommended Action**: {data.get('recommended_action', 'Continue monitoring')}

---

"""

        # Project emails summary
        report += f"""
## 📊 PROJECT UPDATES ({len(results['categorized']['project'])})

"""
        # Group by sender
        project_by_sender = {}
        for email in results['categorized']['project']:
            sender = email.get("sender", "Unknown")
            if sender not in project_by_sender:
                project_by_sender[sender] = []
            project_by_sender[sender].append(email)

        # Show top 10 senders
        top_senders = sorted(project_by_sender.items(), key=lambda x: len(x[1]), reverse=True)[:10]

        for sender, sender_emails in top_senders:
            report += f"""### {sender} ({len(sender_emails)} emails)

Recent subjects:
"""
            for email in sender_emails[:5]:
                subject = email.get("subject", "No Subject")
                date = email.get("date", "")[:10]
                report += f"- {subject} ({date})\n"

            if len(sender_emails) > 5:
                report += f"  ... and {len(sender_emails) - 5} more\n"

            report += "\n"

        # FYI summary
        report += f"""
---

## 📨 FYI EMAILS ({len(results['categorized']['fyi'])})

Low priority informational emails (newsletters, notifications, etc.)

**Top Sources**:
"""
        # Group FYI by sender
        fyi_by_sender = {}
        for email in results['categorized']['fyi']:
            sender = email.get("sender", "Unknown")
            if sender not in fyi_by_sender:
                fyi_by_sender[sender] = 0
            fyi_by_sender[sender] += 1

        top_fyi = sorted(fyi_by_sender.items(), key=lambda x: x[1], reverse=True)[:10]
        for sender, count in top_fyi:
            report += f"- {sender}: {count} emails\n"

        # Footer with stats
        report += f"""

---

## 💡 NEXT STEPS

### Immediate Actions
1. **Review {len(results['action_items'])} action items** - Check for missed commitments
2. **Address {len([s for s, d in results['sentiment'].items() if d.get('relationship_health', 75) < 60])} at-risk relationships** - Follow up with low health scores
3. **Process {len(results['categorized']['urgent'])} urgent emails** - Ensure nothing critical was missed

### Going Forward
- ✅ **Hourly Email Intelligence** now active
- ✅ **Gemma2 9B** analyzing all new emails automatically
- ✅ **Desktop brief** updates every hour at `~/Desktop/EMAIL_INTELLIGENCE_BRIEF.md`
- ✅ **Zero cost** with local models

### Historical Context Established
- Baseline relationship health scores captured
- Historical action item patterns identified
- Email volume and sender patterns documented

---

*Generated by Maia Historical Email Analyzer*
*One-time analysis | Future emails handled by hourly automation*
*Model: Gemma2 9B (Local) | Cost: $0.00*
"""

        return report

    def run_analysis(self, output_file: str = None) -> str:
        """Run complete analysis and save report"""
        start_time = datetime.now()

        # Step 1: Fetch emails
        emails = self.fetch_historical_emails()

        if not emails:
            print("\n⚠️  No emails found in the specified timeframe")
            return ""

        # Step 2: Analyze with Gemma2
        results = self.analyze_batch(emails, batch_size=50)

        # Step 3: Generate report
        print(f"\n📝 Generating report...")
        report = self.generate_report(results, emails)

        # Step 4: Save to file
        if not output_file:
            output_file = str(Path.home() / "Desktop" / f"EMAIL_ANALYSIS_{self.days}DAYS_{datetime.now().strftime('%Y%m%d')}.md")

        output_path = Path(output_file)
        output_path.write_text(report)

        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ Analysis complete!")
        print(f"📄 Report saved: {output_path}")
        print(f"⏱️  Total time: {elapsed:.0f} seconds ({elapsed/60:.1f} minutes)")
        print(f"💰 Total cost: $0.00 (100% local)")
        print(f"\n{'='*70}\n")

        return str(output_path)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Analyze historical emails with Gemma2 9B")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")
    parser.add_argument("--output", type=str, help="Output file path (default: ~/Desktop/EMAIL_ANALYSIS_*.md)")

    args = parser.parse_args()

    try:
        analyzer = HistoricalEmailAnalyzer(days=args.days)
        analyzer.run_analysis(output_file=args.output)
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
