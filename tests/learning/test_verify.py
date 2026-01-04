#!/usr/bin/env python3
"""
Tests for Phase 4: VERIFY Phase (TDD)

Tests session success measurement across multiple dimensions.
"""

import pytest
from dataclasses import asdict


class TestVerifyPhaseBasic:
    """Tests for basic VERIFY functionality."""

    def test_verify_returns_result_dataclass(self):
        """Test that verify returns a VerifyResult dataclass."""
        from claude.tools.learning.verify import VerifyPhase, VerifyResult

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.9,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
        }

        result = verify.verify(uocs_summary, {})

        assert isinstance(result, VerifyResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'insights')

    def test_verify_successful_session(self):
        """Test VERIFY on a successful session."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.9,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 5, 'read': 3, 'edit': 2}
        }

        result = verify.verify(uocs_summary, {})

        assert result.success is True
        assert result.confidence >= 0.7

    def test_verify_failed_session(self):
        """Test VERIFY on a failed session."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 5,
            'success_rate': 0.2,
            'total_latency_ms': 10000,
            'tools_used': {'bash': 5}
        }

        result = verify.verify(uocs_summary, {})

        assert result.success is False
        assert result.confidence < 0.7

    def test_verify_empty_session(self):
        """Test VERIFY on an empty session."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 0,
            'success_rate': 0,
            'total_latency_ms': 0,
            'tools_used': {}
        }

        result = verify.verify(uocs_summary, {})

        # Empty session should not be considered successful
        assert result.success is False


class TestVerifyMetrics:
    """Tests for VERIFY metrics calculation."""

    def test_tool_success_rate_metric(self):
        """Test that tool_success_rate metric is calculated."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.85,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})

        assert 'tool_success_rate' in result.metrics
        assert result.metrics['tool_success_rate'] == 0.85

    def test_task_completion_metric(self):
        """Test that task_completion metric is calculated."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 15,
            'success_rate': 0.9,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 10, 'read': 5}
        }

        result = verify.verify(uocs_summary, {})

        assert 'task_completion' in result.metrics
        assert result.metrics['task_completion'] > 0

    def test_error_recovery_metric(self):
        """Test that error_recovery metric is calculated."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        # Session with some failures but overall success
        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.7,  # Some failures recovered
            'total_latency_ms': 5000,
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})

        assert 'error_recovery' in result.metrics

    def test_efficiency_metric(self):
        """Test that efficiency metric is calculated."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.9,
            'total_latency_ms': 2000,  # Fast session
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})

        assert 'efficiency' in result.metrics


class TestVerifyInsights:
    """Tests for VERIFY insights generation."""

    def test_low_success_rate_insight(self):
        """Test that low success rate generates insight."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.5,  # Below 80% threshold
            'total_latency_ms': 5000,
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})

        # Should have insight about low success rate
        assert len(result.insights) > 0
        assert any('success rate' in i.lower() or 'below' in i.lower() for i in result.insights)

    def test_successful_session_insight(self):
        """Test that successful session generates positive insight."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.95,
            'total_latency_ms': 3000,
            'tools_used': {'bash': 5, 'read': 5}
        }

        result = verify.verify(uocs_summary, {})

        # Should have insight about success
        assert len(result.insights) > 0
        assert any('success' in i.lower() for i in result.insights)


class TestVerifyThresholds:
    """Tests for VERIFY threshold behavior."""

    def test_threshold_boundary_below(self):
        """Test session just below success threshold."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        # Craft a session that should be just below 0.7 threshold
        uocs_summary = {
            'total_captures': 5,
            'success_rate': 0.5,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 5}
        }

        result = verify.verify(uocs_summary, {})

        assert result.success is False
        assert result.confidence < 0.7

    def test_threshold_boundary_above(self):
        """Test session just above success threshold."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        # Craft a session that should be just above 0.7 threshold
        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.85,
            'total_latency_ms': 3000,
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})

        assert result.success is True
        assert result.confidence >= 0.7


class TestVerifyToDict:
    """Tests for VerifyResult serialization."""

    def test_to_dict_returns_dict(self):
        """Test that to_dict returns a dictionary."""
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.9,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})
        result_dict = verify.to_dict(result)

        assert isinstance(result_dict, dict)
        assert 'success' in result_dict
        assert 'confidence' in result_dict
        assert 'metrics' in result_dict
        assert 'insights' in result_dict

    def test_to_dict_serializable(self):
        """Test that to_dict result is JSON serializable."""
        import json
        from claude.tools.learning.verify import VerifyPhase

        verify = VerifyPhase()

        uocs_summary = {
            'total_captures': 10,
            'success_rate': 0.9,
            'total_latency_ms': 5000,
            'tools_used': {'bash': 10}
        }

        result = verify.verify(uocs_summary, {})
        result_dict = verify.to_dict(result)

        # Should not raise
        json_str = json.dumps(result_dict)
        assert json_str is not None


class TestVerifySingleton:
    """Tests for VERIFY singleton pattern."""

    def test_get_verify_returns_singleton(self):
        """Test that get_verify returns same instance."""
        import claude.tools.learning.verify as verify_module
        verify_module._verify = None  # Reset singleton

        from claude.tools.learning.verify import get_verify

        v1 = get_verify()
        v2 = get_verify()

        assert v1 is v2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
