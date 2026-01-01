#!/usr/bin/env python3
"""
Context Pre-Injector - Automatic DB-First Context Loading
Phase 226: Solves "Claude ignores databases" problem

Prints relevant context summary to stdout, which appears
in Claude's context window as a system message.

This module is called by the user-prompt-submit hook on every prompt,
automatically injecting database query results so Claude doesn't have
to remember to query them manually.

Performance target: <100ms
Token target: 200-500 tokens (compact, relevant)

Usage:
    # From hook (bash):
    python3 context_pre_injector.py "$CLAUDE_USER_MESSAGE"

    # Programmatic:
    from context_pre_injector import inject_context
    inject_context("implement security feature")
"""

import sys
from pathlib import Path
from typing import List, Optional

# Maia root detection
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.absolute()

# Add SRE tools to path for SmartContextLoader
sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "sre"))

# Import SmartContextLoader with graceful fallback
try:
    from smart_context_loader import SmartContextLoader
    LOADER_AVAILABLE = True
except ImportError:
    LOADER_AVAILABLE = False
    SmartContextLoader = None


# Stopwords for keyword extraction
STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'and', 'but', 'if', 'or', 'because', 'until', 'while', 'although',
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
    'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
    'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
    'itself', 'they', 'them', 'their', 'theirs', 'themselves',
}

# Complexity indicators - words that suggest a complex task
COMPLEXITY_INDICATORS = {
    'implement', 'create', 'build', 'fix', 'debug', 'analyze', 'design',
    'architect', 'develop', 'refactor', 'optimize', 'migrate', 'integrate',
    'deploy', 'configure', 'troubleshoot', 'investigate', 'audit'
}


def extract_keywords(query: str) -> List[str]:
    """
    Extract searchable keywords from query.

    Filters stopwords and short words, returns max 3 keywords
    for focused capability search.

    Args:
        query: User's natural language query

    Returns:
        List of 0-3 meaningful keywords
    """
    if not query:
        return []

    # Tokenize and filter
    words = query.lower().split()
    keywords = [
        word.strip('.,!?;:()[]{}"\'-')
        for word in words
        if len(word) > 3 and word.lower() not in STOPWORDS
    ]

    # Return unique keywords, max 3
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
            if len(unique) >= 3:
                break

    return unique


def is_complex_query(query: str) -> bool:
    """
    Determine if query warrants phase loading.

    Complex queries (implement, create, build, etc.) benefit from
    historical phase context. Simple questions don't need it.

    Args:
        query: User's natural language query

    Returns:
        True if query is complex, False otherwise
    """
    if not query:
        return False

    query_lower = query.lower()
    return any(indicator in query_lower for indicator in COMPLEXITY_INDICATORS)


def inject_context(query: str) -> None:
    """
    Print relevant context for query to stdout.

    This is the main entry point. Output is captured by the
    user-prompt-submit hook and appears in Claude's context.

    Always succeeds - all failures are caught and handled gracefully.

    Args:
        query: User's natural language query (may be empty)
    """
    try:
        _inject_context_impl(query)
    except Exception:
        # Ultimate fallback - never fail
        _print_fallback_context()


def _inject_context_impl(query: str) -> None:
    """
    Implementation of context injection.

    Separated from inject_context() for cleaner error handling.
    """
    output = []
    output.append("─" * 50)
    output.append("📊 AUTO-INJECTED CONTEXT (DB-First)")
    output.append("─" * 50)

    # Load SmartContextLoader
    loader = None
    if LOADER_AVAILABLE:
        try:
            loader = SmartContextLoader(MAIA_ROOT)
        except Exception:
            pass

    # 1. Capability summary (always include)
    if loader:
        try:
            summary = loader.load_guaranteed_minimum()
            output.append(summary)
        except Exception:
            output.append("Capabilities: 200+ tools, 49+ agents available")
    else:
        output.append("Capabilities: 200+ tools, 49+ agents available")

    # 2. Query-relevant capabilities (if query has substance)
    keywords = extract_keywords(query)
    if keywords and loader:
        try:
            # Search for first keyword
            caps = loader.load_capability_context(query=keywords[0], limit=10)
            if caps and "No matching" not in caps and len(caps) > 50:
                output.append("")
                output.append("**Relevant Capabilities:**")
                # Truncate to keep tokens low
                if len(caps) > 800:
                    caps = caps[:800] + "\n..."
                output.append(caps)
        except Exception:
            pass  # Silent failure

    # 3. Query-relevant phases (if complex query)
    if is_complex_query(query) and loader:
        try:
            result = loader.load_for_intent(query, include_memory=False)
            if result and result.phases_loaded:
                phases_str = ", ".join(str(p) for p in result.phases_loaded[:5])
                output.append("")
                output.append(f"**Relevant Phases**: {phases_str}")
                output.append(f"*Strategy: {result.loading_strategy}*")
        except Exception:
            pass  # Silent failure

    output.append("─" * 50)

    # Print to stdout (hook captures this)
    print("\n".join(output))


def _print_fallback_context() -> None:
    """
    Print minimal fallback context when everything else fails.
    """
    output = [
        "─" * 50,
        "📊 AUTO-INJECTED CONTEXT",
        "─" * 50,
        "Maia AI assistant ready.",
        "Capabilities: 200+ tools, 49+ agents available.",
        "Use `python3 claude/tools/sre/capabilities_registry.py find <query>` for lookups.",
        "─" * 50,
    ]
    print("\n".join(output))


def main():
    """CLI entry point for hook integration."""
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    inject_context(query)
    # Always exit 0 - never block the hook
    sys.exit(0)


if __name__ == "__main__":
    main()
