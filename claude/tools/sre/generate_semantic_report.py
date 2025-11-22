#!/usr/bin/env python3
"""
Generate Semantic Analysis Report from ChromaDB

Reads existing ChromaDB collection and generates comprehensive markdown report
without re-running indexing or clustering.

Created: 2025-10-27
Author: Maia SDM Agent
"""

import os
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import chromadb
import numpy as np

MAIA_ROOT = Path(__file__).resolve().parents[3]

def extract_keywords(text: str, top_n: int = 10) -> list:
    """Simple keyword extraction"""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'issue',
        'resolution', 'ticket', 'user', 'client', 'customer'
    }

    words = text.lower().split()
    word_counts = Counter([
        word.strip('.,;:!?"\'()[]{}')
        for word in words
        if len(word) > 3 and word.strip('.,;:!?"\'()[]{}') not in stop_words
    ])

    return [word for word, count in word_counts.most_common(top_n)]


def main():
    print("📊 Generating Semantic Analysis Report...")

    # Load ChromaDB collection
    rag_db_path = os.path.expanduser("~/.maia/servicedesk_semantic_analysis")
    client = chromadb.PersistentClient(path=rag_db_path)

    collection = client.get_collection(name="tickets_semantic")
    total_tickets = collection.count()

    print(f"   Collection: {total_tickets:,} tickets")

    # Get all data
    results = collection.get(include=['metadatas', 'documents'])
    metadatas = results['metadatas']
    documents = results['documents']

    # Group by category
    by_category = defaultdict(list)
    by_root_cause = defaultdict(list)
    by_account = defaultdict(list)

    for idx, meta in enumerate(metadatas):
        category = meta.get('category', 'Unknown')
        root_cause = meta.get('root_cause', 'Unknown')
        account = meta.get('account_name', 'Unknown')

        by_category[category].append({
            'metadata': meta,
            'document': documents[idx]
        })
        by_root_cause[root_cause].append({
            'metadata': meta,
            'document': documents[idx]
        })
        by_account[account].append({
            'metadata': meta,
            'document': documents[idx]
        })

    # Generate report
    report_lines = [
        "# ServiceDesk Semantic Ticket Analysis Report",
        f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Model**: intfloat/e5-base-v2 (768-dimensional embeddings)",
        f"**Total Tickets Analyzed**: {total_tickets:,}",
        "\n---\n"
    ]

    # Executive Summary
    report_lines.extend([
        "## 📈 Executive Summary\n",
        f"- **Total Tickets**: {total_tickets:,}",
        f"- **Unique Categories**: {len(by_category)}",
        f"- **Unique Root Causes**: {len(by_root_cause)}",
        f"- **Unique Accounts**: {len(by_account)}",
        "\n---\n"
    ])

    # Category Breakdown
    report_lines.extend([
        "## 📁 Ticket Categories (Top 20)\n",
        "Breakdown of tickets by primary category:\n"
    ])

    sorted_categories = sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True)

    for i, (category, items) in enumerate(sorted_categories[:20], 1):
        count = len(items)
        percentage = count / total_tickets * 100

        report_lines.append(f"\n### {i}. {category} ({count:,} tickets, {percentage:.1f}%)\n")

        # Top root causes for this category
        root_causes = Counter([item['metadata'].get('root_cause', 'Unknown') for item in items])
        report_lines.append("**Top Root Causes**:")
        for cause, rc_count in root_causes.most_common(5):
            report_lines.append(f"- {cause}: {rc_count} tickets")

        # Top accounts
        accounts = Counter([item['metadata'].get('account_name', 'Unknown') for item in items])
        report_lines.append("\n**Top Affected Accounts**:")
        for account, acc_count in accounts.most_common(3):
            report_lines.append(f"- {account}: {acc_count} tickets")

        # Extract common keywords
        all_text = " ".join([item['document'].lower() for item in items[:50]])  # Sample first 50
        keywords = extract_keywords(all_text)
        report_lines.append(f"\n**Common Keywords**: {', '.join(keywords[:10])}")

        # Sample tickets
        report_lines.append("\n**Sample Tickets**:")
        for sample in items[:3]:
            ticket_id = sample['metadata'].get('ticket_id', 'Unknown')
            title = sample['metadata'].get('title', 'No title')
            report_lines.append(f"- **{ticket_id}**: {title[:100]}")

    # Root Cause Analysis
    report_lines.extend([
        "\n---\n",
        "## 🔍 Root Cause Analysis (Top 20)\n",
        "Most common root causes across all tickets:\n"
    ])

    sorted_root_causes = sorted(by_root_cause.items(), key=lambda x: len(x[1]), reverse=True)

    for i, (root_cause, items) in enumerate(sorted_root_causes[:20], 1):
        count = len(items)
        percentage = count / total_tickets * 100

        report_lines.append(f"\n### {i}. {root_cause} ({count:,} tickets, {percentage:.1f}%)\n")

        # Top categories for this root cause
        categories = Counter([item['metadata'].get('category', 'Unknown') for item in items])
        report_lines.append("**Top Categories**:")
        for cat, cat_count in categories.most_common(3):
            report_lines.append(f"- {cat}: {cat_count} tickets")

        # Extract keywords
        all_text = " ".join([item['document'].lower() for item in items[:50]])
        keywords = extract_keywords(all_text)
        report_lines.append(f"\n**Common Keywords**: {', '.join(keywords[:8])}")

    # Account Analysis
    report_lines.extend([
        "\n---\n",
        "## 👥 Account Analysis (Top 20)\n",
        "Accounts with most tickets:\n"
    ])

    sorted_accounts = sorted(by_account.items(), key=lambda x: len(x[1]), reverse=True)

    for i, (account, items) in enumerate(sorted_accounts[:20], 1):
        count = len(items)
        percentage = count / total_tickets * 100

        report_lines.append(f"\n### {i}. {account} ({count:,} tickets, {percentage:.1f}%)\n")

        # Top categories
        categories = Counter([item['metadata'].get('category', 'Unknown') for item in items])
        report_lines.append("**Top Categories**:")
        for cat, cat_count in categories.most_common(3):
            report_lines.append(f"- {cat}: {cat_count} tickets")

        # Top root causes
        root_causes = Counter([item['metadata'].get('root_cause', 'Unknown') for item in items])
        report_lines.append("\n**Top Root Causes**:")
        for cause, rc_count in root_causes.most_common(3):
            report_lines.append(f"- {cause}: {rc_count} tickets")

    # Save report
    # Output to work_projects (work output, not Maia system file)
    report_path = Path.home() / "work_projects/servicedesk_analysis/servicedesk_semantic_analysis_report.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))

    print(f"\n✅ Report saved to: {report_path}")
    print(f"   Size: {report_path.stat().st_size / 1024:.1f} KB")
    print(f"\n📖 Preview:")
    print("\n".join(report_lines[:50]))


if __name__ == "__main__":
    main()
