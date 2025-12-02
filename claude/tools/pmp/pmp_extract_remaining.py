#!/usr/bin/env python3
"""
Extract remaining simple endpoints using correct extraction functions.
"""

from pmp_complete_intelligence_extractor_v4_resume import PMPCompleteIntelligenceExtractor

def main():
    extractor = PMPCompleteIntelligenceExtractor()
    extractor.init_database()
    extractor.extraction_id = extractor.start_extraction_run()

    print("\n" + "="*80)
    print("EXTRACTING REMAINING SIMPLE ENDPOINTS")
    print("="*80)
    print(f"Extraction ID: {extractor.extraction_id}\n")

    total_records = 0
    endpoints_extracted = 0

    # Health Policy (single record)
    try:
        count = extractor.extract_endpoint_simple(
            name="Health Policy",
            endpoint="/api/1.4/patch/healthpolicy",
            table="health_policy",
            extract_fn=extractor.extract_simple_json
        )
        total_records += count
        endpoints_extracted += 1
        print(f"✅ Health Policy: {count} record")
    except Exception as e:
        print(f"❌ Health Policy failed: {e}")

    # Approval Settings (single record)
    try:
        count = extractor.extract_endpoint_simple(
            name="Approval Settings",
            endpoint="/api/1.4/patch/approvalsettings",
            table="approval_settings",
            extract_fn=extractor.extract_simple_json
        )
        total_records += count
        endpoints_extracted += 1
        print(f"✅ Approval Settings: {count} record")
    except Exception as e:
        print(f"❌ Approval Settings failed: {e}")

    extractor.complete_extraction_run(endpoints_extracted, total_records)

    print()
    print("="*80)
    print(f"Extracted: {endpoints_extracted} endpoints, {total_records} records")
    print("="*80)

if __name__ == "__main__":
    main()
