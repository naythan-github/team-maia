#!/usr/bin/env python3
"""
Migrate ServiceDesk Operations Intelligence to Hybrid Architecture

Adds ChromaDB semantic layer to existing SQLite database.

Phase: 130.1 - Semantic Enhancement
Created: 2025-10-18
"""

import sqlite3
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

MAIA_ROOT = Path(__file__).parent.parent.parent
DB_PATH = MAIA_ROOT / 'data' / 'servicedesk_operations_intelligence.db'


def migrate_database():
    """Add embedding columns to support ChromaDB integration"""

    print("🔄 Migrating ServiceDesk Operations Intelligence Database to Hybrid Architecture")
    print(f"   Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if migration already applied
    cursor.execute("PRAGMA table_info(operational_insights)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'embedding_id' in columns:
        print("⚠️  Migration already applied - embedding columns exist")
        conn.close()
        return

    print("📝 Step 1: Adding embedding columns to operational_insights table")
    cursor.execute('ALTER TABLE operational_insights ADD COLUMN embedding_id TEXT')
    cursor.execute('ALTER TABLE operational_insights ADD COLUMN embedded_at TEXT')
    conn.commit()
    print("   ✅ Added: embedding_id, embedded_at")

    print()
    print("📝 Step 2: Adding embedding columns to learning_log table")
    cursor.execute('ALTER TABLE learning_log ADD COLUMN embedding_id TEXT')
    cursor.execute('ALTER TABLE learning_log ADD COLUMN embedded_at TEXT')
    conn.commit()
    print("   ✅ Added: embedding_id, embedded_at")

    print()
    print("📝 Step 3: Creating indexes for embedding lookups")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_embedding ON operational_insights(embedding_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_embedding ON learning_log(embedding_id)')
    conn.commit()
    print("   ✅ Created: idx_insights_embedding, idx_learning_embedding")

    print()
    print("✅ Migration Complete!")
    print()
    print("Next Steps:")
    print("  1. Run: python3 servicedesk_ops_intel_hybrid.py embed-all")
    print("  2. Test: python3 servicedesk_ops_intel_hybrid.py search-similar 'Azure escalation'")

    conn.close()


if __name__ == '__main__':
    migrate_database()
