#!/usr/bin/env python3
"""
Simple RAG Quality Comparison

Compares Ollama (768-dim) vs GPU (384-dim) on identical technical queries.
Uses correct embedding model for each collection.

Created: 2025-10-15
Author: Maia System
"""

import chromadb
from chromadb.config import Settings
import requests
import json

# Test queries (L3/L4 technical content)
TECHNICAL_QUERIES = [
    "DNS resolution failure on domain controller",
    "Azure AD conditional access policy blocking authentication",
    "Exchange mailbox database corruption after crash",
    "SQL Server high CPU usage causing query timeouts",
    "VMware vMotion failing due to network latency",
    "DHCP scope exhausted on VLAN",
    "Certificate expired causing SSL errors",
    "Active Directory replication not working",
    "Firewall blocking port 443 traffic"
]

def get_ollama_embedding(text: str) -> list:
    """Get embedding from Ollama"""
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        }
    )
    return response.json()['embedding']

def test_collection(client, collection_name: str, query: str, use_ollama: bool = False):
    """Test a single query against a collection"""
    try:
        collection = client.get_collection(collection_name)

        if use_ollama:
            # Generate Ollama embedding for query
            query_embedding = get_ollama_embedding(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
        else:
            # Let ChromaDB use default embedding (GPU)
            results = collection.query(
                query_texts=[query],
                n_results=5
            )

        return {
            'distances': results['distances'][0],
            'documents': results['documents'][0],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [{}] * 5
        }
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    print("="*70)
    print("RAG QUALITY COMPARISON - Ollama (768-dim) vs GPU (384-dim)")
    print("="*70)

    # Connect to ChromaDB
    from pathlib import Path
    rag_path = str(Path.home() / '.maia/servicedesk_rag')
    client = chromadb.PersistentClient(
        path=rag_path,
        settings=Settings(anonymized_telemetry=False)
    )

    # Get collections
    ollama_coll = client.get_collection("test_comments_ollama")
    gpu_coll = client.get_collection("servicedesk_comments")

    print(f"\n📊 Collections:")
    print(f"   Ollama: {ollama_coll.count():,} docs (768-dim)")
    print(f"   GPU: {gpu_coll.count():,} docs (384-dim)")

    print(f"\n🔬 Testing {len(TECHNICAL_QUERIES)} technical queries...")
    print("="*70)

    for i, query in enumerate(TECHNICAL_QUERIES, 1):
        print(f"\n{i}. Query: \"{query}\"")
        print(f"   {'-'*66}")

        # Test Ollama collection
        print(f"   🔷 Ollama (768-dim):")
        ollama_results = test_collection(client, "test_comments_ollama", query, use_ollama=True)
        if ollama_results:
            print(f"      Top result distance: {ollama_results['distances'][0]:.4f}")
            print(f"      Preview: {ollama_results['documents'][0][:100]}...")

        # Test GPU collection (same query, different embedding)
        print(f"\n   🟩 GPU (384-dim):")
        gpu_results = test_collection(client, "servicedesk_comments", query, use_ollama=False)
        if gpu_results:
            print(f"      Top result distance: {gpu_results['distances'][0]:.4f}")
            print(f"      Preview: {gpu_results['documents'][0][:100]}...")

        # Compare
        if ollama_results and gpu_results:
            ollama_dist = ollama_results['distances'][0]
            gpu_dist = gpu_results['distances'][0]

            if ollama_dist < gpu_dist * 0.9:
                winner = "✅ Ollama BETTER"
            elif gpu_dist < ollama_dist * 0.9:
                winner = "✅ GPU BETTER"
            else:
                winner = "➡️  EQUIVALENT"

            print(f"\n      {winner} (Ollama: {ollama_dist:.4f}, GPU: {gpu_dist:.4f})")

    print("\n" + "="*70)
    print("COMPARISON COMPLETE")
    print("="*70)
    print("\nNote: Lower distance = better semantic match")
    print("Ollama has MORE dimensions (768 vs 384) but may not be better for all queries")

if __name__ == '__main__':
    main()
