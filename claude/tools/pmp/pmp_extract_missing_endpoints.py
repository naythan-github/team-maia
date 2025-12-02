#!/usr/bin/env python3
"""
Quick extraction of missing endpoints (All Systems, Deployment Policies, etc.)
Skips large Supported Patches endpoint to avoid 8-hour extraction.
"""

from pmp_complete_intelligence_extractor_v4_resume import PMPCompleteIntelligenceExtractor

def main():
    extractor = PMPCompleteIntelligenceExtractor()
    extractor.init_database()
    extractor.extraction_id = extractor.start_extraction_run()

    print("\n" + "="*80)
    print("FOCUSED EXTRACTION - Missing Endpoints Only")
    print("="*80)
    print(f"Extraction ID: {extractor.extraction_id}")
    print()

    total_records = 0
    endpoints_extracted = 0

    # All Systems (3,332 records - ~2-3 minutes)
    try:
        count = extractor.extract_endpoint_paginated(
            name="All Systems",
            endpoint="/api/1.4/patch/allsystems",
            table="all_systems",
            extract_fn=extractor.extract_all_systems,
            data_key="allsystems"
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ All Systems failed: {e}")

    # Deployment Policies (93 records - <1 minute)
    try:
        count = extractor.extract_endpoint_paginated(
            name="Deployment Policies",
            endpoint="/api/1.4/patch/deploymentpolicies",
            table="deployment_policies",
            extract_fn=extractor.extract_deployment_policies,
            data_key="deploymentpolicies"
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ Deployment Policies failed: {e}")

    # SOM Computers (3,456 records - ~2-3 minutes)
    try:
        count = extractor.extract_endpoint_paginated(
            name="SOM Computers",
            endpoint="/api/1.4/som/computers",
            table="som_computers",
            extract_fn=extractor.extract_som_computers,
            data_key="computers"
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ SOM Computers failed: {e}")

    # View Configurations
    try:
        count = extractor.extract_endpoint_paginated(
            name="View Configurations",
            endpoint="/api/1.4/patch/viewconfig",
            table="view_configurations",
            extract_fn=extractor.extract_view_configurations,
            data_key="viewconfig"
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ View Configurations failed: {e}")

    # Approval Settings (single record)
    try:
        count = extractor.extract_endpoint_simple(
            name="Approval Settings",
            endpoint="/api/1.4/patch/approvalsettings",
            table="approval_settings",
            extract_fn=extractor.extract_approval_settings
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ Approval Settings failed: {e}")

    # Health Policy (single record)
    try:
        count = extractor.extract_endpoint_simple(
            name="Health Policy",
            endpoint="/api/1.4/patch/healthpolicy",
            table="health_policy",
            extract_fn=extractor.extract_health_policy
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ Health Policy failed: {e}")

    # SOM Summary (single record)
    try:
        count = extractor.extract_endpoint_simple(
            name="SOM Summary",
            endpoint="/api/1.4/som/summary",
            table="som_summary",
            extract_fn=extractor.extract_som_summary
        )
        total_records += count
        endpoints_extracted += 1
    except Exception as e:
        print(f"❌ SOM Summary failed: {e}")

    extractor.complete_extraction_run(endpoints_extracted, total_records)

    print()
    print("="*80)
    print("FOCUSED EXTRACTION COMPLETE")
    print("="*80)
    print(f"Endpoints extracted: {endpoints_extracted}")
    print(f"Total records: {total_records:,}")
    print(f"Database: {extractor.db_path}")
    print()
    print("✅ All Systems, Deployment Policies, and configuration endpoints extracted")
    print("⏭️  Supported Patches (365K records) skipped - extract separately")

if __name__ == "__main__":
    main()
