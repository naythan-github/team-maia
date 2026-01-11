"""
Tests for Feature 5.3: Claude API Integration Stub (F021)
Create the integration point for Claude API (actual API calls will be in Sprint 7).
"""

def test_api_wrapper_exists():
    """API wrapper module exists with required interface."""
    from claude.tools.orchestration.api_wrapper import ClaudeAPIWrapper

    wrapper = ClaudeAPIWrapper()
    assert hasattr(wrapper, 'execute_with_tools')
    assert hasattr(wrapper, 'set_mock_mode')

def test_api_wrapper_mock_mode():
    """API wrapper supports mock mode for testing."""
    from claude.tools.orchestration.api_wrapper import ClaudeAPIWrapper

    wrapper = ClaudeAPIWrapper(mock_mode=True)
    wrapper.set_mock_response({"content": [{"type": "text", "text": "Test response"}]})

    response = wrapper.execute_with_tools(
        prompt="Test prompt",
        tools=[],
        system="Test system"
    )

    assert response["content"][0]["text"] == "Test response"

def test_api_wrapper_formats_handoff_tools():
    """API wrapper formats handoff tools for Claude API."""
    from claude.tools.orchestration.api_wrapper import ClaudeAPIWrapper
    from claude.tools.orchestration.handoff_generator import generate_handoff_functions, generate_tool_schemas

    wrapper = ClaudeAPIWrapper(mock_mode=True)

    collaborations = [{"agent": "security_specialist", "specialty": "security"}]
    functions = generate_handoff_functions(collaborations)
    schemas = generate_tool_schemas(functions)

    # Format for API
    formatted = wrapper.format_tools_for_api(schemas)

    assert len(formatted) > 0
    assert formatted[0]["name"] == "transfer_to_security_specialist"
