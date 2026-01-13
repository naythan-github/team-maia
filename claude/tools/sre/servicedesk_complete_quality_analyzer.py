#!/usr/bin/env python3
"""
ServiceDesk Complete Quality Analyzer with RAG-Enhanced Deduplication

Analyzes ALL 108K comments with intelligent duplicate detection:
- Uses RAG similarity search to identify duplicate/near-duplicate comments
- Analyzes only unique comments (80-90K estimated after deduplication)
- Propagates quality scores to duplicates
- Achieves 100% coverage with 10-30% token savings
- Resumable: Can restart from any point without losing progress

Architecture:
1. RAG duplicate detection (similarity threshold 0.95)
2. LLM quality analysis on unique comments only
3. Score propagation to duplicate clusters
4. Validation across different comment patterns

Created: 2025-10-15
Author: Maia System
"""

import os
import sys
import json
import sqlite3
import requests
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import time

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

# Optional dependency - graceful degradation for importability
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = Settings = None


def _check_chromadb_available():
    """Raise ImportError if chromadb is not installed."""
    if not CHROMADB_AVAILABLE:
        raise ImportError("chromadb required. Install with: pip3 install chromadb")


class ServiceDeskCompleteQualityAnalyzer:
    """Complete quality analysis with RAG-enhanced duplicate detection"""

    def __init__(self, db_path: str = None, llm_model: str = "llama3.2:3b"):
        """Initialize analyzer"""
        self.db_path = db_path or str(DB_PATH)
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434"

        # Initialize ChromaDB (should already be populated by multi_rag_indexer)
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_rag")

        if not os.path.exists(self.rag_db_path):
            print("❌ RAG database not found. Run servicedesk_multi_rag_indexer.py first!")
            sys.exit(1)

        self.chroma_client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            self.collection = self.chroma_client.get_collection("servicedesk_comments")
            print(f"✅ Connected to RAG collection: {self.collection.count():,} comments indexed")
        except Exception as e:
            print(f"❌ Failed to load comments collection: {e}")
            print("   Run: python3 claude/tools/sre/servicedesk_multi_rag_indexer.py --index-all")
            sys.exit(1)

        print(f"✅ ServiceDesk Complete Quality Analyzer initialized")
        print(f"   LLM: {llm_model}")
        print(f"   Database: {self.db_path}")
        print(f"   RAG: {self.rag_db_path}")

    def find_duplicate_clusters(self, similarity_threshold: float = 0.95, batch_size: int = 100):
        """
        Find clusters of duplicate/near-duplicate comments using RAG similarity

        Args:
            similarity_threshold: Cosine similarity threshold (0.95 = 95% similar)
            batch_size: Process in batches for memory efficiency

        Returns:
            Dict[str, List[str]]: {representative_id: [duplicate_ids]}
        """
        print(f"\n{'='*70}")
        print(f"FINDING DUPLICATE CLUSTERS (similarity >= {similarity_threshold})")
        print(f"{'='*70}")

        # Get all comment IDs from RAG
        all_results = self.collection.get(limit=200000)  # Get all
        all_ids = all_results['ids']
        total = len(all_ids)

        print(f"Total comments in RAG: {total:,}")
        print(f"Similarity threshold: {similarity_threshold}")
        print(f"Processing in batches of {batch_size}...\n")

        clusters = {}  # {representative_id: [duplicate_ids]}
        processed = set()

        start_time = time.time()

        for i in range(0, total, batch_size):
            batch_ids = all_ids[i:i+batch_size]

            for comment_id in batch_ids:
                if comment_id in processed:
                    continue

                # Find similar comments
                results = self.collection.query(
                    query_texts=[all_results['documents'][all_ids.index(comment_id)]],
                    n_results=50,  # Check top 50 similar
                    include=['distances']
                )

                # Filter by similarity threshold
                similar_ids = []
                for result_id, distance in zip(results['ids'][0], results['distances'][0]):
                    similarity = 1 - distance
                    if similarity >= similarity_threshold and result_id != comment_id:
                        similar_ids.append(result_id)
                        processed.add(result_id)

                if similar_ids:
                    clusters[comment_id] = similar_ids
                    processed.add(comment_id)

            # Progress update
            progress = min(i + batch_size, total)
            elapsed = time.time() - start_time
            rate = progress / elapsed if elapsed > 0 else 0
            eta = (total - progress) / rate if rate > 0 else 0

            print(f"   Progress: {progress:,}/{total:,} ({100*progress/total:.1f}%) - "
                  f"{len(clusters):,} clusters found - ETA: {eta/60:.1f}m")

        elapsed = time.time() - start_time
        unique_comments = total - sum(len(dupes) for dupes in clusters.values())
        duplicate_comments = sum(len(dupes) for dupes in clusters.values())

        print(f"\n✅ Duplicate detection complete:")
        print(f"   Total comments: {total:,}")
        print(f"   Unique comments: {unique_comments:,} ({100*unique_comments/total:.1f}%)")
        print(f"   Duplicate comments: {duplicate_comments:,} ({100*duplicate_comments/total:.1f}%)")
        print(f"   Duplicate clusters: {len(clusters):,}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Token savings: {100*duplicate_comments/total:.1f}% fewer LLM calls")

        return clusters

    def analyze_comment_quality(self, comment_text: str, comment_id: str, metadata: Dict) -> Optional[Dict]:
        """
        Analyze single comment quality using LLM

        Returns quality analysis dict or None if failed
        """
        # Clean HTML if present
        if '<' in comment_text and '>' in comment_text:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(comment_text, 'html.parser')
            comment_text = soup.get_text(separator=' ', strip=True)

        # Truncate if too long
        if len(comment_text) > 2000:
            comment_text = comment_text[:2000] + "... [truncated]"

        prompt = f"""Analyze this ServiceDesk comment for communication quality. Respond ONLY with valid JSON.

Comment: "{comment_text}"

Provide scores (1-5) for:
- professionalism: Professional tone, courtesy, grammar
- clarity: Clear communication, concise, well-structured
- empathy: Customer acknowledgment, appropriate tone
- actionability: Clear next steps, timeline, resolution info

Also identify:
- content_tags: Array of tags (canned_response, meaningful_update, handoff_notice, resolution_statement, empty_content)
- red_flags: Array of issues (no_context_handoff, defensive_tone, closes_without_confirmation, long_delay_not_acknowledged, technical_jargon, no_timeline)
- intent_summary: 1-2 sentence description of comment purpose

Response format:
{{
  "professionalism_score": <1-5>,
  "clarity_score": <1-5>,
  "empathy_score": <1-5>,
  "actionability_score": <1-5>,
  "content_tags": ["tag1", "tag2"],
  "red_flags": ["flag1", "flag2"],
  "intent_summary": "Brief description"
}}"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )

            if response.status_code != 200:
                return None

            result = response.json()
            analysis_text = result.get('response', '')

            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                analysis = json.loads(analysis_text)

            # Calculate overall quality score
            quality_score = (
                analysis['professionalism_score'] +
                analysis['clarity_score'] +
                analysis['empathy_score'] +
                analysis['actionability_score']
            ) / 4.0

            # Determine quality tier
            if quality_score >= 4.0:
                quality_tier = 'excellent'
            elif quality_score >= 3.0:
                quality_tier = 'good'
            elif quality_score >= 2.0:
                quality_tier = 'acceptable'
            else:
                quality_tier = 'poor'

            analysis['quality_score'] = quality_score
            analysis['quality_tier'] = quality_tier

            return analysis

        except Exception as e:
            print(f"   ⚠️  LLM analysis failed for {comment_id}: {e}")
            return None

    def save_quality_result(self, comment_id: str, ticket_id: str, user_name: str,
                           team: str, comment_type: str, created_time: str,
                           cleaned_text: str, analysis: Dict):
        """Save quality analysis to database"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")

        conn.execute("""
            INSERT OR REPLACE INTO comment_quality (
                comment_id, ticket_id, user_name, team, comment_type, created_time,
                cleaned_text, professionalism_score, clarity_score, empathy_score,
                actionability_score, quality_score, quality_tier, content_tags,
                red_flags, intent_summary, analysis_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comment_id, ticket_id, user_name, team, comment_type, created_time,
            cleaned_text,
            analysis['professionalism_score'],
            analysis['clarity_score'],
            analysis['empathy_score'],
            analysis['actionability_score'],
            analysis['quality_score'],
            analysis['quality_tier'],
            json.dumps(analysis.get('content_tags', [])),
            json.dumps(analysis.get('red_flags', [])),
            analysis.get('intent_summary', ''),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def analyze_all_unique_comments(self, clusters: Dict, batch_size: int = 10):
        """
        Analyze all unique comments (cluster representatives + standalone)

        Args:
            clusters: Result from find_duplicate_clusters()
            batch_size: LLM requests per batch
        """
        print(f"\n{'='*70}")
        print(f"ANALYZING UNIQUE COMMENTS")
        print(f"{'='*70}")

        # Get all comment IDs from RAG
        all_results = self.collection.get(limit=200000)
        all_ids = set(all_results['ids'])

        # Identify which comments need analysis
        cluster_representatives = set(clusters.keys())
        all_duplicates = set()
        for dupes in clusters.values():
            all_duplicates.update(dupes)

        standalone_comments = all_ids - cluster_representatives - all_duplicates

        unique_comments = cluster_representatives | standalone_comments
        total_unique = len(unique_comments)

        print(f"Total comments: {len(all_ids):,}")
        print(f"Cluster representatives: {len(cluster_representatives):,}")
        print(f"Standalone comments: {len(standalone_comments):,}")
        print(f"Unique comments to analyze: {total_unique:,}")
        print(f"Duplicate comments (will propagate): {len(all_duplicates):,}")
        print(f"Token savings: {100*len(all_duplicates)/len(all_ids):.1f}%\n")

        # Check which comments already have quality scores
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT comment_id FROM comment_quality")
        already_analyzed = set(row[0] for row in cursor.fetchall())
        conn.close()

        remaining = unique_comments - already_analyzed
        print(f"Already analyzed: {len(already_analyzed):,}")
        print(f"Remaining to analyze: {len(remaining):,}\n")

        if not remaining:
            print("✅ All unique comments already analyzed!")
            return

        # Analyze remaining comments
        start_time = time.time()
        analyzed_count = 0
        failed_count = 0

        for i, comment_id in enumerate(remaining):
            # Get comment data from RAG
            result = self.collection.get(ids=[comment_id], include=['documents', 'metadatas'])

            if not result['documents']:
                continue

            text = result['documents'][0]
            metadata = result['metadatas'][0]

            # Analyze quality
            analysis = self.analyze_comment_quality(text, comment_id, metadata)

            if analysis:
                self.save_quality_result(
                    comment_id=comment_id,
                    ticket_id=metadata.get('ticket_id', ''),
                    user_name=metadata.get('user_name', ''),
                    team=metadata.get('team', ''),
                    comment_type=metadata.get('comment_type', ''),
                    created_time=metadata.get('created_time', ''),
                    cleaned_text=text[:2000],
                    analysis=analysis
                )
                analyzed_count += 1
            else:
                failed_count += 1

            # Progress update
            if (i + 1) % batch_size == 0 or i == len(remaining) - 1:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(remaining) - (i + 1)) / rate if rate > 0 else 0

                print(f"   Progress: {i+1:,}/{len(remaining):,} ({100*(i+1)/len(remaining):.1f}%) - "
                      f"Success: {analyzed_count:,} | Failed: {failed_count:,} - "
                      f"Rate: {rate:.1f}/s - ETA: {eta/60:.1f}m")

        elapsed = time.time() - start_time
        print(f"\n✅ Unique comment analysis complete:")
        print(f"   Analyzed: {analyzed_count:,}")
        print(f"   Failed: {failed_count:,}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Rate: {analyzed_count/elapsed:.2f} comments/sec")

    def propagate_scores_to_duplicates(self, clusters: Dict):
        """Propagate quality scores from representatives to duplicates"""
        print(f"\n{'='*70}")
        print(f"PROPAGATING SCORES TO DUPLICATES")
        print(f"{'='*70}")

        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        total_propagated = 0

        for representative_id, duplicate_ids in clusters.items():
            # Get representative's quality score
            cursor.execute(
                "SELECT * FROM comment_quality WHERE comment_id = ?",
                (representative_id,)
            )
            rep_result = cursor.fetchone()

            if not rep_result:
                continue

            # Get column names
            columns = [desc[0] for desc in cursor.description]
            rep_data = dict(zip(columns, rep_result))

            # Propagate to duplicates
            for dup_id in duplicate_ids:
                # Get duplicate's metadata from RAG
                dup_result = self.collection.get(ids=[dup_id], include=['metadatas'])
                if not dup_result['metadatas']:
                    continue

                dup_metadata = dup_result['metadatas'][0]

                cursor.execute("""
                    INSERT OR REPLACE INTO comment_quality (
                        comment_id, ticket_id, user_name, team, comment_type, created_time,
                        cleaned_text, professionalism_score, clarity_score, empathy_score,
                        actionability_score, quality_score, quality_tier, content_tags,
                        red_flags, intent_summary, analysis_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dup_id,
                    dup_metadata.get('ticket_id', ''),
                    dup_metadata.get('user_name', ''),
                    dup_metadata.get('team', ''),
                    dup_metadata.get('comment_type', ''),
                    dup_metadata.get('created_time', ''),
                    rep_data['cleaned_text'],
                    rep_data['professionalism_score'],
                    rep_data['clarity_score'],
                    rep_data['empathy_score'],
                    rep_data['actionability_score'],
                    rep_data['quality_score'],
                    rep_data['quality_tier'],
                    rep_data['content_tags'],
                    rep_data['red_flags'],
                    f"[Propagated from {representative_id}] {rep_data['intent_summary']}",
                    datetime.now().isoformat()
                ))

                total_propagated += 1

            conn.commit()

            if len(clusters) > 100 and (list(clusters.keys()).index(representative_id) + 1) % 100 == 0:
                print(f"   Progress: {list(clusters.keys()).index(representative_id)+1:,}/{len(clusters):,} clusters - "
                      f"{total_propagated:,} scores propagated")

        conn.close()

        print(f"\n✅ Score propagation complete:")
        print(f"   Clusters processed: {len(clusters):,}")
        print(f"   Scores propagated: {total_propagated:,}")


def main():
    parser = argparse.ArgumentParser(description="ServiceDesk Complete Quality Analyzer with RAG Deduplication")
    parser.add_argument('--find-duplicates', action='store_true', help="Find duplicate comment clusters")
    parser.add_argument('--analyze', action='store_true', help="Analyze unique comments")
    parser.add_argument('--propagate', action='store_true', help="Propagate scores to duplicates")
    parser.add_argument('--full', action='store_true', help="Run complete pipeline (find + analyze + propagate)")
    parser.add_argument('--similarity', type=float, default=0.95, help="Similarity threshold for duplicates (default: 0.95)")
    parser.add_argument('--batch-size', type=int, default=10, help="LLM batch size (default: 10)")
    parser.add_argument('--clusters-file', type=str, default='servicedesk_duplicate_clusters.json',
                       help="Save/load clusters to/from file")

    args = parser.parse_args()

    analyzer = ServiceDeskCompleteQualityAnalyzer()

    clusters_path = Path.home() / args.clusters_file

    if args.find_duplicates or args.full:
        clusters = analyzer.find_duplicate_clusters(similarity_threshold=args.similarity)

        # Save clusters to file for resume capability
        with open(clusters_path, 'w') as f:
            json.dump(clusters, f, indent=2)
        print(f"\n💾 Clusters saved to: {clusters_path}")

    if args.analyze or args.full:
        # Load clusters if not just found
        if not (args.find_duplicates or args.full):
            if clusters_path.exists():
                with open(clusters_path, 'r') as f:
                    clusters = json.load(f)
                print(f"📂 Loaded clusters from: {clusters_path}")
            else:
                print(f"❌ Clusters file not found: {clusters_path}")
                print("   Run with --find-duplicates first")
                return

        analyzer.analyze_all_unique_comments(clusters, batch_size=args.batch_size)

    if args.propagate or args.full:
        # Load clusters if not already in memory
        if not (args.find_duplicates or args.analyze or args.full):
            if clusters_path.exists():
                with open(clusters_path, 'r') as f:
                    clusters = json.load(f)
                print(f"📂 Loaded clusters from: {clusters_path}")
            else:
                print(f"❌ Clusters file not found: {clusters_path}")
                print("   Run with --find-duplicates first")
                return

        analyzer.propagate_scores_to_duplicates(clusters)


if __name__ == '__main__':
    main()
