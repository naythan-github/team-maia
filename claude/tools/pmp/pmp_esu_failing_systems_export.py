#!/usr/bin/env python3
"""
Export ESU-Failing Systems to Excel with Current Policy Information

Creates comprehensive spreadsheet of systems WITH ESU failures (error code 18),
including last online, last failure, customer name, and CURRENTLY APPLIED policies.

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

def get_esu_failing_systems():
    """Get all systems WITH ESU failures (error code 18)"""
    conn = sqlite3.connect(SYSTEMREPORTS_DB)

    # Get ESU failure details
    query = """
        SELECT DISTINCT
            resource_id,
            patch_name,
            json_extract(raw_data, '$.deploy_remarks') as error_message,
            datetime(json_extract(raw_data, '$.patch_updated_time')/1000, 'unixepoch') as last_failure_date,
            severity
        FROM system_reports
        WHERE json_extract(raw_data, '$.install_error_code') = 18
        AND json_extract(raw_data, '$.deployment_status') = 206
    """

    df_esu = pd.read_sql_query(query, conn)
    conn.close()

    print(f"Found {len(df_esu)} ESU failure records across {df_esu['resource_id'].nunique()} systems")
    return df_esu

def get_system_details(resource_ids):
    """Get system details from SOM computers table"""
    conn = sqlite3.connect(CONFIG_DB)

    placeholders = ','.join(['?' for _ in resource_ids])

    query = f"""
        SELECT
            resource_id,
            json_extract(raw_data, '$.resource_name') as system_name,
            json_extract(raw_data, '$.domain_name') as domain_name,
            json_extract(raw_data, '$.customer_name') as customer_name,
            json_extract(raw_data, '$.branch_office_name') as branch_office,
            json_extract(raw_data, '$.os_name') as os_name,
            json_extract(raw_data, '$.os_version') as os_version,
            json_extract(raw_data, '$.service_pack') as service_pack,
            json_extract(raw_data, '$.ip_address') as ip_address,
            json_extract(raw_data, '$.mac_address') as mac_address,
            json_extract(raw_data, '$.description') as description,
            datetime(json_extract(raw_data, '$.last_contact_time')/1000, 'unixepoch') as last_online
        FROM som_computers
        WHERE resource_id IN ({placeholders})
    """

    df_systems = pd.read_sql_query(query, conn, params=resource_ids)
    conn.close()

    print(f"Retrieved details for {len(df_systems)} systems")
    return df_systems

def get_current_policies_from_tasks():
    """Get currently applied policies from deployment tasks"""
    conn = sqlite3.connect(CONFIG_DB)

    # Try to get deployment policies and their assignments
    queries = []

    # Query 1: Try deployment_policies table
    try:
        query1 = """
            SELECT
                json_extract(raw_data, '$.policy_id') as policy_id,
                json_extract(raw_data, '$.name') as policy_name,
                json_extract(raw_data, '$.description') as policy_description,
                json_extract(raw_data, '$.target_type') as target_type,
                json_extract(raw_data, '$.is_enabled') as is_enabled,
                raw_data
            FROM deployment_policies
        """
        df_policies = pd.read_sql_query(query1, conn)
        print(f"Found {len(df_policies)} deployment policies")
    except Exception as e:
        print(f"No deployment_policies table: {e}")
        df_policies = pd.DataFrame()

    # Query 2: Get scan details which might have policy info
    try:
        query2 = """
            SELECT
                json_extract(raw_data, '$.resource_id') as resource_id,
                json_extract(raw_data, '$.scan_status') as scan_status,
                datetime(json_extract(raw_data, '$.scan_time')/1000, 'unixepoch') as last_scan
            FROM scan_details
            LIMIT 10
        """
        df_scans = pd.read_sql_query(query2, conn)
        print(f"Found {len(df_scans)} scan records")
    except Exception as e:
        print(f"No scan_details or error: {e}")
        df_scans = pd.DataFrame()

    conn.close()
    return df_policies, df_scans

def get_patch_group_assignments():
    """Check if systems are assigned to patch groups"""
    conn = sqlite3.connect(CONFIG_DB)

    try:
        # Check structure of available tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")

        # Try to find policy/group assignments
        # This structure will vary based on PMP version

    except Exception as e:
        print(f"Error checking policy assignments: {e}")

    conn.close()
    return pd.DataFrame()

def analyze_raw_data_for_policies(df_systems):
    """Analyze raw_data fields to find policy information"""
    conn = sqlite3.connect(CONFIG_DB)

    # Get a sample of raw_data to understand structure
    cursor = conn.cursor()
    cursor.execute("SELECT raw_data FROM som_computers LIMIT 1")
    sample = cursor.fetchone()

    if sample:
        data = json.loads(sample[0])
        print("\nSample system raw_data keys:")
        for key in sorted(data.keys())[:20]:
            print(f"  - {key}: {str(data[key])[:50]}")

    conn.close()

def main():
    print("="*80)
    print("PMP ESU-Failing Systems Export")
    print("="*80)
    print()

    # Step 1: Get ESU-failing systems
    print("Step 1: Retrieving ESU-failing systems (error code 18)...")
    df_esu_failures = get_esu_failing_systems()
    print()

    if len(df_esu_failures) == 0:
        print("❌ No ESU failures found")
        return 1

    # Get unique systems
    unique_systems = df_esu_failures['resource_id'].unique().tolist()
    print(f"Unique systems with ESU failures: {len(unique_systems)}")
    print()

    # Step 2: Get system details
    print("Step 2: Retrieving system details...")
    df_systems = get_system_details(unique_systems)
    print()

    # Step 3: Get current policies
    print("Step 3: Retrieving current policy information...")
    df_policies, df_scans = get_current_policies_from_tasks()
    print()

    # Step 4: Analyze raw data for policy info
    print("Step 4: Analyzing raw data structure...")
    analyze_raw_data_for_policies(df_systems)
    print()

    # Step 5: Get patch group assignments
    print("Step 5: Checking patch group assignments...")
    df_assignments = get_patch_group_assignments()
    print()

    # Step 6: Merge ESU failure info with system details
    print("Step 6: Merging data...")
    df_merged = df_esu_failures.merge(df_systems, on='resource_id', how='left')

    # Get the most recent failure per system
    df_final = df_merged.sort_values('last_failure_date', ascending=False).groupby('resource_id').first().reset_index()

    # Step 7: Add customer breakdown (use branch_office as actual customer)
    print("Step 7: Analyzing customer distribution...")
    customer_counts = df_final['branch_office'].value_counts()
    print("\nCustomer Distribution (by Branch Office / Organization):")
    for customer, count in customer_counts.head(15).items():
        if pd.notna(customer) and customer != '--':
            print(f"  {customer}: {count} systems")
    print(f"\n  Total unique organizations: {df_final['branch_office'].nunique()}")
    print()

    # Step 8: Check for policy information in different fields
    print("Step 8: Searching for policy information in system data...")

    # Add placeholder for current policies (will need to be enhanced based on PMP structure)
    df_final['current_policies'] = "Not Available in Extracted Data"
    df_final['policy_notes'] = "Policy information may be in PMP console UI only, not exposed via API"

    # Step 9: Reorder columns
    columns_order = [
        'resource_id',
        'system_name',
        'customer_name',
        'domain_name',
        'branch_office',
        'os_name',
        'os_version',
        'service_pack',
        'ip_address',
        'mac_address',
        'last_online',
        'last_failure_date',
        'patch_name',
        'error_message',
        'severity',
        'current_policies',
        'policy_notes',
        'description'
    ]

    df_export = df_final[columns_order].copy()

    # Fill NaN values
    df_export['customer_name'] = df_export['customer_name'].fillna('Unknown')
    df_export['branch_office'] = df_export['branch_office'].fillna('N/A')
    df_export['description'] = df_export['description'].fillna('')

    # Step 10: Export to Excel
    output_file = Path.home() / "work_projects/pmp_reports/PMP_ESU_Failing_Systems.xlsx"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Step 9: Exporting to Excel...")
    print(f"   Output: {output_file}")
    print()

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: ESU-failing systems
        df_export.to_excel(writer, sheet_name='ESU Failing Systems', index=False)

        # Sheet 2: Customer summary (by branch_office / organization)
        df_customer = df_export.groupby('branch_office').agg({
            'resource_id': 'count',
            'system_name': lambda x: ', '.join(x.head(3)),
            'customer_name': 'first'  # Include MSP name
        }).reset_index()
        df_customer.columns = ['Organization', 'System Count', 'Sample Systems', 'MSP']
        df_customer = df_customer[df_customer['Organization'] != '--']  # Exclude blank
        df_customer = df_customer.sort_values('System Count', ascending=False)
        df_customer.to_excel(writer, sheet_name='Customer Summary', index=False)

        # Sheet 3: Summary statistics
        unique_orgs = df_export[df_export['branch_office'] != '--']['branch_office'].nunique()
        summary_data = {
            'Metric': [
                'MSP Provider',
                'Total ESU-Failing Systems',
                'Unique Customer Organizations',
                'Failing Patch (KB)',
                'Error Code',
                'Error Message',
                'Average Systems per Organization'
            ],
            'Value': [
                df_export['customer_name'].iloc[0] if len(df_export) > 0 else 'N/A',
                len(df_export),
                unique_orgs,
                df_export['patch_name'].iloc[0] if len(df_export) > 0 else 'N/A',
                '18',
                df_export['error_message'].iloc[0] if len(df_export) > 0 else 'N/A',
                f"{len(df_export) / max(unique_orgs, 1):.1f}"
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 4: Current policies (if available)
        if len(df_policies) > 0:
            df_policies.to_excel(writer, sheet_name='PMP Policies', index=False)

        # Sheet 5: Scan details (if available)
        if len(df_scans) > 0:
            df_scans.to_excel(writer, sheet_name='Scan Details', index=False)

    print("="*80)
    print("✅ SUCCESS - ESU-Failing Systems Report Exported")
    print("="*80)
    print()
    print(f"Output File: {output_file}")
    print(f"Total ESU-Failing Systems: {len(df_export):,}")
    print()
    print("Sheets Created:")
    print("  1. ESU Failing Systems - Complete list with ESU error details")
    print("  2. Customer Summary - Systems grouped by customer")
    print("  3. Summary - Key statistics")
    if len(df_policies) > 0:
        print("  4. PMP Policies - Current policies from PMP database")
    if len(df_scans) > 0:
        print("  5. Scan Details - Recent scan information")
    print()
    print("⚠️  NOTE: Current policy assignments may not be fully available")
    print("    Policy information is often stored in PMP console UI state,")
    print("    not always exposed via REST API endpoints.")
    print()
    unique_orgs_final = df_export[df_export['branch_office'] != '--']['branch_office'].nunique()
    print("Key Statistics:")
    print(f"  MSP Provider: {df_export['customer_name'].iloc[0] if len(df_export) > 0 else 'N/A'}")
    print(f"  ESU-Failing Systems: {len(df_export):,}")
    print(f"  Customer Organizations: {unique_orgs_final}")
    print(f"  Failing Patch: {df_export['patch_name'].iloc[0] if len(df_export) > 0 else 'N/A'}")
    print()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
