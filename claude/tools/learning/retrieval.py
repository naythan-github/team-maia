#!/usr/bin/env python3
"""
Conversation Retrieval Tools
Phase 237: Pre-Compaction Learning Capture

Convenience API for retrieving archived conversations.
Wraps ConversationArchive system with user-friendly functions.

Author: Maia (Phase 237)
Created: 2026-01-06
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from claude.tools.learning.archive import get_archive


def get_conversation(
    context_id: str,
    before_timestamp: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve archived conversation for a context.

    Args:
        context_id: Claude context window ID
        before_timestamp: Get snapshot before this time (milliseconds, default: latest)

    Returns:
        {
            'snapshot_id': int,
            'context_id': str,
            'snapshot_timestamp': int,
            'messages': [...],  # Parsed JSONL
            'metadata': {...},
            'learnings': [...],
            'trigger_type': 'auto' | 'manual',
            'message_count': int,
            'token_estimate': int
        }
        Or None if not found

    Example:
        >>> conversation = get_conversation('context_123')
        >>> print(f"Found {conversation['message_count']} messages")
        >>> for msg in conversation['messages']:
        ...     print(msg['content'])
    """
    archive = get_archive()
    return archive.get_conversation(context_id, before_timestamp)


def search_conversations(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search archived conversations using full-text search.

    Args:
        query: Search keywords (supports FTS5 syntax)
        limit: Maximum results to return

    Returns:
        List of matching snapshots ordered by relevance

    Example:
        >>> results = search_conversations("database schema SQLite")
        >>> for result in results:
        ...     print(f"{result['context_id']}: {result['first_message']}")
    """
    archive = get_archive()
    return archive.search_conversations(query, limit)


def get_compaction_history(
    context_id: str
) -> List[Dict[str, Any]]:
    """
    Get timeline of compaction events for a context.

    Args:
        context_id: Claude context window ID

    Returns:
        List of compaction events ordered chronologically:
        [{
            'snapshot_id': int,
            'snapshot_timestamp': int,
            'trigger_type': 'auto' | 'manual',
            'message_count': int,
            'learning_count': int,
            'token_estimate': int
        }]

    Example:
        >>> history = get_compaction_history('context_123')
        >>> print(f"Total compactions: {len(history)}")
        >>> for event in history:
        ...     print(f"{event['snapshot_timestamp']}: {event['message_count']} messages")
    """
    archive = get_archive()
    return archive.get_compaction_history(context_id)


def export_conversation(
    context_id: str,
    format: str = 'markdown',
    output_path: Optional[Path] = None
) -> str:
    """
    Export archived conversation in human-readable format.

    Args:
        context_id: Claude context window ID
        format: Export format ('markdown', 'json', 'text')
        output_path: Optional file path to write to

    Returns:
        Formatted conversation string

    Formats:
        - markdown: GitHub-flavored markdown with headers
        - json: Pretty-printed JSON
        - text: Plain text transcript

    Example:
        >>> markdown = export_conversation('context_123', format='markdown')
        >>> with open('conversation.md', 'w') as f:
        ...     f.write(markdown)
    """
    conversation = get_conversation(context_id)

    if not conversation:
        return ""

    if format == 'markdown':
        output = _export_markdown(conversation)
    elif format == 'json':
        output = _export_json(conversation)
    elif format == 'text':
        output = _export_text(conversation)
    else:
        raise ValueError(f"Unsupported format: {format}")

    # Write to file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(output)

    return output


def get_conversation_stats(
    context_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get statistics about archived conversations.

    Args:
        context_id: Optional context to get stats for (default: global stats)

    Returns:
        {
            'total_snapshots': int,
            'total_messages': int,
            'total_learnings': int,
            'average_messages_per_snapshot': float,
            'compaction_frequency': {...},
            'top_tools': [...],
            'top_agents': [...]
        }

    Example:
        >>> stats = get_conversation_stats()
        >>> print(f"Total archived conversations: {stats['total_snapshots']}")
    """
    archive = get_archive()

    with archive._get_connection() as conn:
        if context_id:
            # Stats for specific context
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as snapshot_count,
                    SUM(message_count) as total_messages,
                    SUM(learning_count) as total_learnings,
                    AVG(message_count) as avg_messages
                FROM conversation_snapshots
                WHERE context_id = ?
            """, (context_id,))
            row = cursor.fetchone()

            return {
                'context_id': context_id,
                'total_snapshots': row['snapshot_count'],
                'total_messages': row['total_messages'] or 0,
                'total_learnings': row['total_learnings'] or 0,
                'average_messages_per_snapshot': row['avg_messages'] or 0.0
            }
        else:
            # Global stats
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as snapshot_count,
                    SUM(message_count) as total_messages,
                    SUM(learning_count) as total_learnings,
                    AVG(message_count) as avg_messages,
                    COUNT(DISTINCT context_id) as unique_contexts
                FROM conversation_snapshots
            """)
            row = cursor.fetchone()

            return {
                'total_snapshots': row['snapshot_count'],
                'total_messages': row['total_messages'] or 0,
                'total_learnings': row['total_learnings'] or 0,
                'average_messages_per_snapshot': row['avg_messages'] or 0.0,
                'unique_contexts': row['unique_contexts']
            }


def _export_markdown(conversation: Dict[str, Any]) -> str:
    """Export conversation as markdown."""
    lines = []

    # Header
    lines.append(f"# Conversation Snapshot: {conversation['context_id']}\n")
    lines.append(f"**Snapshot ID**: {conversation['snapshot_id']}  ")
    lines.append(f"**Timestamp**: {conversation['snapshot_timestamp']}  ")
    lines.append(f"**Messages**: {conversation['message_count']}  ")
    lines.append(f"**Learnings**: {conversation['learning_count']}  ")
    lines.append(f"**Trigger**: {conversation['trigger_type']}  \n")

    # Metadata
    if conversation.get('tool_usage_stats'):
        lines.append("## Tools Used\n")
        for tool, count in conversation['tool_usage_stats'].items():
            lines.append(f"- **{tool}**: {count}")
        lines.append("")

    # Messages
    lines.append("## Conversation\n")
    for msg in conversation['messages']:
        msg_type = msg.get('type', 'unknown')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', 'unknown')

        if msg_type == 'user_message':
            lines.append(f"### 👤 User ({timestamp})\n")
            lines.append(f"{content}\n")
        elif msg_type == 'assistant_message':
            lines.append(f"### 🤖 Assistant ({timestamp})\n")
            lines.append(f"{content}\n")
        elif msg_type in ['tool_use', 'tool_call']:
            tool = msg.get('tool', 'unknown')
            lines.append(f"### 🔧 Tool: {tool} ({timestamp})\n")
            lines.append(f"```\n{content}\n```\n")

    # Learnings
    if conversation.get('learning_ids') and len(conversation['learning_ids']) > 0:
        lines.append("## Learnings Captured\n")
        lines.append(f"Total learnings: {conversation['learning_count']}\n")
        lines.append(f"Learning IDs: {', '.join(conversation['learning_ids'])}\n")

    return '\n'.join(lines)


def _export_json(conversation: Dict[str, Any]) -> str:
    """Export conversation as pretty-printed JSON."""
    return json.dumps(conversation, indent=2, default=str)


def _export_text(conversation: Dict[str, Any]) -> str:
    """Export conversation as plain text."""
    lines = []

    lines.append(f"=== Conversation Snapshot: {conversation['context_id']} ===")
    lines.append(f"Snapshot ID: {conversation['snapshot_id']}")
    lines.append(f"Timestamp: {conversation['snapshot_timestamp']}")
    lines.append(f"Messages: {conversation['message_count']}")
    lines.append(f"Learnings: {conversation['learning_count']}")
    lines.append("")

    for msg in conversation['messages']:
        msg_type = msg.get('type', 'unknown')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', 'unknown')

        if msg_type == 'user_message':
            lines.append(f"[{timestamp}] USER: {content}")
        elif msg_type == 'assistant_message':
            lines.append(f"[{timestamp}] ASSISTANT: {content}")
        elif msg_type in ['tool_use', 'tool_call']:
            tool = msg.get('tool', 'unknown')
            lines.append(f"[{timestamp}] TOOL ({tool}): {content}")

        lines.append("")

    return '\n'.join(lines)
