#!/usr/bin/env python3
"""
RAG Model Comparison - Test Multiple Embedding Models

Tests top-quality embedding models against the same 500 technical ServiceDesk comments:
1. all-mpnet-base-v2 (768-dim, #1 sentence-transformers)
2. bge-large-en-v1.5 (1024-dim, Top 10 MTEB)
3. e5-base-v2 (768-dim, Microsoft)
4. Current: all-MiniLM-L6-v2 (384-dim, baseline)

Created: 2025-10-15
Author: Maia System
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import torch

MAIA_ROOT = Path(__file__).resolve().parents[3]

# Test queries (L3/L4 technical content)
TECHNICAL_QUERIES = [
    ("Infrastructure", "DNS resolution failure on domain controller"),
    ("Security", "Azure AD conditional access policy blocking authentication"),
    ("Application", "Exchange mailbox database corruption after crash"),
    ("Performance", "SQL Server high CPU usage causing query timeouts"),
    ("Virtualization", "VMware vMotion failing due to network latency"),
    ("Storage", "DHCP scope exhausted on VLAN"),
    ("Security", "Certificate expired causing SSL errors"),
    ("Infrastructure", "Active Directory replication not working"),
    ("Security", "Firewall blocking port 443 traffic"),
    ("Application", "SharePoint workflow timer job not running"),
]

# Models to test (name, dimensions, description)
MODELS_TO_TEST = [
    ("sentence-transformers/all-mpnet-base-v2", 768, "#1 sentence-transformers model"),
    ("BAAI/bge-large-en-v1.5", 1024, "Top 10 MTEB, optimized for retrieval"),
    ("BAAI/bge-base-en-v1.5", 768, "Top 20 MTEB, balanced"),
    ("intfloat/e5-base-v2", 768, "Microsoft E5, enterprise quality"),
]


class ModelComparer:
    """Compare multiple embedding models on same dataset"""

    def __init__(self):
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_rag")
        self.device = self._get_device()

        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get the Ollama test collection for samples
        self.ollama_collection = self.client.get_collection("test_comments_ollama")
        self.samples = self._get_samples()

        print(f"✅ Model Comparer initialized")
        print(f"   Device: {self.device}")
        print(f"   Samples: {len(self.samples)} documents")
        print(f"   Test queries: {len(TECHNICAL_QUERIES)}")

    def _get_device(self) -> str:
        """Get best available device"""
        if torch.backends.mps.is_available():
            return 'mps'
        elif torch.cuda.is_available():
            return 'cuda'
        return 'cpu'

    def _get_samples(self) -> List[Dict]:
        """Get all samples from Ollama collection"""
        print("\n📋 Loading samples from test_comments_ollama...")

        # Get all documents
        results = self.ollama_collection.get(
            include=['documents', 'metadatas']
        )

        samples = []
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            samples.append({
                'id': f'sample_{i}',
                'text': doc,
                'metadata': metadata or {}
            })

        print(f"   ✓ Loaded {len(samples)} samples")
        return samples

    def test_model(self, model_name: str, dimensions: int, description: str) -> Dict:
        """Test a single model"""
        print(f"\n{'='*70}")
        print(f"TESTING: {model_name}")
        print(f"Description: {description}")
        print(f"Dimensions: {dimensions}")
        print(f"{'='*70}")

        collection_name = f"test_{model_name.split('/')[-1].replace('-', '_')}"

        try:
            # Load model
            print(f"\n1️⃣  Loading model...")
            start_time = time.time()
            model = SentenceTransformer(model_name, device=self.device)
            load_time = time.time() - start_time
            print(f"   ✓ Model loaded in {load_time:.1f}s")

            # Generate embeddings
            print(f"\n2️⃣  Generating embeddings for {len(self.samples)} documents...")
            start_time = time.time()

            texts = [s['text'] for s in self.samples]
            embeddings = model.encode(
                texts,
                batch_size=64,
                show_progress_bar=True,
                convert_to_numpy=True
            )

            embed_time = time.time() - start_time
            embed_rate = len(self.samples) / embed_time
            print(f"   ✓ Generated {len(embeddings)} embeddings in {embed_time:.1f}s ({embed_rate:.1f} docs/sec)")

            # Create ChromaDB collection
            print(f"\n3️⃣  Creating ChromaDB collection: {collection_name}...")

            # Delete if exists
            try:
                self.client.delete_collection(collection_name)
                print(f"   Deleted existing collection")
            except Exception:
                pass  # Collection doesn't exist yet

            collection = self.client.create_collection(
                name=collection_name,
                metadata={"model": model_name, "dimensions": dimensions}
            )

            # Add documents
            ids = [s['id'] for s in self.samples]
            metadatas = [s['metadata'] for s in self.samples]

            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings.tolist(),
                metadatas=metadatas
            )

            print(f"   ✓ Added {len(ids)} documents to collection")

            # Run test queries
            print(f"\n4️⃣  Running {len(TECHNICAL_QUERIES)} test queries...")
            query_results = []

            for category, query in TECHNICAL_QUERIES:
                # Generate query embedding
                query_embedding = model.encode([query], convert_to_numpy=True)[0]

                # Search
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=5
                )

                avg_distance = sum(results['distances'][0]) / len(results['distances'][0])
                query_results.append({
                    'category': category,
                    'query': query,
                    'avg_distance': avg_distance,
                    'top_distance': results['distances'][0][0]
                })

            avg_top_distance = sum(r['top_distance'] for r in query_results) / len(query_results)

            print(f"   ✓ Average top result distance: {avg_top_distance:.4f}")

            return {
                'model': model_name,
                'dimensions': dimensions,
                'description': description,
                'load_time': load_time,
                'embed_time': embed_time,
                'embed_rate': embed_rate,
                'avg_top_distance': avg_top_distance,
                'query_results': query_results,
                'collection_name': collection_name
            }

        except Exception as e:
            print(f"   ❌ Error testing {model_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def compare_all(self):
        """Compare all models"""
        print(f"\n{'='*70}")
        print("RAG EMBEDDING MODEL COMPARISON")
        print(f"{'='*70}")
        print(f"\nTesting {len(MODELS_TO_TEST)} models on {len(self.samples)} documents")
        print(f"Quality metric: Lower distance = better semantic match")

        results = []

        for model_name, dimensions, description in MODELS_TO_TEST:
            result = self.test_model(model_name, dimensions, description)
            if result:
                results.append(result)

        # Print comparison
        print(f"\n{'='*70}")
        print("COMPARISON RESULTS")
        print(f"{'='*70}")

        # Sort by quality (lower distance = better)
        results.sort(key=lambda x: x['avg_top_distance'])

        print(f"\n🏆 RANKING (by average top result distance):\n")

        for i, r in enumerate(results, 1):
            print(f"{i}. {r['model']}")
            print(f"   Description: {r['description']}")
            print(f"   Dimensions: {r['dimensions']}")
            print(f"   Quality (avg top distance): {r['avg_top_distance']:.4f}")
            print(f"   Speed: {r['embed_rate']:.1f} docs/sec")
            print(f"   Collection: {r['collection_name']}")
            print()

        # Compare to baseline (all-MiniLM-L6-v2 if tested)
        if len(results) > 0:
            best = results[0]
            print(f"\n✅ RECOMMENDED MODEL: {best['model']}")
            print(f"   Best quality with {best['avg_top_distance']:.4f} average distance")
            print(f"   {best['embed_rate']:.1f} docs/sec indexing speed")
            print(f"   Collection ready: {best['collection_name']}")

        return results


def main():
    comparer = ModelComparer()
    results = comparer.compare_all()

    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print(f"{'='*70}")
    print("""
1. Review quality scores above (lower distance = better)
2. Choose best model for your requirements
3. Re-index full collection with chosen model:
   python3 claude/tools/sre/servicedesk_gpu_rag_indexer.py --model <chosen_model>

Collections created (ready for testing):
""")

    for r in results:
        print(f"   - {r['collection_name']} ({r['dimensions']}-dim)")


if __name__ == '__main__':
    main()
