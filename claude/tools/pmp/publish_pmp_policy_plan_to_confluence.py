#!/usr/bin/env python3
"""
Publish PMP Minimum Effective Policy Structure to Orro Confluence Space

Strategic policy design document with implementation roadmap.

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
    print("Publishing PMP Minimum Effective Policy Structure to Orro Confluence Space")
    print("="*80)
    print()

    # Read the markdown document
    docs_path = Path.home() / "work_projects/pmp_reports/PMP_Minimum_Effective_Policy_Structure.md"

    if not docs_path.exists():
        print(f"❌ Error: Policy document not found at {docs_path}")
        return 1

    print(f"📄 Reading policy document from: {docs_path}")
    with open(docs_path, 'r') as f:
        markdown_content = f.read()

    print(f"   Document size: {len(markdown_content):,} characters")
    print()

    # Initialize Confluence client
    print("🔗 Connecting to Confluence...")
    client = ConfluenceClient()
    print()

    # Publish to Orro space
    space_key = "Orro"
    title = "PMP Minimum Effective Policy Structure - 6 Core Policies (2025-12-02)"

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
        print("✅ SUCCESS - Policy Structure Published to Confluence")
        print("="*80)
        print()
        print(f"Space: {space_key}")
        print(f"Title: {title}")
        print(f"URL: {url}")
        print()
        print("📋 Policy Structure includes:")
        print("   - 6 Core Policies (vs 20-30 typical)")
        print("   - 70-80% policy reduction")
        print("   - 68.7% failure reduction")
        print("   - $493K annual savings")
        print("   - 2,288% ROI")
        print("   - Complete implementation roadmap")
        print("   - Risk mitigation strategies")
        print()
        return 0

    except Exception as e:
        print(f"❌ Error publishing policy document: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
