#!/usr/bin/env python3
"""
Publish PMP API Documentation to Orro Confluence Space

SRE-grade API documentation with production-tested patterns.

Created: 2025-12-02
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
MAIA_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MAIA_ROOT / 'claude/tools'))

from confluence_client import ConfluenceClient

def main():
    print("="*80)
    print("Publishing PMP API Documentation to Orro Confluence Space")
    print("="*80)
    print()

    # Read the markdown documentation
    docs_path = Path.home() / "work_projects/pmp_reports/PMP_API_Documentation.md"

    if not docs_path.exists():
        print(f"❌ Error: Documentation not found at {docs_path}")
        return 1

    print(f"📄 Reading documentation from: {docs_path}")
    with open(docs_path, 'r') as f:
        markdown_content = f.read()

    print(f"   Documentation size: {len(markdown_content):,} characters")
    print()

    # Initialize Confluence client
    print("🔗 Connecting to Confluence...")
    client = ConfluenceClient()
    print()

    # Publish to Orro space
    space_key = "Orro"
    title = "ManageEngine Patch Manager Plus - API Documentation (Production-Tested)"

    print(f"📝 Creating Confluence page...")
    print(f"   Space: {space_key}")
    print(f"   Title: {title}")
    print()

    try:
        url = client.create_page_from_markdown(
            space_key=space_key,
            title=title,
            markdown_content=markdown_content
        )

        print("="*80)
        print("✅ SUCCESS - API Documentation Published to Confluence")
        print("="*80)
        print()
        print(f"Space: {space_key}")
        print(f"Title: {title}")
        print(f"URL: {url}")
        print()
        print("📚 Documentation includes:")
        print("   - 12 API endpoints (all production-tested)")
        print("   - OAuth 2.0 authentication (Zoho Australian region)")
        print("   - Reliability patterns (rate limiting, retries, throttling)")
        print("   - Production code examples")
        print("   - Troubleshooting guide")
        print("   - Performance benchmarks (124,752 records extracted)")
        print()
        return 0

    except Exception as e:
        print(f"❌ Error publishing documentation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
