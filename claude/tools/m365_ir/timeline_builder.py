#!/usr/bin/env python3
"""
Timeline Builder - Correlate events and build attack timeline

Features:
- Merge events from multiple log sources
- Chronological sorting
- Attack phase detection (Initial Access, Persistence, Containment)
- Event correlation
- PIR-ready formatting

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import hashlib
import sqlite3
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry, AuditLogEntry, MailboxAuditEntry


class EventPhase(Enum):
    """Attack phases (MITRE-aligned)"""
    INITIAL_ACCESS = "Initial Access"
    PERSISTENCE = "Persistence"
    COLLECTION = "Collection"
    EXFILTRATION = "Exfiltration"
    DETECTION = "Detection"
    CONTAINMENT = "Containment"
    ERADICATION = "Eradication"
    RECOVERY = "Recovery"
    UNKNOWN = "Unknown"


# Keywords to detect attack phases
PHASE_KEYWORDS = {
    EventPhase.PERSISTENCE: [
        "Set-InboxRule", "inbox rule", "forwarding", "Set-Mailbox",
        "Add-MailboxPermission", "delegate", "transport rule"
    ],
    EventPhase.COLLECTION: [
        "MailItemsAccessed", "MessageBind", "FolderBind"
    ],
    EventPhase.CONTAINMENT: [
        "Reset user password", "password reset", "conditional access",
        "named location", "Revoke", "Disable user", "Block"
    ],
    EventPhase.ERADICATION: [
        "Remove-InboxRule", "remove inbox rule", "delete rule"
    ],
}

# High-risk countries for attack detection (nation-state threat actors)
HIGH_RISK_COUNTRIES = {"RU", "CN", "KP", "IR", "BY", "VE", "CU", "SY"}


@dataclass
class TimelineEvent:
    """A single event in the timeline"""
    timestamp: datetime
    user: str
    action: str
    details: str
    source_type: str  # signin, audit, mailbox, legacy_auth
    phase: EventPhase = EventPhase.UNKNOWN
    severity: str = "INFO"  # INFO, WARNING, ALERT, CRITICAL
    evidence: Dict[str, Any] = field(default_factory=dict)
    related_events: List["TimelineEvent"] = field(default_factory=list)

    def __hash__(self):
        return hash((self.timestamp.isoformat(), self.user, self.action))


@dataclass
class PhaseMarker:
    """Marks the start of an attack phase"""
    phase: EventPhase
    timestamp: datetime
    trigger_event: TimelineEvent
    description: str


def build_timeline(
    signin_entries: List[SignInLogEntry] = None,
    audit_entries: List[AuditLogEntry] = None,
    mailbox_entries: List[MailboxAuditEntry] = None,
) -> List[TimelineEvent]:
    """
    Build timeline from multiple log sources.

    Args:
        signin_entries: Sign-in log entries
        audit_entries: Audit log entries
        mailbox_entries: Mailbox audit entries

    Returns:
        Chronologically sorted list of TimelineEvents
    """
    events = []

    # Convert sign-in entries
    if signin_entries:
        for entry in signin_entries:
            events.append(TimelineEvent(
                timestamp=entry.created_datetime,
                user=entry.user_principal_name,
                action=f"Sign-in from {entry.country}",
                details=f"{entry.city}, {entry.country} via {entry.app_display_name}",
                source_type="signin",
                evidence={
                    "ip_address": entry.ip_address,
                    "country": entry.country,
                    "city": entry.city,
                    "app": entry.app_display_name,
                    "status": entry.status_normalized,
                },
            ))

    # Convert audit entries
    if audit_entries:
        for entry in audit_entries:
            events.append(TimelineEvent(
                timestamp=entry.activity_datetime,
                user=entry.target or entry.initiated_by or "System",
                action=entry.activity_display_name,
                details=f"Initiated by: {entry.initiated_by}, Target: {entry.target}",
                source_type="audit",
                evidence={
                    "initiated_by": entry.initiated_by,
                    "target": entry.target,
                    "result": entry.result,
                },
            ))

    # Convert mailbox entries
    if mailbox_entries:
        for entry in mailbox_entries:
            events.append(TimelineEvent(
                timestamp=entry.creation_date,
                user=entry.user_id,
                action=entry.operation,
                details=f"Client: {entry.client_info}, IP: {entry.client_ip_address}",
                source_type="mailbox",
                evidence={
                    "operation": entry.operation,
                    "client_ip": entry.client_ip_address,
                    "folders": entry.folders,
                },
            ))

    # Sort chronologically
    events.sort(key=lambda e: e.timestamp)

    return events


def correlate_events(events: List[TimelineEvent]) -> List[TimelineEvent]:
    """
    Correlate related events (e.g., login → password reset).

    Args:
        events: List of timeline events

    Returns:
        Events with related_events populated
    """
    # Group by user
    user_events: Dict[str, List[TimelineEvent]] = defaultdict(list)
    for event in events:
        user_events[event.user].append(event)

    # Find correlations within each user's events
    for user, user_timeline in user_events.items():
        for i, event in enumerate(user_timeline):
            # Look for related events within 24 hours
            window_start = event.timestamp - timedelta(hours=24)
            window_end = event.timestamp + timedelta(hours=24)

            for j, other in enumerate(user_timeline):
                if i == j:
                    continue
                if window_start <= other.timestamp <= window_end:
                    # Check if events are related
                    if _are_events_related(event, other):
                        event.related_events.append(other)

    return events


def _are_events_related(event1: TimelineEvent, event2: TimelineEvent) -> bool:
    """Check if two events are logically related."""
    # Password reset after login
    if "Sign-in" in event1.action and "password" in event2.action.lower():
        return True
    # CA policy changes together
    if "conditional access" in event1.action.lower() and "conditional access" in event2.action.lower():
        return True
    if "named location" in event1.action.lower() and "conditional access" in event2.action.lower():
        return True
    return False


def detect_attack_phases(
    events: List[TimelineEvent],
    home_country: str = "AU",
) -> List[PhaseMarker]:
    """
    Detect attack phases from timeline events.

    Args:
        events: Timeline events
        home_country: Expected home country for users

    Returns:
        List of phase markers
    """
    phases = []
    seen_phases: Dict[str, set] = {}  # Track phases per user

    for event in events:
        user = event.user
        if user not in seen_phases:
            seen_phases[user] = set()

        # Detect Initial Access (first foreign login)
        if event.source_type == "signin":
            country = event.evidence.get("country", "")
            if country and country != home_country and country in HIGH_RISK_COUNTRIES:
                if EventPhase.INITIAL_ACCESS not in seen_phases[user]:
                    phases.append(PhaseMarker(
                        phase=EventPhase.INITIAL_ACCESS,
                        timestamp=event.timestamp,
                        trigger_event=event,
                        description=f"First foreign access from {country}",
                    ))
                    seen_phases[user].add(EventPhase.INITIAL_ACCESS)
                    event.phase = EventPhase.INITIAL_ACCESS
                    event.severity = "ALERT"

        # Detect other phases by keywords
        action_lower = event.action.lower()
        for phase, keywords in PHASE_KEYWORDS.items():
            if any(kw.lower() in action_lower for kw in keywords):
                if phase not in seen_phases[user]:
                    phases.append(PhaseMarker(
                        phase=phase,
                        timestamp=event.timestamp,
                        trigger_event=event,
                        description=f"{phase.value}: {event.action}",
                    ))
                    seen_phases[user].add(phase)
                event.phase = phase

                # Set severity based on phase
                if phase in [EventPhase.PERSISTENCE, EventPhase.COLLECTION]:
                    event.severity = "CRITICAL"
                elif phase == EventPhase.CONTAINMENT:
                    event.severity = "INFO"

    return phases


class TimelineBuilder:
    """
    Build and analyze attack timelines.

    Phase 260: Now supports database persistence for incremental builds.

    Usage:
        # In-memory (original)
        builder = TimelineBuilder()
        timeline = builder.build(signin_entries, audit_entries)

        # Persisted (new)
        from log_database import IRLogDatabase
        db = IRLogDatabase(case_id="PIR-CASE-001")
        builder = TimelineBuilder(db=db)
        builder.build_and_persist(incremental=True)
    """

    def __init__(self, home_country: str = "AU", db=None):
        self.home_country = home_country
        self.db = db

    def build(
        self,
        signin_entries: List[SignInLogEntry] = None,
        audit_entries: List[AuditLogEntry] = None,
        mailbox_entries: List[MailboxAuditEntry] = None,
    ) -> List[TimelineEvent]:
        """Build timeline from log entries."""
        timeline = build_timeline(signin_entries, audit_entries, mailbox_entries)
        timeline = correlate_events(timeline)
        detect_attack_phases(timeline, self.home_country)
        return timeline

    def get_summary(self, timeline: List[TimelineEvent]) -> Dict[str, Any]:
        """Get summary statistics from timeline."""
        if not timeline:
            return {
                "total_events": 0,
                "date_range": None,
                "users_involved": [],
            }

        users = list(set(e.user for e in timeline))
        phases = list(set(e.phase.value for e in timeline if e.phase != EventPhase.UNKNOWN))

        return {
            "total_events": len(timeline),
            "date_range": {
                "start": timeline[0].timestamp.isoformat(),
                "end": timeline[-1].timestamp.isoformat(),
            },
            "users_involved": users,
            "phases_detected": phases,
            "events_by_type": self._count_by_type(timeline),
            "events_by_severity": self._count_by_severity(timeline),
        }

    def _count_by_type(self, timeline: List[TimelineEvent]) -> Dict[str, int]:
        """Count events by source type."""
        return dict(Counter(e.source_type for e in timeline))

    def _count_by_severity(self, timeline: List[TimelineEvent]) -> Dict[str, int]:
        """Count events by severity."""
        return dict(Counter(e.severity for e in timeline))

    def filter_by_user(
        self,
        timeline: List[TimelineEvent],
        user: str,
    ) -> List[TimelineEvent]:
        """Filter timeline to specific user."""
        return [e for e in timeline if e.user == user]

    def filter_by_date_range(
        self,
        timeline: List[TimelineEvent],
        start: datetime,
        end: datetime,
    ) -> List[TimelineEvent]:
        """Filter timeline to date range."""
        return [e for e in timeline if start <= e.timestamp <= end]

    def format_markdown(self, timeline: List[TimelineEvent]) -> str:
        """Format timeline as markdown table."""
        if not timeline:
            return "No events in timeline."

        lines = [
            "| Time (UTC) | User | Action | Details | Phase |",
            "|------------|------|--------|---------|-------|",
        ]

        for event in timeline:
            time_str = event.timestamp.strftime("%Y-%m-%d %H:%M")
            phase_str = event.phase.value if event.phase != EventPhase.UNKNOWN else "-"
            lines.append(
                f"| {time_str} | {event.user} | {event.action} | {event.details[:50]}... | {phase_str} |"
            )

        return "\n".join(lines)

    def format_for_pir(self, timeline: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Format timeline for PIR report."""
        pir_events = []

        for event in timeline:
            pir_events.append({
                "timestamp": event.timestamp.isoformat(),
                "time_display": event.timestamp.strftime("%b %d, %Y %H:%M UTC"),
                "user": event.user,
                "action": event.action,
                "details": event.details,
                "phase": event.phase.value,
                "severity": event.severity,
                "source": event.source_type,
            })

        return pir_events

    # ================================================================
    # Phase 260: Timeline Persistence Methods
    # ================================================================

    def build_and_persist(
        self,
        incremental: bool = True,
        force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """
        Build timeline from raw logs and persist to database.

        Args:
            incremental: Only process new records since last build
            force_rebuild: Clear existing timeline and rebuild from scratch

        Returns:
            Build result with statistics
        """
        if not self.db:
            raise ValueError("Database required for persistence. Pass db= to __init__")

        import json
        from claude.tools.m365_ir.timeline_filter import (
            is_interesting_event, get_event_severity, map_mitre_technique
        )

        conn = self.db.connect()
        cursor = conn.cursor()

        build_start = datetime.now().isoformat()
        events_added = 0
        events_updated = 0

        # Get last processed timestamps per source if incremental
        last_processed = {}
        if incremental and not force_rebuild:
            cursor.execute("""
                SELECT source_type, MAX(timestamp) as last_ts
                FROM timeline_events
                GROUP BY source_type
            """)
            for row in cursor.fetchall():
                last_processed[row['source_type']] = row['last_ts']

        # Process sign_in_logs
        where_clause = ""
        if 'sign_in_logs' in last_processed:
            where_clause = f"WHERE timestamp > '{last_processed['sign_in_logs']}'"

        cursor.execute(f"SELECT * FROM sign_in_logs {where_clause} ORDER BY timestamp")
        for row in cursor.fetchall():
            event_dict = dict(row)
            event_dict['source_type'] = 'sign_in_logs'

            if is_interesting_event(event_dict, self.home_country):
                event_hash = compute_event_hash(
                    row['timestamp'],
                    row['user_principal_name'],
                    f"Sign-in from {row['location_country']}" if row['location_country'] else "Sign-in",
                    row['id']
                )

                severity = get_event_severity(event_dict)
                mitre = map_mitre_technique(event_dict)

                try:
                    cursor.execute("""
                        INSERT INTO timeline_events
                        (event_hash, timestamp, user_principal_name, action, details,
                         source_type, source_id, severity, mitre_technique,
                         ip_address, location_country, client_app, created_at, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event_hash,
                        event_dict['timestamp'],
                        event_dict['user_principal_name'],
                        f"Sign-in from {event_dict.get('location_country')}" if event_dict.get('location_country') else "Sign-in",
                        event_dict.get('app_display_name', '') or '',
                        'sign_in_logs',
                        event_dict['id'],
                        severity,
                        mitre,
                        event_dict.get('ip_address'),
                        event_dict.get('location_country'),
                        event_dict.get('app_display_name'),
                        datetime.now().isoformat(),
                        get_analyst_name()
                    ))
                    events_added += 1
                except sqlite3.IntegrityError:
                    # Duplicate event_hash - skip
                    pass

        # Record build history
        cursor.execute("""
            INSERT INTO timeline_build_history
            (build_timestamp, build_type, events_added, events_updated,
             source_tables, home_country, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            build_start,
            'incremental' if incremental else 'full',
            events_added,
            events_updated,
            json.dumps({'sign_in_logs': 1}),
            self.home_country,
            'completed'
        ))

        conn.commit()
        conn.close()

        return {
            'events_added': events_added,
            'events_updated': events_updated,
            'build_type': 'incremental' if incremental else 'full'
        }

    def add_annotation(
        self,
        event_id: int,
        annotation_type: str,
        content: str,
        pir_section: Optional[str] = None
    ) -> int:
        """
        Add analyst annotation to timeline event.

        Args:
            event_id: Timeline event ID
            annotation_type: Type (note, finding, question, ioc, false_positive)
            content: Annotation content
            pir_section: PIR section to include in (optional)

        Returns:
            Annotation ID
        """
        if not self.db:
            raise ValueError("Database required")

        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO timeline_annotations
            (timeline_event_id, annotation_type, content, pir_section, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            annotation_type,
            content,
            pir_section,
            datetime.now().isoformat(),
            get_analyst_name()
        ))

        annotation_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return annotation_id

    def exclude_event(self, event_id: int, reason: str) -> None:
        """
        Soft-delete event from timeline with reason.

        Args:
            event_id: Timeline event ID
            reason: Exclusion reason
        """
        if not self.db:
            raise ValueError("Database required")

        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE timeline_events
            SET excluded = 1, exclusion_reason = ?
            WHERE id = ?
        """, (reason, event_id))

        conn.commit()
        conn.close()

    def get_timeline(
        self,
        user: Optional[str] = None,
        phase: Optional[str] = None,
        severity: Optional[str] = None,
        include_excluded: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query persisted timeline with filters.

        Args:
            user: Filter by user (optional)
            phase: Filter by phase (optional)
            severity: Filter by severity (optional)
            include_excluded: Include soft-deleted events

        Returns:
            List of timeline event dicts
        """
        if not self.db:
            raise ValueError("Database required")

        conn = self.db.connect()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if not include_excluded:
            where_clauses.append("excluded = 0")

        if user:
            where_clauses.append("user_principal_name = ?")
            params.append(user)

        if phase:
            where_clauses.append("phase = ?")
            params.append(phase)

        if severity:
            where_clauses.append("severity = ?")
            params.append(severity)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        cursor.execute(f"""
            SELECT * FROM timeline_events
            WHERE {where_sql}
            ORDER BY timestamp
        """, params)

        events = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return events


def compute_event_hash(timestamp: str, user: str, action: str, source_id: int) -> str:
    """Generate unique hash for timeline event deduplication."""
    data = f"{timestamp}|{user}|{action}|{source_id}"
    return hashlib.sha256(data.encode()).hexdigest()


def get_analyst_name() -> str:
    """Get analyst name for created_by field."""
    import os
    import subprocess

    if name := os.environ.get('MAIA_ANALYST'):
        return name

    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except:
        return 'system'


if __name__ == "__main__":
    # Quick test with Oculus data
    import sys
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

        # Build timeline
        builder = TimelineBuilder()
        timeline = builder.build(signin_entries=signin_entries, audit_entries=audit_entries)

        summary = builder.get_summary(timeline)
        print(f"\nTimeline Summary:")
        print(f"  Total events: {summary['total_events']}")
        print(f"  Date range: {summary['date_range']}")
        print(f"  Users: {len(summary['users_involved'])}")
        print(f"  Phases: {summary['phases_detected']}")

        # Show key events (non-INFO severity)
        key_events = [e for e in timeline if e.severity != "INFO"][:20]
        print(f"\nKey events ({len(key_events)} shown):")
        for event in key_events:
            print(f"  [{event.severity}] {event.timestamp.strftime('%Y-%m-%d %H:%M')} - {event.user}: {event.action}")
