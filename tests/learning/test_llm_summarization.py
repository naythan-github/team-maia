#!/usr/bin/env python3
"""
Tests for P4: LLM Summarization - Extract key decisions using local LLM (TDD)

Phase 234: Use Ollama to generate richer session summaries and key decisions.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestLLMSummarizerBasic:
    """Tests for basic LLM summarizer functionality."""

    def test_summarizer_initializes(self):
        """Test that LLMSummarizer initializes correctly."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()
        assert summarizer is not None

    def test_summarizer_has_default_model(self):
        """Test that summarizer has a default model configured."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()
        assert summarizer.model is not None
        assert len(summarizer.model) > 0

    def test_summarizer_accepts_custom_model(self):
        """Test that summarizer accepts custom model parameter."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer(model="llama3.2:3b")
        assert summarizer.model == "llama3.2:3b"


class TestKeyDecisionExtraction:
    """Tests for extracting key decisions from session data."""

    def test_extract_decisions_returns_list(self):
        """Test that extract_decisions returns a list."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.return_value = "1. Used caching for performance\n2. Added error handling"

            session_data = {
                'initial_query': 'Fix the slow API',
                'tools_used': {'bash': 5, 'read': 10, 'edit': 3},
                'files_touched': ['api.py', 'cache.py']
            }

            decisions = summarizer.extract_decisions(session_data)

            assert isinstance(decisions, list)
            assert len(decisions) >= 1

    def test_extract_decisions_parses_numbered_list(self):
        """Test that extract_decisions parses numbered list from LLM."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.return_value = """1. Added Redis caching layer
2. Implemented connection pooling
3. Fixed N+1 query pattern"""

            decisions = summarizer.extract_decisions({'initial_query': 'test'})

            assert len(decisions) == 3
            assert "Redis caching" in decisions[0]
            assert "connection pooling" in decisions[1]

    def test_extract_decisions_handles_empty_response(self):
        """Test graceful handling of empty LLM response."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.return_value = ""

            decisions = summarizer.extract_decisions({'initial_query': 'test'})

            assert isinstance(decisions, list)
            assert len(decisions) == 0

    def test_extract_decisions_handles_ollama_error(self):
        """Test graceful handling of Ollama errors."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama not running")

            decisions = summarizer.extract_decisions({'initial_query': 'test'})

            # Should return empty list, not raise
            assert decisions == []


class TestSummaryGeneration:
    """Tests for generating session summaries."""

    def test_generate_summary_returns_string(self):
        """Test that generate_summary returns a string."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.return_value = "Fixed performance issues by adding caching."

            session_data = {
                'initial_query': 'Fix the slow API',
                'tools_used': {'bash': 5},
                'files_touched': ['api.py']
            }

            summary = summarizer.generate_summary(session_data)

            assert isinstance(summary, str)
            assert len(summary) > 0

    def test_generate_summary_includes_context(self):
        """Test that summary generation uses session context."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch.object(summarizer, '_call_ollama') as mock_ollama:
            mock_ollama.return_value = "Summary text"

            session_data = {
                'initial_query': 'Fix authentication bug',
                'tools_used': {'read': 5, 'edit': 2},
                'files_touched': ['auth.py', 'login.py'],
                'agent_used': 'security_agent'
            }

            summarizer.generate_summary(session_data)

            # Verify prompt included relevant context
            call_args = mock_ollama.call_args[0][0]
            assert 'authentication' in call_args.lower() or 'auth' in call_args.lower()


class TestOllamaIntegration:
    """Tests for Ollama API integration."""

    def test_call_ollama_sends_correct_request(self):
        """Test that _call_ollama sends correct API request."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer(model="llama3.2:3b")

        with patch('ollama.generate') as mock_generate:
            mock_generate.return_value = {'response': 'Test response'}

            result = summarizer._call_ollama("Test prompt")

            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args[1]
            assert call_kwargs['model'] == "llama3.2:3b"
            assert call_kwargs['prompt'] == "Test prompt"

    def test_call_ollama_returns_response_text(self):
        """Test that _call_ollama returns response text."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch('ollama.generate') as mock_generate:
            mock_generate.return_value = {'response': 'Generated text here'}

            result = summarizer._call_ollama("Test prompt")

            assert result == 'Generated text here'

    def test_is_available_returns_true_when_ollama_running(self):
        """Test is_available returns True when Ollama is accessible."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch('ollama.list') as mock_list:
            mock_list.return_value = {'models': [{'name': 'llama3.2:3b'}]}

            assert summarizer.is_available() is True

    def test_is_available_returns_false_when_ollama_down(self):
        """Test is_available returns False when Ollama is not accessible."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        with patch('ollama.list') as mock_list:
            mock_list.side_effect = Exception("Connection refused")

            assert summarizer.is_available() is False


class TestPromptTemplates:
    """Tests for prompt template generation."""

    def test_decision_prompt_includes_session_data(self):
        """Test that decision extraction prompt includes session data."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        session_data = {
            'initial_query': 'Add user authentication',
            'tools_used': {'bash': 3, 'read': 5, 'edit': 2},
            'files_touched': ['auth.py', 'user.py', 'login.py']
        }

        prompt = summarizer._build_decision_prompt(session_data)

        assert 'authentication' in prompt.lower()
        assert 'auth.py' in prompt
        assert 'edit' in prompt.lower()

    def test_summary_prompt_is_concise(self):
        """Test that summary prompt requests concise output."""
        from claude.tools.learning.llm_summarizer import LLMSummarizer

        summarizer = LLMSummarizer()

        prompt = summarizer._build_summary_prompt({'initial_query': 'test'})

        assert 'concise' in prompt.lower() or 'brief' in prompt.lower() or '1-2' in prompt


class TestModelSelection:
    """Tests for automatic model selection."""

    def test_get_best_available_model(self):
        """Test that get_best_available_model returns a valid model."""
        from claude.tools.learning.llm_summarizer import get_best_available_model

        with patch('ollama.list') as mock_list:
            mock_list.return_value = {
                'models': [
                    {'name': 'llama3.2:3b'},
                    {'name': 'mistral:7b'},
                    {'name': 'nomic-embed-text:latest'}
                ]
            }

            model = get_best_available_model()

            # Should pick a text generation model, not embedding
            assert model is not None
            assert 'embed' not in model

    def test_get_best_available_model_prefers_instruction_tuned(self):
        """Test that instruction-tuned models are preferred."""
        from claude.tools.learning.llm_summarizer import get_best_available_model

        with patch('ollama.list') as mock_list:
            mock_list.return_value = {
                'models': [
                    {'name': 'llama3.2:3b'},
                    {'name': 'qwen2.5:7b-instruct'},
                    {'name': 'mistral:7b'}
                ]
            }

            model = get_best_available_model()

            # Should prefer instruct model
            assert 'instruct' in model or model in ['llama3.2:3b', 'llama3.1:8b']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
