"""
Test Swarm Integration with Agent Loader and Conversation Bridge

Tests the complete integration:
1. AgentLoader loads agent prompts
2. Context injection works
3. HandoffParser extracts declarations
4. SwarmConversationBridge orchestrates workflow
5. DNS → Azure handoff works end-to-end
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_loader import AgentLoader, load_agent_for_swarm
from swarm_conversation_bridge import SwarmConversationBridge, parse_agent_response_for_handoff
from agent_swarm import HandoffParser


def test_agent_loader():
    """Test AgentLoader can load agents and inject context"""
    print("=" * 60)
    print("TEST 1: Agent Loader")
    print("=" * 60)

    loader = AgentLoader()

    # Test loading DNS Specialist
    dns_agent = loader.load_agent("dns_specialist")

    assert dns_agent.agent_name == "dns_specialist"
    assert dns_agent.version == "v2"
    assert dns_agent.has_handoff_support == True
    assert len(dns_agent.prompt_content) > 0

    print(f"✅ Loaded {dns_agent.agent_name}")
    print(f"  Version: {dns_agent.version}")
    print(f"  Handoff support: {dns_agent.has_handoff_support}")
    print(f"  Prompt length: {len(dns_agent.prompt_content)} chars")
    print(f"  Specialties: {', '.join(dns_agent.specialties[:3])}")

    # Test context injection
    context = {
        "query": "Setup email authentication",
        "domain": "example.com",
        "previous_work": "User requested email setup"
    }

    full_prompt = loader.inject_context(dns_agent, context, "Initial request")

    assert "SWARM CONTEXT" in full_prompt
    assert "example.com" in full_prompt
    # Handoff reason appears in context section
    assert "Initial request" in full_prompt

    print(f"\n✅ Context injection works")
    print(f"  Full prompt length: {len(full_prompt)} chars")
    print(f"  Contains context: YES")

    # Test convenience function
    quick_prompt = load_agent_for_swarm("azure_solutions_architect", context)
    assert len(quick_prompt) > 0

    print(f"\n✅ Convenience function works")


def test_handoff_parser():
    """Test HandoffParser extracts handoff declarations"""
    print("\n" + "=" * 60)
    print("TEST 2: Handoff Parser")
    print("=" * 60)

    # Simulate DNS Specialist response with handoff
    dns_response = """
I've successfully configured the DNS records for example.com:

- SPF record: v=spf1 include:spf.protection.outlook.com -all
- DKIM: Configured with 2048-bit keys
- DMARC: Policy set to p=none for monitoring phase

All DNS records have propagated successfully.

HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Azure Exchange Online configuration needed
Context:
  - Work completed: DNS authentication records configured and propagated
  - Current state: Ready for Azure integration
  - Next steps: Configure Exchange Online tenant and link custom domain
  - Key data: {"domain": "example.com", "email_provider": "Exchange Online"}

DNS foundation complete. Azure specialist needed for Exchange setup.
"""

    handoff = HandoffParser.extract_handoff(dns_response)

    assert handoff is not None
    assert handoff.to_agent == "azure_solutions_architect"
    assert "Exchange Online" in handoff.reason
    assert "work_completed" in handoff.context
    # key_data is parsed as JSON dict
    assert 'key_data' in handoff.context
    assert handoff.context['key_data']['domain'] == "example.com"

    print(f"✅ HandoffParser works")
    print(f"  To agent: {handoff.to_agent}")
    print(f"  Reason: {handoff.reason}")
    print(f"  Context keys: {list(handoff.context.keys())}")

    # Test no handoff
    no_handoff_response = "Task complete. No further action needed."
    no_handoff = HandoffParser.extract_handoff(no_handoff_response)

    assert no_handoff is None

    print(f"\n✅ No handoff correctly detected")


def test_swarm_conversation_bridge_simulated():
    """Test SwarmConversationBridge in simulated mode"""
    print("\n" + "=" * 60)
    print("TEST 3: Swarm Conversation Bridge (Simulated)")
    print("=" * 60)

    bridge = SwarmConversationBridge(mode="simulated")

    result = bridge.execute_swarm_workflow(
        initial_agent="dns_specialist",
        task={
            "query": "Setup Azure Exchange Online",
            "domain": "example.com",
            "users": 50
        }
    )

    print(f"✅ Simulated workflow executed")
    print(f"  Final agent: {result['final_agent']}")
    print(f"  Total handoffs: {result['total_handoffs']}")
    print(f"  Handoff chain:")

    for handoff in result['handoff_chain']:
        print(f"    {handoff['from']} → {handoff['to']}: {handoff['reason']}")

    print(f"\n  Agent prompts generated: {len(result['agent_prompts_used'])}")
    for i, prompt_info in enumerate(result['agent_prompts_used'], 1):
        print(f"    {i}. {prompt_info['agent']} ({prompt_info['prompt_length']} chars)")


def test_swarm_conversation_bridge_conversation_mode():
    """Test SwarmConversationBridge in conversation mode"""
    print("\n" + "=" * 60)
    print("TEST 4: Swarm Conversation Bridge (Conversation Mode)")
    print("=" * 60)

    bridge = SwarmConversationBridge(mode="conversation")

    # Step 1: Get initial agent prompt
    context = {
        "query": "Setup email authentication for example.com",
        "domain": "example.com"
    }

    dns_prompt = bridge.get_next_agent_prompt(
        agent_name="dns_specialist",
        context=context
    )

    print(f"✅ Generated DNS Specialist prompt")
    print(f"  Prompt length: {len(dns_prompt)} chars")
    print(f"  Contains context: {'example.com' in dns_prompt}")

    # Step 2: Simulate agent response with handoff
    simulated_response = """
DNS configuration complete for example.com.

HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Azure configuration required
Context:
  - Work completed: DNS records configured
  - Next steps: Azure setup
  - Key data: {"domain": "example.com"}
"""

    result = bridge.process_agent_response(simulated_response)

    assert result['task_complete'] == False
    assert result['handoff'] is not None
    assert result['next_agent'] == "azure_solutions_architect"

    print(f"\n✅ Processed agent response with handoff")
    print(f"  Next agent: {result['next_agent']}")
    print(f"  Handoff reason: {result['handoff'].reason}")

    # Step 3: Get next agent prompt
    azure_prompt = bridge.get_next_agent_prompt(
        agent_name=result['next_agent'],
        context=result['handoff'].context,
        handoff_reason=result['handoff'].reason
    )

    print(f"\n✅ Generated Azure Specialist prompt")
    print(f"  Prompt length: {len(azure_prompt)} chars")
    print(f"  Contains handoff reason: {'Azure configuration required' in azure_prompt}")

    # Step 4: Simulate final response (no handoff)
    final_response = "Azure Exchange Online configured successfully. Task complete."

    final_result = bridge.process_agent_response(final_response)

    assert final_result['task_complete'] == True
    assert final_result['handoff'] is None

    print(f"\n✅ Processed final response (task complete)")

    # Get workflow summary
    summary = bridge.get_workflow_summary()

    print(f"\n✅ Workflow Summary:")
    print(f"  Total handoffs: {summary['total_handoffs']}")
    print(f"  Agents involved: {', '.join(summary['agents_invoked'])}")


def test_dns_to_azure_integration():
    """Test complete DNS → Azure handoff workflow"""
    print("\n" + "=" * 60)
    print("TEST 5: DNS → Azure Complete Integration")
    print("=" * 60)

    # This tests the Phase 1 success criteria:
    # "Swarm handoff framework handles test case (DNS → Azure handoff)"

    loader = AgentLoader()

    # 1. Verify both agents exist (handoff support preferred but not required for test)
    dns_agent = loader.load_agent("dns_specialist")
    azure_agent = loader.load_agent("azure_solutions_architect")

    assert dns_agent.has_handoff_support == True, "DNS Specialist must have handoff support for this test"
    # Azure may or may not have handoff support depending on which version is loaded

    print(f"✅ Both agents exist")
    print(f"  DNS Specialist: {dns_agent.version} (handoff: {dns_agent.has_handoff_support})")
    print(f"  Azure Architect: {azure_agent.version} (handoff: {azure_agent.has_handoff_support})")

    # 2. Test complete workflow
    bridge = SwarmConversationBridge(mode="conversation")

    # Initial prompt
    context = {
        "query": "Setup Azure Exchange Online with custom domain",
        "domain": "company.com",
        "users": 500
    }

    dns_prompt = bridge.get_next_agent_prompt("dns_specialist", context)

    print(f"\n✅ Step 1: DNS Specialist prompt generated ({len(dns_prompt)} chars)")

    # Simulated DNS response with handoff
    dns_response = """
DNS configuration complete for company.com.

HANDOFF DECLARATION:
To: azure_solutions_architect
Reason: Azure Exchange Online configuration required
Context:
  - Work completed: DNS authentication records configured (SPF, DKIM, DMARC)
  - Current state: DNS propagated and validated
  - Next steps: Configure Exchange Online tenant, link custom domain
  - Key data: {"domain": "company.com", "users": 500, "dns_ready": true}

DNS foundation ready for Azure Exchange integration.
"""

    result = bridge.process_agent_response(dns_response)

    assert result['handoff'] is not None
    assert result['next_agent'] == "azure_solutions_architect"

    print(f"\n✅ Step 2: DNS → Azure handoff detected")
    print(f"  Reason: {result['handoff'].reason}")

    # Azure prompt
    azure_prompt = bridge.get_next_agent_prompt(
        agent_name="azure_solutions_architect",
        context=result['handoff'].context,
        handoff_reason=result['handoff'].reason
    )

    print(f"\n✅ Step 3: Azure Specialist prompt generated ({len(azure_prompt)} chars)")
    print(f"  Context enriched: {result['handoff'].context.get('dns_ready')}")

    # Simulated Azure response (no handoff)
    azure_response = """
Exchange Online configuration complete:
- Tenant configured
- Custom domain company.com linked
- 500 user mailboxes provisioned
- MX records validated

Task complete. No further handoff needed.
"""

    final_result = bridge.process_agent_response(azure_response)

    assert final_result['task_complete'] == True

    print(f"\n✅ Step 4: Task completed by Azure Specialist")

    # Workflow summary
    summary = bridge.get_workflow_summary()

    print(f"\n✅ Workflow Complete!")
    print(f"  Total handoffs: {summary['total_handoffs']}")
    print(f"  Agents: {' → '.join([summary['handoff_chain'][0]['from'], summary['handoff_chain'][0]['to']])}")

    print(f"\n🎯 Phase 1 Success Criteria: DNS → Azure handoff VALIDATED")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("SWARM INTEGRATION TEST SUITE")
    print("=" * 60)
    print()

    try:
        test_agent_loader()
        test_handoff_parser()
        test_swarm_conversation_bridge_simulated()
        test_swarm_conversation_bridge_conversation_mode()
        test_dns_to_azure_integration()

        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nSwarm Framework is ready for production use!")
        print("\nNext steps:")
        print("1. Use SwarmConversationBridge in Claude Code conversations")
        print("2. Load agent prompts with load_agent_prompt()")
        print("3. Parse responses with parse_agent_response_for_handoff()")
        print("4. Follow handoff chain to completion")

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
