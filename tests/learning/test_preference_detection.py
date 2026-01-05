#!/usr/bin/env python3
"""
Tests for P5: Preference Detection - Detect user corrections and preferences (TDD)

Phase 234: Heuristics for detecting when user corrects Claude.
"""

import pytest
from typing import List, Dict, Any


class TestCorrectionSignalDetection:
    """Tests for detecting correction signals in user messages."""

    def test_detects_explicit_no(self):
        """Test detection of explicit 'no' corrections."""
        from claude.tools.learning.preference_detection import detect_correction

        messages = [
            {"role": "assistant", "content": "I'll use tabs for indentation."},
            {"role": "user", "content": "No, use spaces instead."}
        ]

        result = detect_correction(messages)

        assert result['is_correction'] is True
        assert result['correction_type'] == 'explicit_rejection'

    def test_detects_wrong_keyword(self):
        """Test detection of 'wrong' keyword."""
        from claude.tools.learning.preference_detection import detect_correction

        messages = [
            {"role": "assistant", "content": "I added console.log for debugging."},
            {"role": "user", "content": "That's wrong, use the logger instead."}
        ]

        result = detect_correction(messages)

        assert result['is_correction'] is True

    def test_detects_actually_keyword(self):
        """Test detection of 'actually' keyword indicating correction."""
        from claude.tools.learning.preference_detection import detect_correction

        messages = [
            {"role": "assistant", "content": "I'll commit these changes."},
            {"role": "user", "content": "Actually, let's squash them first."}
        ]

        result = detect_correction(messages)

        assert result['is_correction'] is True
        assert result['correction_type'] == 'redirect'

    def test_detects_instead_keyword(self):
        """Test detection of 'instead' keyword."""
        from claude.tools.learning.preference_detection import detect_correction

        messages = [
            {"role": "assistant", "content": "I'll use axios for HTTP requests."},
            {"role": "user", "content": "Use fetch instead."}
        ]

        result = detect_correction(messages)

        assert result['is_correction'] is True

    def test_no_correction_for_normal_reply(self):
        """Test that normal replies are not flagged as corrections."""
        from claude.tools.learning.preference_detection import detect_correction

        messages = [
            {"role": "assistant", "content": "I've fixed the bug."},
            {"role": "user", "content": "Great, thanks! Now let's add tests."}
        ]

        result = detect_correction(messages)

        assert result['is_correction'] is False


class TestExplicitPreferenceDetection:
    """Tests for detecting explicit preference statements."""

    def test_detects_i_prefer_pattern(self):
        """Test detection of 'I prefer X' pattern."""
        from claude.tools.learning.preference_detection import detect_preference

        message = "I prefer using TypeScript over JavaScript."

        result = detect_preference(message)

        assert result['has_preference'] is True
        assert result['preference_type'] == 'stated_preference'
        assert 'typescript' in result['value'].lower()

    def test_detects_always_pattern(self):
        """Test detection of 'always do X' pattern."""
        from claude.tools.learning.preference_detection import detect_preference

        message = "Always use meaningful variable names."

        result = detect_preference(message)

        assert result['has_preference'] is True
        assert result['preference_type'] == 'rule'

    def test_detects_never_pattern(self):
        """Test detection of 'never do X' pattern."""
        from claude.tools.learning.preference_detection import detect_preference

        message = "Never commit directly to main branch."

        result = detect_preference(message)

        assert result['has_preference'] is True
        assert result['preference_type'] == 'prohibition'

    def test_detects_dont_pattern(self):
        """Test detection of \"don't do X\" pattern."""
        from claude.tools.learning.preference_detection import detect_preference

        message = "Don't add comments to obvious code."

        result = detect_preference(message)

        assert result['has_preference'] is True

    def test_no_preference_for_normal_message(self):
        """Test that normal messages don't trigger preference detection."""
        from claude.tools.learning.preference_detection import detect_preference

        message = "Can you help me fix this bug?"

        result = detect_preference(message)

        assert result['has_preference'] is False


class TestImplicitCorrectionDetection:
    """Tests for detecting implicit corrections (re-asks, alternatives)."""

    def test_detects_immediate_reask(self):
        """Test detection of immediate re-ask after rejection."""
        from claude.tools.learning.preference_detection import detect_implicit_correction

        messages = [
            {"role": "user", "content": "Format this code"},
            {"role": "assistant", "content": "Here's the formatted code with 2-space indent..."},
            {"role": "user", "content": "Format this code with 4-space indentation"}
        ]

        result = detect_implicit_correction(messages)

        assert result['is_implicit_correction'] is True
        assert result['correction_type'] == 'refined_request'

    def test_detects_alternative_after_no(self):
        """Test detection of alternative provided after 'no'."""
        from claude.tools.learning.preference_detection import detect_implicit_correction

        messages = [
            {"role": "assistant", "content": "I'll use MySQL for the database."},
            {"role": "user", "content": "No"},
            {"role": "user", "content": "Use PostgreSQL"}
        ]

        result = detect_implicit_correction(messages)

        assert result['is_implicit_correction'] is True

    def test_no_implicit_correction_for_new_topic(self):
        """Test that new topics are not flagged as corrections."""
        from claude.tools.learning.preference_detection import detect_implicit_correction

        messages = [
            {"role": "user", "content": "Fix the login bug"},
            {"role": "assistant", "content": "Fixed the login bug."},
            {"role": "user", "content": "Now add unit tests"}
        ]

        result = detect_implicit_correction(messages)

        assert result['is_implicit_correction'] is False


class TestPreferenceExtraction:
    """Tests for extracting structured preferences from corrections."""

    def test_extracts_preference_category(self):
        """Test extraction of preference category."""
        from claude.tools.learning.preference_detection import extract_preference

        correction = {
            'is_correction': True,
            'original': "I'll use 2-space indentation",
            'correction': "Use 4-space indentation"
        }

        preference = extract_preference(correction)

        assert preference['category'] == 'coding_style'
        assert 'indent' in preference['key'].lower()

    def test_extracts_tool_preference(self):
        """Test extraction of tool choice preference."""
        from claude.tools.learning.preference_detection import extract_preference

        correction = {
            'is_correction': True,
            'original': "I'll use npm",
            'correction': "Use pnpm instead"
        }

        preference = extract_preference(correction)

        assert preference['category'] == 'tool_choice'
        assert 'pnpm' in preference['value'].lower()

    def test_extracts_communication_preference(self):
        """Test extraction of communication style preference."""
        from claude.tools.learning.preference_detection import extract_preference

        correction = {
            'is_correction': True,
            'original': "Here's a detailed explanation...",
            'correction': "Just give me the code, no explanation needed"
        }

        preference = extract_preference(correction)

        assert preference['category'] == 'communication'


class TestPreferenceConfidence:
    """Tests for preference confidence scoring."""

    def test_explicit_preference_high_confidence(self):
        """Test that explicit preferences have high confidence."""
        from claude.tools.learning.preference_detection import calculate_confidence

        preference = {
            'source': 'explicit',
            'pattern': 'I prefer',
            'context': 'I prefer TypeScript'
        }

        confidence = calculate_confidence(preference)

        assert confidence >= 0.8

    def test_implicit_correction_lower_confidence(self):
        """Test that implicit corrections have lower confidence."""
        from claude.tools.learning.preference_detection import calculate_confidence

        preference = {
            'source': 'implicit',
            'pattern': 'refined_request',
            'context': 'User refined request'
        }

        confidence = calculate_confidence(preference)

        assert 0.4 <= confidence < 0.8

    def test_repeated_correction_increases_confidence(self):
        """Test that repeated corrections increase confidence."""
        from claude.tools.learning.preference_detection import calculate_confidence

        preference = {
            'source': 'explicit',
            'pattern': 'no',
            'occurrence_count': 3
        }

        confidence = calculate_confidence(preference)

        assert confidence >= 0.7


class TestPreferenceDetectionIntegration:
    """Integration tests for preference detection."""

    def test_analyze_conversation_finds_all_preferences(self):
        """Test that analyze_conversation finds all preference types."""
        from claude.tools.learning.preference_detection import analyze_conversation

        messages = [
            {"role": "user", "content": "Help me write a function"},
            {"role": "assistant", "content": "Here's a function with arrow syntax..."},
            {"role": "user", "content": "No, use regular function syntax. I prefer those."},
            {"role": "assistant", "content": "Updated to regular function."},
            {"role": "user", "content": "Also, always add JSDoc comments."}
        ]

        result = analyze_conversation(messages)

        assert len(result['preferences']) >= 2
        assert any(p['type'] == 'coding_style' or 'function' in str(p) for p in result['preferences'])

    def test_analyze_conversation_returns_empty_for_no_preferences(self):
        """Test that analyze_conversation returns empty for normal conversation."""
        from claude.tools.learning.preference_detection import analyze_conversation

        messages = [
            {"role": "user", "content": "What's the weather?"},
            {"role": "assistant", "content": "I can't check the weather."},
            {"role": "user", "content": "That's fine, thanks."}
        ]

        result = analyze_conversation(messages)

        assert len(result['preferences']) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
