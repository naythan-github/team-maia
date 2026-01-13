#!/usr/bin/env python3
"""
RAG A/B Test - Sample-Based Comparison

Selects 500 complex technical comments and indexes them with BOTH:
- Ollama (nomic-embed-text, 768-dim)
- GPU (sentence-transformers, 384-dim)

Stores in separate collections for quality comparison.

Created: 2025-10-15
Author: Maia System
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict
import time

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

# Optional dependencies - graceful degradation for importability
try:
    import chromadb
    from chromadb.config import Settings
    import requests
    from sentence_transformers import SentenceTransformer
    import torch
    RAG_DEPS_AVAILABLE = True
except ImportError as e:
    RAG_DEPS_AVAILABLE = False
    chromadb = Settings = requests = SentenceTransformer = torch = None
    _RAG_IMPORT_ERROR = str(e)


def _check_rag_deps():
    """Raise ImportError if RAG dependencies are missing."""
    if not RAG_DEPS_AVAILABLE:
        raise ImportError(f"Missing dependencies: {_RAG_IMPORT_ERROR}. Install with: pip3 install chromadb sentence-transformers torch requests")


class RAGABTestSampler:
    """Sample-based A/B testing for embedding quality"""

    def __init__(self, db_path: str = None, sample_size: int = 500):
        self.db_path = db_path or str(DB_PATH)
        self.sample_size = sample_size
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_rag")

        # Ollama config
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "nomic-embed-text"

        # GPU config
        self.gpu_model_name = "all-MiniLM-L6-v2"
        self.device = self._get_device()

        print(f"✅ RAG A/B Test Sampler initialized")
        print(f"   Sample size: {sample_size} documents")
        print(f"   Database: {self.db_path}")
        print(f"   ChromaDB: {self.rag_db_path}")
        print(f"   Ollama: {self.ollama_model} (768-dim)")
        print(f"   GPU: {self.gpu_model_name} (384-dim) on {self.device}")

    def _get_device(self) -> str:
        """Detect best available device"""
        if torch.backends.mps.is_available():
            return 'mps'
        elif torch.cuda.is_available():
            return 'cuda'
        else:
            return 'cpu'

    def select_complex_comments(self) -> List[Dict]:
        """
        Select 500 most technically complex comments using RAG semantic search

        Strategy:
        1. Use existing RAG to find technical content via L3/L4 queries
        2. Look for technical jargon, not just length
        3. Prioritize worknotes (internal technical) over customer updates
        4. Deduplicate to ensure variety

        This is MUCH better than length-based selection because:
        - "Sorry for delay, investigating..." (long, not technical)
        - "DNS forwarder broken, fixed via dnscmd" (short, very technical)
        """
        print(f"\n📊 Selecting {self.sample_size} technical comments using RAG...")

        # Connect to existing RAG collection
        client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Use existing comments collection
        try:
            rag_collection = client.get_collection("servicedesk_comments")
            print(f"   Using existing RAG: {rag_collection.count():,} documents")
        except Exception as e:
            print(f"   ⚠️  Could not access RAG collection: {e}")
            print(f"   Falling back to length-based selection...")
            return self._select_by_length()

        # Define technical queries targeting L3/L4 content
        technical_queries = [
            # Infrastructure
            "DNS configuration Active Directory domain controller",
            "DHCP scope exhausted VLAN network configuration",
            "firewall rules port blocking connectivity",
            "VPN tunnel IPsec phase authentication failed",

            # Security
            "Azure AD conditional access MFA policy",
            "certificate expired SSL TLS renewal",
            "Intune device compliance encryption BitLocker",
            "group policy GPO not applying domain",

            # Applications
            "Exchange mailbox database corruption ESEUTIL",
            "SQL Server high CPU query execution plan",
            "SharePoint workflow timer job service",
            "Teams audio video codec network quality",

            # Virtualization
            "VMware vMotion storage vMotion migration",
            "Hyper-V replica replication checkpoint",
            "ESXi host disconnected vCenter HA cluster",

            # Storage/Backup
            "RAID array degraded disk rebuild parity",
            "Veeam backup repository retention policy",
            "SAN LUN iSCSI multipath failover",

            # Monitoring
            "SCOM agent not reporting management server",
            "event log errors warnings critical",
            "performance counter threshold alert",

            # Operating Systems
            "Windows update KB patch registry rollback",
            "Blue screen BSOD memory dump analysis",
            "service startup automatic dependencies failed",
        ]

        # Query RAG for technical content
        print(f"   Querying RAG with {len(technical_queries)} technical search terms...")

        seen_ids = set()
        technical_samples = []

        for i, query in enumerate(technical_queries):
            results = rag_collection.query(
                query_texts=[query],
                n_results=50,  # Get top 50 per query
                where={"comment_type": {"$in": ["worknotes", "comments"]}}  # Exclude system
            )

            # Extract results
            if results['ids'] and results['ids'][0]:
                for j, doc_id in enumerate(results['ids'][0]):
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        technical_samples.append({
                            'id': doc_id,
                            'text': results['documents'][0][j],
                            'distance': results['distances'][0][j],
                            'metadata': results['metadatas'][0][j],
                            'query': query
                        })

            if (i + 1) % 5 == 0:
                print(f"   Progress: {i+1}/{len(technical_queries)} queries - Found {len(seen_ids)} unique technical comments")

            # Stop if we have enough samples
            if len(technical_samples) >= self.sample_size * 2:  # Get 2x for filtering
                break

        # Sort by distance (lower = better match to technical queries)
        technical_samples.sort(key=lambda x: x['distance'])

        # Take top N most technical
        final_samples = technical_samples[:self.sample_size]

        # Statistics
        worknotes = sum(1 for s in final_samples if s['metadata'].get('comment_type') == 'worknotes')
        comments = sum(1 for s in final_samples if s['metadata'].get('comment_type') == 'comments')
        avg_distance = sum(s['distance'] for s in final_samples) / len(final_samples)
        avg_length = sum(s['metadata'].get('text_length', len(s['text'])) for s in final_samples) / len(final_samples)

        print(f"\n   ✅ Selected {len(final_samples)} technical comments via RAG")
        print(f"   L3/L4 worknotes: {worknotes} ({worknotes/len(final_samples)*100:.1f}%)")
        print(f"   Customer comments: {comments} ({comments/len(final_samples)*100:.1f}%)")
        print(f"   Average semantic distance: {avg_distance:.3f} (lower = more technical)")
        print(f"   Average length: {avg_length:.0f} characters")

        # Convert to standard format (remove 'distance' and 'query' fields)
        return [{
            'id': s['id'],
            'text': s['text'],
            'metadata': s['metadata']
        } for s in final_samples]

    def _select_by_length(self) -> List[Dict]:
        """Fallback: length-based selection if RAG not available"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT
            comment_id,
            comment_text,
            comment_type,
            ticket_id,
            user_name,
            team,
            created_time,
            LENGTH(comment_text) as text_length
        FROM comments
        WHERE comment_text IS NOT NULL
          AND comment_text != ''
          AND comment_type IN ('worknotes', 'comments')
          AND LENGTH(comment_text) > 200
        ORDER BY LENGTH(comment_text) DESC
        LIMIT ?
        """

        cursor.execute(query, (self.sample_size,))
        rows = cursor.fetchall()

        samples = []
        for row in rows:
            samples.append({
                'id': row['comment_id'],
                'text': row['comment_text'],
                'metadata': {
                    'comment_type': row['comment_type'],
                    'ticket_id': row['ticket_id'],
                    'user_name': row['user_name'] or '',
                    'team': row['team'] or '',
                    'created_time': row['created_time'] or '',
                    'text_length': row['text_length']
                }
            })

        conn.close()
        return samples

    def index_with_ollama(self, samples: List[Dict], collection_name: str = "test_comments_ollama"):
        """Index samples using Ollama embeddings"""
        print(f"\n🔷 Indexing with Ollama ({self.ollama_model})...")

        # Create ChromaDB client and collection
        client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Delete existing test collection if exists
        try:
            client.delete_collection(collection_name)
            print(f"   Deleted existing collection: {collection_name}")
        except Exception:
            pass  # Collection doesn't exist yet

        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Test sample - Ollama 768-dim embeddings"}
        )

        # Generate embeddings and index
        start_time = time.time()
        indexed = 0

        for i, sample in enumerate(samples):
            # Get embedding from Ollama
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.ollama_model, "prompt": sample['text']},
                timeout=30  # B113: Add timeout
            )

            if response.status_code == 200:
                embedding = response.json()['embedding']

                # Add to ChromaDB
                collection.add(
                    ids=[sample['id']],
                    documents=[sample['text']],
                    embeddings=[embedding],
                    metadatas=[sample['metadata']]
                )
                indexed += 1

                if (i + 1) % 50 == 0:
                    rate = indexed / (time.time() - start_time)
                    print(f"   Progress: {indexed}/{len(samples)} ({rate:.1f} docs/sec)")
            else:
                print(f"   ⚠️  Failed to get embedding for doc {sample['id']}")

        elapsed = time.time() - start_time
        print(f"   ✅ Ollama indexing complete: {indexed} docs in {elapsed:.1f}s ({indexed/elapsed:.1f} docs/sec)")

        return collection

    def index_with_gpu(self, samples: List[Dict], collection_name: str = "test_comments_gpu"):
        """Index samples using GPU sentence-transformers"""
        print(f"\n🚀 Indexing with GPU ({self.gpu_model_name})...")

        # Load model
        print(f"   Loading model...")
        model = SentenceTransformer(self.gpu_model_name)
        if self.device != 'cpu':
            model.to(self.device)
        print(f"   Model loaded on {self.device}")

        # Create ChromaDB client and collection
        client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Delete existing test collection if exists
        try:
            client.delete_collection(collection_name)
            print(f"   Deleted existing collection: {collection_name}")
        except Exception:
            pass  # Collection doesn't exist yet

        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Test sample - GPU 384-dim embeddings"}
        )

        # Extract texts
        texts = [s['text'] for s in samples]

        # Generate embeddings in batches
        print(f"   Generating embeddings...")
        start_time = time.time()

        embeddings = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Add to ChromaDB
        print(f"   Indexing to ChromaDB...")
        collection.add(
            ids=[s['id'] for s in samples],
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=[s['metadata'] for s in samples]
        )

        elapsed = time.time() - start_time
        rate = len(samples) / elapsed
        print(f"   ✅ GPU indexing complete: {len(samples)} docs in {elapsed:.1f}s ({rate:.1f} docs/sec)")

        return collection

    def run_ab_test(self):
        """Run complete A/B test workflow"""
        print("="*70)
        print("RAG A/B TEST - SAMPLE-BASED COMPARISON")
        print("="*70)
        print("\nStrategy: GPU embeddings already exist for all 108K comments")
        print("          Creating Ollama embeddings for 500 technical samples")
        print("          Compare quality on same samples")

        # Step 1: Select samples (using length-based selection)
        print("\n📋 Step 1: Selecting technical comments by length...")
        samples = self._select_by_length()

        # Step 2: Index with Ollama ONLY (GPU already exists in main collection)
        print("\n🔄 Step 2: Indexing with Ollama (768-dim)...")
        ollama_collection = self.index_with_ollama(samples)

        print("\n" + "="*70)
        print("A/B TEST INDEXING COMPLETE")
        print("="*70)
        print(f"\n✅ Ollama sample collection created: {self.sample_size} documents")
        print(f"   Collection: test_comments_ollama ({ollama_collection.count():,} docs, 768-dim)")
        print(f"   Comparison: Use existing servicedesk_comments (108K docs, 384-dim GPU)")
        print(f"\n📊 Ready for quality comparison testing")
        print(f"   Run: python3 claude/tools/sre/rag_embedding_quality_test.py")
        print(f"   Compare queries against both collections")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(description='RAG A/B Test Sample-Based Comparison')
    parser.add_argument('--sample-size', type=int, default=500,
                       help='Number of comments to sample (default: 500)')

    args = parser.parse_args()

    sampler = RAGABTestSampler(sample_size=args.sample_size)
    sampler.run_ab_test()


if __name__ == '__main__':
    main()
