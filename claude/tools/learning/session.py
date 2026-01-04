#!/usr/bin/env python3
"""
Session Lifecycle Orchestrator

Coordinates all PAI v2 components:
- Session start: Initialize UOCS, load context
- Session end: VERIFY, LEARN, generate Maia Memory summary
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from claude.tools.learning.uocs import get_uocs, close_uocs
from claude.tools.learning.memory import get_memory
from claude.tools.learning.verify import get_verify
from claude.tools.learning.learn import get_learn


class SessionManager:
    """Manages the complete session lifecycle."""

    def __init__(self):
        self.memory = get_memory()
        self.verify = get_verify()
        self.learn = get_learn()
        self._active_session: Optional[str] = None
        self._session_data: Dict[str, Any] = {}

    def start_session(
        self,
        context_id: str,
        initial_query: str,
        agent_used: Optional[str] = None,
        domain: Optional[str] = None
    ) -> str:
        """
        Start a new learning session.

        Called from user-prompt-submit hook on first prompt.
        """
        session_id = f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Initialize UOCS
        get_uocs(session_id)

        # Record in Maia Memory
        self.memory.start_session(
            session_id=session_id,
            context_id=context_id,
            initial_query=initial_query,
            agent_used=agent_used,
            domain=domain
        )

        # Store session data
        self._active_session = session_id
        self._session_data = {
            'session_id': session_id,
            'context_id': context_id,
            'initial_query': initial_query,
            'agent_used': agent_used,
            'domain': domain,
            'started_at': datetime.now().isoformat()
        }

        return session_id

    def capture_tool_output(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        latency_ms: int
    ):
        """
        Capture a tool output.

        Called from tool-output hook (if available) or manually.
        """
        if not self._active_session:
            return

        uocs = get_uocs(self._active_session)
        uocs.capture(tool_name, tool_input, tool_output, success, latency_ms)

    def end_session(self, status: str = 'completed') -> Dict[str, Any]:
        """
        End the session and run VERIFY + LEARN.

        Called from /close-session command.
        """
        if not self._active_session:
            return {'error': 'No active session'}

        session_id = self._active_session

        # Finalize UOCS
        uocs_summary = close_uocs(session_id)
        if not uocs_summary:
            uocs_summary = {'total_captures': 0, 'tools_used': {}, 'success_rate': 0}

        # Run VERIFY
        verify_result = self.verify.verify(uocs_summary, self._session_data)

        # Run LEARN (only from successful sessions)
        learn_insights = self.learn.learn(
            session_id=session_id,
            uocs_summary=uocs_summary,
            session_data=self._session_data,
            verify_success=verify_result.success
        )

        # Generate summary
        summary_text = self._generate_summary(uocs_summary, verify_result)
        key_decisions = self._extract_decisions()

        # Record in Maia Memory
        self.memory.end_session(
            session_id=session_id,
            summary_text=summary_text,
            key_decisions=key_decisions,
            tools_used=uocs_summary.get('tools_used', {}),
            files_touched=[],  # TODO: extract from UOCS
            verify_success=verify_result.success,
            verify_confidence=verify_result.confidence,
            verify_metrics=verify_result.metrics,
            learn_insights=self.learn.to_dict(learn_insights),
            status=status
        )

        # Clear active session
        self._active_session = None
        result = {
            'session_id': session_id,
            'verify': self.verify.to_dict(verify_result),
            'learn': self.learn.to_dict(learn_insights),
            'summary': summary_text
        }
        self._session_data = {}

        return result

    def _generate_summary(self, uocs_summary: Dict, verify_result) -> str:
        """Generate human-readable summary."""
        tools = uocs_summary.get('tools_used', {})
        top_tools = sorted(tools.items(), key=lambda x: x[1], reverse=True)[:5]

        parts = [
            f"Session {'completed successfully' if verify_result.success else 'had issues'}.",
            f"Used {uocs_summary.get('total_captures', 0)} tool calls.",
        ]

        if top_tools:
            parts.append(f"Primary tools: {', '.join(t[0] for t in top_tools)}.")

        parts.append(f"Confidence: {verify_result.confidence:.0%}")

        return " ".join(parts)

    def _extract_decisions(self) -> List[str]:
        """Extract key decisions (placeholder - could use LLM)."""
        # For now, return empty - could be enhanced with LLM summarization
        return []

    def get_relevant_context(self, query: str) -> str:
        """Get relevant context from Maia Memory for a new query."""
        return self.memory.get_context_for_query(query)

    @property
    def active_session_id(self) -> Optional[str]:
        return self._active_session


# Singleton
_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get SessionManager singleton."""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager


__all__ = ["SessionManager", "get_session_manager"]
