#!/usr/bin/env python3
"""
Swarm Auto-Loader - Stage 0.8 Enhancement for Automatic Agent Persistence
Phase 134 - Implement Working Principle #15
Phase 134.3 - Per-Context Isolation (Multi-Context Concurrency Fix)
Phase 176 - Default Agent Loading + Recovery Protocol
Phase 228 - Threshold Optimization (60% confidence, capability gap detection)
Phase 229 - Agent Mandate Injection (mandatory agent loading)
Phase 232 - PAI v2 Learning System Integration (session start + VERIFY/LEARN on close)

Purpose:
- Invoke SwarmOrchestrator when routing confidence >=60% and complexity >=3
- Create session state file for Maia agent context loading
- Per-context isolation (each Claude Code window has independent session)
- Default agent loading (sre_principal_engineer_agent when no session exists)
- Recovery protocol integration (checkpoint + git context)
- Agent mandate injection (injects actual agent .md content into Claude's context)
- Capability gap detection and agent recommendation
- PAI v2 learning session lifecycle (start on session create, VERIFY+LEARN on close)
- Graceful degradation for all error scenarios
- Background logging integration with Phase 125

Performance SLA: <200ms (target <50ms)
Reliability SLA: 100% graceful degradation (no blocking failures)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import subprocess

# Maia root detection (claude/hooks/swarm_auto_loader.py -> go up 2 levels to repo root)
MAIA_ROOT = Path(__file__).parent.parent.parent.absolute()

# Phase 228: Capability gap detection file paths
CAPABILITY_GAPS_FILE = MAIA_ROOT / "claude" / "data" / "capability_gaps.json"
AGENT_RECOMMENDATIONS_FILE = MAIA_ROOT / "claude" / "data" / "agent_recommendations.json"

# Phase 228: Threshold constants
AGENT_LOADING_THRESHOLD = 0.60  # Lowered from 0.70 for specialist-first routing
CAPABILITY_GAP_THRESHOLD = 0.40  # Below this = capability gap
GAP_RECOMMENDATION_COUNT = 3    # Gaps needed to recommend new agent
GAP_RECOMMENDATION_DAYS = 7     # Window for counting gaps

# Performance tracking
import time
start_time = time.time()

# Context ID cache (Phase 135.6: Performance optimization - cache expensive process tree walk)
_CONTEXT_ID_CACHE = None


def get_context_id() -> str:
    """
    Generate stable context ID for this Claude Code window.

    Phase 134.3: Per-context isolation to prevent race conditions
    when multiple Claude Code contexts are open simultaneously.
    Phase 134.4: Fix PPID instability by walking process tree to Claude binary
    Phase 135.6: Cache result to avoid repeated process tree walks (121ms → <5ms)

    Strategy:
    1. Check for CLAUDE_SESSION_ID env var (if Claude provides it)
    2. Walk process tree to find stable Claude Code binary PID
    3. Fall back to PPID if tree walk fails
    4. Ensures each context window has independent agent session

    Returns:
        Stable context identifier (e.g., "context_12345")
    """
    global _CONTEXT_ID_CACHE

    # Return cached value if available (99% of calls)
    if _CONTEXT_ID_CACHE is not None:
        return _CONTEXT_ID_CACHE

    # Option 1: Claude-provided session ID (if available)
    if session_id := os.getenv("CLAUDE_SESSION_ID"):
        _CONTEXT_ID_CACHE = session_id
        return session_id

    # Option 2: Walk process tree to find stable Claude Code binary
    # This PID is stable across all subprocess invocations in same window
    try:
        current_pid = os.getpid()
        visited = set()  # Prevent infinite loops

        # Walk up process tree looking for Claude Code binary
        for _ in range(10):  # Max 10 levels
            if current_pid in visited or current_pid <= 1:
                break
            visited.add(current_pid)

            # Get parent and command
            try:
                result = subprocess.run(
                    ['ps', '-p', str(current_pid), '-o', 'ppid=,comm='],
                    capture_output=True,
                    text=True,
                    timeout=0.1
                )
                if result.returncode != 0:
                    break

                output = result.stdout.strip()
                if not output:
                    break

                parts = output.split(None, 1)
                if len(parts) < 2:
                    break

                ppid = int(parts[0])
                comm = parts[1]

                # Found Claude Code binary (stable PID)
                if 'claude' in comm.lower() and 'native-binary' in comm:
                    _CONTEXT_ID_CACHE = str(current_pid)
                    return _CONTEXT_ID_CACHE

                current_pid = ppid

            except (subprocess.TimeoutExpired, ValueError, IndexError):
                break

    except Exception:
        pass  # Fall back to PPID

    # Option 3: Fall back to PPID (may be unstable but better than nothing)
    ppid = os.getppid()
    _CONTEXT_ID_CACHE = str(ppid)
    return _CONTEXT_ID_CACHE


def get_sessions_dir() -> Path:
    """
    Get the sessions directory path (~/.maia/sessions/).

    Phase 230: Multi-user architecture - session files moved from /tmp/ to ~/.maia/sessions/
    for proper user isolation and persistence across reboots.

    Returns:
        Path to sessions directory (creates if not exists)
    """
    sessions_dir = Path.home() / ".maia" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_file_path() -> Path:
    """
    Get session state file path for current context.

    Phase 134.3: Context-specific session files prevent concurrency issues.
    Phase 230: Multi-user architecture - moved from /tmp/ to ~/.maia/sessions/

    Returns:
        Path to session file for this context
        Example: ~/.maia/sessions/swarm_session_12345.json
    """
    context_id = get_context_id()
    return get_sessions_dir() / f"swarm_session_{context_id}.json"


def migrate_legacy_session():
    """
    One-time migration: old /tmp/ session → new ~/.maia/sessions/ location.

    Phase 134.3: Backward compatibility for existing sessions.
    Phase 230: Multi-user architecture - migrate from /tmp/ to ~/.maia/sessions/

    Migration paths:
    - /tmp/maia_active_swarm_session.json → ~/.maia/sessions/swarm_session_{context_id}.json
    - /tmp/maia_active_swarm_session_*.json → ~/.maia/sessions/swarm_session_*.json
    """
    context_id = get_context_id()
    new_session = get_session_file_path()

    # Only migrate if new doesn't exist
    if new_session.exists():
        return

    # Try context-specific /tmp file first
    old_context_session = Path(f"/tmp/maia_active_swarm_session_{context_id}.json")
    if old_context_session.exists():
        try:
            import shutil
            shutil.copy2(old_context_session, new_session)
            old_context_session.unlink()
            return
        except OSError:
            pass

    # Try legacy global /tmp file
    old_global_session = Path("/tmp/maia_active_swarm_session.json")
    if old_global_session.exists():
        try:
            import shutil
            shutil.copy2(old_global_session, new_session)
            old_global_session.unlink()
        except OSError:
            pass  # Graceful degradation


def is_process_alive(pid: int) -> bool:
    """
    Check if a process is still running.

    Args:
        pid: Process ID to check

    Returns:
        True if process exists, False otherwise
    """
    try:
        # Send signal 0 (null signal) - doesn't kill process, just checks existence
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def cleanup_stale_sessions(max_age_hours: int = 24):
    """
    Remove session files older than max_age_hours.

    Phase 134.3: Prevent session pollution from abandoned contexts.
    Phase 134.5: Also remove legacy non-numeric context IDs (e.g., sre_001)
    Phase 134.5.1: Check if process still running before deleting (multi-session safety)
    Phase 230: Multi-user architecture - clean up from ~/.maia/sessions/ and legacy /tmp/
    Runs on every startup (fast: glob + stat).

    Safety: Will NOT delete session if:
    - Process (PID) is still running, OR
    - Session file modified within max_age_hours

    Args:
        max_age_hours: Maximum session age in hours (default: 24)
    """
    cutoff_time = time.time() - (max_age_hours * 3600)

    def cleanup_session_file(session_file: Path, prefix: str):
        """Clean up a single session file if stale."""
        try:
            filename = session_file.name
            if filename.startswith(prefix) and filename.endswith(".json"):
                context_id = filename[len(prefix):-len(".json")]

                # Check if legacy format (non-numeric)
                is_legacy = not context_id.isdigit()

                # Legacy sessions: Always remove (not PID-based, can't verify if active)
                if is_legacy:
                    session_file.unlink()
                    return

                # Numeric context ID (PID): Check if process still running
                pid = int(context_id)
                process_alive = is_process_alive(pid)

                # Only delete if BOTH conditions met:
                # 1. Process no longer running AND
                # 2. Session file older than max_age_hours
                if not process_alive and session_file.stat().st_mtime < cutoff_time:
                    session_file.unlink()
        except (OSError, ValueError):
            pass  # Graceful degradation (file may be locked or deleted)

    try:
        # Clean up new location (~/.maia/sessions/)
        sessions_dir = get_sessions_dir()
        for session_file in sessions_dir.glob("swarm_session_*.json"):
            cleanup_session_file(session_file, "swarm_session_")

        # Clean up legacy location (/tmp/) for backward compatibility
        for session_file in Path("/tmp").glob("maia_active_swarm_session_*.json"):
            cleanup_session_file(session_file, "maia_active_swarm_session_")
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

    Phase 228 Threshold Optimization:
    - Confidence >=60% (lowered from >70% for 90-agent specialist-first routing)
    - Complexity ≥3
    - Domain check REMOVED (redundant - low confidence handles general queries)

    UFC Philosophy: With 90 specialists, prefer routing to agents over fallback.
    """
    if not classification:
        return False

    confidence = classification.get("confidence", 0)
    complexity = classification.get("complexity", 0)

    # Phase 228: Lowered to 60%, removed domain check
    return (
        confidence >= 0.60 and  # Changed from >0.70 to >=0.60
        complexity >= 3
    )


# =============================================================================
# Phase 228: Capability Gap Detection
# =============================================================================

def should_log_capability_gap(classification: Dict[str, Any]) -> bool:
    """
    Determine if query should be logged as a capability gap.

    Phase 228: Queries with confidence < 40% indicate no suitable agent exists.
    These gaps are tracked for future agent creation recommendations.

    Args:
        classification: Classification result with confidence score

    Returns:
        True if confidence < 0.40 (capability gap)
    """
    if not classification:
        return False

    confidence = classification.get("confidence", 0)
    return confidence < CAPABILITY_GAP_THRESHOLD


def log_capability_gap(classification: Dict[str, Any], query: str) -> bool:
    """
    Log a capability gap for future analysis.

    Phase 228: Tracks queries that have no suitable agent match.
    Used to identify patterns that warrant new agent creation.

    Args:
        classification: Classification result
        query: Original user query

    Returns:
        True if logged successfully, False otherwise

    Performance: <10ms
    Graceful: Never raises, always returns bool
    """
    try:
        gap_entry = {
            "query": query[:200],  # Truncate long queries
            "domains": classification.get("domains", [classification.get("primary_domain", "general")]),
            "confidence": classification.get("confidence", 0),
            "complexity": classification.get("complexity", 0),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Load existing gaps
        gaps: List[Dict[str, Any]] = []
        if CAPABILITY_GAPS_FILE.exists():
            try:
                with open(CAPABILITY_GAPS_FILE, 'r') as f:
                    gaps = json.load(f)
            except (json.JSONDecodeError, IOError):
                gaps = []

        # Append new gap
        gaps.append(gap_entry)

        # Keep only last 100 gaps (prevent file bloat)
        gaps = gaps[-100:]

        # Atomic write
        tmp_file = CAPABILITY_GAPS_FILE.with_suffix(".tmp")
        with open(tmp_file, 'w') as f:
            json.dump(gaps, f, indent=2)
        tmp_file.replace(CAPABILITY_GAPS_FILE)

        return True

    except Exception:
        # Graceful degradation - gap logging failure is non-fatal
        return False


def check_for_agent_recommendation(domain: str) -> Optional[Dict[str, Any]]:
    """
    Check if a domain has enough gaps to recommend a new agent.

    Phase 228: If 3+ gaps occur in the same domain within 7 days,
    generate a recommendation for creating a new specialist agent.

    Args:
        domain: Domain to check for gap patterns

    Returns:
        Recommendation dict if threshold met, None otherwise
        {
            "domain": "cooking",
            "count": 5,
            "example_queries": ["query1", "query2", "query3"],
            "recommendation": "Consider creating cooking_specialist_agent",
            "timestamp": "2025-01-02T..."
        }
    """
    try:
        if not CAPABILITY_GAPS_FILE.exists():
            return None

        with open(CAPABILITY_GAPS_FILE, 'r') as f:
            gaps = json.load(f)

        # Filter gaps for this domain within the time window
        cutoff = datetime.utcnow() - timedelta(days=GAP_RECOMMENDATION_DAYS)
        domain_gaps = []

        for gap in gaps:
            # Check domain match
            gap_domains = gap.get("domains", [])
            if domain not in gap_domains and gap.get("primary_domain") != domain:
                continue

            # Check timestamp
            try:
                gap_time = datetime.fromisoformat(gap["timestamp"].replace("Z", "+00:00").replace("+00:00", ""))
                if gap_time < cutoff:
                    continue
            except (ValueError, KeyError):
                continue

            domain_gaps.append(gap)

        # Check if threshold met
        if len(domain_gaps) < GAP_RECOMMENDATION_COUNT:
            return None

        # Generate recommendation
        recommendation = {
            "domain": domain,
            "count": len(domain_gaps),
            "example_queries": [g["query"] for g in domain_gaps[:5]],
            "recommendation": f"Consider creating {domain}_specialist_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Save recommendation
        try:
            recommendations: List[Dict[str, Any]] = []
            if AGENT_RECOMMENDATIONS_FILE.exists():
                with open(AGENT_RECOMMENDATIONS_FILE, 'r') as f:
                    recommendations = json.load(f)

            # Check if already recommended
            existing = [r for r in recommendations if r.get("domain") == domain]
            if not existing:
                recommendations.append(recommendation)

                tmp_file = AGENT_RECOMMENDATIONS_FILE.with_suffix(".tmp")
                with open(tmp_file, 'w') as f:
                    json.dump(recommendations, f, indent=2)
                tmp_file.replace(AGENT_RECOMMENDATIONS_FILE)

        except Exception:
            pass  # Saving recommendation is non-critical

        return recommendation

    except Exception:
        return None


def get_agent_loading_message(
    classification: Dict[str, Any],
    agent: Optional[str]
) -> Optional[str]:
    """
    Generate agent mandate for Claude visibility.

    Phase 228.3: Basic message output
    Phase 229: Full mandate injection with actual agent instructions

    Args:
        classification: Classification result with confidence/complexity
        agent: Agent name to load (or None if no routing)

    Returns:
        Formatted mandate string if agent should load, None otherwise

    Performance: <50ms (file read + formatting)
    Token budget: 800-1500 tokens (~3000-6000 chars)
    """
    if not agent:
        return None

    if not classification:
        return None

    # Check if agent should load (reuse threshold logic)
    if not should_invoke_swarm(classification):
        return None

    # Phase 229: Use mandate injector for full agent instructions
    try:
        from agent_mandate_injector import generate_mandate, find_agent_file

        agent_file = find_agent_file(agent)
        if agent_file:
            mandate = generate_mandate(agent, agent_file)
            if mandate:
                return mandate
    except ImportError:
        pass  # Fallback to simple message

    # Fallback: simple message (Phase 228.3 behavior)
    confidence = classification.get("confidence", 0)
    domain = classification.get("primary_domain", "general")

    message = (
        f"🤖 AGENT LOADED: {agent}\n"
        f"Domain: {domain} | Confidence: {confidence:.0%}\n"
        f"Context: claude/agents/{agent}.md\n"
        f"Respond as this specialist agent."
    )

    return message


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
        "python_review": "python_code_reviewer_agent",
        "code_review": "python_code_reviewer_agent",
        "cooking": "asian_low_sodium_cooking_agent",
        "cocktail": "cocktail_mixologist_agent",
        "restaurant": "perth_restaurant_discovery_agent",
        "travel": "travel_monitor_alert_agent",
        "holiday": "holiday_research_agent",
        "personal": "personal_assistant_agent",
    }

    return domain_agent_map.get(domain)


# =============================================================================
# Phase 221: TDD Feature Tracker Integration
# =============================================================================

def load_tdd_context() -> Optional[Dict[str, Any]]:
    """
    Load active TDD project context from feature_tracker.

    Phase 221: Integrates with feature_tracker.py for TDD enforcement.
    Loads most recently modified features.json and returns status.

    Returns:
        Dict with TDD context or None if no active project:
        {
            "project": "my_project",
            "status": "0/4 passing (0.0%)",
            "next_feature": {"id": "F001", "name": "...", ...},
            "tdd_active": True
        }

    Performance: <10ms
    Graceful: Never raises, returns None on any error
    """
    try:
        # TDD projects stored in project_status/active/
        tdd_data_dir = MAIA_ROOT / "claude" / "data" / "project_status" / "active"

        if not tdd_data_dir.exists():
            return None

        # Find most recently modified features.json
        features_files = list(tdd_data_dir.glob("*_features.json"))

        if not features_files:
            return None

        # Sort by modification time, most recent first
        features_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Load most recent project
        most_recent = features_files[0]
        project_name = most_recent.stem.replace("_features", "")

        with open(most_recent, 'r') as f:
            data = json.load(f)

        # Validate schema
        if "features" not in data or "summary" not in data:
            return None

        summary = data["summary"]

        # Find next failing feature
        next_feature = None
        for f in data["features"]:
            if not f.get("passes", False) and not f.get("blocked", False):
                next_feature = f
                break

        return {
            "project": project_name,
            "tdd_active": True,
            "total": summary.get("total", 0),
            "passing": summary.get("passing", 0),
            "failing": summary.get("failing", 0),
            "blocked": summary.get("blocked", 0),
            "completion_percentage": summary.get("completion_percentage", 0.0),
            "next_feature": next_feature,
            "status": f"{summary.get('passing', 0)}/{summary.get('total', 0)} passing ({summary.get('completion_percentage', 0.0)}%)"
        }

    except Exception:
        # Graceful degradation - TDD context loading is non-critical
        return None


def load_ltm_context() -> Optional[Dict[str, Any]]:
    """
    Load user preferences from Long-Term Memory system.

    Agentic AI Phase 2 Integration: Adds cross-session memory to agent context.
    Loads high-confidence user preferences and recent corrections.

    Returns:
        Dict with LTM context or None if unavailable:
        {
            "preferences": [{"key": "...", "value": "...", ...}, ...],
            "recent_corrections": [...],
            "ltm_active": True
        }

    Performance: <50ms (SQLite query)
    Graceful: Never raises, returns None on any error
    """
    try:
        # Import LTM system
        ltm_path = MAIA_ROOT / "claude" / "tools" / "orchestration"
        if str(ltm_path) not in sys.path:
            sys.path.insert(0, str(ltm_path))

        from long_term_memory import LongTermMemory

        # Initialize LTM with default database
        ltm = LongTermMemory()

        # Load session context (preferences + corrections)
        context = ltm.load_session_context()

        if not context:
            return None

        preferences = context.get("preferences", [])
        corrections = context.get("recent_corrections", [])

        # Only return if we have meaningful data
        if not preferences and not corrections:
            return None

        return {
            "ltm_active": True,
            "preferences": preferences[:10],  # Limit for token budget
            "recent_corrections": corrections[:5],  # Limit for token budget
            "preference_count": len(context.get("preferences", [])),
            "loaded_at": datetime.utcnow().isoformat()
        }

    except ImportError:
        # LTM system not available
        return None
    except Exception:
        # Graceful degradation - LTM loading is non-critical
        return None


def is_development_task(query: str) -> bool:
    """
    Detect if a query is a development task that should use TDD.

    Phase 221: Helps enforce TDD by identifying development work.

    Args:
        query: User's input query

    Returns:
        True if query appears to be development work

    Examples:
        "create a tool for X" → True
        "build a new feature" → True
        "what time is it" → False
        "explain this code" → False
    """
    dev_indicators = [
        "create", "build", "implement", "add", "write", "develop",
        "tool", "agent", "feature", "script", "function", "class",
        "fix bug", "refactor", "enhance", "modify", "update code"
    ]

    query_lower = query.lower()

    # Count development indicators
    dev_score = sum(1 for indicator in dev_indicators if indicator in query_lower)

    # Non-development patterns (questions, exploration)
    non_dev_patterns = [
        "what", "how does", "explain", "search", "find", "list",
        "show me", "where is", "when", "why", "can you"
    ]

    non_dev_score = sum(1 for pattern in non_dev_patterns if query_lower.startswith(pattern))

    # Requires at least 2 dev indicators and no non-dev pattern start
    return dev_score >= 2 and non_dev_score == 0


def check_tdd_enforcement(query: str) -> Optional[str]:
    """
    Check if TDD enforcement should warn about missing features.json.

    Phase 221: Returns warning message if development task detected
    but no active TDD project exists.

    Args:
        query: User's input query

    Returns:
        Warning message if TDD not initialized, None otherwise
    """
    if not is_development_task(query):
        return None

    tdd_context = load_tdd_context()

    if tdd_context and tdd_context.get("tdd_active"):
        # TDD project active - no warning needed
        return None

    # Development task but no TDD project
    return (
        "⚠️ TDD ENFORCEMENT: Development task detected but no features.json found.\n"
        "Consider initializing TDD tracking:\n"
        "  python3 claude/tools/sre/feature_tracker.py init <project_name>\n"
        "  python3 claude/tools/sre/feature_tracker.py add <project> \"Feature X\""
    )


def format_tdd_context_for_session(tdd_context: Dict[str, Any]) -> str:
    """
    Format TDD context for session state injection.

    Returns human-readable TDD status for agent context.
    """
    if not tdd_context:
        return ""

    lines = [
        f"TDD PROJECT: {tdd_context['project']}",
        f"Status: {tdd_context['status']}"
    ]

    if tdd_context.get("blocked", 0) > 0:
        lines.append(f"Blocked: {tdd_context['blocked']} features")

    if tdd_context.get("next_feature"):
        nf = tdd_context["next_feature"]
        lines.append(f"Next: {nf.get('name', 'Unknown')} [{nf.get('id', '?')}]")

        if nf.get("verification"):
            lines.append("Verification:")
            for step in nf["verification"][:3]:  # Max 3 steps
                lines.append(f"  - {step}")

    return "\n".join(lines)


def _start_learning_session(context_id: str, query: str, agent: str, domain: str) -> Optional[str]:
    """
    Start a PAI v2 learning session for tool output capture.

    Phase 232: Integrates with Personal PAI v2 Learning System.
    Called when a new session state is created.

    Args:
        context_id: Claude Code window context ID
        query: Initial user query
        agent: Agent being loaded
        domain: Agent's domain

    Returns:
        Session ID if started, None otherwise

    Performance: <10ms
    Graceful: Never raises, returns None on any error
    """
    try:
        from claude.tools.learning.session import get_session_manager

        manager = get_session_manager()

        # Only start if no active session (prevent duplicates)
        if manager.active_session_id:
            return manager.active_session_id

        session_id = manager.start_session(
            context_id=context_id,
            initial_query=query[:500],  # Truncate for storage
            agent_used=agent,
            domain=domain
        )

        return session_id

    except ImportError:
        # PAI v2 learning system not installed
        return None
    except Exception:
        # Graceful degradation - learning session start is non-critical
        return None


def create_session_state(
    agent: str,
    domain: str,
    classification: Dict[str, Any],
    query: str
) -> bool:
    """
    Create session state file for Maia agent context loading (Phase 5 - with handoff support).

    File: ~/.maia/sessions/swarm_session_{context_id}.json (Phase 230: multi-user)
    Phase 232: Also starts PAI v2 learning session for tool output capture.

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

        # Phase 221: Load TDD context if active project exists
        tdd_context = load_tdd_context()

        # Agentic AI Phase 2: Load LTM (Long-Term Memory) context
        ltm_context = load_ltm_context()

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
            "version": "1.3",  # Agentic AI: LTM integration
            # Phase 221: TDD Feature Tracker Integration
            "tdd_context": tdd_context,
            "tdd_status": format_tdd_context_for_session(tdd_context) if tdd_context else None,
            # Agentic AI Phase 2: Long-Term Memory Integration
            "ltm_context": ltm_context,
            "user_preferences": ltm_context.get("preferences", []) if ltm_context else []
        }

        # Phase 232: Start PAI v2 learning session BEFORE writing (to capture session_id)
        context_id = get_context_id()
        learning_session_id = _start_learning_session(context_id, query, agent, domain)

        # Phase 233.3: Store learning session ID for close_session to use
        if learning_session_id:
            session_data["learning_session_id"] = learning_session_id

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


def _capture_session_memory(session_data: dict) -> bool:
    """
    Capture session memory before closing (Phase 220).

    Logs session to ConversationLogger for cross-session learning.
    Graceful degradation - never blocks session close.

    Args:
        session_data: Session dict with agent, context, etc.

    Returns:
        True if captured, False otherwise (non-blocking)
    """
    try:
        # Import conversation logger
        from claude.tools.conversation_logger import ConversationLogger

        agent = session_data.get("current_agent", "unknown")
        context = session_data.get("context", "")
        started_at = session_data.get("session_start", session_data.get("started_at", ""))

        # Skip if no meaningful context
        if not context or context == "unknown":
            return False

        logger_instance = ConversationLogger()

        # Create journey from session
        journey_id = logger_instance.start_journey(
            problem_description=f"Session with {agent}",
            initial_question=context[:500] if context else "Agent session"
        )

        if journey_id:
            # Add agent used
            logger_instance.add_agent(
                journey_id=journey_id,
                agent_name=agent,
                rationale=f"User-loaded agent session"
            )

            # Complete journey with context as meta-learning
            logger_instance.complete_journey(
                journey_id=journey_id,
                business_impact="Session completed",
                meta_learning=context[:1000] if context else "Session context not captured",
                iteration_count=1,
                embed=True  # Generate embedding for semantic search
            )

            print(f"   📝 Session memory captured")
            return True

        return False

    except ImportError:
        # ConversationLogger not available - graceful degradation
        return False
    except Exception as e:
        # Non-blocking: log but don't fail session close
        print(f"   ⚠️  Memory capture skipped: {str(e)[:50]}")
        return False


# =============================================================================
# Phase 2 Refactoring: close_session() Helper Functions
# TDD: See claude/hooks/tests/test_close_session_helpers.py
# =============================================================================

def _check_git_status() -> tuple:
    """
    Check for uncommitted git changes.

    Returns:
        tuple: (has_issues: bool, files: List[str])
    """
    try:
        result = subprocess.run(
            ['git', '-C', str(MAIA_ROOT), 'status', '--short'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split('\n')
            return (True, files)
        return (False, [])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return (False, [])


def _check_docs_currency() -> tuple:
    """
    Check if documentation (SYSTEM_STATE.md) is older than recent code changes.

    Returns:
        tuple: (has_issues: bool, message: str)
    """
    try:
        system_state = MAIA_ROOT / "SYSTEM_STATE.md"
        if not system_state.exists():
            return (False, "")

        system_state_mtime = system_state.stat().st_mtime

        # Check for recent python/md file changes in last hour
        result = subprocess.run(
            ['find', str(MAIA_ROOT / 'claude'), '-name', '*.py', '-o', '-name', '*.md',
             '-mtime', '-1h'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.stdout.strip():
            recent_files = result.stdout.strip().split('\n')
            recent_file_mtimes = []
            for f in recent_files[:5]:
                try:
                    recent_file_mtimes.append(Path(f).stat().st_mtime)
                except (FileNotFoundError, OSError, PermissionError):
                    pass

            if recent_file_mtimes and max(recent_file_mtimes) > system_state_mtime:
                msg = f"Last update: {datetime.fromtimestamp(system_state_mtime).strftime('%Y-%m-%d %H:%M')}"
                return (True, msg)

        return (False, "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return (False, "")


def _check_background_processes() -> tuple:
    """
    Check for running background processes (Claude Code background tasks).

    Returns:
        tuple: (has_issues: bool, count: int)
    """
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'claude.*bash.*run_in_background'],
            capture_output=True,
            text=True,
            timeout=1
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return (True, len(pids))
        return (False, 0)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return (False, 0)


def _check_checkpoint_currency(has_git_issues: bool) -> tuple:
    """
    Check if checkpoint is stale (>2 hours old with uncommitted changes).

    Args:
        has_git_issues: Whether there are uncommitted git changes

    Returns:
        tuple: (has_issues: bool, age_hours: float)
    """
    try:
        checkpoints_dir = MAIA_ROOT / "claude" / "data" / "checkpoints"
        if not checkpoints_dir.exists():
            return (False, 0.0)

        checkpoints = sorted(
            checkpoints_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if checkpoints:
            latest_checkpoint = checkpoints[0]
            checkpoint_age_hours = (time.time() - latest_checkpoint.stat().st_mtime) / 3600

            # Warn if checkpoint is >2 hours old and we have git changes
            if checkpoint_age_hours > 2 and has_git_issues:
                return (True, checkpoint_age_hours)
            return (False, checkpoint_age_hours)

        return (False, 0.0)
    except (OSError, ValueError):
        return (False, 0.0)


def _check_development_cleanup() -> dict:
    """
    Check for development files that need cleanup.

    Returns:
        dict: {
            'versioned_files': List[str],
            'misplaced_tests': List[str],
            'build_artifacts': List[str]
        }
    """
    result = {
        'versioned_files': [],
        'misplaced_tests': [],
        'build_artifacts': []
    }

    try:
        tools_dir = MAIA_ROOT / 'claude' / 'tools'

        # Find versioned files (*_v2.py, *_v3.py, etc.)
        if tools_dir.exists():
            for py_file in tools_dir.rglob('*_v[0-9]*.py'):
                result['versioned_files'].append(str(py_file.relative_to(MAIA_ROOT)))

            # Find misplaced test files (test_*.py not in tests/ directories)
            for py_file in tools_dir.rglob('test_*.py'):
                if 'tests' not in py_file.parts:
                    result['misplaced_tests'].append(str(py_file.relative_to(MAIA_ROOT)))

        # Find build artifacts
        for artifact in MAIA_ROOT.rglob('.DS_Store'):
            result['build_artifacts'].append(str(artifact.relative_to(MAIA_ROOT)))

        claude_dir = MAIA_ROOT / 'claude'
        if claude_dir.exists():
            for pycache in claude_dir.rglob('__pycache__'):
                if pycache.is_dir():
                    result['build_artifacts'].append(str(pycache.relative_to(MAIA_ROOT)))

    except Exception:
        pass  # Graceful degradation

    return result


def _cleanup_session(session_file: Path) -> bool:
    """
    Capture session memory and delete session file.

    Args:
        session_file: Path to the session file

    Returns:
        bool: True if cleanup succeeded, False otherwise
    """
    if not session_file.exists():
        return False

    try:
        # Read session info
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        # Capture session memory before deletion
        _capture_session_memory(session_data)

        # Delete session file
        session_file.unlink()
        return True

    except (json.JSONDecodeError, IOError, OSError):
        # File corrupt - try to delete anyway
        try:
            session_file.unlink()
            return True
        except OSError:
            return False


def close_session():
    """
    Pre-shutdown workflow: Comprehensive checks before closing Claude Code window.

    Phase 134.7: User-controlled session lifecycle management.
    Phase 213: Enhanced pre-shutdown checklist (git, docs, processes, checkpoints, session)
    Phase 214: Development file cleanup detection (versioned files, misplaced tests, artifacts)
    Phase 230: Refactored to use helper functions for maintainability.
    Phase PAI-v2: Learning system integration (VERIFY + LEARN + Maia Memory)

    Usage:
        python3 swarm_auto_loader.py close_session

    Checks:
    1. Git status (uncommitted changes?) → offer to run save_state
    2. Documentation currency (recent changes without docs updates?)
    3. Active background processes (running shells/tasks?)
    4. Checkpoint currency (work since last checkpoint?)
    5. Development file cleanup (versioned files, test files, build artifacts)
    6. PAI v2 Learning (VERIFY success, LEARN patterns, save to Maia Memory)
    7. Session file cleanup

    Returns:
        Prints status message and exits with code 0
    """
    print("🔍 Pre-shutdown check...\n")

    issues_found = []
    response = ""  # Initialize for later reference

    # Check 1: Git Status
    has_git_issues, git_files = _check_git_status()
    if has_git_issues:
        issues_found.append("git")
        print("⚠️  Uncommitted changes detected:")
        for file in git_files[:10]:
            print(f"   {file}")
        if len(git_files) > 10:
            print(f"   ... and {len(git_files) - 10} more")
        print()

    # Check 2: Documentation Currency
    has_docs_issues, docs_message = _check_docs_currency()
    if has_docs_issues:
        issues_found.append("docs")
        print("⚠️  Recent code changes detected without SYSTEM_STATE.md update")
        print(f"   {docs_message}")
        print()

    # Check 3: Active Background Processes
    has_process_issues, process_count = _check_background_processes()
    if has_process_issues:
        issues_found.append("processes")
        print(f"⚠️  {process_count} background process(es) still running")
        print("   These may be interrupted when window closes")
        print()

    # Check 4: Checkpoint Currency
    has_checkpoint_issues, checkpoint_age = _check_checkpoint_currency(has_git_issues)
    if has_checkpoint_issues:
        issues_found.append("checkpoint")
        print(f"⚠️  Last checkpoint is {checkpoint_age:.1f} hours old")
        print("   Consider creating checkpoint before closing")
        print()

    # Check 5: Development File Cleanup
    cleanup_result = _check_development_cleanup()
    versioned_files = cleanup_result.get("versioned_files", [])
    misplaced_tests = cleanup_result.get("misplaced_tests", [])
    build_artifacts = cleanup_result.get("build_artifacts", [])

    if versioned_files or misplaced_tests or build_artifacts:
        issues_found.append("cleanup")
        print("⚠️  Development file cleanup needed:")

        if versioned_files:
            print(f"   📦 {len(versioned_files)} versioned files (e.g., _v2.py, _v3.py)")
            for vf in versioned_files[:3]:
                print(f"      - {vf}")
            if len(versioned_files) > 3:
                print(f"      ... and {len(versioned_files) - 3} more")

        if misplaced_tests:
            print(f"   🧪 {len(misplaced_tests)} test files in production directories")
            for mt in misplaced_tests[:3]:
                print(f"      - {mt}")
            if len(misplaced_tests) > 3:
                print(f"      ... and {len(misplaced_tests) - 3} more")

        if build_artifacts:
            print(f"   🗑️  {len(build_artifacts)} build artifacts (.DS_Store, __pycache__)")
            for ba in build_artifacts[:3]:
                print(f"      - {ba}")
            if len(build_artifacts) > 3:
                print(f"      ... and {len(build_artifacts) - 3} more")

        print(f"   💡 Tip: These accumulate during development and should be cleaned periodically")
        print()

    # Offer to run save_state if issues found
    if issues_found:
        print("=" * 60)

        # Check for command-line flags or non-interactive mode
        auto_save = "--auto-save" in sys.argv or "-y" in sys.argv
        skip_save = "--skip-save" in sys.argv or "-n" in sys.argv
        is_interactive = sys.stdin.isatty()

        if skip_save:
            response = "n"
        elif auto_save or not is_interactive:
            # Non-interactive mode (called from Claude Code) - recommend save_state
            print("\n📝 Uncommitted changes detected!")
            print("   Run 'save state' in Claude to commit changes before closing.")
            print("   Or use: python3 swarm_auto_loader.py close_session --skip-save")
            response = "n"  # Don't block, just inform
        else:
            response = input("\n📝 Run /save_state to commit changes and update docs? (y/n): ")

        if response.lower() in ['y', 'yes']:
            print("\n🔄 Running save_state workflow...\n")
            try:
                save_state_script = MAIA_ROOT / "claude" / "tools" / "sre" / "save_state.py"
                if save_state_script.exists():
                    result = subprocess.run(
                        ["python3", str(save_state_script)],
                        cwd=MAIA_ROOT,
                        capture_output=False  # Show output in real-time
                    )
                    if result.returncode != 0:
                        print("\n⚠️  save_state blocked - fix issues above, then run /close-session again")
                        sys.exit(1)
                    print()  # Add spacing after save_state output
                else:
                    print("⚠️  save_state.py not found - please run 'save state' manually")
                    sys.exit(0)
            except Exception as e:
                print(f"⚠️  Could not run save_state: {e}")
                print("   Please run 'python3 claude/tools/sre/save_state.py' manually")
                sys.exit(0)
        else:
            print("\n⏭️  Skipping save_state (you can run it manually later)")
            print()
    else:
        print("✅ All checks passed - clean state\n")

    # Check 6: PAI v2 Learning System - VERIFY + LEARN
    # Phase 233.3: Read learning_session_id from swarm_session file
    try:
        from claude.tools.learning.session import get_session_manager
        manager = get_session_manager()

        # Try to load session from file if not in memory
        learning_session_id = None
        session_file = get_session_file_path()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    learning_session_id = session_data.get('learning_session_id')
                    # Load session data for VERIFY/LEARN
                    if learning_session_id and not manager.active_session_id:
                        manager.load_session(
                            session_id=learning_session_id,
                            session_data={
                                'session_id': learning_session_id,
                                'context_id': str(get_context_id()),
                                'initial_query': session_data.get('query', ''),
                                'agent_used': session_data.get('current_agent'),
                                'domain': session_data.get('domain'),
                                'started_at': session_data.get('session_start')
                            }
                        )
            except (json.JSONDecodeError, IOError):
                pass

        if manager.active_session_id:
            print("📊 Running learning analysis...")
            learning_result = manager.end_session()

            # Display VERIFY results
            verify = learning_result.get('verify', {})
            if verify.get('success'):
                print(f"   ✅ Session successful (confidence: {verify.get('confidence', 0):.0%})")
            else:
                print(f"   ⚠️  Session had issues (confidence: {verify.get('confidence', 0):.0%})")

            # Display LEARN results
            insights = learning_result.get('learn', [])
            if insights:
                print(f"   📚 Extracted {len(insights)} pattern(s)")

            print(f"   💾 Summary saved to Maia Memory")
            print()
        elif learning_session_id:
            print(f"ℹ️  Learning session {learning_session_id[:12]}... found but could not load")
    except ImportError:
        pass  # PAI v2 learning system not installed
    except Exception as e:
        print(f"   ⚠️  Learning analysis skipped: {e}")

    # Check 7: Session File Cleanup
    session_file = get_session_file_path()

    if session_file.exists():
        if _cleanup_session(session_file):
            # Read session info for confirmation (already captured in helper)
            print(f"✅ Agent session closed")
        else:
            print(f"⚠️  Could not delete session file")
            sys.exit(1)
    else:
        print(f"ℹ️  No active agent session")

    # Final Confirmation
    print("\n" + "=" * 60)
    print("✅ Pre-shutdown complete")
    print("   Safe to close Claude Code window")
    if issues_found and response.lower() not in ['y', 'yes']:
        print("\n⚠️  Reminder: Uncommitted changes will be preserved in git")
        print("   but session context will be lost")
    print("=" * 60)

    sys.exit(0)


# =============================================================================
# Phase 176: Default Agent Loading + Recovery Protocol
# Phase 207: User-Specific Default Agent Preferences
# =============================================================================

def load_user_preferences() -> Dict[str, Any]:
    """
    Load user-specific preferences for Maia system behavior.

    Phase 207: Allows users to customize default agent based on their
    primary work domain (e.g., SRE, security, development).

    Returns:
        User preferences dict with default_agent and fallback_agent.
        Falls back to system defaults if preferences unavailable.

    Performance: <5ms
    Graceful: Never raises, always returns valid dict
    """
    default_prefs = {
        "default_agent": "sre_principal_engineer_agent",
        "fallback_agent": "sre_principal_engineer_agent"
    }

    try:
        prefs_file = MAIA_ROOT / "claude" / "data" / "user_preferences.json"
        if not prefs_file.exists():
            return default_prefs

        with open(prefs_file, 'r') as f:
            user_prefs = json.load(f)

        # Validate required fields
        if "default_agent" not in user_prefs:
            log_error("user_preferences.json missing 'default_agent' field")
            return default_prefs

        return {
            "default_agent": user_prefs.get("default_agent", "sre_principal_engineer_agent"),
            "fallback_agent": user_prefs.get("fallback_agent", "sre_principal_engineer_agent")
        }

    except (json.JSONDecodeError, IOError) as e:
        log_error(f"Failed to load user preferences: {e}")
        return default_prefs


def load_default_agent() -> Optional[str]:
    """
    Load user-preferred default agent when no session exists.

    Phase 176: Default agent provides reliability-focused foundation
    Phase 207: User preferences allow customization (e.g., SRE as default)

    Returns:
        Agent name if loaded, None if session already exists

    Performance: <50ms
    Graceful fallback: user_prefs → fallback_agent → sre_principal_engineer_agent
    """
    session_file = get_session_file_path()

    # If session already exists, don't override
    if session_file.exists():
        try:
            with open(session_file, 'r') as f:
                json.load(f)  # Validate it's valid JSON
            return None  # Session exists, don't load default
        except (json.JSONDecodeError, IOError):
            pass  # Corrupted session, proceed to load default

    # Phase 207: Load user preferences
    user_prefs = load_user_preferences()
    default_agent = user_prefs["default_agent"]
    fallback_agent = user_prefs["fallback_agent"]

    # Try user's preferred default agent
    agent_file = MAIA_ROOT / "claude" / "agents" / f"{default_agent}.md"
    if not agent_file.exists():
        # Try with _agent suffix
        agent_file = MAIA_ROOT / "claude" / "agents" / f"{default_agent}_agent.md"

    if not agent_file.exists():
        log_error(f"Preferred default agent not found: {default_agent}, falling back to {fallback_agent}")
        default_agent = fallback_agent
        agent_file = MAIA_ROOT / "claude" / "agents" / f"{fallback_agent}.md"

        # Last resort: hardcoded sre_principal_engineer_agent
        if not agent_file.exists():
            agent_file = MAIA_ROOT / "claude" / "agents" / "sre_principal_engineer_agent.md"
            default_agent = "sre_principal_engineer_agent"

        if not agent_file.exists():
            log_error(f"No default agent available (tried {user_prefs['default_agent']}, {fallback_agent}, sre_principal_engineer_agent)")
            return None

    # Determine domain from agent name
    domain_map = {
        "sre_principal_engineer_agent": "sre",
        "security_specialist_agent": "security",
        "devops_principal_architect_agent": "devops",
    }
    domain = domain_map.get(default_agent, "core")

    # Create session state for default agent
    default_classification = {
        "confidence": 1.0,
        "complexity": 1,
        "primary_domain": domain,
    }

    success = create_session_state(
        agent=default_agent,
        domain=domain,
        classification=default_classification,
        query="[Default agent loaded - no prior session]"
    )

    if success:
        return default_agent
    return None


def get_recovery_context() -> Dict[str, Any]:
    """
    Get recovery context from checkpoint manager.

    Phase 176: Integrates with checkpoint_manager.py for session recovery.
    Combines checkpoint data with git history per FR-2.2.

    Returns:
        Recovery context dictionary with checkpoint and git info

    Performance: <5s (includes git operations)
    Graceful: Never raises, always returns valid dict
    """
    context: Dict[str, Any] = {
        'checkpoint': None,
        'git_commits': [],
        'message': None,
    }

    try:
        # Try to import checkpoint_manager
        sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools"))
        from checkpoint_manager import CheckpointManager

        # Get default checkpoints directory
        checkpoints_dir = MAIA_ROOT / "claude" / "data" / "checkpoints"

        if checkpoints_dir.exists():
            manager = CheckpointManager(checkpoints_dir=checkpoints_dir)
            checkpoint_context = manager.get_recovery_context(include_git=True)

            context['checkpoint'] = checkpoint_context.get('checkpoint')
            context['git_commits'] = checkpoint_context.get('git_commits', [])
            context['message'] = checkpoint_context.get('message')
        else:
            context['message'] = "No checkpoints directory found"

    except ImportError:
        context['message'] = "Checkpoint manager not available"
    except Exception as e:
        context['message'] = f"Error loading recovery context: {e}"

    return context


def should_show_recovery() -> bool:
    """
    Determine if recovery prompt should be shown to user.

    Phase 176: Returns True if checkpoint exists from prior work.

    Returns:
        True if recovery context available, False otherwise
    """
    try:
        sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools"))
        from checkpoint_manager import CheckpointManager

        checkpoints_dir = MAIA_ROOT / "claude" / "data" / "checkpoints"

        if not checkpoints_dir.exists():
            return False

        manager = CheckpointManager(checkpoints_dir=checkpoints_dir)
        checkpoint = manager.load_latest_checkpoint()

        return checkpoint is not None

    except Exception:
        return False


def format_recovery_display() -> str:
    """
    Format recovery context for display to user.

    Returns:
        Formatted string for terminal display
    """
    try:
        sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools"))
        from checkpoint_manager import CheckpointManager

        checkpoints_dir = MAIA_ROOT / "claude" / "data" / "checkpoints"

        if checkpoints_dir.exists():
            manager = CheckpointManager(checkpoints_dir=checkpoints_dir)
            return manager.format_recovery_for_display()

    except Exception as e:
        return f"Error formatting recovery: {e}"

    return "No recovery context available"


def process_query(query: str) -> Optional[str]:
    """
    Process a user query and return agent loading message if routing matches.

    Phase 228.3: Unified query processing that outputs agent loading message
    for Claude visibility. Used by both main() and tests.

    Args:
        query: User's input query

    Returns:
        Agent loading message if routing matches, None otherwise.
        Also prints message to stdout for hook integration.

    Performance: <500ms (includes classification)
    Graceful: Never raises, always returns valid result
    """
    try:
        # Step 1: Classify query
        classification = classify_query(query)
        if not classification:
            return None

        # Step 2: Check if swarm invocation needed
        if not should_invoke_swarm(classification):
            return None

        # Step 3: Get agent from coordinator suggestion
        agent = classification.get("suggested_agent")
        if not agent:
            return None

        # Step 4: Verify agent file exists
        agent_file = MAIA_ROOT / f"claude/agents/{agent}_agent.md"
        if not agent_file.exists():
            agent_file = MAIA_ROOT / f"claude/agents/{agent}.md"
        if not agent_file.exists():
            return None

        # Step 5: Generate and output agent loading message
        message = get_agent_loading_message(classification, agent)
        if message:
            print(message)

        # Step 6: Create session state (background work)
        invoke_swarm_orchestrator(agent, query, classification)

        return message

    except Exception:
        return None


def main():
    """
    Main entry point for swarm auto-loader.

    Usage:
        python3 swarm_auto_loader.py "user query"
        python3 swarm_auto_loader.py close_session
        python3 swarm_auto_loader.py get_context_id

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

    # Phase 134.7: Handle close_session command
    if sys.argv[1] == "close_session":
        close_session()
        # close_session() calls sys.exit(), never returns

    # Phase 222: Handle get_context_id command (was documented but not implemented)
    if sys.argv[1] == "get_context_id":
        context_id = get_context_id()
        print(context_id)
        sys.exit(0)

    query = sys.argv[1]

    try:
        # Phase 228.3: Use process_query for unified agent loading with message output
        process_query(query)

        # Log performance
        duration_ms = (time.time() - start_time) * 1000
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
