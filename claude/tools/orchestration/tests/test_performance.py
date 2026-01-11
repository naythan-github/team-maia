"""Performance benchmarks for handoff system."""

import pytest
import time
import json
import tempfile
from pathlib import Path
from claude.tools.orchestration.handoff_executor import detect_handoff
from claude.hooks.session_handoffs import inject_handoff_context, add_handoff_to_session
from claude.tools.orchestration.handoff_generator import build_handoff_context


class TestPerformanceBenchmarks:
    """Performance benchmarks for handoff system."""

    def test_handoff_detection_under_10ms(self):
        """Handoff detection completes in under 10ms."""
        response = {
            "content": [
                {"type": "text", "text": "Some analysis output"},
                {"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": {"data": "test"}}}
            ]
        }

        times = []
        for _ in range(100):
            start = time.perf_counter()
            detect_handoff(response)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 10, f"Average detection time {avg_time:.2f}ms exceeds 10ms"
        assert max_time < 50, f"Max detection time {max_time:.2f}ms exceeds 50ms"

    def test_context_injection_under_50ms(self):
        """Context injection completes in under 50ms."""
        handoff_chain = [
            {"from": f"agent_{i}", "to": f"agent_{i+1}", "output": f"Output {i}" * 100, "reason": "Test"}
            for i in range(5)
        ]

        times = []
        for _ in range(50):
            start = time.perf_counter()
            inject_handoff_context("target_agent", handoff_chain)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        assert avg_time < 50, f"Average injection time {avg_time:.2f}ms exceeds 50ms"

    def test_session_update_under_20ms(self):
        """Session update completes in under 20ms."""
        session_file = Path(tempfile.gettempdir()) / "test_perf_session.json"

        session = {
            "current_agent": "start",
            "handoff_chain": ["start"],
            "context": {"data": "x" * 1000}
        }
        session_file.write_text(json.dumps(session))

        times = []
        for i in range(50):
            start = time.perf_counter()
            add_handoff_to_session(session_file, {
                "from": f"agent_{i}",
                "to": f"agent_{i+1}",
                "reason": "Performance test"
            })
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        assert avg_time < 20, f"Average session update time {avg_time:.2f}ms exceeds 20ms"

    def test_context_build_under_10ms(self):
        """Context building completes in under 10ms."""
        current_context = {"query": "Test", "data": "x" * 500}
        agent_output = "Analysis complete. " * 50

        times = []
        for _ in range(100):
            start = time.perf_counter()
            build_handoff_context(
                current_context=current_context,
                agent_output=agent_output,
                source_agent="test_agent",
                handoff_reason="Test reason"
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        assert avg_time < 10, f"Average context build time {avg_time:.2f}ms exceeds 10ms"

    def test_total_handoff_overhead_under_100ms(self):
        """Total overhead per handoff under 100ms (excluding API call)."""
        session_file = Path(tempfile.gettempdir()) / "test_total_overhead.json"

        session = {
            "current_agent": "agent_a",
            "handoff_chain": ["agent_a"],
            "context": {"initial": "data"}
        }
        session_file.write_text(json.dumps(session))

        response = {
            "content": [{"type": "tool_use", "name": "transfer_to_agent_b", "input": {"context": {}}}]
        }
        handoff_chain = [{"from": "agent_a", "to": "agent_b", "output": "Work done", "reason": "Needed expertise"}]

        times = []
        for _ in range(20):
            start = time.perf_counter()

            # Full handoff processing (minus API call)
            detect_handoff(response)
            inject_handoff_context("agent_b", handoff_chain)
            build_handoff_context({"query": "Test"}, "Output", "agent_a", "Reason")
            add_handoff_to_session(session_file, {
                "from": "agent_a",
                "to": "agent_b",
                "reason": "Test"
            })

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        assert avg_time < 100, f"Average total overhead {avg_time:.2f}ms exceeds 100ms"
