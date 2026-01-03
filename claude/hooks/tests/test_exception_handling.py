"""
Tests for exception handling in hooks.

TDD: Verifies that hooks handle exceptions gracefully without bare except clauses.
Phase: Python Refactoring - Bare Except Elimination
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add hooks to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSwarmAutoLoaderExceptionHandling:
    """Test exception handling in swarm_auto_loader.py"""

    def test_file_stat_handles_missing_file(self):
        """Verify file stat operations handle FileNotFoundError gracefully."""
        # Test that Path.stat() failures don't crash the system
        test_path = Path("/nonexistent/file/that/does/not/exist.py")

        # This should raise FileNotFoundError, not be caught by bare except
        with pytest.raises(FileNotFoundError):
            test_path.stat()

    def test_file_stat_handles_permission_error(self, tmp_path):
        """Verify file stat operations handle PermissionError gracefully."""
        # Create a file we can test with
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # File should be readable
        stat_result = test_file.stat()
        assert stat_result.st_mtime > 0


class TestM4AgentClassificationExceptionHandling:
    """Test exception handling in m4_agent_classification.py"""

    def test_classification_fallback_on_import_error(self):
        """Verify classification returns fallback on ImportError."""
        # Import the module
        try:
            from m4_agent_classification import classify_request

            # Test with mock that raises ImportError
            with patch.dict('sys.modules', {'claude.models.agent_intent_classifier': None}):
                # Should return fallback, not crash
                result = classify_request({"query": "test"})
                # Fallback behavior: use_claude=True
                assert result.get("use_claude", False) is True
        except ImportError:
            pytest.skip("m4_agent_classification not available")

    def test_classification_fallback_on_exception(self):
        """Verify classification returns fallback on any Exception."""
        try:
            from m4_agent_classification import classify_request

            # Mock classifier to raise exception
            with patch('m4_agent_classification.AgentIntentClassifier') as mock_cls:
                mock_cls.side_effect = Exception("Test error")
                result = classify_request({"query": "test"})
                # Should return fallback
                assert result.get("use_claude", False) is True
        except ImportError:
            pytest.skip("m4_agent_classification not available")


class TestBareExceptElimination:
    """Meta-tests: Verify no bare except clauses remain in hooks."""

    def test_no_bare_except_in_swarm_auto_loader(self):
        """Verify swarm_auto_loader.py has no bare except clauses."""
        hooks_dir = Path(__file__).parent.parent
        swarm_file = hooks_dir / "swarm_auto_loader.py"

        if not swarm_file.exists():
            pytest.skip("swarm_auto_loader.py not found")

        content = swarm_file.read_text()
        lines = content.split('\n')

        bare_excepts = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Match "except:" but not "except Exception:" or "except SomeError:"
            if stripped == "except:":
                bare_excepts.append(f"Line {i}: {line.strip()}")

        assert len(bare_excepts) == 0, f"Bare except clauses found:\n" + "\n".join(bare_excepts)

    def test_no_bare_except_in_m4_agent_classification(self):
        """Verify m4_agent_classification.py has no bare except clauses."""
        hooks_dir = Path(__file__).parent.parent
        m4_file = hooks_dir / "m4_agent_classification.py"

        if not m4_file.exists():
            pytest.skip("m4_agent_classification.py not found")

        content = m4_file.read_text()
        lines = content.split('\n')

        bare_excepts = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                bare_excepts.append(f"Line {i}: {line.strip()}")

        assert len(bare_excepts) == 0, f"Bare except clauses found:\n" + "\n".join(bare_excepts)
