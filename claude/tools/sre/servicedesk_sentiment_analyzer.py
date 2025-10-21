#!/usr/bin/env python3
"""
ServiceDesk Comment Sentiment Analyzer
Analyzes customer sentiment using local Ollama LLM (gemma2:9b)

Based on testing results (Phase 119+):
- gemma2:9b: 78% accuracy (+46% vs keyword baseline)
- Processes all ServiceDesk comments for sentiment analysis
- Zero external API costs, complete privacy

Author: Maia System
Created: 2025-10-21
"""

import os
import sys
import json
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"


class ServiceDeskSentimentAnalyzer:
    """Analyze ServiceDesk comment sentiment using Ollama gemma2:9b"""

    def __init__(self, db_path: str = None, llm_model: str = "gemma2:9b"):
        """Initialize sentiment analyzer (default: gemma2:9b - 78% accuracy)"""
        self.db_path = db_path or str(DB_PATH)
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434"

        # Create sentiment results table if not exists
        self._init_sentiment_table()

        print(f"✅ ServiceDesk Sentiment Analyzer initialized")
        print(f"   LLM: {llm_model}")
        print(f"   Database: {self.db_path}")

    def _init_sentiment_table(self):
        """Create comment_sentiment table for storing LLM analysis results"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comment_sentiment (
                comment_id TEXT PRIMARY KEY,
                ticket_id TEXT,
                user_name TEXT,
                team TEXT,
                comment_type TEXT,
                created_time TIMESTAMP,
                cleaned_text TEXT,
                sentiment TEXT,
                confidence REAL,
                reasoning TEXT,
                model_used TEXT,
                latency_ms INTEGER,
                analysis_timestamp TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets("TKT-Ticket ID")
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_comment_sentiment_ticket ON comment_sentiment(ticket_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comment_sentiment_created ON comment_sentiment(created_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_comment_sentiment_sentiment ON comment_sentiment(sentiment)")
        conn.commit()
        conn.close()
        print("   ✅ comment_sentiment table ready")

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

        # Remove email headers (From:, Sent:, To:, etc.)
        text = re.sub(r'(From:|Sent:|To:|Cc:|Subject:)[^\n]*', '', text)

        # Truncate extremely long comments to save LLM tokens
        if len(text) > 2000:
            text = text[:2000] + "... [truncated]"

        return text

    def analyze_sentiment(self, text: str) -> Tuple[str, float, str, int]:
        """
        Analyze sentiment using Ollama LLM with few-shot prompting

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

NEGATIVE - Problem unresolved despite efforts:
Comment: "Thanks for sending through the credentials. Tried all of them, none worked."
{{
    "sentiment": "negative",
    "confidence": 0.85,
    "reasoning": "Despite thanks, credentials failed, problem persists"
}}

NEUTRAL - Standard informational update:
Comment: "This is to acknowledge receiving your request. Ticket has been assigned to the relevant group."
{{
    "sentiment": "neutral",
    "confidence": 0.90,
    "reasoning": "Standard acknowledgment template, no emotion expressed"
}}

MIXED - Appreciation with ongoing concern:
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
                        "temperature": 0.1,  # Lower temperature for more consistent results
                        "num_predict": 150   # Limit output length
                    }
                },
                timeout=60
            )
            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                response_text = response.json()['response'].strip()

                # Extract JSON from response (handle markdown code blocks)
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                try:
                    parsed = json.loads(response_text)
                    sentiment = parsed.get('sentiment', 'neutral').lower()
                    confidence = float(parsed.get('confidence', 0.5))
                    reasoning = parsed.get('reasoning', 'No reasoning provided')[:200]  # Truncate

                    return sentiment, confidence, reasoning, latency

                except json.JSONDecodeError:
                    print(f"\n⚠️  Failed to parse JSON: {response_text[:100]}")
                    return 'neutral', 0.3, f"Parse error", latency
            else:
                return 'neutral', 0.0, f"HTTP {response.status_code}", latency

        except Exception as e:
            latency = int((time.time() - start) * 1000) if 'start' in locals() else 0
            return 'neutral', 0.0, f"Error: {str(e)[:50]}", latency

    def get_unanalyzed_comments(self, limit: int = None) -> List[Dict]:
        """Get comments that haven't been analyzed for sentiment yet"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        # Get comments not in comment_sentiment table
        query = """
            SELECT
                c.comment_id,
                c.ticket_id,
                c.user_name,
                c.team,
                c.comment_type,
                c.created_time,
                c.comment_text
            FROM comments c
            LEFT JOIN comment_sentiment cs ON c.comment_id = cs.comment_id
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
        rows = cursor.fetchall()
        conn.close()

        comments = []
        for row in rows:
            comments.append({
                'comment_id': row[0],
                'ticket_id': row[1],
                'user_name': row[2],
                'team': row[3],
                'comment_type': row[4],
                'created_time': row[5],
                'comment_text': row[6]
            })

        return comments

    def analyze_batch(self, batch_size: int = None, verbose: bool = True) -> Dict:
        """
        Analyze unanalyzed comments in batch

        Args:
            batch_size: Number of comments to analyze (None = all unanalyzed)
            verbose: Print progress updates

        Returns:
            Dict with statistics
        """
        print(f"\n{'='*80}")
        print(f"SERVICEDESK SENTIMENT ANALYSIS - {self.llm_model}")
        print(f"{'='*80}\n")

        # Get unanalyzed comments
        comments = self.get_unanalyzed_comments(limit=batch_size)
        total = len(comments)

        if total == 0:
            print("✅ No new comments to analyze!")
            return {'analyzed': 0, 'total': 0}

        print(f"📊 Found {total} comments to analyze")
        print(f"🤖 Using model: {self.llm_model}\n")

        # Analyze each comment
        analyzed = 0
        errors = 0
        start_time = time.time()

        conn = sqlite3.connect(self.db_path, timeout=30.0)

        for i, comment in enumerate(comments, 1):
            if verbose:
                print(f"  [{i}/{total}] Analyzing comment {comment['comment_id']}...", end=' ')

            # Clean HTML
            cleaned_text = self.clean_html_comment(comment['comment_text'])

            # Analyze sentiment
            sentiment, confidence, reasoning, latency_ms = self.analyze_sentiment(cleaned_text)

            if sentiment != 'neutral' or confidence > 0.5:  # Valid analysis
                # Store results
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO comment_sentiment
                        (comment_id, ticket_id, user_name, team, comment_type, created_time,
                         cleaned_text, sentiment, confidence, reasoning, model_used, latency_ms, analysis_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        comment['comment_id'],
                        comment['ticket_id'],
                        comment['user_name'],
                        comment['team'],
                        comment['comment_type'],
                        comment['created_time'],
                        cleaned_text[:500],  # Truncate for storage
                        sentiment,
                        confidence,
                        reasoning,
                        self.llm_model,
                        latency_ms,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    analyzed += 1

                    if verbose:
                        print(f"✅ {sentiment} (conf: {confidence:.2f}, {latency_ms}ms)")
                except Exception as e:
                    errors += 1
                    if verbose:
                        print(f"❌ Error: {str(e)[:50]}")
            else:
                errors += 1
                if verbose:
                    print(f"⚠️  Failed analysis")

            # Progress update every 10 comments
            if i % 10 == 0 and verbose:
                elapsed = time.time() - start_time
                rate = i / elapsed
                remaining = (total - i) / rate if rate > 0 else 0
                print(f"\n  Progress: {i}/{total} ({i/total*100:.1f}%) - {rate:.1f} comments/sec - ETA: {remaining/60:.1f}min\n")

        conn.close()

        # Final statistics
        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"✅ ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"  Total processed: {total}")
        print(f"  Successfully analyzed: {analyzed}")
        print(f"  Errors: {errors}")
        print(f"  Time elapsed: {elapsed:.1f}s")
        print(f"  Rate: {total/elapsed:.1f} comments/sec")
        print(f"{'='*80}\n")

        return {
            'analyzed': analyzed,
            'total': total,
            'errors': errors,
            'elapsed_seconds': elapsed,
            'rate': total/elapsed if elapsed > 0 else 0
        }

    def get_sentiment_statistics(self) -> Dict:
        """Get sentiment statistics from database"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        # Overall sentiment distribution
        cursor.execute("""
            SELECT sentiment, COUNT(*) as count, AVG(confidence) as avg_conf
            FROM comment_sentiment
            GROUP BY sentiment
            ORDER BY count DESC
        """)
        distribution = {row[0]: {'count': row[1], 'avg_confidence': row[2]} for row in cursor.fetchall()}

        # Total analyzed
        cursor.execute("SELECT COUNT(*) FROM comment_sentiment")
        total = cursor.fetchone()[0]

        conn.close()

        return {
            'total_analyzed': total,
            'distribution': distribution
        }


def main():
    """Main entry point for sentiment analysis"""
    import argparse

    parser = argparse.ArgumentParser(description='ServiceDesk Sentiment Analyzer')
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Number of comments to analyze (default: all unanalyzed)')
    parser.add_argument('--model', type=str, default='gemma2:9b',
                       help='Ollama model to use (default: gemma2:9b)')
    parser.add_argument('--stats', action='store_true',
                       help='Show sentiment statistics only (no analysis)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress verbose output')

    args = parser.parse_args()

    analyzer = ServiceDeskSentimentAnalyzer(llm_model=args.model)

    if args.stats:
        # Show statistics only
        stats = analyzer.get_sentiment_statistics()
        print(f"\n{'='*80}")
        print(f"SENTIMENT STATISTICS")
        print(f"{'='*80}")
        print(f"  Total analyzed: {stats['total_analyzed']}")
        print(f"\n  Distribution:")
        for sentiment, data in stats['distribution'].items():
            pct = data['count'] / stats['total_analyzed'] * 100 if stats['total_analyzed'] > 0 else 0
            print(f"    {sentiment:10s}: {data['count']:4d} ({pct:5.1f}%) - avg conf: {data['avg_confidence']:.2f}")
        print(f"{'='*80}\n")
    else:
        # Run analysis
        result = analyzer.analyze_batch(
            batch_size=args.batch_size,
            verbose=not args.quiet
        )


if __name__ == "__main__":
    main()
