"""
Interview Search System - Hybrid SQLite FTS5 + ChromaDB RAG

A unified system for ingesting, searching, and analyzing interview VTT transcripts.

Components:
- InterviewSearchSystem: Main hybrid search class
- InterviewVTTParser: VTT file parsing
- InterviewScorer: Scoring frameworks (50pt, 100pt, LLM)

Usage:
    from claude.tools.interview import InterviewSearchSystem

    system = InterviewSearchSystem()
    system.ingest("/path/to/interview.vtt", "John Smith", "Pod Lead")
    results = system.search("terraform experience", search_type="hybrid")

CLI:
    python3 -m claude.tools.interview.interview_cli ingest -f file.vtt -c "Name" -r "Role"
    python3 -m claude.tools.interview.interview_cli search -q "query"
    python3 -m claude.tools.interview.interview_cli ask -q "Which candidate..."

Created: 2025-12-15 (Phase 223)
Author: Maia System
"""

from .interview_vtt_parser import InterviewVTTParser
from .interview_search_system import InterviewSearchSystem

__all__ = [
    'InterviewSearchSystem',
    'InterviewVTTParser',
]

__version__ = '1.0.0'
