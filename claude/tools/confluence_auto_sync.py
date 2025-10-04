#!/usr/bin/env python3
"""
Confluence Intelligence Auto-Sync
Automatically checks and processes Confluence pages for intelligence updates

Author: Maia Personal Assistant Agent
Phase: 88 - Personal Assistant Automation Expansion
Date: 2025-10-03
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import hashlib

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.reliable_confluence_client import ReliableConfluenceClient
from claude.tools.confluence_intelligence_processor import ConfluenceIntelligenceProcessor
from claude.tools.confluence_to_trello import ConfluenceToTrello


class ConfluenceAutoSync:
    """Automatic Confluence intelligence synchronization"""

    def __init__(self):
        """Initialize auto-sync system"""
        self.confluence = ReliableConfluenceClient()
        self.processor = ConfluenceIntelligenceProcessor()
        self.trello_sync = ConfluenceToTrello()
        self.cache_file = MAIA_ROOT / "claude" / "data" / "confluence_sync_cache.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load sync cache"""
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                return json.load(f)
        return {"pages": {}}

    def _save_cache(self):
        """Save sync cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _get_content_hash(self, content: str) -> str:
        """Generate hash of page content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def check_and_sync_page(self, page_id: str, board_id: str = None) -> dict:
        """Check if page changed and sync if needed"""
        print(f"🔍 Checking Confluence page {page_id}...")

        # Fetch current page
        page = self.confluence.get_page(page_id)
        if not page:
            return {"error": "Page not found", "synced": False}

        # Get content
        content = page.get('body', {}).get('storage', {}).get('value', '')
        content_hash = self._get_content_hash(content)

        # Check cache
        page_cache = self.cache["pages"].get(page_id, {})
        last_hash = page_cache.get("content_hash")
        last_sync = page_cache.get("last_sync")

        if content_hash == last_hash:
            print(f"✅ No changes detected (last sync: {last_sync})")
            return {
                "page_id": page_id,
                "title": page['title'],
                "changed": False,
                "last_sync": last_sync
            }

        print(f"🔄 Changes detected! Processing intelligence...")

        # Save page content
        summaries_dir = MAIA_ROOT / "claude" / "data" / "confluence_summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        page_file = summaries_dir / f"{page['title'].replace(' ', '_')}_{page_id}.md"
        with open(page_file, 'w') as f:
            f.write(f"# {page['title']}\n\n")
            f.write(f"**URL**: {page.get('_links', {}).get('webui', '')}\n")
            f.write(f"**Updated**: {datetime.now().isoformat()}\n\n")
            # Convert HTML to markdown (basic)
            import html
            text_content = html.unescape(content)
            # Remove HTML tags (basic cleaning)
            import re
            text_content = re.sub(r'<[^>]+>', '\n', text_content)
            text_content = re.sub(r'\n+', '\n\n', text_content)
            f.write(text_content)

        # Process intelligence
        url = f"https://vivoemc.atlassian.net/wiki/spaces/Orro/pages/{page_id}"
        result = self.processor.process_page(str(page_file), url)

        # Sync to Trello if board specified
        if board_id:
            print(f"📋 Syncing to Trello board {board_id}...")
            trello_result = self.trello_sync.sync_to_trello(board_id)
            print(f"✅ Created {trello_result['summary']['total_created']} Trello cards")
        else:
            trello_result = None

        # Update cache
        self.cache["pages"][page_id] = {
            "title": page['title'],
            "content_hash": content_hash,
            "last_sync": datetime.now().isoformat(),
            "intelligence_summary": {
                "actions": len(result['action_items']),
                "questions": len(result['questions']),
                "strategic": len(result['strategic_initiatives']),
                "decisions": len(result['decisions_needed'])
            }
        }
        self._save_cache()

        return {
            "page_id": page_id,
            "title": page['title'],
            "changed": True,
            "synced_at": datetime.now().isoformat(),
            "intelligence": self.cache["pages"][page_id]["intelligence_summary"],
            "trello_sync": trello_result
        }

    def sync_monitored_pages(self, board_id: str = None) -> list:
        """Sync all monitored pages"""
        # Default monitored pages (can be configured)
        monitored_pages = [
            "3113484297"  # Thoughts and notes
        ]

        results = []
        for page_id in monitored_pages:
            result = self.check_and_sync_page(page_id, board_id)
            results.append(result)

        return results


def main():
    """CLI entry"""
    import argparse
    parser = argparse.ArgumentParser(description="Confluence intelligence auto-sync")
    parser.add_argument('--page', type=str, help='Specific page ID to sync')
    parser.add_argument('--board', type=str, default="68de069e996bf03442ae5eea",
                       help='Trello board ID for syncing')
    parser.add_argument('--all', action='store_true', help='Sync all monitored pages')
    args = parser.parse_args()

    sync = ConfluenceAutoSync()

    if args.page:
        result = sync.check_and_sync_page(args.page, args.board)
        print(f"\n{'='*70}")
        print(f"Sync Result:")
        print(json.dumps(result, indent=2))
    elif args.all:
        results = sync.sync_monitored_pages(args.board)
        print(f"\n{'='*70}")
        print(f"Synced {len(results)} pages")
        for r in results:
            if r.get('changed'):
                print(f"  ✅ {r['title']}: Updated")
            else:
                print(f"  ⏭  {r['title']}: No changes")
    else:
        # Default: sync monitored pages
        results = sync.sync_monitored_pages(args.board)
        print(f"\n📊 Sync Summary:")
        changed = [r for r in results if r.get('changed')]
        print(f"  • Total pages checked: {len(results)}")
        print(f"  • Pages with changes: {len(changed)}")
        if changed:
            print(f"\n  Updated pages:")
            for r in changed:
                intel = r.get('intelligence', {})
                print(f"    - {r['title']}: {intel.get('actions', 0)} actions, "
                      f"{intel.get('strategic', 0)} strategic items")


if __name__ == "__main__":
    main()
