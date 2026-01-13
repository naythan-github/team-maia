#!/usr/bin/env python3
"""
Meeting Transcript Search - Semantic Search Across All Meeting Transcripts

Search meeting transcripts using RAG semantic search with natural language queries.

Usage:
    # Search all meetings
    python3 claude/tools/search_meeting_transcripts.py "database migration strategy"

    # Search specific meeting
    python3 claude/tools/search_meeting_transcripts.py "Q4 priorities" --meeting-id 20251029_154500

    # Limit results
    python3 claude/tools/search_meeting_transcripts.py "action items" --limit 3

    # JSON output for programmatic use
    python3 claude/tools/search_meeting_transcripts.py "technical debt" --json

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-10-29
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Optional dependency - graceful degradation for importability
try:
    from claude.tools.whisper_meeting_transcriber import MeetingTranscriptionRAG
    TRANSCRIBER_AVAILABLE = True
except ImportError:
    TRANSCRIBER_AVAILABLE = False
    MeetingTranscriptionRAG = None


def _check_transcriber_available():
    """Raise ImportError if whisper_meeting_transcriber is not available."""
    if not TRANSCRIBER_AVAILABLE:
        raise ImportError("MeetingTranscriptionRAG not available. Ensure whisper_meeting_transcriber.py exists")


def format_result(result: Dict[str, Any], index: int) -> str:
    """Format search result for display"""
    metadata = result['metadatas'][0]
    document = result['documents'][0]

    output = []
    output.append(f"\n{'─' * 80}")
    output.append(f"Result #{index + 1}")
    output.append(f"{'─' * 80}")
    output.append(f"Meeting: {metadata.get('meeting_id', 'Unknown')}")
    output.append(f"Date: {metadata.get('date', 'Unknown')}")
    output.append(f"Time: {metadata.get('time', 'Unknown')}")
    output.append(f"Chunk: {metadata.get('chunk_number', 'Unknown')}")

    if 'title' in metadata:
        output.append(f"Title: {metadata['title']}")

    output.append(f"\nTranscript:")
    output.append(f"{document[:500]}{'...' if len(document) > 500 else ''}")
    output.append("")

    return "\n".join(output)


def search_transcripts(query: str, meeting_id: str = None, limit: int = 5,
                      json_output: bool = False) -> int:
    """
    Search meeting transcripts

    Args:
        query: Search query
        meeting_id: Optional meeting ID filter
        limit: Number of results
        json_output: Output as JSON

    Returns:
        Exit code
    """
    try:
        # Initialize RAG
        rag = MeetingTranscriptionRAG()

        if not rag.enabled:
            print("❌ RAG system not available")
            print("   Install dependencies: pip3 install chromadb sentence-transformers")
            return 1

        # Search
        results = rag.search(query, n_results=limit, meeting_id=meeting_id)

        if not results or not results.get('documents'):
            print(f"No results found for: {query}")
            return 1

        # Output results
        if json_output:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n🔍 Search Results for: '{query}'")
            print(f"Found {len(results['documents'][0])} results\n")

            for i in range(len(results['documents'][0])):
                result = {
                    'documents': [results['documents'][0][i]],
                    'metadatas': [results['metadatas'][0][i]]
                }
                print(format_result(result, i))

            print(f"{'─' * 80}\n")

        return 0

    except Exception as e:
        print(f"❌ Search failed: {e}")
        return 1


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Search meeting transcripts using semantic search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search all meetings
  %(prog)s "database migration strategy"

  # Search specific meeting
  %(prog)s "Q4 priorities" --meeting-id 20251029_154500

  # Limit results
  %(prog)s "action items" --limit 3

  # JSON output
  %(prog)s "technical debt" --json
        """
    )

    parser.add_argument(
        'query',
        help='Search query (natural language)'
    )
    parser.add_argument(
        '--meeting-id',
        help='Filter by specific meeting ID'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Maximum number of results (default: 5)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    return search_transcripts(
        query=args.query,
        meeting_id=args.meeting_id,
        limit=args.limit,
        json_output=args.json
    )


if __name__ == "__main__":
    sys.exit(main())
