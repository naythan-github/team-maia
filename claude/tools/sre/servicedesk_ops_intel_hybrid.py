#!/usr/bin/env python3
"""
ServiceDesk Operations Intelligence - Hybrid Architecture (SQLite + ChromaDB)

Extends base operations intelligence with semantic search capabilities.

Phase: 130.1 - Semantic Enhancement
Created: 2025-10-18
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from servicedesk_operations_intelligence import (
    ServiceDeskOpsIntelligence,
    OperationalInsight,
    Learning,
    DB_PATH
)

MAIA_ROOT = Path(__file__).parent.parent.parent
CHROMA_PATH = Path.home() / '.maia' / 'ops_intelligence_embeddings'


class ServiceDeskOpsIntelHybrid(ServiceDeskOpsIntelligence):
    """
    Hybrid operational intelligence with semantic search.

    Combines SQLite (structured data) + ChromaDB (semantic search)
    for optimal pattern recognition and learning retrieval.
    """

    def __init__(self, db_path: Path = DB_PATH, chroma_path: Path = CHROMA_PATH):
        """Initialize hybrid system with SQLite + ChromaDB"""
        super().__init__(db_path)

        # Initialize ChromaDB
        self.chroma_path = chroma_path
        self.chroma_path.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collections
        self.insights_collection = self.chroma_client.get_or_create_collection(
            name="ops_intelligence_insights",
            metadata={"description": "Operational insights with semantic search"}
        )

        self.learning_collection = self.chroma_client.get_or_create_collection(
            name="ops_intelligence_learnings",
            metadata={"description": "Learning entries with semantic search"}
        )

    def add_insight(self, insight: OperationalInsight) -> int:
        """Add insight to SQLite and auto-embed in ChromaDB"""
        # Add to SQLite (parent class)
        insight_id = super().add_insight(insight)

        # Auto-embed in ChromaDB
        self._embed_insight(insight_id)

        return insight_id

    def _embed_insight(self, insight_id: int) -> str:
        """Embed insight in ChromaDB for semantic search"""
        import sqlite3

        # Get insight from SQLite
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM operational_insights WHERE insight_id = ?', (insight_id,))
        insight = dict(cursor.fetchone())
        conn.close()

        # Create embedding text (description + root_cause for richer semantics)
        embedding_text = f"{insight['title']}. {insight['description']} Root cause: {insight['root_cause']}"

        # Prepare metadata (searchable fields)
        metadata = {
            'insight_id': str(insight_id),
            'insight_type': insight['insight_type'],
            'severity': insight['severity'] or '',
            'status': insight['status'],
            'identified_date': insight['identified_date'],
            'business_impact': insight['business_impact'] or ''
        }

        # Add to ChromaDB
        embedding_id = f"insight_{insight_id}"
        self.insights_collection.add(
            documents=[embedding_text],
            metadatas=[metadata],
            ids=[embedding_id]
        )

        # Update SQLite with embedding tracking
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE operational_insights
            SET embedding_id = ?, embedded_at = ?
            WHERE insight_id = ?
        ''', (embedding_id, datetime.now().isoformat(), insight_id))
        conn.commit()
        conn.close()

        print(f"   🔗 Embedded in ChromaDB: {embedding_id}")
        return embedding_id

    def find_similar_insights(
        self,
        query: str,
        top_k: int = 5,
        status_filter: str = None
    ) -> List[Dict]:
        """
        Semantic search for similar insights.

        Args:
            query: Natural language query
            top_k: Number of results to return
            status_filter: Optional status filter (active, resolved, etc.)

        Returns:
            List of insights with similarity scores
        """
        # Query ChromaDB
        where_filter = {}
        if status_filter:
            where_filter['status'] = status_filter

        results = self.insights_collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        # Enrich with full SQLite data
        enriched_results = []
        if results['ids'] and results['ids'][0]:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            for idx, embedding_id in enumerate(results['ids'][0]):
                insight_id = int(embedding_id.split('_')[1])
                cursor.execute('SELECT * FROM operational_insights WHERE insight_id = ?', (insight_id,))
                insight = dict(cursor.fetchone())
                insight['similarity_score'] = 1 - results['distances'][0][idx]  # Convert distance to similarity
                enriched_results.append(insight)

            conn.close()

        return enriched_results

    def check_similar_patterns(self, new_insight: OperationalInsight, similarity_threshold: float = 0.85) -> Optional[Dict]:
        """
        Check if new insight matches existing patterns.

        Auto-suggests past recommendations if similar case found.

        Args:
            new_insight: Newly identified insight
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            Dict with similar insight + past recommendations if found
        """
        query = f"{new_insight.title}. {new_insight.description}"
        similar = self.find_similar_insights(query, top_k=3)

        if not similar:
            return None

        # Check if similarity exceeds threshold
        if similar[0]['similarity_score'] >= similarity_threshold:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get past recommendations for similar insight
            cursor.execute('''
                SELECT * FROM recommendations
                WHERE insight_id = ?
                ORDER BY created_at DESC
            ''', (similar[0]['insight_id'],))
            past_recs = [dict(row) for row in cursor.fetchall()]

            # Get outcomes for those recommendations
            outcomes = []
            for rec in past_recs:
                cursor.execute('''
                    SELECT * FROM outcomes
                    WHERE recommendation_id = ?
                ''', (rec['recommendation_id'],))
                outcome_rows = cursor.fetchall()
                if outcome_rows:
                    outcomes.append(dict(outcome_rows[0]))

            conn.close()

            return {
                'similar_insight': similar[0],
                'similarity_score': similar[0]['similarity_score'],
                'past_recommendations': past_recs,
                'outcomes': outcomes
            }

        return None

    def add_learning(self, learning: Learning) -> int:
        """Add learning to SQLite and auto-embed in ChromaDB"""
        # Add to SQLite (parent class)
        learning_id = super().add_learning(learning)

        # Auto-embed in ChromaDB
        self._embed_learning(learning_id)

        return learning_id

    def _embed_learning(self, learning_id: int) -> str:
        """Embed learning in ChromaDB for semantic search"""
        import sqlite3

        # Get learning from SQLite
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM learning_log WHERE learning_id = ?', (learning_id,))
        learning = dict(cursor.fetchone())
        conn.close()

        # Create embedding text (what worked + why)
        embedding_text = f"What worked: {learning['what_worked']}. Why: {learning['why_analysis']}. Similar situations: {learning['similar_situations']}"

        # Prepare metadata
        metadata = {
            'learning_id': str(learning_id),
            'learning_type': learning['learning_type'],
            'confidence_before': str(learning['confidence_before'] or 0),
            'confidence_after': str(learning['confidence_after'] or 0),
            'would_recommend_again': str(learning['would_recommend_again'])
        }

        # Add to ChromaDB
        embedding_id = f"learning_{learning_id}"
        self.learning_collection.add(
            documents=[embedding_text],
            metadatas=[metadata],
            ids=[embedding_id]
        )

        # Update SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE learning_log
            SET embedding_id = ?, embedded_at = ?
            WHERE learning_id = ?
        ''', (embedding_id, datetime.now().isoformat(), learning_id))
        conn.commit()
        conn.close()

        print(f"   🔗 Learning embedded: {embedding_id}")
        return embedding_id

    def find_similar_learnings(
        self,
        query: str,
        top_k: int = 5,
        learning_type_filter: str = None
    ) -> List[Dict]:
        """
        Semantic search for similar learnings.

        Args:
            query: Natural language query (e.g., "training effectiveness")
            top_k: Number of results
            learning_type_filter: Optional filter (success, failure, etc.)

        Returns:
            List of learnings with similarity scores
        """
        where_filter = {}
        if learning_type_filter:
            where_filter['learning_type'] = learning_type_filter

        results = self.learning_collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        # Enrich with SQLite data
        enriched_results = []
        if results['ids'] and results['ids'][0]:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            for idx, embedding_id in enumerate(results['ids'][0]):
                learning_id = int(embedding_id.split('_')[1])
                cursor.execute('SELECT * FROM learning_log WHERE learning_id = ?', (learning_id,))
                learning = dict(cursor.fetchone())
                learning['similarity_score'] = 1 - results['distances'][0][idx]
                enriched_results.append(learning)

            conn.close()

        return enriched_results

    def embed_all_existing(self):
        """Migrate existing insights and learnings to ChromaDB"""
        import sqlite3

        print("🔄 Embedding existing operational intelligence in ChromaDB...")
        print()

        # Embed all insights
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT insight_id FROM operational_insights WHERE embedding_id IS NULL')
        insight_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        print(f"📊 Insights to embed: {len(insight_ids)}")
        for insight_id in insight_ids:
            self._embed_insight(insight_id)

        # Embed all learnings
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT learning_id FROM learning_log WHERE embedding_id IS NULL')
        learning_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        print()
        print(f"🎓 Learnings to embed: {len(learning_ids)}")
        for learning_id in learning_ids:
            self._embed_learning(learning_id)

        print()
        print(f"✅ Embedded {len(insight_ids)} insights + {len(learning_ids)} learnings")


def main():
    """CLI interface for hybrid intelligence"""
    parser = argparse.ArgumentParser(description='ServiceDesk Ops Intelligence - Hybrid (SQLite + ChromaDB)')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Embed existing data
    parser_embed = subparsers.add_parser('embed-all', help='Embed all existing insights/learnings in ChromaDB')

    # Semantic search
    parser_search = subparsers.add_parser('search-similar', help='Semantic search for similar insights')
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--top-k', type=int, default=5, help='Number of results')
    parser_search.add_argument('--status', help='Filter by status')

    # Find similar learnings
    parser_learning = subparsers.add_parser('search-learnings', help='Semantic search for similar learnings')
    parser_learning.add_argument('query', help='Search query')
    parser_learning.add_argument('--top-k', type=int, default=5, help='Number of results')

    # Check pattern
    parser_pattern = subparsers.add_parser('check-pattern', help='Check if query matches existing patterns')
    parser_pattern.add_argument('query', help='Description of new issue')

    args = parser.parse_args()

    ops_intel = ServiceDeskOpsIntelHybrid()

    if args.command == 'embed-all':
        ops_intel.embed_all_existing()

    elif args.command == 'search-similar':
        results = ops_intel.find_similar_insights(args.query, top_k=args.top_k, status_filter=args.status)
        print(f"\n🔍 Semantic search results for '{args.query}':\n")
        for result in results:
            print(f"  📌 [{result['insight_type']}] {result['title']}")
            print(f"     Similarity: {result['similarity_score']:.2%} | Status: {result['status']} | Date: {result['identified_date']}")
            print(f"     Root Cause: {result['root_cause'][:100]}...")
            print()

    elif args.command == 'search-learnings':
        results = ops_intel.find_similar_learnings(args.query, top_k=args.top_k)
        print(f"\n🎓 Similar learnings for '{args.query}':\n")
        for result in results:
            print(f"  💡 {result['learning_type'].upper()}")
            print(f"     Similarity: {result['similarity_score']:.2%}")
            print(f"     What Worked: {result['what_worked'][:100]}...")
            print(f"     Confidence: {result['confidence_before']}% → {result['confidence_after']}%")
            print()

    elif args.command == 'check-pattern':
        # Create temporary insight for pattern checking
        temp_insight = OperationalInsight(
            insight_type='temp',
            title=args.query,
            description=args.query,
            identified_date=datetime.now().isoformat()
        )

        pattern_match = ops_intel.check_similar_patterns(temp_insight)

        if pattern_match:
            print(f"\n⚠️  SIMILAR PATTERN DETECTED (Similarity: {pattern_match['similarity_score']:.2%})\n")
            print(f"📌 Past Case: {pattern_match['similar_insight']['title']}")
            print(f"   Date: {pattern_match['similar_insight']['identified_date']}")
            print(f"   Status: {pattern_match['similar_insight']['status']}")
            print()

            if pattern_match['past_recommendations']:
                print("💡 Past Recommendations:")
                for rec in pattern_match['past_recommendations']:
                    print(f"   - {rec['title']} (Priority: {rec['priority']}, Status: {rec['status']})")
            print()

            if pattern_match['outcomes']:
                print("📈 Past Outcomes:")
                for outcome in pattern_match['outcomes']:
                    print(f"   - {outcome['metric_type']}: {outcome['baseline_value']} → {outcome['current_value']} ({outcome['improvement_pct']:.1f}% improvement)")
            print()
        else:
            print(f"\n✅ No similar patterns found (this appears to be a new issue)")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
