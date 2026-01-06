#!/usr/bin/env python3
"""
Tests for Enhanced Learning Patterns
Phase 237.3: Enhanced Pattern Library

New pattern types:
- refactoring: Code quality improvements
- error_recovery: Error → fix sequences
- optimization: Performance improvements
- learning: Explicit insights
- breakthrough: Major discoveries
- test: Testing-related learnings
- security: Security fixes

Author: Maia (Phase 237.3)
Created: 2026-01-06
"""

import json
import pytest
from claude.tools.learning.extraction import (
    LearningExtractor,
    LEARNING_PATTERNS,
    get_extractor
)


@pytest.fixture
def enhanced_extractor():
    """Create extractor with enhanced patterns."""
    return get_extractor()


# ============================================================================
# Refactoring Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_refactoring():
    """Transcript containing refactoring pattern."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Refactored the authentication module to use dependency injection for better testability.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_refactoring_pattern(enhanced_extractor, transcript_with_refactoring):
    """Test refactoring pattern detection."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_refactoring)

    learnings = [l for l in result['learnings'] if l['type'] == 'refactoring']
    assert len(learnings) >= 1
    assert 'refactor' in learnings[0]['content'].lower()


@pytest.fixture
def transcript_with_cleanup():
    """Transcript with code cleanup."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Cleaned up duplicate code by extracting common logic into a shared utility function.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_cleanup_as_refactoring(enhanced_extractor, transcript_with_cleanup):
    """Test cleanup detected as refactoring."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_cleanup)

    learnings = [l for l in result['learnings'] if l['type'] == 'refactoring']
    assert len(learnings) >= 1


# ============================================================================
# Error Recovery Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_error_recovery():
    """Transcript with error → fix sequence."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Encountered TypeError: cannot concatenate str and int. Fixed by adding explicit type conversion.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_error_recovery_pattern(enhanced_extractor, transcript_with_error_recovery):
    """Test error recovery pattern detection."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_error_recovery)

    learnings = [l for l in result['learnings'] if l['type'] == 'error_recovery']
    assert len(learnings) >= 1
    assert 'error' in learnings[0]['content'].lower() or 'exception' in learnings[0]['content'].lower()


@pytest.fixture
def transcript_with_exception_handling():
    """Transcript with exception handling."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Caught FileNotFoundError and handled it by creating the missing directory.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_exception_handling(enhanced_extractor, transcript_with_exception_handling):
    """Test exception handling detected as error recovery."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_exception_handling)

    learnings = [l for l in result['learnings'] if l['type'] == 'error_recovery']
    assert len(learnings) >= 1


# ============================================================================
# Optimization Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_optimization():
    """Transcript with performance optimization."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Optimized database queries by adding an index on the user_id column, reducing query time from 2s to 50ms.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_optimization_pattern(enhanced_extractor, transcript_with_optimization):
    """Test optimization pattern detection."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_optimization)

    learnings = [l for l in result['learnings'] if l['type'] == 'optimization']
    assert len(learnings) >= 1
    assert 'optim' in learnings[0]['content'].lower()


@pytest.fixture
def transcript_with_performance_improvement():
    """Transcript with performance improvement."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Improved performance by implementing caching, reducing API calls by 80%.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_performance_improvement(enhanced_extractor, transcript_with_performance_improvement):
    """Test performance improvement detected as optimization."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_performance_improvement)

    learnings = [l for l in result['learnings'] if l['type'] == 'optimization']
    assert len(learnings) >= 1


# ============================================================================
# Learning Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_explicit_learning():
    """Transcript with explicit learning statement."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Learned that SQLite performs better for small datasets (<100K rows) compared to Postgres.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_explicit_learning(enhanced_extractor, transcript_with_explicit_learning):
    """Test explicit learning pattern detection."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_explicit_learning)

    learnings = [l for l in result['learnings'] if l['type'] == 'learning']
    assert len(learnings) >= 1
    assert 'learned' in learnings[0]['content'].lower()


@pytest.fixture
def transcript_with_insight():
    """Transcript with insight."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Realized that the bottleneck was in the serialization step, not the database query.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_insight_as_learning(enhanced_extractor, transcript_with_insight):
    """Test insight detected as learning."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_insight)

    learnings = [l for l in result['learnings'] if l['type'] == 'learning']
    assert len(learnings) >= 1


# ============================================================================
# Breakthrough Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_breakthrough():
    """Transcript with major breakthrough."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Breakthrough: Discovered that the memory leak was caused by circular references in the event handler.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_breakthrough_pattern(enhanced_extractor, transcript_with_breakthrough):
    """Test breakthrough pattern detection."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_breakthrough)

    learnings = [l for l in result['learnings'] if l['type'] == 'breakthrough']
    assert len(learnings) >= 1
    assert 'breakthrough' in learnings[0]['content'].lower() or 'discover' in learnings[0]['content'].lower()


@pytest.fixture
def transcript_with_key_insight():
    """Transcript with key insight marker."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Key insight: The issue only occurs when multiple threads access the cache simultaneously.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_key_insight_as_breakthrough(enhanced_extractor, transcript_with_key_insight):
    """Test key insight detected as breakthrough."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_key_insight)

    learnings = [l for l in result['learnings'] if l['type'] == 'breakthrough']
    assert len(learnings) >= 1


# ============================================================================
# Test Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_test_learning():
    """Transcript with testing learning."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Added integration tests to verify the authentication flow works end-to-end.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_test_pattern(enhanced_extractor, transcript_with_test_learning):
    """Test pattern detection for testing learnings."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_test_learning)

    learnings = [l for l in result['learnings'] if l['type'] == 'test']
    assert len(learnings) >= 1
    assert 'test' in learnings[0]['content'].lower()


@pytest.fixture
def transcript_with_test_coverage():
    """Transcript with test coverage improvement."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Increased test coverage from 75% to 95% by adding edge case tests.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_test_coverage(enhanced_extractor, transcript_with_test_coverage):
    """Test coverage improvement detected as test learning."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_test_coverage)

    learnings = [l for l in result['learnings'] if l['type'] == 'test']
    assert len(learnings) >= 1


# ============================================================================
# Security Pattern Tests
# ============================================================================

@pytest.fixture
def transcript_with_security_fix():
    """Transcript with security fix."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Fixed SQL injection vulnerability by using parameterized queries instead of string concatenation.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_security_fix(enhanced_extractor, transcript_with_security_fix):
    """Test security fix pattern detection."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_security_fix)

    learnings = [l for l in result['learnings'] if l['type'] == 'security']
    assert len(learnings) >= 1
    assert any(keyword in learnings[0]['content'].lower() for keyword in ['security', 'vulnerability', 'injection'])


@pytest.fixture
def transcript_with_vulnerability():
    """Transcript with vulnerability discovery."""
    messages = [
        {
            'type': 'assistant_message',
            'content': 'Identified XSS vulnerability in user input handling and sanitized all user-generated content.',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_vulnerability_fix(enhanced_extractor, transcript_with_vulnerability):
    """Test vulnerability fix detected as security learning."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_vulnerability)

    learnings = [l for l in result['learnings'] if l['type'] == 'security']
    assert len(learnings) >= 1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.fixture
def transcript_with_multiple_enhanced_patterns():
    """Transcript with multiple enhanced pattern types."""
    messages = [
        {
            'type': 'assistant_message',
            'content': '''
            Refactored the API handler to use async/await for better performance.
            Optimized database queries, reducing latency from 500ms to 50ms.
            Learned that connection pooling is critical for high-traffic APIs.
            Fixed security vulnerability by adding CSRF token validation.
            Added comprehensive test coverage for all endpoints.
            ''',
            'timestamp': '2026-01-06T10:00:00Z'
        }
    ]
    return '\n'.join(json.dumps(msg) for msg in messages)


def test_extract_multiple_enhanced_patterns(enhanced_extractor, transcript_with_multiple_enhanced_patterns):
    """Test extraction of multiple enhanced pattern types from single message."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_multiple_enhanced_patterns)

    pattern_types = {l['type'] for l in result['learnings']}

    # Should detect multiple pattern types
    assert len(pattern_types) >= 3

    # Verify specific patterns detected
    assert any(l['type'] == 'refactoring' for l in result['learnings'])
    assert any(l['type'] == 'optimization' for l in result['learnings'])
    assert any(l['type'] == 'security' for l in result['learnings'])


def test_enhanced_patterns_preserve_context(enhanced_extractor, transcript_with_refactoring):
    """Test that enhanced patterns preserve message context."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_refactoring)

    if result['learnings']:
        learning = result['learnings'][0]
        assert 'context' in learning
        assert 'timestamp' in learning


def test_enhanced_patterns_have_confidence(enhanced_extractor, transcript_with_optimization):
    """Test that enhanced patterns include confidence scores."""
    result = enhanced_extractor.extract_from_transcript(transcript_with_optimization)

    learnings = [l for l in result['learnings'] if l['type'] == 'optimization']
    if learnings:
        assert 'confidence' in learnings[0]
        assert 0.0 <= learnings[0]['confidence'] <= 1.0


# ============================================================================
# Pattern Count Tests
# ============================================================================

def test_enhanced_patterns_added_to_library():
    """Test that enhanced patterns are added to LEARNING_PATTERNS."""
    # After implementation, LEARNING_PATTERNS should have 12 types (5 original + 7 new)
    expected_patterns = [
        'decision', 'solution', 'outcome', 'handoff', 'checkpoint',  # Original 5
        'refactoring', 'error_recovery', 'optimization', 'learning',   # New 7
        'breakthrough', 'test', 'security'
    ]

    # This will fail until we implement the patterns
    for pattern_type in expected_patterns:
        assert pattern_type in LEARNING_PATTERNS, f"Pattern '{pattern_type}' not found in LEARNING_PATTERNS"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
