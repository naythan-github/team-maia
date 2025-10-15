#!/usr/bin/env python3
"""
RAG Diagnostic Tool - Identify ChromaDB timeout issues
"""

import chromadb
from chromadb.config import Settings
import time
import sys

def test_collection_access():
    """Test basic collection access"""
    print("="*70)
    print("RAG DIAGNOSTIC - ChromaDB Access Test")
    print("="*70)

    try:
        print("\n1. Connecting to ChromaDB...")
        start = time.time()
        client = chromadb.PersistentClient(
            path='/Users/naythandawe/.maia/servicedesk_rag',
            settings=Settings(anonymized_telemetry=False)
        )
        print(f"   ✅ Connected in {time.time()-start:.2f}s")

        print("\n2. Listing collections...")
        start = time.time()
        collections = client.list_collections()
        print(f"   ✅ Found {len(collections)} collections in {time.time()-start:.2f}s")

        for coll in collections:
            print(f"\n3. Testing collection: {coll.name}")

            # Test count
            start = time.time()
            count = coll.count()
            print(f"   Count: {count:,} docs ({time.time()-start:.2f}s)")

            # Test peek (first few docs)
            start = time.time()
            try:
                peek = coll.peek(limit=3)
                print(f"   ✅ Peek: Retrieved {len(peek['ids'])} docs ({time.time()-start:.2f}s)")
            except Exception as e:
                print(f"   ⚠️  Peek failed: {e}")

            # Test simple query with timeout
            if count < 10000:  # Only test small collections
                print(f"   Testing query on small collection ({count:,} docs)...")
                start = time.time()
                try:
                    results = coll.query(
                        query_texts=["test query"],
                        n_results=5
                    )
                    print(f"   ✅ Query: Retrieved {len(results['ids'][0])} results ({time.time()-start:.2f}s)")
                except Exception as e:
                    print(f"   ❌ Query failed: {e}")
            else:
                print(f"   ⚠️  Skipping query test (collection too large: {count:,} docs)")
                print(f"   This is likely causing timeouts in quality comparison!")

        print("\n" + "="*70)
        print("DIAGNOSTIC COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_collection_access()
