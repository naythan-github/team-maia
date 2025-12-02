#!/usr/bin/env python3
"""
Export Non-ESU Systems to Excel with Policy Information

Creates comprehensive spreadsheet of systems WITHOUT ESU failures,
including last online, last failure, customer name, and applicable policies.

Created: 2025-12-02
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# Database paths
CONFIG_DB = str(Path.home() / ".maia/databases/intelligence/pmp_config.db")
SYSTEMREPORTS_DB = str(Path.home() / ".maia/databases/intelligence/pmp_systemreports.db")

def get_esu_systems():
    """Get list of systems with ESU failures to exclude"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)
    query = """
        SELECT DISTINCT resource_id
        FROM system_reports
        WHERE json_extract(raw_data, '$.install_error_code') = 18
        AND json_extract(raw_data, '$.deployment_status') = 206
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return set(df['resource_id'].tolist())

def get_non_esu_systems():
    """Get all systems WITHOUT ESU failures"""
    conn_config = sqlite3.connect(CONFIG_DB)

    # Get all systems from SOM computers table (has system details)
    query = """
        SELECT
            resource_id,
            json_extract(raw_data, '$.resource_name') as system_name,
            json_extract(raw_data, '$.domain_name') as domain_name,
            json_extract(raw_data, '$.customer_name') as customer_name,
            json_extract(raw_data, '$.branch_office_name') as branch_office,
            json_extract(raw_data, '$.os_name') as os_name,
            json_extract(raw_data, '$.service_pack') as service_pack,
            json_extract(raw_data, '$.ip_address') as ip_address,
            datetime(json_extract(raw_data, '$.last_contact_time')/1000, 'unixepoch') as last_online
        FROM som_computers
    """
    df_systems = pd.read_sql_query(query, conn_config)
    conn_config.close()

    # Get ESU systems to exclude
    esu_systems = get_esu_systems()

    # Filter out ESU systems
    df_non_esu = df_systems[~df_systems['resource_id'].isin(esu_systems)].copy()

    print(f"Total systems: {len(df_systems)}")
    print(f"ESU systems (excluded): {len(esu_systems)}")
    print(f"Non-ESU systems: {len(df_non_esu)}")

    return df_non_esu

def get_last_failure_date(resource_ids):
    """Get last failure date for each system (excluding ESU failures)"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)

    # Create placeholders for SQL IN clause
    placeholders = ','.join(['?' for _ in resource_ids])

    query = f"""
        SELECT
            resource_id,
            MAX(datetime(json_extract(raw_data, '$.patch_updated_time')/1000, 'unixepoch')) as last_failure_date,
            COUNT(*) as total_failures,
            json_extract(raw_data, '$.install_error_code') as last_error_code,
            json_extract(raw_data, '$.deploy_remarks') as last_error_message
        FROM system_reports
        WHERE json_extract(raw_data, '$.deployment_status') = 206
        AND json_extract(raw_data, '$.install_error_code') != 18
        AND resource_id IN ({placeholders})
        GROUP BY resource_id
    """

    df = pd.read_sql_query(query, conn, params=resource_ids)
    conn.close()
    return df

def get_patch_statistics(resource_ids):
    """Get patch deployment statistics for each system"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)

    placeholders = ','.join(['?' for _ in resource_ids])

    query = f"""
        SELECT
            resource_id,
            COUNT(*) as total_patches,
            SUM(CASE WHEN json_extract(raw_data, '$.deployment_status') = 209 THEN 1 ELSE 0 END) as installed_count,
            SUM(CASE WHEN json_extract(raw_data, '$.deployment_status') = 206 AND json_extract(raw_data, '$.install_error_code') != 18 THEN 1 ELSE 0 END) as failed_count,
            SUM(CASE WHEN json_extract(raw_data, '$.deployment_status') = 207 THEN 1 ELSE 0 END) as reboot_pending_count,
            SUM(CASE WHEN severity = 4 THEN 1 ELSE 0 END) as critical_patches,
            SUM(CASE WHEN severity = 3 THEN 1 ELSE 0 END) as important_patches
        FROM system_reports
        WHERE resource_id IN ({placeholders})
        GROUP BY resource_id
    """

    df = pd.read_sql_query(query, conn, params=resource_ids)
    conn.close()
    return df

def get_applicable_policies():
    """Get policy information from config database"""
    conn = sqlite3.connect(CONFIG_DB)

    # Get deployment policies
    query = """
        SELECT
            policy_id,
            json_extract(raw_data, '$.name') as policy_name,
            json_extract(raw_data, '$.description') as policy_description,
            json_extract(raw_data, '$.is_enabled') as is_enabled
        FROM deployment_policies
    """

    try:
        df_policies = pd.read_sql_query(query, conn)
        print(f"Found {len(df_policies)} policies in database")
    except Exception as e:
        print(f"No deployment_policies table or error: {e}")
        df_policies = pd.DataFrame(columns=['policy_id', 'policy_name', 'policy_description', 'is_enabled'])

    conn.close()
    return df_policies

def determine_recommended_policy(row):
    """Determine recommended policy based on system characteristics"""
    os_name = str(row.get('os_name', '')).lower()
    total_patches = row.get('total_patches', 0)
    critical_patches = row.get('critical_patches', 0)
    failed_count = row.get('failed_count', 0)

    policies = []

    # Critical Security - Express Lane (Policy 1)
    if critical_patches > 0:
        policies.append("Policy 1: Critical Security - Express Lane")

    # Important Security - Standard Track (Policy 2)
    if row.get('important_patches', 0) > 0:
        policies.append("Policy 2: Important Security - Standard Track")

    # Check for GN Audio (Policy 5 - High Risk Quarantine)
    # This would require vendor info from patch data
    if failed_count > 0 and failed_count / max(total_patches, 1) > 0.10:
        policies.append("Policy 5: Manual Review Required (High Failure Rate)")

    # Microsoft Non-Security (Policy 3)
    if "windows" in os_name:
        policies.append("Policy 3: Microsoft Non-Security - Monthly")

    # Third Party (Policy 4)
    policies.append("Policy 4: Third Party - Monthly")

    return " | ".join(policies) if policies else "No Active Policies"

def main():
    print("="*80)
    print("PMP Non-ESU Systems Export")
    print("="*80)
    print()

    # Step 1: Get non-ESU systems
    print("Step 1: Retrieving non-ESU systems...")
    df_systems = get_non_esu_systems()
    print()

    if len(df_systems) == 0:
        print("❌ No non-ESU systems found")
        return 1

    # Step 2: Get failure information
    print("Step 2: Retrieving failure history...")
    resource_ids = df_systems['resource_id'].tolist()
    df_failures = get_last_failure_date(resource_ids)
    print(f"   Found failure data for {len(df_failures)} systems")
    print()

    # Step 3: Get patch statistics
    print("Step 3: Retrieving patch statistics...")
    df_stats = get_patch_statistics(resource_ids)
    print(f"   Retrieved statistics for {len(df_stats)} systems")
    print()

    # Step 4: Get policies
    print("Step 4: Retrieving policy information...")
    df_policies = get_applicable_policies()
    print()

    # Step 5: Merge data
    print("Step 5: Merging data...")
    df_final = df_systems.merge(df_failures, on='resource_id', how='left')
    df_final = df_final.merge(df_stats, on='resource_id', how='left')

    # Step 6: Determine recommended policies
    print("Step 6: Determining applicable policies...")
    df_final['recommended_policies'] = df_final.apply(determine_recommended_policy, axis=1)

    # Step 7: Calculate health score
    df_final['health_score'] = 100 - (
        (df_final['failed_count'].fillna(0) * 2) +
        (df_final['reboot_pending_count'].fillna(0) * 1) +
        (df_final['critical_patches'].fillna(0) * 0.5)
    )
    df_final['health_score'] = df_final['health_score'].clip(0, 100)

    # Step 8: Add status column
    def determine_status(row):
        if pd.isna(row['last_online']):
            return "Unknown"
        elif row.get('failed_count', 0) > 5:
            return "High Risk"
        elif row.get('critical_patches', 0) > 0:
            return "Needs Attention"
        elif row.get('reboot_pending_count', 0) > 0:
            return "Reboot Required"
        else:
            return "Healthy"

    df_final['status'] = df_final.apply(determine_status, axis=1)

    # Step 9: Reorder and clean columns
    columns_order = [
        'resource_id',
        'system_name',
        'customer_name',
        'domain_name',
        'branch_office',
        'os_name',
        'service_pack',
        'ip_address',
        'last_online',
        'last_failure_date',
        'status',
        'health_score',
        'total_patches',
        'installed_count',
        'failed_count',
        'reboot_pending_count',
        'critical_patches',
        'important_patches',
        'recommended_policies'
    ]

    df_export = df_final[columns_order].copy()

    # Fill NaN values
    df_export['customer_name'] = df_export['customer_name'].fillna('Unknown')
    df_export['last_failure_date'] = df_export['last_failure_date'].fillna('No Failures')
    df_export['failed_count'] = df_export['failed_count'].fillna(0).astype(int)
    df_export['reboot_pending_count'] = df_export['reboot_pending_count'].fillna(0).astype(int)

    # Step 10: Export to Excel
    output_file = Path.home() / "work_projects/pmp_reports/PMP_Non_ESU_Systems_Report.xlsx"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Step 7: Exporting to Excel...")
    print(f"   Output: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Main system list
        df_export.to_excel(writer, sheet_name='Non-ESU Systems', index=False)

        # Sheet 2: High risk systems
        df_high_risk = df_export[df_export['status'] == 'High Risk'].copy()
        df_high_risk = df_high_risk.sort_values('failed_count', ascending=False)
        df_high_risk.to_excel(writer, sheet_name='High Risk Systems', index=False)

        # Sheet 3: Summary statistics
        summary_data = {
            'Metric': [
                'Total Non-ESU Systems',
                'Systems with Failures',
                'Systems Needing Reboot',
                'High Risk Systems',
                'Healthy Systems',
                'Average Health Score',
                'Total Critical Patches',
                'Total Important Patches'
            ],
            'Value': [
                len(df_export),
                len(df_export[df_export['failed_count'] > 0]),
                len(df_export[df_export['reboot_pending_count'] > 0]),
                len(df_high_risk),
                len(df_export[df_export['status'] == 'Healthy']),
                f"{df_export['health_score'].mean():.1f}",
                int(df_export['critical_patches'].sum()),
                int(df_export['important_patches'].sum())
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 4: Customer breakdown
        df_customer = df_export.groupby('customer_name').agg({
            'resource_id': 'count',
            'failed_count': 'sum',
            'critical_patches': 'sum',
            'health_score': 'mean'
        }).reset_index()
        df_customer.columns = ['Customer', 'System Count', 'Total Failures', 'Critical Patches', 'Avg Health Score']
        df_customer = df_customer.sort_values('System Count', ascending=False)
        df_customer.to_excel(writer, sheet_name='Customer Breakdown', index=False)

        # Sheet 5: Policy recommendations summary
        policy_counts = df_export['recommended_policies'].value_counts().reset_index()
        policy_counts.columns = ['Policy Combination', 'System Count']
        policy_counts.to_excel(writer, sheet_name='Policy Distribution', index=False)

        # Sheet 6: Available policies (if any)
        if len(df_policies) > 0:
            df_policies.to_excel(writer, sheet_name='Current PMP Policies', index=False)

    print()
    print("="*80)
    print("✅ SUCCESS - Non-ESU Systems Report Exported")
    print("="*80)
    print()
    print(f"Output File: {output_file}")
    print(f"Total Systems: {len(df_export):,}")
    print()
    print("Sheets Created:")
    print("  1. Non-ESU Systems - Complete system list with all details")
    print("  2. High Risk Systems - Systems with >5 failures")
    print("  3. Summary - Key metrics and statistics")
    print("  4. Customer Breakdown - Systems grouped by customer")
    print("  5. Policy Distribution - Recommended policy assignments")
    if len(df_policies) > 0:
        print("  6. Current PMP Policies - Active policies in PMP")
    print()
    print("Key Statistics:")
    print(f"  Total Non-ESU Systems: {len(df_export):,}")
    print(f"  Systems with Failures: {len(df_export[df_export['failed_count'] > 0]):,}")
    print(f"  High Risk Systems: {len(df_high_risk):,}")
    print(f"  Average Health Score: {df_export['health_score'].mean():.1f}/100")
    print()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
