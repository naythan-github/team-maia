#!/usr/bin/env python3
"""
ServiceDesk GPU-Accelerated RAG Indexer

Uses sentence-transformers with Apple Silicon Metal GPU for 5-10x speedup.
Batch processes embeddings on GPU for maximum throughput.

Performance Comparison:
- Ollama (serial): ~15 docs/sec
- Ollama (parallel): ~20 docs/sec
- GPU batch: ~100-200 docs/sec (5-10x faster!)

Memory Requirements:
- Model: ~500MB-1GB
- Batch processing: ~200MB
- Total: ~2-3GB (safe for 32GB M4)

Created: 2025-10-15
Author: Maia System
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import time
import numpy as np

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError as e:
    print("❌ Missing dependencies.")
    print("   Install: pip3 install sentence-transformers torch chromadb")
    print(f"   Error: {e}")
    sys.exit(1)


class GPURAGIndexer:
    """GPU-accelerated RAG indexer using sentence-transformers"""

    def __init__(self, db_path: str = None, model_name: str = "intfloat/e5-base-v2", batch_size: int = 64):
        """
        Initialize GPU indexer

        Args:
            db_path: Path to SQLite database
            model_name: HuggingFace sentence-transformers model (default: intfloat/e5-base-v2 - best quality)
            batch_size: Documents to process per GPU batch (64-256 recommended)
        """
        self.db_path = db_path or str(DB_PATH)
        self.model_name = model_name
        self.batch_size = batch_size

        # ChromaDB storage
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_rag")
        os.makedirs(self.rag_db_path, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.rag_db_path)

        # Check for Apple Silicon GPU
        self.device = self._get_device()

        print(f"✅ GPU RAG Indexer initialized")
        print(f"   Model: {model_name}")
        print(f"   Device: {self.device}")
        print(f"   Batch size: {batch_size}")
        print(f"   Database: {self.db_path}")
        print(f"   ChromaDB: {self.rag_db_path}")

        # Load model
        print(f"\n📥 Loading embedding model...")
        start = time.time()
        self.model = SentenceTransformer(model_name)

        # Move to GPU if available
        if self.device != 'cpu':
            self.model.to(self.device)
            print(f"   ✅ Model loaded on {self.device} in {time.time()-start:.1f}s")
        else:
            print(f"   ⚠️  GPU not available, using CPU (slower)")

        # Collection definitions (same as serial/parallel versions)
        self.collections = {
            "comments": {
                "description": "ServiceDesk comment communications (108K entries, avg 609 chars)",
                "table": "comments",
                "id_field": "comment_id",
                "text_field": "comment_text",
                "metadata_fields": [
                    "ticket_id", "user_name", "team", "created_time",
                    "visible_to_customer", "comment_type",
                    # Quality metadata (NULL if not analyzed)
                    "professionalism_score", "clarity_score", "empathy_score",
                    "actionability_score", "quality_score", "quality_tier",
                    "content_tags", "red_flags", "intent_summary", "has_quality_analysis"
                ]
            },
            "descriptions": {
                "description": "Ticket problem descriptions (10.9K entries, avg 1,266 chars)",
                "table": "tickets",
                "id_field": "[TKT-Ticket ID]",
                "text_field": "[TKT-Description]",
                "metadata_fields": ["[TKT-Title]", "[TKT-Category]", "[TKT-Severity]", "[TKT-Status]", "[TKT-Team]", "[TKT-Created Time]"]
            },
            "solutions": {
                "description": "Ticket resolution solutions (10.7K entries, avg 51 chars)",
                "table": "tickets",
                "id_field": "[TKT-Ticket ID]",
                "text_field": "[TKT-Solution]",
                "metadata_fields": ["[TKT-Title]", "[TKT-Category]", "[TKT-Status]", "[TKT-Team]", "[TKT-Closure Date]"]
            },
            "titles": {
                "description": "Ticket titles (10.9K entries, 65.7% unique, avg 59 chars)",
                "table": "tickets",
                "id_field": "[TKT-Ticket ID]",
                "text_field": "[TKT-Title]",
                "metadata_fields": ["[TKT-Category]", "[TKT-Severity]", "[TKT-Status]", "[TKT-Team]", "[TKT-Created Time]"]
            },
            "work_logs": {
                "description": "Timesheet work descriptions (73K entries, avg 138 chars)",
                "table": "timesheets",
                "id_field": "rowid",
                "text_field": "[TS-Description]",
                "metadata_fields": ["[TS-User Username]", "[TS-Title]", "[TS-Date]", "[TS-Hours]", "[TS-Crm ID]", "[TS-Category]"]
            }
        }

    def _get_device(self) -> str:
        """Detect best available device (Apple Metal > CUDA > CPU)"""
        if torch.backends.mps.is_available():
            return 'mps'  # Apple Silicon Metal
        elif torch.cuda.is_available():
            return 'cuda'
        else:
            return 'cpu'

    def fetch_documents(self, collection_name: str, limit: int = None) -> List[Dict]:
        """
        Fetch all documents from database for a collection

        Returns:
            List of dicts with 'id', 'text', and metadata fields
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        config = self.collections[collection_name]

        # Build SQL query
        if collection_name == "comments":
            # Special handling for comments - LEFT JOIN with quality analysis
            query = f"""
                SELECT
                    c.comment_id as id,
                    c.comment_text as text,
                    c.ticket_id,
                    c.user_name,
                    c.team,
                    c.created_time,
                    c.visible_to_customer,
                    c.comment_type,
                    -- Quality metadata (NULL if not analyzed)
                    cq.professionalism_score,
                    cq.clarity_score,
                    cq.empathy_score,
                    cq.actionability_score,
                    cq.quality_score,
                    cq.quality_tier,
                    cq.content_tags,
                    cq.red_flags,
                    cq.intent_summary,
                    CASE WHEN cq.quality_score IS NOT NULL THEN 1 ELSE 0 END as has_quality_analysis
                FROM comments c
                LEFT JOIN comment_quality cq ON c.comment_id = cq.comment_id
                WHERE c.comment_text IS NOT NULL AND c.comment_text != ''
                {f"LIMIT {limit}" if limit else ""}
            """
        else:
            # Standard query for other collections
            metadata_select = ", ".join(config['metadata_fields'])
            where_clause = f"WHERE {config['text_field']} IS NOT NULL AND {config['text_field']} != ''"
            limit_clause = f"LIMIT {limit}" if limit else ""

            query = f"""
                SELECT
                    {config['id_field']} as id,
                    {config['text_field']} as text,
                    {metadata_select}
                FROM {config['table']}
                {where_clause}
                {limit_clause}
            """

        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(query)
        rows = cursor.fetchall()

        documents = []
        for row in rows:
            doc = {
                'id': str(row['id']),
                'text': row['text']
            }

            # Add metadata fields
            for field in config['metadata_fields']:
                clean_field = field.replace('[', '').replace(']', '')
                try:
                    value = row[field]
                except (KeyError, IndexError):
                    try:
                        value = row[clean_field]
                    except (KeyError, IndexError):
                        continue

                if value is not None:
                    doc[clean_field] = str(value)

            documents.append(doc)

        conn.close()
        return documents

    def index_collection_gpu(self, collection_name: str, limit: int = None):
        """
        Index a collection using GPU batch embeddings

        Args:
            collection_name: Name of collection to index
            limit: Max documents to index (None = all)
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        config = self.collections[collection_name]

        print(f"\n{'='*70}")
        print(f"GPU BATCH INDEXING: {collection_name}")
        print(f"{'='*70}")
        print(f"Description: {config['description']}")
        print(f"Device: {self.device}")
        print(f"Batch size: {self.batch_size}")

        # Fetch all documents
        print(f"\n📊 Fetching documents from database...")
        start_fetch = time.time()
        documents = self.fetch_documents(collection_name, limit=limit)
        fetch_time = time.time() - start_fetch

        total_docs = len(documents)
        print(f"   Fetched {total_docs:,} documents in {fetch_time:.1f}s")

        if total_docs == 0:
            print("   ⚠️  No documents to index")
            return

        # Initialize ChromaDB
        client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Delete existing collection if it exists (for model changes)
        collection_fullname = f"servicedesk_{collection_name}"
        try:
            client.delete_collection(collection_fullname)
            print(f"   🗑️  Deleted existing collection: {collection_fullname}")
        except:
            pass

        collection = client.create_collection(
            name=collection_fullname,
            metadata={"description": config['description'], "model": self.model_name}
        )

        # Process in batches
        print(f"\n🚀 GPU batch processing...")
        start_index = time.time()
        total_indexed = 0

        for i in range(0, total_docs, self.batch_size):
            batch = documents[i:i+self.batch_size]

            # Prepare batch data
            ids = []
            texts = []
            metadatas = []

            for doc in batch:
                text = doc['text']

                # Truncate very long texts
                if len(text) > 5000:
                    text = text[:5000] + "... [truncated]"

                # Build metadata
                metadata = {
                    'text_length': len(text),
                    'indexed_at': datetime.now().isoformat()
                }

                # Copy all other fields as metadata
                for key, value in doc.items():
                    if key not in ['id', 'text']:
                        metadata[key] = value

                ids.append(doc['id'])
                texts.append(text)
                metadatas.append(metadata)

            # Generate embeddings on GPU (THIS IS THE FAST PART!)
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            # Convert to list for ChromaDB
            embeddings_list = embeddings.tolist()

            # Add to ChromaDB with pre-computed embeddings
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings_list
            )

            total_indexed += len(ids)

            # Progress update
            if (i // self.batch_size + 1) % 10 == 0 or i + self.batch_size >= total_docs:
                elapsed = time.time() - start_index
                rate = total_indexed / elapsed if elapsed > 0 else 0
                eta = (total_docs - total_indexed) / rate if rate > 0 else 0

                print(f"   Progress: {total_indexed:,}/{total_docs:,} ({100*total_indexed/total_docs:.1f}%) - "
                      f"Rate: {rate:.0f} docs/s - ETA: {eta/60:.1f}m")

        index_time = time.time() - start_index
        total_time = fetch_time + index_time

        print(f"\n✅ {collection_name.upper()} GPU indexing complete:")
        print(f"   Documents indexed: {total_indexed:,}")
        print(f"   Fetch time: {fetch_time:.1f}s")
        print(f"   Index time: {index_time:.1f}s ({total_indexed/index_time:.1f} docs/sec)")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   ChromaDB: {self.rag_db_path}")
        print(f"   Collection: servicedesk_{collection_name}")

    def index_all_gpu(self):
        """Index all collections using GPU"""
        print(f"\n{'='*70}")
        print(f"GPU INDEXING ALL COLLECTIONS")
        print(f"{'='*70}")
        print(f"Device: {self.device}")
        print(f"Batch size: {self.batch_size}")

        overall_start = time.time()
        results = {}

        for collection_name in self.collections.keys():
            try:
                start = time.time()
                self.index_collection_gpu(collection_name)
                elapsed = time.time() - start

                # Get final count
                client = chromadb.PersistentClient(path=self.rag_db_path)
                collection = client.get_collection(f"servicedesk_{collection_name}")
                count = collection.count()

                results[collection_name] = {
                    "status": "success",
                    "count": count,
                    "time": elapsed
                }

            except Exception as e:
                print(f"\n❌ Failed to index {collection_name}: {e}")
                results[collection_name] = {
                    "status": "failed",
                    "error": str(e)
                }

        overall_elapsed = time.time() - overall_start

        # Summary
        print(f"\n{'='*70}")
        print(f"GPU INDEXING SUMMARY")
        print(f"{'='*70}")
        print(f"Total time: {overall_elapsed/60:.1f} minutes")
        print()

        total_docs = 0
        for name, result in results.items():
            if result['status'] == 'success':
                rate = result['count'] / result['time'] if result['time'] > 0 else 0
                print(f"✅ {name:15} - {result['count']:,} docs in {result['time']:.1f}s ({rate:.0f} docs/s)")
                total_docs += result['count']
            else:
                print(f"❌ {name:15} - FAILED: {result.get('error', 'Unknown error')}")

        avg_rate = total_docs / overall_elapsed if overall_elapsed > 0 else 0
        print(f"\n📊 Overall: {total_docs:,} documents at {avg_rate:.0f} docs/sec")

    def benchmark_gpu_vs_ollama(self, sample_size: int = 1000):
        """
        Benchmark GPU vs Ollama performance

        Args:
            sample_size: Number of documents to test
        """
        print(f"\n{'='*70}")
        print(f"GPU vs OLLAMA BENCHMARK")
        print(f"{'='*70}")
        print(f"Sample size: {sample_size:,} documents")
        print(f"GPU Device: {self.device}\n")

        # Use temporary test path
        test_rag_path = os.path.expanduser("~/.maia/servicedesk_rag_gpu_benchmark")
        os.makedirs(test_rag_path, exist_ok=True)

        # Fetch sample
        documents = self.fetch_documents('descriptions', limit=sample_size)
        actual_size = len(documents)
        texts = [doc['text'][:5000] for doc in documents]

        print(f"Fetched: {actual_size:,} documents\n")

        # Test GPU batch embedding
        print("🚀 Testing GPU BATCH EMBEDDING...")
        start = time.time()

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        gpu_time = time.time() - start
        gpu_rate = actual_size / gpu_time if gpu_time > 0 else 0

        print(f"   Time: {gpu_time:.1f}s")
        print(f"   Rate: {gpu_rate:.1f} docs/s")
        print(f"   Embedding shape: {embeddings.shape}")

        # Estimated Ollama performance (based on earlier tests)
        ollama_rate = 15  # docs/sec from serial tests
        ollama_time = actual_size / ollama_rate

        print(f"\n📊 Estimated Ollama Serial:")
        print(f"   Time: {ollama_time:.1f}s")
        print(f"   Rate: {ollama_rate:.1f} docs/s")

        # Results
        speedup = ollama_time / gpu_time if gpu_time > 0 else 0
        print(f"\n{'='*70}")
        print(f"RESULTS:")
        print(f"   GPU:    {gpu_time:.1f}s ({gpu_rate:.1f} docs/s)")
        print(f"   Ollama: {ollama_time:.1f}s ({ollama_rate:.1f} docs/s) [estimated]")
        print(f"   Speedup: {speedup:.1f}x faster")
        print(f"   108K comments: {108000/gpu_rate/60:.1f} min (GPU) vs {108000/ollama_rate/60:.1f} min (Ollama)")
        print(f"{'='*70}")

        # Cleanup
        import shutil
        shutil.rmtree(test_rag_path, ignore_errors=True)


    def search_by_quality(
        self,
        query_text: str = None,
        quality_tier: str = None,        # 'excellent', 'good', 'acceptable', 'poor'
        min_quality_score: float = None,  # 1.0-5.0
        min_empathy_score: int = None,    # 1-5
        min_clarity_score: int = None,    # 1-5
        team: str = None,
        limit: int = 10
    ) -> dict:
        """
        Quality-aware semantic search in comments collection

        Examples:
            # Find excellent empathy examples from Cloud-Kirby team
            results = indexer.search_by_quality(
                query_text='customer escalation response',
                quality_tier='excellent',
                min_empathy_score=4,
                team='Cloud-Kirby',
                limit=10
            )

            # Find all high-quality VPN responses
            results = indexer.search_by_quality(
                query_text='VPN connectivity issue',
                min_quality_score=4.0,
                limit=20
            )

        Returns:
            {
                'ids': [['comment_id_1', 'comment_id_2', ...]],
                'documents': [['comment_text_1', 'comment_text_2', ...]],
                'metadatas': [[{metadata_1}, {metadata_2}, ...]],
                'distances': [[distance_1, distance_2, ...]]
            }
        """

        collection = self.client.get_collection(name='servicedesk_comments')

        # Build ChromaDB where clause (must use $and for multiple conditions)
        where_conditions = []

        # Only search comments with quality analysis
        if quality_tier or min_quality_score or min_empathy_score or min_clarity_score:
            where_conditions.append({'has_quality_analysis': 1})

        if quality_tier:
            where_conditions.append({'quality_tier': quality_tier})

        if team:
            where_conditions.append({'team': team})

        # Build final where clause
        where_clause = None
        if len(where_conditions) == 1:
            where_clause = where_conditions[0]
        elif len(where_conditions) > 1:
            where_clause = {'$and': where_conditions}

        # ChromaDB doesn't support >= for metadata, so we filter post-query
        # Build query
        query_params = {
            'n_results': limit * 3 if (min_quality_score or min_empathy_score or min_clarity_score) else limit
        }

        if query_text:
            # Encode query text with same model used for indexing
            query_embedding = self.model.encode([query_text], convert_to_numpy=True)[0]
            query_params['query_embeddings'] = [query_embedding.tolist()]

        if where_clause:
            query_params['where'] = where_clause

        # Execute search
        results = collection.query(**query_params)

        # Post-filter for numeric thresholds (ChromaDB limitation)
        if min_quality_score or min_empathy_score or min_clarity_score:
            filtered_ids = []
            filtered_docs = []
            filtered_metas = []
            filtered_distances = []

            for i, meta in enumerate(results['metadatas'][0]):
                # Check thresholds
                passes = True

                if min_quality_score and (not meta.get('quality_score') or float(meta['quality_score']) < min_quality_score):
                    passes = False

                if min_empathy_score and (not meta.get('empathy_score') or int(meta['empathy_score']) < min_empathy_score):
                    passes = False

                if min_clarity_score and (not meta.get('clarity_score') or int(meta['clarity_score']) < min_clarity_score):
                    passes = False

                if passes:
                    filtered_ids.append(results['ids'][0][i])
                    filtered_docs.append(results['documents'][0][i])
                    filtered_metas.append(meta)
                    filtered_distances.append(results['distances'][0][i])

                if len(filtered_ids) >= limit:
                    break

            # Reconstruct results
            results = {
                'ids': [filtered_ids],
                'documents': [filtered_docs],
                'metadatas': [filtered_metas],
                'distances': [filtered_distances]
            }

        return results

    def get_quality_statistics(self) -> dict:
        """Get quality analysis statistics from ChromaDB metadata"""

        collection = self.client.get_collection(name='servicedesk_comments')

        # Get all metadata (ChromaDB doesn't have aggregation, so we sample)
        sample = collection.get(
            where={'has_quality_analysis': 1},
            limit=10000,  # Sample up to 10K analyzed comments
            include=['metadatas']
        )

        if not sample['metadatas']:
            return {
                'total_analyzed': 0,
                'error': 'No quality analysis found in ChromaDB'
            }

        metadatas = sample['metadatas']

        # Calculate statistics
        quality_scores = [float(m['quality_score']) for m in metadatas if m.get('quality_score')]
        empathy_scores = [int(m['empathy_score']) for m in metadatas if m.get('empathy_score')]

        quality_tiers = {}
        for m in metadatas:
            tier = m.get('quality_tier', 'unknown')
            quality_tiers[tier] = quality_tiers.get(tier, 0) + 1

        teams = {}
        for m in metadatas:
            team = m.get('team', 'unknown')
            teams[team] = teams.get(team, 0) + 1

        import statistics as stats

        return {
            'total_analyzed': len(metadatas),
            'quality_score': {
                'avg': stats.mean(quality_scores) if quality_scores else 0,
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'stdev': stats.stdev(quality_scores) if len(quality_scores) > 1 else 0
            },
            'empathy_score': {
                'avg': stats.mean(empathy_scores) if empathy_scores else 0,
                'min': min(empathy_scores) if empathy_scores else 0,
                'max': max(empathy_scores) if empathy_scores else 0
            },
            'quality_tiers': quality_tiers,
            'teams': teams
        }


def main():
    parser = argparse.ArgumentParser(description="GPU-Accelerated ServiceDesk RAG Indexer")
    parser.add_argument('--index', type=str, help="Index specific collection")
    parser.add_argument('--index-all', action='store_true', help="Index all collections")
    parser.add_argument('--benchmark', action='store_true', help="Benchmark GPU vs Ollama")
    parser.add_argument('--search-quality', action='store_true', help="Test quality-aware search")
    parser.add_argument('--quality-stats', action='store_true', help="Show quality statistics")
    parser.add_argument('--model', type=str, default='intfloat/e5-base-v2',
                       help="sentence-transformers model (default: intfloat/e5-base-v2)")
    parser.add_argument('--batch-size', type=int, default=64,
                       help="GPU batch size (default: 64, try 128-256 for M4)")
    parser.add_argument('--sample-size', type=int, default=1000,
                       help="Sample size for benchmark (default: 1000)")
    parser.add_argument('--limit', type=int, help="Limit documents to index (for testing)")

    args = parser.parse_args()

    indexer = GPURAGIndexer(model_name=args.model, batch_size=args.batch_size)

    if args.benchmark:
        indexer.benchmark_gpu_vs_ollama(sample_size=args.sample_size)
    elif args.search_quality:
        # Test quality-aware search
        print("\n🔍 Testing Quality-Aware Search")
        print("="*70)

        results = indexer.search_by_quality(
            query_text='customer escalation empathy',
            quality_tier='excellent',
            min_empathy_score=4,
            limit=5
        )

        print(f"\nFound {len(results['documents'][0])} excellent empathy examples:\n")
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"{i}. User: {meta.get('user_name', 'unknown')} | Team: {meta.get('team', 'unknown')}")
            print(f"   Empathy: {meta.get('empathy_score', 'N/A')}/5 | Quality: {meta.get('quality_score', 'N/A')}/5")
            print(f"   {doc[:200]}...")
            print()

    elif args.quality_stats:
        # Show quality statistics
        print("\n📊 Quality Analysis Statistics")
        print("="*70)

        stats = indexer.get_quality_statistics()

        print(f"\nTotal Analyzed: {stats['total_analyzed']:,} comments")
        print(f"\nQuality Scores:")
        print(f"   Average: {stats['quality_score']['avg']:.2f}/5.0")
        print(f"   Range: {stats['quality_score']['min']:.2f} - {stats['quality_score']['max']:.2f}")
        print(f"   Std Dev: {stats['quality_score']['stdev']:.2f}")

        print(f"\nQuality Tiers:")
        for tier, count in sorted(stats['quality_tiers'].items(), key=lambda x: x[1], reverse=True):
            pct = (count / stats['total_analyzed'] * 100) if stats['total_analyzed'] > 0 else 0
            print(f"   {tier:12s}: {count:4d} ({pct:5.1f}%)")

        print(f"\nTop Teams (by analyzed comments):")
        for team, count in sorted(stats['teams'].items(), key=lambda x: x[1], reverse=True)[:5]:
            pct = (count / stats['total_analyzed'] * 100) if stats['total_analyzed'] > 0 else 0
            print(f"   {team:20s}: {count:4d} ({pct:5.1f}%)")

    elif args.index:
        indexer.index_collection_gpu(args.index, limit=args.limit)
    elif args.index_all:
        indexer.index_all_gpu()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
