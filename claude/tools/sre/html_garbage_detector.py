#!/usr/bin/env python3
"""
HTML Garbage Detector for ServiceDesk Comments

Detects comments that are >80% HTML markup and should be excluded from sentiment analysis.

Usage:
    from html_garbage_detector import is_html_garbage

    if is_html_garbage(comment_text):
        # Skip LLM analysis, mark as invalid

Author: SRE Principal Engineer Agent
Created: 2025-10-24 (Phase 135 - Incident Resolution)
"""

import re
from typing import Tuple


def is_html_garbage(text: str, html_threshold: float = 0.8) -> Tuple[bool, float]:
    """
    Detect if comment is primarily HTML markup (garbage data).

    Args:
        text: Comment text to analyze
        html_threshold: Ratio above which text is considered HTML garbage (default: 0.8 = 80%)

    Returns:
        Tuple of (is_garbage: bool, html_ratio: float)

    Examples:
        >>> is_html_garbage("<p>assisted</p>")
        (True, 0.93)  # 93% HTML tags

        >>> is_html_garbage("Thanks for your help!")
        (False, 0.0)  # 0% HTML tags

        >>> is_html_garbage("<p>Thanks for <b>your</b> help!</p>")
        (False, 0.42)  # 42% HTML tags (below 80% threshold)
    """
    if not text or len(text) == 0:
        return False, 0.0

    # Strip HTML tags and measure remaining text
    text_without_html = re.sub(r'<[^>]+>', '', text)

    # Calculate HTML ratio
    original_length = len(text)
    clean_length = len(text_without_html)

    if original_length == 0:
        return False, 0.0

    html_ratio = (original_length - clean_length) / original_length

    # Check if exceeds threshold
    is_garbage = html_ratio >= html_threshold

    return is_garbage, html_ratio


def detect_html_garbage_batch(comments: list, html_threshold: float = 0.8) -> dict:
    """
    Batch detect HTML garbage in multiple comments.

    Args:
        comments: List of dicts with 'comment_id' and 'comment_text' keys
        html_threshold: HTML ratio threshold (default: 0.8)

    Returns:
        Dictionary with:
            - garbage_ids: List of comment_ids that are HTML garbage
            - garbage_count: Count of garbage comments
            - clean_count: Count of clean comments
            - html_ratios: Dict mapping comment_id -> html_ratio
    """
    garbage_ids = []
    html_ratios = {}

    for comment in comments:
        comment_id = comment.get('comment_id')
        text = comment.get('comment_text', '')

        is_garbage, html_ratio = is_html_garbage(text, html_threshold)

        html_ratios[comment_id] = html_ratio

        if is_garbage:
            garbage_ids.append(comment_id)

    return {
        'garbage_ids': garbage_ids,
        'garbage_count': len(garbage_ids),
        'clean_count': len(comments) - len(garbage_ids),
        'html_ratios': html_ratios
    }


def create_html_filter_sql() -> str:
    """
    Generate PostgreSQL SQL to filter HTML garbage comments.

    Returns:
        SQL WHERE clause to exclude HTML-heavy comments
    """
    return """
    -- Exclude comments where >80% is HTML markup
    AND (
        LENGTH(comment_text) - LENGTH(REGEXP_REPLACE(comment_text, '<[^>]+>', '', 'g'))
    ) / NULLIF(LENGTH(comment_text), 0)::float < 0.8
    """


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("<p>assisted</p>", True),  # 93% HTML
        ("Thanks for your help!", False),  # 0% HTML
        ("<p>Thanks for <b>your</b> help!</p>", False),  # 42% HTML
        ("<p><span style='color: rgb(0, 0, 0); font-family: poppins, sans-serif;'>Test</span></p>", True),  # >80% HTML
    ]

    print("HTML Garbage Detector - Test Cases")
    print("=" * 80)

    for text, expected_garbage in test_cases:
        is_garbage, html_ratio = is_html_garbage(text)
        status = "✅" if is_garbage == expected_garbage else "❌"
        print(f"{status} Text: {text[:50]}...")
        print(f"   HTML Ratio: {html_ratio:.2%}, Is Garbage: {is_garbage}")
        print()
