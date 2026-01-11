#!/usr/bin/env python3
"""
Tests for Phase 264 Timeline Builder Multi-Schema Support
Tests sign-in type filtering, service principal events, and Phase 264 field support.

Created: 2026-01-11
Phase: 264 Sprint 3.2
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import SignInLogEntry
from claude.tools.m365_ir.timeline_builder import (
    TimelineEvent,
    EventPhase,
    build_timeline,
    filter_timeline_by_signin_type,
    filter_timeline_by_schema_variant,
    create_service_principal_event,
)


def create_graph_signin_entry(
    user: str = "user@example.com",
    country: str = "AU",
    dt: datetime = None,
    sign_in_type: str = "interactive",
    is_service_principal: int = 0,
    service_principal_name: str = None,
    latency_ms: int = None,
    device_compliant: int = None,
    mfa_result: str = None,
    schema_variant: str = "graph_interactive",
) -> SignInLogEntry:
    """Helper to create Graph API sign-in entries with Phase 264 fields."""
    if dt is None:
        dt = datetime.now()

    return SignInLogEntry(
        created_datetime=dt,
        user_principal_name=user if not is_service_principal else "",
        user_display_name=user.split("@")[0] if not is_service_principal else "",
        app_display_name="Test App",
        ip_address="1.1.1.1",
        city="Sydney",
        country=country,
        device="",
        browser="Chrome",
        os="Windows",
        status_raw="Success" if not is_service_principal else "0",
        status_normalized="success",
        risk_state="none",
        risk_level_during_signin="none",
        risk_level_aggregated="none",
        conditional_access_status="success",
        # Phase 264 fields
        sign_in_type=sign_in_type,
        is_service_principal=is_service_principal,
        service_principal_name=service_principal_name,
        latency_ms=latency_ms,
        device_compliant=device_compliant,
        mfa_result=mfa_result,
        schema_variant=schema_variant,
    )


class TestSignInTypeFiltering:
    """Tests for Feature 3.2.1: Sign-In Type Filtering."""

    def test_filter_interactive_signins(self):
        """Should filter timeline to only interactive sign-ins."""
        entries = [
            create_graph_signin_entry(user="interactive@example.com", sign_in_type="interactive"),
            create_graph_signin_entry(user="noninteractive@example.com", sign_in_type="noninteractive"),
            create_graph_signin_entry(
                user="",
                sign_in_type="service_principal",
                is_service_principal=1,
                service_principal_name="DevOps Agent",
            ),
        ]

        timeline = build_timeline(signin_entries=entries)
        filtered = filter_timeline_by_signin_type(timeline, "interactive")

        assert len(filtered) == 1
        assert all(e.evidence.get("sign_in_type") == "interactive" for e in filtered)

    def test_filter_noninteractive_signins(self):
        """Should filter timeline to only noninteractive sign-ins."""
        entries = [
            create_graph_signin_entry(user="interactive@example.com", sign_in_type="interactive"),
            create_graph_signin_entry(user="noninteractive@example.com", sign_in_type="noninteractive"),
        ]

        timeline = build_timeline(signin_entries=entries)
        filtered = filter_timeline_by_signin_type(timeline, "noninteractive")

        assert len(filtered) == 1
        assert all(e.evidence.get("sign_in_type") == "noninteractive" for e in filtered)

    def test_filter_service_principal_signins(self):
        """Should filter timeline to only service principal sign-ins."""
        entries = [
            create_graph_signin_entry(user="user@example.com", sign_in_type="interactive"),
            create_graph_signin_entry(
                user="",
                sign_in_type="service_principal",
                is_service_principal=1,
                service_principal_name="DevOps Agent",
            ),
        ]

        timeline = build_timeline(signin_entries=entries)
        filtered = filter_timeline_by_signin_type(timeline, "service_principal")

        assert len(filtered) == 1
        assert all(e.evidence.get("is_service_principal") == 1 for e in filtered)


class TestServicePrincipalEvents:
    """Tests for Feature 3.2.2: Service Principal Event Types."""

    def test_create_service_principal_event(self):
        """Should create timeline event for service principal auth."""
        entry = create_graph_signin_entry(
            user="",
            sign_in_type="service_principal",
            is_service_principal=1,
            service_principal_name="Azure DevOps",
            schema_variant="graph_application",
        )

        event = create_service_principal_event(entry)

        assert "Service Principal" in event.action
        assert event.user == "Azure DevOps"
        assert event.evidence["is_service_principal"] == True
        assert event.source_type == "service_principal"

    def test_service_principal_in_timeline(self):
        """Should include service principal events in timeline build."""
        entries = [
            create_graph_signin_entry(
                user="",
                sign_in_type="service_principal",
                is_service_principal=1,
                service_principal_name="Automation Account",
            ),
        ]

        timeline = build_timeline(signin_entries=entries)

        assert len(timeline) == 1
        assert timeline[0].evidence.get("is_service_principal") == 1


class TestLatencyEventDetails:
    """Tests for Feature 3.2.3: Latency in Event Details."""

    def test_include_latency_in_event_details(self):
        """Should include latency in event evidence."""
        entry = create_graph_signin_entry(user="user@example.com", latency_ms=250)

        timeline = build_timeline(signin_entries=[entry])

        assert len(timeline) == 1
        assert timeline[0].evidence.get("latency_ms") == 250

    def test_slow_signin_warning_severity(self):
        """Should set WARNING severity for slow sign-ins."""
        entry = create_graph_signin_entry(user="user@example.com", latency_ms=1500)

        timeline = build_timeline(signin_entries=[entry])

        assert timeline[0].severity == "WARNING"

    def test_very_slow_signin_alert_severity(self):
        """Should set ALERT severity for very slow sign-ins."""
        entry = create_graph_signin_entry(user="user@example.com", latency_ms=6000)

        timeline = build_timeline(signin_entries=[entry])

        assert timeline[0].severity == "ALERT"


class TestDeviceComplianceEventDetails:
    """Tests for Feature 3.2.4: Device Compliance in Event Details."""

    def test_include_device_compliance_in_event(self):
        """Should include device compliance in event evidence."""
        entry = create_graph_signin_entry(user="user@example.com", device_compliant=1)

        timeline = build_timeline(signin_entries=[entry])

        assert timeline[0].evidence.get("device_compliant") == 1

    def test_noncompliant_device_warning(self):
        """Should set WARNING severity for non-compliant device sign-ins."""
        entry = create_graph_signin_entry(user="user@example.com", device_compliant=0)

        timeline = build_timeline(signin_entries=[entry])

        assert timeline[0].severity in ["WARNING", "ALERT"]


class TestSchemaVariantFiltering:
    """Tests for Feature 3.2.5: Schema Variant Filtering."""

    def test_filter_by_graph_interactive_schema(self):
        """Should filter timeline by graph_interactive schema."""
        entries = [
            create_graph_signin_entry(user="graph@example.com", schema_variant="graph_interactive"),
            create_graph_signin_entry(user="legacy@example.com", schema_variant="legacy_portal"),
        ]

        timeline = build_timeline(signin_entries=entries)
        filtered = filter_timeline_by_schema_variant(timeline, "graph_interactive")

        assert len(filtered) == 1
        assert all(e.evidence.get("schema_variant") == "graph_interactive" for e in filtered)

    def test_filter_by_legacy_portal_schema(self):
        """Should filter timeline by legacy_portal schema."""
        entries = [
            create_graph_signin_entry(user="graph@example.com", schema_variant="graph_interactive"),
            create_graph_signin_entry(user="legacy@example.com", schema_variant="legacy_portal"),
        ]

        timeline = build_timeline(signin_entries=entries)
        filtered = filter_timeline_by_schema_variant(timeline, "legacy_portal")

        assert len(filtered) == 1
        assert all(e.evidence.get("schema_variant") == "legacy_portal" for e in filtered)

    def test_filter_by_graph_application_schema(self):
        """Should filter timeline by graph_application (service principal) schema."""
        entries = [
            create_graph_signin_entry(user="user@example.com", schema_variant="graph_interactive"),
            create_graph_signin_entry(
                user="",
                is_service_principal=1,
                service_principal_name="DevOps",
                schema_variant="graph_application",
            ),
        ]

        timeline = build_timeline(signin_entries=entries)
        filtered = filter_timeline_by_schema_variant(timeline, "graph_application")

        assert len(filtered) == 1
        assert filtered[0].evidence.get("schema_variant") == "graph_application"


class TestMFAEventDetails:
    """Tests for MFA status in event details."""

    def test_include_mfa_result_in_event(self):
        """Should include MFA result in event evidence."""
        entry = create_graph_signin_entry(
            user="user@example.com",
            mfa_result="MFA requirement satisfied by claim in the token",
        )

        timeline = build_timeline(signin_entries=[entry])

        assert "satisfied" in timeline[0].evidence.get("mfa_result", "").lower()
