#!/usr/bin/env python3
"""
PMP Complete Intelligence Extractor - Fixed Pagination

API uses fixed 25-record pages. Only `page` parameter is accepted (no `pageLimit`).

Database: ~/.maia/databases/intelligence/pmp_config.db

Usage:
    python3 pmp_complete_intelligence_extractor_v3.py
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


class PMPCompleteIntelligenceExtractor:
    """Comprehensive PMP data extraction with correct pagination (fixed 25 records/page)"""

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
        """Initialize database schema for all endpoint data"""
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

        # 3. All Patches (5,217 patches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS all_patches (
                patch_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                platform TEXT,
                patch_released_time INTEGER,
                patch_size INTEGER,
                patch_noreboot INTEGER,
                installed INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 5. Supported Patches (364,673 patches - master catalog)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supported_patches (
                update_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                bulletin_id TEXT,
                patch_lang TEXT,
                patch_updated_time INTEGER,
                is_superceded INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 7. All Systems (3,364 systems)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS all_systems (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                branch_office_id INTEGER,
                last_patched_time INTEGER,
                total_driver_patches INTEGER,
                missing_bios_patches INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 9. Deployment Policies (92 policies)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployment_policies (
                template_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                template_name TEXT,
                creation_time INTEGER,
                modified_time INTEGER,
                is_template_alive INTEGER,
                set_as_default INTEGER,
                user_id INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 10. Health Policy
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_policy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                policy_data TEXT NOT NULL,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 11. View Configurations (225 configs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS view_configurations (
                config_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                collection_id INTEGER,
                total_target_count INTEGER,
                os_platform_name TEXT,
                collection_platform_id INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 12. Approval Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_id INTEGER,
                settings_data TEXT NOT NULL,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 13. Scan Details (3,364 systems)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_details (
                resource_id INTEGER PRIMARY KEY,
                extraction_id INTEGER,
                resource_health_status INTEGER,
                os_platform_name TEXT,
                branch_office_id INTEGER,
                agent_installed_on INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 14. Installed Patches (3,505 patches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installed_patches (
                patch_id INTEGER,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                platform TEXT,
                patch_released_time INTEGER,
                patch_noreboot INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                PRIMARY KEY (patch_id, extraction_id),
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        # 15. Missing Patches (1,712 patches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missing_patches (
                patch_id INTEGER,
                extraction_id INTEGER,
                bulletin_id TEXT,
                update_name TEXT,
                platform TEXT,
                patch_released_time INTEGER,
                patch_noreboot INTEGER,
                raw_data TEXT,
                extracted_at TEXT NOT NULL,
                PRIMARY KEY (patch_id, extraction_id),
                FOREIGN KEY (extraction_id) REFERENCES api_extraction_runs(extraction_id)
            )
        """)

        conn.commit()
        conn.close()

    def start_extraction_run(self):
        """Start new extraction run and return extraction_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO api_extraction_runs (started_at, status)
            VALUES (?, 'running')
        """, (datetime.now().isoformat(),))

        self.extraction_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"\n🔄 Started extraction run #{self.extraction_id}")
        return self.extraction_id

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

        Args:
            endpoint: API endpoint path
            page: Optional page number (for paginated endpoints)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Response data with message_response wrapper removed
        """
        import requests

        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {"Authorization": f"Zoho-oauthtoken {token}"}  # FIX: Use Zoho format, not Bearer!
                url = f"{self.base_url}{endpoint}"

                # Only add page param if specified (API rejects pageLimit!)
                params = {'page': page} if page is not None else None

                response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

                if response.status_code == 200:
                    # Check for HTML throttling page (not JSON)
                    content = response.text
                    if content.strip().startswith('<') or '<!DOCTYPE' in content or '<html' in content.lower():
                        # API returned HTML instead of JSON - likely throttled
                        print(f"   ⚠️  Received HTML response (throttling). Waiting 60s...")
                        time.sleep(60)
                        continue

                    try:
                        data = response.json()
                        # Extract message_response wrapper
                        if 'message_response' in data:
                            return data['message_response']
                        return data
                    except ValueError as e:
                        # JSON parse error - likely empty or malformed response
                        print(f"   ⚠️  JSON parse error (throttling?). Waiting 60s...")
                        time.sleep(60)
                        continue
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
                        print(f"   ❌ HTTP {response.status_code}: {endpoint} (max retries)")
                        return None
                else:
                    print(f"   ⚠️  HTTP {response.status_code}: {endpoint}")
                    return None

            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"   ⚠️  Timeout. Retry {attempt}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Timeout after {max_retries} attempts: {endpoint}")
                    return None
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"   ⚠️  Connection error. Retry {attempt}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Connection failed after {max_retries} attempts: {endpoint}")
                    return None
            except Exception as e:
                print(f"   ❌ Error fetching {endpoint}: {e}")
                return None

        return None

    def fetch_all_pages(self, endpoint: str, data_key: str) -> List[Dict]:
        """
        Fetch all pages from a paginated API endpoint.
        
        API pagination: Fixed 25 records per page, uses only 'page' parameter (no pageLimit!)
        
        Args:
            endpoint: API endpoint path
            data_key: Key in response containing the records array
        
        Returns:
            List of all records across all pages
        """
        all_records = []
        page = 1
        PAGE_SIZE = 25  # Fixed by API

        while True:
            data = self.fetch_json(endpoint, page)

            if not data:
                break

            # Get total count on first page
            total_count = data.get('total', 0)
            if page == 1 and total_count > 0:
                expected_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
                print(f"      Total records: {total_count:,} ({expected_pages} pages @ 25/page)")

            # Get records for this page - FIX: Check multiple possible field names
            # API returns different field names for same data across endpoints
            records = None

            # Try primary field name first
            if data_key in data:
                records = data[data_key]
            # Try common alternatives
            elif 'data' in data:
                records = data['data']
            # Try singular/plural variations
            elif data_key.endswith('s') and data_key[:-1] in data:
                records = data[data_key[:-1]]  # e.g., 'allpatches' → 'allpatch'
            elif data_key + 's' in data:
                records = data[data_key + 's']  # e.g., 'patch' → 'patches'
            # Try common field name patterns for specific endpoint types
            elif 'allpatches' in data_key or 'patches' in data_key:
                # Patch endpoints: try patches/allpatches
                records = data.get('patches', data.get('allpatches', []))
            elif 'allsystems' in data_key or 'systems' in data_key or 'computers' in data_key:
                # System endpoints: try computers/systems/allsystems
                records = data.get('computers', data.get('systems', data.get('allsystems', [])))
            elif 'policies' in data_key or 'deploymentpolicies' in data_key:
                # Policy endpoints: try deploymenttemplate/policies
                records = data.get('deploymenttemplate', data.get('policies', []))
            else:
                records = []

            if not records:
                break

            all_records.extend(records)

            # Progress update every 50 pages
            if page % 50 == 0:
                print(f"      Progress: {len(all_records):,}/{total_count:,} records ({page} pages)")

            # Check if we've got all records
            if len(all_records) >= total_count:
                break

            page += 1
            time.sleep(0.25)  # Rate limiting

        print(f"      ✅ Fetched {len(all_records):,} records from {page} pages")
        return all_records

    def extract_endpoint_paginated(self, name: str, endpoint: str, table: str,
                                   extract_fn, data_key: str) -> int:
        """
        Extract endpoint with pagination support.
        
        Args:
            name: Display name
            endpoint: API endpoint
            table: Database table name
            extract_fn: Function to extract and insert data
            data_key: Key containing records array in response
        
        Returns:
            Number of records extracted
        """
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

    def extract_endpoint_simple(self, name: str, endpoint: str, table: str, extract_fn) -> int:
        """
        Extract endpoint without pagination (single response).
        
        Args:
            name: Display name
            endpoint: API endpoint
            table: Database table name
            extract_fn: Function to extract and insert data
        
        Returns:
            Number of records extracted
        """
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

    def extract_all(self):
        """Extract data from all 15 working endpoints"""
        self.start_extraction_run()

        total_records = 0
        endpoints_extracted = 0
        errors = []

        print("=" * 80)
        print("PMP COMPLETE INTELLIGENCE EXTRACTION (FIXED PAGINATION)")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Extraction ID: {self.extraction_id}")
        print()

        # ===== EXTRACT ALL ENDPOINTS =====

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

            # 3. All Patches (5,217) - PAGINATED
            count = self.extract_endpoint_paginated(
                "3. All Patches (Active)",
                "/api/1.4/patch/allpatches",
                "all_patches",
                self.extract_all_patches,
                "allpatches"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 5. Supported Patches (364,673 - this will take time!) - PAGINATED
            print("\n⚠️  Supported Patches: 364,673 records - this will take ~30 minutes...")
            count = self.extract_endpoint_paginated(
                "5. Supported Patches (Master Catalog)",
                "/api/1.4/patch/supportedpatches",
                "supported_patches",
                self.extract_supported_patches,
                "supportedpatches"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 7. All Systems (3,364) - PAGINATED
            count = self.extract_endpoint_paginated(
                "7. All Systems",
                "/api/1.4/patch/allsystems",
                "all_systems",
                self.extract_all_systems,
                "allsystems"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 9. Deployment Policies (92) - PAGINATED
            count = self.extract_endpoint_paginated(
                "9. Deployment Policies",
                "/api/1.4/patch/deploymentpolicies",
                "deployment_policies",
                self.extract_deployment_policies,
                "deploymentpolicies"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 10. Health Policy (non-paginated)
            count = self.extract_endpoint_simple(
                "10. Health Policy",
                "/api/1.4/patch/healthpolicy",
                "health_policy",
                self.extract_simple_json
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 11. View Configurations (225) - PAGINATED
            count = self.extract_endpoint_paginated(
                "11. View Configurations",
                "/api/1.4/patch/viewconfig",
                "view_configurations",
                self.extract_view_configurations,
                "viewconfig"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 12. Approval Settings (non-paginated)
            count = self.extract_endpoint_simple(
                "12. Approval Settings",
                "/api/1.4/patch/approvalsettings",
                "approval_settings",
                self.extract_simple_json
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 13. Scan Details (3,364) - PAGINATED
            count = self.extract_endpoint_paginated(
                "13. Scan Details",
                "/api/1.4/patch/scandetails",
                "scan_details",
                self.extract_scan_details,
                "scandetails"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 14. Installed Patches (3,505) - PAGINATED
            count = self.extract_endpoint_paginated(
                "14. Installed Patches",
                "/api/1.4/patch/installedpatches",
                "installed_patches",
                self.extract_installed_patches,
                "installedpatches"
            )
            total_records += count
            endpoints_extracted += 1
            time.sleep(0.5)

            # 15. Missing Patches (1,712) - PAGINATED
            count = self.extract_endpoint_paginated(
                "15. Missing Patches",
                "/api/1.4/patch/missingpatches",
                "missing_patches",
                self.extract_missing_patches,
                "missingpatches"
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
        print(f"Endpoints extracted: {endpoints_extracted}/11")
        print(f"Total records: {total_records:,}")
        print(f"Database: {self.db_path}")
        print()

        if errors:
            print("⚠️  Errors encountered:")
            for error in errors:
                print(f"   - {error}")

    # ===== EXTRACTION FUNCTIONS =====

    def extract_simple_json(self, data: Dict, table: str) -> int:
        """Extract simple JSON data (summary, policies, settings)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Determine column names based on table
        if table == "patch_summary":
            cursor.execute("""
                INSERT OR REPLACE INTO patch_summary (extraction_id, summary_data, extracted_at)
                VALUES (?, ?, ?)
            """, (self.extraction_id, json.dumps(data), datetime.now().isoformat()))
        elif table == "health_policy":
            cursor.execute("""
                INSERT OR REPLACE INTO health_policy (extraction_id, policy_data, extracted_at)
                VALUES (?, ?, ?)
            """, (self.extraction_id, json.dumps(data), datetime.now().isoformat()))
        elif table == "approval_settings":
            cursor.execute("""
                INSERT OR REPLACE INTO approval_settings (extraction_id, settings_data, extracted_at)
                VALUES (?, ?, ?)
            """, (self.extraction_id, json.dumps(data), datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return 1

    def extract_all_patches(self, patches: List[Dict], table: str) -> int:
        """Extract all patches data from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for patch in patches:
            cursor.execute("""
                INSERT OR REPLACE INTO all_patches
                (patch_id, extraction_id, bulletin_id, update_name, platform,
                 patch_released_time, patch_size, patch_noreboot, installed,
                 raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patch.get('update_id'),
                self.extraction_id,
                patch.get('bulletin_id'),
                patch.get('update_name'),
                patch.get('platform'),
                patch.get('patch_released_time'),
                patch.get('patch_size'),
                patch.get('patch_noreboot'),
                patch.get('installed'),
                json.dumps(patch),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(patches)

    def extract_supported_patches(self, patches: List[Dict], table: str) -> int:
        """Extract supported patches (master catalog) from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        batch_size = 1000
        for i in range(0, len(patches), batch_size):
            batch = patches[i:i+batch_size]

            for patch in batch:
                cursor.execute("""
                    INSERT OR REPLACE INTO supported_patches
                    (update_id, extraction_id, bulletin_id, patch_lang,
                     patch_updated_time, is_superceded, raw_data, extracted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patch.get('update_id'),
                    self.extraction_id,
                    patch.get('bulletin_id'),
                    patch.get('patch_lang'),
                    patch.get('patch_updated_time'),
                    patch.get('is_superceded'),
                    json.dumps(patch),
                    datetime.now().isoformat()
                ))

            conn.commit()
            print(f"      DB Write: {min(i+batch_size, len(patches)):,}/{len(patches):,} patches...")

        conn.close()
        return len(patches)

    def extract_all_systems(self, systems: List[Dict], table: str) -> int:
        """Extract all systems data from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for system in systems:
            cursor.execute("""
                INSERT OR REPLACE INTO all_systems
                (resource_id, extraction_id, resource_health_status, os_platform_name,
                 branch_office_id, last_patched_time, total_driver_patches,
                 missing_bios_patches, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system.get('resource_id'),
                self.extraction_id,
                system.get('resource_health_status'),
                system.get('os_platform_name'),
                system.get('branch_office_id'),
                system.get('last_patched_time'),
                system.get('total_driver_patches'),
                system.get('missing_bios_patches'),
                json.dumps(system),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(systems)

    def extract_deployment_policies(self, policies: List[Dict], table: str) -> int:
        """Extract deployment policies from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for policy in policies:
            cursor.execute("""
                INSERT OR REPLACE INTO deployment_policies
                (template_id, extraction_id, template_name, creation_time,
                 modified_time, is_template_alive, set_as_default, user_id,
                 raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                policy.get('template_id'),
                self.extraction_id,
                policy.get('template_name'),
                policy.get('creation_time'),
                policy.get('modified_time'),
                policy.get('is_template_alive'),
                policy.get('set_as_default'),
                policy.get('user_id'),
                json.dumps(policy),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(policies)

    def extract_view_configurations(self, configs: List[Dict], table: str) -> int:
        """Extract view configurations from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for config in configs:
            cursor.execute("""
                INSERT OR REPLACE INTO view_configurations
                (config_id, extraction_id, collection_id, total_target_count,
                 os_platform_name, collection_platform_id, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.get('config_id'),
                self.extraction_id,
                config.get('collection_id'),
                config.get('total_target_count'),
                config.get('os_platform_name'),
                config.get('collection_platform_id'),
                json.dumps(config),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(configs)

    def extract_scan_details(self, systems: List[Dict], table: str) -> int:
        """Extract scan details from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for system in systems:
            cursor.execute("""
                INSERT OR REPLACE INTO scan_details
                (resource_id, extraction_id, resource_health_status, os_platform_name,
                 branch_office_id, agent_installed_on, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system.get('resource_id'),
                self.extraction_id,
                system.get('resource_health_status'),
                system.get('os_platform_name'),
                system.get('branch_office_id'),
                system.get('agent_installed_on'),
                json.dumps(system),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(systems)

    def extract_installed_patches(self, patches: List[Dict], table: str) -> int:
        """Extract installed patches from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for patch in patches:
            cursor.execute("""
                INSERT OR REPLACE INTO installed_patches
                (patch_id, extraction_id, bulletin_id, update_name, platform,
                 patch_released_time, patch_noreboot, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patch.get('update_id'),
                self.extraction_id,
                patch.get('bulletin_id'),
                patch.get('update_name'),
                patch.get('platform'),
                patch.get('patch_released_time'),
                patch.get('patch_noreboot'),
                json.dumps(patch),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(patches)

    def extract_missing_patches(self, patches: List[Dict], table: str) -> int:
        """Extract missing patches from records list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for patch in patches:
            cursor.execute("""
                INSERT OR REPLACE INTO missing_patches
                (patch_id, extraction_id, bulletin_id, update_name, platform,
                 patch_released_time, patch_noreboot, raw_data, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patch.get('update_id'),
                self.extraction_id,
                patch.get('bulletin_id'),
                patch.get('update_name'),
                patch.get('platform'),
                patch.get('patch_released_time'),
                patch.get('patch_noreboot'),
                json.dumps(patch),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()
        return len(patches)


def main():
    """Main entry point"""
    extractor = PMPCompleteIntelligenceExtractor()
    extractor.extract_all()


if __name__ == "__main__":
    main()
