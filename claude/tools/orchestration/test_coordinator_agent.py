"""
Coordinator Agent Test Suite

Tests intent classification, agent selection, and routing decisions
across various query types and complexity levels.

Test Coverage:
- Intent classification (domains, categories, complexity)
- Entity extraction (domains, emails, numbers)
- Agent selection (single, swarm, complex)
- Routing confidence and reasoning
- Edge cases and fallbacks
"""

import sys
from pathlib import Path

# Add orchestration directory to path
sys.path.insert(0, str(Path(__file__).parent))

from coordinator_agent import (
    CoordinatorAgent,
    IntentClassifier,
    AgentSelector,
    Intent,
    RoutingDecision
)


class TestIntentClassifier:
    """Test suite for IntentClassifier"""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.passed = 0
        self.failed = 0

    def test_simple_dns_query(self):
        """Test 1: Simple DNS query - single domain, technical question"""
        query = "How do I configure SPF records for my domain?"
        intent = self.classifier.classify(query)

        assert 'dns' in intent.domains, f"Expected 'dns' in domains, got {intent.domains}"
        assert intent.category == 'technical_question', f"Expected 'technical_question', got {intent.category}"
        assert intent.complexity <= 4, f"Expected low complexity, got {intent.complexity}"
        assert intent.confidence >= 0.7, f"Expected high confidence, got {intent.confidence}"

        print("✅ Test 1: Simple DNS query - PASSED")
        self.passed += 1

    def test_azure_migration_query(self):
        """Test 2: Azure migration - high complexity, multiple domains"""
        query = "I need to migrate 250 users from on-prem Exchange to Exchange Online with minimal downtime"
        intent = self.classifier.classify(query)

        assert 'azure' in intent.domains, f"Expected 'azure' in domains, got {intent.domains}"
        assert intent.complexity >= 7, f"Expected high complexity (migration + scale), got {intent.complexity}"
        assert 'numbers' in intent.entities, f"Expected number extraction, got {intent.entities}"

        # Check for 250 users extracted
        user_count = next((n for n in intent.entities.get('numbers', []) if n['value'] == 250), None)
        assert user_count is not None, f"Expected 250 users extracted, got {intent.entities.get('numbers')}"

        print("✅ Test 2: Azure migration query - PASSED")
        self.passed += 1

    def test_multi_domain_security_query(self):
        """Test 3: Multi-domain security and DNS query"""
        query = "Setup email authentication (SPF, DKIM, DMARC) and audit security compliance for example.com"
        intent = self.classifier.classify(query)

        # Should detect both DNS and security domains
        assert len(intent.domains) >= 2, f"Expected multiple domains, got {intent.domains}"
        assert 'dns' in intent.domains or 'security' in intent.domains, f"Expected dns/security, got {intent.domains}"

        # Should extract domain name
        assert 'domains' in intent.entities, f"Expected domain extraction, got {intent.entities}"
        assert 'example.com' in intent.entities['domains'], f"Expected example.com, got {intent.entities['domains']}"

        print("✅ Test 3: Multi-domain security query - PASSED")
        self.passed += 1

    def test_financial_planning_query(self):
        """Test 4: Financial planning - strategic category"""
        query = "Should I invest $50000 in super or invest in property?"
        intent = self.classifier.classify(query)

        assert 'financial' in intent.domains, f"Expected 'financial', got {intent.domains}"
        assert intent.category == 'strategic_planning', f"Expected 'strategic_planning', got {intent.category}"

        # Check for $50000 extraction
        if 'numbers' in intent.entities:
            amount = next((n for n in intent.entities['numbers'] if n['value'] == 50000), None)
            assert amount is not None, f"Expected 50000 extracted, got {intent.entities['numbers']}"

        print("✅ Test 4: Financial planning query - PASSED")
        self.passed += 1

    def test_operational_task_query(self):
        """Test 5: Operational task - configure/setup pattern"""
        query = "Configure Azure AD authentication for my web app"
        intent = self.classifier.classify(query)

        assert 'azure' in intent.domains, f"Expected 'azure', got {intent.domains}"
        assert intent.category == 'operational_task', f"Expected 'operational_task', got {intent.category}"

        print("✅ Test 5: Operational task query - PASSED")
        self.passed += 1

    def test_analysis_research_query(self):
        """Test 6: Analysis/research category"""
        query = "Analyze our cloud costs and compare Azure vs AWS pricing"
        intent = self.classifier.classify(query)

        assert intent.category == 'analysis_research', f"Expected 'analysis_research', got {intent.category}"
        assert 'cloud' in intent.domains or 'azure' in intent.domains, f"Expected cloud/azure, got {intent.domains}"

        print("✅ Test 6: Analysis research query - PASSED")
        self.passed += 1

    def test_urgent_query(self):
        """Test 7: Urgent query increases complexity"""
        query = "URGENT: Fix broken email authentication ASAP"
        intent = self.classifier.classify(query)

        assert intent.complexity >= 4, f"Expected urgency to increase complexity, got {intent.complexity}"
        assert 'dns' in intent.domains, f"Expected 'dns' (email auth), got {intent.domains}"

        print("✅ Test 7: Urgent query complexity - PASSED")
        self.passed += 1

    def test_general_query_fallback(self):
        """Test 8: General query with no specific domain"""
        query = "What's the best way to organize my project files?"
        intent = self.classifier.classify(query)

        # Should default to 'general' domain
        assert 'general' in intent.domains, f"Expected 'general' fallback, got {intent.domains}"

        # Confidence should be lower for general queries
        assert intent.confidence < 0.8, f"Expected lower confidence for general query, got {intent.confidence}"

        print("✅ Test 8: General query fallback - PASSED")
        self.passed += 1

    def test_email_extraction(self):
        """Test 9: Email address extraction"""
        query = "Setup forwarding for john.doe@example.com to support@company.com"
        intent = self.classifier.classify(query)

        assert 'emails' in intent.entities, f"Expected email extraction, got {intent.entities}"
        assert 'john.doe@example.com' in intent.entities['emails'], f"Expected john.doe@example.com, got {intent.entities['emails']}"
        assert 'support@company.com' in intent.entities['emails'], f"Expected support@company.com, got {intent.entities['emails']}"

        print("✅ Test 9: Email extraction - PASSED")
        self.passed += 1

    def test_custom_integration_complexity(self):
        """Test 10: Custom integration increases complexity"""
        query = "Integrate our custom CRM with Azure AD using custom SAML configuration"
        intent = self.classifier.classify(query)

        # Should detect integration + custom indicators
        assert intent.complexity >= 6, f"Expected high complexity (integration + custom), got {intent.complexity}"

        print("✅ Test 10: Custom integration complexity - PASSED")
        self.passed += 1

    def run_all(self):
        """Run all intent classifier tests"""
        print("\n=== IntentClassifier Test Suite ===\n")

        tests = [
            self.test_simple_dns_query,
            self.test_azure_migration_query,
            self.test_multi_domain_security_query,
            self.test_financial_planning_query,
            self.test_operational_task_query,
            self.test_analysis_research_query,
            self.test_urgent_query,
            self.test_general_query_fallback,
            self.test_email_extraction,
            self.test_custom_integration_complexity
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nIntentClassifier: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


class TestAgentSelector:
    """Test suite for AgentSelector"""

    def __init__(self):
        self.selector = AgentSelector()
        self.classifier = IntentClassifier()
        self.passed = 0
        self.failed = 0

    def test_single_agent_routing(self):
        """Test 11: Simple query routes to single agent"""
        query = "How do I set up MX records?"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        assert routing.strategy == 'single_agent', f"Expected 'single_agent', got {routing.strategy}"
        assert routing.initial_agent == 'dns_specialist', f"Expected 'dns_specialist', got {routing.initial_agent}"
        assert len(routing.agents) == 1, f"Expected 1 agent, got {len(routing.agents)}"

        print("✅ Test 11: Single agent routing - PASSED")
        self.passed += 1

    def test_swarm_routing_multi_domain(self):
        """Test 12: Multi-domain query routes to swarm"""
        query = "Setup DNS authentication and configure Azure Exchange Online"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        assert routing.strategy == 'swarm', f"Expected 'swarm', got {routing.strategy}"
        assert len(routing.agents) >= 2, f"Expected multiple agents, got {len(routing.agents)}"
        assert 'dns_specialist' in routing.agents or 'azure_solutions_architect' in routing.agents, \
            f"Expected DNS or Azure agent, got {routing.agents}"

        print("✅ Test 12: Swarm routing multi-domain - PASSED")
        self.passed += 1

    def test_complex_swarm_routing(self):
        """Test 13: High complexity routes to complex swarm"""
        query = "Migrate 250 users from on-prem Exchange to Azure with custom DNS, security audit, and compliance checks"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        assert routing.strategy == 'swarm', f"Expected 'swarm', got {routing.strategy}"
        assert intent.complexity >= 7, f"Expected high complexity, got {intent.complexity}"
        assert len(routing.agents) >= 2, f"Expected multiple agents for complex task, got {len(routing.agents)}"

        print("✅ Test 13: Complex swarm routing - PASSED")
        self.passed += 1

    def test_financial_agent_routing(self):
        """Test 14: Financial query routes to financial advisor"""
        query = "Should I salary sacrifice into super?"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        assert routing.initial_agent == 'financial_advisor', f"Expected 'financial_advisor', got {routing.initial_agent}"

        print("✅ Test 14: Financial agent routing - PASSED")
        self.passed += 1

    def test_security_agent_routing(self):
        """Test 15: Security query routes to security agent"""
        query = "Audit our Azure security posture and compliance"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        # Should route to either security or azure agent
        assert routing.initial_agent in ['cloud_security_principal', 'azure_solutions_architect'], \
            f"Expected security/azure agent, got {routing.initial_agent}"

        print("✅ Test 15: Security agent routing - PASSED")
        self.passed += 1

    def test_routing_confidence(self):
        """Test 16: Routing confidence matches intent confidence"""
        query = "Configure DNS records"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        # Single agent routing should have high confidence matching intent
        assert routing.confidence >= intent.confidence * 0.9, \
            f"Expected routing confidence ~{intent.confidence}, got {routing.confidence}"

        print("✅ Test 16: Routing confidence - PASSED")
        self.passed += 1

    def test_swarm_confidence_penalty(self):
        """Test 17: Swarm routing has confidence penalty"""
        query = "Setup DNS and Azure Exchange with security audit"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        # Swarm routing should have slightly lower confidence
        assert routing.confidence < intent.confidence, \
            f"Expected confidence penalty for swarm, intent={intent.confidence}, routing={routing.confidence}"

        print("✅ Test 17: Swarm confidence penalty - PASSED")
        self.passed += 1

    def test_context_enrichment(self):
        """Test 18: Routing includes enriched context"""
        query = "Configure Azure AD for john.doe@example.com"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        # Context should include query and entities
        assert 'query' in routing.context, f"Expected 'query' in context, got {routing.context.keys()}"
        assert 'intent_category' in routing.context, f"Expected 'intent_category' in context"
        assert 'entities' in routing.context, f"Expected 'entities' in context"

        print("✅ Test 18: Context enrichment - PASSED")
        self.passed += 1

    def test_fallback_to_ai_specialists(self):
        """Test 19: Unknown domain falls back to AI Specialists"""
        query = "Help me with quantum computing optimization"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        # General domain should route to ai_specialists_agent
        if 'general' in intent.domains:
            assert routing.initial_agent == 'ai_specialists_agent', \
                f"Expected 'ai_specialists_agent' fallback, got {routing.initial_agent}"

        print("✅ Test 19: Fallback to AI Specialists - PASSED")
        self.passed += 1

    def test_domains_in_context(self):
        """Test 20: Multi-domain routing includes all domains in context"""
        query = "Setup DNS authentication and Azure security for 100 users"
        intent = self.classifier.classify(query)
        routing = self.selector.select(intent, query)

        if routing.strategy == 'swarm':
            assert 'domains_involved' in routing.context, \
                f"Expected 'domains_involved' in swarm context, got {routing.context.keys()}"
            assert len(routing.context['domains_involved']) >= 2, \
                f"Expected multiple domains, got {routing.context['domains_involved']}"

        print("✅ Test 20: Domains in context - PASSED")
        self.passed += 1

    def run_all(self):
        """Run all agent selector tests"""
        print("\n=== AgentSelector Test Suite ===\n")

        tests = [
            self.test_single_agent_routing,
            self.test_swarm_routing_multi_domain,
            self.test_complex_swarm_routing,
            self.test_financial_agent_routing,
            self.test_security_agent_routing,
            self.test_routing_confidence,
            self.test_swarm_confidence_penalty,
            self.test_context_enrichment,
            self.test_fallback_to_ai_specialists,
            self.test_domains_in_context
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nAgentSelector: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


class TestCoordinatorAgent:
    """Test suite for CoordinatorAgent end-to-end"""

    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.passed = 0
        self.failed = 0

    def test_end_to_end_simple_query(self):
        """Test 21: End-to-end simple DNS query"""
        routing = self.coordinator.route("How do I configure SPF records?")

        assert routing.strategy == 'single_agent', f"Expected single_agent, got {routing.strategy}"
        assert routing.initial_agent == 'dns_specialist', f"Expected dns_specialist, got {routing.initial_agent}"
        assert routing.confidence >= 0.7, f"Expected high confidence, got {routing.confidence}"

        print("✅ Test 21: End-to-end simple query - PASSED")
        self.passed += 1

    def test_end_to_end_complex_query(self):
        """Test 22: End-to-end complex multi-domain query"""
        query = "Migrate 200 users to Azure Exchange Online with DNS authentication and security compliance"
        routing = self.coordinator.route(query)

        assert routing.strategy == 'swarm', f"Expected swarm, got {routing.strategy}"
        assert len(routing.agents) >= 2, f"Expected multiple agents, got {len(routing.agents)}"

        print("✅ Test 22: End-to-end complex query - PASSED")
        self.passed += 1

    def test_routing_history_recording(self):
        """Test 23: Routing decisions are recorded in history"""
        initial_count = len(self.coordinator.routing_history)

        self.coordinator.route("Test query 1")
        self.coordinator.route("Test query 2")

        assert len(self.coordinator.routing_history) == initial_count + 2, \
            f"Expected 2 new records, got {len(self.coordinator.routing_history) - initial_count}"

        print("✅ Test 23: Routing history recording - PASSED")
        self.passed += 1

    def test_routing_stats(self):
        """Test 24: Routing statistics generation"""
        # Route a few queries
        self.coordinator.route("Setup DNS")
        self.coordinator.route("Configure Azure")
        self.coordinator.route("Financial advice")

        stats = self.coordinator.get_routing_stats()

        assert 'total_routes' in stats, f"Expected 'total_routes' in stats, got {stats.keys()}"
        assert stats['total_routes'] >= 3, f"Expected at least 3 routes, got {stats['total_routes']}"
        assert 'strategies' in stats, f"Expected 'strategies' in stats"
        assert 'most_used_agents' in stats, f"Expected 'most_used_agents' in stats"

        print("✅ Test 24: Routing statistics - PASSED")
        self.passed += 1

    def test_convenience_function(self):
        """Test 25: route_query() convenience function"""
        from coordinator_agent import route_query

        routing = route_query("Setup email authentication")

        assert isinstance(routing, RoutingDecision), f"Expected RoutingDecision, got {type(routing)}"
        assert routing.initial_agent == 'dns_specialist', f"Expected dns_specialist, got {routing.initial_agent}"

        print("✅ Test 25: Convenience function - PASSED")
        self.passed += 1

    def run_all(self):
        """Run all coordinator tests"""
        print("\n=== CoordinatorAgent Test Suite ===\n")

        tests = [
            self.test_end_to_end_simple_query,
            self.test_end_to_end_complex_query,
            self.test_routing_history_recording,
            self.test_routing_stats,
            self.test_convenience_function
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nCoordinatorAgent: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


def main():
    """Run all test suites"""
    print("=" * 60)
    print("COORDINATOR AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    # Run all test suites
    intent_tests = TestIntentClassifier()
    intent_passed = intent_tests.run_all()

    selector_tests = TestAgentSelector()
    selector_passed = selector_tests.run_all()

    coordinator_tests = TestCoordinatorAgent()
    coordinator_passed = coordinator_tests.run_all()

    # Summary
    total_passed = intent_tests.passed + selector_tests.passed + coordinator_tests.passed
    total_failed = intent_tests.failed + selector_tests.failed + coordinator_tests.failed

    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("=" * 60)

    # Exit code
    if total_failed == 0:
        print("\n✅ ALL TESTS PASSED\n")
        return 0
    else:
        print(f"\n❌ {total_failed} TESTS FAILED\n")
        return 1


if __name__ == '__main__':
    exit(main())
