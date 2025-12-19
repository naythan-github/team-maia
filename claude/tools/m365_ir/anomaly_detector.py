#!/usr/bin/env python3
"""
Anomaly Detector - Detect impossible travel, legacy auth abuse, and suspicious patterns

Features:
- Impossible travel detection (geographic + time analysis)
- Legacy auth abuse (SMTP/IMAP from foreign countries)
- High-risk country login detection
- Credential stuffing pattern detection

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import sys
import math

MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry, LegacyAuthEntry


class AnomalyType(Enum):
    """Types of security anomalies"""
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    LEGACY_AUTH_ABUSE = "legacy_auth_abuse"
    HIGH_RISK_COUNTRY = "high_risk_country"
    CREDENTIAL_STUFFING = "credential_stuffing"
    UNUSUAL_TIME = "unusual_time"
    BULK_ACCESS = "bulk_access"


# High-risk countries commonly associated with attacks
HIGH_RISK_COUNTRIES = {"RU", "CN", "KP", "IR", "BY", "VE", "CU", "SY"}

# Approximate city coordinates for travel calculations (major cities)
CITY_COORDS: Dict[str, Tuple[float, float]] = {
    # Australia
    ("Melbourne", "AU"): (-37.8136, 144.9631),
    ("Sydney", "AU"): (-33.8688, 151.2093),
    ("Brisbane", "AU"): (-27.4698, 153.0251),
    ("Perth", "AU"): (-31.9505, 115.8605),
    # USA
    ("New York", "US"): (40.7128, -74.0060),
    ("Los Angeles", "US"): (34.0522, -118.2437),
    ("Chicago", "US"): (41.8781, -87.6298),
    ("San Francisco", "US"): (37.7749, -122.4194),
    # Europe
    ("London", "GB"): (51.5074, -0.1278),
    ("Paris", "FR"): (48.8566, 2.3522),
    ("Berlin", "DE"): (52.5200, 13.4050),
    ("Moscow", "RU"): (55.7558, 37.6173),
    # Asia
    ("Beijing", "CN"): (39.9042, 116.4074),
    ("Shanghai", "CN"): (31.2304, 121.4737),
    ("Tokyo", "JP"): (35.6762, 139.6503),
    ("Singapore", "SG"): (1.3521, 103.8198),
    # Others
    ("Auckland", "NZ"): (-36.8485, 174.7633),
    ("Shijiazhuang", "CN"): (38.0428, 114.5149),
}

# Country centroids (fallback when city not found)
COUNTRY_COORDS: Dict[str, Tuple[float, float]] = {
    "AU": (-25.2744, 133.7751),
    "US": (37.0902, -95.7129),
    "GB": (55.3781, -3.4360),
    "RU": (61.5240, 105.3188),
    "CN": (35.8617, 104.1954),
    "IN": (20.5937, 78.9629),
    "KR": (35.9078, 127.7669),
    "JP": (36.2048, 138.2529),
    "NZ": (-40.9006, 174.8860),
    "SG": (1.3521, 103.8198),
    "KP": (40.3399, 127.5101),
    "IR": (32.4279, 53.6880),
    "BY": (53.7098, 27.9534),
    "VE": (6.4238, -66.5897),
    "CU": (21.5218, -77.7812),
    "SY": (34.8021, 38.9968),
}

# Maximum travel speed (km/h) - commercial jet ~900 km/h, add buffer
MAX_TRAVEL_SPEED_KMH = 1000


@dataclass
class Anomaly:
    """A detected security anomaly"""
    anomaly_type: AnomalyType
    user_principal_name: str
    timestamp: datetime
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Optional fields for specific anomaly types
    source_location: Optional[str] = None
    dest_location: Optional[str] = None
    time_delta: Optional[timedelta] = None
    distance_km: Optional[float] = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points on Earth in km."""
    R = 6371  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def calculate_travel_distance(
    city1: str, country1: str,
    city2: str, country2: str
) -> float:
    """
    Calculate approximate travel distance between two locations.

    Args:
        city1, country1: Source location
        city2, country2: Destination location

    Returns:
        Distance in kilometers
    """
    # Try city-level coordinates first
    coords1 = CITY_COORDS.get((city1, country1))
    coords2 = CITY_COORDS.get((city2, country2))

    # Fall back to country centroids
    if not coords1:
        coords1 = COUNTRY_COORDS.get(country1, (0, 0))
    if not coords2:
        coords2 = COUNTRY_COORDS.get(country2, (0, 0))

    return haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])


def detect_impossible_travel(
    entries: List[SignInLogEntry],
    max_speed_kmh: float = MAX_TRAVEL_SPEED_KMH,
) -> List[Anomaly]:
    """
    Detect impossible travel - logins from distant locations in short time.

    Args:
        entries: List of sign-in entries
        max_speed_kmh: Maximum plausible travel speed

    Returns:
        List of impossible travel anomalies
    """
    anomalies = []

    # Group by user
    user_entries: Dict[str, List[SignInLogEntry]] = defaultdict(list)
    for entry in entries:
        user_entries[entry.user_principal_name].append(entry)

    for user, user_logins in user_entries.items():
        # Sort by time
        sorted_logins = sorted(user_logins, key=lambda e: e.created_datetime)

        for i in range(1, len(sorted_logins)):
            prev = sorted_logins[i-1]
            curr = sorted_logins[i]

            # Skip if same location
            if prev.country == curr.country and prev.city == curr.city:
                continue

            # Calculate distance and time
            distance = calculate_travel_distance(
                prev.city, prev.country,
                curr.city, curr.country
            )
            time_delta = curr.created_datetime - prev.created_datetime
            hours = time_delta.total_seconds() / 3600

            if hours <= 0:
                continue

            # Calculate required speed
            required_speed = distance / hours

            # Check if impossible (faster than max speed)
            if required_speed > max_speed_kmh and distance > 500:  # Ignore small distances
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.IMPOSSIBLE_TRAVEL,
                    user_principal_name=user,
                    timestamp=curr.created_datetime,
                    description=f"Impossible travel: {prev.city}, {prev.country} to {curr.city}, {curr.country} in {hours:.1f}h ({distance:.0f}km, {required_speed:.0f}km/h required)",
                    severity="HIGH",
                    evidence={
                        "source_entry": prev,
                        "dest_entry": curr,
                        "distance_km": distance,
                        "time_hours": hours,
                        "required_speed_kmh": required_speed,
                    },
                    source_location=f"{prev.city}, {prev.country}",
                    dest_location=f"{curr.city}, {curr.country}",
                    time_delta=time_delta,
                    distance_km=distance,
                ))

    return anomalies


def detect_legacy_auth_abuse(
    entries: List[LegacyAuthEntry],
    home_country: str = "AU",
) -> List[Anomaly]:
    """
    Detect legacy authentication abuse (SMTP/IMAP from foreign countries).

    Args:
        entries: List of legacy auth entries
        home_country: Expected home country for users

    Returns:
        List of legacy auth abuse anomalies
    """
    anomalies = []

    # Group by user for pattern detection
    user_entries: Dict[str, List[LegacyAuthEntry]] = defaultdict(list)

    for entry in entries:
        # Skip if from home country
        if entry.country == home_country:
            continue

        user_entries[entry.user_principal_name].append(entry)

        # Determine severity based on success/failure
        is_success = entry.status_normalized == "success" or entry.status == "0"
        severity = "HIGH" if is_success else "MEDIUM"

        anomalies.append(Anomaly(
            anomaly_type=AnomalyType.LEGACY_AUTH_ABUSE,
            user_principal_name=entry.user_principal_name,
            timestamp=entry.created_datetime,
            description=f"Legacy auth ({entry.client_app_used}) from {entry.country}: {entry.failure_reason or 'Success'}",
            severity=severity,
            evidence={
                "client_app": entry.client_app_used,
                "country": entry.country,
                "status": entry.status,
                "failure_reason": entry.failure_reason,
                "ip_address": entry.ip_address,
            },
        ))

    # Detect credential stuffing patterns (many attempts in short time)
    for user, user_logins in user_entries.items():
        if len(user_logins) >= 5:  # 5+ attempts
            sorted_logins = sorted(user_logins, key=lambda e: e.created_datetime)
            first = sorted_logins[0].created_datetime
            last = sorted_logins[-1].created_datetime
            duration = (last - first).total_seconds() / 60  # minutes

            if duration <= 60 and len(user_logins) >= 5:  # 5+ in an hour
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.CREDENTIAL_STUFFING,
                    user_principal_name=user,
                    timestamp=last,
                    description=f"Credential stuffing: {len(user_logins)} legacy auth attempts in {duration:.0f} minutes",
                    severity="HIGH",
                    evidence={
                        "attempt_count": len(user_logins),
                        "duration_minutes": duration,
                        "countries": list(set(e.country for e in user_logins)),
                    },
                ))

    return anomalies


def detect_high_risk_country_login(
    entries: List[SignInLogEntry],
    high_risk_countries: set = HIGH_RISK_COUNTRIES,
) -> List[Anomaly]:
    """
    Detect logins from high-risk countries.

    Args:
        entries: List of sign-in entries
        high_risk_countries: Set of high-risk country codes

    Returns:
        List of high-risk country anomalies
    """
    anomalies = []

    for entry in entries:
        if entry.country in high_risk_countries:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.HIGH_RISK_COUNTRY,
                user_principal_name=entry.user_principal_name,
                timestamp=entry.created_datetime,
                description=f"Login from high-risk country: {entry.country} ({entry.city})",
                severity="MEDIUM",
                evidence={
                    "country": entry.country,
                    "city": entry.city,
                    "ip_address": entry.ip_address,
                    "app": entry.app_display_name,
                },
            ))

    return anomalies


class AnomalyDetector:
    """
    Comprehensive anomaly detector for M365 security logs.

    Usage:
        detector = AnomalyDetector()
        anomalies = detector.detect_all(signin_entries, legacy_auth_entries)
        summary = detector.get_summary(anomalies)
    """

    def __init__(
        self,
        home_country: str = "AU",
        max_travel_speed_kmh: float = MAX_TRAVEL_SPEED_KMH,
        high_risk_countries: set = HIGH_RISK_COUNTRIES,
    ):
        self.home_country = home_country
        self.max_travel_speed_kmh = max_travel_speed_kmh
        self.high_risk_countries = high_risk_countries

    def detect_all(
        self,
        signin_entries: List[SignInLogEntry] = None,
        legacy_auth_entries: List[LegacyAuthEntry] = None,
    ) -> List[Anomaly]:
        """
        Run all anomaly detection algorithms.

        Args:
            signin_entries: Sign-in log entries
            legacy_auth_entries: Legacy auth log entries

        Returns:
            List of all detected anomalies
        """
        anomalies = []

        if signin_entries:
            anomalies.extend(detect_impossible_travel(
                signin_entries,
                self.max_travel_speed_kmh
            ))
            anomalies.extend(detect_high_risk_country_login(
                signin_entries,
                self.high_risk_countries
            ))

        if legacy_auth_entries:
            anomalies.extend(detect_legacy_auth_abuse(
                legacy_auth_entries,
                self.home_country
            ))

        # Sort by timestamp
        anomalies.sort(key=lambda a: a.timestamp)

        return anomalies

    def get_summary(self, anomalies: List[Anomaly]) -> Dict[str, Any]:
        """
        Get summary statistics from anomalies.

        Args:
            anomalies: List of detected anomalies

        Returns:
            Summary dict
        """
        by_type = Counter(a.anomaly_type.value for a in anomalies)
        by_user = Counter(a.user_principal_name for a in anomalies)
        by_severity = Counter(a.severity for a in anomalies)

        return {
            "total_anomalies": len(anomalies),
            "by_type": dict(by_type),
            "by_user": dict(by_user),
            "by_severity": dict(by_severity),
            "unique_users_affected": len(by_user),
        }


if __name__ == "__main__":
    # Quick test with Oculus data
    import sys
    from claude.tools.m365_ir.m365_log_parser import M365LogParser, LogType

    if len(sys.argv) > 1:
        export_paths = [Path(p) for p in sys.argv[1:]]
        parser = M365LogParser.from_export(export_paths[0])

        # Load all entries
        signin_entries = parser.merge_exports(export_paths, LogType.SIGNIN)
        print(f"Loaded {len(signin_entries)} sign-in entries")

        # Load legacy auth if available
        legacy_entries = []
        for export in export_paths:
            discovered = parser.discover_log_files(export)
            if LogType.LEGACY_AUTH in discovered:
                legacy_entries.extend(parser.parse_legacy_auth(discovered[LogType.LEGACY_AUTH]))
        print(f"Loaded {len(legacy_entries)} legacy auth entries")

        # Detect anomalies
        detector = AnomalyDetector()
        anomalies = detector.detect_all(signin_entries, legacy_entries)

        summary = detector.get_summary(anomalies)
        print(f"\nAnomaly Summary:")
        print(f"  Total: {summary['total_anomalies']}")
        print(f"  By type: {summary['by_type']}")
        print(f"  By severity: {summary['by_severity']}")
        print(f"  Users affected: {summary['unique_users_affected']}")

        # Show top anomalies
        print(f"\nTop 10 anomalies:")
        for a in anomalies[:10]:
            print(f"  [{a.severity}] {a.anomaly_type.value}: {a.user_principal_name}")
            print(f"    {a.description}")
