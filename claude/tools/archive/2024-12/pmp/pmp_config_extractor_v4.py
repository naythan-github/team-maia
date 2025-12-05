#!/usr/bin/env python3
"""
PMP Configuration Extractor v4 - ONLY VALIDATED WORKING ENDPOINTS

Based on individual endpoint testing, this extracts ONLY the 4 endpoints
that returned actual data:
1. Patch Summary
2. Health Policy
3. View Configurations (225 records)
4. Approval Settings

All other endpoints return empty arrays despite showing totals (vendor API bug).
Use pmp_dcapi_patch_extractor for comprehensive patch/system data.

Database: ~/.maia/databases/intelligence/pmp_config.db

Usage:
    python3 pmp_config_extractor_v4.py
"""

import sys
import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager import PMPOAuthManager

# Database path
DB_PATH = Path.home() / ".maia" / "databases" / "intelligence" / "pmp_config.db"


class PMPConfigExtractor:
    """Extract ONLY validated working configuration endpoints"""

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
        """Initialize database schema for working endpoints only"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Extraction runs tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_extraction_runs (
                extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                endpoints_extracted INTEGER DEFAULT 0,
                total_records INTEGER DEFAULT 0,
                errors TEXT
            )
        """)

        # 1. Patch Summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patch_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                summary_data TEXT NOT NULL,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 2. Health Policy
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_policy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                policy_data TEXT NOT NULL,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 3. View Configurations (225 records)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS view_configurations (
                config_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                view_name TEXT,
                view_desc TEXT,
                is_default INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 4. Approval Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                settings_data TEXT NOT NULL,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        conn.commit()
        conn.close()

    def start_extraction_run(self):
        """Start a new extraction run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO api_extraction_runs (started_at, status)
            VALUES (?, 'running')
        """, (datetime.now().isoformat(),))

        self.extraction_id = cursor.lastrowid
        conn.commit()
        conn.close()

    def complete_extraction_run(self, endpoints_extracted: int, total_records: int, errors: Optional[str] = None):
        """Mark extraction run as complete"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE api_extraction_runs
            SET completed_at = ?,
                status = ?,
                endpoints_extracted = ?,
                total_records = ?,
                errors = ?
            WHERE extraction_id = ?
        """, (
            datetime.now().isoformat(),
            'completed' if not errors else 'completed_with_errors',
            endpoints_extracted,
            total_records,
            errors,
            self.extraction_id
        ))

        conn.commit()
        conn.close()

    def fetch_json(self, endpoint: str, page: Optional[int] = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Fetch JSON data from API endpoint with retry logic.
        Copied from DCAPI extractor reliability patterns.
        """
        import requests

        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.base_url}{endpoint}"
                params = {'page': page} if page is not None else None

                response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

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

    def fetch_all_pages(self, endpoint: str, data_key: str) -> List[Dict]:
        """Fetch all pages from paginated endpoint"""
        all_records = []
        page = 1

        print(f"   Fetching page {page}...")
        data = self.fetch_json(endpoint, page=page)

        if data is None:
            return []

        # Get total count
        total_count = data.get('total', 0)
        records = data.get(data_key, [])

        if total_count == 0:
            print(f"   ⚠️  API returned total=0")
            return []

        all_records.extend(records)
        print(f"   Page 1: {len(records)} records (total: {total_count:,})")

        # Calculate pages needed (25 records per page)
        pages_needed = (total_count + 24) // 25

        # Fetch remaining pages
        for page in range(2, pages_needed + 1):
            data = self.fetch_json(endpoint, page=page)
            if data is None:
                print(f"   ⚠️  Failed to fetch page {page}")
                break

            records = data.get(data_key, [])
            all_records.extend(records)

            # Progress update every 10 pages
            if page % 10 == 0:
                print(f"      Progress: {len(all_records):,}/{total_count:,} records ({page}/{pages_needed} pages)")

            # Check if we've got all records
            if len(all_records) >= total_count:
                break

            time.sleep(0.25)  # Rate limiting

        print(f"      ✅ Fetched {len(all_records):,} records from {page} pages")
        return all_records

    def extract_simple_json(self, data: Dict, table: str) -> int:
        """Extract simple JSON object to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Map table names to their data column names
        column_map = {
            'patch_summary': 'summary_data',
            'health_policy': 'policy_data',
            'approval_settings': 'settings_data'
        }

        data_column = column_map.get(table)
        if not data_column:
            raise ValueError(f"Unknown table: {table}")

        cursor.execute(f"""
            INSERT INTO {table} (extraction_id, {data_column}, extracted_at)
            VALUES (?, ?, ?)
        """, (self.extraction_id, json.dumps(data), datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return 1

    def extract_view_configurations(self, records: List[Dict], table: str) -> int:
        """Extract view configurations to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for record in records:
            cursor.execute(f"""
                INSERT OR REPLACE INTO {table}
                (config_id, extraction_id, view_name, view_desc, is_default, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get('VIEW_ID'),
                self.extraction_id,
                record.get('VIEW_NAME'),
                record.get('VIEW_DESC'),
                record.get('IS_DEFAULT'),
                json.dumps(record),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(records)

    def extract_endpoint_simple(self, name: str, endpoint: str, table: str, extract_fn) -> int:
        """Extract non-paginated endpoint"""
        print(f"\n📥 Extracting: {name}")
        print(f"   Endpoint: {endpoint}")

        start_time = time.time()
        data = self.fetch_json(endpoint)

        if data is None:
            print(f"   ❌ Failed to fetch data")
            return 0

        record_count = extract_fn(data, table)
        elapsed = time.time() - start_time

        print(f"   ✅ Extracted {record_count:,} records in {elapsed:.2f}s")
        return record_count

    def extract_endpoint_paginated(self, name: str, endpoint: str, table: str,
                                   extract_fn, data_key: str) -> int:
        """Extract paginated endpoint"""
        print(f"\n📥 Extracting: {name}")
        print(f"   Endpoint: {endpoint}")

        start_time = time.time()

        # Fetch all pages
        records = self.fetch_all_pages(endpoint, data_key)

        if not records:
            print(f"   ❌ No records found")
            return 0

        # Insert into database
        record_count = extract_fn(records, table)
        elapsed = time.time() - start_time

        print(f"   ✅ Extracted {record_count:,} records in {elapsed:.2f}s")
        return record_count

    def extract_all(self):
        """Extract data from 4 validated working endpoints"""
        self.start_extraction_run()

        total_records = 0
        endpoints_extracted = 0
        errors = []

        print("=" * 80)
        print("PMP CONFIGURATION EXTRACTION - VALIDATED ENDPOINTS ONLY")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Extraction ID: {self.extraction_id}")
        print()
        print("NOTE: Only extracting 4 working endpoints.")
        print("      Use pmp_dcapi_patch_extractor for comprehensive patch/system data.")
        print()

        try:
            # 1. Patch Summary (non-paginated)
            count = self.extract_endpoint_simple(
                "1. Patch Summary",
                "/api/1.4/patch/summary",
                "patch_summary",
                self.extract_simple_json
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 2. Health Policy (non-paginated)
            count = self.extract_endpoint_simple(
                "2. Health Policy",
                "/api/1.4/patch/healthpolicy",
                "health_policy",
                self.extract_simple_json
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 3. View Configurations (225 records, paginated)
            count = self.extract_endpoint_paginated(
                "3. View Configurations",
                "/api/1.4/patch/viewconfig",
                "view_configurations",
                self.extract_view_configurations,
                "viewconfig"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 4. Approval Settings (non-paginated)
            count = self.extract_endpoint_simple(
                "4. Approval Settings",
                "/api/1.4/patch/approvalsettings",
                "approval_settings",
                self.extract_simple_json
            )
            total_records += count
            endpoints_extracted += 1

        except Exception as e:
            error_msg = f"Extraction error: {str(e)}"
            errors.append(error_msg)
            print(f"\n❌ {error_msg}")

        # Complete extraction run
        self.complete_extraction_run(
            endpoints_extracted,
            total_records,
            '\n'.join(errors) if errors else None
        )

        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)
        print(f"Extraction ID: {self.extraction_id}")
        print(f"Endpoints extracted: {endpoints_extracted}/4")
        print(f"Total records: {total_records:,}")
        print(f"Database: {self.db_path}")
        print()

        if errors:
            print("⚠️  ERRORS:")
            for error in errors:
                print(f"   - {error}")
            print()


if __name__ == '__main__':
    print("PMP Configuration Extractor v4")
    print("Extracting ONLY 4 validated working endpoints")
    print()

    extractor = PMPConfigExtractor()
    extractor.extract_all()

    print("✅ Extraction complete!")
