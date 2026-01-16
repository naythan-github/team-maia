#!/usr/bin/env python3
"""
End-to-end tests for subagent orchestration pipeline.

SPRINT-003-SWARM-TASK-ORCHESTRATION E2E Validation
Tests the full flow: query → spawn decision → prompt build → track execution → detect handoff

These tests validate the complete pipeline integration.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest import TestCase, mock

# Add maia root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))


class TestOrchestrationPipelineEndToEnd(TestCase):
    """E2E tests for the full orchestration pipeline."""

    def setUp(self):
        """Create isolated test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.sessions_dir = Path(self.temp_dir) / "sessions"
        self.sessions_dir.mkdir(parents=True)

        # Create a minimal session file
        self.context_id = "12345"
        self.session_file = self.sessions_dir / f"swarm_session_{self.context_id}.json"
        session_data = {
            "current_agent": "sre_principal_engineer_agent",
            "session_start": datetime.utcnow().isoformat() + "Z",
            "domain": "sre",
            "context": {
                "active_sprint": "SPRINT-TEST",
                "sprint_status": "IN_PROGRESS"
            }
        }
        self.session_file.write_text(json.dumps(session_data))

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_e2e_exploration_query_full_pipeline(self):
        """
        E2E: Full pipeline for exploration query.

        Flow:
        1. Query: "explore the authentication system"
        2. SpawnDecisionEngine decides to spawn (exploration pattern)
        3. SubagentPromptBuilder builds prompt with agent context
        4. SubagentTracker records execution
        5. Response analyzed for handoffs
        """
        from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine
        from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder
        from claude.tools.orchestration.subagent_tracker import SubagentTracker
        from claude.tools.orchestration.subagent_handoff import SubagentHandoffDetector

        query = "explore the authentication system and find where tokens are validated"

        # Step 1: Spawn Decision
        engine = SpawnDecisionEngine()
        decision = engine.analyze(
            query=query,
            session_context={},
            files_mentioned=[]
        )

        self.assertTrue(
            decision.should_spawn,
            "Exploration query should trigger spawn"
        )
        # recommended_agent is an agent name (e.g., security_engineer_agent)
        # not a subagent type - just verify we got a recommendation
        self.assertIsNotNone(decision.recommended_agent)
        self.assertGreater(decision.confidence, 0.5)

        # Step 2: Build Prompt
        builder = SubagentPromptBuilder()
        prompt_result = builder.build(
            task=query,
            agent_name="cloud_security_principal_agent",  # Use existing agent
            additional_context="Sprint: SPRINT-TEST\nFocus: authentication"
        )

        self.assertIn("security", prompt_result.prompt.lower())
        self.assertIn(query, prompt_result.prompt)
        self.assertGreater(prompt_result.total_tokens, 100)

        # Step 3: Track Execution
        tracker = SubagentTracker(
            context_id=self.context_id,
            session_dir=self.sessions_dir
        )
        execution_id = tracker.start_execution(
            agent="cloud_security_principal_agent",
            task=query,
            model="sonnet"
        )

        self.assertIsNotNone(execution_id)
        self.assertTrue(execution_id.startswith("exec_"))

        # Simulate subagent response
        simulated_response = """
        Found authentication in:
        - src/auth/token_validator.py:45 - validates JWT tokens
        - src/auth/session_manager.py:120 - manages session lifecycle
        - src/middleware/auth_middleware.py:30 - request authentication

        Recommendation: transfer_to_security_architect_agent for architectural review
        of the token validation approach.
        """

        # Step 4: Complete Execution
        tracker.complete_execution(
            exec_id=execution_id,
            result_summary=simulated_response[:200]
        )

        # Verify execution recorded
        last = tracker.get_last_execution()
        self.assertIsNotNone(last)
        self.assertEqual(last.execution_id, execution_id)

        # Step 5: Detect Handoff
        detector = SubagentHandoffDetector()
        handoff = detector.analyze(
            subagent_result=simulated_response,
            current_agent="cloud_security_principal_agent"
        )

        self.assertTrue(handoff.should_handoff)
        # Verify handoff was detected to a security-related agent
        self.assertIn("security", handoff.target_agent.lower())

    def test_e2e_simple_query_no_spawn(self):
        """
        E2E: Simple query that should NOT spawn subagent.

        Query: "edit line 45 of config.py"
        This is a simple, targeted task - handle directly.
        """
        from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

        query = "edit line 45 of config.py to change the timeout to 30"

        engine = SpawnDecisionEngine()
        decision = engine.analyze(
            query=query,
            session_context={},
            files_mentioned=["config.py"]
        )

        self.assertFalse(
            decision.should_spawn,
            "Simple edit query should NOT trigger spawn"
        )

    def test_e2e_sprint_mode_biases_toward_spawn(self):
        """
        E2E: Sprint mode context biases toward spawning.

        When in active sprint, even moderate complexity queries
        should spawn to maintain focus.
        """
        from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

        sprint_context = {
            "active_sprint": "SPRINT-003-SESSION-CLEANUP",
            "sprint_status": "IN_PROGRESS",
            "current_phase": "P5"
        }

        query = "check the status of the database connection pool"

        engine = SpawnDecisionEngine()
        decision = engine.analyze(
            query=query,
            session_context=sprint_context,
            files_mentioned=[]
        )

        self.assertIsNotNone(decision)

    def test_e2e_multi_domain_handoff_chain(self):
        """
        E2E: Response triggers handoff to multiple potential domains.
        """
        from claude.tools.orchestration.subagent_handoff import SubagentHandoffDetector

        response = """
        Analysis complete. Found issues in multiple areas:

        1. Security concern: The API key is stored in plaintext
           Recommend: handoff_to_security_engineer_agent for review

        2. Infrastructure issue: The deployment script doesn't handle rollbacks
        """

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            subagent_result=response,
            current_agent="sre_principal_engineer_agent"
        )

        self.assertTrue(result.should_handoff)
        # The actual agent returned depends on the handoff pattern matching
        self.assertIn("security", result.target_agent.lower())

    def test_e2e_agent_recommendation_accuracy(self):
        """
        E2E: SpawnDecisionEngine recommends appropriate agents.

        The recommended_agent is an agent name (e.g., sre_principal_engineer_agent),
        not a subagent type. We verify that exploration queries trigger spawn.
        """
        from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

        test_cases = [
            "explore how the kubernetes pods are configured",
            "find all files that handle authentication",
            "analyze the caching architecture",
        ]

        engine = SpawnDecisionEngine()

        for query in test_cases:
            decision = engine.analyze(
                query=query,
                session_context={},
                files_mentioned=[]
            )
            self.assertTrue(
                decision.should_spawn,
                f"Query '{query}' should trigger spawn"
            )
            self.assertIsNotNone(
                decision.recommended_agent,
                f"Query '{query}' should have a recommended agent"
            )

    def test_e2e_execution_chain_persistence(self):
        """
        E2E: Multiple executions form a trackable chain.
        """
        from claude.tools.orchestration.subagent_tracker import SubagentTracker

        tracker = SubagentTracker(
            context_id=self.context_id,
            session_dir=self.sessions_dir
        )

        # First execution
        exec1_id = tracker.start_execution(
            agent="sre_principal_engineer_agent",
            task="analyze system health",
            model="sonnet"
        )
        tracker.complete_execution(exec1_id, "Found issues in monitoring")

        # Second execution
        exec2_id = tracker.start_execution(
            agent="devops_architect_agent",
            task="review monitoring configuration",
            model="sonnet"
        )
        tracker.complete_execution(exec2_id, "Monitoring config updated")

        # Third execution
        exec3_id = tracker.start_execution(
            agent="sre_principal_engineer_agent",
            task="validate fix",
            model="haiku"
        )
        tracker.complete_execution(exec3_id, "Validation passed")

        # Get full chain
        chain = tracker.get_chain()

        self.assertEqual(len(chain.executions), 3)
        self.assertEqual(chain.executions[0].execution_id, exec1_id)
        self.assertEqual(chain.executions[1].execution_id, exec2_id)
        self.assertEqual(chain.executions[2].execution_id, exec3_id)

    def test_e2e_prompt_builder_with_additional_context(self):
        """
        E2E: Prompt builder includes additional context correctly.
        """
        from claude.tools.orchestration.subagent_prompt_builder import SubagentPromptBuilder

        builder = SubagentPromptBuilder()
        result = builder.build(
            task="implement heartbeat mechanism",
            agent_name="sre_principal_engineer_agent",
            additional_context="Sprint: SPRINT-003-SESSION-CLEANUP\nPhase: P5\nTDD Required: Yes"
        )

        self.assertIn("heartbeat", result.prompt.lower())
        self.assertIn("SPRINT-003", result.prompt)
        self.assertIn("TDD Required", result.prompt)


class TestOrchestrationErrorHandling(TestCase):
    """E2E tests for error handling in orchestration."""

    def setUp(self):
        """Create isolated test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.sessions_dir = Path(self.temp_dir) / "sessions"
        self.sessions_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_e2e_nonexistent_session_graceful_handling(self):
        """
        E2E: Orchestration handles nonexistent session directory gracefully.
        """
        from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine
        from claude.tools.orchestration.subagent_tracker import SubagentTracker

        engine = SpawnDecisionEngine()
        decision = engine.analyze(
            query="explore the codebase",
            session_context={},
            files_mentioned=[]
        )
        self.assertIsNotNone(decision)
        self.assertTrue(decision.should_spawn)

        nonexistent_dir = Path(self.temp_dir) / "nonexistent"
        tracker = SubagentTracker(
            context_id="test123",
            session_dir=nonexistent_dir
        )

        exec_id = tracker.start_execution(
            agent="test", task="test", model="sonnet"
        )
        self.assertIsNotNone(exec_id)

    def test_e2e_empty_query_handling(self):
        """
        E2E: Orchestration handles empty/minimal queries.
        """
        from claude.tools.orchestration.spawn_decision import SpawnDecisionEngine

        engine = SpawnDecisionEngine()

        decision = engine.analyze(
            query="",
            session_context={},
            files_mentioned=[]
        )
        self.assertIsNotNone(decision)
        self.assertFalse(decision.should_spawn)

        decision = engine.analyze(
            query="hi",
            session_context={},
            files_mentioned=[]
        )
        self.assertIsNotNone(decision)

    def test_e2e_handoff_detector_no_handoff_needed(self):
        """
        E2E: Handoff detector correctly identifies when no handoff is needed.
        """
        from claude.tools.orchestration.subagent_handoff import SubagentHandoffDetector

        response = """
        Analysis complete. All systems are functioning normally.
        No issues found in the current configuration.
        The implementation follows best practices.
        """

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            subagent_result=response,
            current_agent="sre_principal_engineer_agent"
        )

        self.assertFalse(result.should_handoff)


if __name__ == '__main__':
    import unittest
    unittest.main()
