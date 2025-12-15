#!/usr/bin/env python3
"""
Interview Search System CLI

Unified command-line interface for interview VTT analysis.

Commands:
    ingest    - Parse and index a VTT interview file
    search    - Search interviews (fts, semantic, or hybrid)
    ask       - Ask questions using RAG + LLM
    compare   - Compare multiple candidates
    analyze   - Score a single interview
    list      - List all indexed interviews
    stats     - Show system statistics

Usage:
    python3 interview_cli.py ingest -f interview.vtt -c "John Smith" -r "Pod Lead"
    python3 interview_cli.py search -q "terraform experience"
    python3 interview_cli.py ask -q "Which candidate has strongest Azure skills?"

Author: Maia System
Created: 2025-12-15 (Phase 223)
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.interview.interview_search_system import InterviewSearchSystem, SearchResult
from claude.tools.interview.interview_scoring import InterviewScorer


def format_table(headers: list, rows: list, max_width: int = 40) -> str:
    """Format data as ASCII table"""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)[:max_width]
            widths[i] = max(widths[i], len(cell_str))

    # Build table
    lines = []

    # Header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Rows
    for row in rows:
        row_line = " | ".join(str(c)[:max_width].ljust(widths[i]) for i, c in enumerate(row))
        lines.append(row_line)

    return "\n".join(lines)


def cmd_ingest(args, system: InterviewSearchSystem):
    """Ingest a VTT file"""
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    result = system.ingest(
        vtt_path=args.file,
        candidate_name=args.candidate,
        role_title=args.role,
        interview_date=args.date
    )

    print(f"\nIngestion complete")
    print(f"  Interview ID: {result['interview_id']}")
    print(f"  Candidate: {result['candidate_name']}")
    print(f"  Role: {result['role_title']}")
    print(f"  Segments: {result['total_segments']}")
    print(f"  Words: {result['total_words']}")

    if args.json:
        print(f"\nJSON:\n{json.dumps(result, indent=2)}")


def cmd_search(args, system: InterviewSearchSystem):
    """Search interviews"""
    results = system.search(
        query=args.query,
        search_type=args.type,
        n_results=args.limit,
        candidate_filter=args.candidate,
        role_filter=args.role
    )

    if not results:
        print(f"\nNo results found for: {args.query}")
        return

    print(f"\nFound {len(results)} results for: '{args.query}' (type: {args.type})")
    print("=" * 80)

    if args.json:
        output = [
            {
                'candidate': r.candidate_name,
                'role': r.role_title,
                'speaker': r.speaker,
                'text': r.text,
                'score': r.score
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r.candidate_name} - {r.role_title} (score: {r.score:.3f})")
            print(f"    Speaker: {r.speaker}")
            print(f"    {r.text[:200]}...")


def cmd_ask(args, system: InterviewSearchSystem):
    """Ask a question using RAG + LLM"""
    print(f"\nQuestion: {args.question}")
    print("Searching for relevant context...")

    result = system.ask(
        question=args.question,
        context_limit=args.context_limit,
        model=args.model
    )

    print(f"\nSources used: {result['context_used']}")
    print("=" * 80)
    print(f"\nAnswer:\n{result['answer']}")

    if args.json:
        print(f"\nJSON:\n{json.dumps(result, indent=2)}")


def cmd_compare(args, system: InterviewSearchSystem):
    """Compare multiple interviews"""
    result = system.compare(
        interview_ids=args.interviews,
        output_format=args.output
    )

    if not result['interviews']:
        print("No interviews found with provided IDs")
        return

    print(f"\nComparing {result['count']} interviews:")
    print("=" * 80)

    if args.output == 'json':
        print(json.dumps(result, indent=2))
    elif args.output == 'markdown':
        print("| Candidate | Role | Segments | Words | Score | Recommendation |")
        print("|-----------|------|----------|-------|-------|----------------|")
        for i in result['interviews']:
            print(f"| {i.get('candidate_name', 'N/A')} | {i.get('role_title', 'N/A')} | "
                  f"{i.get('total_segments', 0)} | {i.get('total_words', 0)} | "
                  f"{i.get('best_score', 'N/A')} | {i.get('recommendation', 'N/A')} |")
    else:  # table
        headers = ['Candidate', 'Role', 'Segments', 'Words', 'Score', 'Rec']
        rows = [
            [
                i.get('candidate_name', 'N/A'),
                i.get('role_title', 'N/A'),
                i.get('total_segments', 0),
                i.get('total_words', 0),
                i.get('best_score', 'N/A'),
                i.get('recommendation', 'N/A')
            ]
            for i in result['interviews']
        ]
        print(format_table(headers, rows))


def cmd_analyze(args, system: InterviewSearchSystem):
    """Analyze and score an interview"""
    # Get interview segments
    conn = system._get_connection()
    try:
        cursor = conn.execute("""
            SELECT i.candidate_name, i.role_title, s.speaker, s.text_content
            FROM interviews i
            JOIN interview_segments s ON i.interview_id = s.interview_id
            WHERE i.interview_id = ?
        """, (args.interview,))
        rows = cursor.fetchall()

        if not rows:
            print(f"Interview not found: {args.interview}")
            sys.exit(1)

        # Build dialogue dict
        dialogue = {}
        candidate_name = rows[0]['candidate_name']
        role_title = rows[0]['role_title']

        for row in rows:
            speaker = row['speaker']
            if speaker not in dialogue:
                dialogue[speaker] = []
            dialogue[speaker].append(row['text_content'])

    finally:
        conn.close()

    # Score
    scorer = InterviewScorer()
    result = scorer.score(dialogue, framework=args.framework)

    print(f"\nInterview Analysis: {candidate_name} - {role_title}")
    print(f"Framework: {args.framework}")
    print("=" * 80)
    print(f"\nScore: {result.total_score}/{result.max_score} ({result.percentage:.1f}%)")
    print(f"Recommendation: {result.recommendation}")
    print(f"Rationale: {result.rationale}")

    print("\nBreakdown:")
    for key, value in result.breakdown.items():
        if not key.endswith('_evidence'):
            print(f"  {key}: {value}")

    if result.green_flags:
        print(f"\nStrengths: {', '.join(result.green_flags)}")

    if result.red_flags:
        print(f"\nConcerns: {', '.join(result.red_flags)}")

    if args.json:
        from dataclasses import asdict
        print(f"\nJSON:\n{json.dumps(asdict(result), indent=2)}")

    # Store score in database
    if not args.dry_run:
        conn = system._get_connection()
        try:
            conn.execute("""
                INSERT INTO interview_scores
                (interview_id, scoring_framework, total_score, max_score, percentage,
                 score_breakdown, red_flags, green_flags, recommendation, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                args.interview,
                result.framework,
                result.total_score,
                result.max_score,
                result.percentage,
                json.dumps(result.breakdown),
                json.dumps(result.red_flags),
                json.dumps(result.green_flags),
                result.recommendation,
                result.rationale
            ))
            conn.commit()
            print("\nScore saved to database.")
        finally:
            conn.close()


def cmd_list(args, system: InterviewSearchSystem):
    """List all interviews"""
    interviews = system.list_interviews(
        role_filter=args.role,
        status=args.status
    )

    if not interviews:
        print("No interviews found")
        return

    print(f"\nFound {len(interviews)} interviews:")
    print("=" * 80)

    if args.json:
        print(json.dumps(interviews, indent=2))
    else:
        headers = ['ID', 'Candidate', 'Role', 'Date', 'Segments', 'Score']
        rows = [
            [
                i['interview_id'][:8] + "...",
                i['candidate_name'],
                i['role_title'] or 'N/A',
                i['interview_date'] or 'N/A',
                i['total_segments'],
                f"{i['best_score']:.0f}%" if i['best_score'] else 'N/A'
            ]
            for i in interviews
        ]
        print(format_table(headers, rows))


def cmd_stats(args, system: InterviewSearchSystem):
    """Show system statistics"""
    stats = system.get_stats()

    print("\nInterview Search System Statistics")
    print("=" * 40)
    print(f"  Total Interviews:     {stats['total_interviews']}")
    print(f"  Total Segments:       {stats['total_segments']}")
    print(f"  Unique Candidates:    {stats['unique_candidates']}")
    print(f"  Unique Roles:         {stats['unique_roles']}")
    print(f"  ChromaDB Documents:   {stats['chromadb_documents']}")

    if args.json:
        print(f"\nJSON:\n{json.dumps(stats, indent=2)}")


def main():
    parser = argparse.ArgumentParser(
        description="Interview Search System - Hybrid SQLite FTS5 + ChromaDB RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a new interview
  python3 interview_cli.py ingest -f /path/to/interview.vtt -c "John Smith" -r "Pod Lead"

  # Search with hybrid (default)
  python3 interview_cli.py search -q "terraform experience"

  # Semantic search only
  python3 interview_cli.py search -q "managing difficult team members" --type semantic

  # Ask a question
  python3 interview_cli.py ask -q "Which candidate has the strongest leadership?"

  # Analyze an interview
  python3 interview_cli.py analyze -i <interview_id> --framework 100_point
        """
    )

    # Global args
    parser.add_argument('--json', action='store_true', help='Output in JSON format')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # INGEST command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a VTT interview file')
    ingest_parser.add_argument('-f', '--file', required=True, help='Path to VTT file')
    ingest_parser.add_argument('-c', '--candidate', required=True, help='Candidate name')
    ingest_parser.add_argument('-r', '--role', required=True, help='Role title')
    ingest_parser.add_argument('-d', '--date', help='Interview date (YYYY-MM-DD)')

    # SEARCH command
    search_parser = subparsers.add_parser('search', help='Search interviews')
    search_parser.add_argument('-q', '--query', required=True, help='Search query')
    search_parser.add_argument('-t', '--type', default='hybrid',
                               choices=['fts', 'semantic', 'hybrid'],
                               help='Search type (default: hybrid)')
    search_parser.add_argument('-l', '--limit', type=int, default=10,
                               help='Number of results (default: 10)')
    search_parser.add_argument('--candidate', help='Filter by candidate name')
    search_parser.add_argument('--role', help='Filter by role')

    # ASK command
    ask_parser = subparsers.add_parser('ask', help='Ask a question using RAG + LLM')
    ask_parser.add_argument('-q', '--question', required=True, help='Question to ask')
    ask_parser.add_argument('--context-limit', type=int, default=5,
                            help='Context segments to retrieve (default: 5)')
    ask_parser.add_argument('--model', default='llama3.2',
                            help='Ollama model (default: llama3.2)')

    # COMPARE command
    compare_parser = subparsers.add_parser('compare', help='Compare candidates')
    compare_parser.add_argument('-i', '--interviews', nargs='+', required=True,
                                help='Interview IDs to compare')
    compare_parser.add_argument('-o', '--output', default='table',
                                choices=['table', 'json', 'markdown'],
                                help='Output format (default: table)')

    # ANALYZE command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze and score an interview')
    analyze_parser.add_argument('-i', '--interview', required=True,
                                help='Interview ID to analyze')
    analyze_parser.add_argument('-f', '--framework', default='100_point',
                                choices=['100_point', '50_point', 'llm'],
                                help='Scoring framework (default: 100_point)')
    analyze_parser.add_argument('--dry-run', action='store_true',
                                help='Do not save score to database')

    # LIST command
    list_parser = subparsers.add_parser('list', help='List all interviews')
    list_parser.add_argument('--role', help='Filter by role')
    list_parser.add_argument('--status', default='active',
                             help='Filter by status (default: active)')

    # STATS command
    subparsers.add_parser('stats', help='Show system statistics')

    args = parser.parse_args()

    # Initialize system
    try:
        system = InterviewSearchSystem()
    except Exception as e:
        print(f"Error initializing system: {e}")
        sys.exit(1)

    # Route to command handler
    commands = {
        'ingest': cmd_ingest,
        'search': cmd_search,
        'ask': cmd_ask,
        'compare': cmd_compare,
        'analyze': cmd_analyze,
        'list': cmd_list,
        'stats': cmd_stats,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args, system)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
