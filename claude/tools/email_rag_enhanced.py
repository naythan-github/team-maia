#!/usr/bin/env python3
"""
Enhanced Email RAG - GPU-Accelerated Semantic Analysis

Uses llama3.2:3b for intelligent email summarization + nomic-embed-text for embeddings.
Maximum quality semantic search leveraging available GPU resources.

Pipeline:
1. Extract email content
2. llama3.2:3b generates semantic summary (key topics, people, actions, context)
3. Embed summary + original content with nomic-embed-text
4. Store in ChromaDB with rich metadata

Author: Maia System
Created: 2025-10-02 (Phase 80 - Enhanced)
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


class EnhancedEmailRAG:
    """GPU-accelerated email RAG with LLM semantic analysis"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.expanduser("~/.maia/email_rag_enhanced")
        os.makedirs(self.db_path, exist_ok=True)

        self.ollama_url = "http://localhost:11434"
        self.analysis_model = "llama3.2:3b"  # GPU-accelerated semantic analysis
        self.embedding_model = "nomic-embed-text"  # Fast embeddings

        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="emails_enhanced",
            metadata={"description": "Emails with LLM semantic analysis"}
        )

        self.mail_bridge = MacOSMailBridge()
        self.index_state_file = os.path.join(self.db_path, "index_state.json")
        self.index_state = self._load_index_state()

        print(f"✅ Enhanced Email RAG initialized")
        print(f"   Analysis: {self.analysis_model} (GPU-accelerated)")
        print(f"   Embeddings: {self.embedding_model}")

    def _load_index_state(self) -> Dict[str, Any]:
        if os.path.exists(self.index_state_file):
            with open(self.index_state_file, 'r') as f:
                return json.load(f)
        return {"indexed_emails": {}, "last_index_time": None}

    def _save_index_state(self):
        with open(self.index_state_file, 'w') as f:
            json.dump(self.index_state, f, indent=2)

    def _email_hash(self, message: Dict[str, Any]) -> str:
        key = f"{message['id']}:{message['subject']}:{message['date']}"
        return hashlib.md5(key.encode()).hexdigest()

    def _analyze_email_semantics(self, subject: str, content: str, sender: str) -> str:
        """Use llama3.2:3b to extract semantic meaning"""
        prompt = f"""Analyze this email and extract key semantic information in 2-3 concise sentences:

Subject: {subject}
From: {sender}
Content: {content[:1500]}

Extract: main topics, key people/organizations mentioned, action items, and context. Be specific and concrete."""

        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={"model": self.analysis_model, "prompt": prompt, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from nomic-embed-text"""
        response = requests.post(
            f"{self.ollama_url}/api/embed",
            json={"model": self.embedding_model, "input": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    def index_inbox(self, limit: Optional[int] = None, force: bool = False) -> Dict[str, int]:
        """Index emails with GPU-accelerated semantic analysis"""
        print("📧 Retrieving inbox messages...")
        messages = self.mail_bridge.get_inbox_messages(limit=limit or 1000)

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

                print(f"  [{i}/{len(messages)}] 🧠 Analyzing: {content['subject'][:50]}...")

                # GPU-accelerated semantic analysis
                semantic_summary = self._analyze_email_semantics(
                    content['subject'],
                    content['content'][:2000],
                    content['from']
                )

                # Combine for embedding: original + AI summary
                doc_text = f"{content['subject']}\n\n{semantic_summary}\n\n{content['content'][:1000]}"

                print(f"      💡 Summary: {semantic_summary[:80]}...")
                print(f"      📊 Embedding...")

                embedding = self._get_embedding(doc_text)

                metadata = {
                    "message_id": msg['id'],
                    "subject": content['subject'][:500],
                    "sender": content['from'][:200],
                    "date": content['date'],
                    "read": str(content['read']),
                    "semantic_summary": semantic_summary[:500],
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

    def semantic_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Enhanced semantic search with AI summaries"""
        query_embedding = self._get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "subject": results['metadatas'][0][i]['subject'],
                "sender": results['metadatas'][0][i]['sender'],
                "date": results['metadatas'][0][i]['date'],
                "semantic_summary": results['metadatas'][0][i].get('semantic_summary', 'N/A'),
                "relevance": 1 - results['distances'][0][i],
                "message_id": results['metadatas'][0][i]['message_id']
            })

        return matches

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_indexed": len(self.index_state["indexed_emails"]),
            "last_index_time": self.index_state.get("last_index_time"),
            "collection_count": self.collection.count(),
            "analysis_model": self.analysis_model,
            "embedding_model": self.embedding_model,
            "db_path": self.db_path
        }


def main():
    print("🧠 Enhanced Email RAG - GPU-Accelerated Semantic Analysis\n")

    try:
        rag = EnhancedEmailRAG()

        print("📊 Current Status:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"   • {key}: {value}")

        print("\n" + "="*60)
        print("📥 Indexing with LLM Analysis (limit 10 for demo)...")
        print("="*60)

        index_stats = rag.index_inbox(limit=10)
        print(f"\n✅ Indexing Complete:")
        print(f"   • Total: {index_stats['total']}")
        print(f"   • New: {index_stats['new']}")
        print(f"   • Skipped: {index_stats['skipped']}")
        print(f"   • Errors: {index_stats['errors']}")

        if index_stats['new'] > 0:
            print("\n" + "="*60)
            print("🔍 Enhanced Search: 'cloud restructure'")
            print("="*60)

            results = rag.semantic_search("cloud restructure meetings", n_results=3)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['subject'][:60]}")
                print(f"   From: {r['sender'][:50]}")
                print(f"   📝 AI Summary: {r['semantic_summary']}")
                print(f"   Relevance: {r['relevance']:.2%}")

        print("\n✅ Enhanced Email RAG Operational!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
