#!/usr/bin/env python3
"""
Automatic Capture Integration - Phase 115.3

Automatically captures real items from existing Maia systems into Executive Information Manager:
- Email RAG (high-priority emails)
- Daily Briefing (action items, decisions, commitments)
- Action Tracker (GTD items)
- Calendar (upcoming meetings)

Author: Maia (My AI Agent)
Created: 2025-10-14
Phase: 115.3 (Agent Orchestration Layer - Production Integration)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import importlib.util

# Path setup
MAIA_ROOT = Path(os.environ.get('MAIA_ROOT', Path.home() / 'git' / 'maia' / 'claude'))

def import_module_from_path(module_name: str, file_path: Path):
    """Dynamic module import"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import Executive Information Manager
exec_info_path = MAIA_ROOT / "tools" / "information_management" / "executive_information_manager.py"
exec_info_module = import_module_from_path("executive_information_manager", exec_info_path)
ExecutiveInformationManager = exec_info_module.ExecutiveInformationManager


class AutoCaptureIntegration:
    """
    Automatic capture from existing Maia systems into Executive Information Manager.
    """

    def __init__(self):
        """Initialize integration with Executive Information Manager"""
        self.manager = ExecutiveInformationManager()
        self.maia_root = MAIA_ROOT

    def capture_from_daily_briefing(self) -> int:
        """
        Capture high-impact items from enhanced daily briefing.

        Returns:
            Number of items captured
        """
        briefing_file = self.maia_root / "data" / "enhanced_daily_briefing.json"

        if not briefing_file.exists():
            print(f"⚠️  Daily briefing not found: {briefing_file}")
            return 0

        with open(briefing_file, 'r') as f:
            briefing = json.load(f)

        captured = 0

        # Capture high-impact items (score >= 7.0)
        for item in briefing.get('high_impact_items', []):
            if item.get('impact_score', 0) >= 7.0:
                # Determine time sensitivity from deadline
                deadline = item.get('deadline', '')
                time_sensitivity = 'urgent' if 'today' in deadline.lower() else \
                                 'week' if 'week' in deadline.lower() else 'month'

                # Determine decision impact
                decision_impact = 'high' if item.get('impact_score', 0) >= 8.0 else 'medium'

                # Capture item
                self.manager.capture_item(
                    source='daily_briefing',
                    item_type='action',
                    title=item.get('action', 'Untitled action'),
                    content=f"Impact: {item.get('impact_score')}/10 | Deadline: {deadline} | Business Outcome: {item.get('business_outcome', 'N/A')}",
                    metadata={
                        'source_id': item.get('action'),
                        'time_sensitivity': time_sensitivity,
                        'decision_impact': decision_impact,
                        'stakeholder_importance': 'team',  # Default
                        'strategic_alignment': 'supporting'  # Default
                    }
                )
                captured += 1

        # Capture decision packages
        for decision in briefing.get('decision_packages', []):
            priority = decision.get('priority', 'medium').lower()
            decision_impact = 'high' if priority in ['critical', 'high'] else 'medium'

            self.manager.capture_item(
                source='daily_briefing',
                item_type='decision',
                title=f"Decision: {decision.get('topic', 'Untitled')}",
                content=f"Context: {decision.get('context', 'N/A')} | Recommendation: {decision.get('recommendation', 'N/A')} | Confidence: {decision.get('confidence', 'N/A')}",
                metadata={
                    'source_id': decision.get('topic'),
                    'time_sensitivity': 'week',
                    'decision_impact': decision_impact,
                    'stakeholder_importance': 'executive' if priority == 'critical' else 'team',
                    'strategic_alignment': 'core'
                }
            )
            captured += 1

        print(f"✅ Captured {captured} items from daily briefing")
        return captured

    def capture_from_action_tracker(self) -> int:
        """
        Capture active GTD items from action tracker.

        Returns:
            Number of items captured
        """
        action_file = self.maia_root / "data" / "action_completion_metrics.json"

        if not action_file.exists():
            print(f"⚠️  Action tracker not found: {action_file}")
            return 0

        with open(action_file, 'r') as f:
            actions = json.load(f)

        captured = 0

        # Capture active actions (not completed)
        for action in actions.get('actions', []):
            if action.get('status') != 'completed':
                # Determine time sensitivity from context
                contexts = action.get('context_tags', [])
                time_sensitivity = 'urgent' if '@needs-decision' in contexts else \
                                 'week' if '@quick-wins' in contexts else 'month'

                # Determine decision impact
                decision_impact = 'high' if '@strategic' in contexts else \
                                'medium' if '@needs-decision' in contexts else 'low'

                # Determine stakeholder
                stakeholder = 'team'
                for tag in contexts:
                    if tag.startswith('@stakeholder-'):
                        stakeholder = 'client'
                        break

                self.manager.capture_item(
                    source='action_tracker',
                    item_type='task',
                    title=action.get('action', 'Untitled action'),
                    content=f"Project: {action.get('project', 'N/A')} | Contexts: {', '.join(contexts)} | Duration: {action.get('estimated_duration', 'N/A')}",
                    metadata={
                        'source_id': str(action.get('id')),
                        'time_sensitivity': time_sensitivity,
                        'decision_impact': decision_impact,
                        'stakeholder_importance': stakeholder,
                        'strategic_alignment': 'core' if '@strategic' in contexts else 'supporting'
                    }
                )
                captured += 1

        print(f"✅ Captured {captured} items from action tracker")
        return captured

    def capture_from_email_rag(self, days_back: int = 7) -> int:
        """
        Capture actionable emails using intelligent semantic filtering.

        Strategy:
        - Semantic queries for action items, questions, decisions
        - Filter out noise (meeting acceptances, auto-replies)
        - Prioritize external stakeholders and urgent matters
        - Only recent emails (last 7 days)

        Returns:
            Number of items captured
        """
        # Try to import email RAG
        try:
            email_rag_path = self.maia_root / "tools" / "email_rag_ollama.py"
            email_rag_module = import_module_from_path("email_rag_ollama", email_rag_path)
            EmailRAG = email_rag_module.EmailRAGOllama
            rag = EmailRAG()
        except Exception as e:
            print(f"⚠️  Could not import Email RAG: {e}")
            return 0

        captured = 0
        seen_messages = set()

        # Semantic queries: (query, time_sensitivity, decision_impact, stakeholder, limit)
        queries = [
            ("urgent matters need immediate attention", 'urgent', 'high', 'executive', 5),
            ("action items I need to complete", 'week', 'high', 'team', 10),
            ("questions waiting for my response", 'week', 'medium', 'team', 10),
            ("decisions pending my approval", 'week', 'high', 'executive', 8),
            ("emails from external clients", 'week', 'medium', 'client', 8),
        ]

        for query_text, time_sens, decision_imp, stakeholder, limit in queries:
            try:
                results = rag.semantic_search(query_text, n_results=limit)

                for result in results:
                    msg_id = result.get('message_id')
                    if msg_id in seen_messages:
                        continue

                    # Filter noise
                    subject = result.get('subject', '')
                    if any(subject.startswith(p) for p in ['Accepted:', 'Automatic reply:', 'Canceled:']):
                        continue

                    # Lower threshold to capture more (learning phase)
                    if result.get('relevance', 0) < 0.25:
                        continue

                    # External stakeholders get higher priority
                    sender = result.get('sender', '')
                    if '@orro.group' not in sender.lower():
                        stakeholder = 'client'
                        decision_imp = 'high'

                    self.manager.capture_item(
                        source='email_rag',
                        item_type='email',
                        title=f"Email: {subject}",
                        content=f"From: {sender} | {result.get('preview', '')}",
                        metadata={
                            'source_id': msg_id,
                            'time_sensitivity': time_sens,
                            'decision_impact': decision_imp,
                            'stakeholder_importance': stakeholder,
                            'strategic_alignment': 'core' if decision_imp == 'high' else 'supporting'
                        }
                    )
                    captured += 1
                    seen_messages.add(msg_id)

            except Exception as e:
                print(f"⚠️  Error in email query: {e}")
                continue

        print(f"✅ Captured {captured} items from Email RAG")
        return captured

    def capture_from_vtt_intelligence(self) -> int:
        """
        Capture action items and decisions from VTT meeting intelligence.

        Returns:
            Number of items captured
        """
        vtt_file = self.maia_root / "data" / "vtt_intelligence.json"

        if not vtt_file.exists():
            print(f"⚠️  VTT intelligence not found: {vtt_file}")
            return 0

        with open(vtt_file, 'r') as f:
            vtt_data = json.load(f)

        captured = 0

        # Capture action items from all meetings
        for meeting_id, meeting_data in vtt_data.get('meetings', {}).items():
            results = meeting_data.get('results', {})

            # Capture action items
            for action in results.get('action_items', []):
                # Skip if status is completed
                if action.get('status') == 'completed':
                    continue

                # Determine time sensitivity from deadline
                deadline = action.get('deadline', '').lower()
                time_sensitivity = 'urgent' if any(word in deadline for word in ['today', 'asap', 'immediate']) else \
                                 'week' if 'week' in deadline else \
                                 'month' if 'month' in deadline else 'later'

                # Determine if this is for the user (Naythan)
                owner = action.get('owner', '').lower()
                is_mine = 'naythan' in owner or owner in ['', 'me', 'i']

                # Only capture items assigned to user
                if is_mine:
                    self.manager.capture_item(
                        source='vtt_intelligence',
                        item_type='action',
                        title=action.get('action', 'Untitled action'),
                        content=f"From meeting: {meeting_id} | Owner: {action.get('owner', 'N/A')} | Deadline: {deadline}",
                        metadata={
                            'source_id': f"{meeting_id}_{action.get('action', '')}",
                            'time_sensitivity': time_sensitivity,
                            'decision_impact': 'medium',
                            'stakeholder_importance': 'team',
                            'strategic_alignment': 'supporting'
                        }
                    )
                    captured += 1

            # Capture key decisions
            for decision in results.get('key_decisions', []):
                decision_text = decision.get('decision', '') if isinstance(decision, dict) else str(decision)

                self.manager.capture_item(
                    source='vtt_intelligence',
                    item_type='decision',
                    title=f"Decision: {decision_text[:100]}",
                    content=f"From meeting: {meeting_id} | Full decision: {decision_text}",
                    metadata={
                        'source_id': f"{meeting_id}_decision",
                        'time_sensitivity': 'week',
                        'decision_impact': 'high',
                        'stakeholder_importance': 'team',
                        'strategic_alignment': 'core'
                    }
                )
                captured += 1

        print(f"✅ Captured {captured} items from VTT intelligence")
        return captured

    def run_full_capture(self) -> Dict:
        """
        Run full capture from all sources.

        Returns:
            Capture statistics
        """
        print("\n" + "="*80)
        print("🔄 AUTOMATIC CAPTURE INTEGRATION")
        print("="*80 + "\n")

        stats = {
            'daily_briefing': 0,
            'action_tracker': 0,
            'vtt_intelligence': 0,
            'email_rag': 0,
            'total': 0
        }

        # Capture from each source
        stats['daily_briefing'] = self.capture_from_daily_briefing()
        stats['action_tracker'] = self.capture_from_action_tracker()
        stats['vtt_intelligence'] = self.capture_from_vtt_intelligence()
        stats['email_rag'] = self.capture_from_email_rag()
        stats['total'] = sum(stats.values()) - stats['total']  # Exclude total from sum

        print("\n" + "="*80)
        print("📊 CAPTURE SUMMARY")
        print("="*80)
        print(f"Daily Briefing: {stats['daily_briefing']} items")
        print(f"Action Tracker: {stats['action_tracker']} items")
        print(f"VTT Intelligence: {stats['vtt_intelligence']} items")
        print(f"Email RAG: {stats['email_rag']} items")
        print(f"Total Captured: {stats['total']} items")
        print("="*80 + "\n")

        if stats['total'] > 0:
            print("✅ Automatic capture complete! Run 'python3 executive_information_manager.py process' to prioritize.")
        else:
            print("⚠️  No items captured. Check that data sources have content.")

        return stats


def main():
    """Main entry point"""
    integration = AutoCaptureIntegration()
    integration.run_full_capture()


if __name__ == "__main__":
    main()
