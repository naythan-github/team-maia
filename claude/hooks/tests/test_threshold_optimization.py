#!/usr/bin/env python3
"""
TDD Tests for Threshold Optimization (Phase 228)

Tests for:
- FR-1: 60% agent loading threshold
- FR-2: 40% capability gap detection
- FR-3: New agent recommendation (3+ gaps)

Run: python3 -m pytest claude/hooks/tests/test_threshold_optimization.py -v
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAgentLoadingThreshold:
    """FR-1: Agent loading threshold lowered to 60%"""

    def test_tc1_1_confidence_60_complexity_3_loads_agent(self):
        """TC-1.1: confidence=0.60, complexity=3 → SHOULD load agent"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.60,
            "complexity": 3,
            "primary_domain": "security"
        }

        result = should_invoke_swarm(classification)
        assert result is True, "60% confidence with complexity 3 should load agent"

    def test_tc1_2_confidence_59_does_not_load(self):
        """TC-1.2: confidence=0.59, complexity=3 → SHOULD NOT load agent"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.59,
            "complexity": 3,
            "primary_domain": "security"
        }

        result = should_invoke_swarm(classification)
        assert result is False, "59% confidence should not load agent"

    def test_tc1_3_confidence_70_loads_agent(self):
        """TC-1.3: confidence=0.70, complexity=3 → SHOULD load agent"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.70,
            "complexity": 3,
            "primary_domain": "sre"
        }

        result = should_invoke_swarm(classification)
        assert result is True, "70% confidence should load agent"

    def test_tc1_4_low_complexity_does_not_load(self):
        """TC-1.4: confidence=0.60, complexity=2 → SHOULD NOT load (complexity too low)"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.60,
            "complexity": 2,
            "primary_domain": "security"
        }

        result = should_invoke_swarm(classification)
        assert result is False, "Complexity 2 should not load agent regardless of confidence"

    def test_tc1_5_general_domain_with_high_confidence_loads(self):
        """TC-1.5: confidence=0.80, domain="general" → SHOULD load (removed domain check)"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.80,
            "complexity": 4,
            "primary_domain": "general"
        }

        result = should_invoke_swarm(classification)
        assert result is True, "General domain with high confidence should load agent (domain check removed)"

    def test_edge_case_exactly_60_percent(self):
        """Edge case: exactly 0.60 should trigger (inclusive)"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.60,
            "complexity": 3,
            "primary_domain": "python_review"
        }

        result = should_invoke_swarm(classification)
        assert result is True, "Exactly 60% should trigger (>= not >)"


class TestCapabilityGapDetection:
    """FR-2: Capability gap detection at 40%"""

    def setup_method(self):
        """Setup temp file for gap logging"""
        self.temp_dir = tempfile.mkdtemp()
        self.gap_file = Path(self.temp_dir) / "capability_gaps.json"

    def teardown_method(self):
        """Cleanup temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tc2_1_confidence_39_logs_gap(self):
        """TC-2.1: confidence=0.39 → SHOULD log capability gap"""
        from swarm_auto_loader import log_capability_gap, should_log_capability_gap

        classification = {
            "confidence": 0.39,
            "complexity": 4,
            "primary_domain": "general"
        }

        should_log = should_log_capability_gap(classification)
        assert should_log is True, "39% confidence should trigger gap logging"

    def test_tc2_2_confidence_40_no_gap(self):
        """TC-2.2: confidence=0.40 → SHOULD NOT log gap (at threshold)"""
        from swarm_auto_loader import should_log_capability_gap

        classification = {
            "confidence": 0.40,
            "complexity": 4,
            "primary_domain": "general"
        }

        should_log = should_log_capability_gap(classification)
        assert should_log is False, "40% confidence is at threshold, should not log gap"

    def test_tc2_3_gap_log_contains_required_fields(self):
        """TC-2.3: Gap log contains query, domains, timestamp"""
        from swarm_auto_loader import log_capability_gap

        classification = {
            "confidence": 0.35,
            "complexity": 4,
            "primary_domain": "general",
            "domains": ["general"]
        }
        query = "how do I make a soufflé?"

        with patch('swarm_auto_loader.CAPABILITY_GAPS_FILE', self.gap_file):
            log_capability_gap(classification, query)

        assert self.gap_file.exists(), "Gap file should be created"

        with open(self.gap_file) as f:
            gaps = json.load(f)

        assert len(gaps) > 0, "Should have at least one gap logged"
        gap = gaps[-1]

        assert "query" in gap, "Gap should contain query"
        assert "domains" in gap, "Gap should contain domains"
        assert "timestamp" in gap, "Gap should contain timestamp"
        assert "confidence" in gap, "Gap should contain confidence"
        assert gap["query"] == query
        assert gap["confidence"] == 0.35

    def test_tc2_4_gap_logging_failure_graceful(self):
        """TC-2.4: Gap logging failure → conversation continues (graceful)"""
        from swarm_auto_loader import log_capability_gap

        classification = {
            "confidence": 0.30,
            "complexity": 4,
            "primary_domain": "general"
        }

        # Use invalid path to simulate failure
        with patch('swarm_auto_loader.CAPABILITY_GAPS_FILE', Path("/nonexistent/path/gaps.json")):
            # Should not raise exception
            try:
                log_capability_gap(classification, "test query")
            except Exception as e:
                pytest.fail(f"Gap logging should not raise exceptions: {e}")


class TestNewAgentRecommendation:
    """FR-3: New agent recommendation after 3+ gaps"""

    def setup_method(self):
        """Setup temp files"""
        self.temp_dir = tempfile.mkdtemp()
        self.gap_file = Path(self.temp_dir) / "capability_gaps.json"
        self.rec_file = Path(self.temp_dir) / "agent_recommendations.json"

    def teardown_method(self):
        """Cleanup temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tc3_1_two_gaps_no_recommendation(self):
        """TC-3.1: 2 gaps in "cooking" domain → NO recommendation"""
        from swarm_auto_loader import check_for_agent_recommendation

        # Create 2 gaps
        gaps = [
            {"query": "how to make ramen", "domains": ["cooking"], "timestamp": datetime.now().isoformat(), "confidence": 0.35},
            {"query": "best sushi rice", "domains": ["cooking"], "timestamp": datetime.now().isoformat(), "confidence": 0.30}
        ]

        with open(self.gap_file, 'w') as f:
            json.dump(gaps, f)

        with patch('swarm_auto_loader.CAPABILITY_GAPS_FILE', self.gap_file):
            with patch('swarm_auto_loader.AGENT_RECOMMENDATIONS_FILE', self.rec_file):
                recommendation = check_for_agent_recommendation("cooking")

        assert recommendation is None, "2 gaps should not trigger recommendation"

    def test_tc3_2_three_gaps_within_7_days_triggers_recommendation(self):
        """TC-3.2: 3 gaps in "cooking" domain within 7 days → recommendation generated"""
        from swarm_auto_loader import check_for_agent_recommendation

        now = datetime.now()
        gaps = [
            {"query": "how to make ramen", "domains": ["cooking"], "timestamp": now.isoformat(), "confidence": 0.35},
            {"query": "best sushi rice", "domains": ["cooking"], "timestamp": (now - timedelta(days=1)).isoformat(), "confidence": 0.30},
            {"query": "tempura batter recipe", "domains": ["cooking"], "timestamp": (now - timedelta(days=2)).isoformat(), "confidence": 0.32}
        ]

        with open(self.gap_file, 'w') as f:
            json.dump(gaps, f)

        with patch('swarm_auto_loader.CAPABILITY_GAPS_FILE', self.gap_file):
            with patch('swarm_auto_loader.AGENT_RECOMMENDATIONS_FILE', self.rec_file):
                recommendation = check_for_agent_recommendation("cooking")

        assert recommendation is not None, "3 gaps within 7 days should trigger recommendation"
        assert recommendation["domain"] == "cooking"
        assert len(recommendation["example_queries"]) >= 3

    def test_tc3_3_three_gaps_spread_over_14_days_no_recommendation(self):
        """TC-3.3: 3 gaps over 14 days → NO recommendation (too spread)"""
        from swarm_auto_loader import check_for_agent_recommendation

        now = datetime.now()
        gaps = [
            {"query": "how to make ramen", "domains": ["cooking"], "timestamp": now.isoformat(), "confidence": 0.35},
            {"query": "best sushi rice", "domains": ["cooking"], "timestamp": (now - timedelta(days=8)).isoformat(), "confidence": 0.30},
            {"query": "tempura batter recipe", "domains": ["cooking"], "timestamp": (now - timedelta(days=10)).isoformat(), "confidence": 0.32}
        ]

        with open(self.gap_file, 'w') as f:
            json.dump(gaps, f)

        with patch('swarm_auto_loader.CAPABILITY_GAPS_FILE', self.gap_file):
            with patch('swarm_auto_loader.AGENT_RECOMMENDATIONS_FILE', self.rec_file):
                recommendation = check_for_agent_recommendation("cooking")

        assert recommendation is None, "Gaps spread over 14 days should not trigger recommendation"

    def test_tc3_4_recommendation_contains_required_fields(self):
        """TC-3.4: Recommendation contains domain, example queries, count"""
        from swarm_auto_loader import check_for_agent_recommendation

        now = datetime.now()
        gaps = [
            {"query": "query 1", "domains": ["newdomain"], "timestamp": now.isoformat(), "confidence": 0.35},
            {"query": "query 2", "domains": ["newdomain"], "timestamp": now.isoformat(), "confidence": 0.30},
            {"query": "query 3", "domains": ["newdomain"], "timestamp": now.isoformat(), "confidence": 0.32}
        ]

        with open(self.gap_file, 'w') as f:
            json.dump(gaps, f)

        with patch('swarm_auto_loader.CAPABILITY_GAPS_FILE', self.gap_file):
            with patch('swarm_auto_loader.AGENT_RECOMMENDATIONS_FILE', self.rec_file):
                recommendation = check_for_agent_recommendation("newdomain")

        assert recommendation is not None
        assert "domain" in recommendation
        assert "example_queries" in recommendation
        assert "count" in recommendation
        assert recommendation["count"] >= 3


class TestPerformance:
    """NFR-1: Performance requirements"""

    def test_threshold_check_under_5ms(self):
        """Threshold check should complete in under 5ms"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {
            "confidence": 0.65,
            "complexity": 4,
            "primary_domain": "security"
        }

        start = time.perf_counter()
        for _ in range(100):
            should_invoke_swarm(classification)
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms per call

        assert elapsed < 5, f"Threshold check took {elapsed:.2f}ms, should be <5ms"


class TestBackwardsCompatibility:
    """NFR-3: Backwards compatibility"""

    def test_none_classification_handled(self):
        """None classification should return False without error"""
        from swarm_auto_loader import should_invoke_swarm

        result = should_invoke_swarm(None)
        assert result is False

    def test_missing_fields_handled(self):
        """Missing fields should be handled gracefully"""
        from swarm_auto_loader import should_invoke_swarm

        classification = {"confidence": 0.70}  # Missing complexity and domain

        result = should_invoke_swarm(classification)
        assert result is False  # Should not crash, just return False


class TestAgentLoadingMessage:
    """Phase 228.3: Agent loading message output for Claude visibility"""

    def test_get_agent_loading_message_returns_message_when_routing(self):
        """When agent should load, get_agent_loading_message returns instruction"""
        from swarm_auto_loader import get_agent_loading_message

        classification = {
            "confidence": 0.90,
            "complexity": 4,
            "primary_domain": "python_review"
        }

        message = get_agent_loading_message(classification, "python_code_reviewer")

        assert message is not None, "Should return a message when agent loads"
        assert "python_code_reviewer" in message, "Message should contain agent name"
        assert "AGENT" in message.upper(), "Message should indicate agent loading"

    def test_get_agent_loading_message_returns_none_when_no_routing(self):
        """When agent should NOT load, get_agent_loading_message returns None"""
        from swarm_auto_loader import get_agent_loading_message

        classification = {
            "confidence": 0.40,  # Below threshold
            "complexity": 2,
            "primary_domain": "general"
        }

        message = get_agent_loading_message(classification, None)

        assert message is None, "Should return None when no agent loads"

    def test_agent_loading_message_contains_context_path(self):
        """Agent loading message should include path to agent context file"""
        from swarm_auto_loader import get_agent_loading_message

        classification = {
            "confidence": 0.85,
            "complexity": 3,
            "primary_domain": "security"
        }

        message = get_agent_loading_message(classification, "security_analyst")

        assert message is not None
        assert "claude/agents/" in message, "Message should include agent context path"

    def test_agent_loading_message_under_100_tokens(self):
        """Agent loading message should be concise (<100 tokens ~400 chars)"""
        from swarm_auto_loader import get_agent_loading_message

        classification = {
            "confidence": 0.90,
            "complexity": 5,
            "primary_domain": "sre"
        }

        message = get_agent_loading_message(classification, "sre_principal_engineer")

        assert message is not None
        assert len(message) < 500, f"Message too long: {len(message)} chars (should be <500)"

    def test_process_query_outputs_message_when_routing(self):
        """process_query should output agent loading message when routing matches"""
        from swarm_auto_loader import process_query
        import io
        import sys

        # Capture stdout
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        try:
            process_query("review the python code in the tools")
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()

        # Should contain agent loading message
        assert "AGENT" in output.upper() or "python_code_reviewer" in output.lower(), \
            f"Output should contain agent loading info. Got: {output[:200]}"

    def test_process_query_silent_when_no_routing(self):
        """process_query should be silent when routing doesn't match"""
        from swarm_auto_loader import process_query
        import io
        import sys

        # Capture stdout
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        try:
            # Simple query that shouldn't trigger agent loading
            process_query("hello")
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()

        # Should NOT contain agent loading message (silent for simple queries)
        assert "AGENT LOADED" not in output.upper(), \
            f"Should not output agent loading for simple query. Got: {output[:200]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
