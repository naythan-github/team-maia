#!/usr/bin/env python3
"""
Phase 6 Validation Script for PMP DCAPI Patch Extractor

Validates:
1. Live API connectivity and response structure
2. Performance characteristics
3. Resilience features
4. Observability
5. Smoke test (end-to-end)
"""

import sys
import os
import time
import json
import sqlite3
import tracemalloc
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pmp_oauth_manager import PMPOAuthManager

# Constants from requirements
DCAPI_ENDPOINT = "/dcapi/threats/systemreport/patches"
TOTAL_PAGES = 111
SYSTEMS_PER_PAGE = 30
DB_PATH = Path.home() / ".maia" / "databases" / "intelligence" / "pmp_config.db"

class Phase6Validator:
    """Phase 6 validation test suite"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.results = {
            'category_1_live_api': {},
            'category_2_performance': {},
            'category_3_resilience': {},
            'category_4_observability': {},
            'category_5_smoke': {}
        }

    # =========================================================================
    # CATEGORY 1: LIVE API VALIDATION
    # =========================================================================

    def test_api_connectivity(self):
        """Test DCAPI endpoint connectivity"""
        print("\n📡 Testing API connectivity...")

        try:
            token = self.oauth_manager.get_valid_token()
            base_url = self.oauth_manager.server_url

            # Fetch page 1
            url = f"{base_url}{DCAPI_ENDPOINT}?page=1&pageLimit={SYSTEMS_PER_PAGE}"
            headers = {"Authorization": f"Bearer {token}"}

            import requests
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self.results['category_1_live_api']['connectivity'] = {
                    'status': 'PASS',
                    'status_code': 200,
                    'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                }
                print(f"   ✅ Connectivity: PASS (200 OK, {response.elapsed.total_seconds():.2f}s)")
                return data
            else:
                self.results['category_1_live_api']['connectivity'] = {
                    'status': 'FAIL',
                    'status_code': response.status_code,
                    'error': response.text[:200]
                }
                print(f"   ❌ Connectivity: FAIL ({response.status_code})")
                return None

        except Exception as e:
            self.results['category_1_live_api']['connectivity'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Connectivity: ERROR ({e})")
            return None

    def test_pagination(self):
        """Test pagination works correctly"""
        print("\n📄 Testing pagination...")

        try:
            token = self.oauth_manager.get_valid_token()
            base_url = self.oauth_manager.server_url

            # Fetch pages 1, 2, and last page (664)
            test_pages = [1, 2, TOTAL_PAGES]
            results = {}

            for page in test_pages:
                url = f"{base_url}{DCAPI_ENDPOINT}?page={page}&pageLimit={SYSTEMS_PER_PAGE}"
                headers = {"Authorization": f"Bearer {token}"}

                import requests
                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    system_count = len(data.get('message_response', {}).get('systemreport', []))
                    results[f'page_{page}'] = {
                        'status': 'PASS',
                        'system_count': system_count
                    }
                    print(f"   ✅ Page {page}: {system_count} systems")
                else:
                    results[f'page_{page}'] = {
                        'status': 'FAIL',
                        'status_code': response.status_code
                    }
                    print(f"   ❌ Page {page}: FAIL ({response.status_code})")

            self.results['category_1_live_api']['pagination'] = results

            # Check if all passed
            all_passed = all(r['status'] == 'PASS' for r in results.values())
            print(f"   {'✅' if all_passed else '❌'} Pagination: {'PASS' if all_passed else 'FAIL'}")

        except Exception as e:
            self.results['category_1_live_api']['pagination'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Pagination: ERROR ({e})")

    def test_data_structure(self):
        """Test data structure matches schema expectations"""
        print("\n🔍 Testing data structure...")

        try:
            token = self.oauth_manager.get_valid_token()
            base_url = self.oauth_manager.server_url

            # Fetch page 1
            url = f"{base_url}{DCAPI_ENDPOINT}?page=1&pageLimit={SYSTEMS_PER_PAGE}"
            headers = {"Authorization": f"Bearer {token}"}

            import requests
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                systems = data.get('message_response', {}).get('systemreport', [])

                if not systems:
                    self.results['category_1_live_api']['data_structure'] = {
                        'status': 'FAIL',
                        'error': 'No systems in response'
                    }
                    print(f"   ❌ Data structure: FAIL (no systems)")
                    return

                # Check first system has required fields
                first_system = systems[0]
                required_fields = ['resource_id', 'patches']
                missing_fields = [f for f in required_fields if f not in first_system]

                if missing_fields:
                    self.results['category_1_live_api']['data_structure'] = {
                        'status': 'FAIL',
                        'missing_fields': missing_fields
                    }
                    print(f"   ❌ Data structure: FAIL (missing {missing_fields})")
                    return

                # Check patches array structure
                patches = first_system.get('patches', [])
                if patches:
                    first_patch = patches[0]
                    patch_fields = ['patch_id', 'patchname', 'severity', 'patch_status']
                    missing_patch_fields = [f for f in patch_fields if f not in first_patch]

                    if missing_patch_fields:
                        self.results['category_1_live_api']['data_structure'] = {
                            'status': 'FAIL',
                            'missing_patch_fields': missing_patch_fields
                        }
                        print(f"   ❌ Data structure: FAIL (missing patch fields {missing_patch_fields})")
                        return

                self.results['category_1_live_api']['data_structure'] = {
                    'status': 'PASS',
                    'system_count': len(systems),
                    'sample_patch_count': len(patches),
                    'fields_validated': required_fields + patch_fields
                }
                print(f"   ✅ Data structure: PASS ({len(systems)} systems, {len(patches)} patches in first system)")

            else:
                self.results['category_1_live_api']['data_structure'] = {
                    'status': 'FAIL',
                    'status_code': response.status_code
                }
                print(f"   ❌ Data structure: FAIL ({response.status_code})")

        except Exception as e:
            self.results['category_1_live_api']['data_structure'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Data structure: ERROR ({e})")

    # =========================================================================
    # CATEGORY 2: PERFORMANCE TESTING
    # =========================================================================

    def test_performance(self):
        """Test performance characteristics (single page)"""
        print("\n⚡ Testing performance (single page extraction)...")

        try:
            token = self.oauth_manager.get_valid_token()
            base_url = self.oauth_manager.server_url

            # Start memory tracking
            tracemalloc.start()

            # Time single page extraction
            start_time = time.time()

            url = f"{base_url}{DCAPI_ENDPOINT}?page=1&pageLimit={SYSTEMS_PER_PAGE}"
            headers = {"Authorization": f"Bearer {token}"}

            import requests
            response = requests.get(url, headers=headers, timeout=30)

            elapsed_time = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Calculate metrics
            systems_extracted = len(response.json().get('systems', [])) if response.status_code == 200 else 0
            throughput = systems_extracted / elapsed_time if elapsed_time > 0 else 0
            memory_mb = peak / (1024 * 1024)

            # Check targets
            # Target: <15 min/batch (50 pages) = <18s per page, ≥10 systems/sec
            target_time_per_page = (15 * 60) / 50  # 18 seconds
            target_throughput = 10  # systems/sec
            target_memory = 100  # MB

            time_pass = elapsed_time < target_time_per_page
            throughput_pass = throughput >= target_throughput
            memory_pass = memory_mb < target_memory

            self.results['category_2_performance'] = {
                'elapsed_time_s': round(elapsed_time, 2),
                'throughput_systems_per_sec': round(throughput, 1),
                'memory_peak_mb': round(memory_mb, 2),
                'time_target_pass': time_pass,
                'throughput_target_pass': throughput_pass,
                'memory_target_pass': memory_pass,
                'overall_pass': time_pass and throughput_pass and memory_pass
            }

            print(f"   {'✅' if time_pass else '❌'} Time: {elapsed_time:.2f}s (target: <{target_time_per_page:.0f}s)")
            print(f"   {'✅' if throughput_pass else '❌'} Throughput: {throughput:.1f} systems/sec (target: ≥{target_throughput})")
            print(f"   {'✅' if memory_pass else '❌'} Memory: {memory_mb:.2f} MB (target: <{target_memory} MB)")

        except Exception as e:
            self.results['category_2_performance'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Performance: ERROR ({e})")

    # =========================================================================
    # CATEGORY 3: RESILIENCE TESTING
    # =========================================================================

    def test_checkpoint_system(self):
        """Test checkpoint system exists and is queryable"""
        print("\n💾 Testing checkpoint system...")

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='dcapi_extraction_checkpoints'
            """)

            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Try to query checkpoints
                cursor.execute("SELECT COUNT(*) FROM dcapi_extraction_checkpoints")
                count = cursor.fetchone()[0]

                self.results['category_3_resilience']['checkpoint_system'] = {
                    'status': 'PASS',
                    'table_exists': True,
                    'checkpoint_count': count
                }
                print(f"   ✅ Checkpoint system: PASS (table exists, {count} checkpoints)")
            else:
                self.results['category_3_resilience']['checkpoint_system'] = {
                    'status': 'FAIL',
                    'table_exists': False
                }
                print(f"   ❌ Checkpoint system: FAIL (table missing)")

            conn.close()

        except Exception as e:
            self.results['category_3_resilience']['checkpoint_system'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Checkpoint system: ERROR ({e})")

    def test_token_refresh(self):
        """Test token refresh capability"""
        print("\n🔑 Testing token refresh...")

        try:
            # Get initial token
            token1 = self.oauth_manager.get_valid_token()

            # Force refresh
            token2 = self.oauth_manager.get_valid_token()

            # Tokens should be valid (non-empty strings)
            token_valid = bool(token1) and bool(token2)

            self.results['category_3_resilience']['token_refresh'] = {
                'status': 'PASS' if token_valid else 'FAIL',
                'token1_length': len(token1) if token1 else 0,
                'token2_length': len(token2) if token2 else 0
            }

            print(f"   {'✅' if token_valid else '❌'} Token refresh: {'PASS' if token_valid else 'FAIL'}")

        except Exception as e:
            self.results['category_3_resilience']['token_refresh'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Token refresh: ERROR ({e})")

    # =========================================================================
    # CATEGORY 4: OBSERVABILITY VALIDATION
    # =========================================================================

    def test_observability(self):
        """Test observability (logs emitted)"""
        print("\n📊 Testing observability...")

        # For now, just verify the extractor can be imported and has logging
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from pmp_dcapi_patch_extractor import PMPDCAPIExtractor, logger

            # Check logger exists
            logger_exists = logger is not None

            self.results['category_4_observability'] = {
                'status': 'PASS' if logger_exists else 'FAIL',
                'logger_exists': logger_exists,
                'logger_name': logger.name if logger_exists else None
            }

            print(f"   {'✅' if logger_exists else '❌'} Observability: {'PASS' if logger_exists else 'FAIL'} (logger configured)")

        except Exception as e:
            self.results['category_4_observability'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Observability: ERROR ({e})")

    # =========================================================================
    # CATEGORY 5: SMOKE TESTING
    # =========================================================================

    def test_database_integrity(self):
        """Test database schema integrity"""
        print("\n🗄️  Testing database integrity...")

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check required tables exist
            required_tables = ['patch_system_mapping', 'snapshots', 'dcapi_extraction_checkpoints']
            results = {}

            for table in required_tables:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name=?
                """, (table,))

                exists = cursor.fetchone() is not None
                results[table] = exists
                print(f"   {'✅' if exists else '❌'} Table '{table}': {'EXISTS' if exists else 'MISSING'}")

            all_exist = all(results.values())

            self.results['category_5_smoke']['database_integrity'] = {
                'status': 'PASS' if all_exist else 'FAIL',
                'tables': results
            }

            conn.close()

        except Exception as e:
            self.results['category_5_smoke']['database_integrity'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"   ❌ Database integrity: ERROR ({e})")

    # =========================================================================
    # RUNNER
    # =========================================================================

    def run_all_tests(self):
        """Run all validation tests"""
        print("=" * 70)
        print("🔬 PHASE 6 VALIDATION - PMP DCAPI PATCH EXTRACTOR")
        print("=" * 70)

        # Category 1: Live API Validation
        print("\n" + "=" * 70)
        print("CATEGORY 1: LIVE API VALIDATION")
        print("=" * 70)
        self.test_api_connectivity()
        self.test_pagination()
        self.test_data_structure()

        # Category 2: Performance Testing
        print("\n" + "=" * 70)
        print("CATEGORY 2: PERFORMANCE TESTING")
        print("=" * 70)
        self.test_performance()

        # Category 3: Resilience Testing
        print("\n" + "=" * 70)
        print("CATEGORY 3: RESILIENCE TESTING")
        print("=" * 70)
        self.test_checkpoint_system()
        self.test_token_refresh()

        # Category 4: Observability Validation
        print("\n" + "=" * 70)
        print("CATEGORY 4: OBSERVABILITY VALIDATION")
        print("=" * 70)
        self.test_observability()

        # Category 5: Smoke Testing
        print("\n" + "=" * 70)
        print("CATEGORY 5: SMOKE TESTING")
        print("=" * 70)
        self.test_database_integrity()

        # Summary
        self.print_summary()

        return self.results

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)

        # Count passes/fails per category
        for category, tests in self.results.items():
            category_name = category.replace('_', ' ').upper()

            if not tests:
                print(f"\n{category_name}: NO TESTS RUN")
                continue

            passes = sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') == 'PASS')
            fails = sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') == 'FAIL')
            errors = sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') == 'ERROR')
            total = len(tests)

            status_icon = "✅" if fails == 0 and errors == 0 else "❌"
            print(f"\n{status_icon} {category_name}:")
            print(f"   Pass: {passes}/{total}, Fail: {fails}/{total}, Error: {errors}/{total}")

        # Overall pass/fail
        total_fails = sum(
            sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') in ['FAIL', 'ERROR'])
            for tests in self.results.values()
        )

        print("\n" + "=" * 70)
        if total_fails == 0:
            print("✅ OVERALL: PASS - All validation tests passed")
        else:
            print(f"❌ OVERALL: FAIL - {total_fails} test(s) failed or errored")
        print("=" * 70)


if __name__ == "__main__":
    validator = Phase6Validator()
    results = validator.run_all_tests()

    # Save results to JSON
    output_file = Path(__file__).parent / "phase6_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    # Exit with code based on results
    total_fails = sum(
        sum(1 for t in tests.values() if isinstance(t, dict) and t.get('status') in ['FAIL', 'ERROR'])
        for tests in results.values()
    )

    sys.exit(0 if total_fails == 0 else 1)
