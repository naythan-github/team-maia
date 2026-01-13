#!/usr/bin/env python3
"""
Conversation RAG - Ollama Local Embeddings

Semantic search across saved conversations for knowledge retrieval.
Uses Ollama's nomic-embed-text for 100% local processing.

Author: Maia System
Created: 2025-10-09 (Phase 101 - Conversation Persistence)
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Optional dependency - graceful degradation for importability
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = Settings = None


def _check_chromadb_available():
    """Raise ImportError if chromadb is not installed."""
    if not CHROMADB_AVAILABLE:
        raise ImportError("chromadb required. Install with: pip3 install chromadb")


class ConversationRAG:
    """Conversation RAG with Ollama local embeddings"""

    def __init__(self, db_path: Optional[str] = None, embedding_model: str = "nomic-embed-text"):
        """Initialize with Ollama embeddings"""
        self.db_path = db_path or os.path.expanduser("~/.maia/conversation_rag")
        os.makedirs(self.db_path, exist_ok=True)

        self.embedding_model = embedding_model
        self.ollama_url = "http://localhost:11434"

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Saved conversations with Ollama embeddings"}
        )

        self.index_state_file = os.path.join(self.db_path, "index_state.json")
        self.index_state = self._load_index_state()

        print(f"✅ Conversation RAG initialized with {embedding_model}")

    def _load_index_state(self) -> Dict[str, Any]:
        """Load index state"""
        if os.path.exists(self.index_state_file):
            with open(self.index_state_file, 'r') as f:
                return json.load(f)
        return {
            "total_conversations": 0,
            "last_save_time": None,
            "conversations": {}
        }

    def _save_index_state(self):
        """Save index state"""
        with open(self.index_state_file, 'w') as f:
            json.dump(self.index_state, f, indent=2)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.embedding_model, "input": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]
        except Exception as e:
            print(f"⚠️  Embedding error: {e}")
            raise

    def save_conversation(
        self,
        topic: str,
        summary: str,
        key_decisions: List[str],
        tags: List[str],
        context: Optional[str] = None,
        action_items: Optional[List[str]] = None
    ) -> str:
        """
        Save a conversation to RAG

        Args:
            topic: Brief topic description
            summary: Full conversation summary
            key_decisions: List of key decisions/recommendations
            tags: Keywords for search
            context: Additional context
            action_items: Optional action items

        Returns:
            conversation_id: Unique ID for saved conversation
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Construct searchable document
        doc_text = f"""Topic: {topic}

Summary: {summary}

Key Decisions:
{chr(10).join(f"- {d}" for d in key_decisions)}

Tags: {', '.join(tags)}
"""

        if action_items:
            doc_text += f"\nAction Items:\n{chr(10).join(f'- {a}' for a in action_items)}"

        if context:
            doc_text += f"\n\nAdditional Context: {context}"

        try:
            print(f"💾 Saving conversation: {topic[:50]}...")

            # Get embedding
            embedding = self._get_embedding(doc_text)

            # Store in ChromaDB
            metadata = {
                "conversation_id": conversation_id,
                "topic": topic[:500],
                "timestamp": timestamp,
                "tags": json.dumps(tags),
                "key_decisions_count": len(key_decisions),
                "date": timestamp[:10]
            }

            self.collection.add(
                documents=[doc_text],
                metadatas=[metadata],
                ids=[conversation_id],
                embeddings=[embedding]
            )

            # Update index state
            self.index_state["conversations"][conversation_id] = {
                "topic": topic,
                "timestamp": timestamp,
                "tags": tags
            }
            self.index_state["total_conversations"] = len(self.index_state["conversations"])
            self.index_state["last_save_time"] = timestamp
            self._save_index_state()

            print(f"✅ Conversation saved successfully!")
            print(f"   ID: {conversation_id}")
            print(f"   Tags: {', '.join(tags)}")

            return conversation_id

        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            raise

    def search(
        self,
        query: str,
        limit: int = 5,
        tags_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for conversations

        Args:
            query: Natural language search query
            limit: Maximum results to return
            tags_filter: Optional tag filtering

        Returns:
            List of matching conversations with relevance scores
        """
        try:
            print(f"\n🔍 Searching conversations: '{query}'")

            # Get query embedding
            query_embedding = self._get_embedding(query)

            # Build filter if tags provided
            where_filter = None
            if tags_filter:
                # ChromaDB where filter - check if ANY tag matches
                where_filter = {
                    "$or": [
                        {"tags": {"$contains": tag}} for tag in tags_filter
                    ]
                }

            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter if tags_filter else None
            )

            if not results['ids'] or not results['ids'][0]:
                print("No results found")
                return []

            # Format results
            conversations = []
            for i, conv_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                document = results['documents'][0][i]
                distance = results['distances'][0][i]

                # Calculate relevance (1 - distance, as lower distance = more similar)
                relevance = max(0, 1 - distance)

                conversations.append({
                    "conversation_id": conv_id,
                    "topic": metadata.get("topic", "Untitled"),
                    "timestamp": metadata.get("timestamp", "Unknown"),
                    "date": metadata.get("date", "Unknown"),
                    "tags": json.loads(metadata.get("tags", "[]")),
                    "relevance": relevance,
                    "preview": document[:300],
                    "full_content": document
                })

            print(f"\n📊 Found {len(conversations)} conversation(s)\n")

            return conversations

        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get full conversation by ID"""
        try:
            result = self.collection.get(ids=[conversation_id])

            if not result['ids']:
                return None

            metadata = result['metadatas'][0]
            document = result['documents'][0]

            return {
                "conversation_id": conversation_id,
                "topic": metadata.get("topic", "Untitled"),
                "timestamp": metadata.get("timestamp", "Unknown"),
                "tags": json.loads(metadata.get("tags", "[]")),
                "content": document
            }

        except Exception as e:
            print(f"❌ Error retrieving conversation: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation RAG statistics"""
        return {
            "total_conversations": self.index_state.get("total_conversations", 0),
            "last_save_time": self.index_state.get("last_save_time"),
            "storage_path": self.db_path,
            "embedding_model": self.embedding_model
        }

    def list_recent(self, limit: int = 10) -> List[Dict[str, str]]:
        """List recent conversations"""
        conversations = self.index_state.get("conversations", {})

        recent = sorted(
            conversations.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )[:limit]

        return [
            {
                "conversation_id": conv_id,
                "topic": conv_data["topic"],
                "timestamp": conv_data["timestamp"],
                "tags": conv_data["tags"]
            }
            for conv_id, conv_data in recent
        ]


def main():
    """CLI interface for conversation RAG"""
    import argparse

    parser = argparse.ArgumentParser(description="Conversation RAG - Semantic Search")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--save", action="store_true", help="Interactive save conversation")
    parser.add_argument("--stats", action="store_true", help="Show RAG statistics")
    parser.add_argument("--list", action="store_true", help="List recent conversations")
    parser.add_argument("--get", help="Get conversation by ID")
    parser.add_argument("--tags", help="Filter by tags (comma-separated)")

    args = parser.parse_args()

    rag = ConversationRAG()

    if args.stats:
        stats = rag.get_stats()
        print("\n📊 Conversation RAG Statistics")
        print(f"   Total Conversations: {stats['total_conversations']}")
        print(f"   Last Save: {stats['last_save_time'] or 'Never'}")
        print(f"   Storage: {stats['storage_path']}")
        print(f"   Embedding Model: {stats['embedding_model']}\n")

    elif args.list:
        recent = rag.list_recent()
        print("\n📚 Recent Conversations\n")
        for conv in recent:
            print(f"   {conv['timestamp'][:10]} - {conv['topic']}")
            print(f"   ID: {conv['conversation_id']}")
            print(f"   Tags: {', '.join(conv['tags'])}\n")

    elif args.get:
        conv = rag.get_conversation(args.get)
        if conv:
            print(f"\n📄 Conversation: {conv['topic']}\n")
            print(f"Timestamp: {conv['timestamp']}")
            print(f"Tags: {', '.join(conv['tags'])}\n")
            print(conv['content'])
        else:
            print(f"❌ Conversation {args.get} not found")

    elif args.query:
        tags_filter = args.tags.split(",") if args.tags else None
        results = rag.search(args.query, tags_filter=tags_filter)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['topic']}")
            print(f"   Relevance: {result['relevance']:.1%} | Date: {result['date']}")
            print(f"   Tags: {', '.join(result['tags'])}")
            print(f"   Preview: {result['preview'][:150]}...\n")

    elif args.save:
        print("\n💾 Save Conversation (Interactive)\n")
        topic = input("Topic: ")
        summary = input("Summary: ")
        decisions = input("Key Decisions (comma-separated): ").split(",")
        tags = input("Tags (comma-separated): ").split(",")
        context = input("Additional Context (optional): ")

        conv_id = rag.save_conversation(
            topic=topic.strip(),
            summary=summary.strip(),
            key_decisions=[d.strip() for d in decisions if d.strip()],
            tags=[t.strip() for t in tags if t.strip()],
            context=context.strip() if context else None
        )

        print(f"\n✅ Saved as: {conv_id}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
