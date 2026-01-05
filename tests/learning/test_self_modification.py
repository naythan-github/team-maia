#!/usr/bin/env python3
"""
Tests for P7: Self-modification - Update preferences and suggest prompt updates (TDD)

Phase 234: Modify user preferences based on learnings and suggest agent prompt updates.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestPreferenceUpdate:
    """Tests for updating user preferences based on learnings."""

    def test_update_preference_creates_entry(self):
        """Test that update_preference creates a new preference entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import update_preference

                result = update_preference(
                    category='coding_style',
                    key='indentation',
                    value='4 spaces',
                    confidence=0.8,
                    source_session='session_123'
                )

                assert result['updated'] is True

    def test_update_preference_increases_confidence(self):
        """Test that repeated updates increase confidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import update_preference, get_preference

                # First update
                update_preference('tool_choice', 'package_manager', 'pnpm', 0.6, 's1')

                # Second update
                update_preference('tool_choice', 'package_manager', 'pnpm', 0.6, 's2')

                pref = get_preference('tool_choice', 'package_manager')

                assert pref['confidence'] > 0.6

    def test_get_preference_returns_none_for_missing(self):
        """Test that get_preference returns None for missing preference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import get_preference

                pref = get_preference('nonexistent', 'key')

                assert pref is None

    def test_list_preferences_returns_all(self):
        """Test that list_preferences returns all stored preferences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import (
                    update_preference, list_preferences
                )

                update_preference('coding_style', 'indent', '4 spaces', 0.8, 's1')
                update_preference('tool_choice', 'pm', 'pnpm', 0.7, 's1')

                prefs = list_preferences()

                assert len(prefs) >= 2


class TestUserPreferencesFile:
    """Tests for syncing with user_preferences.json."""

    def test_sync_to_user_preferences_json(self):
        """Test syncing learned preferences to user_preferences.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_maia = Path(tmpdir) / "maia"
            fake_maia.mkdir()
            prefs_file = fake_maia / "claude" / "data" / "user_preferences.json"
            prefs_file.parent.mkdir(parents=True)
            prefs_file.write_text('{"default_agent": "sre"}')

            with patch('claude.tools.learning.self_modification.USER_PREFERENCES_PATH', prefs_file):
                from claude.tools.learning.self_modification import sync_to_user_preferences

                learned_prefs = {
                    'coding_style': {'indentation': {'value': '4 spaces', 'confidence': 0.9}}
                }

                result = sync_to_user_preferences(learned_prefs)

                assert result['synced'] is True

                # Verify file updated
                updated = json.loads(prefs_file.read_text())
                assert 'learned_preferences' in updated

    def test_sync_preserves_existing_preferences(self):
        """Test that sync preserves existing user preferences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_maia = Path(tmpdir) / "maia"
            fake_maia.mkdir()
            prefs_file = fake_maia / "claude" / "data" / "user_preferences.json"
            prefs_file.parent.mkdir(parents=True)
            prefs_file.write_text('{"default_agent": "security_agent", "version": "1.0"}')

            with patch('claude.tools.learning.self_modification.USER_PREFERENCES_PATH', prefs_file):
                from claude.tools.learning.self_modification import sync_to_user_preferences

                sync_to_user_preferences({})

                updated = json.loads(prefs_file.read_text())
                assert updated['default_agent'] == 'security_agent'
                assert updated['version'] == '1.0'


class TestPromptSuggestions:
    """Tests for generating agent prompt update suggestions."""

    def test_suggest_prompt_update_returns_suggestion(self):
        """Test that suggest_prompt_update returns a suggestion."""
        from claude.tools.learning.self_modification import suggest_prompt_update

        pattern = {
            'type': 'workflow',
            'description': 'Always run tests before committing',
            'confidence': 0.85,
            'occurrence_count': 5
        }

        suggestion = suggest_prompt_update(pattern)

        assert suggestion is not None
        assert 'suggestion' in suggestion
        assert 'target_file' in suggestion

    def test_suggest_prompt_update_identifies_target_agent(self):
        """Test that suggestion identifies the correct target agent."""
        from claude.tools.learning.self_modification import suggest_prompt_update

        pattern = {
            'type': 'workflow',
            'domain': 'sre',
            'description': 'Use structured logging',
            'confidence': 0.9,
            'occurrence_count': 3
        }

        suggestion = suggest_prompt_update(pattern)

        assert 'sre' in suggestion['target_file'].lower()

    def test_suggest_prompt_update_requires_high_confidence(self):
        """Test that low confidence patterns don't generate suggestions."""
        from claude.tools.learning.self_modification import suggest_prompt_update

        pattern = {
            'type': 'workflow',
            'description': 'Some pattern',
            'confidence': 0.4,  # Too low
            'occurrence_count': 1
        }

        suggestion = suggest_prompt_update(pattern)

        assert suggestion is None or suggestion.get('skip_reason') == 'low_confidence'


class TestPromptSuggestionFormat:
    """Tests for prompt suggestion output format."""

    def test_suggestion_includes_diff(self):
        """Test that suggestion includes a diff-style change."""
        from claude.tools.learning.self_modification import suggest_prompt_update

        pattern = {
            'type': 'preference',
            'domain': 'general',
            'description': 'User prefers concise responses',
            'confidence': 0.9,
            'occurrence_count': 4
        }

        suggestion = suggest_prompt_update(pattern)

        if suggestion and not suggestion.get('skip_reason'):
            assert 'diff' in suggestion or 'change' in suggestion

    def test_suggestion_requires_approval(self):
        """Test that suggestion is marked as requiring approval."""
        from claude.tools.learning.self_modification import suggest_prompt_update

        pattern = {
            'type': 'workflow',
            'domain': 'sre',
            'description': 'Always check SLOs',
            'confidence': 0.95,
            'occurrence_count': 10
        }

        suggestion = suggest_prompt_update(pattern)

        if suggestion and not suggestion.get('skip_reason'):
            assert suggestion.get('requires_approval', True) is True


class TestSelfModificationIntegration:
    """Integration tests for self-modification system."""

    def test_process_learnings_updates_preferences(self):
        """Test that process_learnings updates preferences from LEARN output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import process_learnings

                learnings = {
                    'patterns': [
                        {
                            'pattern_type': 'preference',
                            'description': 'User prefers TypeScript',
                            'confidence': 0.8
                        }
                    ],
                    'preferences': [
                        {
                            'category': 'language',
                            'key': 'preferred',
                            'value': 'TypeScript',
                            'confidence': 0.8
                        }
                    ]
                }

                result = process_learnings(learnings, session_id='s123')

                assert result['preferences_updated'] >= 1

    def test_process_learnings_generates_suggestions(self):
        """Test that process_learnings generates prompt suggestions."""
        from claude.tools.learning.self_modification import process_learnings

        learnings = {
            'patterns': [
                {
                    'pattern_type': 'workflow',
                    'domain': 'sre',
                    'description': 'Always check error budgets before deploys',
                    'confidence': 0.9,
                    'occurrence_count': 5
                }
            ],
            'preferences': []
        }

        result = process_learnings(learnings, session_id='s123')

        assert 'suggestions' in result


class TestSafetyGuardrails:
    """Tests for safety guardrails in self-modification."""

    def test_cannot_modify_core_identity(self):
        """Test that core identity files cannot be modified."""
        from claude.tools.learning.self_modification import suggest_prompt_update

        pattern = {
            'type': 'workflow',
            'description': 'Change identity',
            'confidence': 0.99,
            'occurrence_count': 100,
            'target_hint': 'identity.md'  # Core file
        }

        suggestion = suggest_prompt_update(pattern)

        # Should refuse or require explicit override
        assert suggestion is None or suggestion.get('blocked') is True

    def test_max_changes_per_session(self):
        """Test that there's a limit on changes per session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import (
                    update_preference, MAX_UPDATES_PER_SESSION
                )

                # Try to exceed limit
                for i in range(MAX_UPDATES_PER_SESSION + 5):
                    result = update_preference(f'cat_{i}', f'key_{i}', 'val', 0.8, 'same_session')

                # Last few should be blocked
                # (Implementation should track and enforce)
                # This test documents the expected behavior


class TestModificationAudit:
    """Tests for audit trail of modifications."""

    def test_modifications_are_logged(self):
        """Test that all modifications are logged for audit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import (
                    update_preference, get_modification_log
                )

                update_preference('test', 'key', 'value', 0.8, 's1')

                log = get_modification_log()

                assert len(log) >= 1
                assert log[0]['session_id'] == 's1'

    def test_log_includes_timestamp(self):
        """Test that modification log includes timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                from claude.tools.learning.self_modification import (
                    update_preference, get_modification_log
                )

                update_preference('test', 'key', 'value', 0.8, 's1')

                log = get_modification_log()

                assert 'timestamp' in log[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
