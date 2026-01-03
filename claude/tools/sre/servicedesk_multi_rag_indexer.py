#!/usr/bin/env python3
"""
ServiceDesk Multi-Collection RAG Indexer

Creates separate ChromaDB collections for different ServiceDesk text fields:
- comments: Communication quality analysis (108K entries)
- descriptions: Incident similarity search (10.9K entries)
- solutions: Resolution recommendations (10.7K entries)
- titles: Quick pattern matching (10.9K entries)
- work_logs: Time tracking analysis (73K entries)

Architecture: Separate collections for query performance and targeted use cases
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

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ Missing chromadb. Install: pip3 install chromadb")
    sys.exit(1)


class ServiceDeskMultiRAGIndexer:
    """Index multiple ServiceDesk text fields into separate ChromaDB collections"""

    def __init__(self, db_path: str = None, embedding_model: str = "nomic-embed-text"):
        """Initialize multi-collection RAG indexer"""
        self.db_path = db_path or str(DB_PATH)
        self.embedding_model = embedding_model

        # ChromaDB storage location
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_rag")
        os.makedirs(self.rag_db_path, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=self.rag_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Collection definitions
        self.collections = {
            "comments": {
                "description": "ServiceDesk comment communications (108K entries, avg 609 chars)",
                "table": "comments",
                "id_field": "comment_id",
                "text_field": "comment_text",
                "metadata_fields": ["ticket_id", "user_name", "team", "created_time", "visible_to_customer", "comment_type"]
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
                "id_field": "rowid",  # SQLite implicit rowid
                "text_field": "[TS-Description]",
                "metadata_fields": ["[TS-User Username]", "[TS-Title]", "[TS-Date]", "[TS-Hours]", "[TS-Crm ID]", "[TS-Category]"]
            }
        }

        print(f"✅ ServiceDesk Multi-RAG Indexer initialized")
        print(f"   Embedding model: {embedding_model}")
        print(f"   Database: {self.db_path}")
        print(f"   ChromaDB path: {self.rag_db_path}")
        print(f"   Collections: {len(self.collections)}")

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        config = self.collections[name]
        return self.chroma_client.get_or_create_collection(
            name=f"servicedesk_{name}",
            metadata={"description": config["description"]}
        )

    def _build_index_query(self, collection_name: str, limit: int = None) -> str:
        """Build SQL query for indexing a collection.

        Args:
            collection_name: Name of collection
            limit: Max documents to fetch

        Returns:
            SQL query string
        """
        config = self.collections[collection_name]
        metadata_select = ", ".join(config['metadata_fields'])

        # Build WHERE clause based on collection type
        if collection_name == "comments":
            where_clause = "WHERE comment_text IS NOT NULL AND comment_text != ''"
        else:
            where_clause = f"WHERE {config['text_field']} IS NOT NULL AND {config['text_field']} != ''"

        limit_clause = f"LIMIT {limit}" if limit else ""

        return f"""
            SELECT
                {config['id_field']} as id,
                {config['text_field']} as text,
                {metadata_select}
            FROM {config['table']}
            {where_clause}
            {limit_clause}
        """

    def _process_row_to_document(self, row, collection_name: str, existing_ids: set):
        """Process a database row into document tuple.

        Args:
            row: sqlite3.Row object
            collection_name: Name of collection
            existing_ids: Set of already indexed IDs (for resumable indexing)

        Returns:
            Tuple of (id, text, metadata) or None if row should be skipped
        """
        config = self.collections[collection_name]
        row_id = str(row['id'])

        # Skip if already indexed
        if collection_name == "comments" and row_id in existing_ids:
            return None

        text = row['text']
        if not text or text.strip() == '':
            return None

        # Truncate very long texts
        if len(text) > 5000:
            text = text[:5000] + "... [truncated]"

        # Build metadata
        metadata = {
            "text_length": len(text),
            "indexed_at": datetime.now().isoformat()
        }

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
                metadata[clean_field] = str(value)

        return (row_id, text, metadata)

    def _print_index_completion(self, collection_name: str, total_indexed: int, elapsed: float):
        """Print indexing completion summary.

        Args:
            collection_name: Name of collection
            total_indexed: Total documents indexed
            elapsed: Time elapsed in seconds
        """
        rate = total_indexed / elapsed if elapsed > 0 else 0
        print(f"\n✅ {collection_name.upper()} indexing complete: {total_indexed:,} documents indexed")
        print(f"   Time: {elapsed:.1f}s ({rate:.1f} docs/sec)")
        print(f"   ChromaDB: {self.rag_db_path}")
        print(f"   Collection: servicedesk_{collection_name}")

    def index_collection(self, collection_name: str, batch_size: int = 100, limit: int = None):
        """
        Index a single collection from ServiceDesk database

        Args:
            collection_name: Name of collection (comments, descriptions, solutions, titles, work_logs)
            batch_size: Documents per batch (default: 100)
            limit: Max documents to index (None = all)
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}. Available: {list(self.collections.keys())}")

        config = self.collections[collection_name]
        collection = self.get_or_create_collection(collection_name)

        print(f"\n{'='*70}")
        print(f"INDEXING: {collection_name}")
        print(f"{'='*70}")
        print(f"Description: {config['description']}")
        print(f"Table: {config['table']}")
        print(f"Text field: {config['text_field']}")

        # Get existing IDs for resumable indexing (comments only)
        existing_ids = set()
        if collection_name == "comments":
            try:
                existing = collection.get(limit=200000)
                existing_ids = set(existing['ids'])
                print(f"   Found {len(existing_ids)} already indexed comments")
            except Exception:
                pass

        # Build and execute query
        query = self._build_index_query(collection_name, limit)
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"\n📊 Fetching data from database...")
        start_time = time.time()
        cursor.execute(query)

        # Process in batches
        total_indexed = 0
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break

            ids, documents, metadatas = [], [], []
            for row in rows:
                result = self._process_row_to_document(row, collection_name, existing_ids)
                if result:
                    row_id, text, metadata = result
                    ids.append(row_id)
                    documents.append(text)
                    metadatas.append(metadata)

            if ids:
                collection.add(ids=ids, documents=documents, metadatas=metadatas)
                total_indexed += len(ids)
                print(f"   Progress: {total_indexed:,} indexed - Batch: {len(ids)} documents")

        conn.close()
        self._print_index_completion(collection_name, total_indexed, time.time() - start_time)

    def index_all(self, batch_size: int = 100, skip_existing: bool = True):
        """Index all collections"""
        print(f"\n{'='*70}")
        print(f"INDEXING ALL COLLECTIONS")
        print(f"{'='*70}")

        start_time = time.time()
        results = {}

        for collection_name in self.collections.keys():
            try:
                # Check if already exists
                if skip_existing:
                    try:
                        collection = self.get_or_create_collection(collection_name)
                        count = collection.count()
                        if count > 0:
                            print(f"\n⏭️  SKIPPING {collection_name}: Already has {count:,} documents")
                            results[collection_name] = {"status": "skipped", "count": count}
                            continue
                    except Exception:
                        pass

                self.index_collection(collection_name, batch_size=batch_size)
                collection = self.get_or_create_collection(collection_name)
                results[collection_name] = {"status": "indexed", "count": collection.count()}

            except Exception as e:
                print(f"\n❌ Failed to index {collection_name}: {e}")
                results[collection_name] = {"status": "failed", "error": str(e)}

        elapsed = time.time() - start_time

        # Summary
        print(f"\n{'='*70}")
        print(f"INDEXING SUMMARY")
        print(f"{'='*70}")
        print(f"Total time: {elapsed/60:.1f} minutes")
        print()

        for name, result in results.items():
            status = result['status']
            if status == "indexed":
                print(f"✅ {name:15} - {result['count']:,} documents indexed")
            elif status == "skipped":
                print(f"⏭️  {name:15} - {result['count']:,} documents (already indexed)")
            else:
                print(f"❌ {name:15} - FAILED: {result.get('error', 'Unknown error')}")

    def get_stats(self):
        """Get statistics for all collections"""
        print(f"\n{'='*70}")
        print(f"COLLECTION STATISTICS")
        print(f"{'='*70}")

        for name in self.collections.keys():
            try:
                collection = self.get_or_create_collection(name)
                count = collection.count()

                # Get sample metadata
                sample = collection.peek(limit=1)
                avg_length = sample['metadatas'][0].get('text_length', 'N/A') if sample['metadatas'] else 'N/A'

                print(f"\n{name.upper()}:")
                print(f"  Collection: servicedesk_{name}")
                print(f"  Documents: {count:,}")
                print(f"  Sample length: {avg_length}")
                print(f"  Description: {self.collections[name]['description']}")

            except Exception as e:
                print(f"\n{name.upper()}: ❌ Error - {e}")

    def search_example(self, collection_name: str, query: str, n_results: int = 5):
        """Example search query"""
        collection = self.get_or_create_collection(collection_name)

        print(f"\n{'='*70}")
        print(f"SEARCH EXAMPLE: {collection_name}")
        print(f"{'='*70}")
        print(f"Query: {query}")
        print()

        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\n{i}. Relevance: {1-distance:.3f}")
            print(f"   Text: {doc[:200]}...")
            print(f"   Metadata: {metadata}")


def main():
    parser = argparse.ArgumentParser(description="ServiceDesk Multi-Collection RAG Indexer")
    parser.add_argument('--index', type=str, help="Index specific collection (comments, descriptions, solutions, titles, work_logs)")
    parser.add_argument('--index-all', action='store_true', help="Index all collections")
    parser.add_argument('--stats', action='store_true', help="Show collection statistics")
    parser.add_argument('--search', type=str, help="Search query")
    parser.add_argument('--collection', type=str, default='descriptions', help="Collection to search (default: descriptions)")
    parser.add_argument('--batch-size', type=int, default=100, help="Batch size for indexing (default: 100)")
    parser.add_argument('--limit', type=int, help="Limit documents to index (for testing)")

    args = parser.parse_args()

    indexer = ServiceDeskMultiRAGIndexer()

    if args.index:
        indexer.index_collection(args.index, batch_size=args.batch_size, limit=args.limit)
    elif args.index_all:
        indexer.index_all(batch_size=args.batch_size)
    elif args.stats:
        indexer.get_stats()
    elif args.search:
        indexer.search_example(args.collection, args.search)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
