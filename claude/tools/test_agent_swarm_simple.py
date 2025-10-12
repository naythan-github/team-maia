"""
Simple test for Swarm Handoff Framework (no pytest dependency)

Tests DNS → Azure handoff workflow as specified in
AGENT_EVOLUTION_PROJECT_PLAN.md Phase 1 success criteria
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_swarm import (
    SwarmOrchestrator,
    AgentHandoff,
    AgentResult,
    HandoffParser,
    MaxHandoffsExceeded,
    AgentNotFoundError
)


def test_agent_handoff():
    """Test basic handoff creation"""
    print("Testing AgentHandoff creation...")

    handoff = AgentHandoff(
        to_agent="azure_solutions_architect",
        context={"domain": "example.com"},
        reason="Need Azure configuration"
    )

    assert handoff.to_agent == "azure_solutions_architect"
    assert handoff.context["domain"] == "example.com"
    assert handoff.reason == "Need Azure configuration"
    assert handoff.timestamp is not None

    print("✅ AgentHandoff creation works")


def test_handoff_parser():
    """Test parsing handoff declarations"""
    print("\nTesting HandoffParser...")

    agent_output = """
Some agent output here.

HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Need Azure DNS configuration
Context:
  - Work completed: SPF/DKIM/DMARC records generated
  - Current state: DNS records ready for implementation
  - Next steps: Configure Azure DNS zones
  - Key data: {"domain": "example.com", "tenant": "client.onmicrosoft.com"}

More output after handoff.
"""

    handoff = HandoffParser.extract_handoff(agent_output)

    assert handoff is not None
    assert handoff.to_agent == "azure_solutions_architect"
    assert handoff.reason == "Need Azure DNS configuration"
    assert "work_completed" in handoff.context

    print("✅ HandoffParser works")


def test_agent_registry():
    """Test loading agents from claude/agents/"""
    print("\nTesting Agent Registry...")

    orchestrator = SwarmOrchestrator()

    # Should load agents
    assert len(orchestrator.agent_registry) > 0
    print(f"  Loaded {len(orchestrator.agent_registry)} agents")

    # Should have agents with handoff support
    assert "dns_specialist" in orchestrator.agent_registry
    assert "azure_solutions_architect" in orchestrator.agent_registry

    # Check agent metadata
    dns_agent = orchestrator.agent_registry["dns_specialist"]
    # Version may be 'v2' or 'base' depending on naming convention
    assert dns_agent['version'] in ['v2', 'base', 'v1']
    assert dns_agent['path'].exists()

    print(f"✅ Agent Registry works - {len(orchestrator.agent_registry)} agents loaded")
    print(f"  DNS Specialist: {dns_agent['file']}")
    print(f"  Azure Architect: {orchestrator.agent_registry['azure_solutions_architect']['file']}")


def test_agent_name_extraction():
    """Test agent name extraction from filename"""
    print("\nTesting agent name extraction...")

    orchestrator = SwarmOrchestrator()

    tests = [
        ("dns_specialist_agent_v2", "dns_specialist"),
        ("azure_solutions_architect_agent", "azure_solutions_architect"),
        ("sre_principal_engineer_agent_v2", "sre_principal_engineer"),
    ]

    for input_name, expected_output in tests:
        result = orchestrator._extract_agent_name(input_name)
        assert result == expected_output, f"Expected {expected_output}, got {result}"

    print("✅ Agent name extraction works")


def test_dns_to_azure_workflow():
    """
    Test DNS → Azure handoff workflow structure

    As specified in AGENT_EVOLUTION_PROJECT_PLAN.md Phase 1:
    "Swarm handoff framework handles test case (DNS → Azure handoff)"
    """
    print("\nTesting DNS → Azure Handoff Workflow...")

    orchestrator = SwarmOrchestrator()

    # Verify both agents exist and have handoff support
    assert "dns_specialist" in orchestrator.agent_registry
    assert "azure_solutions_architect" in orchestrator.agent_registry

    dns_agent = orchestrator.agent_registry["dns_specialist"]
    azure_agent = orchestrator.agent_registry["azure_solutions_architect"]

    # Both should have handoff support (version flexible)
    assert dns_agent['version'] in ['v2', 'base', 'v1'], f"DNS agent version: {dns_agent['version']}"
    assert azure_agent['version'] in ['v2', 'base', 'v1'], f"Azure agent version: {azure_agent['version']}"

    # Verify agent files exist
    assert dns_agent['path'].exists()
    assert azure_agent['path'].exists()

    print(f"  ✓ DNS Specialist agent exists ({dns_agent['version']})")
    print(f"  ✓ Azure Solutions Architect agent exists ({azure_agent['version']})")

    # Verify DNS agent has handoff triggers to Azure
    with open(dns_agent['path'], 'r') as f:
        dns_content = f.read()

    assert "Integration Points" in dns_content
    assert "Explicit Handoff Declaration" in dns_content
    assert "azure_solutions_architect" in dns_content.lower()
    assert "HANDOFF DECLARATION:" in dns_content

    print("  ✓ DNS agent has handoff triggers to Azure")
    print("✅ DNS → Azure workflow structure validated")


def test_handoff_stats():
    """Test handoff statistics tracking"""
    print("\nTesting handoff statistics...")

    orchestrator = SwarmOrchestrator()

    # Add some mock handoff history
    orchestrator.handoff_history = [
        {
            "from": "dns_specialist",
            "to": "azure_solutions_architect",
            "reason": "Azure config needed",
            "context_size": 500,
            "timestamp": "2025-01-15T10:00:00"
        },
        {
            "from": "dns_specialist",
            "to": "azure_solutions_architect",
            "reason": "Another Azure task",
            "context_size": 600,
            "timestamp": "2025-01-15T11:00:00"
        },
        {
            "from": "azure_solutions_architect",
            "to": "cloud_security_principal",
            "reason": "Security review",
            "context_size": 800,
            "timestamp": "2025-01-15T12:00:00"
        }
    ]

    stats = orchestrator.get_handoff_stats()

    assert stats['total_handoffs'] == 3
    assert stats['unique_paths'] == 2
    assert len(stats['most_common_handoffs']) == 2

    # Most common should be dns → azure (2 times)
    most_common = stats['most_common_handoffs'][0]
    assert most_common['from'] == "dns_specialist"
    assert most_common['to'] == "azure_solutions_architect"
    assert most_common['count'] == 2

    print(f"  Total handoffs: {stats['total_handoffs']}")
    print(f"  Unique paths: {stats['unique_paths']}")
    print(f"  Most common: {most_common['from']} → {most_common['to']} ({most_common['count']}x)")
    print("✅ Handoff statistics tracking works")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("SWARM HANDOFF FRAMEWORK TEST SUITE")
    print("=" * 60)

    try:
        test_agent_handoff()
        test_handoff_parser()
        test_agent_registry()
        test_agent_name_extraction()
        test_dns_to_azure_workflow()
        test_handoff_stats()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSwarm Handoff Framework is ready for integration!")
        print("\nNext steps:")
        print("1. Integrate with Maia agent execution system")
        print("2. Replace _call_agent_with_context stub with actual agent invocation")
        print("3. Test with real agent workflows")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
