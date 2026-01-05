#!/usr/bin/env python3
"""
Context Injection Module

Phase 234: Auto-inject relevant prior sessions on session start.

Provides helper functions for retrieving relevant learning context
to inject into new sessions.
"""

from typing import Optional


def get_learning_context(query: str, limit: int = 3) -> str:
    """
    Get relevant learning context for a query.

    Searches Maia Memory for prior sessions related to the query
    and returns formatted context for injection.

    Args:
        query: The current query/task description
        limit: Maximum number of prior sessions to include

    Returns:
        Formatted context string, or empty string if no matches/errors
    """
    try:
        from claude.tools.learning.memory import get_memory

        memory = get_memory()
        return memory.get_context_for_query(query, limit)
    except Exception:
        # Graceful degradation - never fail, just return empty
        return ""


def inject_context_on_session_start(
    context_id: str,
    initial_query: str,
    agent_used: Optional[str] = None
) -> str:
    """
    Inject relevant prior session context when starting a new session.

    Called from swarm_auto_loader during session initialization.

    Args:
        context_id: Current context/window ID (reserved for future agent-specific filtering)
        initial_query: The user's initial query
        agent_used: The agent being loaded (reserved for future agent-specific filtering)

    Returns:
        Context string to prepend to session, or empty string

    Note:
        context_id and agent_used are currently unused but kept for API
        consistency with swarm_auto_loader and future agent-specific context.
    """
    # Reserved for future use: agent-specific context filtering
    _ = context_id, agent_used

    try:
        # Get relevant prior sessions
        context = get_learning_context(initial_query)

        if not context:
            return ""

        # Format for injection
        return f"""
---
## Prior Session Context (from Maia Memory)
{context}
---

"""
    except Exception:
        return ""


__all__ = ["get_learning_context", "inject_context_on_session_start"]
