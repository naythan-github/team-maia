#!/usr/bin/env python3
"""
AssumptionLog - Track and validate assumptions during IR investigations

Phase 230: Account Validator Implementation
Requirements: FR-4 (Explicit Assumption Logging)

PURPOSE: Prevent assumption-based errors by explicitly logging all inferences
and validating them against source data.

CRITICAL: This class prevents the ben@oculus.info error where we assumed
account was disabled long ago without checking actual timestamps.
"""

from datetime import datetime
from typing import List, Dict, Any


class AssumptionLog:
    """
    Track all assumptions made during investigation.

    Each assumption must be:
    1. Explicitly stated (what we're inferring)
    2. Based on evidence (what data led to this inference)
    3. Validated with query (how we check if it's true)
    4. Marked as PROVEN/DISPROVEN (result of validation)
    """

    def __init__(self):
        """Initialize empty assumption log."""
        self.assumptions: List[Dict[str, Any]] = []

    def add_assumption(
        self,
        statement: str,
        evidence: str,
        validation_query: str,
        result: str
    ) -> None:
        """
        Log an assumption with validation result.

        Args:
            statement: The assumption being made (e.g., "Account was disabled before attack")
            evidence: What observable data led to this assumption
            validation_query: The SQL query used to validate the assumption
            result: Validation result - must start with "PROVEN" or "DISPROVEN"

        Example:
            assumption_log.add_assumption(
                statement="Account was disabled before attack",
                evidence="account_enabled=False, password from 2020",
                validation_query="SELECT timestamp FROM entra_audit_log WHERE activity='Disable account'",
                result="DISPROVEN - disabled 2025-12-03, attack started 2025-11-04"
            )
        """
        proven = result.upper().startswith("PROVEN")

        self.assumptions.append({
            'assumption': statement,
            'based_on': evidence,
            'validation_query': validation_query,
            'result': result,
            'proven': proven,
            'timestamp': datetime.now().isoformat()
        })

    def get_disproven_assumptions(self) -> List[Dict[str, Any]]:
        """
        Return assumptions that were disproven - HIGH RISK.

        A disproven assumption means we made an inference that was
        contradicted by the data. This is a critical analytical error.

        Returns:
            List of disproven assumptions with full details
        """
        return [a for a in self.assumptions if not a['proven']]

    def get_proven_assumptions(self) -> List[Dict[str, Any]]:
        """Return assumptions that were validated."""
        return [a for a in self.assumptions if a['proven']]

    def has_disproven_assumptions(self) -> bool:
        """Check if any assumptions were disproven."""
        return len(self.get_disproven_assumptions()) > 0

    def summary(self) -> Dict[str, Any]:
        """
        Get summary of all assumptions.

        Returns:
            Dict with counts and lists of proven/disproven assumptions
        """
        disproven = self.get_disproven_assumptions()
        proven = self.get_proven_assumptions()

        return {
            'total_assumptions': len(self.assumptions),
            'proven_count': len(proven),
            'disproven_count': len(disproven),
            'proven': proven,
            'disproven': disproven
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"AssumptionLog({len(self.assumptions)} assumptions, {len(self.get_disproven_assumptions())} disproven)"
