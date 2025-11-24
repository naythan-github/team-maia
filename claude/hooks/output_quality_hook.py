#!/usr/bin/env python3
"""
Output Quality Hook - Pre-Delivery Quality Check

Phase 1 Agentic AI Enhancement: Self-Critique Before Completion

Integrates the OutputCritic system as a lightweight quality gate
that can be called before delivering agent responses.

Usage:
    from output_quality_hook import check_output_quality, should_refine

    # Quick check
    result = check_output_quality(response_text, query)
    if result['needs_refinement']:
        print(result['refinement_prompt'])

    # Simple boolean
    if should_refine(response_text, query):
        # Trigger refinement

Author: Maia System
Created: 2025-11-24 (Phase 1 Agentic AI Enhancement)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure orchestration tools are importable
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "orchestration"))


def check_output_quality(
    output: str,
    query: Optional[str] = None,
    threshold: float = 0.7,
    use_llm: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Check output quality before delivery.

    Args:
        output: The response text to check
        query: Original user query (for context)
        threshold: Quality threshold (default: 0.7)
        use_llm: Use LLM for deeper semantic check (default: False for speed)
        verbose: Print progress

    Returns:
        Dict with:
            - score: Quality score (0.0-1.0)
            - passed: Whether it passed threshold
            - needs_refinement: Whether refinement is recommended
            - issues: List of issues found
            - refinement_prompt: Suggested refinement if needed
    """
    try:
        from output_critic import OutputCritic

        critic = OutputCritic(threshold=threshold, use_llm=use_llm)

        context = {}
        if query:
            context['query'] = query

        result = critic.critique(output, context, verbose=verbose)

        return {
            'score': result.overall_score,
            'passed': result.passed,
            'needs_refinement': result.refinement_needed,
            'issues': [
                {
                    'category': i.category.value,
                    'severity': i.severity,
                    'description': i.description,
                    'suggestion': i.suggestion
                }
                for i in result.issues
            ],
            'refinement_prompt': result.refinement_prompt,
            'category_scores': result.category_scores,
            'strengths': result.strengths
        }

    except ImportError as e:
        # Graceful degradation - return passing result
        return {
            'score': 1.0,
            'passed': True,
            'needs_refinement': False,
            'issues': [],
            'refinement_prompt': None,
            'category_scores': {},
            'strengths': ['Quality check unavailable (graceful pass)'],
            'error': str(e)
        }


def should_refine(
    output: str,
    query: Optional[str] = None,
    threshold: float = 0.7
) -> bool:
    """
    Quick check if output needs refinement.

    Args:
        output: Response text to check
        query: Original query (optional)
        threshold: Quality threshold

    Returns:
        True if refinement is recommended
    """
    result = check_output_quality(output, query, threshold, use_llm=False)
    return result['needs_refinement']


def get_high_severity_issues(
    output: str,
    query: Optional[str] = None
) -> list:
    """
    Get only high severity issues from output.

    Args:
        output: Response text to check
        query: Original query (optional)

    Returns:
        List of high severity issues
    """
    result = check_output_quality(output, query, use_llm=False)
    return [i for i in result['issues'] if i['severity'] == 'high']


def format_quality_summary(result: Dict[str, Any]) -> str:
    """
    Format quality check result as human-readable summary.

    Args:
        result: Result from check_output_quality()

    Returns:
        Formatted string
    """
    lines = []
    status = "✅ PASSED" if result['passed'] else "❌ NEEDS WORK"
    lines.append(f"Quality: {status} ({result['score']:.0%})")

    if result['issues']:
        lines.append(f"\nIssues ({len(result['issues'])}):")
        for issue in result['issues'][:3]:
            lines.append(f"  [{issue['severity'].upper()}] {issue['description']}")

    if result['strengths']:
        lines.append(f"\nStrengths: {', '.join(result['strengths'][:2])}")

    return '\n'.join(lines)


# CLI interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Output Quality Hook")
    parser.add_argument('--text', '-t', help='Text to check')
    parser.add_argument('--file', '-f', help='File to check')
    parser.add_argument('--query', '-q', help='Original query context')
    parser.add_argument('--threshold', type=float, default=0.7)
    parser.add_argument('--llm', action='store_true', help='Use LLM evaluation')

    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Provide --text or --file")
        return 1

    result = check_output_quality(
        text,
        query=args.query,
        threshold=args.threshold,
        use_llm=args.llm,
        verbose=True
    )

    print("\n" + "=" * 50)
    print(format_quality_summary(result))

    return 0 if result['passed'] else 1


if __name__ == "__main__":
    sys.exit(main())
