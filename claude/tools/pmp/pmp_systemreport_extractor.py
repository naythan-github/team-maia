#!/usr/bin/env python3
"""
PMP System Report Extractor - Per-System Query Pattern

Uses the CORRECT PMP API pattern:
1. GET /api/1.4/patch/allsystems → Get all systems with resource_id
2. For each system: GET /api/1.4/patch/systemreport?resid={resource_id}

This follows the API design documented at:
https://www.manageengine.com/eu/patch-management/api/system-report-patch-management.html

Database: ~/.maia/databases/intelligence/pmp_systemreports.db

Usage:
    python3 pmp_systemreport_extractor.py
"""

import sys
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager import PMPOAuthManager

# Database path
DB_PATH = Path.home() / ".maia" / "databases" / "intelligence" / "pmp_systemreports.db"


class PMPSystemReportExtractor:
    """Extract patch data using per-system systemreport queries"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.base_url = self.oauth_manager.server_url
        self.db_path = DB_PATH
        self.extraction_id = None

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Extraction runs tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_runs (
                extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                systems_found INTEGER DEFAULT 0,
                systems_processed INTEGER DEFAULT 0,
                total_patches INTEGER DEFAULT 0,
                errors TEXT
            )
        """)

        # Systems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                computer_name TEXT,
                domain_name TEXT,
                os_name TEXT,
                ip_address TEXT,
                agent_version TEXT,
                last_contact_time INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES extraction_runs(extraction_id)
            )
        """)

        # System reports (patches per system)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                resource_id INTEGER,
                patch_id INTEGER,
                patch_name TEXT,
                bulletin_id TEXT,
                severity INTEGER,
                patch_status INTEGER,
                approval_status INTEGER,
                is_reboot_required INTEGER,
                patch_deployed INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES extraction_runs(extraction_id),
                FOREIGN KEY (resource_id) REFERENCES systems(resource_id)
            )
        """)

        # Index for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_reports_resource
            ON system_reports(resource_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_reports_patch
            ON system_reports(patch_id)
        """)

        conn.commit()
        conn.close()

    def start_extraction_run(self):
        """Start a new extraction run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO extraction_runs (started_at, status)
            VALUES (?, 'running')
        """, (datetime.now().isoformat(),))

        self.extraction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"✅ Started extraction run ID: {self.extraction_id}")

    def complete_extraction_run(self, systems_found: int, systems_processed: int,
                                total_patches: int, errors: Optional[str] = None):
        """Mark extraction run as complete"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE extraction_runs
            SET completed_at = ?,
                status = ?,
                systems_found = ?,
                systems_processed = ?,
                total_patches = ?,
                errors = ?
            WHERE extraction_id = ?
        """, (
            datetime.now().isoformat(),
            'completed' if not errors else 'completed_with_errors',
            systems_found,
            systems_processed,
            total_patches,
            errors,
            self.extraction_id
        ))

        conn.commit()
        conn.close()

    def fetch_json(self, endpoint: str, page: Optional[int] = None,
                   params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Fetch JSON data from API endpoint with retry logic.
        Copied from DCAPI extractor reliability patterns.
        """
        import requests

        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {"Authorization": f"Zoho-oauthtoken {token}"}  # FIX: Use Zoho format, not Bearer!
                url = f"{self.base_url}{endpoint}"

                # Build params
                request_params = params.copy() if params else {}
                if page is not None:
                    request_params['page'] = page

                response = requests.get(url, headers=headers, params=request_params, timeout=(10, 30))

                if response.status_code == 200:
                    data = response.json()
                    # Extract message_response wrapper if present
                    if 'message_response' in data:
                        return data['message_response']
                    return data
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"   ⚠️  Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # 2s, 4s, 8s
                        print(f"   ⚠️  Server error {response.status_code}. Retry {attempt}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ HTTP {response.status_code} after {max_retries} retries")
                        return None
                else:
                    print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                    return None

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"   ⚠️  Timeout. Retry {attempt}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Timeout after {max_retries} attempts")
                    return None
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"   ⚠️  Connection error. Retry {attempt}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Connection failed after {max_retries} attempts")
                    return None
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                return None

        return None

    def fetch_all_systems(self) -> List[Dict]:
        """Step 1: Fetch all systems with their resource IDs"""
        print("\n📥 Step 1: Fetching all systems...")
        print(f"   Endpoint: /api/1.4/patch/allsystems")

        all_systems = []
        page = 1

        while True:
            print(f"   Fetching page {page}...")
            data = self.fetch_json("/api/1.4/patch/allsystems", page=page)

            if data is None:
                print(f"   ❌ Failed to fetch page {page}")
                break

            # FIX: Check multiple possible field names (matches PowerShell script)
            systems = None
            if 'allsystems' in data:
                systems = data['allsystems']
            elif 'computers' in data:
                systems = data['computers']
            elif 'systems' in data:
                systems = data['systems']
            elif 'data' in data:
                systems = data['data']
            else:
                systems = []

            total = data.get('total', 0)

            if not systems:
                if total > 0 and len(all_systems) == 0:
                    print(f"   ⚠️  WARNING: API reports {total} systems but returns empty array")
                    print(f"   This may be a vendor API issue. Stopping extraction.")
                break

            all_systems.extend(systems)
            print(f"   Page {page}: {len(systems)} systems (total: {total:,})")

            # Check if we've got all systems
            if len(all_systems) >= total:
                break

            page += 1
            time.sleep(0.25)  # Rate limiting

        print(f"   ✅ Found {len(all_systems):,} systems")
        return all_systems

    def save_systems(self, systems: List[Dict]) -> int:
        """Save systems to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for system in systems:
            cursor.execute("""
                INSERT OR REPLACE INTO systems
                (resource_id, extraction_id, computer_name, domain_name, os_name,
                 ip_address, agent_version, last_contact_time, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system.get('resource_id'),
                self.extraction_id,
                system.get('computer_name'),
                system.get('domain_name'),
                system.get('os_name'),
                system.get('ip_address'),
                system.get('agent_version'),
                system.get('last_contact_time'),
                json.dumps(system),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(systems)

    def fetch_system_report(self, resource_id: int) -> Optional[List[Dict]]:
        """Step 2: Fetch patch report for a specific system"""
        all_patches = []
        page = 1

        while True:
            data = self.fetch_json("/api/1.4/patch/systemreport",
                                   page=page,
                                   params={'resid': resource_id})

            if data is None:
                return None

            patches = data.get('systemreport', [])
            total = data.get('total', 0)

            if not patches:
                break

            all_patches.extend(patches)

            # Check if we've got all patches
            if len(all_patches) >= total:
                break

            page += 1
            time.sleep(0.1)  # Rate limiting

        return all_patches

    def save_system_report(self, resource_id: int, patches: List[Dict]) -> int:
        """Save system report to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for patch in patches:
            cursor.execute("""
                INSERT INTO system_reports
                (extraction_id, resource_id, patch_id, patch_name, bulletin_id,
                 severity, patch_status, approval_status, is_reboot_required,
                 patch_deployed, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.extraction_id,
                resource_id,
                patch.get('patch_id'),
                patch.get('patch_name'),
                patch.get('bulletin_id'),
                patch.get('severity'),
                patch.get('patch_status'),
                patch.get('approval_status'),
                patch.get('is_reboot_required'),
                patch.get('patch_deployed'),
                json.dumps(patch),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(patches)

    def extract_all(self):
        """Main extraction workflow"""
        self.start_extraction_run()

        print("=" * 80)
        print("PMP SYSTEM REPORT EXTRACTION - PER-SYSTEM QUERY PATTERN")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Extraction ID: {self.extraction_id}")
        print()

        # Step 1: Get all systems
        systems = self.fetch_all_systems()
        if not systems:
            print("\n❌ No systems found. Extraction aborted.")
            self.complete_extraction_run(0, 0, 0, "No systems found")
            return

        # Save systems
        print(f"\n💾 Saving {len(systems):,} systems to database...")
        self.save_systems(systems)
        print(f"   ✅ Saved")

        # Step 2: Get patch reports for each system
        print(f"\n📥 Step 2: Fetching patch reports for {len(systems):,} systems...")
        print("   (This may take a while...)\n")

        systems_processed = 0
        total_patches = 0
        errors = []

        for idx, system in enumerate(systems, 1):
            resource_id = system.get('resource_id')
            computer_name = system.get('computer_name', 'Unknown')

            if not resource_id:
                print(f"   ⚠️  [{idx}/{len(systems)}] {computer_name}: No resource_id, skipping")
                continue

            print(f"   [{idx}/{len(systems)}] {computer_name} (resid={resource_id})...", end='', flush=True)

            patches = self.fetch_system_report(resource_id)

            if patches is None:
                print(f" ❌ Failed")
                errors.append(f"System {resource_id} ({computer_name}): Failed to fetch")
                continue

            if patches:
                self.save_system_report(resource_id, patches)
                print(f" ✅ {len(patches)} patches")
                total_patches += len(patches)
            else:
                print(f" ✅ 0 patches")

            systems_processed += 1

            # Progress update every 10 systems
            if idx % 10 == 0:
                print(f"      Progress: {systems_processed}/{len(systems)} systems, {total_patches:,} patches")

            time.sleep(0.25)  # Rate limiting

        # Complete extraction
        error_summary = '\n'.join(errors) if errors else None
        self.complete_extraction_run(len(systems), systems_processed, total_patches, error_summary)

        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)
        print(f"Extraction ID: {self.extraction_id}")
        print(f"Systems found: {len(systems):,}")
        print(f"Systems processed: {systems_processed:,}")
        print(f"Total patches extracted: {total_patches:,}")
        print(f"Database: {self.db_path}")
        print()

        if errors:
            print(f"⚠️  ERRORS: {len(errors)}")
            for error in errors[:10]:  # Show first 10
                print(f"   - {error}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more")
            print()


if __name__ == '__main__':
    print("PMP System Report Extractor")
    print("Using per-system query pattern (allsystems → systemreport)")
    print()

    extractor = PMPSystemReportExtractor()
    extractor.extract_all()

    print("✅ Extraction complete!")
