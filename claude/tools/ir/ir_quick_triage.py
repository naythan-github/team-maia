#!/usr/bin/env python3
"""
IR Quick Triage Tool - Automated first-pass analysis of investigation data.

Phase 224 - IR Automation Tools
Flags HIGH/MEDIUM/LOW risk items based on detection rules.

Usage:
    from ir_quick_triage import QuickTriage, RiskLevel
    triage = QuickTriage(knowledge_base=kb)
    result = triage.analyze_sign_in(log_entry)
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

try:
    from ir_knowledge import IRKnowledgeBase
except ImportError:
    IRKnowledgeBase = None


class RiskLevel(Enum):
    """Risk level classification."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CLEAN = "CLEAN"


@dataclass
class TriageResult:
    """Result of triage analysis."""
    user: str
    risk_level: RiskLevel
    rule_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    details: str = ""
    context: str = ""


# Detection rule definitions
DETECTION_RULES = {
    # User Agent Rules
    'UA-001': {
        'name': 'Impossible User Agent',
        'description': 'Safari on Windows (impossible combination)',
        'confidence': 1.0,
        'risk': RiskLevel.HIGH
    },
    'UA-002': {
        'name': 'Spoofed Mobile',
        'description': 'Mobile UA from datacenter IP',
        'confidence': 0.9,
        'risk': RiskLevel.HIGH
    },
    # IP Rules
    'IP-001': {
        'name': 'Known Malicious',
        'description': 'IP in knowledge base malicious list',
        'confidence': 1.0,
        'risk': RiskLevel.HIGH
    },
    'IP-002': {
        'name': 'Budget VPS',
        'description': 'IP matches Hostinger/BuyVM/FranTech ASN',
        'confidence': 0.7,
        'risk': RiskLevel.MEDIUM
    },
    'IP-003': {
        'name': 'Datacenter IP',
        'description': 'IP in known datacenter ranges',
        'confidence': 0.6,
        'risk': RiskLevel.MEDIUM
    },
    # Time Rules
    'TIME-001': {
        'name': 'Off-Hours Consent',
        'description': 'OAuth consent 00:00-05:59 local',
        'confidence': 0.8,
        'risk': RiskLevel.MEDIUM
    },
    'TIME-002': {
        'name': 'Off-Hours Sign-in',
        'description': 'Sign-in 00:00-05:59 local (non-automated)',
        'confidence': 0.5,
        'risk': RiskLevel.LOW
    },
    # OAuth Rules
    'OAUTH-001': {
        'name': 'Excessive Permissions',
        'description': 'App has >50 permissions',
        'confidence': 0.9,
        'risk': RiskLevel.HIGH
    },
    'OAUTH-002': {
        'name': 'Legacy Protocol Access',
        'description': 'IMAP/POP/EAS permissions',
        'confidence': 0.8,
        'risk': RiskLevel.MEDIUM
    },
    'OAUTH-003': {
        'name': 'Unknown Multi-tenant App',
        'description': 'App not in service principals',
        'confidence': 0.7,
        'risk': RiskLevel.MEDIUM
    },
    # Pattern Rules
    'PATTERN-001': {
        'name': 'Consistent Foreign IP',
        'description': 'Single foreign IP over extended period',
        'confidence': 0.6,
        'risk': RiskLevel.MEDIUM
    }
}

# Budget VPS ASN ranges (Hostinger, BuyVM, FranTech, etc.)
BUDGET_VPS_ASNS = {
    'AS47583',   # Hostinger
    'AS53667',   # FranTech
    'AS35916',   # BuyVM
    'AS396356',  # MaxiHost
    'AS20473',   # Vultr
}

# Legacy protocol patterns
LEGACY_PROTOCOLS = ['IMAP', 'POP', 'EAS', 'SMTP', 'ActiveSync']


class QuickTriage:
    """Quick triage tool for automated first-pass analysis."""

    def __init__(self, knowledge_base: Optional['IRKnowledgeBase'] = None):
        """Initialize triage tool.

        Args:
            knowledge_base: Optional IRKnowledgeBase for cross-referencing
        """
        self.kb = knowledge_base

    def analyze_sign_in(self, log_entry: Dict[str, Any]) -> TriageResult:
        """Analyze a single sign-in log entry.

        Args:
            log_entry: Dict with sign-in log fields

        Returns:
            TriageResult with risk assessment
        """
        user = log_entry.get('userPrincipalName', 'unknown')
        ip = log_entry.get('ipAddress', '')
        user_agent = log_entry.get('userAgent', '')
        asn = log_entry.get('asn', '')

        triggered_rules = []
        max_confidence = 0.0
        details_parts = []
        context_parts = []

        # UA-001: Safari on Windows (Impossible)
        if self._is_safari_on_windows(user_agent):
            triggered_rules.append('UA-001')
            max_confidence = max(max_confidence, DETECTION_RULES['UA-001']['confidence'])
            details_parts.append(f"Safari on Windows detected in UA")

        # IP-001: Known malicious IP
        if self.kb and ip:
            ioc_results = self.kb.query_ioc('ip', ip)
            if ioc_results:
                for ioc in ioc_results:
                    if ioc.get('status') == 'BLOCKED':
                        triggered_rules.append('IP-001')
                        max_confidence = max(max_confidence, DETECTION_RULES['IP-001']['confidence'])
                        context_parts.append(f"PIR-{ioc['investigation_id']}: {ioc.get('context', '')}")
                    else:
                        # Still add context even if not blocked
                        context_parts.append(f"{ioc['investigation_id']}: {ioc.get('context', '')}")

        # IP-002: Budget VPS
        if asn and asn in BUDGET_VPS_ASNS:
            triggered_rules.append('IP-002')
            max_confidence = max(max_confidence, DETECTION_RULES['IP-002']['confidence'])
            details_parts.append(f"Budget VPS detected: {asn}")

        # Check KB for pattern matches
        if self.kb and user_agent:
            pattern_results = self.kb.query_patterns('impossible_ua')
            for pattern in pattern_results:
                if re.search(pattern['signature'], user_agent):
                    context_parts.append(f"{pattern.get('investigation_id', 'prior')}: Known impossible UA pattern")

        # Determine risk level
        risk_level = self._calculate_risk_level(triggered_rules, max_confidence)

        return TriageResult(
            user=user,
            risk_level=risk_level,
            rule_ids=triggered_rules,
            confidence=max_confidence,
            details='; '.join(details_parts) if details_parts else '',
            context='; '.join(context_parts) if context_parts else ''
        )

    def analyze_consent(self, consent_entry: Dict[str, Any]) -> TriageResult:
        """Analyze an OAuth consent entry.

        Args:
            consent_entry: Dict with consent fields

        Returns:
            TriageResult with risk assessment
        """
        user = consent_entry.get('principalId', 'unknown')
        client_id = consent_entry.get('clientId', '')
        scope = consent_entry.get('scope', '')
        timestamp = consent_entry.get('activityDateTime', '')
        ip = consent_entry.get('ipAddress', '')
        asn = consent_entry.get('asn', '')

        triggered_rules = []
        max_confidence = 0.0
        details_parts = []
        context_parts = []

        # TIME-001: Off-hours consent
        if self._is_off_hours(timestamp):
            triggered_rules.append('TIME-001')
            max_confidence = max(max_confidence, DETECTION_RULES['TIME-001']['confidence'])
            hour = self._extract_hour(timestamp)
            details_parts.append(f"Off-hours consent at {hour}:xx")

        # OAUTH-001: Excessive permissions (>50)
        permissions = scope.split() if scope else []
        if len(permissions) > 50:
            triggered_rules.append('OAUTH-001')
            max_confidence = max(max_confidence, DETECTION_RULES['OAUTH-001']['confidence'])
            details_parts.append(f"Excessive permissions: {len(permissions)}")

        # OAUTH-002: Legacy protocol
        if self._has_legacy_protocol(scope):
            triggered_rules.append('OAUTH-002')
            max_confidence = max(max_confidence, DETECTION_RULES['OAUTH-002']['confidence'])
            protocols = [p for p in LEGACY_PROTOCOLS if p in scope]
            details_parts.append(f"Legacy protocol: {', '.join(protocols)}")

        # IP-002: Budget VPS (if IP provided in consent)
        if asn and asn in BUDGET_VPS_ASNS:
            triggered_rules.append('IP-002')
            max_confidence = max(max_confidence, DETECTION_RULES['IP-002']['confidence'])
            details_parts.append(f"Budget VPS: {asn}")

        # Determine risk level
        risk_level = self._calculate_risk_level(triggered_rules, max_confidence)

        return TriageResult(
            user=user,
            risk_level=risk_level,
            rule_ids=triggered_rules,
            confidence=max_confidence,
            details='; '.join(details_parts) if details_parts else '',
            context='; '.join(context_parts) if context_parts else ''
        )

    def process_sign_in_csv(self, csv_path: str) -> List[TriageResult]:
        """Process a sign-in log CSV file.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of TriageResult for entries with findings

        Raises:
            ValueError: If CSV is malformed (includes line number)
        """
        results = []
        required_fields = ['userPrincipalName', 'ipAddress', 'userAgent', 'createdDateTime']

        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)

            # Check headers
            if reader.fieldnames is None:
                return []

            for line_num, row in enumerate(reader, start=2):  # Line 1 is header
                # Validate required fields
                for field in required_fields:
                    if field not in row or row[field] is None:
                        raise ValueError(f"Missing required field '{field}' at line {line_num}")

                result = self.analyze_sign_in(row)

                # Only include entries with findings
                if result.rule_ids:
                    results.append(result)

        return results

    def generate_report(
        self,
        customer_name: str,
        findings: List[TriageResult]
    ) -> str:
        """Generate a markdown triage report.

        Args:
            customer_name: Name of the customer
            findings: List of TriageResult

        Returns:
            Markdown formatted report
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Categorize findings
        high_risk = [f for f in findings if f.risk_level == RiskLevel.HIGH]
        medium_risk = [f for f in findings if f.risk_level == RiskLevel.MEDIUM]
        low_risk = [f for f in findings if f.risk_level == RiskLevel.LOW]

        lines = [
            f"# Triage Report: {customer_name}",
            f"Generated: {timestamp}",
            "",
            "## HIGH RISK (Immediate Investigation)",
            "",
        ]

        if high_risk:
            lines.append("| User | Finding | Rule | Confidence | Details |")
            lines.append("|------|---------|------|------------|---------|")
            for f in high_risk:
                rules = ', '.join(f.rule_ids)
                conf = f"{f.confidence * 100:.0f}%"
                lines.append(f"| {f.user} | {self._get_rule_name(f.rule_ids)} | {rules} | {conf} | {f.details} |")
        else:
            lines.append("*No high risk findings*")

        lines.extend([
            "",
            "## MEDIUM RISK (Investigation Needed)",
            "",
        ])

        if medium_risk:
            lines.append("| User | Finding | Rule | Confidence | Details |")
            lines.append("|------|---------|------|------------|---------|")
            for f in medium_risk:
                rules = ', '.join(f.rule_ids)
                conf = f"{f.confidence * 100:.0f}%"
                lines.append(f"| {f.user} | {self._get_rule_name(f.rule_ids)} | {rules} | {conf} | {f.details} |")
        else:
            lines.append("*No medium risk findings*")

        lines.extend([
            "",
            "## LOW RISK (Monitor)",
            "",
        ])

        if low_risk:
            lines.append("| User | Finding | Rule | Confidence | Details |")
            lines.append("|------|---------|------|------------|---------|")
            for f in low_risk:
                rules = ', '.join(f.rule_ids)
                conf = f"{f.confidence * 100:.0f}%"
                lines.append(f"| {f.user} | {self._get_rule_name(f.rule_ids)} | {rules} | {conf} | {f.details} |")
        else:
            lines.append("*No low risk findings*")

        lines.extend([
            "",
            "## Summary",
            f"- HIGH: {len(high_risk)} items",
            f"- MEDIUM: {len(medium_risk)} items",
            f"- LOW: {len(low_risk)} items",
        ])

        return '\n'.join(lines)

    # === Private Helper Methods ===

    def _is_safari_on_windows(self, user_agent: str) -> bool:
        """Check for impossible Safari on Windows combination."""
        if not user_agent:
            return False

        # Safari identifier present
        has_safari = 'Safari/' in user_agent and 'AppleWebKit' in user_agent

        # Not Chrome/Edge (which include Safari in UA)
        is_chrome = 'Chrome/' in user_agent or 'CriOS/' in user_agent
        is_edge = 'Edg/' in user_agent or 'Edge/' in user_agent

        # Windows platform
        is_windows = 'Windows' in user_agent

        return has_safari and not is_chrome and not is_edge and is_windows

    def _is_off_hours(self, timestamp: str) -> bool:
        """Check if timestamp is during off-hours (00:00-05:59)."""
        if not timestamp:
            return False

        try:
            # Handle ISO format with Z suffix
            if timestamp.endswith('Z'):
                timestamp = timestamp[:-1]

            dt = datetime.fromisoformat(timestamp)
            return 0 <= dt.hour < 6
        except (ValueError, AttributeError):
            return False

    def _extract_hour(self, timestamp: str) -> int:
        """Extract hour from timestamp."""
        try:
            if timestamp.endswith('Z'):
                timestamp = timestamp[:-1]
            dt = datetime.fromisoformat(timestamp)
            return dt.hour
        except (ValueError, AttributeError):
            return 0

    def _has_legacy_protocol(self, scope: str) -> bool:
        """Check if scope includes legacy protocol permissions."""
        if not scope:
            return False

        scope_upper = scope.upper()
        return any(proto in scope_upper for proto in LEGACY_PROTOCOLS)

    def _calculate_risk_level(
        self,
        triggered_rules: List[str],
        max_confidence: float
    ) -> RiskLevel:
        """Calculate overall risk level from triggered rules."""
        if not triggered_rules:
            return RiskLevel.CLEAN

        # Check if any HIGH risk rules triggered
        for rule_id in triggered_rules:
            if rule_id in DETECTION_RULES:
                if DETECTION_RULES[rule_id]['risk'] == RiskLevel.HIGH:
                    return RiskLevel.HIGH

        # Multiple medium rules compound to HIGH
        medium_count = sum(
            1 for rule_id in triggered_rules
            if rule_id in DETECTION_RULES and
            DETECTION_RULES[rule_id]['risk'] == RiskLevel.MEDIUM
        )

        if medium_count >= 2:
            return RiskLevel.HIGH

        # Check for MEDIUM risk
        for rule_id in triggered_rules:
            if rule_id in DETECTION_RULES:
                if DETECTION_RULES[rule_id]['risk'] == RiskLevel.MEDIUM:
                    return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _get_rule_name(self, rule_ids: List[str]) -> str:
        """Get human-readable name for rules."""
        if not rule_ids:
            return "Unknown"

        names = []
        for rule_id in rule_ids:
            if rule_id in DETECTION_RULES:
                names.append(DETECTION_RULES[rule_id]['name'])

        return ', '.join(names) if names else rule_ids[0]


if __name__ == "__main__":
    # Quick demo
    print("IR Quick Triage Tool - Demo")
    print("=" * 40)

    triage = QuickTriage()

    # Test Safari on Windows
    result = triage.analyze_sign_in({
        'userPrincipalName': 'test@example.com',
        'ipAddress': '10.0.0.1',
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/605.1.15 Safari/605.1.15',
        'createdDateTime': '2025-12-18T10:00:00Z'
    })

    print(f"User: {result.user}")
    print(f"Risk: {result.risk_level.value}")
    print(f"Rules: {result.rule_ids}")
    print(f"Confidence: {result.confidence}")
    print(f"Details: {result.details}")
