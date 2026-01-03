#!/usr/bin/env python3
"""
User Baseliner - Statistical analysis of user login patterns

Determines user "home" location from login history to distinguish:
- Legitimate logins (user in home country)
- Legitimate travel (user in known secondary locations)
- Suspicious logins (user in unexpected foreign location)

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import sys

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry


# Countries commonly associated with attacks (high-risk)
HIGH_RISK_COUNTRIES = {"RU", "CN", "KP", "IR", "BY", "VE", "CU", "SY"}


@dataclass
class UserBaseline:
    """User login baseline profile"""
    user_principal_name: str
    primary_country: str
    secondary_countries: List[str]
    confidence: float  # 0-1, how confident we are in the baseline
    total_logins: int
    country_distribution: Dict[str, int]

    # Computed property
    is_suspicious: bool = False

    def __post_init__(self):
        """Calculate if user is suspicious based on patterns"""
        # Suspicious if: low confidence, or never logged in from expected country
        if self.confidence < 0.5:
            self.is_suspicious = True
        elif self.primary_country == "UNKNOWN":
            self.is_suspicious = True


def calculate_user_baseline(
    user_principal_name: str,
    entries: List[SignInLogEntry],
    primary_threshold: float = 0.5,
    secondary_threshold: float = 0.05,
) -> UserBaseline:
    """
    Calculate user baseline from login history.

    Args:
        user_principal_name: User email
        entries: List of sign-in entries for this user
        primary_threshold: Minimum percentage for primary country confidence
        secondary_threshold: Minimum percentage to be considered secondary country

    Returns:
        UserBaseline with primary country, secondary countries, and confidence
    """
    if not entries:
        return UserBaseline(
            user_principal_name=user_principal_name,
            primary_country="UNKNOWN",
            secondary_countries=[],
            confidence=0.0,
            total_logins=0,
            country_distribution={},
            is_suspicious=True,
        )

    # Count logins by country
    country_counts = Counter(
        e.country for e in entries
        if e.user_principal_name == user_principal_name and e.country
    )

    if not country_counts:
        return UserBaseline(
            user_principal_name=user_principal_name,
            primary_country="UNKNOWN",
            secondary_countries=[],
            confidence=0.0,
            total_logins=len(entries),
            country_distribution={},
            is_suspicious=True,
        )

    total = sum(country_counts.values())

    # Find primary country (most common)
    primary_country, primary_count = country_counts.most_common(1)[0]
    confidence = primary_count / total

    # Find secondary countries (above threshold, excluding primary)
    secondary_countries = [
        country for country, count in country_counts.items()
        if country != primary_country and (count / total) >= secondary_threshold
    ]

    # Mark as suspicious if confidence is at or below threshold (no clear majority)
    is_suspicious = confidence <= primary_threshold

    return UserBaseline(
        user_principal_name=user_principal_name,
        primary_country=primary_country,
        secondary_countries=secondary_countries,
        confidence=confidence,
        total_logins=total,
        country_distribution=dict(country_counts),
        is_suspicious=is_suspicious,
    )


def is_foreign_login(
    entry: SignInLogEntry,
    baseline: UserBaseline,
    strict_high_risk: bool = True,
) -> bool:
    """
    Determine if a login is foreign (anomalous) compared to baseline.

    Args:
        entry: Sign-in log entry to check
        baseline: User's baseline profile
        strict_high_risk: Always flag high-risk countries even if in secondary

    Returns:
        True if login is foreign/anomalous
    """
    if not entry.country:
        return False

    country = entry.country

    # Check if from primary country
    if country == baseline.primary_country:
        return False

    # Check if from known secondary country (travel)
    if country in baseline.secondary_countries:
        # Unless it's a high-risk country and strict mode is on
        if strict_high_risk and country in HIGH_RISK_COUNTRIES:
            return True
        return False

    # Not in baseline → foreign
    return True


class UserBaseliner:
    """
    Bulk user baseline calculator and anomaly detector.

    Usage:
        baseliner = UserBaseliner()
        baselines = baseliner.calculate_all_baselines(signin_entries)
        anomalies = baseliner.find_anomalous_logins(signin_entries, baselines)
    """

    def __init__(
        self,
        primary_threshold: float = 0.5,
        secondary_threshold: float = 0.05,
    ):
        """
        Initialize baseliner.

        Args:
            primary_threshold: Minimum percentage for confident primary country
            secondary_threshold: Minimum percentage to be secondary country
        """
        self.primary_threshold = primary_threshold
        self.secondary_threshold = secondary_threshold

    def calculate_all_baselines(
        self,
        entries: List[SignInLogEntry],
    ) -> Dict[str, UserBaseline]:
        """
        Calculate baselines for all users in the entries.

        Args:
            entries: List of all sign-in entries

        Returns:
            Dict mapping user email to UserBaseline
        """
        # Group entries by user
        users: Dict[str, List[SignInLogEntry]] = defaultdict(list)
        for entry in entries:
            users[entry.user_principal_name].append(entry)

        # Calculate baseline for each user
        baselines = {}
        for user, user_entries in users.items():
            baselines[user] = calculate_user_baseline(
                user,
                user_entries,
                self.primary_threshold,
                self.secondary_threshold,
            )

        return baselines

    def find_anomalous_logins(
        self,
        entries: List[SignInLogEntry],
        baselines: Dict[str, UserBaseline],
    ) -> List[SignInLogEntry]:
        """
        Find all anomalous/foreign logins across all users.

        Args:
            entries: List of all sign-in entries
            baselines: Calculated baselines for all users

        Returns:
            List of anomalous sign-in entries
        """
        anomalies = []

        for entry in entries:
            user = entry.user_principal_name
            if user not in baselines:
                continue

            baseline = baselines[user]
            if is_foreign_login(entry, baseline):
                entry.is_foreign = True
                anomalies.append(entry)

        return anomalies

    def get_summary(
        self,
        baselines: Dict[str, UserBaseline],
    ) -> Dict[str, Any]:
        """
        Get summary statistics from baselines.

        Args:
            baselines: Calculated baselines

        Returns:
            Summary dict with counts and lists
        """
        au_users = [u for u, b in baselines.items() if b.primary_country == "AU"]
        us_users = [u for u, b in baselines.items() if b.primary_country == "US"]
        other_users = [
            u for u, b in baselines.items()
            if b.primary_country not in ["AU", "US", "UNKNOWN"]
        ]
        suspicious = [u for u, b in baselines.items() if b.is_suspicious]

        return {
            "total_users": len(baselines),
            "au_based": len(au_users),
            "us_based": len(us_users),
            "other_based": len(other_users),
            "suspicious": len(suspicious),
            "au_users": au_users,
            "us_users": us_users,
            "suspicious_users": suspicious,
        }


if __name__ == "__main__":
    # Quick test with Oculus data
    import sys
    from claude.tools.m365_ir.m365_log_parser import M365LogParser, LogType

    if len(sys.argv) > 1:
        export_paths = [Path(p) for p in sys.argv[1:]]
        parser = M365LogParser.from_export(export_paths[0])

        # Merge all exports
        entries = parser.merge_exports(export_paths, LogType.SIGNIN)
        print(f"Loaded {len(entries)} sign-in entries")

        # Calculate baselines
        baseliner = UserBaseliner()
        baselines = baseliner.calculate_all_baselines(entries)

        # Get summary
        summary = baseliner.get_summary(baselines)
        print(f"\nUser Summary:")
        print(f"  Total users: {summary['total_users']}")
        print(f"  AU-based: {summary['au_based']}")
        print(f"  US-based: {summary['us_based']}")
        print(f"  Other: {summary['other_based']}")
        print(f"  Suspicious: {summary['suspicious']}")

        # Show US users (potential false positives)
        if summary['us_users']:
            print(f"\nUS-based users (potential false positives):")
            for user in summary['us_users']:
                b = baselines[user]
                print(f"  {user}: {b.confidence:.0%} US, {b.total_logins} logins")

        # Show suspicious users
        if summary['suspicious_users']:
            print(f"\nSuspicious users (no clear home country):")
            for user in summary['suspicious_users']:
                b = baselines[user]
                print(f"  {user}: {b.primary_country} ({b.confidence:.0%}), {b.total_logins} logins")

        # Find anomalies
        anomalies = baseliner.find_anomalous_logins(entries, baselines)
        print(f"\nAnomalous logins: {len(anomalies)}")

        # Group by user
        from collections import Counter
        anomaly_users = Counter(a.user_principal_name for a in anomalies)
        print(f"Users with anomalies: {len(anomaly_users)}")
        for user, count in anomaly_users.most_common(10):
            b = baselines[user]
            print(f"  {user}: {count} anomalies (baseline: {b.primary_country})")
