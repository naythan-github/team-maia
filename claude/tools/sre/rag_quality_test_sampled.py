#!/usr/bin/env python3
"""
RAG Quality Test - Sampled Approach

Strategy to avoid timeout issues:
1. Test Ollama collection (500 docs) - no timeout risk
2. Create small GPU test collection (same 500 docs) - no timeout risk
3. Compare quality on identical dataset

This bypasses the 108K GPU collection timeout issue.

Created: 2025-10-15
Author: Maia Data Analysis Agent
"""

import chromadb
from chromadb.config import Settings
import requests
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import json
from datetime import datetime
from pathlib import Path

MAIA_ROOT = Path(__file__).resolve().parents[3]

# Test queries (L3/L4 technical content)
TECHNICAL_QUERIES = [
    {
        "query": "DNS resolution failure on domain controller",
        "category": "Infrastructure",
        "expected_terms": ["DNS", "domain", "controller", "resolution"]
    },
    {
        "query": "Azure AD conditional access policy blocking authentication",
        "category": "Security",
        "expected_terms": ["Azure", "conditional access", "authentication", "MFA"]
    },
    {
        "query": "Exchange mailbox database corruption after crash",
        "category": "Application",
        "expected_terms": ["Exchange", "mailbox", "database", "corruption"]
    },
    {
        "query": "SQL Server high CPU usage causing query timeouts",
        "category": "Performance",
        "expected_terms": ["SQL", "CPU", "performance", "query"]
    },
    {
        "query": "VMware vMotion failing due to network latency",
        "category": "Virtualization",
        "expected_terms": ["VMware", "vMotion", "network", "latency"]
    },
    {
        "query": "DHCP scope exhausted on VLAN",
        "category": "Infrastructure",
        "expected_terms": ["DHCP", "scope", "VLAN", "IP"]
    },
    {
        "query": "Certificate expired causing SSL errors",
        "category": "Security",
        "expected_terms": ["certificate", "expired", "SSL", "TLS"]
    },
    {
        "query": "Active Directory replication not working",
        "category": "Infrastructure",
        "expected_terms": ["Active Directory", "replication", "domain"]
    },
    {
        "query": "Firewall blocking port 443 traffic",
        "category": "Security",
        "expected_terms": ["firewall", "port", "443", "blocking"]
    },
    {
        "query": "password reset for locked account",
        "category": "Basic Support",
        "expected_terms": ["password", "reset", "locked", "account"]
    }
]


class RAGQualityTester:
    """Compare Ollama vs GPU embeddings on identical dataset"""

    def __init__(self):
        self.rag_path = "/Users/naythandawe/.maia/servicedesk_rag"
        self.client = chromadb.PersistentClient(
            path=self.rag_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Ollama config
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "nomic-embed-text"

        # GPU config
        self.gpu_model_name = "all-MiniLM-L6-v2"
        self.device = self._get_device()

        print("="*70)
        print("RAG QUALITY TEST - SAMPLED APPROACH")
        print("="*70)
        print(f"\nStrategy: Test both models on SAME 500-doc sample")
        print(f"Ollama: {self.ollama_model} (768-dim)")
        print(f"GPU:    {self.gpu_model_name} (384-dim) on {self.device}")

    def _get_device(self) -> str:
        """Detect best available device"""
        if torch.backends.mps.is_available():
            return 'mps'
        elif torch.cuda.is_available():
            return 'cuda'
        return 'cpu'

    def create_gpu_test_collection(self):
        """Create GPU version of same 500 docs from Ollama collection"""
        print("\n📋 Step 1: Creating GPU test collection from Ollama samples...")

        # Get Ollama collection
        ollama_coll = self.client.get_collection("test_comments_ollama")
        print(f"   Ollama collection: {ollama_coll.count():,} docs")

        # Get all documents from Ollama collection
        print(f"   Retrieving documents...")
        all_data = ollama_coll.get()

        documents = all_data['documents']
        ids = all_data['ids']
        metadatas = all_data['metadatas']

        print(f"   Retrieved {len(documents):,} documents")

        # Load GPU model
        print(f"   Loading GPU model...")
        model = SentenceTransformer(self.gpu_model_name)
        if self.device != 'cpu':
            model.to(self.device)
        print(f"   Model loaded on {self.device}")

        # Generate GPU embeddings
        print(f"   Generating GPU embeddings...")
        embeddings = model.encode(
            documents,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Create GPU test collection
        print(f"   Creating GPU test collection...")
        try:
            self.client.delete_collection("test_comments_gpu")
        except:
            pass

        gpu_coll = self.client.create_collection(
            name="test_comments_gpu",
            metadata={"description": "Test sample - GPU 384-dim embeddings (same docs as Ollama)"}
        )

        # Add to collection
        gpu_coll.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"   ✅ GPU test collection created: {gpu_coll.count():,} docs")
        return gpu_coll

    def get_ollama_embedding(self, text: str) -> list:
        """Get embedding from Ollama"""
        response = requests.post(
            f"{self.ollama_url}/api/embeddings",
            json={"model": self.ollama_model, "prompt": text}
        )
        if response.status_code == 200:
            return response.json()['embedding']
        else:
            raise Exception(f"Ollama API error: {response.status_code}")

    def test_query(self, query: str, collection_name: str, use_ollama_embedding: bool = False):
        """Test a single query against a collection"""
        collection = self.client.get_collection(collection_name)

        if use_ollama_embedding:
            # Use Ollama embedding for query
            query_embedding = self.get_ollama_embedding(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
        else:
            # Use default (text-based query with GPU model)
            results = collection.query(
                query_texts=[query],
                n_results=5
            )

        return {
            'distances': results['distances'][0],
            'documents': results['documents'][0],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [{}] * 5
        }

    def calculate_term_precision(self, documents: list, expected_terms: list) -> float:
        """Calculate what % of expected technical terms appear in top results"""
        if not documents or not expected_terms:
            return 0.0

        all_text = " ".join(documents).lower()
        matches = sum(1 for term in expected_terms if term.lower() in all_text)
        return matches / len(expected_terms)

    def run_comparison(self):
        """Run full quality comparison"""
        print("\n" + "="*70)
        print("QUALITY COMPARISON TEST")
        print("="*70)

        results = []

        for i, test in enumerate(TECHNICAL_QUERIES, 1):
            print(f"\n[{i}/{len(TECHNICAL_QUERIES)}] {test['category']}: {test['query']}")

            # Test Ollama
            print(f"   🔷 Ollama (768-dim)...")
            try:
                ollama_results = self.test_query(test['query'], "test_comments_ollama", use_ollama_embedding=True)
                ollama_precision = self.calculate_term_precision(ollama_results['documents'], test['expected_terms'])
                ollama_avg_dist = np.mean(ollama_results['distances'])
                print(f"      Distance: {ollama_avg_dist:.4f}, Precision: {ollama_precision:.1%}")
            except Exception as e:
                print(f"      ❌ Error: {e}")
                ollama_precision = None
                ollama_avg_dist = None

            # Test GPU
            print(f"   🟩 GPU (384-dim)...")
            try:
                gpu_results = self.test_query(test['query'], "test_comments_gpu", use_ollama_embedding=False)
                gpu_precision = self.calculate_term_precision(gpu_results['documents'], test['expected_terms'])
                gpu_avg_dist = np.mean(gpu_results['distances'])
                print(f"      Distance: {gpu_avg_dist:.4f}, Precision: {gpu_precision:.1%}")
            except Exception as e:
                print(f"      ❌ Error: {e}")
                gpu_precision = None
                gpu_avg_dist = None

            # Compare
            if ollama_precision is not None and gpu_precision is not None:
                diff = gpu_precision - ollama_precision
                if abs(diff) < 0.10:  # Within 10%
                    verdict = "≈ EQUIVALENT"
                elif diff > 0:
                    verdict = f"✅ GPU BETTER (+{diff:.1%})"
                else:
                    verdict = f"⚠️  OLLAMA BETTER ({diff:.1%})"
                print(f"      Verdict: {verdict}")

            results.append({
                'query': test['query'],
                'category': test['category'],
                'ollama': {
                    'precision': ollama_precision,
                    'avg_distance': ollama_avg_dist
                },
                'gpu': {
                    'precision': gpu_precision,
                    'avg_distance': gpu_avg_dist
                }
            })

        # Calculate overall statistics
        ollama_precisions = [r['ollama']['precision'] for r in results if r['ollama']['precision'] is not None]
        gpu_precisions = [r['gpu']['precision'] for r in results if r['gpu']['precision'] is not None]

        print("\n" + "="*70)
        print("OVERALL RESULTS")
        print("="*70)

        if ollama_precisions and gpu_precisions:
            ollama_avg = np.mean(ollama_precisions)
            gpu_avg = np.mean(gpu_precisions)
            diff = gpu_avg - ollama_avg

            print(f"\nOllama (768-dim):")
            print(f"  Average precision: {ollama_avg:.1%}")
            print(f"  Range: {min(ollama_precisions):.1%} - {max(ollama_precisions):.1%}")

            print(f"\nGPU (384-dim):")
            print(f"  Average precision: {gpu_avg:.1%}")
            print(f"  Range: {min(gpu_precisions):.1%} - {max(gpu_precisions):.1%}")

            print(f"\nDifference: {diff:+.1%}")

            print("\n" + "="*70)
            print("RECOMMENDATION")
            print("="*70)

            if abs(diff) < 0.05:  # < 5% difference
                print("\n✅ VERDICT: Equivalent quality (< 5% difference)")
                print("\n💡 Recommendation: USE GPU")
                print("   Reasons:")
                print("   - Equivalent retrieval quality for L3/L4 technical content")
                print("   - 6.5x faster indexing (97 docs/sec vs 15 docs/sec)")
                print("   - 50% smaller storage (384-dim vs 768-dim)")
                print("   - Already indexed 108K documents")
                print("   - No need to re-index with Ollama")
            elif diff > 0:
                print(f"\n✅ VERDICT: GPU superior ({diff:+.1%} better precision)")
                print("\n💡 Recommendation: STRONGLY USE GPU")
            else:
                print(f"\n⚠️  VERDICT: Ollama superior ({-diff:.1%} better precision)")
                print("\n💡 Recommendation: Consider trade-offs")
                print("   - Ollama: Better quality but 6.5x slower")
                print("   - GPU: Slightly lower quality but much faster")
                print(f"   - Quality difference: {-diff:.1%}")
                print("   - Decision depends on priority: quality vs speed")

            # Save results
            output_file = MAIA_ROOT / "claude/data/rag_quality_test_results.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'test_date': datetime.now().isoformat(),
                    'test_approach': 'Sampled comparison on identical 500-doc dataset',
                    'ollama_model': 'nomic-embed-text (768-dim)',
                    'gpu_model': 'all-MiniLM-L6-v2 (384-dim)',
                    'test_queries': results,
                    'summary': {
                        'ollama_avg_precision': float(ollama_avg),
                        'gpu_avg_precision': float(gpu_avg),
                        'difference': float(diff),
                        'verdict': 'GPU' if diff >= -0.05 else 'Ollama'
                    }
                }, f, indent=2)

            print(f"\n📊 Detailed results saved to: {output_file}")

        print("="*70)


def main():
    tester = RAGQualityTester()

    # Check if GPU test collection exists
    try:
        gpu_coll = tester.client.get_collection("test_comments_gpu")
        print(f"\n✅ GPU test collection already exists: {gpu_coll.count():,} docs")
        print(f"   Skipping creation step...")
    except:
        print(f"\n⚠️  GPU test collection not found, creating it...")
        tester.create_gpu_test_collection()

    # Run comparison
    tester.run_comparison()


if __name__ == '__main__':
    main()
