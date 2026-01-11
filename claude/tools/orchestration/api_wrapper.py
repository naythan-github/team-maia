"""
Feature 5.3: Claude API Integration Stub (F021)
Integration point for Claude API (actual API calls will be in Sprint 7).

This module provides:
- ClaudeAPIWrapper class with mock mode for testing
- Tool formatting for Claude API compatibility
- Placeholder for future API integration

Sprint 5: Stub implementation with mock mode
Sprint 7: Full API integration with Anthropic SDK
"""

from typing import Dict, List, Any, Optional


class ClaudeAPIWrapper:
    """
    Wrapper for Claude API interactions with handoff tool support.

    This is a stub implementation for Sprint 5. Sprint 7 will replace
    mock mode with actual Anthropic API calls.

    Attributes:
        mock_mode: If True, uses mock responses instead of API calls
        mock_response: Stored mock response for testing
    """

    def __init__(self, mock_mode: bool = False):
        """
        Initialize API wrapper.

        Args:
            mock_mode: Enable mock mode for testing (default: False)
        """
        self.mock_mode = mock_mode
        self.mock_response: Optional[Dict[str, Any]] = None

    def set_mock_mode(self, enabled: bool):
        """
        Enable or disable mock mode.

        Args:
            enabled: True to enable mock mode, False to disable
        """
        self.mock_mode = enabled

    def set_mock_response(self, response: Dict[str, Any]):
        """
        Set mock response for testing.

        Args:
            response: Mock response dict matching Claude API format
                     {
                         "content": [
                             {"type": "text", "text": "Response text"}
                         ]
                     }
        """
        self.mock_response = response

    def execute_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Execute a prompt with tool support.

        Sprint 5: Mock implementation
        Sprint 7: Will integrate with Anthropic SDK

        Args:
            prompt: User prompt/query
            tools: List of tool schemas (formatted for Claude API)
            system: System prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Claude API response format:
            {
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "tool_use", "name": "...", "input": {...}}
                ],
                "stop_reason": "end_turn" | "tool_use",
                "usage": {"input_tokens": ..., "output_tokens": ...}
            }

        Raises:
            NotImplementedError: If mock_mode is False (Sprint 7)
        """
        if self.mock_mode:
            # Return mock response if set
            if self.mock_response:
                return self.mock_response

            # Default mock response
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Mock response to: {prompt[:50]}..."
                    }
                ],
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50
                }
            }
        else:
            # Sprint 7: Implement actual API call
            raise NotImplementedError(
                "API integration not yet implemented. "
                "Use mock_mode=True for testing, or wait for Sprint 7."
            )

    def format_tools_for_api(
        self,
        tool_schemas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format handoff tool schemas for Claude API compatibility.

        Converts internal tool schema format to Claude API tool format.

        Args:
            tool_schemas: List of internal tool schemas from handoff_generator

        Returns:
            List of tools formatted for Claude API:
            [
                {
                    "name": "transfer_to_security_specialist",
                    "description": "...",
                    "input_schema": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                }
            ]
        """
        # Tool schemas from handoff_generator are already in Claude API format
        # This method exists for future format conversions if needed
        return tool_schemas
