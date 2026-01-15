#!/usr/bin/env python3
"""
PMP Query Templates - Pre-built SQL patterns for common PMP queries.

Sprint: SPRINT-PMP-INTEL-001
Phase: P3 - Query Templates

Provides:
- Named query templates with descriptions
- Parameter documentation
- Example usage for each template
- Direct execution via PMPIntelligenceService integration

Author: Data Analyst Agent
Date: 2026-01-15
Version: 1.0
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QueryTemplate:
    """Definition of a reusable query template."""
    name: str
    description: str
    parameters: List[str]
    example: str
    database: str  # Preferred database
    sql: str


# =============================================================================
# QUERY TEMPLATE REGISTRY
# =============================================================================

TEMPLATES: Dict[str, QueryTemplate] = {

    # -------------------------------------------------------------------------
    # SYSTEM QUERIES
    # -------------------------------------------------------------------------

    "org_systems": QueryTemplate(
        name="org_systems",
        description="Get all systems for an organization/branch with health status",
        parameters=["org_pattern"],
        example='pmp.get_systems_by_organization("GS1%")',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.resource_name') as name,
                json_extract(raw_data, '$.os_name') as os,
                json_extract(raw_data, '$.resource_health_status') as health_status,
                json_extract(raw_data, '$.branch_office_name') as organization,
                json_extract(raw_data, '$.ip_address') as ip_address,
                json_extract(raw_data, '$.computer_live_status') as online_status
            FROM all_systems
            WHERE json_extract(raw_data, '$.resource_name') LIKE :org_pattern
               OR json_extract(raw_data, '$.branch_office_name') LIKE :org_pattern
            ORDER BY json_extract(raw_data, '$.resource_name')
        """
    ),

    "windows_servers": QueryTemplate(
        name="windows_servers",
        description="Get all Windows Server systems (2016, 2019, 2022)",
        parameters=["org_pattern"],
        example='pmp.query_raw(TEMPLATES["windows_servers"].sql, params={"org_pattern": "GS1%"})',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.resource_name') as name,
                json_extract(raw_data, '$.os_name') as os,
                json_extract(raw_data, '$.resource_health_status') as health_status,
                json_extract(raw_data, '$.last_scan_time') as last_scan
            FROM all_systems
            WHERE json_extract(raw_data, '$.os_name') LIKE '%Windows Server%'
              AND (json_extract(raw_data, '$.resource_name') LIKE :org_pattern
                   OR json_extract(raw_data, '$.branch_office_name') LIKE :org_pattern)
            ORDER BY json_extract(raw_data, '$.resource_health_status') DESC
        """
    ),

    "vulnerable_systems": QueryTemplate(
        name="vulnerable_systems",
        description="Get highly vulnerable systems (health_status = 3)",
        parameters=["severity_threshold"],
        example='pmp.get_vulnerable_systems(severity=3)',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.resource_name') as name,
                json_extract(raw_data, '$.os_name') as os,
                json_extract(raw_data, '$.branch_office_name') as organization,
                json_extract(raw_data, '$.resource_health_status') as health_status
            FROM all_systems
            WHERE CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) >= :severity_threshold
            ORDER BY json_extract(raw_data, '$.branch_office_name'),
                     json_extract(raw_data, '$.resource_name')
        """
    ),

    "stale_systems": QueryTemplate(
        name="stale_systems",
        description="Get systems not scanned in last N days",
        parameters=["days_threshold"],
        example='pmp.query_raw(TEMPLATES["stale_systems"].sql, params={"days_threshold": 7})',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.resource_name') as name,
                json_extract(raw_data, '$.os_name') as os,
                json_extract(raw_data, '$.last_scan_time') as last_scan,
                json_extract(raw_data, '$.agent_last_contact_time') as last_contact
            FROM all_systems
            WHERE json_extract(raw_data, '$.last_scan_time') <
                  (strftime('%s', 'now') * 1000 - :days_threshold * 24 * 60 * 60 * 1000)
            ORDER BY json_extract(raw_data, '$.last_scan_time')
        """
    ),

    # -------------------------------------------------------------------------
    # PATCH QUERIES
    # -------------------------------------------------------------------------

    "failed_patches": QueryTemplate(
        name="failed_patches",
        description="Get patches with deployment failures, sorted by failure count",
        parameters=[],
        example='pmp.get_failed_patches()',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.patch_name') as patch_name,
                json_extract(raw_data, '$.bulletin_id') as bulletin_id,
                CAST(json_extract(raw_data, '$.failed') AS INTEGER) as failed_count,
                CAST(json_extract(raw_data, '$.missing') AS INTEGER) as missing_count,
                ROUND(
                    CAST(json_extract(raw_data, '$.failed') AS REAL) /
                    NULLIF(CAST(json_extract(raw_data, '$.missing') AS REAL) +
                           CAST(json_extract(raw_data, '$.failed') AS REAL), 0) * 100,
                    1
                ) as failure_rate_pct
            FROM missing_patches
            WHERE CAST(json_extract(raw_data, '$.failed') AS INTEGER) > 0
            ORDER BY failed_count DESC
        """
    ),

    "failed_patches_windows": QueryTemplate(
        name="failed_patches_windows",
        description="Windows Server patches with deployment failures",
        parameters=["os_version"],
        example='pmp.get_failed_patches(os_filter="Windows Server 2019%")',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.patch_name') as patch_name,
                json_extract(raw_data, '$.bulletin_id') as bulletin_id,
                CAST(json_extract(raw_data, '$.failed') AS INTEGER) as failed_count,
                CAST(json_extract(raw_data, '$.missing') AS INTEGER) as missing_count
            FROM missing_patches
            WHERE CAST(json_extract(raw_data, '$.failed') AS INTEGER) > 0
              AND (json_extract(raw_data, '$.patch_name') LIKE :os_version
                   OR json_extract(raw_data, '$.patch_name') LIKE '%-2016.%'
                   OR json_extract(raw_data, '$.patch_name') LIKE '%-2019.%'
                   OR json_extract(raw_data, '$.patch_name') LIKE '%-2022.%')
            ORDER BY failed_count DESC
        """
    ),

    "critical_patches_missing": QueryTemplate(
        name="critical_patches_missing",
        description="Critical severity patches not yet deployed",
        parameters=["org_pattern"],
        example='pmp.query_raw(TEMPLATES["critical_patches_missing"].sql)',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.patch_name') as patch_name,
                json_extract(raw_data, '$.bulletin_id') as bulletin_id,
                CAST(json_extract(raw_data, '$.missing') AS INTEGER) as systems_missing,
                json_extract(raw_data, '$.severity') as severity
            FROM missing_patches
            WHERE json_extract(raw_data, '$.severity') = 'Critical'
            ORDER BY systems_missing DESC
        """
    ),

    # -------------------------------------------------------------------------
    # DEPLOYMENT STATUS QUERIES
    # -------------------------------------------------------------------------

    "deployment_failures_by_system": QueryTemplate(
        name="deployment_failures_by_system",
        description="Get deployment failures grouped by system (patch_status != installed)",
        parameters=["org_pattern"],
        example='pmp.query_raw(TEMPLATES["deployment_failures_by_system"].sql)',
        database="pmp_systemreports.db",
        sql="""
            SELECT
                s.computer_name as system_name,
                s.os_name,
                COUNT(*) as failed_patches,
                GROUP_CONCAT(sr.patch_name, ', ') as patches
            FROM system_reports sr
            JOIN systems s ON sr.resource_id = s.resource_id
            WHERE sr.patch_deployed = 0
              AND s.computer_name LIKE :org_pattern
            GROUP BY s.computer_name
            ORDER BY failed_patches DESC
        """
    ),

    "reboot_pending_systems": QueryTemplate(
        name="reboot_pending_systems",
        description="Systems with patches waiting for reboot",
        parameters=[],
        example='pmp.query_raw(TEMPLATES["reboot_pending_systems"].sql)',
        database="pmp_systemreports.db",
        sql="""
            SELECT
                s.computer_name as system_name,
                s.os_name,
                COUNT(*) as pending_patches
            FROM system_reports sr
            JOIN systems s ON sr.resource_id = s.resource_id
            WHERE sr.is_reboot_required = 1
            GROUP BY s.computer_name
            ORDER BY pending_patches DESC
        """
    ),

    # -------------------------------------------------------------------------
    # COMPLIANCE / SUMMARY QUERIES
    # -------------------------------------------------------------------------

    "org_health_summary": QueryTemplate(
        name="org_health_summary",
        description="Health summary by organization/branch",
        parameters=[],
        example='pmp.query_raw(TEMPLATES["org_health_summary"].sql)',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.branch_office_name') as organization,
                COUNT(*) as total_systems,
                SUM(CASE WHEN CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) = 1 THEN 1 ELSE 0 END) as healthy,
                SUM(CASE WHEN CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) = 2 THEN 1 ELSE 0 END) as moderate,
                SUM(CASE WHEN CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) = 3 THEN 1 ELSE 0 END) as critical,
                ROUND(
                    SUM(CASE WHEN CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                    1
                ) as healthy_pct
            FROM all_systems
            GROUP BY json_extract(raw_data, '$.branch_office_name')
            ORDER BY critical DESC, healthy_pct ASC
        """
    ),

    "os_distribution": QueryTemplate(
        name="os_distribution",
        description="System count by operating system",
        parameters=["org_pattern"],
        example='pmp.query_raw(TEMPLATES["os_distribution"].sql)',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.os_name') as os_name,
                COUNT(*) as system_count,
                SUM(CASE WHEN CAST(json_extract(raw_data, '$.resource_health_status') AS INTEGER) = 3 THEN 1 ELSE 0 END) as vulnerable_count
            FROM all_systems
            WHERE json_extract(raw_data, '$.branch_office_name') LIKE :org_pattern
               OR json_extract(raw_data, '$.resource_name') LIKE :org_pattern
            GROUP BY json_extract(raw_data, '$.os_name')
            ORDER BY system_count DESC
        """
    ),

    "never_patched_systems": QueryTemplate(
        name="never_patched_systems",
        description="Systems that have never been patched (last_patched_time = 0)",
        parameters=["org_pattern"],
        example='pmp.query_raw(TEMPLATES["never_patched_systems"].sql)',
        database="pmp_config.db",
        sql="""
            SELECT
                json_extract(raw_data, '$.resource_name') as name,
                json_extract(raw_data, '$.os_name') as os,
                json_extract(raw_data, '$.branch_office_name') as organization,
                json_extract(raw_data, '$.resource_health_status') as health_status
            FROM all_systems
            WHERE (json_extract(raw_data, '$.last_patched_time') = 0
                   OR json_extract(raw_data, '$.last_patched_time') IS NULL)
              AND (json_extract(raw_data, '$.resource_name') LIKE :org_pattern
                   OR json_extract(raw_data, '$.branch_office_name') LIKE :org_pattern)
            ORDER BY json_extract(raw_data, '$.resource_health_status') DESC
        """
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_template(name: str) -> Optional[QueryTemplate]:
    """Get a query template by name."""
    return TEMPLATES.get(name)


def list_templates() -> List[str]:
    """List all available template names."""
    return list(TEMPLATES.keys())


def describe_templates() -> str:
    """Get human-readable description of all templates."""
    lines = ["Available PMP Query Templates:", "=" * 50, ""]

    for name, template in TEMPLATES.items():
        lines.append(f"**{name}**")
        lines.append(f"  Description: {template.description}")
        lines.append(f"  Parameters: {', '.join(template.parameters) or 'None'}")
        lines.append(f"  Example: {template.example}")
        lines.append(f"  Database: {template.database}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    print(describe_templates())
