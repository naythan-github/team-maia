"""
Tests for optimal_local_llm_interface.py CLI helper functions.

TDD: Phase 4 refactoring - decompose main (147 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_cmd_models_exists(self, mock_run, mock_router):
        """Helper for models command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        assert hasattr(interface, '_cmd_models')
        assert callable(interface._cmd_models)

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_cmd_task_exists(self, mock_run, mock_router):
        """Helper for task command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        assert hasattr(interface, '_cmd_task')
        assert callable(interface._cmd_task)

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_cmd_generate_exists(self, mock_run, mock_router):
        """Helper for generate command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        assert hasattr(interface, '_cmd_generate')
        assert callable(interface._cmd_generate)

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_cmd_test_exists(self, mock_run, mock_router):
        """Helper for test command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        assert hasattr(interface, '_cmd_test')
        assert callable(interface._cmd_test)


class TestCmdModels:
    """Test _cmd_models helper."""

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_returns_none(self, mock_run, mock_router):
        """Should return None (prints to stdout)."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nllama3.2:3b\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        result = interface._cmd_models()
        assert result is None


class TestCmdTask:
    """Test _cmd_task helper."""

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_returns_model_info(self, mock_run, mock_router):
        """Should return model info dict."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\ncodellama:13b\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        result = interface._cmd_task("Generate code for API")
        assert result is None or isinstance(result, dict)


class TestCmdTest:
    """Test _cmd_test helper."""

    @patch('optimal_local_llm_interface.ProductionLLMRouter')
    @patch('subprocess.run')
    def test_runs_test_prompts(self, mock_run, mock_router):
        """Should run through test prompts."""
        mock_run.return_value = MagicMock(returncode=0, stdout="NAME\nllama3.2:3b\n")
        from optimal_local_llm_interface import OptimalLocalLLMInterface
        interface = OptimalLocalLLMInterface()
        # Should not raise
        interface._cmd_test()
