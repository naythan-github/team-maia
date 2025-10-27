#!/usr/bin/env python3
"""
ServiceDesk Tier Backfill Script - PostgreSQL Edition

Project: TIER-TRACKER-001
Phase: 3 - Database Schema Implementation
Date: 2025-10-27

Purpose:
Backfill support_tier column in PostgreSQL servicedesk.tickets table
using TierCategorizer logic from categorize_tickets_by_tier.py

Requirements:
- DP-2: Backfill Process (batch updates, transaction-safe)
- NFR-1.3: Performance (<5 minutes for 10,939 tickets)
- NFR-2.3: Transaction safety (COMMIT on success, ROLLBACK on error)
- User Q2: Phased validation (100 sample → accuracy check → full backfill)

Features:
- Batch processing (1000 rows at a time) - 10-20x faster than row-by-row
- Transaction-safe (atomic COMMIT/ROLLBACK)
- Progress logging (every 1000 rows)
- Idempotent (safe to re-run)
- Sample mode for accuracy validation

Execution:
  # Sample mode (100 tickets for accuracy validation)
  python3 claude/tools/sre/backfill_support_tiers_to_postgres.py --sample

  # Full backfill (all 10,939 tickets)
  python3 claude/tools/sre/backfill_support_tiers_to_postgres.py --full

Database Access:
  Uses docker exec per ARCHITECTURE.md ADR-001 (PostgreSQL in isolated container)
"""

import argparse
import subprocess
import time
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import json

# Import TierCategorizer from existing script
MAIA_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MAIA_ROOT / "claude/tools/sre"))
from categorize_tickets_by_tier import TierCategorizer

# PostgreSQL connection settings
DOCKER_CONTAINER = "servicedesk-postgres"
DB_USER = "servicedesk_user"
DB_NAME = "servicedesk"

# Batch size for updates (1000 rows = optimal performance)
BATCH_SIZE = 1000

# Sample size for accuracy validation
SAMPLE_SIZE = 100


def execute_sql(sql: str) -> Tuple[int, str, str]:
    """
    Execute SQL via docker exec

    Args:
        sql: SQL command to execute

    Returns:
        Tuple[int, str, str]: (return_code, stdout, stderr)
    """
    cmd = [
        "docker", "exec", DOCKER_CONTAINER,
        "psql", "-U", DB_USER, "-d", DB_NAME,
        "-c", sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return (result.returncode, result.stdout, result.stderr)


def execute_sql_json(sql: str) -> List[Dict]:
    """
    Execute SQL and return results as JSON

    Args:
        sql: SQL query to execute

    Returns:
        List[Dict]: Query results as list of dictionaries
    """
    # Add -t (no headers) and format as JSON-friendly output
    cmd = [
        "docker", "exec", DOCKER_CONTAINER,
        "psql", "-U", DB_USER, "-d", DB_NAME,
        "-t", "-A",  # No headers, unaligned mode
        "-F", "|",   # Field separator
        "-c", sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"SQL execution failed: {result.stderr}")

    # Parse pipe-separated output
    lines = [line for line in result.stdout.strip().split('\n') if line.strip()]

    return lines


def fetch_tickets(sample_mode: bool = False) -> List[Dict]:
    """
    Fetch tickets from PostgreSQL database

    Args:
        sample_mode: If True, fetch only SAMPLE_SIZE tickets

    Returns:
        List[Dict]: List of ticket dictionaries
    """
    limit_clause = f"LIMIT {SAMPLE_SIZE}" if sample_mode else ""

    sql = f"""
    SELECT
        "TKT-Ticket ID"::text AS ticket_id,
        COALESCE("TKT-Title", '') AS title,
        COALESCE("TKT-Description", '') AS description,
        COALESCE("TKT-Category", '') AS category,
        COALESCE("TKT-Root Cause Category", '') AS root_cause
    FROM servicedesk.tickets
    WHERE support_tier IS NULL
    ORDER BY "TKT-Created Time" DESC
    {limit_clause}
    """

    print(f"📊 Fetching tickets from database...")
    lines = execute_sql_json(sql)

    tickets = []
    for line in lines:
        if not line.strip():
            continue

        parts = line.split('|')
        if len(parts) >= 5:
            tickets.append({
                'ticket_id': parts[0].strip(),
                'title': parts[1].strip() if parts[1].strip() else None,
                'description': parts[2].strip() if parts[2].strip() else None,
                'category': parts[3].strip() if parts[3].strip() else None,
                'root_cause': parts[4].strip() if parts[4].strip() else None
            })

    print(f"✅ Fetched {len(tickets):,} tickets\n")
    return tickets


def categorize_tickets(tickets: List[Dict]) -> List[Tuple[str, str]]:
    """
    Categorize tickets using TierCategorizer

    Args:
        tickets: List of ticket dictionaries

    Returns:
        List[Tuple[str, str]]: List of (ticket_id, tier) tuples
    """
    print(f"🔍 Categorizing {len(tickets):,} tickets...")

    categorizer = TierCategorizer()
    results = []

    for idx, ticket in enumerate(tickets):
        tier = categorizer.categorize_ticket(ticket)
        results.append((ticket['ticket_id'], tier))

        if (idx + 1) % 1000 == 0:
            print(f"   Processed {idx+1:,}/{len(tickets):,} tickets...")

    print(f"✅ Categorization complete\n")
    return results


def backfill_batch(batch: List[Tuple[str, str]]) -> bool:
    """
    Backfill a batch of tickets (transaction-safe)

    Args:
        batch: List of (ticket_id, tier) tuples

    Returns:
        bool: True if successful, False otherwise
    """
    # Build UPDATE statement with CASE
    # TKT-Ticket ID is INTEGER type, so use numeric values (no quotes)
    cases = []
    ticket_ids = []

    for ticket_id, tier in batch:
        # Validate ticket_id is numeric
        try:
            tid_num = int(ticket_id)
            cases.append(f"WHEN \"TKT-Ticket ID\"={tid_num} THEN '{tier}'")
            ticket_ids.append(str(tid_num))
        except ValueError:
            print(f"⚠️  Skipping invalid ticket ID: {ticket_id}")
            continue

    if not cases:
        print("⚠️  No valid ticket IDs in batch, skipping")
        return True

    case_stmt = '\n        '.join(cases)
    id_list = ', '.join(ticket_ids)

    sql = f"""
    BEGIN;

    UPDATE servicedesk.tickets
    SET support_tier = CASE
        {case_stmt}
    END
    WHERE "TKT-Ticket ID" IN ({id_list});

    COMMIT;
    """

    returncode, stdout, stderr = execute_sql(sql)

    if returncode != 0:
        print(f"❌ Batch update failed: {stderr}")
        # Rollback is automatic on error
        return False

    return True


def validate_backfill() -> Dict[str, int]:
    """
    Validate backfill results

    Returns:
        Dict[str, int]: Validation statistics
    """
    print("🔍 Validating backfill results...\n")

    # Check NULL count
    sql_null = "SELECT COUNT(*) FROM servicedesk.tickets WHERE support_tier IS NULL;"
    lines = execute_sql_json(sql_null)
    null_count = int(lines[0].strip()) if lines else -1

    # Check tier distribution
    sql_dist = """
    SELECT support_tier, COUNT(*) as count
    FROM servicedesk.tickets
    WHERE support_tier IS NOT NULL
    GROUP BY support_tier
    ORDER BY support_tier;
    """
    lines = execute_sql_json(sql_dist)

    tier_counts = {}
    for line in lines:
        parts = line.split('|')
        if len(parts) == 2:
            tier = parts[0].strip()
            count = int(parts[1].strip())
            tier_counts[tier] = count

    return {
        'null_count': null_count,
        'l1_count': tier_counts.get('L1', 0),
        'l2_count': tier_counts.get('L2', 0),
        'l3_count': tier_counts.get('L3', 0),
        'total': sum(tier_counts.values())
    }


def display_sample_results(tickets: List[Dict], categorized: List[Tuple[str, str]]):
    """
    Display sample categorization results for manual review

    Args:
        tickets: Original tickets
        categorized: Categorization results
    """
    print("\n" + "="*80)
    print("📋 SAMPLE CATEGORIZATION RESULTS (Manual Review)")
    print("="*80 + "\n")

    # Create lookup for easier access
    tier_lookup = {ticket_id: tier for ticket_id, tier in categorized}

    # Display first 20 samples
    for i, ticket in enumerate(tickets[:20]):
        ticket_id = ticket['ticket_id']
        tier = tier_lookup.get(ticket_id, 'UNKNOWN')

        print(f"Ticket {i+1}: {ticket_id}")
        print(f"  Tier: {tier}")
        print(f"  Title: {ticket['title'][:80] if ticket['title'] else 'N/A'}")
        print(f"  Category: {ticket['category']}")
        print(f"  Root Cause: {ticket['root_cause']}")
        print()

    print("="*80)
    print("⚠️  MANUAL REVIEW REQUIRED")
    print("="*80)
    print("\nReview the sample categorizations above.")
    print("Verify that tier assignments are accurate (≥90% accuracy expected).")
    print("\nIf accuracy is acceptable, run full backfill with: --full")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Backfill support_tier column in PostgreSQL')
    parser.add_argument('--sample', action='store_true', help=f'Sample mode (categorize {SAMPLE_SIZE} tickets for validation)')
    parser.add_argument('--full', action='store_true', help='Full backfill mode (all tickets)')

    args = parser.parse_args()

    if not args.sample and not args.full:
        parser.error("Must specify either --sample or --full")

    print("\n" + "="*80)
    print("🔄 ServiceDesk Tier Backfill Script - PostgreSQL Edition")
    print("="*80)
    print(f"Project: TIER-TRACKER-001")
    print(f"Database: {DOCKER_CONTAINER} / {DB_NAME}")
    print(f"Mode: {'SAMPLE' if args.sample else 'FULL BACKFILL'}")
    print("="*80 + "\n")

    # Step 1: Fetch tickets
    start_time = time.time()
    tickets = fetch_tickets(sample_mode=args.sample)

    if len(tickets) == 0:
        print("✅ No tickets to backfill (all tickets already have support_tier)")
        return

    # Step 2: Categorize tickets
    categorized = categorize_tickets(tickets)

    # Step 3: Display sample results (sample mode only)
    if args.sample:
        display_sample_results(tickets, categorized)

        # Show tier distribution
        tier_counts = {'L1': 0, 'L2': 0, 'L3': 0}
        for _, tier in categorized:
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        total = len(categorized)
        print("\n📊 TIER DISTRIBUTION (Sample)")
        print("="*80)
        for tier in ['L1', 'L2', 'L3']:
            count = tier_counts[tier]
            pct = count / total * 100 if total > 0 else 0
            print(f"  {tier}: {count:,} tickets ({pct:.1f}%)")
        print("="*80 + "\n")

        elapsed = time.time() - start_time
        print(f"⏱️  Sample categorization completed in {elapsed:.1f} seconds\n")
        return

    # Step 4: Backfill in batches (full mode)
    print(f"💾 Backfilling {len(categorized):,} tickets in batches of {BATCH_SIZE}...")

    batches = [categorized[i:i+BATCH_SIZE] for i in range(0, len(categorized), BATCH_SIZE)]
    total_batches = len(batches)

    for batch_idx, batch in enumerate(batches):
        batch_num = batch_idx + 1
        print(f"   Batch {batch_num}/{total_batches}: Updating {len(batch):,} tickets...")

        success = backfill_batch(batch)

        if not success:
            print(f"❌ Backfill failed at batch {batch_num}")
            print(f"   Successfully updated {batch_idx * BATCH_SIZE:,} tickets")
            print(f"   Remaining: {len(categorized) - (batch_idx * BATCH_SIZE):,} tickets")
            sys.exit(1)

    print(f"✅ Backfill complete! Updated {len(categorized):,} tickets\n")

    # Step 5: Validate results
    stats = validate_backfill()

    print("="*80)
    print("📊 BACKFILL VALIDATION RESULTS")
    print("="*80)
    print(f"  NULL tiers remaining: {stats['null_count']:,}")
    print(f"  L1 tickets: {stats['l1_count']:,} ({stats['l1_count']/stats['total']*100:.1f}%)")
    print(f"  L2 tickets: {stats['l2_count']:,} ({stats['l2_count']/stats['total']*100:.1f}%)")
    print(f"  L3 tickets: {stats['l3_count']:,} ({stats['l3_count']/stats['total']*100:.1f}%)")
    print(f"  Total categorized: {stats['total']:,}")
    print("="*80 + "\n")

    # Step 6: Performance metrics
    elapsed = time.time() - start_time
    tickets_per_sec = len(categorized) / elapsed if elapsed > 0 else 0

    print("="*80)
    print("⚡ PERFORMANCE METRICS")
    print("="*80)
    print(f"  Total time: {elapsed:.1f} seconds")
    print(f"  Throughput: {tickets_per_sec:.0f} tickets/second")
    print(f"  Performance SLO: <300 seconds (5 minutes)")
    print(f"  Status: {'✅ PASS' if elapsed < 300 else '❌ FAIL'}")
    print("="*80 + "\n")

    # Step 7: Industry benchmark comparison
    l1_pct = stats['l1_count'] / stats['total'] * 100 if stats['total'] > 0 else 0
    l2_pct = stats['l2_count'] / stats['total'] * 100 if stats['total'] > 0 else 0
    l3_pct = stats['l3_count'] / stats['total'] * 100 if stats['total'] > 0 else 0

    print("="*80)
    print("🎯 INDUSTRY BENCHMARK COMPARISON")
    print("="*80)
    print(f"  L1: {l1_pct:.1f}% (Benchmark: 60-70%)")
    print(f"  L2: {l2_pct:.1f}% (Benchmark: 25-35%)")
    print(f"  L3: {l3_pct:.1f}% (Benchmark: 5-10%)")
    print("="*80 + "\n")

    if stats['null_count'] == 0:
        print("✅ SUCCESS: All tickets categorized, no NULL tiers remaining\n")
    else:
        print(f"⚠️  WARNING: {stats['null_count']:,} tickets still have NULL support_tier\n")


if __name__ == "__main__":
    main()
