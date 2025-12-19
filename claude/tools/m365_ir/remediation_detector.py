#!/usr/bin/env python3
"""
Remediation Detector - Detect containment actions from M365 audit logs.

Features:
- Detect remediation events (token revokes, password resets, MFA resets)
- Identify remediation date (day with peak remediation activity)
- Calculate accurate dwell time (attack start → detection)
- Classify attack phases (Initial Access, Active Attack, Containment)

Author: Maia System
Created: 2025-12-19 (Phase 225.1)
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Dict, Optional, Set, Any
from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import AuditLogEntry, SignInLogEntry


class AttackPhase(Enum):
    """Attack lifecycle phases"""
    INITIAL_ACCESS = "initial_access"
    ACTIVE_ATTACK = "active_attack"
    DETECTION = "detection"
    CONTAINMENT = "containment"
    POST_INCIDENT = "post_incident"


# Mapping of audit activity names to remediation event types
REMEDIATION_SIGNALS = {
    "Update StsRefreshTokenValidFrom Timestamp": "token_revoke",
    "Reset user password": "password_reset",
    "Update PasswordProfile": "password_change",
    "Admin deleted security info": "mfa_reset",
    "Disable account": "account_disable",
    "Enable account": "account_enable",
}

# High-risk countries for attack detection (excluding legitimate business locations)
HIGH_RISK_COUNTRIES = {"RU", "CN", "KP", "IR", "BY", "VE", "CU", "SY", "NL", "DE", "KR", "IN", "BR", "TW", "MY", "PH"}


@dataclass
class RemediationEvent:
    """A single remediation event"""
    timestamp: datetime
    event_type: str
    user: str
    initiated_by: str
    raw_activity: str

    def __hash__(self):
        return hash((self.timestamp, self.event_type, self.user))


@dataclass
class RemediationSummary:
    """Summary of remediation activities"""
    remediation_date: Optional[date]
    first_remediation_date: Optional[date]
    total_events: int
    users_remediated: int
    remediated_users: Set[str]
    by_type: Dict[str, int]
    by_date: Dict[date, int]
    events: List[RemediationEvent]

    def get_summary_dict(self) -> Dict[str, Any]:
        """Return summary as dictionary"""
        return {
            "remediation_date": self.remediation_date.isoformat() if self.remediation_date else None,
            "first_remediation_date": self.first_remediation_date.isoformat() if self.first_remediation_date else None,
            "total_events": self.total_events,
            "users_remediated": self.users_remediated,
            "by_type": self.by_type,
        }


@dataclass
class IncidentTimeline:
    """Complete incident timeline with phases"""
    attack_start_date: Optional[date]
    attack_start_user: Optional[str]
    attack_start_country: Optional[str]
    first_remediation_date: Optional[date]
    detection_date: Optional[date]  # Bulk remediation date
    dwell_time_days: Optional[int]
    phases: List[AttackPhase]
    remediation_summary: Optional[RemediationSummary]

    def get_summary(self) -> str:
        """Generate human-readable timeline summary"""
        lines = []
        if self.attack_start_date:
            lines.append(f"Attack Start: {self.attack_start_date} ({self.attack_start_user} from {self.attack_start_country})")
        if self.first_remediation_date:
            lines.append(f"First Remediation: {self.first_remediation_date}")
        if self.detection_date:
            lines.append(f"Bulk Remediation: {self.detection_date}")
        if self.dwell_time_days is not None:
            lines.append(f"Dwell Time: {self.dwell_time_days} days")
        if self.phases:
            lines.append(f"Phases: {', '.join(p.value for p in self.phases)}")
        return "\n".join(lines)


class RemediationDetector:
    """
    Detect remediation events and build incident timeline.

    Usage:
        detector = RemediationDetector()
        summary = detector.get_remediation_summary(audit_entries)
        timeline = detector.build_incident_timeline(signin_entries, audit_entries)
    """

    def __init__(self, bulk_threshold: int = 5):
        """
        Initialize detector.

        Args:
            bulk_threshold: Minimum events per day to consider "bulk" remediation
        """
        self.bulk_threshold = bulk_threshold

    def detect_remediation_events(
        self,
        audit_entries: List[AuditLogEntry],
    ) -> List[RemediationEvent]:
        """
        Detect remediation events from audit logs.

        Args:
            audit_entries: List of audit log entries

        Returns:
            List of RemediationEvent objects
        """
        events = []

        for entry in audit_entries:
            if entry.activity_display_name in REMEDIATION_SIGNALS:
                event_type = REMEDIATION_SIGNALS[entry.activity_display_name]

                # Extract user from target field
                user = entry.target
                if "," in user:
                    user = user.split(",")[0].strip()

                events.append(RemediationEvent(
                    timestamp=entry.activity_datetime,
                    event_type=event_type,
                    user=user,
                    initiated_by=entry.initiated_by,
                    raw_activity=entry.activity_display_name,
                ))

        return events

    def get_remediation_summary(
        self,
        audit_entries: List[AuditLogEntry],
    ) -> RemediationSummary:
        """
        Generate summary of remediation activities.

        Args:
            audit_entries: List of audit log entries

        Returns:
            RemediationSummary object
        """
        events = self.detect_remediation_events(audit_entries)

        if not events:
            return RemediationSummary(
                remediation_date=None,
                first_remediation_date=None,
                total_events=0,
                users_remediated=0,
                remediated_users=set(),
                by_type={},
                by_date={},
                events=[],
            )

        # Count by type
        by_type = Counter(e.event_type for e in events)

        # Count by date
        by_date = Counter(e.timestamp.date() for e in events)

        # Find remediation date (day with most activity)
        remediation_date = by_date.most_common(1)[0][0] if by_date else None

        # Find first remediation date
        first_remediation_date = min(e.timestamp.date() for e in events) if events else None

        # Get unique users
        remediated_users = set(e.user for e in events)

        return RemediationSummary(
            remediation_date=remediation_date,
            first_remediation_date=first_remediation_date,
            total_events=len(events),
            users_remediated=len(remediated_users),
            remediated_users=remediated_users,
            by_type=dict(by_type),
            by_date=dict(by_date),
            events=events,
        )

    def detect_attack_start(
        self,
        signin_entries: List[SignInLogEntry],
        home_country: str = "AU",
        exclude_countries: Optional[Set[str]] = None,
    ) -> Optional[datetime]:
        """
        Detect attack start from first foreign sign-in.

        Args:
            signin_entries: List of sign-in log entries
            home_country: Organization's home country
            exclude_countries: Countries to exclude (e.g., {"US"} for AU companies with US staff)

        Returns:
            Datetime of first foreign sign-in, or None if no foreign sign-ins
        """
        if exclude_countries is None:
            exclude_countries = {"US"}  # Default: exclude US for AU companies

        # Countries to consider as "home" (not attack)
        safe_countries = {home_country} | exclude_countries

        # Find first foreign sign-in
        foreign_signins = [
            e for e in signin_entries
            if e.country and e.country not in safe_countries
        ]

        if not foreign_signins:
            return None

        # Sort by timestamp and return earliest
        foreign_signins.sort(key=lambda x: x.created_datetime)
        return foreign_signins[0].created_datetime

    def build_incident_timeline(
        self,
        signin_entries: List[SignInLogEntry],
        audit_entries: List[AuditLogEntry],
        home_country: str = "AU",
    ) -> IncidentTimeline:
        """
        Build complete incident timeline.

        Args:
            signin_entries: List of sign-in log entries
            audit_entries: List of audit log entries
            home_country: Organization's home country

        Returns:
            IncidentTimeline object
        """
        # Get remediation summary
        remediation_summary = self.get_remediation_summary(audit_entries)

        # Detect attack start
        attack_start = self.detect_attack_start(signin_entries, home_country)

        # Find attack start details
        attack_start_user = None
        attack_start_country = None
        if attack_start:
            for e in signin_entries:
                if e.created_datetime == attack_start:
                    attack_start_user = e.user_principal_name
                    attack_start_country = e.country
                    break

        # Calculate dwell time
        dwell_time_days = None
        if attack_start and remediation_summary.remediation_date:
            dwell_time_days = (remediation_summary.remediation_date - attack_start.date()).days

        # Classify phases
        phases = []
        if attack_start:
            phases.append(AttackPhase.INITIAL_ACCESS)
            phases.append(AttackPhase.ACTIVE_ATTACK)
        if remediation_summary.total_events > 0:
            phases.append(AttackPhase.CONTAINMENT)

        return IncidentTimeline(
            attack_start_date=attack_start.date() if attack_start else None,
            attack_start_user=attack_start_user,
            attack_start_country=attack_start_country,
            first_remediation_date=remediation_summary.first_remediation_date,
            detection_date=remediation_summary.remediation_date,
            dwell_time_days=dwell_time_days,
            phases=phases,
            remediation_summary=remediation_summary,
        )

    def get_summary(self, timeline: IncidentTimeline) -> Dict[str, Any]:
        """Get timeline summary as dictionary."""
        return {
            "attack_start_date": timeline.attack_start_date.isoformat() if timeline.attack_start_date else None,
            "attack_start_user": timeline.attack_start_user,
            "attack_start_country": timeline.attack_start_country,
            "detection_date": timeline.detection_date.isoformat() if timeline.detection_date else None,
            "dwell_time_days": timeline.dwell_time_days,
            "phases": [p.value for p in timeline.phases],
            "remediation": timeline.remediation_summary.get_summary_dict() if timeline.remediation_summary else None,
        }


if __name__ == "__main__":
    # Quick test with Oculus data
    from claude.tools.m365_ir.m365_log_parser import M365LogParser, LogType

    if len(sys.argv) > 1:
        export_paths = [Path(p) for p in sys.argv[1:]]
        parser = M365LogParser.from_export(export_paths[0])

        # Load entries
        signin_entries = parser.merge_exports(export_paths, LogType.SIGNIN)
        audit_entries = []
        for export in export_paths:
            discovered = parser.discover_log_files(export)
            if LogType.AUDIT in discovered:
                audit_entries.extend(parser.parse_audit_logs(discovered[LogType.AUDIT]))

        print(f"Loaded {len(signin_entries)} sign-in entries")
        print(f"Loaded {len(audit_entries)} audit entries")

        # Detect remediation
        detector = RemediationDetector()
        timeline = detector.build_incident_timeline(signin_entries, audit_entries)

        print(f"\n{timeline.get_summary()}")
