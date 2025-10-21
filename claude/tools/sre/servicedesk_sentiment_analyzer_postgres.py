#!/usr/bin/env python3
"""
ServiceDesk Comment Sentiment Analyzer - PostgreSQL Version
Analyzes customer sentiment using gemma2:9b LLM and writes directly to PostgreSQL

Modern architecture (replaces SQLite+ETL legacy pattern):
PostgreSQL → Analysis → PostgreSQL → Grafana (real-time)

Based on servicedesk_quality_analyzer_postgres.py pattern
Uses gemma2:9b model (83% accuracy, +51% vs keyword baseline)

Author: Maia System
Created: 2025-10-21
"""

import sys
import json
import psycopg2
import requests
import time
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Tuple

# PostgreSQL connection details
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'servicedesk',
    'user': 'servicedesk_user',
    'password': 'ServiceDesk2025!SecurePass'
}


class PostgreSQLSentimentAnalyzer:
    """PostgreSQL-enabled sentiment analyzer using gemma2:9b (83% accuracy)"""

    def __init__(self, llm_model: str = "gemma2:9b"):
        """Initialize with PostgreSQL connection"""
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434"

        # Connect to PostgreSQL
        self.pg_conn = psycopg2.connect(**PG_CONFIG)
        print(f"✅ Connected to PostgreSQL: servicedesk database")
        print(f"🤖 LLM Model: {llm_model} (83% accuracy)")

    def clean_html_comment(self, html_text: str) -> str:
        """Extract clean text from HTML-formatted comments"""
        if not html_text:
            return ""

        soup = BeautifulSoup(html_text, 'html.parser')

        # Remove script/style tags
        for tag in soup(['script', 'style']):
            tag.decompose()

        # Extract text
        text = soup.get_text(separator=' ', strip=True)

        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove email headers
        text = re.sub(r'(From:|Sent:|To:|Cc:|Subject:)[^\n]*', '', text)

        # Truncate long comments
        if len(text) > 2000:
            text = text[:2000] + "... [truncated]"

        return text

    def analyze_sentiment(self, text: str) -> Tuple[str, float, str, int]:
        """
        Analyze sentiment using Ollama gemma2:9b with few-shot prompting

        Returns: (sentiment, confidence, reasoning, latency_ms)
        """
        if not text or len(text.strip()) < 10:
            return 'neutral', 0.0, 'Text too short for analysis', 0

        prompt = f"""Analyze the sentiment of this customer support comment.

IMPORTANT INSTRUCTIONS:
1. DEFAULT to positive, negative, or neutral - only use "mixed" when CLEARLY both sentiments exist
2. MIXED requires BOTH: explicit gratitude/appreciation AND explicit frustration/problem
3. "Thanks but [problem still exists]" = mixed
4. "Working on it, please test" = neutral (NOT mixed - just uncertainty)
5. Standard acknowledgments with no emotion = neutral (NOT positive)
6. Respond ONLY with valid JSON (no markdown, no extra text)

EXAMPLES OF EACH SENTIMENT:

POSITIVE - Problem resolved successfully:
Comment: "We successfully reset the password. Please refer to the following link for the credentials."
{{
    "sentiment": "positive",
    "confidence": 0.95,
    "reasoning": "Problem resolved, credentials provided, successful outcome"
}}

NEGATIVE - Complete failure explicitly stated (RARE - only when stating total failure):
Comment: "Thanks for sending through the credentials. Tried all of them, none worked."
{{
    "sentiment": "negative",
    "confidence": 0.85,
    "reasoning": "Despite politeness, complete failure stated - nothing worked at all"
}}

NEUTRAL - Issue not resolved yet, no frustration (NOT negative):
Comment: "Could you please let me know when you're online so that I can look into this? We may be able to rectify the issue with a simple reboot."
{{
    "sentiment": "neutral",
    "confidence": 0.90,
    "reasoning": "Problem exists but no frustration, just coordinating next steps"
}}

NEUTRAL - Standard informational update:
Comment: "This is to acknowledge receiving your request. Ticket has been assigned to the relevant group."
{{
    "sentiment": "neutral",
    "confidence": 0.90,
    "reasoning": "Standard acknowledgment template, no emotion expressed"
}}

MIXED - Appreciation with ongoing concern (RARE - only when BOTH present):
Comment: "Thanks Nish, Sorry I should clarify, we can login to Magento but there is not application setting page."
{{
    "sentiment": "mixed",
    "confidence": 0.80,
    "reasoning": "Gratitude expressed (positive) but issue still exists (negative)"
}}

NOW ANALYZE THIS COMMENT:

Comment: {text}

JSON response:"""

        try:
            start = time.time()
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150
                    }
                },
                timeout=60
            )
            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                response_text = response.json()['response'].strip()

                # Extract JSON from response
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                try:
                    parsed = json.loads(response_text)
                    sentiment = parsed.get('sentiment', 'neutral').lower()
                    confidence = float(parsed.get('confidence', 0.5))
                    reasoning = parsed.get('reasoning', 'No reasoning provided')[:200]

                    return sentiment, confidence, reasoning, latency

                except json.JSONDecodeError:
                    return 'neutral', 0.3, 'Parse error', latency
            else:
                return 'neutral', 0.0, f"HTTP {response.status_code}", latency

        except Exception as e:
            latency = int((time.time() - start) * 1000) if 'start' in locals() else 0
            return 'neutral', 0.0, f"Error: {str(e)[:50]}", latency

    def get_unanalyzed_comments(self, limit: int = None) -> List[Dict]:
        """Get comments from PostgreSQL that haven't been analyzed yet"""
        cursor = self.pg_conn.cursor()

        query = """
            SELECT
                c.comment_id,
                c.ticket_id,
                c.user_name,
                c.team,
                c.comment_type,
                c.created_time,
                c.comment_text
            FROM servicedesk.comments c
            LEFT JOIN servicedesk.comment_sentiment cs ON c.comment_id = cs.comment_id
            WHERE cs.comment_id IS NULL
                AND c.user_name != 'brian'
                AND c.comment_type NOT IN ('Automation', 'System')
                AND c.comment_text IS NOT NULL
                AND LENGTH(c.comment_text) > 10
            ORDER BY c.created_time DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]

        comments = []
        for row in cursor.fetchall():
            comment = dict(zip(columns, row))
            comments.append(comment)

        cursor.close()
        return comments

    def analyze_and_store(self, comments: List[Dict], batch_size: int = 100):
        """Analyze comments and store results in PostgreSQL"""
        cursor = self.pg_conn.cursor()

        total = len(comments)
        processed = 0
        errors = 0
        start_time = time.time()

        print(f"\n📊 Analyzing {total} comments...")
        print(f"🤖 Model: {self.llm_model}")

        for i, comment in enumerate(comments, 1):
            # Clean HTML
            cleaned_text = self.clean_html_comment(comment['comment_text'])

            # Analyze sentiment
            sentiment, confidence, reasoning, latency_ms = self.analyze_sentiment(cleaned_text)

            if sentiment != 'neutral' or confidence > 0.5:  # Valid analysis
                try:
                    cursor.execute("""
                        INSERT INTO servicedesk.comment_sentiment (
                            comment_id, ticket_id, user_name, team, comment_type, created_time,
                            cleaned_text, sentiment, confidence, reasoning, model_used, latency_ms, analysis_timestamp
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (comment_id) DO UPDATE SET
                            sentiment = EXCLUDED.sentiment,
                            confidence = EXCLUDED.confidence,
                            reasoning = EXCLUDED.reasoning,
                            model_used = EXCLUDED.model_used,
                            latency_ms = EXCLUDED.latency_ms,
                            analysis_timestamp = EXCLUDED.analysis_timestamp
                    """, (
                        int(comment['comment_id']),
                        int(comment['ticket_id']),
                        comment['user_name'],
                        comment['team'],
                        comment['comment_type'],
                        comment['created_time'],
                        cleaned_text[:500],
                        sentiment,
                        confidence,
                        reasoning,
                        self.llm_model,
                        latency_ms,
                        datetime.now()
                    ))
                    processed += 1

                except Exception as e:
                    errors += 1
                    if errors < 5:  # Only print first few errors
                        print(f"  ❌ Error on comment {comment['comment_id']}: {str(e)[:100]}")
            else:
                errors += 1

            # Commit in batches
            if i % batch_size == 0:
                self.pg_conn.commit()
                elapsed = time.time() - start_time
                rate = i / elapsed
                remaining = (total - i) / rate if rate > 0 else 0
                print(f"  Progress: {i}/{total} ({i/total*100:.1f}%) - {rate:.1f}/sec - ETA: {remaining/60:.0f}min - {sentiment} (conf: {confidence:.2f})")

        self.pg_conn.commit()
        cursor.close()

        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"✅ ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"  Total processed: {total}")
        print(f"  Successfully analyzed: {processed}")
        print(f"  Errors: {errors}")
        print(f"  Time elapsed: {elapsed:.1f}s")
        print(f"  Rate: {total/elapsed:.1f} comments/sec")
        print(f"{'='*80}\n")

        return {'analyzed': processed, 'total': total, 'errors': errors}

    def get_sentiment_statistics(self) -> Dict:
        """Get sentiment statistics from PostgreSQL"""
        cursor = self.pg_conn.cursor()

        # Overall distribution
        cursor.execute("""
            SELECT sentiment, COUNT(*) as count, ROUND(AVG(confidence)::numeric, 2) as avg_conf
            FROM servicedesk.comment_sentiment
            GROUP BY sentiment
            ORDER BY count DESC
        """)
        distribution = {row[0]: {'count': row[1], 'avg_confidence': float(row[2])} for row in cursor.fetchall()}

        # Total analyzed
        cursor.execute("SELECT COUNT(*) FROM servicedesk.comment_sentiment")
        total = cursor.fetchone()[0]

        cursor.close()

        return {
            'total_analyzed': total,
            'distribution': distribution
        }

    def close(self):
        """Close PostgreSQL connection"""
        self.pg_conn.close()


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='ServiceDesk Sentiment Analyzer - PostgreSQL')
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Number of comments to analyze (default: all unanalyzed)')
    parser.add_argument('--model', type=str, default='gemma2:9b',
                       help='Ollama model to use (default: gemma2:9b)')
    parser.add_argument('--stats', action='store_true',
                       help='Show sentiment statistics only (no analysis)')
    parser.add_argument('--commit-size', type=int, default=100,
                       help='Commit every N records (default: 100)')

    args = parser.parse_args()

    analyzer = PostgreSQLSentimentAnalyzer(llm_model=args.model)

    if args.stats:
        # Show statistics only
        stats = analyzer.get_sentiment_statistics()
        print(f"\n{'='*80}")
        print(f"SENTIMENT STATISTICS (PostgreSQL)")
        print(f"{'='*80}")
        print(f"  Total analyzed: {stats['total_analyzed']:,}")
        print(f"\n  Distribution:")
        for sentiment, data in stats['distribution'].items():
            pct = data['count'] / stats['total_analyzed'] * 100 if stats['total_analyzed'] > 0 else 0
            print(f"    {sentiment:10s}: {data['count']:5,} ({pct:5.1f}%) - avg conf: {data['avg_confidence']:.2f}")
        print(f"{'='*80}\n")
    else:
        # Run analysis
        print("\n📥 PHASE 1: Extracting unanalyzed comments from PostgreSQL...")
        comments = analyzer.get_unanalyzed_comments(limit=args.batch_size)

        if not comments:
            print("✅ No new comments to analyze!")
            stats = analyzer.get_sentiment_statistics()
            print(f"\n📊 Current total: {stats['total_analyzed']:,} comments analyzed")
        else:
            print(f"   Found {len(comments):,} unanalyzed comments")

            print("\n🤖 PHASE 2: Analyzing with gemma2:9b and storing to PostgreSQL...")
            result = analyzer.analyze_and_store(comments, batch_size=args.commit_size)

            print("\n📊 PHASE 3: Summary...")
            stats = analyzer.get_sentiment_statistics()
            print(f"\n{'='*80}")
            print(f"FINAL STATISTICS")
            print(f"{'='*80}")
            print(f"  Total in database: {stats['total_analyzed']:,}")
            for sentiment, data in stats['distribution'].items():
                pct = data['count'] / stats['total_analyzed'] * 100 if stats['total_analyzed'] > 0 else 0
                print(f"    {sentiment:10s}: {data['count']:5,} ({pct:5.1f}%)")
            print(f"{'='*80}\n")

    analyzer.close()
    print("✅ Done! Grafana dashboard will update automatically.\n")


if __name__ == "__main__":
    main()
