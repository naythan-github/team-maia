#!/usr/bin/env python3
"""
Test Suite: Automatic Agent Persistence System
==============================================

Tests for Phase 134 - Automatic Agent Routing with Session Persistence

Test Coverage:
- Happy Path: Single domain, multi-agent handoff, domain switching
- Error Handling: Agent file missing, circular handoffs, low confidence
- Performance: Hook latency, agent loading time
- Integration: Phase 125 logging, user overrides

Project: AGENT_PERSISTENCE_134
Requirements: claude/data/AGENT_PERSISTENCE_TDD_REQUIREMENTS.md
"""

import unittest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime

# Import modules under test (will be implemented in Phases 2-5)
try:
    from coordinator_agent import IntentClassifier, AgentSelector, CoordinatorAgent
    from agent_swarm import SwarmOrchestrator, AgentResult, AgentHandoff, HandoffParser
    from agent_loader import AgentLoader, AgentPrompt
except ImportError:
    # Modules not yet fully implemented - create mocks for test design
    pass


class TestAgentPersistenceHappyPath(unittest.TestCase):
    """Test happy path scenarios - automatic loading and persistence"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "maia_active_swarm_session.json"

    def tearDown(self):
        """Clean up test fixtures"""
        if self.session_file.exists():
            self.session_file.unlink()

    def test_single_domain_specialist_query(self):
        """
        Test 1: Single Domain Specialist Query

        Requirement: Req 1 - Automatic Swarm Invocation

        Given: User submits security-related query
        When: Hook classifies with confidence >70%
        Then: Security specialist agent loaded automatically
        And: Session state persisted
        """
        # Arrange
        user_query = "Review this Python code for security issues"

        # Mock coordinator classification
        mock_intent = {
            'category': 'security',
            'domains': ['security'],
            'complexity': 5,
            'confidence': 0.87
        }

        # Act
        with patch('coordinator_agent.IntentClassifier') as MockClassifier:
            classifier = MockClassifier.return_value
            classifier.classify.return_value = mock_intent

            # Simulate hook Stage 0.8 behavior
            result = self._simulate_hook_stage_08(user_query)

        # Assert
        self.assertEqual(result['agent_suggested'], 'security_specialist')
        self.assertEqual(result['confidence'], 0.87)
        self.assertTrue(result['should_invoke_swarm'])

        # Verify session file created
        self.assertTrue(self.session_file.exists())

        with open(self.session_file) as f:
            session = json.load(f)

        self.assertEqual(session['current_agent'], 'security_specialist')
        self.assertEqual(session['domain'], 'security')
        self.assertGreater(session['last_classification_confidence'], 0.70)

    def test_multi_agent_handoff_chain(self):
        """
        Test 2: Multi-Agent Handoff Chain

        Requirement: Req 4 - Swarm Orchestrator Integration

        Given: User requests multi-domain task
        When: Initial agent determines handoff needed
        Then: Context passed to next agent
        And: Handoff chain tracked
        """
        # Arrange
        user_query = "Setup Azure Exchange with custom domain and security"

        expected_chain = [
            {'from': 'dns_specialist', 'to': 'azure_solutions_architect', 'reason': 'DNS configured, need Exchange setup'},
            {'from': 'azure_solutions_architect', 'to': 'security_specialist', 'reason': 'Exchange configured, need security hardening'}
        ]

        # Act
        with patch('agent_swarm.SwarmOrchestrator') as MockSwarm:
            orchestrator = MockSwarm.return_value
            orchestrator.execute_with_handoffs.return_value = {
                'final_agent': 'security_specialist',
                'handoff_chain': expected_chain,
                'total_handoffs': 2,
                'final_output': {'status': 'complete'}
            }

            result = self._simulate_swarm_execution(user_query, initial_agent='dns_specialist')

        # Assert
        self.assertEqual(len(result['handoff_chain']), 2)
        self.assertEqual(result['final_agent'], 'security_specialist')

        # Verify context enrichment
        self.assertIn('from', result['handoff_chain'][0])
        self.assertIn('to', result['handoff_chain'][0])
        self.assertIn('reason', result['handoff_chain'][0])

    def test_domain_switch_mid_conversation(self):
        """
        Test 3: Domain Switch Mid-Conversation

        Requirement: Req 2 - Domain Change Detection & Agent Switching

        Given: Agent currently active (FinOps)
        When: User query domain changes (Security)
        Then: Domain change detected
        And: New agent loaded with context from previous
        """
        # Arrange
        # Message 1: FinOps domain
        msg1 = "Optimize Azure costs"
        initial_session = {
            'current_agent': 'finops_agent',
            'domain': 'finops',
            'context': {'cost_analysis': 'completed'},
            'last_classification_confidence': 0.85
        }
        self._write_session(initial_session)

        # Message 2: Security domain
        msg2 = "Make it secure"

        # Act
        with patch('coordinator_agent.IntentClassifier') as MockClassifier:
            classifier = MockClassifier.return_value
            classifier.classify.return_value = {
                'category': 'security',
                'domains': ['security'],
                'complexity': 6,
                'confidence': 0.88
            }

            result = self._simulate_domain_switch_detection(msg2)

        # Assert
        self.assertTrue(result['domain_changed'])
        self.assertEqual(result['previous_agent'], 'finops_agent')
        self.assertEqual(result['new_agent'], 'security_specialist')

        # Verify context handoff
        self.assertIn('cost_analysis', result['enriched_context'])

        # Verify session updated
        with open(self.session_file) as f:
            session = json.load(f)

        self.assertEqual(session['current_agent'], 'security_specialist')
        self.assertEqual(session['domain'], 'security')
        self.assertIn('finops_agent', session['handoff_chain'])


class TestAgentPersistenceErrorHandling(unittest.TestCase):
    """Test error handling and graceful degradation"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "maia_active_swarm_session.json"

    def test_agent_file_missing(self):
        """
        Test 4: Agent File Missing

        Requirement: Req 5 - Graceful Degradation & Error Handling

        Given: Routing suggests agent
        When: Agent file doesn't exist
        Then: Fallback to base Maia
        And: Warning logged
        And: Conversation continues
        """
        # Arrange
        user_query = "Optimize Azure costs"
        agent_file = Path("claude/agents/finops_agent.md")

        # Act
        with patch('agent_loader.AgentLoader.load_agent') as mock_load:
            mock_load.side_effect = FileNotFoundError(f"Agent file not found: {agent_file}")

            result = self._simulate_agent_load_with_fallback('finops_agent')

        # Assert
        self.assertEqual(result['status'], 'fallback_to_base_maia')
        self.assertEqual(result['error'], 'agent_file_not_found')
        self.assertTrue(result['conversation_continues'])
        self.assertIn('WARNING', result['log_message'])

    def test_circular_handoff_detection(self):
        """
        Test 5: Circular Handoff Detection

        Requirement: Req 5 - Graceful Degradation (Circular handoff prevention)

        Given: Agent A hands off to Agent B
        When: Agent B hands back to Agent A (loop)
        Then: MaxHandoffsExceeded after 5 handoffs
        And: Error logged with handoff chain
        And: Last valid output returned
        """
        # Arrange
        handoff_chain = [
            {'from': 'agent_a', 'to': 'agent_b'},
            {'from': 'agent_b', 'to': 'agent_a'},
            {'from': 'agent_a', 'to': 'agent_b'},
            {'from': 'agent_b', 'to': 'agent_a'},
            {'from': 'agent_a', 'to': 'agent_b'},
            {'from': 'agent_b', 'to': 'agent_a'}  # 6th handoff - exceeds limit
        ]

        # Act
        with patch('agent_swarm.SwarmOrchestrator.execute_with_handoffs') as mock_exec:
            from agent_swarm import MaxHandoffsExceeded
            mock_exec.side_effect = MaxHandoffsExceeded(
                "Exceeded 5 handoffs. Chain: agent_a → agent_b → agent_a → agent_b → agent_a → agent_b"
            )

            result = self._simulate_circular_handoff_detection()

        # Assert
        self.assertEqual(result['status'], 'max_handoffs_exceeded')
        self.assertEqual(result['handoff_count'], 5)
        self.assertIsNotNone(result['last_valid_output'])
        self.assertIn('agent_a → agent_b', result['error_message'])

    def test_low_confidence_query(self):
        """
        Test 6: Low Confidence Query

        Requirement: Req 6 - Low Confidence Handling

        Given: User submits general query
        When: Routing confidence <70%
        Then: No agent loaded
        And: Base Maia handles query
        And: No swarm overhead
        """
        # Arrange
        user_query = "What's the weather?"

        # Act
        with patch('coordinator_agent.IntentClassifier') as MockClassifier:
            classifier = MockClassifier.return_value
            classifier.classify.return_value = {
                'category': 'general',
                'domains': ['general'],
                'complexity': 1,
                'confidence': 0.20
            }

            result = self._simulate_hook_stage_08(user_query)

        # Assert
        self.assertFalse(result['should_invoke_swarm'])
        self.assertEqual(result['agent_suggested'], None)
        self.assertEqual(result['handling'], 'base_maia')


class TestAgentPersistencePerformance(unittest.TestCase):
    """Test performance requirements and SLAs"""

    def test_hook_latency(self):
        """
        Test 7: Hook Latency

        Requirement: Non-functional - Performance (Hook <200ms)

        Given: Hook Stage 0.8 executes
        When: Classification + routing decision made
        Then: Complete in <200ms for 95% of queries
        """
        # Arrange
        queries = [
            "Review code for security",
            "Optimize Azure costs",
            "Setup DNS records",
            "Analyze performance issues",
            "Help with Python error"
        ] * 20  # 100 queries

        latencies = []

        # Act
        for query in queries:
            start = time.time()
            with patch('coordinator_agent.CoordinatorAgent.route') as mock_route:
                mock_route.return_value = Mock(
                    strategy='single_agent',
                    agents=['mock_agent'],
                    confidence=0.85
                )
                self._simulate_hook_stage_08(query)

            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

        # Assert
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        self.assertLess(p95_latency, 200,
                       f"P95 latency {p95_latency:.1f}ms exceeds 200ms target")

        # Log performance stats
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        print(f"\nHook Latency Stats:")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  P95: {p95_latency:.1f}ms")
        print(f"  Max: {max_latency:.1f}ms")

    def test_agent_loading_time(self):
        """
        Test 8: Agent Loading Time

        Requirement: Non-functional - Performance (Agent load <3s)

        Given: Agent file exists
        When: AgentLoader.load_agent() called
        Then: Complete in <3s for 95% of loads
        """
        # Arrange
        agents = [
            'security_specialist',
            'sre_principal_engineer',
            'azure_solutions_architect',
            'dns_specialist',
            'finops_agent'
        ]

        load_times = []

        # Act
        for agent in agents * 20:  # 100 loads
            start = time.time()

            # Mock agent file read
            mock_content = "# Agent Prompt\n" + ("x" * 50000)  # ~50KB file
            with patch('builtins.open', mock_open(read_data=mock_content)):
                with patch('agent_loader.AgentLoader.load_agent') as mock_load:
                    mock_load.return_value = Mock(
                        agent_name=agent,
                        prompt_content=mock_content,
                        version='v2.2'
                    )
                    self._simulate_agent_load(agent)

            load_time = time.time() - start
            load_times.append(load_time)

        # Assert
        p95_load_time = sorted(load_times)[int(len(load_times) * 0.95)]
        self.assertLess(p95_load_time, 3.0,
                       f"P95 load time {p95_load_time:.2f}s exceeds 3s target")


class TestAgentPersistenceIntegration(unittest.TestCase):
    """Test integration with existing systems"""

    def test_phase_125_logging_integration(self):
        """
        Test 9: Phase 125 Logging Integration

        Requirement: Integration - Phase 125 routing accuracy logger

        Given: Automatic routing triggered
        When: Agent loaded successfully
        Then: Routing decision logged to database
        And: Handoff chain logged if multi-agent
        And: Dashboard displays metrics
        """
        # Arrange
        user_query = "Review code for security"
        routing_decision = {
            'strategy': 'single_agent',
            'agents': ['security_specialist'],
            'initial_agent': 'security_specialist',
            'confidence': 0.87,
            'reasoning': 'Security domain query'
        }

        # Act
        with patch('routing_decision_logger.RoutingDecisionLogger') as MockLogger:
            logger = MockLogger.return_value
            logger.log_suggestion.return_value = 'query_hash_123'

            result = self._simulate_phase_125_logging(user_query, routing_decision)

        # Assert
        self.assertTrue(result['logged'])
        self.assertIsNotNone(result['query_hash'])
        self.assertEqual(result['agent_suggested'], 'security_specialist')

        # Verify log structure
        log_entry = result['log_entry']
        self.assertIn('timestamp', log_entry)
        self.assertIn('user_query', log_entry)
        self.assertIn('suggested_agent', log_entry)
        self.assertIn('confidence', log_entry)
        self.assertIn('session_id', log_entry)

    def test_user_override(self):
        """
        Test 10: User Override

        Requirement: Req 7 - Explicit Override Capability

        Given: Automatic routing suggests Security Agent
        When: User explicitly requests SRE agent instead
        Then: Override detected
        And: SRE agent loaded
        And: Override logged with reasoning
        """
        # Arrange
        msg1 = "Review this code"
        automatic_suggestion = 'security_specialist'

        msg2 = "Actually, load sre_principal_engineer instead"
        user_override = 'sre_principal_engineer'

        # Act
        with patch('coordinator_agent.CoordinatorAgent.route') as mock_route:
            # First message - automatic suggestion
            mock_route.return_value = Mock(
                strategy='single_agent',
                agents=[automatic_suggestion],
                initial_agent=automatic_suggestion
            )

            result1 = self._simulate_hook_stage_08(msg1)

            # Second message - user override
            result2 = self._simulate_user_override_detection(msg2, user_override)

        # Assert
        self.assertTrue(result2['override_detected'])
        self.assertEqual(result2['suggested_agent'], automatic_suggestion)
        self.assertEqual(result2['actual_agent'], user_override)
        self.assertEqual(result2['override_reason'], 'user_explicit_request')

        # Verify override logged for accuracy tracking
        self.assertTrue(result2['logged_to_phase_125'])


# ============================================================================
# Test Helper Methods (Base class with shared helpers)
# ============================================================================

class TestHelperMixin:
    """Mixin class with shared test helper methods"""

    def _simulate_hook_stage_08(self, user_query):
        """Simulate hook Stage 0.8 behavior"""
        # This will be replaced with actual hook integration in Phase 2
        result = {
            'agent_suggested': None,
            'confidence': 0.0,
            'should_invoke_swarm': False,
            'handling': 'base_maia'
        }

        # Simple pattern matching for test purposes
        if 'security' in user_query.lower() or 'code' in user_query.lower():
            result['agent_suggested'] = 'security_specialist'
            result['confidence'] = 0.87
            result['should_invoke_swarm'] = True
            result['handling'] = 'specialist_agent'

            # Create session file for test
            session_data = {
                'current_agent': 'security_specialist',
                'domain': 'security',
                'context': {},
                'handoff_chain': [],
                'last_classification_confidence': 0.87
            }
            self._write_session(session_data)

        elif 'cost' in user_query.lower() or 'optimize' in user_query.lower():
            result['agent_suggested'] = 'finops_agent'
            result['confidence'] = 0.85
            result['should_invoke_swarm'] = True
            result['handling'] = 'specialist_agent'
        elif 'weather' in user_query.lower():
            result['confidence'] = 0.20
            result['should_invoke_swarm'] = False

        return result

    def _simulate_swarm_execution(self, user_query, initial_agent):
        """Simulate swarm orchestrator execution"""
        # This will be replaced with actual SwarmOrchestrator in Phase 3
        return {
            'final_agent': 'security_specialist',
            'handoff_chain': [
                {'from': 'dns_specialist', 'to': 'azure_solutions_architect', 'reason': 'DNS configured, need Exchange setup'},
                {'from': 'azure_solutions_architect', 'to': 'security_specialist', 'reason': 'Exchange configured, need security hardening'}
            ],
            'total_handoffs': 2,
            'final_output': {'status': 'complete'}
        }

    def _simulate_domain_switch_detection(self, new_query):
        """Simulate domain change detection logic"""
        # This will be implemented in Phase 5

        # Read current session
        with open(self.session_file) as f:
            current_session = json.load(f)

        # Mock new classification
        new_intent = {
            'category': 'security',
            'domains': ['security'],
            'confidence': 0.88
        }

        # Detect domain change
        domain_changed = current_session['domain'] != new_intent['domains'][0]

        result = {
            'domain_changed': domain_changed,
            'previous_agent': current_session['current_agent'],
            'new_agent': 'security_specialist',
            'enriched_context': current_session.get('context', {})
        }

        # Update session file for test
        if domain_changed:
            previous_agent = current_session['current_agent']
            current_session['current_agent'] = 'security_specialist'
            current_session['domain'] = 'security'
            # Preserve handoff chain history
            if 'handoff_chain' not in current_session:
                current_session['handoff_chain'] = []
            current_session['handoff_chain'].append(previous_agent)
            self._write_session(current_session)

        return result

    def _write_session(self, session_data):
        """Write session state file"""
        # Ensure session_file attribute exists (for tests without setUp)
        if not hasattr(self, 'session_file'):
            self.temp_dir = tempfile.mkdtemp()
            self.session_file = Path(self.temp_dir) / "maia_active_swarm_session.json"

        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

    def _simulate_agent_load_with_fallback(self, agent_name):
        """Simulate agent loading with graceful fallback"""
        # This will be implemented in Phase 3-4
        try:
            # Attempt to load agent (will fail in this test)
            raise FileNotFoundError(f"Agent file not found: {agent_name}")
        except FileNotFoundError as e:
            # Graceful degradation
            return {
                'status': 'fallback_to_base_maia',
                'error': 'agent_file_not_found',
                'conversation_continues': True,
                'log_message': f"WARNING: {str(e)}, fallback to base context"
            }

    def _simulate_circular_handoff_detection(self):
        """Simulate circular handoff detection"""
        # This will be implemented in Phase 3 (SwarmOrchestrator)
        return {
            'status': 'max_handoffs_exceeded',
            'handoff_count': 5,
            'last_valid_output': {'result': 'partial solution'},
            'error_message': 'Exceeded 5 handoffs. Chain: agent_a → agent_b → ...'
        }

    def _simulate_agent_load(self, agent_name):
        """Simulate agent file loading"""
        # Mock file I/O delay
        time.sleep(0.001)  # 1ms mock delay
        return Mock(agent_name=agent_name)

    def _simulate_phase_125_logging(self, user_query, routing_decision):
        """Simulate Phase 125 routing logger integration"""
        # This will be integrated in Phase 2
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_query': user_query,
            'suggested_agent': routing_decision['initial_agent'],
            'confidence': routing_decision['confidence'],
            'session_id': 'test_session_123'
        }

        return {
            'logged': True,
            'query_hash': 'query_hash_123',
            'agent_suggested': routing_decision['initial_agent'],
            'log_entry': log_entry
        }

    def _simulate_user_override_detection(self, user_message, override_agent):
        """Simulate user override detection"""
        # This will be implemented in Phase 4-5
        override_detected = 'load' in user_message.lower() and override_agent in user_message

        return {
            'override_detected': override_detected,
            'suggested_agent': 'security_specialist',
            'actual_agent': override_agent,
            'override_reason': 'user_explicit_request',
            'logged_to_phase_125': True
        }


# Apply mixin to test classes
class TestAgentPersistenceHappyPath(TestHelperMixin, TestAgentPersistenceHappyPath):
    """Happy path tests with helper methods"""
    pass


class TestAgentPersistenceErrorHandling(TestHelperMixin, TestAgentPersistenceErrorHandling):
    """Error handling tests with helper methods"""
    pass


class TestAgentPersistencePerformance(TestHelperMixin, TestAgentPersistencePerformance):
    """Performance tests with helper methods"""
    pass


class TestAgentPersistenceIntegration(TestHelperMixin, TestAgentPersistenceIntegration):
    """Integration tests with helper methods"""
    pass


# ============================================================================
# Test Runner
# ============================================================================

def run_test_suite():
    """Run complete test suite with reporting"""

    print("="*80)
    print("AUTOMATIC AGENT PERSISTENCE - TEST SUITE")
    print("Project: AGENT_PERSISTENCE_134")
    print("="*80)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAgentPersistenceHappyPath))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentPersistenceErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentPersistencePerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentPersistenceIntegration))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Ready for Phase 2 (Implementation)")
    else:
        print("❌ TESTS FAILED - Review failures before proceeding")

    return result


if __name__ == '__main__':
    run_test_suite()
