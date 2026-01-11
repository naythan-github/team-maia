"""
Test suite for automatic agent handoff generator (Sprint 1).

Tests the generation of transfer_to_X functions from agent metadata.
"""

import pytest
from claude.tools.orchestration.handoff_generator import (
    parse_agent_collaborations,
    generate_handoff_functions,
    generate_tool_schemas,
    build_handoff_context,
    AgentRegistry,
)


class TestAgentCollaborationParser:
    """Feature 1.1: Parse agent markdown to extract collaboration partners."""

    def test_parse_agent_collaborations(self):
        """Extract collaboration partners from agent markdown."""
        agent_content = '''
        ## Integration Points
        **Collaborations**: Python Code Reviewer (code quality), DevOps Principal (CI/CD), Cloud Security Principal (security)
        '''
        result = parse_agent_collaborations(agent_content)
        assert result == [
            {"agent": "python_code_reviewer", "specialty": "code quality"},
            {"agent": "devops_principal", "specialty": "CI/CD"},
            {"agent": "cloud_security_principal", "specialty": "security"}
        ]

    def test_parse_collaborations_with_agent_suffix(self):
        """Handle agent names with _agent suffix."""
        agent_content = '''
        ## Integration Points
        **Collaborations**: Python Code Reviewer Agent (code quality)
        '''
        result = parse_agent_collaborations(agent_content)
        assert result == [
            {"agent": "python_code_reviewer_agent", "specialty": "code quality"}
        ]

    def test_parse_no_collaborations(self):
        """Return empty list if no collaborations found."""
        agent_content = '''
        ## Integration Points
        **Dependencies**: Some other section
        '''
        result = parse_agent_collaborations(agent_content)
        assert result == []

    def test_parse_empty_collaborations(self):
        """Handle empty collaborations section."""
        agent_content = '''
        ## Integration Points
        **Collaborations**: None
        '''
        result = parse_agent_collaborations(agent_content)
        assert result == []

    def test_parse_single_collaboration(self):
        """Parse single collaboration entry."""
        agent_content = '''
        ## Integration Points
        **Collaborations**: Azure Architect (Azure infrastructure)
        '''
        result = parse_agent_collaborations(agent_content)
        assert result == [
            {"agent": "azure_architect", "specialty": "Azure infrastructure"}
        ]


class TestHandoffFunctionFactory:
    """Feature 1.2: Generate callable handoff functions from collaborations."""

    def test_generate_handoff_functions(self):
        """Generate transfer_to_X functions from collaborations."""
        collaborations = [
            {"agent": "security_specialist", "specialty": "security audits"}
        ]
        functions = generate_handoff_functions(collaborations)

        assert len(functions) == 1
        assert functions[0].__name__ == "transfer_to_security_specialist"
        assert "security audits" in functions[0].__doc__

        # Function returns handoff structure
        result = functions[0]()
        assert result["handoff_to"] == "security_specialist"

    def test_handoff_function_with_context(self):
        """Handoff function accepts context parameter."""
        collaborations = [
            {"agent": "azure_architect", "specialty": "Azure infrastructure"}
        ]
        functions = generate_handoff_functions(collaborations)

        context = {"query": "Setup Azure DNS", "domain": "example.com"}
        result = functions[0](context=context)

        assert result["handoff_to"] == "azure_architect"
        assert result["context"] == context

    def test_generate_multiple_handoff_functions(self):
        """Generate multiple handoff functions."""
        collaborations = [
            {"agent": "security_specialist", "specialty": "security"},
            {"agent": "devops_principal", "specialty": "CI/CD"}
        ]
        functions = generate_handoff_functions(collaborations)

        assert len(functions) == 2
        function_names = [f.__name__ for f in functions]
        assert "transfer_to_security_specialist" in function_names
        assert "transfer_to_devops_principal" in function_names

    def test_handoff_function_includes_specialty_in_doc(self):
        """Function docstring includes specialty for LLM guidance."""
        collaborations = [
            {"agent": "python_code_reviewer", "specialty": "code quality"}
        ]
        functions = generate_handoff_functions(collaborations)

        assert "python_code_reviewer" in functions[0].__doc__
        assert "code quality" in functions[0].__doc__


class TestAgentRegistryEnhancement:
    """Feature 1.3: Extend agent registry with handoff capabilities."""

    def test_registry_includes_handoff_tools(self):
        """Agent registry includes generated handoff tools."""
        registry = AgentRegistry()
        agent = registry.get("sre_principal_engineer")

        assert "handoff_tools" in agent
        assert len(agent["handoff_tools"]) > 0
        # SRE Principal collaborates with Python Code Reviewer
        assert any(
            t.__name__ == "transfer_to_python_code_reviewer"
            for t in agent["handoff_tools"]
        )

    def test_registry_caches_handoff_tools(self):
        """Registry caches handoff tools for performance."""
        registry = AgentRegistry()

        # First access
        agent1 = registry.get("sre_principal_engineer")
        tools1 = agent1["handoff_tools"]

        # Second access should return same objects
        agent2 = registry.get("sre_principal_engineer")
        tools2 = agent2["handoff_tools"]

        assert tools1 is tools2  # Same object reference (cached)

    def test_registry_handles_agent_without_collaborations(self):
        """Registry handles agents with no collaborations."""
        registry = AgentRegistry()
        # Create mock agent with no collaborations
        agent = registry.get_with_content(
            "test_agent",
            "## Integration Points\n**Dependencies**: None"
        )

        assert "handoff_tools" in agent
        assert agent["handoff_tools"] == []

    def test_handoff_tools_are_callable(self):
        """Handoff tools in registry are callable."""
        registry = AgentRegistry()
        agent = registry.get("sre_principal_engineer")

        for tool in agent["handoff_tools"]:
            assert callable(tool)
            result = tool()
            assert "handoff_to" in result


class TestHandoffToolSchemaGeneration:
    """Feature 1.4: Generate OpenAI-compatible tool schemas for Claude."""

    def test_generate_tool_schemas(self):
        """Generate tool schemas for Claude API."""
        functions = generate_handoff_functions([
            {"agent": "azure_architect", "specialty": "Azure infrastructure"}
        ])
        schemas = generate_tool_schemas(functions)

        assert len(schemas) == 1
        assert schemas[0]["name"] == "transfer_to_azure_architect"
        assert "Azure infrastructure" in schemas[0]["description"]
        assert schemas[0]["input_schema"]["type"] == "object"

    def test_schema_includes_context_parameter(self):
        """Schema includes context parameter definition."""
        functions = generate_handoff_functions([
            {"agent": "security_specialist", "specialty": "security"}
        ])
        schemas = generate_tool_schemas(functions)

        schema = schemas[0]
        assert "properties" in schema["input_schema"]
        assert "context" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["properties"]["context"]["type"] == "object"

    def test_schema_validates_against_claude_spec(self):
        """Schema structure matches Claude API requirements."""
        functions = generate_handoff_functions([
            {"agent": "devops_principal", "specialty": "CI/CD"}
        ])
        schemas = generate_tool_schemas(functions)

        schema = schemas[0]
        # Required Claude tool schema fields
        assert "name" in schema
        assert "description" in schema
        assert "input_schema" in schema
        assert schema["input_schema"]["type"] == "object"
        assert "properties" in schema["input_schema"]

    def test_multiple_schemas_generation(self):
        """Generate multiple tool schemas."""
        functions = generate_handoff_functions([
            {"agent": "azure_architect", "specialty": "Azure"},
            {"agent": "security_specialist", "specialty": "security"}
        ])
        schemas = generate_tool_schemas(functions)

        assert len(schemas) == 2
        schema_names = [s["name"] for s in schemas]
        assert "transfer_to_azure_architect" in schema_names
        assert "transfer_to_security_specialist" in schema_names


class TestHandoffContextBuilder:
    """Feature 1.5: Build enriched context for handoff."""

    def test_build_handoff_context(self):
        """Build context object for handoff."""
        current_context = {"query": "Setup Azure DNS", "domain": "example.com"}
        agent_output = "Configured public DNS. Need Azure Private DNS."

        enriched = build_handoff_context(
            current_context=current_context,
            agent_output=agent_output,
            source_agent="dns_specialist",
            handoff_reason="Azure infrastructure needed"
        )

        assert enriched["previous_agent"] == "dns_specialist"
        assert enriched["handoff_reason"] == "Azure infrastructure needed"
        assert "agent_output" in enriched
        assert enriched["query"] == "Setup Azure DNS"  # Preserved
        assert enriched["domain"] == "example.com"  # Preserved

    def test_context_includes_timestamp(self):
        """Context includes timestamp for tracking."""
        enriched = build_handoff_context(
            current_context={},
            agent_output="Output",
            source_agent="test_agent",
            handoff_reason="test"
        )

        assert "handoff_timestamp" in enriched
        assert isinstance(enriched["handoff_timestamp"], str)

    def test_context_truncates_long_output(self):
        """Truncate agent output if too long."""
        long_output = "x" * 10000
        enriched = build_handoff_context(
            current_context={},
            agent_output=long_output,
            source_agent="test_agent",
            handoff_reason="test"
        )

        # Should be truncated to reasonable length (e.g., 2000 chars)
        assert len(enriched["agent_output"]) <= 2000

    def test_context_preserves_original_fields(self):
        """All original context fields are preserved."""
        current_context = {
            "query": "test",
            "custom_field": "value",
            "nested": {"data": "here"}
        }
        enriched = build_handoff_context(
            current_context=current_context,
            agent_output="Output",
            source_agent="test_agent",
            handoff_reason="test"
        )

        assert enriched["query"] == "test"
        assert enriched["custom_field"] == "value"
        assert enriched["nested"]["data"] == "here"

    def test_context_handles_empty_agent_output(self):
        """Handle empty agent output gracefully."""
        enriched = build_handoff_context(
            current_context={"query": "test"},
            agent_output="",
            source_agent="test_agent",
            handoff_reason="test"
        )

        assert enriched["agent_output"] == ""
        assert "previous_agent" in enriched
