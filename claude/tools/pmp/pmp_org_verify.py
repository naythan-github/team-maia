#!/usr/bin/env python3
"""
PMP Organization Verification Tool
Compares organizations in database vs PMP API
Handles rate limiting gracefully
"""

import sqlite3
import time
from pathlib import Path
from collections import defaultdict

try:
    from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
except ImportError:
    from pmp_oauth_manager import PMPOAuthManager


def get_db_organizations(db_path: Path) -> dict:
    """Get organizations from database with system counts"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT branch_office_name, COUNT(*) as count
        FROM systems
        GROUP BY branch_office_name
        ORDER BY branch_office_name
    """)

    orgs = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    return orgs


def get_api_organizations(max_pages: int = None) -> dict:
    """Get organizations from PMP API with system counts"""
    oauth = PMPOAuthManager()

    try:
        # Get first page
        response = oauth.api_request('GET', '/api/1.4/patch/scandetails')
        data = response.json()

        total_systems = data['message_response']['total']
        page_limit = data['message_response']['limit']
        total_pages = (total_systems + page_limit - 1) // page_limit

        if max_pages:
            total_pages = min(total_pages, max_pages)

        print(f"API: {total_systems} total systems, {total_pages} pages to check")

        org_counts = defaultdict(int)

        for page in range(1, total_pages + 1):
            try:
                if page > 1:
                    response = oauth.api_request(
                        'GET',
                        '/api/1.4/patch/scandetails',
                        params={'page': page}
                    )
                    data = response.json()

                systems = data['message_response']['scandetails']

                for system in systems:
                    org = system.get('branch_office_name', 'Unknown')
                    if org and org != '--':
                        org_counts[org] += 1

                print(f"\rProgress: {page}/{total_pages} pages ({len(org_counts)} orgs, {sum(org_counts.values())} systems)", end='', flush=True)

                time.sleep(0.25)  # Rate limiting

            except Exception as e:
                print(f"\n⚠️  Error at page {page}: {e}")
                print(f"Stopping at page {page-1} to avoid rate limit")
                break

        print()
        return dict(org_counts)

    except Exception as e:
        print(f"❌ API Error: {e}")
        return {}


def main():
    db_path = Path.home() / ".maia/databases/intelligence/pmp_config.db"

    print("=" * 70)
    print("PMP ORGANIZATION VERIFICATION")
    print("=" * 70)
    print()

    # Get database orgs
    print("📊 Loading organizations from database...")
    db_orgs = get_db_organizations(db_path)
    print(f"   Found {len(db_orgs)} organizations ({sum(db_orgs.values())} systems)")
    print()

    # Get API orgs (limit to avoid rate limiting)
    print("🔍 Querying PMP API (checking all pages, will stop if rate limited)...")
    api_orgs = get_api_organizations()
    print(f"   Found {len(api_orgs)} organizations ({sum(api_orgs.values())} systems)")
    print()

    # Compare
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print()

    db_only = set(db_orgs.keys()) - set(api_orgs.keys())
    api_only = set(api_orgs.keys()) - set(db_orgs.keys())
    common = set(db_orgs.keys()) & set(api_orgs.keys())

    if api_only:
        print(f"⚠️  MISSING FROM DATABASE ({len(api_only)} organizations):")
        for org in sorted(api_only):
            print(f"   - {org} ({api_orgs[org]} systems in API)")
        print()

    if db_only:
        print(f"ℹ️  IN DATABASE BUT NOT IN API RESULTS ({len(db_only)} organizations):")
        print(f"   (Note: May be in later pages if API query was rate limited)")
        for org in sorted(db_only):
            print(f"   - {org} ({db_orgs[org]} systems in DB)")
        print()

    if common:
        print(f"✅ MATCHED ({len(common)} organizations):")

        # Check for count mismatches
        mismatches = []
        for org in sorted(common):
            db_count = db_orgs[org]
            api_count = api_orgs[org]
            if db_count != api_count:
                mismatches.append((org, db_count, api_count))

        if mismatches:
            print(f"   ⚠️  System count mismatches:")
            for org, db_count, api_count in mismatches:
                diff = api_count - db_count
                print(f"      - {org}: DB={db_count}, API={api_count} (diff: {diff:+d})")
        else:
            print(f"   All {len(common)} organizations have matching system counts")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Database: {len(db_orgs)} organizations, {sum(db_orgs.values())} systems")
    print(f"API:      {len(api_orgs)} organizations, {sum(api_orgs.values())} systems")
    print(f"Missing:  {sum(api_orgs.values()) - sum(db_orgs.values())} systems not in database")

    if api_only:
        print(f"\n🚨 ACTION REQUIRED: {len(api_only)} organizations missing from database")
        print(f"   Run: python3 claude/tools/pmp/pmp_enhanced_extractor.py")
    else:
        print(f"\n✅ All organizations from API are in database")


if __name__ == '__main__':
    main()
