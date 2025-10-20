#!/usr/bin/env python3
"""
Sentiment Analysis Validation Dataset Generator

Generates a stratified sample of 500 comments for manual labeling:
- 200 keyword-positive (for validation)
- 200 keyword-negative (for validation)
- 100 keyword-neutral (edge cases)

Outputs CSV for manual labeling with columns:
- comment_id, comment_text, keyword_sentiment, manual_sentiment, notes

Created: 2025-10-20 (TDD Phase 1)
"""

import os
import sys
import csv
import psycopg2
from pathlib import Path
from datetime import datetime

MAIA_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = MAIA_ROOT / "tests/sentiment_validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def connect_postgres():
    """Connect to PostgreSQL"""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="servicedesk",
        user="servicedesk_user",
        password="servicedesk_password"
    )

def generate_validation_dataset():
    """Generate 500-comment stratified sample"""
    print("🔍 Generating sentiment validation dataset...")

    conn = connect_postgres()
    cur = conn.cursor()

    # Query for stratified sample
    query = """
    WITH keyword_classified AS (
        SELECT
            comment_id,
            ticket_id,
            comment_text,
            created_time,
            CASE
                WHEN LOWER(comment_text) ~ '.*(thank|great|excellent|happy|appreciate|wonderful|fantastic|perfect|amazing).*'
                THEN 'positive'
                WHEN LOWER(comment_text) ~ '.*(issue|problem|unhappy|frustrated|angry|disappointed|urgent|critical|error|fail).*'
                THEN 'negative'
                ELSE 'neutral'
            END as keyword_sentiment
        FROM servicedesk.comments
        WHERE visible_to_customer = 'Yes'
          AND created_time >= '2025-07-01'
          AND LENGTH(comment_text) BETWEEN 50 AND 800
          AND comment_text NOT LIKE '%[AUTOMATION - Workflow]%'
    )
    (
        SELECT * FROM keyword_classified WHERE keyword_sentiment = 'positive' ORDER BY RANDOM() LIMIT 200
    )
    UNION ALL
    (
        SELECT * FROM keyword_classified WHERE keyword_sentiment = 'negative' ORDER BY RANDOM() LIMIT 200
    )
    UNION ALL
    (
        SELECT * FROM keyword_classified WHERE keyword_sentiment = 'neutral' ORDER BY RANDOM() LIMIT 100
    );
    """

    cur.execute(query)
    results = cur.fetchall()

    # Write to CSV
    output_file = OUTPUT_DIR / f"sentiment_validation_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'comment_id',
            'ticket_id',
            'comment_text',
            'created_time',
            'keyword_sentiment',
            'manual_sentiment',  # To be filled manually
            'confidence',  # 1-5 scale
            'notes'  # Edge case notes
        ])

        for row in results:
            writer.writerow([
                row[0],  # comment_id
                row[1],  # ticket_id
                row[2][:500],  # comment_text (truncate for readability)
                row[3],  # created_time
                row[4],  # keyword_sentiment
                '',  # manual_sentiment (empty for labeling)
                '',  # confidence (empty for labeling)
                ''   # notes (empty for labeling)
            ])

    cur.close()
    conn.close()

    print(f"✅ Generated {len(results)} comments for validation")
    print(f"📄 Output: {output_file}")
    print(f"\n📋 Next Steps:")
    print(f"   1. Open CSV in spreadsheet app")
    print(f"   2. Fill 'manual_sentiment' column: positive/negative/neutral/mixed")
    print(f"   3. Fill 'confidence' column: 1 (unsure) to 5 (very confident)")
    print(f"   4. Add notes for edge cases (sarcasm, negation, mixed)")
    print(f"   5. Save and use for model testing")

    return output_file

if __name__ == "__main__":
    generate_validation_dataset()
