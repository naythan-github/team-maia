#!/usr/bin/env python3
"""
HITL Gate - Adaptive Human-in-the-Loop Safety Gate

Agentic AI Phase 3 Integration: Confidence-based pause points for high-risk actions.

Uses AdaptiveHITL to determine when human confirmation is needed before
executing potentially destructive or risky operations.

Usage:
    from hitl_gate import check_action, should_pause_for_action, record_user_decision

    # Check if action needs confirmation
    needs_pause, reason = should_pause_for_action('database_drop', {'target': 'prod_db'})
    if needs_pause:
        print(f"⚠️ Confirmation required: {reason}")

    # After user decision, record for learning
    record_user_decision('database_drop', approved=True)

Author: Maia System
Created: 2026-01-03 (Agentic AI Phase 3 Integration)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Add orchestration tools to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT / "claude" / "tools" / "orchestration"))

# Try to import AdaptiveHITL
try:
    from adaptive_hitl import AdaptiveHITL
    HITL_AVAILABLE = True
except ImportError:
    HITL_AVAILABLE = False

# Singleton instance for session
_hitl_instance = None


def get_hitl_instance() -> Optional['AdaptiveHITL']:
    """
    Get or create singleton AdaptiveHITL instance.

    Returns:
        AdaptiveHITL instance or None if unavailable
    """
    global _hitl_instance

    if not HITL_AVAILABLE:
        return None

    if _hitl_instance is None:
        try:
            _hitl_instance = AdaptiveHITL()
        except Exception:
            return None

    return _hitl_instance


def should_pause_for_action(
    action_type: str,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """
    Check if an action requires human confirmation.

    Uses confidence-based thresholds that learn from user decisions.

    Args:
        action_type: Type of action (e.g., 'file_delete', 'database_drop', 'git_push_force')
        context: Optional context dict with:
            - target: Target of action (file path, db name, etc.)
            - environment: 'production' or 'development'
            - targets: List of targets for bulk operations

    Returns:
        Tuple of (should_pause, reason)

    Examples:
        >>> should_pause_for_action('file_read')
        (False, 'Safe action')

        >>> should_pause_for_action('database_drop', {'target': 'production_db'})
        (True, "Critical action 'database_drop' always requires confirmation")

        >>> should_pause_for_action('file_delete', {'targets': ['a', 'b', 'c', 'd', 'e']})
        (True, 'Bulk operation affecting 5 items requires confirmation')
    """
    hitl = get_hitl_instance()

    if hitl is None:
        # HITL unavailable - default to not pausing for most actions
        # but still pause for known critical actions
        critical_actions = ['database_drop', 'git_push_force', 'rm_rf', 'format_disk']
        if action_type in critical_actions:
            return True, f"Critical action '{action_type}' requires confirmation (HITL unavailable)"
        return False, "HITL unavailable - allowing action"

    action = {'type': action_type}
    if context:
        action.update(context)

    return hitl.should_pause(action, context)


def check_action(
    action_type: str,
    target: Optional[str] = None,
    environment: Optional[str] = None,
    is_bulk: bool = False,
    bulk_count: int = 0
) -> Dict[str, Any]:
    """
    Comprehensive action check with structured response.

    Args:
        action_type: Type of action
        target: Target of action (optional)
        environment: Environment ('production', 'development')
        is_bulk: Whether this is a bulk operation
        bulk_count: Number of items affected

    Returns:
        Dict with:
            - requires_confirmation: bool
            - reason: str
            - confidence: float (0.0-1.0)
            - action_category: str ('safe', 'moderate', 'destructive', 'critical')
    """
    context = {}
    if target:
        context['target'] = target
    if environment:
        context['environment'] = environment
    if is_bulk:
        context['targets'] = ['item'] * bulk_count

    should_pause, reason = should_pause_for_action(action_type, context)

    hitl = get_hitl_instance()
    confidence = 0.5  # Default
    category = 'moderate'  # Default

    if hitl:
        try:
            confidence = hitl.calculate_confidence({'type': action_type}, context)
            category = hitl.classify_action({'type': action_type})
        except Exception:
            pass

    return {
        'requires_confirmation': should_pause,
        'reason': reason,
        'confidence': confidence,
        'action_category': category,
        'action_type': action_type
    }


def record_user_decision(
    action_type: str,
    approved: bool,
    feedback: Optional[str] = None
) -> bool:
    """
    Record user's decision for learning.

    The HITL system learns from approvals/rejections to adjust
    future confidence thresholds.

    Args:
        action_type: Type of action that was checked
        approved: Whether user approved the action
        feedback: Optional user feedback

    Returns:
        True if decision was recorded, False otherwise
    """
    hitl = get_hitl_instance()

    if hitl is None:
        return False

    try:
        action = {'type': action_type}
        hitl.record_decision(action, approved, feedback)
        return True
    except Exception:
        return False


def get_learned_confidence(action_type: str) -> Optional[float]:
    """
    Get the learned confidence for an action type.

    Args:
        action_type: Type of action

    Returns:
        Learned confidence (0.0-1.0) or None if not available
    """
    hitl = get_hitl_instance()

    if hitl is None:
        return None

    try:
        return hitl.get_learned_confidence(action_type)
    except Exception:
        return None


def format_confirmation_prompt(
    action_type: str,
    reason: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format a user-friendly confirmation prompt.

    Args:
        action_type: Type of action
        reason: Reason confirmation is needed
        context: Action context

    Returns:
        Formatted prompt string
    """
    lines = [
        "⚠️  CONFIRMATION REQUIRED",
        f"Action: {action_type}",
        f"Reason: {reason}"
    ]

    if context:
        if 'target' in context:
            lines.append(f"Target: {context['target']}")
        if 'environment' in context:
            lines.append(f"Environment: {context['environment']}")
        if 'targets' in context and isinstance(context['targets'], list):
            lines.append(f"Items affected: {len(context['targets'])}")

    lines.append("\nProceed? [y/N]")

    return '\n'.join(lines)


# CLI interface for testing
def main():
    import argparse

    parser = argparse.ArgumentParser(description="HITL Gate - Action Safety Check")
    parser.add_argument('action', help='Action type to check')
    parser.add_argument('--target', '-t', help='Target of action')
    parser.add_argument('--env', '-e', choices=['production', 'development'], help='Environment')
    parser.add_argument('--bulk', '-b', type=int, help='Number of items for bulk operation')

    args = parser.parse_args()

    context = {}
    if args.target:
        context['target'] = args.target
    if args.env:
        context['environment'] = args.env
    if args.bulk:
        context['targets'] = ['item'] * args.bulk

    should_pause, reason = should_pause_for_action(args.action, context)

    if should_pause:
        print(format_confirmation_prompt(args.action, reason, context))
        return 1
    else:
        print(f"✅ Action '{args.action}' approved (confidence-based)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
