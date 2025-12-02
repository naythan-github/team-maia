#!/usr/bin/env python3
"""
PMP Failure Analysis - Excel Export
Generates comprehensive failure rate and patch compliance analysis
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Database paths
CONFIG_DB = Path.home() / ".maia/databases/intelligence/pmp_config.db"
SYSTEMREPORTS_DB = Path.home() / ".maia/databases/intelligence/pmp_systemreports.db"
OUTPUT_DIR = Path.home() / "work_projects/pmp_reports"
OUTPUT_FILE = OUTPUT_DIR / f"pmp_failure_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_status_code_reference():
    """Sheet 1: Status Code Reference"""
    data = {
        'Category': [
            'Approval Status', 'Approval Status', 'Approval Status',
            'Installation Status', 'Installation Status', 'Installation Status',
            'Deployment Status', 'Deployment Status', 'Deployment Status', 'Deployment Status',
            'Download Status', 'Download Status',
            'Severity', 'Severity', 'Severity', 'Severity', 'Severity'
        ],
        'Code': [
            0, 211, 212,
            201, 202, 206,
            209, 206, 207, 245,
            221, '--',
            0, 1, 2, 3, 4
        ],
        'Status': [
            'Not Approved', 'Approved', 'Declined',
            'Installed', 'Missing', 'Failed to Install',
            'Installed', 'Failed', 'Reboot Pending', 'Delayed',
            'Downloaded', 'Yet to Download',
            'Unrated', 'Low', 'Moderate', 'Important', 'Critical'
        ],
        'Description': [
            'Patch pending approval', 'Patch approved for deployment', 'Patch rejected/declined',
            'Patch successfully installed', 'Patch not installed on system', 'Installation attempt failed',
            'Successfully deployed and installed', 'Deployment failed', 'Installed, awaiting reboot', 'Deployment delayed',
            'Patch file downloaded to server', 'Not downloaded yet',
            'No severity assigned', 'Minor issues', 'Moderate security issues', 'Significant security issues', 'Critical security vulnerabilities'
        ]
    }
    return pd.DataFrame(data)

def get_installation_failures():
    """Sheet 2: Installation Failures (Status 206)"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)
    query = """
    SELECT
        sr.resource_id,
        json_extract(sr.raw_data, '$.resource_id_string') as system_id,
        sr.patch_name,
        sr.bulletin_id,
        sr.severity,
        CASE sr.severity
            WHEN 4 THEN 'Critical'
            WHEN 3 THEN 'Important'
            WHEN 2 THEN 'Moderate'
            WHEN 1 THEN 'Low'
            ELSE 'Unrated'
        END as severity_label,
        json_extract(sr.raw_data, '$.install_error_code') as error_code,
        json_extract(sr.raw_data, '$.deploy_remarks') as failure_reason,
        datetime(json_extract(sr.raw_data, '$.patch_released_time')/1000, 'unixepoch') as release_date
    FROM system_reports sr
    WHERE json_extract(sr.raw_data, '$.deployment_status') = 206
    ORDER BY sr.severity DESC, sr.patch_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_reboot_pending():
    """Sheet 3: Patches Awaiting Reboot (Status 207)"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)
    query = """
    SELECT
        sr.resource_id,
        json_extract(sr.raw_data, '$.resource_id_string') as system_id,
        sr.patch_name,
        sr.bulletin_id,
        sr.severity,
        CASE sr.severity
            WHEN 4 THEN 'Critical'
            WHEN 3 THEN 'Important'
            WHEN 2 THEN 'Moderate'
            WHEN 1 THEN 'Low'
            ELSE 'Unrated'
        END as severity_label,
        datetime(json_extract(sr.raw_data, '$.installed_time')/1000, 'unixepoch') as installed_date,
        CAST((julianday('now') - julianday(datetime(json_extract(sr.raw_data, '$.installed_time')/1000, 'unixepoch'))) AS INTEGER) as days_pending
    FROM system_reports sr
    WHERE json_extract(sr.raw_data, '$.deployment_status') = 207
    ORDER BY days_pending DESC, sr.severity DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_critical_missing_patches():
    """Sheet 4: Critical Missing Patches"""
    conn = sqlite3.connect(CONFIG_DB)
    query = """
    SELECT
        json_extract(mp.raw_data, '$.resource_id') as resource_id,
        mp.patch_id,
        mp.bulletin_id,
        json_extract(mp.raw_data, '$.severity') as severity,
        CASE json_extract(mp.raw_data, '$.severity')
            WHEN 4 THEN 'Critical'
            WHEN 3 THEN 'Important'
            WHEN 2 THEN 'Moderate'
            WHEN 1 THEN 'Low'
            ELSE 'Unrated'
        END as severity_label,
        datetime(mp.patch_released_time/1000, 'unixepoch') as release_date,
        CAST((julianday('now') - julianday(datetime(mp.patch_released_time/1000, 'unixepoch'))) AS INTEGER) as days_unpatched
    FROM missing_patches mp
    WHERE json_extract(mp.raw_data, '$.severity') IN (3, 4)
    ORDER BY severity DESC, days_unpatched DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_patch_compliance_summary():
    """Sheet 5: Overall Patch Compliance"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)
    query = """
    SELECT
        'Total Patches' as metric,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM system_reports), 2) as percentage
    FROM system_reports
    UNION ALL
    SELECT
        'Installed (209)',
        COUNT(*),
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM system_reports), 2)
    FROM system_reports
    WHERE json_extract(raw_data, '$.deployment_status') = 209
    UNION ALL
    SELECT
        'Failed (206)',
        COUNT(*),
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM system_reports), 2)
    FROM system_reports
    WHERE json_extract(raw_data, '$.deployment_status') = 206
    UNION ALL
    SELECT
        'Reboot Pending (207)',
        COUNT(*),
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM system_reports), 2)
    FROM system_reports
    WHERE json_extract(raw_data, '$.deployment_status') = 207
    UNION ALL
    SELECT
        'Delayed (245)',
        COUNT(*),
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM system_reports), 2)
    FROM system_reports
    WHERE json_extract(raw_data, '$.deployment_status') = 245
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_failure_rate_by_severity():
    """Sheet 6: Failure Rate by Severity"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)
    query = """
    SELECT
        sr.severity,
        CASE sr.severity
            WHEN 4 THEN 'Critical'
            WHEN 3 THEN 'Important'
            WHEN 2 THEN 'Moderate'
            WHEN 1 THEN 'Low'
            ELSE 'Unrated'
        END as severity_label,
        COUNT(*) as total_patches,
        SUM(CASE WHEN json_extract(sr.raw_data, '$.deployment_status') = 206 THEN 1 ELSE 0 END) as failed_count,
        ROUND(SUM(CASE WHEN json_extract(sr.raw_data, '$.deployment_status') = 206 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate_pct
    FROM system_reports sr
    GROUP BY sr.severity
    ORDER BY sr.severity DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_system_risk_scores():
    """Sheet 7: Systems with High Risk (Most Critical Missing Patches)"""
    # Get critical missing patches per system from config DB
    conn_config = sqlite3.connect(CONFIG_DB)

    query = """
    SELECT
        json_extract(mp.raw_data, '$.resource_id') as resource_id,
        COUNT(*) as critical_missing_count,
        SUM(CASE WHEN json_extract(mp.raw_data, '$.severity') = 4 THEN 1 ELSE 0 END) as critical_severity_4,
        SUM(CASE WHEN json_extract(mp.raw_data, '$.severity') = 3 THEN 1 ELSE 0 END) as important_severity_3
    FROM missing_patches mp
    WHERE json_extract(mp.raw_data, '$.severity') IN (3, 4)
    GROUP BY resource_id
    HAVING critical_missing_count > 0
    ORDER BY critical_severity_4 DESC, important_severity_3 DESC
    LIMIT 50
    """
    df = pd.read_sql_query(query, conn_config)
    conn_config.close()

    # Calculate risk score: Critical=10 points, Important=3 points
    df['risk_score'] = (df['critical_severity_4'] * 10) + (df['important_severity_3'] * 3)
    df = df.sort_values('risk_score', ascending=False)

    return df

def main():
    print("🔍 PMP Failure Analysis - Excel Export")
    print("=" * 80)
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Create Excel writer
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:

        print("📋 Sheet 1: Status Code Reference...")
        df1 = create_status_code_reference()
        df1.to_excel(writer, sheet_name='Status Codes', index=False)

        print("📋 Sheet 2: Installation Failures...")
        df2 = get_installation_failures()
        df2.to_excel(writer, sheet_name='Installation Failures', index=False)
        print(f"   ❌ Found {len(df2)} failed installations")

        print("📋 Sheet 3: Reboot Pending...")
        df3 = get_reboot_pending()
        df3.to_excel(writer, sheet_name='Reboot Pending', index=False)
        print(f"   ⏳ Found {len(df3)} patches awaiting reboot")

        print("📋 Sheet 4: Critical Missing Patches...")
        df4 = get_critical_missing_patches()
        df4.to_excel(writer, sheet_name='Critical Missing', index=False)
        print(f"   ⚠️  Found {len(df4)} critical/important missing patches")

        print("📋 Sheet 5: Patch Compliance Summary...")
        df5 = get_patch_compliance_summary()
        df5.to_excel(writer, sheet_name='Compliance Summary', index=False)

        print("📋 Sheet 6: Failure Rate by Severity...")
        df6 = get_failure_rate_by_severity()
        df6.to_excel(writer, sheet_name='Failure Rates', index=False)

        print("📋 Sheet 7: System Risk Scores...")
        df7 = get_system_risk_scores()
        df7.to_excel(writer, sheet_name='High Risk Systems', index=False)
        print(f"   🎯 Found {len(df7)} systems with critical missing patches")

    print()
    print("=" * 80)
    print(f"✅ Export complete: {OUTPUT_FILE}")
    print(f"📊 Total sheets: 7")
    print()
    print("Sheet Summary:")
    print("  1. Status Codes - Complete reference of all PMP status codes")
    print("  2. Installation Failures - All failed installations (206)")
    print("  3. Reboot Pending - Patches installed but awaiting reboot (207)")
    print("  4. Critical Missing - High-severity unpatched vulnerabilities")
    print("  5. Compliance Summary - Overall patch deployment statistics")
    print("  6. Failure Rates - Failure rates by patch severity")
    print("  7. High Risk Systems - Systems with most critical missing patches")
    print()

if __name__ == "__main__":
    main()
