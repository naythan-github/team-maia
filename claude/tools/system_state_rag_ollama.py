#!/usr/bin/env python3
"""
System State RAG - Ollama Local Embeddings

Semantic search across SYSTEM_STATE.md phases for institutional memory retrieval.
Uses Ollama's nomic-embed-text for 100% local processing.

Author: Maia System
Created: 2025-10-03 (Phase 84)
"""

import os
import sys
import re
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


class SystemStateRAGOllama:
    """System State RAG with Ollama local embeddings"""

    def __init__(self, db_path: Optional[str] = None, embedding_model: str = "nomic-embed-text",
                 system_state_path: Optional[str] = None):
        """Initialize with Ollama embeddings"""
        self.db_path = db_path or os.path.expanduser("~/.maia/system_state_rag")
        os.makedirs(self.db_path, exist_ok=True)

        self.embedding_model = embedding_model
        self.ollama_url = "http://localhost:11434"

        self.system_state_path = system_state_path or os.path.join(MAIA_ROOT, "SYSTEM_STATE.md")

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="system_state_phases",
            metadata={"description": "SYSTEM_STATE.md phases with Ollama embeddings"}
        )

        self.index_state_file = os.path.join(self.db_path, "index_state.json")
        self.index_state = self._load_index_state()

        print(f"✅ System State RAG initialized with {embedding_model}")

    def _load_index_state(self) -> Dict[str, Any]:
        """Load index state"""
        if os.path.exists(self.index_state_file):
            with open(self.index_state_file, 'r') as f:
                return json.load(f)
        return {"indexed_phases": {}, "last_index_time": None}

    def _save_index_state(self):
        """Save index state"""
        with open(self.index_state_file, 'w') as f:
            json.dump(self.index_state, f, indent=2)

    def _phase_hash(self, phase: Dict[str, Any]) -> str:
        """Generate phase hash"""
        key = f"{phase.get('number', 'unknown')}:{phase.get('title', 'untitled')}:{phase.get('date', '')}"
        return hashlib.md5(key.encode()).hexdigest()

    def _parse_system_state(self) -> List[Dict[str, Any]]:
        """Parse SYSTEM_STATE.md into phases"""
        if not os.path.exists(self.system_state_path):
            return []

        with open(self.system_state_path, 'r', encoding='utf-8') as f:
            content = f.read()

        phases = []

        # Split by ### headers that contain "PHASE" (case insensitive)
        # Pattern matches: ### **Title** ⭐ **...PHASE XX...**
        phase_pattern = r'###\s+\*\*(.+?)\*\*[^\n]*?PHASE\s+(\d+[A-Z]?\.?\d*)[^\n]*?\n(.*?)(?=###\s+\*\*|$)'

        for match in re.finditer(phase_pattern, content, re.DOTALL | re.IGNORECASE):
            title = match.group(1).strip()
            phase_num = match.group(2).strip()
            phase_content = match.group(3).strip()

            # Extract date from header or default to current
            date = datetime.now().strftime('%Y-%m-%d')

            phases.append({
                'number': phase_num,
                'title': title,
                'content': phase_content[:5000],  # Limit content for embedding
                'date': date
            })

        return phases

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        response = requests.post(
            f"{self.ollama_url}/api/embed",
            json={"model": self.embedding_model, "input": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    def index_phases(self, force: bool = False) -> Dict[str, int]:
        """Index SYSTEM_STATE.md phases with Ollama embeddings"""
        print("📚 Parsing SYSTEM_STATE.md...")
        phases = self._parse_system_state()

        stats = {"total": len(phases), "new": 0, "skipped": 0, "errors": 0}

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for i, phase in enumerate(phases, 1):
            phase_hash = self._phase_hash(phase)

            if not force and phase_hash in self.index_state["indexed_phases"]:
                stats["skipped"] += 1
                continue

            try:
                doc_text = f"{phase['title']}\n\n{phase['content']}"

                print(f"  [{i}/{len(phases)}] Embedding Phase {phase['number']}: {phase['title'][:50]}...")
                embedding = self._get_embedding(doc_text)

                metadata = {
                    "phase_number": str(phase['number']),
                    "title": phase['title'][:500],
                    "date": phase['date'],
                    "content_preview": phase['content'][:200]
                }

                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(phase_hash)
                embeddings.append(embedding)

                stats["new"] += 1

            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                stats["errors"] += 1
                continue

        if documents:
            print(f"\n💾 Storing {len(documents)} phases in vector database...")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            for phase_id in ids:
                self.index_state["indexed_phases"][phase_id] = datetime.now().isoformat()

            self.index_state["last_index_time"] = datetime.now().isoformat()
            self._save_index_state()

        return stats

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        phase_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search across phases with Ollama embeddings"""
        query_embedding = self._get_embedding(query)

        where_filter = {}
        if phase_filter:
            where_filter["phase_number"] = {"$eq": phase_filter}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "phase": results['metadatas'][0][i]['phase_number'],
                "title": results['metadatas'][0][i]['title'],
                "date": results['metadatas'][0][i]['date'],
                "relevance": 1 - results['distances'][0][i],
                "preview": results['metadatas'][0][i]['content_preview'] + "..."
            })

        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Get stats"""
        return {
            "total_indexed": len(self.index_state["indexed_phases"]),
            "last_index_time": self.index_state.get("last_index_time"),
            "collection_count": self.collection.count(),
            "embedding_model": self.embedding_model,
            "db_path": self.db_path
        }


def main():
    """Demo System State RAG with Ollama"""
    print("🧠 System State RAG - Ollama Local Embeddings\n")

    try:
        rag = SystemStateRAGOllama()

        print("📊 Current Status:")
        stats = rag.get_stats()
        for key, value in stats.items():
            print(f"   • {key}: {value}")

        print("\n" + "="*60)
        print("📥 Indexing SYSTEM_STATE.md Phases...")
        print("="*60)

        index_stats = rag.index_phases()
        print(f"\n✅ Indexing Complete:")
        print(f"   • Total: {index_stats['total']}")
        print(f"   • New: {index_stats['new']}")
        print(f"   • Skipped: {index_stats['skipped']}")
        print(f"   • Errors: {index_stats['errors']}")

        if index_stats['total'] > 0:
            print("\n" + "="*60)
            print("🔍 Demo Search: 'email integration'")
            print("="*60)

            results = rag.semantic_search("email integration", n_results=3)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. Phase {r['phase']}: {r['title'][:60]}")
                print(f"   Date: {r['date']}")
                print(f"   Relevance: {r['relevance']:.2%}")
                print(f"   Preview: {r['preview'][:100]}")

        print("\n✅ System State RAG Operational!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
