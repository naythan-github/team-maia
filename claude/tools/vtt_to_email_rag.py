#!/usr/bin/env python3
"""
VTT to Email RAG Integration
Index meeting summaries into email RAG for semantic search

Author: Maia Personal Assistant Agent
Phase: 86.2 - VTT Intelligence Pipeline
Date: 2025-10-03
"""

import os
import sys
from pathlib import Path
from typing import Dict
import logging
import hashlib

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.email_rag_ollama import EmailRAGOllama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VTTEmailRAGIntegration:
    """Integrate VTT summaries with Email RAG"""

    def __init__(self):
        """Initialize integration"""
        # Use separate collection for meeting summaries
        self.rag = EmailRAGOllama(
            db_path=os.path.expanduser("~/.maia/meeting_rag_ollama")
        )

        # Override collection to meeting-specific one
        self.rag.collection = self.rag.client.get_or_create_collection(
            name="meeting_summaries",
            metadata={"description": "VTT meeting summaries"}
        )

    def index_summary(self, summary_file: Path) -> Dict:
        """
        Index a VTT summary file into RAG

        Args:
            summary_file: Path to markdown summary

        Returns:
            Indexing results
        """
        logger.info(f"Indexing summary: {summary_file.name}")

        # Read summary
        with open(summary_file, 'r') as f:
            content = f.read()

        # Extract metadata from summary
        metadata = self._extract_metadata(content, summary_file)

        # Generate document hash
        doc_hash = hashlib.md5(f"{summary_file.name}:{content}".encode()).hexdigest()

        # Check if already indexed
        try:
            existing = self.rag.collection.get(ids=[doc_hash])
            if existing['ids']:
                logger.info(f"Summary already indexed: {summary_file.name}")
                return {"status": "skipped", "reason": "already_indexed"}
        except Exception:
            pass  # Collection query failed, proceed with indexing

        # Get embedding
        embedding = self.rag._get_embedding(content)

        # Add to collection
        self.rag.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_hash],
            embeddings=[embedding]
        )

        logger.info(f"✅ Indexed: {summary_file.name}")

        return {"status": "indexed", "doc_id": doc_hash}

    def _extract_metadata(self, content: str, summary_file: Path) -> Dict:
        """Extract metadata from summary content"""
        import re

        metadata = {
            "source": "vtt_summary",
            "file": str(summary_file),
            "indexed_at": str(Path(summary_file).stat().st_mtime)
        }

        # Extract meeting date
        date_match = re.search(r'\*\*Meeting Date\*\*:\s*([^\n]+)', content)
        if date_match:
            metadata["meeting_date"] = date_match.group(1).strip()

        # Extract participants
        participants_match = re.search(r'\*\*Participants\*\*:\s*([^\n]+)', content)
        if participants_match:
            metadata["participants"] = participants_match.group(1).strip()

        # Extract meeting type
        type_match = re.search(r'\*\*Meeting Type\*\*:\s*([^\n]+)', content)
        if type_match:
            metadata["meeting_type"] = type_match.group(1).strip()

        return metadata

    def search_meetings(self, query: str, n_results: int = 5) -> Dict:
        """
        Search meeting summaries semantically

        Args:
            query: Search query
            n_results: Number of results

        Returns:
            Search results
        """
        embedding = self.rag._get_embedding(query)

        results = self.rag.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "file": results['metadatas'][0][i].get('file', 'Unknown'),
                    "meeting_date": results['metadatas'][0][i].get('meeting_date', 'Unknown'),
                    "participants": results['metadatas'][0][i].get('participants', 'Unknown'),
                    "relevance": 1 - results['distances'][0][i],  # Convert distance to relevance
                    "excerpt": results['documents'][0][i][:200]
                })

        return {"query": query, "results": formatted_results}

    def index_all_summaries(self, summaries_dir: Path) -> Dict:
        """
        Index all VTT summaries in directory

        Args:
            summaries_dir: Directory containing summary markdown files

        Returns:
            Indexing results summary
        """
        results = {"indexed": 0, "skipped": 0, "errors": 0}

        summary_files = list(summaries_dir.glob("*.md"))
        logger.info(f"Found {len(summary_files)} summary files")

        for summary_file in summary_files:
            try:
                result = self.index_summary(summary_file)
                if result["status"] == "indexed":
                    results["indexed"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error(f"Failed to index {summary_file.name}: {e}")
                results["errors"] += 1

        return results


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="VTT to Email RAG Integration")
    parser.add_argument("command", choices=["index", "index-all", "search"],
                       help="Command to execute")
    parser.add_argument("--file", help="Summary file to index")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--results", type=int, default=5, help="Number of search results")

    args = parser.parse_args()

    integration = VTTEmailRAGIntegration()

    if args.command == "index":
        if not args.file:
            print("❌ Error: --file required")
            sys.exit(1)

        summary_file = Path(args.file)
        result = integration.index_summary(summary_file)
        print(f"\n✅ {result['status'].upper()}: {summary_file.name}")

    elif args.command == "index-all":
        summaries_dir = Path.home() / "git" / "maia" / "claude" / "data" / "transcript_summaries"
        print(f"\n🔄 Indexing all summaries from {summaries_dir}...")

        results = integration.index_all_summaries(summaries_dir)
        print(f"\n✅ Indexing Complete:")
        print(f"   • Indexed: {results['indexed']}")
        print(f"   • Skipped: {results['skipped']}")
        print(f"   • Errors: {results['errors']}")

    elif args.command == "search":
        if not args.query:
            print("❌ Error: --query required")
            sys.exit(1)

        print(f"\n🔍 Searching meetings for: '{args.query}'...\n")
        results = integration.search_meetings(args.query, n_results=args.results)

        for i, result in enumerate(results['results'], 1):
            print(f"{i}. {Path(result['file']).stem}")
            print(f"   Date: {result['meeting_date']}")
            print(f"   Participants: {result['participants']}")
            print(f"   Relevance: {result['relevance']:.1%}")
            print(f"   {result['excerpt']}...\n")


if __name__ == "__main__":
    main()
