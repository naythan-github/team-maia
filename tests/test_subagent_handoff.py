"""
Tests for SubagentHandoffDetector - SPRINT-003 Phase 4.

TDD: Tests written FIRST before implementation.
"""

import pytest
from typing import Optional


class TestSubagentHandoffDetector:
    """Unit tests for SubagentHandoffDetector."""

    def test_explicit_transfer_to_pattern(self):
        """Test detection of transfer_to_X patterns."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
            HandoffRecommendation
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "Based on my analysis, I recommend transfer_to_security_agent for this vulnerability review.",
            current_agent="sre_principal_engineer_agent"
        )

        assert result.should_handoff is True
        assert result.target_agent == "security_agent"
        assert "transfer_to_security_agent" in result.detected_patterns
        assert result.confidence >= 0.8

    def test_explicit_handoff_to_pattern(self):
        """Test detection of 'handoff to X' patterns."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "This needs specialized CI/CD knowledge. I suggest handoff to devops for pipeline configuration.",
            current_agent="sre_principal_engineer_agent"
        )

        assert result.should_handoff is True
        assert result.target_agent == "devops"
        assert "handoff to devops" in result.detected_patterns
        assert result.confidence >= 0.8

    def test_explicit_recommend_pattern(self):
        """Test detection of 'recommend X agent' patterns."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "Given the security implications, I recommend security agent for a thorough audit.",
            current_agent="devops_principal_architect_agent"
        )

        assert result.should_handoff is True
        assert result.target_agent == "security"
        assert "recommend security agent" in result.detected_patterns
        assert result.confidence >= 0.8

    def test_domain_keyword_security(self):
        """Test domain keywords triggering security agent handoff."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "This configuration has authentication vulnerabilities and needs security hardening.",
            current_agent="sre_principal_engineer_agent"
        )

        assert result.should_handoff is True
        assert result.target_agent == "cloud_security_principal_agent"
        assert result.confidence >= 0.5
        assert result.confidence < 0.8  # Implicit detection = medium confidence

    def test_domain_keyword_infrastructure(self):
        """Test terraform/infrastructure keywords triggering infra agent."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "We need to update the terraform modules to provision the Azure infrastructure.",
            current_agent="devops_principal_architect_agent"
        )

        assert result.should_handoff is True
        assert result.target_agent == "azure_infrastructure_architect_agent"
        assert result.confidence >= 0.5
        assert result.confidence < 0.8

    def test_no_handoff_when_appropriate(self):
        """Test no handoff when task is complete and appropriate."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "The deployment pipeline has been configured successfully. All tests pass.",
            current_agent="devops_principal_architect_agent"
        )

        assert result.should_handoff is False
        assert result.target_agent is None
        assert result.confidence == 0.0
        assert len(result.detected_patterns) == 0

    def test_context_extraction(self):
        """Test key context extraction for handoff."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()
        result = detector.analyze(
            "I've identified three critical vulnerabilities in the auth module. "
            "Transfer_to_security_agent for remediation: CVE-2024-1234, CVE-2024-5678, and CVE-2024-9012.",
            current_agent="sre_principal_engineer_agent"
        )

        assert result.should_handoff is True
        assert result.context_to_pass is not None
        assert "CVE" in result.context_to_pass or "vulnerabilities" in result.context_to_pass

    def test_confidence_high_explicit(self):
        """Test explicit patterns have high confidence (>=0.8)."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()

        # Test multiple explicit patterns
        explicit_texts = [
            "transfer_to_security_agent",
            "handoff to devops",
            "recommend security agent",
            "this requires security expertise",
            "escalate to infrastructure",
        ]

        for text in explicit_texts:
            result = detector.analyze(text, current_agent="sre_principal_engineer_agent")
            assert result.should_handoff is True, f"Should handoff for: {text}"
            assert result.confidence >= 0.8, f"Confidence should be >= 0.8 for explicit pattern: {text}"

    def test_confidence_medium_implicit(self):
        """Test implicit domain patterns have medium confidence (0.5-0.7)."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()

        # Test domain keyword detection (implicit)
        result = detector.analyze(
            "There are authentication issues with the terraform deployment.",
            current_agent="sre_principal_engineer_agent"
        )

        assert result.should_handoff is True
        assert result.confidence >= 0.5
        assert result.confidence <= 0.7


class TestSubagentHandoffIntegration:
    """Integration tests for handoff detection."""

    def test_sre_to_security_handoff(self):
        """Test SRE result triggers appropriate security handoff."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()

        # Simulated SRE agent output with security concerns
        sre_output = """
        System analysis complete. Found the following issues:

        1. High memory usage on web-server-01 (resolved)
        2. Suspicious login attempts detected from IP 192.168.1.100
        3. SSL certificates expiring in 7 days

        The suspicious login attempts suggest a potential security breach.
        I recommend transfer_to_security_agent for investigation of the authentication anomalies.
        """

        result = detector.analyze(sre_output, current_agent="sre_principal_engineer_agent")

        assert result.should_handoff is True
        assert result.target_agent == "security_agent"
        assert "transfer_to_security_agent" in result.detected_patterns
        assert "authentication" in result.reason.lower() or "security" in result.reason.lower()

    def test_multi_domain_result(self):
        """Test multi-domain results pick best match."""
        from claude.tools.orchestration.subagent_handoff import (
            SubagentHandoffDetector,
        )

        detector = SubagentHandoffDetector()

        # Output mentioning multiple domains, but with explicit handoff
        multi_domain_output = """
        Analysis shows issues across multiple areas:
        - Security: authentication bypass vulnerability
        - Infrastructure: terraform state drift detected
        - CI/CD: pipeline failing at test stage

        The most critical issue is the authentication bypass.
        Escalate to security for immediate remediation.
        """

        result = detector.analyze(multi_domain_output, current_agent="sre_principal_engineer_agent")

        assert result.should_handoff is True
        # Should pick the explicit escalation target
        assert result.target_agent == "security"
        assert result.confidence >= 0.8  # Explicit pattern
