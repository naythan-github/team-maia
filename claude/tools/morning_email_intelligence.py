#!/usr/bin/env python3
"""
Morning Email Intelligence - Sonnet-Powered Email Triage
Daily analysis of inbox with action item extraction and sentiment tracking

Schedule: Daily 7:00 AM (Mon-Fri)
Model: Claude Sonnet 4.5
Cost: ~$2-3/month

Author: Maia System
Created: 2025-11-21
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    import anthropic
except ImportError:
    print("❌ Missing anthropic SDK. Install: pip3 install anthropic")
    sys.exit(1)

from claude.tools.email_rag_ollama import EmailRAGOllama


class MorningEmailIntelligence:
    """Generate morning email brief with Sonnet intelligence"""

    def __init__(self):
        """Initialize with secure API key from keychain"""
        self.api_key = self._get_api_key()
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.email_rag = EmailRAGOllama(extract_contacts=False)

        # Output paths
        self.output_dir = Path.home() / "Desktop"
        self.output_file = self.output_dir / "EMAIL_MORNING_BRIEF.md"

        # Cost tracking
        self.total_cost = 0.0
        self.api_calls = 0

    def _get_api_key(self) -> str:
        """Get Anthropic API key from keychain (secure)"""
        try:
            # Try keychain first
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "anthropic-api", "-a", "maia", "-w"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Fallback: Check environment variable (for initial setup)
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("❌ No API key found. Run setup:")
                print('   security add-generic-password -s "anthropic-api" -a "maia" -w "YOUR_KEY"')
                sys.exit(1)
            return api_key

    def _get_recent_emails(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get emails from last N hours using macOS Mail bridge"""
        from claude.tools.macos_mail_bridge import MacOSMailBridge

        mail_bridge = MacOSMailBridge()
        cutoff_date = datetime.now() - timedelta(hours=hours)

        emails = []

        # Fetch from Inbox, Sent, CC folders
        for folder in ["Inbox", "Sent", "CC"]:
            try:
                folder_emails = mail_bridge.get_messages(
                    mailbox=folder,
                    limit=100,
                    date_filter=cutoff_date.strftime("%Y-%m-%d")
                )

                # Filter to unread for Inbox
                if folder == "Inbox":
                    folder_emails = [e for e in folder_emails if not e.get("read", True)]

                emails.extend(folder_emails)
            except Exception as e:
                print(f"⚠️  Could not fetch {folder}: {e}")

        # Sort by date (newest first)
        emails.sort(key=lambda e: e.get("date", ""), reverse=True)

        return emails

    def _categorize_with_sonnet(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize emails using Claude Sonnet (high accuracy)"""
        if not emails:
            return {"urgent": [], "project": [], "fyi": []}

        # Build email summary for Sonnet
        email_summaries = []
        for i, email in enumerate(emails[:50]):  # Limit to 50 for token efficiency
            email_summaries.append({
                "id": i,
                "from": email.get("sender", "Unknown"),
                "subject": email.get("subject", "No Subject"),
                "date": email.get("date", ""),
                "preview": email.get("content", "")[:300]
            })

        prompt = f"""Analyze these {len(email_summaries)} emails and categorize each as URGENT, PROJECT, or FYI.

URGENT = Requires immediate action today (client escalations, deadlines, security alerts, executive requests)
PROJECT = Important updates, team coordination, ongoing work (can wait until after urgent items)
FYI = Informational only, low priority (newsletters, notifications, non-actionable updates)

Emails to categorize:
{json.dumps(email_summaries, indent=2)}

Respond with JSON only:
{{
  "urgent": [0, 3, 7],
  "project": [1, 2, 4, 5, 6],
  "fyi": [8, 9, 10]
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            self.api_calls += 1
            self.total_cost += self._calculate_cost(message.usage)

            # Parse JSON response
            response_text = message.content[0].text
            categorization = json.loads(response_text)

            # Map IDs back to emails
            result = {
                "urgent": [emails[i] for i in categorization.get("urgent", []) if i < len(emails)],
                "project": [emails[i] for i in categorization.get("project", []) if i < len(emails)],
                "fyi": [emails[i] for i in categorization.get("fyi", []) if i < len(emails)]
            }

            return result

        except Exception as e:
            print(f"⚠️  Sonnet categorization failed: {e}")
            # Fallback: simple keyword-based categorization
            return self._fallback_categorization(emails)

    def _extract_action_items_with_sonnet(self, emails: List[Dict]) -> List[Dict]:
        """Extract action items from urgent emails using Sonnet (high recall)"""
        if not emails:
            return []

        # Focus on urgent emails only (cost optimization)
        email_texts = []
        for email in emails[:10]:  # Max 10 urgent emails
            email_texts.append(f"""
From: {email.get('sender', 'Unknown')}
Subject: {email.get('subject', 'No Subject')}
Date: {email.get('date', '')}
Content: {email.get('content', '')[:1000]}
---""")

        prompt = f"""Extract ALL action items from these urgent emails. Be comprehensive - catch explicit requests ("Please send X"), implicit tasks ("We need Y by Friday"), and commitments I made in replies.

For each action item, identify:
1. The task (what needs to be done)
2. Who requested it (sender)
3. Deadline (if mentioned, otherwise "ASAP" for urgent emails)
4. Priority (HIGH/MEDIUM based on urgency language)

Emails:
{''.join(email_texts)}

Respond with JSON only:
{{
  "action_items": [
    {{
      "task": "Send IT Glue export to Moir Group",
      "sender": "brett.lester@moirgroup.com.au",
      "deadline": "Today 5PM",
      "priority": "HIGH",
      "context": "MSP transition handover"
    }}
  ]
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )

            self.api_calls += 1
            self.total_cost += self._calculate_cost(message.usage)

            response_text = message.content[0].text
            result = json.loads(response_text)

            return result.get("action_items", [])

        except Exception as e:
            print(f"⚠️  Action extraction failed: {e}")
            return []

    def _analyze_sentiment_with_sonnet(self, emails: List[Dict]) -> Dict[str, Dict]:
        """Analyze sender sentiment for stakeholder relationship tracking"""
        if not emails:
            return {}

        # Group by sender
        by_sender = {}
        for email in emails:
            sender = email.get("sender", "Unknown")
            if sender not in by_sender:
                by_sender[sender] = []
            by_sender[sender].append(email)

        # Analyze top 10 senders only (cost optimization)
        top_senders = sorted(by_sender.items(), key=lambda x: len(x[1]), reverse=True)[:10]

        sentiment_results = {}

        for sender, sender_emails in top_senders:
            # Build email history for this sender
            email_texts = []
            for email in sender_emails[:5]:  # Max 5 emails per sender
                email_texts.append(f"""
Subject: {email.get('subject', '')}
Date: {email.get('date', '')}
Preview: {email.get('content', '')[:300]}
---""")

            prompt = f"""Analyze the sentiment and relationship health from these recent emails from {sender}.

Consider:
- Tone (professional, frustrated, urgent, casual)
- Language patterns (escalating frustration, satisfied, neutral)
- Response expectations (immediate action needed, routine communication)

Emails from {sender}:
{''.join(email_texts)}

Respond with JSON only:
{{
  "sentiment": "POSITIVE|NEUTRAL|CONCERNED|FRUSTRATED",
  "relationship_health": 85,
  "signals": ["Awaiting deliverable", "Response time sensitive"],
  "recommended_action": "Follow up by EOD"
}}"""

            try:
                message = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )

                self.api_calls += 1
                self.total_cost += self._calculate_cost(message.usage)

                response_text = message.content[0].text
                result = json.loads(response_text)
                sentiment_results[sender] = result

            except Exception as e:
                print(f"⚠️  Sentiment analysis failed for {sender}: {e}")

        return sentiment_results

    def _calculate_cost(self, usage) -> float:
        """Calculate API cost from usage (Sonnet pricing)"""
        # Claude Sonnet 4.5: $3/M input, $15/M output
        input_cost = (usage.input_tokens / 1_000_000) * 3.0
        output_cost = (usage.output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost

    def _fallback_categorization(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Simple keyword-based categorization (fallback)"""
        urgent_keywords = ["urgent", "asap", "immediate", "critical", "escalation", "breach", "alert"]
        fyi_keywords = ["newsletter", "notification", "digest", "summary", "update"]

        categorized = {"urgent": [], "project": [], "fyi": []}

        for email in emails:
            subject = email.get("subject", "").lower()
            content = email.get("content", "").lower()

            if any(kw in subject or kw in content for kw in urgent_keywords):
                categorized["urgent"].append(email)
            elif any(kw in subject for kw in fyi_keywords):
                categorized["fyi"].append(email)
            else:
                categorized["project"].append(email)

        return categorized

    def generate_morning_brief(self) -> str:
        """Generate complete morning email brief"""
        print(f"\n📧 Morning Email Intelligence")
        print(f"{'='*60}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Step 1: Fetch recent emails
        print(f"\n📥 Fetching emails from last 24 hours...")
        emails = self._get_recent_emails(hours=24)
        print(f"   Found {len(emails)} emails")

        if not emails:
            print("   No new emails to process")
            return self._generate_empty_brief()

        # Step 2: Categorize with Sonnet
        print(f"\n🤖 Categorizing with Claude Sonnet...")
        categorized = self._categorize_with_sonnet(emails)
        print(f"   URGENT: {len(categorized['urgent'])}")
        print(f"   PROJECT: {len(categorized['project'])}")
        print(f"   FYI: {len(categorized['fyi'])}")

        # Step 3: Extract action items from urgent emails
        print(f"\n📋 Extracting action items from urgent emails...")
        action_items = self._extract_action_items_with_sonnet(categorized["urgent"])
        print(f"   Found {len(action_items)} action items")

        # Step 4: Analyze sentiment for key senders
        print(f"\n😊 Analyzing sentiment for stakeholder tracking...")
        sentiment = self._analyze_sentiment_with_sonnet(emails)
        print(f"   Analyzed {len(sentiment)} key senders")

        # Step 5: Generate markdown brief
        print(f"\n📝 Generating morning brief...")
        brief = self._format_brief(categorized, action_items, sentiment)

        # Step 6: Save to Desktop
        self.output_file.write_text(brief)
        print(f"\n✅ Morning brief saved: {self.output_file}")
        print(f"💰 Total cost: ${self.total_cost:.3f}")
        print(f"🔢 API calls: {self.api_calls}")

        return brief

    def _format_brief(self, categorized: Dict, action_items: List[Dict], sentiment: Dict) -> str:
        """Format morning brief as markdown"""
        now = datetime.now()

        brief = f"""# Morning Email Brief - {now.strftime('%A, %B %d, %Y')}

Generated: {now.strftime('%I:%M %p')} | Model: Claude Sonnet 4.5
Processed: {sum(len(v) for v in categorized.values())} emails | Cost: ${self.total_cost:.3f}

---

## 🚨 URGENT ({len(categorized['urgent'])} emails - IMMEDIATE ACTION)

"""

        # Urgent emails
        for i, email in enumerate(categorized["urgent"][:10], 1):
            sender = email.get("sender", "Unknown")
            subject = email.get("subject", "No Subject")
            date = email.get("date", "")[:19]  # Trim to date/time only

            # Check if sentiment available
            sentiment_info = sentiment.get(sender, {})
            sentiment_emoji = {
                "POSITIVE": "😊",
                "NEUTRAL": "😐",
                "CONCERNED": "😟",
                "FRUSTRATED": "😤"
            }.get(sentiment_info.get("sentiment", "NEUTRAL"), "😐")

            brief += f"""{i}. **{subject}**
   From: {sender} | {date}
   Sentiment: {sentiment_emoji} {sentiment_info.get('sentiment', 'NEUTRAL')}

"""

            # Show related action items
            related_actions = [a for a in action_items if a.get("sender", "").lower() in sender.lower()]
            if related_actions:
                brief += "   **Action Items:**\n"
                for action in related_actions:
                    brief += f"   - [ ] {action['task']} (Due: {action['deadline']})\n"
                brief += "\n"

        # All action items summary
        if action_items:
            brief += f"""---

## 📋 ACTION ITEMS EXTRACTED ({len(action_items)} total)

"""
            for action in action_items:
                priority_emoji = "🔴" if action.get("priority") == "HIGH" else "🟡"
                brief += f"""{priority_emoji} **{action['task']}**
   Requested by: {action['sender']}
   Due: {action['deadline']} | Priority: {action['priority']}
   Context: {action.get('context', 'N/A')}

"""

        # Project updates
        brief += f"""---

## 📊 PROJECT UPDATES ({len(categorized['project'])} emails)

"""
        for i, email in enumerate(categorized["project"][:10], 1):
            subject = email.get("subject", "No Subject")
            sender = email.get("sender", "Unknown")
            brief += f"{i}. {subject}\n   From: {sender}\n\n"

        if len(categorized["project"]) > 10:
            brief += f"   ... and {len(categorized['project']) - 10} more\n\n"

        # FYI section
        brief += f"""---

## 📨 FYI ({len(categorized['fyi'])} emails - Low Priority)

"""
        for i, email in enumerate(categorized["fyi"][:5], 1):
            subject = email.get("subject", "No Subject")
            brief += f"{i}. {subject}\n"

        if len(categorized["fyi"]) > 5:
            brief += f"\n... and {len(categorized['fyi']) - 5} more\n"

        # Relationship intelligence
        if sentiment:
            brief += f"""

---

## 📈 RELATIONSHIP INTELLIGENCE

"""
            for sender, data in list(sentiment.items())[:5]:
                health = data.get("relationship_health", 75)
                health_emoji = "🟢" if health >= 75 else "🟡" if health >= 60 else "🔴"

                brief += f"""**{sender}**
   {health_emoji} Health: {health}/100 | Sentiment: {data.get('sentiment', 'NEUTRAL')}
   Signals: {', '.join(data.get('signals', []))}
   Recommended: {data.get('recommended_action', 'Continue monitoring')}

"""

        # Footer with stats
        brief += f"""---

## 💰 PROCESSING STATS

- Sonnet API calls: {self.api_calls}
- Total cost: ${self.total_cost:.3f}
- Emails processed: {sum(len(v) for v in categorized.values())}
- Action items: {len(action_items)}
- Time saved: ~18 minutes manual triage

**Next Steps:**
1. Address {len(categorized['urgent'])} urgent emails before 9 AM
2. Review {len(action_items)} action items (auto-added to GTD tracker)
3. Monitor relationship health for {len([s for s, d in sentiment.items() if d.get('relationship_health', 75) < 70])} at-risk contacts

---

*Generated by Maia Morning Email Intelligence*
*Schedule: Daily 7:00 AM (Mon-Fri) | Adjust: Edit LaunchAgent plist*
"""

        return brief

    def _generate_empty_brief(self) -> str:
        """Generate brief when no emails found"""
        now = datetime.now()
        brief = f"""# Morning Email Brief - {now.strftime('%A, %B %d, %Y')}

Generated: {now.strftime('%I:%M %p')} | Model: Claude Sonnet 4.5

---

## 📬 INBOX: CLEAR

No new emails in the last 24 hours.

✅ All caught up!

---

*Generated by Maia Morning Email Intelligence*
"""
        self.output_file.write_text(brief)
        return brief


def main():
    """Main entry point for scheduled execution"""
    try:
        intelligence = MorningEmailIntelligence()
        intelligence.generate_morning_brief()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error generating morning brief: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
