#!/usr/bin/env python3
"""
TDD Tests for Domain Detection Improvements (Phase 228.1)

Tests for improved python_review domain detection to ensure
queries about reviewing Python code route to python_code_reviewer_agent.

Run: python3 -m pytest claude/tools/orchestration/tests/test_domain_detection.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPythonReviewDomainDetection:
    """Tests for python_review domain keyword matching"""

    def test_review_python_code_detects_python_review(self):
        """'review the python code' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("review the python code in the tools")

        assert 'python_review' in intent.domains, \
            f"Expected 'python_review' in domains, got {intent.domains}"

    def test_python_code_review_detects_python_review(self):
        """'python code review' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("do a python code review")

        assert 'python_review' in intent.domains

    def test_review_python_files_detects_python_review(self):
        """'review python files' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("review python files for quality issues")

        assert 'python_review' in intent.domains

    def test_check_python_code_quality_detects_python_review(self):
        """'check python code quality' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("check python code quality")

        assert 'python_review' in intent.domains

    def test_analyze_python_for_efficiency_detects_python_review(self):
        """'analyze python for efficiency' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("analyze python code for efficiency")

        assert 'python_review' in intent.domains

    def test_python_refactor_detects_python_review(self):
        """'refactor python' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("help me refactor this python code")

        assert 'python_review' in intent.domains

    def test_review_py_files_detects_python_review(self):
        """'review .py files' should detect python_review domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("review the .py files in this directory")

        assert 'python_review' in intent.domains


class TestAgentRouting:
    """Tests for correct agent routing after domain detection"""

    def test_python_review_routes_to_python_code_reviewer(self):
        """python_review domain should route to python_code_reviewer agent"""
        from coordinator_agent import CoordinatorAgent

        coordinator = CoordinatorAgent()
        routing = coordinator.route("review the python code in the tools")

        assert routing.initial_agent == 'python_code_reviewer', \
            f"Expected 'python_code_reviewer', got '{routing.initial_agent}'"

    def test_code_quality_check_routes_correctly(self):
        """Code quality checks should include python_code_reviewer in routing"""
        from coordinator_agent import CoordinatorAgent

        coordinator = CoordinatorAgent()
        routing = coordinator.route("check code quality of the security tools")

        # Multi-domain queries may route to swarm - verify python_code_reviewer is included
        # "security tools" matches both 'security' and 'python_review' domains
        assert 'python_code_reviewer' in routing.agents, \
            f"Expected 'python_code_reviewer' in agents, got {routing.agents}"


class TestConfidenceWithNewKeywords:
    """Tests for confidence levels with improved detection"""

    def test_python_review_query_has_high_confidence(self):
        """Python review queries should have >=60% confidence"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("review the python code in the tools")

        assert intent.confidence >= 0.60, \
            f"Expected confidence >= 0.60, got {intent.confidence}"

    def test_python_review_not_classified_as_general(self):
        """Python review should not fall back to 'general' domain"""
        from coordinator_agent import IntentClassifier

        classifier = IntentClassifier()
        intent = classifier.classify("review the python code for efficiency")

        assert intent.domains != ['general'], \
            "Python review should not be classified as 'general'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
