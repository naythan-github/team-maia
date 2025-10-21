#!/usr/bin/env python3
"""
Swarm Auto-Loader - Stage 0.8 Enhancement for Automatic Agent Persistence
Phase 134 - Implement Working Principle #15
Phase 134.3 - Per-Context Isolation (Multi-Context Concurrency Fix)

Purpose:
- Invoke SwarmOrchestrator when routing confidence >70% and complexity >3
- Create session state file for Maia agent context loading
- Per-context isolation (each Claude Code window has independent session)
- Graceful degradation for all error scenarios
- Background logging integration with Phase 125

Performance SLA: <200ms (target <50ms)
Reliability SLA: 100% graceful degradation (no blocking failures)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess

# Maia root detection (claude/hooks/swarm_auto_loader.py -> go up 2 levels to repo root)
MAIA_ROOT = Path(__file__).parent.parent.parent.absolute()

# Performance tracking
import time
start_time = time.time()


def get_context_id() -> str:
    """
    Generate stable context ID for this Claude Code window.

    Phase 134.3: Per-context isolation to prevent race conditions
    when multiple Claude Code contexts are open simultaneously.

    Strategy:
    1. Check for CLAUDE_SESSION_ID env var (if Claude provides it)
    2. Fall back to PPID (parent process ID - stable per window)
    3. Ensures each context window has independent agent session

    Returns:
        Stable context identifier (e.g., "context_12345")
    """
    # Option 1: Claude-provided session ID (if available)
    if session_id := os.getenv("CLAUDE_SESSION_ID"):
        return session_id

    # Option 2: Parent PID (stable per terminal/window)
    # Each Claude Code window = different PPID = different context
    ppid = os.getppid()
    return f"context_{ppid}"


def get_session_file_path() -> Path:
    """
    Get session state file path for current context.

    Phase 134.3: Context-specific session files prevent concurrency issues.

    Returns:
        Path to session file for this context
        Example: /tmp/maia_active_swarm_session_context_12345.json
    """
    context_id = get_context_id()
    return Path(f"/tmp/maia_active_swarm_session_{context_id}.json")


def migrate_legacy_session():
    """
    One-time migration: old global session → new context-specific session.

    Phase 134.3: Backward compatibility for existing sessions.
    Migrates /tmp/maia_active_swarm_session.json → context-specific file.
    """
    old_session = Path("/tmp/maia_active_swarm_session.json")
    new_session = get_session_file_path()

    # Only migrate if old exists and new doesn't
    if old_session.exists() and not new_session.exists():
        try:
            old_session.rename(new_session)
        except OSError:
            pass  # Graceful degradation


def cleanup_stale_sessions(max_age_hours: int = 24):
    """
    Remove session files older than max_age_hours.

    Phase 134.3: Prevent /tmp pollution from abandoned contexts.
    Runs on every startup (fast: glob + stat).

    Args:
        max_age_hours: Maximum session age in hours (default: 24)
    """
    cutoff_time = time.time() - (max_age_hours * 3600)

    try:
        for session_file in Path("/tmp").glob("maia_active_swarm_session_*.json"):
            try:
                if session_file.stat().st_mtime < cutoff_time:
                    session_file.unlink()
            except OSError:
                pass  # Graceful degradation (file may be locked or deleted)
    except Exception:
        pass  # Graceful degradation


# Session state file (context-specific)
SESSION_STATE_FILE = get_session_file_path()


def classify_query(query: str) -> Optional[Dict[str, Any]]:
    """
    Classify user query using coordinator agent.

    Returns classification result or None if classification fails.
    Performance target: <500ms (coordinator startup + classification)
    """
    try:
        coordinator_cli = MAIA_ROOT / "claude/tools/orchestration/coordinator_agent.py"
        if not coordinator_cli.exists():
            return None

        # Run classification with JSON output (Phase 134 enhancement)
        result = subprocess.run(
            [sys.executable, str(coordinator_cli), "classify", query, "--json"],
            capture_output=True,
            text=True,
            timeout=0.5  # 500ms timeout (coordinator needs startup time)
        )

        # Return code handling:
        # 0 = routing available
        # 1 = classification error
        # 2 = no routing needed (low confidence/complexity)
        if result.returncode == 1:
            return None  # Error

        if result.returncode == 2:
            return None  # No routing needed

        # Parse JSON output (return code 0)
        data = json.loads(result.stdout)

        # Check if routing needed
        if not data.get("routing_needed", False):
            return None

        # Extract classification fields
        intent = data.get("intent", {})
        routing = data.get("routing", {})

        classification = {
            "confidence": intent.get("confidence", 0),
            "complexity": intent.get("complexity", 0),
            "primary_domain": intent.get("primary_domain", "general"),
            "suggested_agent": routing.get("initial_agent"),
            "strategy": routing.get("strategy"),
            "reasoning": routing.get("reasoning")
        }

        return classification

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        # Graceful degradation: classification failure is non-fatal
        return None


def should_invoke_swarm(classification: Dict[str, Any]) -> bool:
    """
    Determine if swarm orchestrator should be invoked.

    Criteria (from TDD requirements):
    - Confidence >70%
    - Complexity ≥3 (changed from >3 to match requirements)
    - Domain is not "general"
    """
    if not classification:
        return False

    confidence = classification.get("confidence", 0)
    complexity = classification.get("complexity", 0)
    domain = classification.get("primary_domain", "general")

    return (
        confidence > 0.70 and
        complexity >= 3 and  # ≥3 not >3 (TDD requirement alignment)
        domain != "general"
    )


def get_agent_for_domain(domain: str) -> Optional[str]:
    """
    Map domain to agent filename.

    Returns agent name (without .md extension) or None if no mapping.
    """
    # Domain → Agent mapping (based on Phase 121 coordinator)
    domain_agent_map = {
        "security": "security_specialist_agent",
        "azure": "azure_solutions_architect_agent",
        "cloud": "azure_solutions_architect_agent",
        "devops": "devops_principal_architect_agent",
        "sre": "sre_principal_engineer_agent",
        "reliability": "sre_principal_engineer_agent",
        "finops": "finops_agent",
        "cost_optimization": "finops_agent",
        "recruitment": "technical_recruitment_agent",
        "servicedesk": "service_desk_manager_agent",
        "identity": "principal_idam_engineer_agent",
        "idam": "principal_idam_engineer_agent",
        "endpoint": "principal_endpoint_engineer_agent",
        "dns": "dns_specialist_agent",
        "information": "information_management_orchestrator_agent",
        "stakeholder": "stakeholder_intelligence_agent",
        "decision": "decision_intelligence_agent",
        "job_search": "jobs_agent",
        "linkedin": "linkedin_ai_advisor_agent",
        "financial": "financial_advisor_agent",
        "confluence": "confluence_organization_agent",
        "content": "team_knowledge_sharing_agent",
        "ai_systems": "ai_specialists_agent",
        "prompt_engineering": "prompt_engineer_agent",
        "tokens": "token_optimization_agent",
        "development": "developer_agent",
        "architecture": "software_architect_agent",
        "data": "azure_data_engineer_agent",
        "cooking": "asian_low_sodium_cooking_agent",
        "cocktail": "cocktail_mixologist_agent",
        "restaurant": "perth_restaurant_discovery_agent",
        "travel": "travel_monitor_alert_agent",
        "holiday": "holiday_research_agent",
        "personal": "personal_assistant_agent",
    }

    return domain_agent_map.get(domain)


def create_session_state(
    agent: str,
    domain: str,
    classification: Dict[str, Any],
    query: str
) -> bool:
    """
    Create session state file for Maia agent context loading (Phase 5 - with handoff support).

    File: /tmp/maia_active_swarm_session.json
    Format:
    {
        "current_agent": "security_specialist_agent",
        "session_start": "2025-10-20T14:30:00",
        "handoff_chain": ["finops_agent", "security_specialist_agent"],
        "context": {"previous_work": "..."},
        "domain": "security",
        "last_classification_confidence": 0.87,
        "query": "Review code for security"
    }

    Returns True if successful, False otherwise.
    Performance target: <5ms (atomic write)
    """
    try:
        # Check for existing session to preserve context and handoff chain
        existing_context = {}
        session_start = datetime.utcnow().isoformat()

        # Determine handoff chain (priority order):
        # 1. Classification has handoff_chain (domain change already calculated it)
        # 2. No existing session (first agent load)
        # 3. Existing session, same domain (preserve existing chain)
        if "handoff_chain" in classification:
            # Domain change case: classification already computed new chain
            existing_handoff_chain = classification["handoff_chain"]
        else:
            # Default: single agent (will be overridden if session exists)
            existing_handoff_chain = [agent]

        if SESSION_STATE_FILE.exists():
            try:
                with open(SESSION_STATE_FILE, 'r') as f:
                    existing_session = json.load(f)
                    existing_context = existing_session.get("context", {})
                    # Preserve session start for continuity
                    session_start = existing_session.get("session_start", session_start)

                    # If classification didn't set handoff_chain, preserve existing
                    if "handoff_chain" not in classification:
                        existing_handoff_chain = existing_session.get("handoff_chain", [agent])
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults

        session_data = {
            "current_agent": agent,
            "session_start": session_start,
            "handoff_chain": existing_handoff_chain,
            "context": existing_context,  # Preserve context across handoffs
            "domain": domain,
            "last_classification_confidence": classification.get("confidence", 0),
            "last_classification_complexity": classification.get("complexity", 0),
            "query": query[:200],  # Truncate for file size
            "handoff_reason": classification.get("handoff_reason"),  # Phase 5: Track why handoff occurred
            "created_by": "swarm_auto_loader.py",
            "version": "1.1"  # Phase 5 version
        }

        # Atomic write (tmp file + rename for consistency)
        tmp_file = SESSION_STATE_FILE.with_suffix(".tmp")
        with open(tmp_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Atomic rename
        tmp_file.replace(SESSION_STATE_FILE)

        # Set secure permissions (600 - user only)
        SESSION_STATE_FILE.chmod(0o600)

        return True

    except Exception as e:
        # Graceful degradation: session state failure is non-fatal
        # Log error but don't block conversation
        log_error(f"Failed to create session state: {e}")
        return False


def invoke_swarm_orchestrator(
    agent: str,
    query: str,
    classification: Dict[str, Any]
) -> bool:
    """
    Invoke SwarmOrchestrator with specified initial agent.

    NOTE: For Phase 2, we ONLY create session state (not full swarm execution).
    Full swarm integration happens in Phase 3.

    Phase 2 goal: Hook creates session state → Maia reads on startup
    Phase 3 goal: Hook invokes swarm → Swarm executes agent → Context enrichment

    Returns True if session state created successfully.
    Performance target: <50ms
    """
    # Phase 2: Create session state file (Maia will read this on startup)
    success = create_session_state(agent, classification.get("primary_domain"), classification, query)

    # Phase 3 TODO: Replace with actual SwarmOrchestrator invocation
    # swarm = SwarmOrchestrator(agent_dir=MAIA_ROOT / "claude/agents")
    # result = swarm.execute_with_handoffs(
    #     initial_agent=agent,
    #     task={"query": query, "domain": classification.get("primary_domain")},
    #     max_handoffs=5
    # )

    return success


def log_routing_decision(
    classification: Dict[str, Any],
    agent_loaded: Optional[str],
    success: bool,
    duration_ms: float
):
    """
    Log routing decision for Phase 125 accuracy tracking.

    Logs to routing_decisions.db via routing_decision_logger.py.
    Non-blocking (background logging).
    """
    try:
        logger_cli = MAIA_ROOT / "claude/tools/orchestration/routing_decision_logger.py"
        if not logger_cli.exists():
            return

        # Background logging (non-blocking)
        log_data = json.dumps({
            "classification": classification,
            "agent_loaded": agent_loaded,
            "success": success,
            "duration_ms": duration_ms
        })

        subprocess.Popen(
            [sys.executable, str(logger_cli), "log", log_data],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception:
        # Graceful degradation: logging failure is non-fatal
        pass


def log_error(message: str):
    """Log error to stderr for debugging (non-blocking)."""
    print(f"[swarm_auto_loader ERROR] {message}", file=sys.stderr)


def main():
    """
    Main entry point for swarm auto-loader.

    Usage:
        python3 swarm_auto_loader.py "user query"

    Exit codes:
        0: Success (agent loaded or gracefully degraded)
        Non-zero: Not used (all failures degrade gracefully)
    """
    # Phase 134.3: Cleanup stale sessions + migrate legacy session
    migrate_legacy_session()
    cleanup_stale_sessions(max_age_hours=24)

    # Validate arguments
    if len(sys.argv) < 2:
        # No query provided - graceful exit (hook may call without query)
        sys.exit(0)

    query = sys.argv[1]

    try:
        # Step 1: Classify query (10ms target)
        classification = classify_query(query)
        if not classification:
            # Classification failed - graceful degradation (no agent loading)
            sys.exit(0)

        # Step 2: Check if swarm invocation needed
        if not should_invoke_swarm(classification):
            # Low confidence or simple query - no agent needed
            sys.exit(0)

        # Step 3: Get agent from coordinator suggestion (Phase 134 - use coordinator's choice directly)
        agent = classification.get("suggested_agent")

        if not agent:
            # No agent suggested - graceful degradation
            log_routing_decision(classification, None, False, (time.time() - start_time) * 1000)
            sys.exit(0)

        # Step 4: Check for existing session (Phase 5 - Domain change detection)
        existing_session = None
        if SESSION_STATE_FILE.exists():
            try:
                with open(SESSION_STATE_FILE, 'r') as f:
                    existing_session = json.load(f)
            except (json.JSONDecodeError, IOError):
                # Corrupted session - will create new one
                existing_session = None

        # Detect domain change
        domain_changed = False
        if existing_session:
            current_domain = classification.get("primary_domain", "general")
            previous_domain = existing_session.get("domain", "general")
            previous_agent = existing_session.get("current_agent")

            # Domain changed if:
            # 1. Different domain AND
            # 2. New domain confidence >70% AND
            # 3. Either: a) New confidence ≥9% higher than previous, OR
            #            b) Both confidences are ≥70% (both high-confidence classifications)
            if current_domain != previous_domain:
                new_confidence = classification.get("confidence", 0)
                prev_confidence = existing_session.get("last_classification_confidence", 0)

                # Accept domain change if new domain is high confidence
                # Allow if: new much higher than old, OR both are high confidence
                confidence_delta_significant = (new_confidence - prev_confidence) >= 0.09
                both_high_confidence = new_confidence >= 0.70 and prev_confidence >= 0.70

                if new_confidence > 0.70 and (confidence_delta_significant or both_high_confidence):
                    domain_changed = True
                    # Update handoff chain
                    existing_handoff_chain = existing_session.get("handoff_chain", [])
                    classification["handoff_chain"] = existing_handoff_chain + [agent]
                    classification["handoff_reason"] = f"Domain change: {previous_domain} → {current_domain}"

        # Step 5: Verify agent file exists (try with _agent suffix)
        agent_file = MAIA_ROOT / f"claude/agents/{agent}_agent.md"
        if not agent_file.exists():
            # Try without _agent suffix
            agent_file = MAIA_ROOT / f"claude/agents/{agent}.md"
        if not agent_file.exists():
            # Agent file missing - graceful degradation
            log_error(f"Agent file not found: {agent_file}")
            log_routing_decision(classification, agent, False, (time.time() - start_time) * 1000)
            sys.exit(0)

        # Step 6: Invoke swarm orchestrator (Phase 2-5: session state with handoff tracking)
        success = invoke_swarm_orchestrator(agent, query, classification)

        # Step 6: Log routing decision (background)
        duration_ms = (time.time() - start_time) * 1000
        log_routing_decision(classification, agent if success else None, success, duration_ms)

        # Performance check (warn if >200ms)
        if duration_ms > 200:
            log_error(f"Performance SLA violation: {duration_ms:.1f}ms (target <200ms)")

        # Always exit 0 (graceful degradation)
        sys.exit(0)

    except Exception as e:
        # Catch-all graceful degradation
        log_error(f"Unexpected error: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
