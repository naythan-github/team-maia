#!/usr/bin/env python3
"""
Email RAG System - Semantic Email Search with Local Embeddings

Indexes emails from Mail.app into ChromaDB vector store for intelligent semantic search.
Uses local sentence-transformers for privacy-preserving embeddings.

Features:
- Local embeddings (all-MiniLM-L6-v2) - 384 dimensions, fast, privacy-first
- Metadata filtering (sender, date, read status, mailbox)
- Semantic search across email content and subjects
- Incremental indexing (only new/updated emails)
- Zero cloud transmission for Orro Group client data

Integration:
- Works with macos_mail_bridge.py for email access
- Compatible with M365 Integration Agent architecture
- Ready for Personal Assistant Agent coordination

Author: Maia System
Created: 2025-10-02 (Phase 80)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import hashlib

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip3 install chromadb sentence-transformers")
    sys.exit(1)

from claude.tools.macos_mail_bridge import MacOSMailBridge


class EmailRAGSystem:
    """Semantic email search with local embeddings"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Email RAG system

        Args:
            db_path: Optional ChromaDB path (defaults to ~/.maia/email_rag)
        """
        self.db_path = db_path or os.path.expanduser("~/.maia/email_rag")
        os.makedirs(self.db_path, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create email collection
        self.collection = self.client.get_or_create_collection(
            name="emails",
            metadata={"description": "Email messages with semantic search"}
        )

        # Initialize local embedding model
        print("📦 Loading local embedding model (all-MiniLM-L6-v2)...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded (384 dimensions, local processing)")

        # Initialize Mail.app bridge
        self.mail_bridge = MacOSMailBridge()

        # Track indexed emails
        self.index_state_file = os.path.join(self.db_path, "index_state.json")
        self.index_state = self._load_index_state()

    def _load_index_state(self) -> Dict[str, Any]:
        """Load indexing state from disk"""
        if os.path.exists(self.index_state_file):
            with open(self.index_state_file, 'r') as f:
                return json.load(f)
        return {"indexed_emails": {}, "last_index_time": None}

    def _save_index_state(self):
        """Save indexing state to disk"""
        with open(self.index_state_file, 'w') as f:
            json.dump(self.index_state, f, indent=2)

    def _email_hash(self, message: Dict[str, Any]) -> str:
        """Generate unique hash for email"""
        key = f"{message['id']}:{message['subject']}:{message['date']}"
        return hashlib.md5(key.encode()).hexdigest()

    def index_inbox(self, limit: Optional[int] = None, force: bool = False) -> Dict[str, int]:
        """
        Index inbox emails into RAG system

        Args:
            limit: Optional limit on number of emails to index
            force: Force re-indexing of all emails

        Returns:
            Statistics about indexing operation
        """
        print("📧 Retrieving inbox messages...")
        messages = self.mail_bridge.get_inbox_messages(limit=limit or 1000)

        stats = {"total": len(messages), "new": 0, "skipped": 0, "errors": 0}

        documents = []
        metadatas = []
        ids = []

        for msg in messages:
            msg_hash = self._email_hash(msg)

            # Skip already indexed (unless force)
            if not force and msg_hash in self.index_state["indexed_emails"]:
                stats["skipped"] += 1
                continue

            try:
                # Get full content
                content = self.mail_bridge.get_message_content(msg['id'])

                # Prepare document (subject + content for semantic search)
                doc_text = f"{content['subject']}\n\n{content['content']}"

                # Prepare metadata
                metadata = {
                    "message_id": msg['id'],
                    "subject": content['subject'][:500],  # Limit for ChromaDB
                    "sender": content['from'][:200],
                    "date": content['date'],
                    "read": str(content['read']),
                    "mailbox": "Inbox"
                }

                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(msg_hash)

                stats["new"] += 1

                # Progress indicator
                if stats["new"] % 10 == 0:
                    print(f"  📝 Indexed {stats['new']} emails...")

            except Exception as e:
                print(f"  ⚠️  Error indexing email {msg['id']}: {e}")
                stats["errors"] += 1
                continue

        # Batch index into ChromaDB
        if documents:
            print(f"\n🔄 Generating embeddings for {len(documents)} emails...")
            embeddings = self.embedder.encode(documents, show_progress_bar=True)

            print(f"💾 Storing in vector database...")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings.tolist()
            )

            # Update index state
            for msg_id in ids:
                self.index_state["indexed_emails"][msg_id] = datetime.now().isoformat()

            self.index_state["last_index_time"] = datetime.now().isoformat()
            self._save_index_state()

        return stats

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        sender_filter: Optional[str] = None,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across indexed emails

        Args:
            query: Natural language search query
            n_results: Number of results to return
            sender_filter: Optional sender email/name filter
            date_filter: Optional date filter

        Returns:
            List of matching emails with relevance scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode([query])[0]

        # Build metadata filter
        where_filter = {}
        if sender_filter:
            where_filter["sender"] = {"$contains": sender_filter}
        if date_filter:
            where_filter["date"] = {"$contains": date_filter}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        # Format results
        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "subject": results['metadatas'][0][i]['subject'],
                "sender": results['metadatas'][0][i]['sender'],
                "date": results['metadatas'][0][i]['date'],
                "relevance": 1 - results['distances'][0][i],  # Convert distance to similarity
                "preview": results['documents'][0][i][:200] + "...",
                "message_id": results['metadatas'][0][i]['message_id']
            })

        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            "total_indexed": len(self.index_state["indexed_emails"]),
            "last_index_time": self.index_state.get("last_index_time"),
            "collection_count": self.collection.count(),
            "db_path": self.db_path
        }


def main():
    """Demo Email RAG System"""
    print("🧠 Email RAG System - Semantic Email Search\n")

    try:
        # Initialize
        rag = EmailRAGSystem()

        # Show current stats
        print("📊 Current RAG Status:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"   • {key}: {value}")

        # Index inbox (limit for demo)
        print("\n" + "="*60)
        print("📥 Indexing Inbox Emails...")
        print("="*60)

        index_stats = rag.index_inbox(limit=50)  # Start with 50 for demo
        print(f"\n✅ Indexing Complete:")
        print(f"   • Total emails processed: {index_stats['total']}")
        print(f"   • Newly indexed: {index_stats['new']}")
        print(f"   • Already indexed (skipped): {index_stats['skipped']}")
        print(f"   • Errors: {index_stats['errors']}")

        # Demo search
        if index_stats['new'] > 0:
            print("\n" + "="*60)
            print("🔍 Demo: Semantic Search")
            print("="*60)

            # Example query
            query = "Claude AI usage"
            print(f"\nQuery: '{query}'")
            results = rag.semantic_search(query, n_results=3)

            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['subject'][:60]}")
                print(f"   From: {result['sender']}")
                print(f"   Relevance: {result['relevance']:.2%}")

        print("\n" + "="*60)
        print("✅ Email RAG System Operational!")
        print("💡 Try: rag.semantic_search('your query here')")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
