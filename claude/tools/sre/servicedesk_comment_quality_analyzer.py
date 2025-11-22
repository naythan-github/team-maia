#!/usr/bin/env python3
"""
ServiceDesk Comment Quality Analyzer
Analyzes communication quality using local Ollama LLM + ChromaDB RAG

Leverages existing email_rag_ollama.py infrastructure for 100% local processing.
Zero external API costs, complete privacy for ServiceDesk data.

Author: Maia System (Phase 118.2)
Created: 2025-10-14
"""

import os
import sys
import json
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import re

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print("❌ Missing dependencies. Install: pip3 install chromadb sentence-transformers")
    print(f"   Error: {e}")
    sys.exit(1)


class ServiceDeskCommentAnalyzer:
    """Analyze ServiceDesk comment quality using Ollama LLM"""

    def __init__(self, db_path: str = None, embedding_model: str = "intfloat/e5-base-v2", llm_model: str = "llama3.1:8b"):
        """Initialize analyzer (default: intfloat/e5-base-v2, 768-dim, llama3.1:8b for quality scoring)"""
        self.db_path = db_path or str(DB_PATH)
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434"

        # Load sentence-transformers model (e5-base-v2, 768-dim)
        print(f"Loading embedding model: {embedding_model}...")
        self.embedder = SentenceTransformer(embedding_model)
        print(f"✅ Embeddings loaded: {embedding_model} ({self.embedder.get_sentence_embedding_dimension()}-dim)")

        # Initialize ChromaDB for comment storage/similarity
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_rag")
        os.makedirs(self.rag_db_path, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name="servicedesk_comments",
            metadata={"description": "ServiceDesk comments with quality analysis", "model": embedding_model}
        )

        # Create quality results table if not exists
        self._init_quality_table()

        print(f"✅ ServiceDesk Comment Analyzer initialized")
        print(f"   LLM: {llm_model}")
        print(f"   Database: {self.db_path}")

    def _init_quality_table(self):
        """Create comment_quality table for storing LLM analysis results"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comment_quality (
                comment_id TEXT PRIMARY KEY,
                ticket_id TEXT,
                user_name TEXT,
                team TEXT,
                comment_type TEXT,
                created_time TIMESTAMP,
                cleaned_text TEXT,
                professionalism_score INTEGER,
                clarity_score INTEGER,
                empathy_score INTEGER,
                actionability_score INTEGER,
                quality_score REAL,
                quality_tier TEXT,
                content_tags TEXT,
                red_flags TEXT,
                intent_summary TEXT,
                analysis_timestamp TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets("TKT-Ticket ID")
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_quality_user ON comment_quality(user_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_quality_tier ON comment_quality(quality_tier)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_quality_score ON comment_quality(quality_score)")
        conn.commit()
        conn.close()
        print("   ✅ comment_quality table ready")

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

    def extract_sample_for_analysis(self, strategy: str = 'random', sample_size: int = 3300) -> List[Dict]:
        """
        Extract sample of comments for LLM analysis

        Strategy:
        - 'random': Simple random sample (FAST, 1-2 seconds)
        - 'stratified': Complex multi-strata sample (SLOW, 60+ seconds)
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)

        samples = []

        # Fast path: Simple random sample
        if strategy == 'random':
            random_sample = f"""
                SELECT
                    ticket_id, user_name, team, comment_type,
                    comment_text, created_time, visible_to_customer
                FROM comments
                WHERE comment_type = 'comments'
                ORDER BY RANDOM()
                LIMIT {sample_size}
            """
            samples.extend(self._fetch_comments(conn, random_sample, "random_sample"))
            conn.close()
            return samples

        # Sample 1: Quick flicker agents (djain, emoazzam, mlally, aziadeh, jsingh from Phase 1)
        quick_flickers = """
            SELECT
                ticket_id, user_name, team, comment_type,
                comment_text, created_time, visible_to_customer
            FROM comments
            WHERE comment_type = 'comments'
                AND user_name IN ('djain', 'emoazzam', 'mlally', 'aziadeh', 'jsingh', 'bhishanagc', 'ddignadice')
            ORDER BY RANDOM()
            LIMIT 500
        """
        samples.extend(self._fetch_comments(conn, quick_flickers, "quick_flickers"))

        # Sample 2: High-volume agents
        high_volume = """
            WITH high_volume_agents AS (
                SELECT user_name
                FROM comments
                WHERE comment_type = 'comments'
                GROUP BY user_name
                HAVING COUNT(*) > 100
            )
            SELECT
                c.ticket_id, c.user_name, c.team, c.comment_type,
                c.comment_text, c.created_time, c.visible_to_customer
            FROM comments c
            INNER JOIN high_volume_agents h ON c.user_name = h.user_name
            WHERE c.comment_type = 'comments'
            ORDER BY RANDOM()
            LIMIT 500
        """
        samples.extend(self._fetch_comments(conn, high_volume, "high_volume"))

        # Sample 3: Tickets with multiple handoffs
        multi_handoff = """
            WITH handoff_tickets AS (
                SELECT
                    ticket_id,
                    COUNT(DISTINCT user_name) as agent_count
                FROM comments
                WHERE comment_type IN ('comments', 'worknotes')
                GROUP BY ticket_id
                HAVING agent_count >= 3
            )
            SELECT
                c.ticket_id, c.user_name, c.team, c.comment_type,
                c.comment_text, c.created_time, c.visible_to_customer
            FROM comments c
            INNER JOIN handoff_tickets h ON c.ticket_id = h.ticket_id
            WHERE c.comment_type = 'comments'
            ORDER BY RANDOM()
            LIMIT 500
        """
        samples.extend(self._fetch_comments(conn, multi_handoff, "multi_handoff"))

        # Sample 4: Random baseline
        baseline = """
            SELECT
                ticket_id, user_name, team, comment_type,
                comment_text, created_time, visible_to_customer
            FROM comments
            WHERE comment_type = 'comments'
            ORDER BY RANDOM()
            LIMIT 500
        """
        samples.extend(self._fetch_comments(conn, baseline, "baseline"))

        # Sample 5: Per-team (top 10 teams by volume)
        team_sample = """
            WITH top_teams AS (
                SELECT team, COUNT(*) as cnt
                FROM comments
                WHERE team LIKE 'Cloud -%' AND comment_type = 'comments'
                GROUP BY team
                ORDER BY cnt DESC
                LIMIT 10
            ),
            team_comments AS (
                SELECT
                    c.ticket_id, c.user_name, c.team, c.comment_type,
                    c.comment_text, c.created_time, c.visible_to_customer,
                    ROW_NUMBER() OVER (PARTITION BY c.team ORDER BY RANDOM()) as rn
                FROM comments c
                INNER JOIN top_teams t ON c.team = t.team
                WHERE c.comment_type = 'comments'
            )
            SELECT ticket_id, user_name, team, comment_type, comment_text, created_time, visible_to_customer
            FROM team_comments
            WHERE rn <= 100
        """
        samples.extend(self._fetch_comments(conn, team_sample, "team_sample"))

        # Sample 6: Time series (100 per month for trend analysis)
        time_series = """
            WITH monthly_comments AS (
                SELECT
                    ticket_id, user_name, team, comment_type,
                    comment_text, created_time, visible_to_customer,
                    strftime('%Y-%m', created_time) as month,
                    ROW_NUMBER() OVER (PARTITION BY strftime('%Y-%m', created_time) ORDER BY RANDOM()) as rn
                FROM comments
                WHERE comment_type = 'comments'
                    AND strftime('%Y-%m', created_time) IN ('2025-07', '2025-08', '2025-09')
            )
            SELECT ticket_id, user_name, team, comment_type, comment_text, created_time, visible_to_customer
            FROM monthly_comments
            WHERE rn <= 100
        """
        samples.extend(self._fetch_comments(conn, time_series, "time_series"))

        conn.close()

        # Remove duplicates (same ticket_id + created_time)
        unique_samples = {}
        for sample in samples:
            key = f"{sample['ticket_id']}_{sample['created_time']}"
            if key not in unique_samples:
                unique_samples[key] = sample

        final_samples = list(unique_samples.values())
        print(f"   ✅ Extracted {len(final_samples)} unique comments for analysis")

        return final_samples[:sample_size]  # Cap at requested size

    def _fetch_comments(self, conn, query: str, sample_type: str) -> List[Dict]:
        """Execute query and return list of comment dicts"""
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            comment = dict(zip(columns, row))
            comment['sample_type'] = sample_type
            results.append(comment)
        return results

    def analyze_comment_quality(self, comment: Dict) -> Dict:
        """
        Analyze single comment quality using Ollama LLM

        Returns quality scores, classifications, red flags
        """
        cleaned_text = self.clean_html_comment(comment['comment_text'])

        if len(cleaned_text) < 10:
            # Too short to analyze meaningfully
            return {
                'professionalism_score': 1,
                'clarity_score': 1,
                'empathy_score': 1,
                'actionability_score': 1,
                'quality_score': 1.0,
                'quality_tier': 'poor',
                'content_tags': ['empty'],
                'red_flags': ['meaningless_content'],
                'intent_summary': 'Empty or meaningless comment'
            }

        # Construct LLM prompt
        prompt = f"""You are a ServiceDesk communication quality analyst. Analyze this customer-facing comment and provide structured assessment.

COMMENT METADATA:
- Ticket ID: {comment['ticket_id']}
- Agent: {comment['user_name']}
- Team: {comment['team']}
- Created: {comment['created_time']}

COMMENT TEXT:
{cleaned_text}

ANALYSIS REQUIRED (respond in JSON format):

1. QUALITY SCORES (1-5, where 1=poor, 5=excellent):
   - professionalism: <score>
   - clarity: <score>
   - empathy: <score>
   - actionability: <score>

2. CONTENT TAGS (select all that apply):
   Options: canned_response, meaningful_update, handoff_notice, request_for_info,
   resolution_statement, apology, timeline_setting, empty_content

3. RED FLAGS (select all that apply):
   Options: no_context_handoff, defensive_tone, closes_without_confirmation,
   long_delay_not_acknowledged, technical_jargon, no_timeline

4. INTENT SUMMARY: <1-2 sentence description of communication intent>

5. QUALITY TIER: <excellent, good, acceptable, or poor>

Respond ONLY with valid JSON. No markdown formatting, no explanations.
"""

        try:
            # Call Ollama LLM
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for consistent classifications
                        "num_predict": 1000,  # Increased from 500 to prevent JSON truncation
                        "format": "json"  # Force JSON output
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            llm_output = response.json()['response']

            # Parse JSON response
            # Remove markdown code blocks if present
            llm_output = re.sub(r'```json\s*', '', llm_output)
            llm_output = re.sub(r'```\s*$', '', llm_output)

            # Try to extract JSON if embedded in text
            json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
            if json_match:
                llm_output = json_match.group(0)

            # Parse JSON with repair logic for truncation
            try:
                analysis = json.loads(llm_output)
            except json.JSONDecodeError:
                # Repair truncated JSON by adding missing closing braces
                fixed = llm_output.rstrip()
                open_braces = fixed.count('{') - fixed.count('}')
                if open_braces > 0:
                    fixed += '\n' + ('}' * open_braces)
                analysis = json.loads(fixed)  # Retry with repaired JSON

            # Extract scores from nested or flat structure
            # LLM may return {"qualityScores": {...}} or flat {"professionalism": ...}
            if 'qualityScores' in analysis:
                quality_scores = analysis['qualityScores']
            else:
                quality_scores = analysis

            # Extract individual scores with fallback
            scores = [
                quality_scores.get('professionalism', 3),
                quality_scores.get('clarity', 3),
                quality_scores.get('empathy', 3),
                quality_scores.get('actionability', 3)
            ]
            quality_score = round(sum(scores) / len(scores), 2)

            # Flatten scores to top level (database expects flat structure)
            analysis['professionalism_score'] = scores[0]
            analysis['clarity_score'] = scores[1]
            analysis['empathy_score'] = scores[2]
            analysis['actionability_score'] = scores[3]
            analysis['quality_score'] = quality_score

            # Normalize key names (camelCase → snake_case)
            if 'contentTags' in analysis:
                analysis['content_tags'] = analysis.pop('contentTags')
            if 'redFlags' in analysis:
                analysis['red_flags'] = analysis.pop('redFlags')
            if 'intentSummary' in analysis:
                analysis['intent_summary'] = analysis.pop('intentSummary')
            if 'qualityTier' in analysis:
                analysis['quality_tier'] = analysis.pop('qualityTier')

            # Calculate quality_tier if not provided by LLM
            if 'quality_tier' not in analysis:
                if quality_score >= 4.0:
                    analysis['quality_tier'] = 'excellent'
                elif quality_score >= 3.0:
                    analysis['quality_tier'] = 'good'
                elif quality_score >= 2.0:
                    analysis['quality_tier'] = 'acceptable'
                else:
                    analysis['quality_tier'] = 'poor'

            return analysis

        except Exception as e:
            print(f"   ⚠️  LLM analysis failed for comment {comment['ticket_id']}: {e}")
            # Return default neutral scores on failure
            return {
                'professionalism_score': 3,
                'clarity_score': 3,
                'empathy_score': 3,
                'actionability_score': 3,
                'quality_score': 3.0,
                'quality_tier': 'acceptable',
                'content_tags': ['analysis_failed'],
                'red_flags': [],
                'intent_summary': 'Analysis failed - manual review needed'
            }

    def analyze_batch(self, comments: List[Dict], batch_size: int = 10):
        """
        Analyze batch of comments and store results

        Processes in small batches to avoid overwhelming Ollama
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for concurrent access

        total = len(comments)
        processed = 0

        print(f"\n📊 Analyzing {total} comments in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = comments[i:i+batch_size]

            for comment in batch:
                # Check if already analyzed
                existing = conn.execute(
                    "SELECT 1 FROM comment_quality WHERE ticket_id = ? AND created_time = ?",
                    (comment['ticket_id'], comment['created_time'])
                ).fetchone()

                if existing:
                    processed += 1
                    continue

                # Analyze comment
                analysis = self.analyze_comment_quality(comment)
                cleaned_text = self.clean_html_comment(comment['comment_text'])

                # Store results
                conn.execute("""
                    INSERT OR REPLACE INTO comment_quality (
                        comment_id, ticket_id, user_name, team, comment_type, created_time,
                        cleaned_text, professionalism_score, clarity_score, empathy_score,
                        actionability_score, quality_score, quality_tier, content_tags,
                        red_flags, intent_summary, analysis_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"{comment['ticket_id']}_{comment['created_time']}",  # comment_id
                    comment['ticket_id'],
                    comment['user_name'],
                    comment['team'],
                    comment['comment_type'],
                    comment['created_time'],
                    cleaned_text,
                    analysis.get('professionalism_score', 3),  # Use _score suffix (flattened keys)
                    analysis.get('clarity_score', 3),
                    analysis.get('empathy_score', 3),
                    analysis.get('actionability_score', 3),
                    analysis['quality_score'],
                    analysis['quality_tier'],
                    json.dumps(analysis.get('content_tags', [])),
                    json.dumps(analysis.get('red_flags', [])),
                    analysis.get('intent_summary', ''),
                    datetime.now().isoformat()
                ))

                processed += 1

                if processed % 10 == 0:
                    conn.commit()
                    print(f"   Progress: {processed}/{total} ({processed/total*100:.1f}%)")

        conn.commit()
        conn.close()

        print(f"\n✅ Analysis complete: {processed}/{total} comments processed")

    def get_ollama_embedding(self, text: str) -> List[float]:
        """Get embedding vector from Ollama"""
        response = requests.post(
            f"{self.ollama_url}/api/embeddings",
            json={
                "model": self.embedding_model,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['embedding']

    def index_all_comments_to_rag(self, batch_size: int = 100):
        """
        Index ALL comments to ChromaDB with embeddings for semantic search

        This enables:
        - Semantic similarity search (find similar communication patterns)
        - Quality trend analysis by topic
        - Pattern detection across agents
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)

        # Get total comment count
        total = conn.execute("SELECT COUNT(*) FROM comments WHERE comment_type = 'comments'").fetchone()[0]

        # Check how many already indexed
        existing_count = self.collection.count()

        print(f"\n📚 RAG INDEXING: {total:,} total comments")
        print(f"   Already indexed: {existing_count:,}")
        print(f"   Remaining: {total - existing_count:,}")

        if existing_count >= total:
            print("   ✅ All comments already indexed!")
            return

        # Fetch comments in batches
        offset = existing_count
        processed = existing_count

        while offset < total:
            # Fetch batch
            cursor = conn.execute(f"""
                SELECT
                    ticket_id,
                    user_name,
                    team,
                    comment_type,
                    comment_text,
                    created_time,
                    visible_to_customer,
                    ROWID
                FROM comments
                WHERE comment_type = 'comments'
                LIMIT {batch_size} OFFSET {offset}
            """)

            batch = cursor.fetchall()
            if not batch:
                break

            # Prepare batch for ChromaDB
            ids = []
            documents = []
            metadatas = []

            for row in batch:
                ticket_id, user_name, team, comment_type, comment_text, created_time, visible_to_customer, rowid = row

                # Clean comment text
                cleaned = self.clean_html_comment(comment_text)
                if len(cleaned) < 10:
                    continue  # Skip empty comments

                # Create unique ID
                comment_id = f"{ticket_id}_{created_time}_{rowid}"

                # Document for embedding
                documents.append(cleaned)
                ids.append(comment_id)

                # Metadata for filtering
                metadatas.append({
                    'ticket_id': str(ticket_id),
                    'user_name': str(user_name) if user_name else 'unknown',
                    'team': str(team) if team else 'unknown',
                    'created_time': str(created_time),
                    'visible_to_customer': str(visible_to_customer),
                    'text_length': len(cleaned)
                })

            if ids:
                # Get embeddings from Ollama and add to ChromaDB
                try:
                    # ChromaDB will call Ollama for embeddings automatically if we use default embedding function
                    # But we need to use our custom Ollama endpoint
                    embeddings = []
                    for doc in documents:
                        try:
                            emb = self.get_ollama_embedding(doc)
                            embeddings.append(emb)
                        except Exception as e:
                            print(f"   ⚠️  Embedding failed: {e}")
                            embeddings.append([0.0] * 768)  # Fallback zero vector

                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )

                    processed += len(ids)
                    print(f"   Progress: {processed:,}/{total:,} ({processed/total*100:.1f}%) - Batch: {len(ids)} comments")

                except Exception as e:
                    print(f"   ⚠️  Batch indexing failed: {e}")

            offset += batch_size

        conn.close()
        print(f"\n✅ RAG indexing complete: {processed:,} comments indexed")
        print(f"   ChromaDB: {self.rag_db_path}")
        print(f"   Collection: servicedesk_comments")

    def generate_summary_report(self) -> str:
        """Generate executive summary of quality analysis results"""
        conn = sqlite3.connect(self.db_path)

        report = []
        report.append("="*80)
        report.append("SERVICEDESK COMMENT QUALITY ANALYSIS - EXECUTIVE SUMMARY")
        report.append("="*80)
        report.append("")

        # Overall quality distribution
        tier_dist = conn.execute("""
            SELECT
                quality_tier,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM comment_quality), 1) as pct
            FROM comment_quality
            GROUP BY quality_tier
            ORDER BY
                CASE quality_tier
                    WHEN 'excellent' THEN 1
                    WHEN 'good' THEN 2
                    WHEN 'acceptable' THEN 3
                    WHEN 'poor' THEN 4
                END
        """).fetchall()

        report.append("📊 OVERALL QUALITY DISTRIBUTION:")
        for tier, count, pct in tier_dist:
            report.append(f"   {tier.upper():15s} {count:5d} comments ({pct:5.1f}%)")
        report.append("")

        # Average scores by agent
        agent_scores = conn.execute("""
            SELECT
                user_name,
                COUNT(*) as comments_analyzed,
                ROUND(AVG(quality_score), 2) as avg_quality,
                ROUND(AVG(professionalism_score), 2) as avg_professionalism,
                ROUND(AVG(clarity_score), 2) as avg_clarity,
                ROUND(AVG(empathy_score), 2) as avg_empathy,
                ROUND(AVG(actionability_score), 2) as avg_actionability
            FROM comment_quality
            GROUP BY user_name
            HAVING comments_analyzed >= 10
            ORDER BY avg_quality DESC
            LIMIT 10
        """).fetchall()

        report.append("🏆 TOP 10 AGENTS BY QUALITY SCORE:")
        report.append(f"   {'Agent':<15s} {'Comments':<10s} {'Quality':<10s} {'Prof':<8s} {'Clarity':<8s} {'Empathy':<8s} {'Action':<8s}")
        report.append("   " + "-"*75)
        for row in agent_scores:
            report.append(f"   {row[0]:<15s} {row[1]:<10d} {row[2]:<10.2f} {row[3]:<8.2f} {row[4]:<8.2f} {row[5]:<8.2f} {row[6]:<8.2f}")
        report.append("")

        # Red flag frequency
        all_red_flags = conn.execute("""
            SELECT red_flags FROM comment_quality WHERE red_flags != '[]'
        """).fetchall()

        red_flag_counts = {}
        for (flags_json,) in all_red_flags:
            flags = json.loads(flags_json)
            for flag in flags:
                red_flag_counts[flag] = red_flag_counts.get(flag, 0) + 1

        report.append("🚩 RED FLAG FREQUENCY:")
        for flag, count in sorted(red_flag_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(all_red_flags) * 100 if all_red_flags else 0
            report.append(f"   {flag:<30s} {count:5d} occurrences ({pct:5.1f}%)")
        report.append("")

        # Poor quality agents (intervention needed)
        poor_agents = conn.execute("""
            SELECT
                user_name,
                COUNT(*) as comments,
                ROUND(100.0 * SUM(CASE WHEN quality_tier = 'poor' THEN 1 ELSE 0 END) / COUNT(*), 1) as poor_pct,
                ROUND(AVG(quality_score), 2) as avg_quality
            FROM comment_quality
            GROUP BY user_name
            HAVING comments >= 10 AND poor_pct > 30
            ORDER BY poor_pct DESC
            LIMIT 10
        """).fetchall()

        if poor_agents:
            report.append("⚠️  AGENTS REQUIRING INTERVENTION (>30% poor quality):")
            for agent, comments, poor_pct, avg_quality in poor_agents:
                report.append(f"   {agent:<15s} {comments:5d} comments, {poor_pct:5.1f}% poor quality, avg score: {avg_quality:.2f}")
            report.append("")

        report.append("="*80)
        report.append("Analysis complete. Detailed results in comment_quality table.")
        report.append("="*80)

        conn.close()

        return "\n".join(report)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="ServiceDesk Comment Quality Analyzer")
    parser.add_argument("--extract", action="store_true", help="Extract sample for analysis")
    parser.add_argument("--analyze", action="store_true", help="Run LLM analysis on extracted sample")
    parser.add_argument("--report", action="store_true", help="Generate summary report")
    parser.add_argument("--rag", action="store_true", help="Index ALL comments to ChromaDB for semantic search")
    parser.add_argument("--full", action="store_true", help="Run full pipeline (extract + analyze + report)")
    parser.add_argument("--sample-size", type=int, default=3300, help="Sample size for analysis")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for LLM processing")
    parser.add_argument("--rag-batch-size", type=int, default=100, help="Batch size for RAG indexing")

    args = parser.parse_args()

    analyzer = ServiceDeskCommentAnalyzer()

    if args.full or args.extract:
        print("\n📥 PHASE 1: Extracting sample comments...")
        sample = analyzer.extract_sample_for_analysis(sample_size=args.sample_size)

        # Save sample to work_projects (work output, not Maia system file)
        sample_file = Path.home() / "work_projects/servicedesk_analysis/servicedesk_comment_sample.json"
        with open(sample_file, 'w') as f:
            json.dump(sample, f, indent=2, default=str)
        print(f"   ✅ Sample saved to: {sample_file}")

    if args.full or args.analyze:
        print("\n🤖 PHASE 2: Analyzing comment quality with Ollama LLM...")

        # Load sample from work_projects
        sample_file = Path.home() / "work_projects/servicedesk_analysis/servicedesk_comment_sample.json"
        if sample_file.exists():
            with open(sample_file, 'r') as f:
                sample = json.load(f)

            analyzer.analyze_batch(sample, batch_size=args.batch_size)
        else:
            print("   ❌ No sample found. Run with --extract first.")
            return

    if args.rag:
        print("\n📚 RAG INDEXING: Indexing ALL comments to ChromaDB...")
        analyzer.index_all_comments_to_rag(batch_size=args.rag_batch_size)

    if args.full or args.report:
        print("\n📊 PHASE 3: Generating summary report...")
        report = analyzer.generate_summary_report()
        print(report)

        # Save report
        report_file = MAIA_ROOT / "claude/data/SERVICEDESK_QUALITY_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n   ✅ Report saved to: {report_file}")


if __name__ == "__main__":
    main()
