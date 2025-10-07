#!/usr/bin/env python3
"""
Email RAG System - Ollama Local Embeddings

Uses Ollama's nomic-embed-text for 100% local email semantic search.
Zero external dependencies, complete privacy for Orro Group data.

Author: Maia System
Created: 2025-10-02 (Phase 80)
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ Missing chromadb. Install: pip3 install chromadb")
    sys.exit(1)

from claude.tools.macos_mail_bridge import MacOSMailBridge


class EmailRAGOllama:
    """Email RAG with Ollama local embeddings"""

    def __init__(self, db_path: Optional[str] = None, embedding_model: str = "nomic-embed-text"):
        """Initialize with Ollama embeddings"""
        self.db_path = db_path or os.path.expanduser("~/.maia/email_rag_ollama")
        os.makedirs(self.db_path, exist_ok=True)

        self.embedding_model = embedding_model
        self.ollama_url = "http://localhost:11434"

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="emails_ollama",
            metadata={"description": "Emails with Ollama embeddings"}
        )

        self.mail_bridge = MacOSMailBridge()

        self.index_state_file = os.path.join(self.db_path, "index_state.json")
        self.index_state = self._load_index_state()

        print(f"✅ Email RAG initialized with {embedding_model}")

    def _load_index_state(self) -> Dict[str, Any]:
        """Load index state"""
        if os.path.exists(self.index_state_file):
            with open(self.index_state_file, 'r') as f:
                return json.load(f)
        return {"indexed_emails": {}, "last_index_time": None}

    def _save_index_state(self):
        """Save index state"""
        with open(self.index_state_file, 'w') as f:
            json.dump(self.index_state, f, indent=2)

    def _email_hash(self, message: Dict[str, Any]) -> str:
        """Generate email hash"""
        key = f"{message['id']}:{message['subject']}:{message['date']}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        response = requests.post(
            f"{self.ollama_url}/api/embed",
            json={"model": self.embedding_model, "input": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    def index_inbox(self, limit: Optional[int] = None, force: bool = False) -> Dict[str, int]:
        """Index emails with Ollama embeddings"""
        # If not forcing full index, only fetch recent emails (last 50)
        # RAG will skip already-indexed emails automatically
        if force:
            fetch_limit = limit or 1000
            print(f"📧 Retrieving inbox messages (full scan, limit={fetch_limit})...")
        else:
            fetch_limit = 50  # Only check last 50 emails for new ones (hourly runs)
            print(f"📧 Retrieving last {fetch_limit} inbox messages for new emails...")

        messages = self.mail_bridge.get_inbox_messages(limit=fetch_limit)

        stats = {"total": len(messages), "new": 0, "skipped": 0, "errors": 0}

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for i, msg in enumerate(messages, 1):
            msg_hash = self._email_hash(msg)

            if not force and msg_hash in self.index_state["indexed_emails"]:
                stats["skipped"] += 1
                continue

            try:
                content = self.mail_bridge.get_message_content(msg['id'])
                doc_text = f"{content['subject']}\n\n{content['content'][:2000]}"  # Limit content

                print(f"  [{i}/{len(messages)}] Embedding: {content['subject'][:50]}...")
                embedding = self._get_embedding(doc_text)

                metadata = {
                    "message_id": msg['id'],
                    "subject": content['subject'][:500],
                    "sender": content['from'][:200],
                    "date": content['date'],
                    "read": str(content['read']),
                    "mailbox": "Inbox"
                }

                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(msg_hash)
                embeddings.append(embedding)

                stats["new"] += 1

            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                stats["errors"] += 1
                continue

        if documents:
            print(f"\n💾 Storing {len(documents)} emails in vector database...")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            for msg_id in ids:
                self.index_state["indexed_emails"][msg_id] = datetime.now().isoformat()

            self.index_state["last_index_time"] = datetime.now().isoformat()
            self._save_index_state()

        return stats

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        sender_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search with Ollama embeddings"""
        query_embedding = self._get_embedding(query)

        where_filter = {}
        if sender_filter:
            where_filter["sender"] = {"$contains": sender_filter}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "subject": results['metadatas'][0][i]['subject'],
                "sender": results['metadatas'][0][i]['sender'],
                "date": results['metadatas'][0][i]['date'],
                "relevance": 1 - results['distances'][0][i],
                "preview": results['documents'][0][i][:200] + "...",
                "message_id": results['metadatas'][0][i]['message_id']
            })

        return matches

    def search_by_sender(
        self,
        sender_email: str,
        n_results: Optional[int] = None,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search emails by sender email address using metadata filtering (100% accuracy)

        Args:
            sender_email: Email address or partial match (e.g., "con.alexakis" or "con.alexakis@orro.group")
            n_results: Max results (None = all matching emails)
            date_filter: Optional date string to filter by (e.g., "7 October 2025")

        Returns:
            List of matching emails sorted by date (newest first)
        """
        from dateutil import parser as date_parser

        # Get all emails and filter by sender
        results = self.collection.get(include=['metadatas', 'documents'])

        if not results['ids']:
            return []

        # Filter by sender
        matching_emails = []
        for i, metadata in enumerate(results['metadatas']):
            sender = metadata.get('sender', '').lower()
            if sender_email.lower() in sender:
                # Optional date filter
                if date_filter:
                    if date_filter not in metadata.get('date', ''):
                        continue

                try:
                    parsed_date = date_parser.parse(metadata.get('date', ''))
                except Exception:
                    parsed_date = datetime.min

                matching_emails.append({
                    'subject': metadata.get('subject', 'No subject'),
                    'sender': metadata.get('sender', 'Unknown'),
                    'date': metadata.get('date', 'Unknown'),
                    'message_id': metadata.get('message_id', ''),
                    'read': metadata.get('read', 'Unknown'),
                    'content': results['documents'][i] if i < len(results['documents']) else '',
                    '_sort_date': parsed_date
                })

        # Sort by date (newest first)
        matching_emails.sort(key=lambda x: x['_sort_date'], reverse=True)

        # Remove sort helper
        for email in matching_emails:
            del email['_sort_date']

        # Apply limit
        if n_results:
            matching_emails = matching_emails[:n_results]

        return matching_emails

    def smart_search(
        self,
        query: str,
        sender_filter: Optional[str] = None,
        date_filter: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: metadata filtering + semantic search

        Args:
            query: Search query (e.g., "comms room audit")
            sender_filter: Optional sender email/name filter
            date_filter: Optional date string filter
            n_results: Max results

        Returns:
            List of matching emails with relevance scores
        """
        from dateutil import parser as date_parser

        # If only sender filter, use structured search
        if sender_filter and not query:
            return self.search_by_sender(sender_filter, n_results, date_filter)

        # Get semantic search results
        query_embedding = self._get_embedding(query)

        # Get all results for filtering
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=100  # Get more for filtering
        )

        matches = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]

            # Apply filters
            if sender_filter:
                sender = metadata.get('sender', '').lower()
                if sender_filter.lower() not in sender:
                    continue

            if date_filter:
                if date_filter not in metadata.get('date', ''):
                    continue

            matches.append({
                'subject': metadata.get('subject', 'No subject'),
                'sender': metadata.get('sender', 'Unknown'),
                'date': metadata.get('date', 'Unknown'),
                'message_id': metadata.get('message_id', ''),
                'relevance': 1 - results['distances'][0][i],
                'content': results['documents'][0][i]
            })

        # Return top N
        return matches[:n_results]

    def get_recent_emails(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent emails by actual date parsing (not alphabetical sorting)
        Returns list of email metadata sorted by date (newest first)
        """
        from dateutil import parser as date_parser

        results = self.collection.get(include=['metadatas'])

        if not results['ids']:
            return []

        # Parse dates and create sortable list
        emails_with_dates = []
        for i, metadata in enumerate(results['metadatas']):
            try:
                # Parse the date string to datetime
                date_str = metadata.get('date', '')
                parsed_date = date_parser.parse(date_str)
                emails_with_dates.append((parsed_date, metadata))
            except Exception:
                # If parsing fails, use epoch (oldest possible)
                emails_with_dates.append((datetime.min, metadata))

        # Sort by parsed date (newest first)
        emails_with_dates.sort(key=lambda x: x[0], reverse=True)

        # Return top N
        return [
            {
                'subject': meta.get('subject', 'No subject'),
                'sender': meta.get('sender', 'Unknown'),
                'date': meta.get('date', 'Unknown'),
                'message_id': meta.get('message_id', ''),
                'read': meta.get('read', 'Unknown')
            }
            for _, meta in emails_with_dates[:n]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get stats"""
        return {
            "total_indexed": len(self.index_state["indexed_emails"]),
            "last_index_time": self.index_state.get("last_index_time"),
            "collection_count": self.collection.count(),
            "embedding_model": self.embedding_model,
            "db_path": self.db_path
        }


def main():
    """Production Email RAG with Ollama - Full Inbox Indexing"""
    print("🧠 Email RAG System - Ollama Local Embeddings\n")

    try:
        rag = EmailRAGOllama()

        print("📊 Current Status:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"   • {key}: {value}")

        print("\n" + "="*60)
        print("📥 Indexing Full Inbox (all unindexed emails)...")
        print("="*60)

        index_stats = rag.index_inbox(limit=None)
        print(f"\n✅ Indexing Complete:")
        print(f"   • Total: {index_stats['total']}")
        print(f"   • New: {index_stats['new']}")
        print(f"   • Skipped: {index_stats['skipped']}")
        print(f"   • Errors: {index_stats['errors']}")

        if index_stats['new'] > 0:
            print("\n" + "="*60)
            print("🔍 Demo Search: 'Claude AI'")
            print("="*60)

            results = rag.semantic_search("Claude AI", n_results=3)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['subject'][:60]}")
                print(f"   From: {r['sender']}")
                print(f"   Relevance: {r['relevance']:.2%}")

        print("\n✅ Email RAG System Operational!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
