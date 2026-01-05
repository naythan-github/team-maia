#!/usr/bin/env python3
"""
LLM Summarization Module

Phase 234: Use Ollama to generate richer session summaries and extract key decisions.
"""

import re
from typing import Dict, Any, List, Optional

# Try to import ollama at module level (avoids repeated import overhead)
try:
    import ollama as _ollama
    _HAS_OLLAMA = True
except ImportError:
    _ollama = None
    _HAS_OLLAMA = False

# Model preference order (instruction-tuned and fast models first)
MODEL_PREFERENCE = [
    'qwen2.5:7b-instruct',
    'llama3.1:8b',
    'llama3.2:3b',
    'mistral:7b',
    'gemma2:9b',
    'phi3:mini',
]


def get_best_available_model() -> Optional[str]:
    """
    Get the best available Ollama model for summarization.

    Prefers instruction-tuned models, excludes embedding models.

    Returns:
        Model name or None if no suitable model available
    """
    if not _HAS_OLLAMA:
        return None

    try:
        result = _ollama.list()
        available = {m['name'] for m in result.get('models', [])}

        # Filter out embedding models
        available = {m for m in available if 'embed' not in m.lower()}

        # Return first available from preference list
        for model in MODEL_PREFERENCE:
            if model in available:
                return model

        # Fallback to any available model
        if available:
            return next(iter(available))

        return None
    except Exception:
        return None


class LLMSummarizer:
    """Uses Ollama to generate session summaries and extract key decisions."""

    DEFAULT_MODEL = 'llama3.2:3b'

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the summarizer.

        Args:
            model: Ollama model to use. If None, auto-selects best available.
        """
        if model:
            self.model = model
        else:
            self.model = get_best_available_model() or self.DEFAULT_MODEL

    def is_available(self) -> bool:
        """Check if Ollama is available and running."""
        if not _HAS_OLLAMA:
            return False
        try:
            _ollama.list()
            return True
        except Exception:
            return False

    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API with prompt.

        Args:
            prompt: The prompt to send

        Returns:
            Response text from the model

        Raises:
            ImportError: If ollama is not installed
        """
        if not _HAS_OLLAMA:
            raise ImportError("ollama package not installed")

        response = _ollama.generate(
            model=self.model,
            prompt=prompt,
            options={
                'temperature': 0.3,  # Lower for more focused output
                'num_predict': 500,  # Limit output length
            }
        )

        return response.get('response', '')

    def _build_decision_prompt(self, session_data: Dict[str, Any]) -> str:
        """Build prompt for extracting key decisions."""
        query = session_data.get('initial_query', 'Unknown task')
        tools = session_data.get('tools_used', {})
        files = session_data.get('files_touched', [])
        agent = session_data.get('agent_used', '')

        tools_str = ', '.join(f"{t}({c}x)" for t, c in tools.items()) if tools else 'None'
        files_str = ', '.join(files[:10]) if files else 'None'  # Limit to 10 files

        return f"""Extract the key technical decisions from this coding session.

Task: {query}
Agent: {agent or 'General'}
Tools used: {tools_str}
Files touched: {files_str}

List 1-5 key technical decisions made during this session. Each should be:
- A specific technical choice (not just "fixed bug")
- Actionable and reusable knowledge
- Written as a single line

Format: numbered list (1. Decision one, 2. Decision two, etc.)
If no clear decisions can be extracted, return an empty response.

Key decisions:"""

    def _build_summary_prompt(self, session_data: Dict[str, Any]) -> str:
        """Build prompt for generating session summary."""
        query = session_data.get('initial_query', 'Unknown task')
        tools = session_data.get('tools_used', {})
        files = session_data.get('files_touched', [])

        return f"""Write a concise 1-2 sentence summary of this coding session.

Task: {query}
Tools used: {', '.join(tools.keys()) if tools else 'None'}
Files modified: {len(files)} files

Summary should describe what was accomplished, not how.
Be brief and specific.

Summary:"""

    def extract_decisions(self, session_data: Dict[str, Any]) -> List[str]:
        """
        Extract key decisions from session data using LLM.

        Args:
            session_data: Dictionary with initial_query, tools_used, files_touched, etc.

        Returns:
            List of key decision strings
        """
        try:
            prompt = self._build_decision_prompt(session_data)
            response = self._call_ollama(prompt)

            if not response.strip():
                return []

            return self._parse_numbered_list(response)
        except Exception:
            return []

    def _parse_numbered_list(self, text: str) -> List[str]:
        """Parse a numbered list from LLM output."""
        decisions = []

        # Match numbered items: "1. text", "1) text", "- text"
        patterns = [
            r'^\d+[\.\)]\s*(.+)$',
            r'^-\s*(.+)$',
            r'^\*\s*(.+)$',
        ]

        for line in text.strip().split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    decision = match.group(1).strip()
                    if decision and len(decision) > 5:  # Filter trivial entries
                        decisions.append(decision)
                    break

        return decisions

    def generate_summary(self, session_data: Dict[str, Any]) -> str:
        """
        Generate a concise session summary using LLM.

        Args:
            session_data: Dictionary with session information

        Returns:
            Summary string
        """
        try:
            prompt = self._build_summary_prompt(session_data)
            response = self._call_ollama(prompt)

            # Clean up response
            summary = response.strip()

            # Take first 1-2 sentences
            sentences = re.split(r'[.!?]+', summary)
            if sentences:
                summary = '. '.join(s.strip() for s in sentences[:2] if s.strip())
                if summary and not summary.endswith('.'):
                    summary += '.'

            return summary or "Session completed."
        except Exception:
            return "Session completed."


# Singleton
_summarizer: Optional[LLMSummarizer] = None


def get_summarizer() -> LLMSummarizer:
    """Get LLMSummarizer singleton."""
    global _summarizer
    if _summarizer is None:
        _summarizer = LLMSummarizer()
    return _summarizer


__all__ = ["LLMSummarizer", "get_summarizer", "get_best_available_model"]
