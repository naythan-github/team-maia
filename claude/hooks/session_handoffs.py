"""
Session Integration for Automatic Agent Handoffs

Integrates handoff functionality with Maia session state, providing:
- Session handoff state storage
- Context injection for handoffs
- Learning pattern capture
- Handoff recovery mechanisms

Sprint 3 of Automatic Agent Handoffs feature.
"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


# ==============================================================================
# Feature 3.1: Session Handoff State (F011)
# ==============================================================================

def add_handoff_to_session(session_file: Path, handoff: Dict[str, Any]) -> None:
    """
    Add a handoff record to the session state.

    Updates the session file with:
    - Appended handoff to handoff_chain
    - Updated current_agent
    - Preserved existing context

    Args:
        session_file: Path to session JSON file
        handoff: Handoff record with from, to, reason, optional timestamp
    """
    # Read existing session
    session = json.loads(session_file.read_text())

    # Update handoff chain
    if "handoff_chain" not in session:
        session["handoff_chain"] = []

    session["handoff_chain"].append(handoff)

    # Update current agent
    session["current_agent"] = handoff["to"]

    # Write atomically
    session_file.write_text(json.dumps(session, indent=2))


# ==============================================================================
# Feature 3.2: Handoff Context Injection (F012)
# ==============================================================================

def inject_handoff_context(target_agent: str, handoff_chain: List[Dict[str, Any]]) -> str:
    """
    Inject prior agent context into new agent prompt.

    Creates a formatted context string with:
    - Prior agent output
    - Handoff reasons
    - Truncation for long outputs (>2000 chars)

    Args:
        target_agent: Agent receiving the handoff
        handoff_chain: List of handoff records with from, to, output

    Returns:
        Formatted context string for injection
    """
    MAX_OUTPUT_LENGTH = 2000

    context_parts = []

    for handoff in handoff_chain:
        from_agent = handoff.get("from", "unknown")
        output = handoff.get("output", "")
        reason = handoff.get("reason", "")

        # Truncate long output
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + "... (truncated)"

        context_part = f"Prior work by {from_agent}:\n{output}"
        if reason:
            context_part += f"\nHandoff reason: {reason}"

        context_parts.append(context_part)

    return "\n\n".join(context_parts)


# ==============================================================================
# Feature 3.3: Learning Integration (F013)
# ==============================================================================

class HandoffPatternTracker:
    """
    Track handoff patterns for PAI v2 learning.

    Captures:
    - Successful/failed handoffs
    - Pattern frequencies
    - Cross-session persistence
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize pattern tracker.

        Args:
            storage_path: Optional path for pattern storage (defaults to temp)
        """
        if storage_path is None:
            import tempfile
            storage_path = Path(tempfile.gettempdir()) / "handoff_patterns_default.json"

        self.storage_path = storage_path
        self.patterns = []

        # Load existing patterns if file exists
        if self.storage_path.exists():
            self.patterns = json.loads(self.storage_path.read_text())

    def log_handoff(self, from_agent: str, to_agent: str, query: str, success: bool) -> None:
        """
        Log a handoff for pattern learning.

        Args:
            from_agent: Source agent
            to_agent: Target agent
            query: Query that triggered handoff
            success: Whether handoff succeeded
        """
        pattern = {
            "from": from_agent,
            "to": to_agent,
            "query": query,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        self.patterns.append(pattern)
        self._persist()

    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get all logged patterns."""
        return self.patterns

    def get_pattern_stats(self, from_agent: str, to_agent: str) -> Dict[str, Any]:
        """
        Get statistics for a specific handoff pattern.

        Args:
            from_agent: Source agent
            to_agent: Target agent

        Returns:
            Dict with count and success_rate
        """
        matching = [
            p for p in self.patterns
            if p["from"] == from_agent and p["to"] == to_agent
        ]

        if not matching:
            return {"count": 0, "success_rate": 0.0}

        success_count = sum(1 for p in matching if p["success"])

        return {
            "count": len(matching),
            "success_rate": success_count / len(matching)
        }

    def _persist(self) -> None:
        """Persist patterns to storage."""
        self.storage_path.write_text(json.dumps(self.patterns, indent=2))


# ==============================================================================
# Feature 3.4: Handoff Recovery (F014)
# ==============================================================================

@dataclass
class RecoveryResult:
    """Result of handoff recovery attempt."""
    recovered: bool
    fallback_agent: Optional[str]
    suggested_alternatives: List[str]
    error_logged: bool


class HandoffRecovery:
    """
    Recover from failed handoffs gracefully.

    Provides:
    - Agent not found handling
    - Fallback to source agent
    - Alternative agent suggestions
    - Failure logging
    """

    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize recovery handler.

        Args:
            log_path: Optional path for failure logs
        """
        if log_path is None:
            import tempfile
            log_path = Path(tempfile.gettempdir()) / "handoff_failures_default.json"

        self.log_path = log_path
        self.failures = []

        # Load existing failures if file exists
        if self.log_path.exists():
            self.failures = json.loads(self.log_path.read_text())

    def handle_failure(
        self,
        source_agent: str,
        target_agent: str,
        error: str,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """
        Handle a failed handoff.

        Args:
            source_agent: Agent that initiated handoff
            target_agent: Agent that failed to receive handoff
            error: Error message
            context: Additional context

        Returns:
            RecoveryResult with fallback and alternatives
        """
        # Log the failure
        failure_record = {
            "source_agent": source_agent,
            "target_agent": target_agent,
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

        self.failures.append(failure_record)
        self._persist()

        # Determine recovery strategy
        suggested_alternatives = []

        # For agent not found, suggest common alternatives
        if "not found" in error.lower():
            suggested_alternatives = self._suggest_alternatives(target_agent)

        return RecoveryResult(
            recovered=True,
            fallback_agent=source_agent,  # Always fallback to source
            suggested_alternatives=suggested_alternatives,
            error_logged=True
        )

    def _suggest_alternatives(self, failed_agent: str) -> List[str]:
        """
        Suggest alternative agents when target fails.

        Args:
            failed_agent: Agent that failed

        Returns:
            List of suggested alternatives (may be empty)
        """
        # Basic suggestion logic - can be enhanced
        suggestions_map = {
            "security_specialist": ["sre_principal", "infrastructure_specialist"],
            "sre_principal": ["infrastructure_specialist", "devops_engineer"],
            "infrastructure_specialist": ["sre_principal", "cloud_architect"]
        }

        return suggestions_map.get(failed_agent, [])

    def _persist(self) -> None:
        """Persist failure logs to storage."""
        self.log_path.write_text(json.dumps(self.failures, indent=2))
