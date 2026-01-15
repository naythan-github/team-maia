#!/usr/bin/env python3
"""
Prompt Export System

Sprint: SPRINT-002-PROMPT-CAPTURE

Exports session prompts for team sharing in multiple formats:
- JSONL (for import into other systems)
- Markdown (for documentation/wiki)
- CSV (for analysis)
"""

import csv
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, List, Any, Optional

from claude.tools.learning.memory import get_memory


def export_session_prompts(
    session_id: str,
    format: str = 'jsonl',
    output_path: Optional[Path] = None,
    include_metadata: bool = True
) -> str:
    """
    Export prompts for a single session.

    Args:
        session_id: Session to export
        format: 'jsonl', 'markdown', 'csv'
        output_path: Optional file path to write
        include_metadata: Include timestamp, char_count, etc.

    Returns:
        Formatted export string
    """
    memory = get_memory()
    prompts = memory.get_prompts_for_session(session_id)

    if format == 'jsonl':
        output = _export_jsonl(prompts, include_metadata)
    elif format == 'markdown':
        output = _export_markdown(session_id, prompts, include_metadata)
    elif format == 'csv':
        output = _export_csv(prompts, include_metadata)
    else:
        raise ValueError(f"Unsupported format: {format}")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)

    return output


def export_prompts_by_date_range(
    start_date: str,
    end_date: str,
    format: str = 'jsonl',
    output_path: Optional[Path] = None
) -> str:
    """
    Export all prompts within a date range.

    Args:
        start_date: ISO format start date
        end_date: ISO format end date
        format: Export format
        output_path: Optional output file

    Returns:
        Formatted export string
    """
    memory = get_memory()
    memory._ensure_prompts_initialized()

    conn = memory._get_conn()
    cursor = conn.execute("""
        SELECT * FROM session_prompts
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
    """, (start_date, end_date))

    prompts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if format == 'jsonl':
        output = _export_jsonl(prompts, include_metadata=True)
    elif format == 'markdown':
        output = _export_markdown_multi(prompts)
    elif format == 'csv':
        output = _export_csv(prompts, include_metadata=True)
    else:
        raise ValueError(f"Unsupported format: {format}")

    if output_path:
        Path(output_path).write_text(output)

    return output


def _export_jsonl(prompts: List[Dict], include_metadata: bool) -> str:
    """Export as JSON Lines format."""
    lines = []
    for p in prompts:
        if include_metadata:
            record = {
                'session_id': p['session_id'],
                'prompt_index': p['prompt_index'],
                'prompt_text': p['prompt_text'],
                'timestamp': p['timestamp'],
                'char_count': p['char_count'],
                'word_count': p['word_count'],
            }
        else:
            record = {
                'prompt_text': p['prompt_text'],
            }
        lines.append(json.dumps(record))
    return '\n'.join(lines)


def _export_markdown(session_id: str, prompts: List[Dict], include_metadata: bool) -> str:
    """Export as Markdown document."""
    lines = [
        f"# Session Prompts: {session_id}",
        "",
        f"**Total Prompts**: {len(prompts)}",
        f"**Exported**: {datetime.now().isoformat()}",
        "",
        "---",
        "",
    ]

    for p in prompts:
        lines.append(f"## Prompt {p['prompt_index'] + 1}")
        if include_metadata:
            lines.append(f"*{p['timestamp']} | {p['char_count']} chars | {p['word_count']} words*")
        lines.append("")
        lines.append("```")
        lines.append(p['prompt_text'])
        lines.append("```")
        lines.append("")

    return '\n'.join(lines)


def _export_markdown_multi(prompts: List[Dict]) -> str:
    """Export multiple sessions as Markdown."""
    lines = [
        "# Prompt Export",
        "",
        f"**Total Prompts**: {len(prompts)}",
        f"**Exported**: {datetime.now().isoformat()}",
        "",
    ]

    # Group by session
    sessions: Dict[str, List[Dict]] = {}
    for p in prompts:
        sid = p['session_id']
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(p)

    lines.append(f"**Sessions**: {len(sessions)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for session_id, session_prompts in sessions.items():
        lines.append(f"## Session: {session_id}")
        lines.append("")
        for p in session_prompts:
            lines.append(f"### Prompt {p['prompt_index'] + 1}")
            lines.append(f"*{p['timestamp']}*")
            lines.append("")
            lines.append("```")
            lines.append(p['prompt_text'])
            lines.append("```")
            lines.append("")

    return '\n'.join(lines)


def _export_csv(prompts: List[Dict], include_metadata: bool) -> str:
    """Export as CSV."""
    output = StringIO()

    if include_metadata:
        fieldnames = ['session_id', 'prompt_index', 'timestamp', 'char_count', 'word_count', 'prompt_text']
    else:
        fieldnames = ['prompt_text']

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(prompts)

    return output.getvalue()


__all__ = ['export_session_prompts', 'export_prompts_by_date_range']
