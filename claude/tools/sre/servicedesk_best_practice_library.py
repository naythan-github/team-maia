#!/usr/bin/env python3
"""
ServiceDesk Best Practice Library Builder

Curates excellent comment examples across quality dimensions for use in coaching.

Features:
- RAG search for top-scored comments by dimension
- Automatic filtering by quality tier (excellent)
- Manual review + curation workflow
- Export to markdown library
- Tag by dimension, team, scenario

Usage:
    # Build library for all dimensions
    python3 servicedesk_best_practice_library.py --build-all --limit 20

    # Build library for specific dimension
    python3 servicedesk_best_practice_library.py --dimension empathy --limit 20

    # Export library to markdown
    python3 servicedesk_best_practice_library.py --export

    # Interactive curation mode
    python3 servicedesk_best_practice_library.py --curate --dimension clarity

Phase: 2.2 (Quality Intelligence Roadmap)
Author: Maia (ServiceDesk Manager Agent)
Date: 2025-10-18
"""

import argparse
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from servicedesk_gpu_rag_indexer import GPURAGIndexer


class BestPracticeLibrary:
    """
    Build and manage a curated library of excellent ServiceDesk comments
    """

    def __init__(self, db_path: str = None, library_path: str = None):
        self.db_path = db_path or '/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db'
        self.library_path = library_path or '/Users/naythandawe/git/maia/claude/data/best_practice_library.json'
        self.rag_indexer = GPURAGIndexer(db_path=self.db_path)

        # Quality dimensions
        self.dimensions = ['professionalism', 'clarity', 'empathy', 'actionability']

        # Load existing library
        self.library = self._load_library()

    def _load_library(self) -> Dict:
        """Load existing library or create new one"""
        if Path(self.library_path).exists():
            with open(self.library_path, 'r') as f:
                return json.load(f)
        return {
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0',
                'total_examples': 0
            },
            'examples': {dim: [] for dim in self.dimensions}
        }

    def _save_library(self):
        """Save library to JSON"""
        self.library['metadata']['last_updated'] = datetime.now().isoformat()
        self.library['metadata']['total_examples'] = sum(
            len(examples) for examples in self.library['examples'].values()
        )

        with open(self.library_path, 'w') as f:
            json.dump(self.library, f, indent=2)

        print(f"\n💾 Library saved: {self.library_path}")
        print(f"   Total examples: {self.library['metadata']['total_examples']:,}")

    def build_dimension_library(
        self,
        dimension: str,
        limit: int = 20,
        auto_approve: bool = False
    ) -> List[Dict]:
        """
        Build best practice library for a specific dimension

        Args:
            dimension: Quality dimension (professionalism, clarity, empathy, actionability)
            limit: Number of examples to fetch
            auto_approve: Auto-approve all examples (skip manual review)

        Returns:
            List of curated examples
        """

        print(f"\n{'='*70}")
        print(f"BUILDING BEST PRACTICE LIBRARY: {dimension.upper()}")
        print(f"{'='*70}")

        # 1. RAG search for excellent examples
        print(f"\n🔍 Searching for excellent {dimension} examples...")

        search_params = {
            'query_text': f"excellent {dimension} customer service communication",
            'quality_tier': 'excellent',
            'limit': limit * 3  # Fetch 3x to account for filtering
        }

        # Add dimension-specific score filter
        if dimension == 'professionalism':
            search_params['min_professionalism_score'] = 4
        elif dimension == 'clarity':
            search_params['min_clarity_score'] = 4
        elif dimension == 'empathy':
            search_params['min_empathy_score'] = 4
        elif dimension == 'actionability':
            search_params['min_actionability_score'] = 4

        # Note: search_by_quality needs min score params added
        # For now, fetch by tier and filter in post-processing
        results = self.rag_indexer.search_by_quality(
            query_text=search_params['query_text'],
            quality_tier=search_params['quality_tier'],
            limit=search_params['limit']
        )

        if not results.get('results'):
            print(f"   ⚠️  No excellent examples found for {dimension}")
            return []

        print(f"   ✅ Found {len(results['results'])} candidates")

        # 2. Filter by dimension-specific score (post-processing)
        filtered = []
        for result in results['results']:
            metadata = result.get('metadata', {})
            score_key = f'{dimension}_score'
            score = metadata.get(score_key)

            if score and score >= 4:
                filtered.append(result)

        print(f"   ✅ Filtered to {len(filtered)} high-scoring examples (score >= 4)")

        # 3. Manual curation or auto-approve
        curated = []
        if auto_approve:
            curated = filtered[:limit]
            print(f"   ✅ Auto-approved {len(curated)} examples")
        else:
            # Interactive curation
            curated = self._curate_examples(filtered, dimension, limit)

        # 4. Add to library
        for example in curated:
            self._add_to_library(dimension, example)

        print(f"\n✅ Added {len(curated)} examples to {dimension} library")
        return curated

    def _curate_examples(
        self,
        candidates: List[Dict],
        dimension: str,
        limit: int
    ) -> List[Dict]:
        """
        Interactive curation workflow

        User reviews each candidate and approves/rejects
        """

        print(f"\n{'='*70}")
        print(f"INTERACTIVE CURATION: {dimension.upper()}")
        print(f"{'='*70}")
        print(f"Review candidates and approve/reject (a=approve, r=reject, q=quit)")
        print()

        curated = []
        for i, candidate in enumerate(candidates):
            if len(curated) >= limit:
                break

            metadata = candidate.get('metadata', {})
            text = candidate.get('document', '')

            print(f"\n{'─'*70}")
            print(f"Candidate {i+1}/{len(candidates)}")
            print(f"{'─'*70}")
            print(f"Team: {metadata.get('team', 'Unknown')}")
            print(f"Agent: {metadata.get('user_name', 'Unknown')}")
            print(f"Created: {metadata.get('created_time', 'Unknown')}")
            print(f"\nScores:")
            print(f"  Professionalism: {metadata.get('professionalism_score', 'N/A')}/5")
            print(f"  Clarity: {metadata.get('clarity_score', 'N/A')}/5")
            print(f"  Empathy: {metadata.get('empathy_score', 'N/A')}/5")
            print(f"  Actionability: {metadata.get('actionability_score', 'N/A')}/5")
            print(f"  Overall: {metadata.get('quality_score', 'N/A')}/5")
            print(f"\nComment Text:")
            print(f"─────────────────")
            print(text[:500] + ('...' if len(text) > 500 else ''))
            print(f"─────────────────")

            # Get user input
            choice = input(f"\nApprove this example? (a/r/q): ").strip().lower()

            if choice == 'a':
                curated.append(candidate)
                print(f"✅ Approved ({len(curated)}/{limit})")
            elif choice == 'r':
                print(f"❌ Rejected")
            elif choice == 'q':
                print(f"⏸️  Curation stopped")
                break

        return curated

    def _add_to_library(self, dimension: str, example: Dict):
        """Add example to library"""

        metadata = example.get('metadata', {})

        library_entry = {
            'comment_id': metadata.get('comment_id'),
            'ticket_id': metadata.get('ticket_id'),
            'user_name': metadata.get('user_name'),
            'team': metadata.get('team'),
            'created_time': metadata.get('created_time'),
            'text': example.get('document', ''),
            'scores': {
                'professionalism': metadata.get('professionalism_score'),
                'clarity': metadata.get('clarity_score'),
                'empathy': metadata.get('empathy_score'),
                'actionability': metadata.get('actionability_score'),
                'overall': metadata.get('quality_score')
            },
            'quality_tier': metadata.get('quality_tier'),
            'tags': metadata.get('content_tags', '').split(',') if metadata.get('content_tags') else [],
            'added_to_library': datetime.now().isoformat()
        }

        # Check if already exists
        existing_ids = [e.get('comment_id') for e in self.library['examples'][dimension]]
        if library_entry['comment_id'] not in existing_ids:
            self.library['examples'][dimension].append(library_entry)

    def build_all_dimensions(self, limit_per_dimension: int = 20, auto_approve: bool = False):
        """Build library for all dimensions"""

        print(f"\n{'='*70}")
        print(f"BUILDING COMPLETE BEST PRACTICE LIBRARY")
        print(f"{'='*70}")
        print(f"Target: {limit_per_dimension} examples per dimension")
        print(f"Auto-approve: {auto_approve}")

        for dimension in self.dimensions:
            self.build_dimension_library(dimension, limit_per_dimension, auto_approve)

        self._save_library()

        print(f"\n{'='*70}")
        print(f"LIBRARY BUILD COMPLETE")
        print(f"{'='*70}")
        self._print_library_stats()

    def export_to_markdown(self, output_path: str = None):
        """Export library to markdown format"""

        output_path = output_path or '/Users/naythandawe/git/maia/claude/data/best_practice_library.md'

        markdown = []
        markdown.append("# ServiceDesk Best Practice Library\n")
        markdown.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        markdown.append(f"**Total Examples**: {self.library['metadata']['total_examples']}\n")
        markdown.append("---\n\n")

        for dimension in self.dimensions:
            examples = self.library['examples'][dimension]
            markdown.append(f"## {dimension.title()} ({len(examples)} examples)\n\n")

            for i, example in enumerate(examples, 1):
                markdown.append(f"### Example {i}\n\n")
                markdown.append(f"**Agent**: {example['user_name']} ({example['team']})\n")
                markdown.append(f"**Date**: {example['created_time']}\n")
                markdown.append(f"**Scores**: Prof={example['scores']['professionalism']}/5, "
                               f"Clar={example['scores']['clarity']}/5, "
                               f"Emp={example['scores']['empathy']}/5, "
                               f"Act={example['scores']['actionability']}/5\n\n")
                markdown.append(f"**Comment**:\n```\n{example['text']}\n```\n\n")
                markdown.append("---\n\n")

        # Write to file
        with open(output_path, 'w') as f:
            f.write(''.join(markdown))

        print(f"\n📄 Markdown export: {output_path}")
        print(f"   Size: {len(''.join(markdown)):,} characters")

    def _print_library_stats(self):
        """Print library statistics"""

        print(f"\n📊 Library Statistics:")
        print(f"   Created: {self.library['metadata']['created']}")
        print(f"   Last Updated: {self.library['metadata']['last_updated']}")
        print(f"   Total Examples: {self.library['metadata']['total_examples']}")
        print(f"\n   By Dimension:")
        for dimension in self.dimensions:
            count = len(self.library['examples'][dimension])
            print(f"     {dimension.title():<15} {count:>3} examples")

    def get_examples_for_dimension(self, dimension: str, limit: int = 5) -> List[Dict]:
        """Get random examples from library for a dimension"""
        import random
        examples = self.library['examples'].get(dimension, [])
        return random.sample(examples, min(limit, len(examples)))

    def search_examples(
        self,
        dimension: str = None,
        team: str = None,
        min_score: float = None
    ) -> List[Dict]:
        """Search library for examples matching criteria"""

        results = []
        search_dimensions = [dimension] if dimension else self.dimensions

        for dim in search_dimensions:
            for example in self.library['examples'][dim]:
                # Filter by team
                if team and example['team'] != team:
                    continue

                # Filter by score
                if min_score:
                    score = example['scores'].get(dim)
                    if not score or score < min_score:
                        continue

                results.append({**example, 'dimension': dim})

        return results


def main():
    parser = argparse.ArgumentParser(description='ServiceDesk Best Practice Library Builder')

    # Build commands
    parser.add_argument('--build-all', action='store_true',
                       help='Build library for all dimensions')
    parser.add_argument('--dimension', type=str,
                       help='Build library for specific dimension (professionalism, clarity, empathy, actionability)')
    parser.add_argument('--limit', type=int, default=20,
                       help='Number of examples per dimension (default: 20)')
    parser.add_argument('--auto-approve', action='store_true',
                       help='Auto-approve all examples (skip manual review)')

    # Curation commands
    parser.add_argument('--curate', action='store_true',
                       help='Interactive curation mode')

    # Export commands
    parser.add_argument('--export', action='store_true',
                       help='Export library to markdown')
    parser.add_argument('--output', type=str,
                       help='Output path for markdown export')

    # Stats commands
    parser.add_argument('--stats', action='store_true',
                       help='Show library statistics')

    args = parser.parse_args()

    # Initialize library
    library = BestPracticeLibrary()

    # Execute commands
    if args.build_all:
        library.build_all_dimensions(args.limit, args.auto_approve)
    elif args.dimension:
        if args.curate:
            library.build_dimension_library(args.dimension, args.limit, auto_approve=False)
        else:
            library.build_dimension_library(args.dimension, args.limit, args.auto_approve)
        library._save_library()
    elif args.export:
        library.export_to_markdown(args.output)
    elif args.stats:
        library._print_library_stats()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
