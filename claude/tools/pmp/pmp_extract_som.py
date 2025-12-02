#!/usr/bin/env python3
"""
Extract SOM (Scope of Management) endpoints.
Built with TDD - tests in tests/test_som_endpoints.py
"""

from pmp_complete_intelligence_extractor_v4_resume import PMPCompleteIntelligenceExtractor

def main():
    extractor = PMPCompleteIntelligenceExtractor()
    extractor.init_database()
    extractor.extraction_id = extractor.start_extraction_run()

    print("\n" + "="*80)
    print("SOM ENDPOINT EXTRACTION")
    print("="*80)
    print(f"Extraction ID: {extractor.extraction_id}\n")

    total_records = 0
    endpoints_extracted = 0

    # SOM Computers (3,448 records - ~2-3 minutes)
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
        print(f"✅ SOM Computers: {count} records")
    except Exception as e:
        print(f"❌ SOM Computers failed: {e}")

    # SOM Summary (single record)
    try:
        count = extractor.extract_endpoint_simple(
            name="SOM Summary",
            endpoint="/api/1.4/som/summary",
            table="som_summary",
            extract_fn=extractor.extract_simple_json
        )
        total_records += count
        endpoints_extracted += 1
        print(f"✅ SOM Summary: {count} record")
    except Exception as e:
        print(f"❌ SOM Summary failed: {e}")

    extractor.complete_extraction_run(endpoints_extracted, total_records)

    print()
    print("="*80)
    print(f"Extracted: {endpoints_extracted} endpoints, {total_records:,} records")
    print("="*80)

if __name__ == "__main__":
    main()
