#!/usr/bin/env python3
"""
ServiceDesk Comment Quality Analyzer - PostgreSQL Version
Analyzes communication quality and writes directly to PostgreSQL

Uses the same LLM logic as servicedesk_comment_quality_analyzer.py
but reads/writes to PostgreSQL instead of SQLite.

Author: Maia System
Created: 2025-10-20
"""

import sys
import json
import psycopg2
from datetime import datetime
from typing import List, Dict

# Import the existing analyzer for LLM logic
sys.path.insert(0, '/Users/naythandawe/git/maia')
from claude.tools.sre.servicedesk_comment_quality_analyzer import ServiceDeskCommentAnalyzer

# PostgreSQL connection details
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'servicedesk',
    'user': 'servicedesk_user',
    'password': 'ServiceDesk2025!SecurePass'
}


class PostgreSQLQualityAnalyzer:
    """PostgreSQL-enabled quality analyzer"""

    def __init__(self, llm_model: str = "llama3.1:8b"):
        """Initialize with PostgreSQL connection"""
        self.llm_model = llm_model

        # Initialize the LLM analyzer (for analyze_comment_quality method)
        # Pass a dummy SQLite path since we won't use it for storage
        self.analyzer = ServiceDeskCommentAnalyzer(
            db_path="/tmp/dummy.db",
            llm_model=llm_model
        )

        # Connect to PostgreSQL
        self.pg_conn = psycopg2.connect(**PG_CONFIG)
        print(f"✅ Connected to PostgreSQL: servicedesk database")

    def extract_comments(self, sample_size: int = 1000) -> List[Dict]:
        """Extract random sample of comments from PostgreSQL"""
        cursor = self.pg_conn.cursor()

        query = f"""
            SELECT
                ticket_id, user_name, team, comment_type,
                comment_text, created_time, visible_to_customer
            FROM servicedesk.comments
            WHERE comment_type = 'comments'
            ORDER BY RANDOM()
            LIMIT {sample_size}
        """

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]

        comments = []
        for row in cursor.fetchall():
            comment = dict(zip(columns, row))
            comments.append(comment)

        cursor.close()
        print(f"   ✅ Extracted {len(comments)} comments from PostgreSQL")
        return comments

    def analyze_and_store(self, comments: List[Dict], batch_size: int = 10):
        """Analyze comments and store results in PostgreSQL"""
        cursor = self.pg_conn.cursor()

        total = len(comments)
        processed = 0

        print(f"\n📊 Analyzing {total} comments in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = comments[i:i+batch_size]

            for comment in batch:
                # Check if already analyzed
                cursor.execute("""
                    SELECT 1 FROM servicedesk.comment_quality
                    WHERE ticket_id = %s::text AND created_time = %s
                """, (str(comment['ticket_id']), comment['created_time']))

                if cursor.fetchone():
                    processed += 1
                    continue

                # Analyze comment using existing LLM logic
                analysis = self.analyzer.analyze_comment_quality(comment)
                cleaned_text = self.analyzer.clean_html_comment(comment['comment_text'])

                # Store in PostgreSQL (no unique constraint, so skip ON CONFLICT)
                cursor.execute("""
                    INSERT INTO servicedesk.comment_quality (
                        comment_id, ticket_id, user_name, team, comment_type, created_time,
                        cleaned_text, professionalism_score, clarity_score, empathy_score,
                        actionability_score, quality_score, quality_tier, content_tags,
                        red_flags, intent_summary, analysis_timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"{comment['ticket_id']}_{comment['created_time']}",
                    str(comment['ticket_id']),
                    comment['user_name'],
                    comment['team'],
                    comment['comment_type'],
                    comment['created_time'],
                    cleaned_text,
                    analysis.get('professionalism_score', 3),
                    analysis.get('clarity_score', 3),
                    analysis.get('empathy_score', 3),
                    analysis.get('actionability_score', 3),
                    analysis['quality_score'],
                    analysis['quality_tier'],
                    json.dumps(analysis.get('content_tags', [])),
                    json.dumps(analysis.get('red_flags', [])),
                    analysis.get('intent_summary', ''),
                    datetime.now()
                ))

                processed += 1

                if processed % 10 == 0:
                    self.pg_conn.commit()
                    print(f"   Progress: {processed}/{total} ({processed/total*100:.1f}%)")

        self.pg_conn.commit()
        cursor.close()

        print(f"\n✅ Analysis complete: {processed}/{total} comments processed")

    def generate_summary(self):
        """Generate summary from PostgreSQL data"""
        cursor = self.pg_conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT professionalism_score) as unique_prof,
                COUNT(DISTINCT clarity_score) as unique_clarity,
                MIN(quality_score) as min_q,
                MAX(quality_score) as max_q,
                ROUND(AVG(quality_score)::numeric, 2) as avg_q
            FROM servicedesk.comment_quality
        """)

        stats = cursor.fetchone()
        cursor.close()

        print(f"\n📊 QUALITY ANALYSIS SUMMARY (PostgreSQL):")
        print(f"   Total analyzed: {stats[0]}")
        print(f"   Unique professionalism scores: {stats[1]}")
        print(f"   Unique clarity scores: {stats[2]}")
        print(f"   Quality score range: {stats[3]:.2f} - {stats[4]:.2f}")
        print(f"   Average quality: {stats[5]}")

    def close(self):
        """Close PostgreSQL connection"""
        self.pg_conn.close()


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="ServiceDesk Quality Analyzer - PostgreSQL")
    parser.add_argument("--sample-size", type=int, default=1000, help="Number of comments to analyze")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--llm-model", default="llama3.1:8b", help="Ollama LLM model to use")

    args = parser.parse_args()

    analyzer = PostgreSQLQualityAnalyzer(llm_model=args.llm_model)

    print("\n📥 PHASE 1: Extracting comments from PostgreSQL...")
    comments = analyzer.extract_comments(sample_size=args.sample_size)

    print("\n🤖 PHASE 2: Analyzing with Ollama LLM and storing to PostgreSQL...")
    analyzer.analyze_and_store(comments, batch_size=args.batch_size)

    print("\n📊 PHASE 3: Summary...")
    analyzer.generate_summary()

    analyzer.close()
    print("\n✅ Done! Grafana dashboard will update automatically.")


if __name__ == "__main__":
    main()
