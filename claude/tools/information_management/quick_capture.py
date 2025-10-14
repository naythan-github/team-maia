#!/usr/bin/env python3
"""
Quick Capture Helper - Phase 115.3

Simple interface for manually capturing items into Executive Information Manager.
Use this to capture emails, tasks, decisions, or questions that need prioritization.

Usage:
    # Interactive mode
    python3 quick_capture.py

    # Command line mode
    python3 quick_capture.py --title "Review Q4 budget" --type task --priority high

Author: Maia (My AI Agent)
Created: 2025-10-14
Phase: 115.3 (Agent Orchestration Layer - Production Integration)
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
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


def interactive_capture():
    """Interactive capture mode with prompts"""
    print("\n" + "="*80)
    print("📥 QUICK CAPTURE - Interactive Mode")
    print("="*80 + "\n")

    manager = ExecutiveInformationManager()

    # Get item details
    print("What would you like to capture?\n")

    title = input("Title/Subject: ").strip()
    if not title:
        print("❌ Title is required")
        return

    print("\nType: ")
    print("  1. Email")
    print("  2. Task/Action")
    print("  3. Decision")
    print("  4. Meeting")
    print("  5. Question")
    item_type_map = {'1': 'email', '2': 'task', '3': 'decision', '4': 'meeting', '5': 'question'}
    item_type_choice = input("Choose (1-5): ").strip()
    item_type = item_type_map.get(item_type_choice, 'task')

    content = input("\nNotes/Content (optional): ").strip() or None

    print("\nTime Sensitivity:")
    print("  1. Urgent (today)")
    print("  2. This week")
    print("  3. This month")
    print("  4. Later/someday")
    time_map = {'1': 'urgent', '2': 'week', '3': 'month', '4': 'later'}
    time_choice = input("Choose (1-4): ").strip()
    time_sensitivity = time_map.get(time_choice, 'week')

    print("\nDecision Impact:")
    print("  1. High (strategic/financial impact)")
    print("  2. Medium (operational impact)")
    print("  3. Low (tactical/minor)")
    print("  4. None (informational)")
    decision_map = {'1': 'high', '2': 'medium', '3': 'low', '4': 'none'}
    decision_choice = input("Choose (1-4): ").strip()
    decision_impact = decision_map.get(decision_choice, 'medium')

    print("\nStakeholder:")
    print("  1. Executive/Leadership")
    print("  2. Client")
    print("  3. Team member")
    print("  4. Vendor")
    print("  5. External")
    stakeholder_map = {'1': 'executive', '2': 'client', '3': 'team', '4': 'vendor', '5': 'external'}
    stakeholder_choice = input("Choose (1-5): ").strip()
    stakeholder = stakeholder_map.get(stakeholder_choice, 'team')

    print("\nStrategic Alignment:")
    print("  1. Core (directly supports strategic goals)")
    print("  2. Supporting (enables strategic work)")
    print("  3. Tangential (loosely related)")
    print("  4. Unrelated")
    alignment_map = {'1': 'core', '2': 'supporting', '3': 'tangential', '4': 'unrelated'}
    alignment_choice = input("Choose (1-4): ").strip()
    alignment = alignment_map.get(alignment_choice, 'supporting')

    # Capture item
    print("\n" + "-"*80)
    item_id = manager.capture_item(
        source='manual',
        item_type=item_type,
        title=title,
        content=content,
        metadata={
            'time_sensitivity': time_sensitivity,
            'decision_impact': decision_impact,
            'stakeholder_importance': stakeholder,
            'strategic_alignment': alignment
        }
    )

    print("\n✅ Item captured successfully!")
    print(f"   Run 'python3 executive_information_manager.py process' to prioritize.")
    print("="*80 + "\n")


def cli_capture(args):
    """Command-line capture mode"""
    manager = ExecutiveInformationManager()

    # Map CLI args to metadata
    priority_map = {
        'critical': ('urgent', 'high', 'executive', 'core'),
        'high': ('week', 'high', 'client', 'core'),
        'medium': ('week', 'medium', 'team', 'supporting'),
        'low': ('month', 'low', 'team', 'tangential')
    }

    time_sens, dec_impact, stakeholder, alignment = priority_map.get(args.priority, priority_map['medium'])

    item_id = manager.capture_item(
        source=args.source,
        item_type=args.type,
        title=args.title,
        content=args.content,
        metadata={
            'time_sensitivity': time_sens,
            'decision_impact': dec_impact,
            'stakeholder_importance': stakeholder,
            'strategic_alignment': alignment
        }
    )

    print(f"\n✅ Captured: {args.title} (ID: {item_id})")
    print(f"   Priority: {args.priority} | Type: {args.type}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Quick capture for Executive Information Manager')
    parser.add_argument('--title', help='Item title/subject')
    parser.add_argument('--type', default='task', choices=['email', 'task', 'decision', 'meeting', 'question'],
                       help='Item type')
    parser.add_argument('--content', help='Item content/notes')
    parser.add_argument('--priority', default='medium', choices=['critical', 'high', 'medium', 'low'],
                       help='Overall priority level')
    parser.add_argument('--source', default='manual', help='Source system')

    args = parser.parse_args()

    if args.title:
        # CLI mode
        cli_capture(args)
    else:
        # Interactive mode
        interactive_capture()


if __name__ == "__main__":
    main()
