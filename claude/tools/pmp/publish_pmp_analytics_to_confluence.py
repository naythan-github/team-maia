#!/usr/bin/env python3
"""
Publish PMP Comprehensive Analytics Report to Orro Confluence Space

Uses confluence_client.py to publish markdown directly to Confluence.

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
    print("Publishing PMP Comprehensive Analytics Report to Orro Confluence Space")
    print("="*80)
    print()

    # Read the markdown report
    report_path = Path.home() / "work_projects/pmp_reports/PMP_Comprehensive_Analytics_Report.md"

    if not report_path.exists():
        print(f"❌ Error: Report not found at {report_path}")
        return 1

    print(f"📄 Reading report from: {report_path}")
    with open(report_path, 'r') as f:
        markdown_content = f.read()

    print(f"   Report size: {len(markdown_content):,} characters")
    print()

    # Initialize Confluence client
    print("🔗 Connecting to Confluence...")
    client = ConfluenceClient()
    print()

    # Publish to Orro space
    space_key = "Orro"
    title = "PMP Patch Management Analytics - Comprehensive Report (2025-12-02)"

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
        print("✅ SUCCESS - Report Published to Confluence")
        print("="*80)
        print()
        print(f"Space: {space_key}")
        print(f"Title: {title}")
        print(f"URL: {url}")
        print()
        print("📊 View the report in your browser:")
        print(f"   {url}")
        print()
        return 0

    except Exception as e:
        print(f"❌ Error publishing report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
