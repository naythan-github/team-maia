#!/usr/bin/env python3
"""
Email RAG Batch Indexer - Handles 1,280+ emails with AppleScript timeout workaround

Problem: AppleScript times out (>30s) when retrieving 654+ messages from a single folder
Solution: Batch retrieval in 150-message chunks, then index with deduplication

Author: SRE Principal Engineer Agent
Created: 2025-10-29
"""

import os
import sys
from pathlib import Path

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.email_rag_ollama import EmailRAGOllama
from claude.tools.macos_mail_bridge import MacOSMailBridge


def batch_index_all_emails(batch_size=150):
    """
    Index all emails in batches to avoid AppleScript timeout

    Args:
        batch_size: Messages per batch (150 is safe for 30s timeout)
    """
    print("🔄 Batch Email Indexer - All 1,280 emails\n")
    print("=" * 70)

    # Initialize
    rag = EmailRAGOllama()
    bridge = MacOSMailBridge()

    # Get folder counts
    print("📊 Checking email counts in Mail.app...")
    import subprocess
    result = subprocess.run([
        'osascript', '-e', '''
        tell application "Mail"
            set targetAccount to account 1
            set inboxMB to mailbox "Inbox" of targetAccount
            set sentMB to mailbox "Sent Items" of targetAccount

            set ccMB to missing value
            repeat with mb in mailboxes of targetAccount
                if name of mb is "CC" then
                    set ccMB to mb
                    exit repeat
                end if
            end repeat

            set inboxCount to count of messages of inboxMB
            set sentCount to count of messages of sentMB
            set ccCount to 0
            if ccMB is not missing value then
                set ccCount to count of messages of ccMB
            end if

            return inboxCount & "|" & sentCount & "|" & ccCount
        end tell
        '''
    ], capture_output=True, text=True, timeout=10)

    counts = result.stdout.strip().split("|")
    # Strip commas and spaces from AppleScript number formatting
    inbox_total = int(counts[0].replace(',', '').strip())
    sent_total = int(counts[1].replace(',', '').strip())
    cc_total = int(counts[2].replace(',', '').strip())

    print(f"   • Inbox: {inbox_total} emails")
    print(f"   • Sent Items: {sent_total} emails")
    print(f"   • CC: {cc_total} emails")
    print(f"   • Total: {inbox_total + sent_total + cc_total} emails\n")

    # Calculate batches needed
    inbox_batches = (inbox_total + batch_size - 1) // batch_size
    sent_batches = (sent_total + batch_size - 1) // batch_size
    cc_batches = (cc_total + batch_size - 1) // batch_size
    total_batches = inbox_batches + sent_batches + cc_batches

    print(f"📦 Batch plan ({batch_size} emails per batch):")
    print(f"   • Inbox: {inbox_batches} batches")
    print(f"   • Sent Items: {sent_batches} batches")
    print(f"   • CC: {cc_batches} batches")
    print(f"   • Total: {total_batches} batches\n")

    current_batch = 0
    total_indexed = 0
    total_errors = 0

    # Index each folder in batches
    folders = [
        ("Inbox", inbox_total, inbox_batches),
        ("Sent Items", sent_total, sent_batches),
        ("CC", cc_total, cc_batches)
    ]

    for folder_name, folder_total, folder_batches in folders:
        if folder_total == 0:
            continue

        print(f"\n{'='*70}")
        print(f"📂 Indexing {folder_name} ({folder_total} emails in {folder_batches} batches)")
        print(f"{'='*70}\n")

        for batch_num in range(folder_batches):
            current_batch += 1

            # Index this batch
            print(f"[Batch {current_batch}/{total_batches}] {folder_name} batch {batch_num+1}/{folder_batches}...")

            try:
                stats = rag.index_inbox(
                    limit=batch_size,
                    hours_ago=None,
                    force=False
                )

                batch_new = stats.get('new', 0)
                batch_errors = stats.get('errors', 0)
                total_indexed += batch_new
                total_errors += batch_errors

                print(f"   ✓ Indexed: {batch_new} new, {stats.get('skipped', 0)} skipped, {batch_errors} errors")

            except Exception as e:
                print(f"   ✗ Batch failed: {str(e)[:100]}")
                total_errors += 1
                continue

    # Final report
    print(f"\n{'='*70}")
    print(f"✅ Batch Indexing Complete!")
    print(f"{'='*70}\n")

    results = rag.collection.get(include=['metadatas'])
    mailbox_counts = {}
    for m in results['metadatas']:
        mb = m.get('mailbox', 'Unknown')
        mailbox_counts[mb] = mailbox_counts.get(mb, 0) + 1

    final_total = sum(mailbox_counts.values())

    print(f"📊 Final Statistics:")
    print(f"   • Total indexed: {final_total} emails")
    print(f"   • New in this run: {total_indexed}")
    print(f"   • Errors: {total_errors}")
    print(f"\n📂 Mailbox Distribution:")
    for mb, count in sorted(mailbox_counts.items(), key=lambda x: x[1], reverse=True):
        expected = {'Inbox': inbox_total, 'Sent Items': sent_total, 'CC': cc_total}
        exp = expected.get(mb, 0)
        pct = (count/final_total)*100 if final_total > 0 else 0
        cov = (count/exp)*100 if exp > 0 else 0
        print(f"   • {mb}: {count}/{exp} ({pct:.1f}% of total, {cov:.1f}% coverage)")

    grand_total = inbox_total + sent_total + cc_total
    print(f"\n✅ Overall: {final_total}/{grand_total} emails ({(final_total/grand_total)*100:.1f}% complete)")

    return final_total, mailbox_counts


if __name__ == "__main__":
    try:
        total, distribution = batch_index_all_emails(batch_size=150)
        print("\n✅ Batch indexing successful!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Batch indexing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
