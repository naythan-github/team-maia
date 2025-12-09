#!/usr/bin/env python3
"""
Session Memory Retriever - Context Loading Hook

Retrieves relevant past work for injection at session start.
Designed to be called during context loading protocol.

Usage:
    # In context loading:
    from claude.tools.memory.session_memory_retriever import get_session_memory
    memory_context = get_session_memory("user's current query or problem")

    # CLI:
    python3 session_memory_retriever.py "database optimization"

Author: SRE Principal Engineer Agent
Created: 2025-12-08
"""

import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_session_memory(
    query: str,
    max_results: int = 3,
    min_relevance: float = 0.3
) -> str:
    """
    Get relevant past work memory for session-start injection.

    This is the main entry point for the context loading protocol.
    Gracefully returns empty string on any failure.

    Args:
        query: Current session's problem/question/context
        max_results: Maximum past journeys to include (default: 3)
        min_relevance: Minimum relevance threshold (default: 0.3)

    Returns:
        Formatted markdown string with relevant past work,
        or empty string if none found or on error.

    Example output:
        ## Relevant Past Work

        ### [Dec 05] API performance optimization
        - **Agent**: SRE Principal Engineer
        - **Learning**: Connection pooling reduced latency by 40%
        - **Relevance**: 85%
    """
    if not query or not query.strip():
        return ""

    try:
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG

        rag = ConversationMemoryRAG()
        return rag.get_memory_context(
            current_query=query,
            max_results=max_results,
            min_relevance=min_relevance
        )

    except ImportError as e:
        logger.debug(f"Memory RAG not available: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Session memory retrieval failed (non-blocking): {e}")
        return ""


def get_memory_stats() -> dict:
    """
    Get memory system statistics.

    Returns:
        Dict with memory system stats, or empty dict on error.
    """
    try:
        from claude.tools.memory.conversation_memory_rag import ConversationMemoryRAG
        rag = ConversationMemoryRAG()
        return rag.get_stats()
    except Exception:
        return {}


def main():
    """CLI interface for testing memory retrieval."""
    if len(sys.argv) < 2:
        print("Session Memory Retriever")
        print("=" * 40)
        print("\nUsage: session_memory_retriever.py <query>")
        print("\nExample:")
        print("  python3 session_memory_retriever.py 'database optimization'")
        print("\nStats:")
        stats = get_memory_stats()
        if stats:
            for k, v in stats.items():
                print(f"  {k}: {v}")
        else:
            print("  Memory system not initialized")
        return 0

    query = " ".join(sys.argv[1:])
    print(f"🔍 Retrieving memory for: {query}\n")

    context = get_session_memory(query)

    if context:
        print(context)
    else:
        print("No relevant past work found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
