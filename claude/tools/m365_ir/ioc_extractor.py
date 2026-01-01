#!/usr/bin/env python3
"""
IOC Extractor and MITRE ATT&CK Mapper

Features:
- Extract IOCs (IPs, countries, user agents, OAuth apps)
- Map events to MITRE ATT&CK techniques
- Export IOCs to CSV/JSON
- Generate IOC summary

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple, Set
from pathlib import Path
import csv
import json
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry, LegacyAuthEntry, MailboxAuditEntry


class IOCType(Enum):
    """Types of Indicators of Compromise"""
    IP_ADDRESS = "ip_address"
    COUNTRY = "country"
    USER_AGENT = "user_agent"
    OAUTH_APP = "oauth_app"
    EMAIL_RULE = "email_rule"
    FORWARDING_ADDRESS = "forwarding_address"


@dataclass
class IOC:
    """An Indicator of Compromise"""
    ioc_type: IOCType
    value: str
    first_seen: datetime
    last_seen: datetime
    count: int
    affected_users: Set[str] = field(default_factory=set)
    context: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.ioc_type, self.value))


@dataclass
class MitreTechnique:
    """MITRE ATT&CK Technique"""
    technique_id: str
    name: str
    tactic: str
    description: str
    url: str = ""


# MITRE ATT&CK mappings for M365 attacks
MITRE_MAPPINGS = {
    # Initial Access
    "signin_foreign": MitreTechnique(
        technique_id="T1078.004",
        name="Valid Accounts: Cloud Accounts",
        tactic="Initial Access",
        description="Adversaries may obtain and abuse credentials of a cloud account",
        url="https://attack.mitre.org/techniques/T1078/004/",
    ),
    "legacy_auth": MitreTechnique(
        technique_id="T1078.004",
        name="Valid Accounts: Cloud Accounts",
        tactic="Initial Access",
        description="Legacy auth (IMAP/SMTP) bypasses MFA",
        url="https://attack.mitre.org/techniques/T1078/004/",
    ),
    # Persistence
    "inbox_rule": MitreTechnique(
        technique_id="T1114.003",
        name="Email Collection: Email Forwarding Rule",
        tactic="Persistence",
        description="Adversaries may setup email forwarding rules",
        url="https://attack.mitre.org/techniques/T1114/003/",
    ),
    "delegate_access": MitreTechnique(
        technique_id="T1098.002",
        name="Account Manipulation: Additional Email Delegate Permissions",
        tactic="Persistence",
        description="Adversaries may grant additional permission levels to mailbox",
        url="https://attack.mitre.org/techniques/T1098/002/",
    ),
    # Collection
    "mailbox_access": MitreTechnique(
        technique_id="T1114.002",
        name="Email Collection: Remote Email Collection",
        tactic="Collection",
        description="Adversaries may access email to collect sensitive information",
        url="https://attack.mitre.org/techniques/T1114/002/",
    ),
    # Defense Evasion
    "delete_rule": MitreTechnique(
        technique_id="T1070.008",
        name="Indicator Removal: Clear Mailbox Data",
        tactic="Defense Evasion",
        description="Adversaries may modify/delete mail to remove evidence",
        url="https://attack.mitre.org/techniques/T1070/008/",
    ),
    # Account Manipulation
    "password_reset": MitreTechnique(
        technique_id="T1098",
        name="Account Manipulation",
        tactic="Persistence",
        description="Account modification for persistence or access",
        url="https://attack.mitre.org/techniques/T1098/",
    ),
}

# Keywords to technique mappings
TECHNIQUE_KEYWORDS = {
    "signin_foreign": ["Sign-in from RU", "Sign-in from CN", "Sign-in from KP", "Sign-in from IR"],
    "legacy_auth": ["IMAP", "SMTP", "POP3", "legacy_auth"],
    "inbox_rule": ["Set-InboxRule", "inbox rule", "InboxRule", "forwarding"],
    "delegate_access": ["Add-MailboxPermission", "delegate", "SendAs", "SendOnBehalf"],
    "mailbox_access": ["MailItemsAccessed", "MessageBind", "FolderBind"],
    "delete_rule": ["HardDelete", "Remove-InboxRule", "delete"],
    "password_reset": ["Reset user password", "password reset", "Password changed"],
}


class IOCExtractor:
    """
    Extract Indicators of Compromise from M365 logs.

    Usage:
        extractor = IOCExtractor()
        iocs = extractor.extract(signin_entries, legacy_entries)
        extractor.export_csv(iocs, "iocs.csv")
    """

    def _update_or_create_ioc(
        self,
        ioc_map: Dict[Tuple[IOCType, str], IOC],
        ioc_type: IOCType,
        value: str,
        timestamp: datetime,
        user: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IOC:
        """
        Update existing IOC or create new one.

        Args:
            ioc_map: Map of existing IOCs
            ioc_type: Type of IOC
            value: IOC value
            timestamp: Event timestamp
            user: Affected user
            context: Optional context dict

        Returns:
            Updated or created IOC
        """
        key = (ioc_type, value)
        if key not in ioc_map:
            ioc_map[key] = IOC(
                ioc_type=ioc_type,
                value=value,
                first_seen=timestamp,
                last_seen=timestamp,
                count=0,
                affected_users=set(),
                context=context.copy() if context else {},
            )
        ioc = ioc_map[key]
        ioc.count += 1
        ioc.affected_users.add(user)
        ioc.last_seen = max(ioc.last_seen, timestamp)
        ioc.first_seen = min(ioc.first_seen, timestamp)
        return ioc

    def extract(
        self,
        signin_entries: List[SignInLogEntry] = None,
        legacy_entries: List[LegacyAuthEntry] = None,
        mailbox_entries: List[MailboxAuditEntry] = None,
    ) -> List[IOC]:
        """
        Extract all IOCs from log entries.

        Args:
            signin_entries: Sign-in log entries
            legacy_entries: Legacy auth entries
            mailbox_entries: Mailbox audit entries

        Returns:
            List of deduplicated IOCs
        """
        ioc_map: Dict[Tuple[IOCType, str], IOC] = {}

        # Extract from sign-in logs
        if signin_entries:
            for entry in signin_entries:
                # IP addresses
                if entry.ip_address:
                    ioc = self._update_or_create_ioc(
                        ioc_map, IOCType.IP_ADDRESS, entry.ip_address,
                        entry.created_datetime, entry.user_principal_name,
                        context={"countries": set(), "cities": set()}
                    )
                    ioc.context.setdefault("countries", set()).add(entry.country)
                    ioc.context.setdefault("cities", set()).add(entry.city)

                # Countries
                if entry.country:
                    self._update_or_create_ioc(
                        ioc_map, IOCType.COUNTRY, entry.country,
                        entry.created_datetime, entry.user_principal_name
                    )

                # User agents (browser + OS)
                if entry.browser or entry.os:
                    ua = f"{entry.browser} / {entry.os}"
                    self._update_or_create_ioc(
                        ioc_map, IOCType.USER_AGENT, ua,
                        entry.created_datetime, entry.user_principal_name
                    )

        # Extract from legacy auth
        if legacy_entries:
            for entry in legacy_entries:
                if entry.ip_address:
                    ioc = self._update_or_create_ioc(
                        ioc_map, IOCType.IP_ADDRESS, entry.ip_address,
                        entry.created_datetime, entry.user_principal_name,
                        context={"legacy_auth": True}
                    )
                    ioc.context["legacy_auth"] = True

        # Convert context sets to lists for JSON serialization
        for ioc in ioc_map.values():
            if "countries" in ioc.context:
                ioc.context["countries"] = list(ioc.context["countries"])
            if "cities" in ioc.context:
                ioc.context["cities"] = list(ioc.context["cities"])

        return list(ioc_map.values())

    def export_csv(self, iocs: List[IOC], path: Path) -> None:
        """Export IOCs to CSV file."""
        path = Path(path)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Value", "Count", "First Seen", "Last Seen", "Affected Users"])
            for ioc in iocs:
                writer.writerow([
                    ioc.ioc_type.value,
                    ioc.value,
                    ioc.count,
                    ioc.first_seen.isoformat(),
                    ioc.last_seen.isoformat(),
                    ";".join(ioc.affected_users),
                ])

    def export_json(self, iocs: List[IOC], path: Path) -> None:
        """Export IOCs to JSON file."""
        path = Path(path)
        data = []
        for ioc in iocs:
            data.append({
                "type": ioc.ioc_type.value,
                "value": ioc.value,
                "count": ioc.count,
                "first_seen": ioc.first_seen.isoformat(),
                "last_seen": ioc.last_seen.isoformat(),
                "affected_users": list(ioc.affected_users),
                "context": ioc.context,
            })
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_summary(self, iocs: List[IOC]) -> Dict[str, Any]:
        """Get IOC summary statistics."""
        by_type = Counter(i.ioc_type.value for i in iocs)

        ip_iocs = sorted(
            [i for i in iocs if i.ioc_type == IOCType.IP_ADDRESS],
            key=lambda x: x.count,
            reverse=True
        )
        country_iocs = sorted(
            [i for i in iocs if i.ioc_type == IOCType.COUNTRY],
            key=lambda x: x.count,
            reverse=True
        )

        return {
            "total_iocs": len(iocs),
            "by_type": dict(by_type),
            "top_ips": [(i.value, i.count) for i in ip_iocs[:10]],
            "top_countries": [(i.value, i.count) for i in country_iocs[:10]],
            "unique_ips": len(ip_iocs),
            "unique_countries": len(country_iocs),
        }


class MitreMapper:
    """
    Map M365 events to MITRE ATT&CK techniques.

    Usage:
        mapper = MitreMapper()
        technique = mapper.map_event("Set-InboxRule", "audit")
    """

    def map_event(self, action: str, source_type: str) -> Optional[MitreTechnique]:
        """
        Map an event to a MITRE ATT&CK technique.

        Args:
            action: Event action/name
            source_type: Log source type (signin, audit, mailbox, legacy_auth)

        Returns:
            MitreTechnique or None
        """
        action_lower = action.lower()

        # Check each technique's keywords
        for technique_key, keywords in TECHNIQUE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in action_lower:
                    return MITRE_MAPPINGS.get(technique_key)

        # Source-type specific mappings
        if source_type == "legacy_auth":
            return MITRE_MAPPINGS.get("legacy_auth")

        if source_type == "signin" and any(c in action for c in ["RU", "CN", "KP", "IR"]):
            return MITRE_MAPPINGS.get("signin_foreign")

        return None

    def get_techniques_for_events(
        self,
        events: List[Tuple[str, str]],
    ) -> List[MitreTechnique]:
        """
        Get all unique MITRE techniques for a list of events.

        Args:
            events: List of (action, source_type) tuples

        Returns:
            List of unique MitreTechniques
        """
        techniques = {}
        for action, source_type in events:
            technique = self.map_event(action, source_type)
            if technique and technique.technique_id not in techniques:
                techniques[technique.technique_id] = technique
        return list(techniques.values())

    def get_technique_summary(
        self,
        techniques: List[MitreTechnique],
    ) -> Dict[str, List[MitreTechnique]]:
        """Group techniques by tactic."""
        by_tactic: Dict[str, List[MitreTechnique]] = defaultdict(list)
        for t in techniques:
            by_tactic[t.tactic].append(t)
        return dict(by_tactic)


if __name__ == "__main__":
    # Quick test with Oculus data
    import sys
    from claude.tools.m365_ir.m365_log_parser import M365LogParser, LogType

    if len(sys.argv) > 1:
        export_paths = [Path(p) for p in sys.argv[1:]]
        parser = M365LogParser.from_export(export_paths[0])

        # Load entries
        signin_entries = parser.merge_exports(export_paths, LogType.SIGNIN)
        legacy_entries = []
        for export in export_paths:
            discovered = parser.discover_log_files(export)
            if LogType.LEGACY_AUTH in discovered:
                legacy_entries.extend(parser.parse_legacy_auth(discovered[LogType.LEGACY_AUTH]))

        print(f"Loaded {len(signin_entries)} sign-in entries")
        print(f"Loaded {len(legacy_entries)} legacy auth entries")

        # Extract IOCs
        extractor = IOCExtractor()
        iocs = extractor.extract(signin_entries=signin_entries, legacy_entries=legacy_entries)

        summary = extractor.get_summary(iocs)
        print(f"\nIOC Summary:")
        print(f"  Total: {summary['total_iocs']}")
        print(f"  By type: {summary['by_type']}")
        print(f"  Unique IPs: {summary['unique_ips']}")
        print(f"  Unique countries: {summary['unique_countries']}")
        print(f"\n  Top IPs: {summary['top_ips'][:5]}")
        print(f"  Top countries: {summary['top_countries']}")
