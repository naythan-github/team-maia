#!/usr/bin/env python3
"""
Universal Output Capture System (UOCS)

Captures all tool outputs during a session for:
- Session replay and debugging
- VERIFY phase success measurement
- LEARN phase pattern extraction
- Kai summary generation input

Performance: <10ms overhead (async writes)
Storage: ~/.maia/outputs/{session_id}/
Retention: 7 days default (configurable)
"""

import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class CapturedOutput:
    """A single captured tool output."""
    capture_id: str
    tool_name: str
    timestamp: str
    input_hash: str
    output_path: Optional[str]
    output_size: int
    success: bool
    latency_ms: int
    capture_mode: str


class UOCS:
    """Universal Output Capture System."""

    # Capture modes by tool type
    CAPTURE_MODES = {
        'bash': 'output',        # Capture stdout/stderr
        'read': 'metadata',      # Just file path + size
        'write': 'metadata',     # Just file path
        'edit': 'diff',          # Capture the diff
        'grep': 'output',        # Capture matches
        'glob': 'output',        # Capture file list
        'task': 'metadata',      # Agent task summary
        'webfetch': 'summary',   # First 1000 chars
        'websearch': 'output',   # Search results
    }

    MAX_OUTPUT_SIZE = 100_000  # 100KB per capture

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.outputs_dir = Path.home() / ".maia" / "outputs" / session_id
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        self.captures: List[CapturedOutput] = []
        self.tool_counter = 0
        self._lock = threading.Lock()

    def capture(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        latency_ms: int
    ) -> str:
        """
        Capture a tool invocation (async, non-blocking).

        Returns capture_id.
        """
        self.tool_counter += 1
        capture_id = f"{self.tool_counter:04d}_{tool_name}"

        # Async capture to avoid blocking
        thread = threading.Thread(
            target=self._do_capture,
            args=(capture_id, tool_name, tool_input, tool_output, success, latency_ms),
            daemon=True
        )
        thread.start()

        return capture_id

    def _do_capture(
        self,
        capture_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        latency_ms: int
    ):
        """Actual capture logic (runs in thread)."""
        try:
            # Compute input hash for deduplication
            input_str = json.dumps(tool_input, sort_keys=True, default=str)
            input_hash = hashlib.sha256(input_str.encode()).hexdigest()[:16]

            # Determine capture mode
            capture_mode = self.CAPTURE_MODES.get(tool_name.lower(), 'metadata')

            # Capture based on mode
            output_path = None
            output_size = 0

            if capture_mode == 'output':
                content = self._truncate(str(tool_output))
                output_path = self.outputs_dir / f"{capture_id}.txt"
                output_path.write_text(content)
                output_size = len(content)

            elif capture_mode == 'diff':
                content = self._extract_diff(tool_input, tool_output)
                if content:
                    output_path = self.outputs_dir / f"{capture_id}.diff"
                    output_path.write_text(content)
                    output_size = len(content)

            elif capture_mode == 'summary':
                content = self._truncate(str(tool_output), 1000)
                output_path = self.outputs_dir / f"{capture_id}.txt"
                output_path.write_text(content)
                output_size = len(content)

            # metadata mode: no content saved

            # Record capture
            captured = CapturedOutput(
                capture_id=capture_id,
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
                input_hash=input_hash,
                output_path=str(output_path) if output_path else None,
                output_size=output_size,
                success=success,
                latency_ms=latency_ms,
                capture_mode=capture_mode
            )

            with self._lock:
                self.captures.append(captured)
                self._write_manifest()

        except Exception:
            # Never fail - graceful degradation
            pass

    def _truncate(self, content: str, max_size: int = None) -> str:
        """Truncate content to max size."""
        max_size = max_size or self.MAX_OUTPUT_SIZE
        if len(content) > max_size:
            return content[:max_size] + f"\n... [TRUNCATED at {max_size} bytes]"
        return content

    def _extract_diff(self, tool_input: Dict, tool_output: Any) -> Optional[str]:
        """Extract diff from edit operations."""
        if 'old_string' in tool_input and 'new_string' in tool_input:
            return f"--- old\n+++ new\n-{tool_input['old_string']}\n+{tool_input['new_string']}"
        return None

    def _write_manifest(self):
        """Write manifest to disk."""
        manifest = {
            'session_id': self.session_id,
            'capture_count': len(self.captures),
            'captures': [asdict(c) for c in self.captures]
        }
        manifest_path = self.outputs_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

    def get_summary(self) -> Dict[str, Any]:
        """Get session capture summary for Kai."""
        tools_used = {}
        total_latency = 0
        success_count = 0

        for c in self.captures:
            tools_used[c.tool_name] = tools_used.get(c.tool_name, 0) + 1
            total_latency += c.latency_ms
            if c.success:
                success_count += 1

        return {
            'session_id': self.session_id,
            'total_captures': len(self.captures),
            'tools_used': tools_used,
            'success_rate': success_count / max(len(self.captures), 1),
            'total_latency_ms': total_latency,
            'total_size_bytes': sum(c.output_size for c in self.captures)
        }

    def finalize(self) -> Dict[str, Any]:
        """Finalize session - write summary."""
        summary = self.get_summary()
        summary_path = self.outputs_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2))
        return summary


# Singleton per session
_active_uocs: Dict[str, UOCS] = {}


def get_uocs(session_id: str) -> UOCS:
    """Get or create UOCS for session."""
    if session_id not in _active_uocs:
        _active_uocs[session_id] = UOCS(session_id)
    return _active_uocs[session_id]


def close_uocs(session_id: str) -> Optional[Dict[str, Any]]:
    """Close and finalize UOCS for session."""
    if session_id in _active_uocs:
        summary = _active_uocs[session_id].finalize()
        del _active_uocs[session_id]
        return summary
    return None


__all__ = ["UOCS", "CapturedOutput", "get_uocs", "close_uocs", "_active_uocs"]
