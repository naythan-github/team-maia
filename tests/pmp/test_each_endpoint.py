#!/usr/bin/env python3
"""
Test EACH API endpoint individually with resilient fetch logic
Only proceed to next endpoint if current one passes
"""

import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
import requests


class EndpointTester:
    """Test each endpoint individually with retry logic"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.base_url = self.oauth_manager.server_url
        self.passed = []
        self.failed = []

    def fetch_with_retry(self, endpoint: str, page: int = None, max_retries: int = 3):
        """Fetch with retry logic - same as extractor v3"""
        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.base_url}{endpoint}"
                params = {'page': page} if page is not None else None

                response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"      ⚠️  Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        print(f"      ⚠️  Server error {response.status_code}. Retry {attempt}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {'error': f'HTTP {response.status_code} after {max_retries} retries'}
                else:
                    return {'error': f'HTTP {response.status_code}'}

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"      ⚠️  Timeout. Retry {attempt}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {'error': f'Timeout after {max_retries} attempts'}
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"      ⚠️  Connection error. Retry {attempt}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {'error': f'Connection failed after {max_retries} attempts'}
            except Exception as e:
                return {'error': str(e)}

        return {'error': 'Max retries exceeded'}

    def test_endpoint(self, name: str, endpoint: str, data_key: str = None, is_paginated: bool = False):
        """Test a single endpoint"""
        print(f"\n{'='*80}")
        print(f"Testing: {name}")
        print(f"Endpoint: {endpoint}")
        print(f"{'='*80}")

        # Test first page or single response
        data = self.fetch_with_retry(endpoint, page=1 if is_paginated else None)

        if 'error' in data:
            print(f"❌ FAILED: {data['error']}")
            self.failed.append({'name': name, 'endpoint': endpoint, 'error': data['error']})
            return False

        # Extract message_response wrapper if present
        if 'message_response' in data:
            data = data['message_response']

        # Validate response structure
        if is_paginated:
            if not data_key:
                print(f"❌ FAILED: No data_key specified for paginated endpoint")
                self.failed.append({'name': name, 'endpoint': endpoint, 'error': 'Missing data_key'})
                return False

            records = data.get(data_key, [])
            total = data.get('total', 0)

            if total == 0:
                print(f"⚠️  WARNING: Endpoint returned 0 total records")

            print(f"✅ SUCCESS: Page 1 returned {len(records)} records (total: {total:,})")
            print(f"   Sample fields: {list(records[0].keys())[:8] if records else 'N/A'}")

            # Test page 2 to verify pagination works
            if total > 25:
                print(f"   Testing page 2...")
                data2 = self.fetch_with_retry(endpoint, page=2)
                if 'error' in data2:
                    print(f"   ⚠️  Page 2 failed: {data2['error']}")
                else:
                    if 'message_response' in data2:
                        data2 = data2['message_response']
                    records2 = data2.get(data_key, [])
                    print(f"   ✅ Page 2 returned {len(records2)} records")
        else:
            # Non-paginated endpoint
            if isinstance(data, dict):
                print(f"✅ SUCCESS: Single object response")
                print(f"   Fields: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"✅ SUCCESS: Array response with {len(data)} items")
            else:
                print(f"⚠️  WARNING: Unexpected response type: {type(data)}")

        self.passed.append({'name': name, 'endpoint': endpoint})
        return True

    def run_all_tests(self):
        """Test all 15 working endpoints"""
        print("\n" + "="*80)
        print("PMP API ENDPOINT VALIDATION - Testing Each Endpoint Individually")
        print("="*80)

        # Endpoint definitions (from API catalog)
        endpoints = [
            {'name': '1. Patch Summary', 'endpoint': '/api/1.4/patch/summary', 'paginated': False},
            {'name': '3. All Patches', 'endpoint': '/api/1.4/patch/allpatches', 'data_key': 'patches', 'paginated': True},
            {'name': '5. Supported Patches', 'endpoint': '/api/1.4/patch/supportedpatches', 'data_key': 'supportedpatch', 'paginated': True},
            {'name': '7. All Systems', 'endpoint': '/api/1.4/patch/allsystems', 'data_key': 'computers', 'paginated': True},
            {'name': '9. Deployment Policies', 'endpoint': '/api/1.4/patch/deploymentpolicies', 'data_key': 'deploymenttemplate', 'paginated': True},
            {'name': '10. Health Policy', 'endpoint': '/api/1.4/patch/healthpolicy', 'paginated': False},
            {'name': '11. View Configurations', 'endpoint': '/api/1.4/patch/viewconfig', 'data_key': 'viewconfig', 'paginated': True},
            {'name': '12. Approval Settings', 'endpoint': '/api/1.4/patch/approvalsettings', 'paginated': False},
            {'name': '13. Scan Details', 'endpoint': '/api/1.4/patch/scandetails', 'data_key': 'computers', 'paginated': True},
            {'name': '14. Installed Patches', 'endpoint': '/api/1.4/patch/installedpatches', 'data_key': 'patches', 'paginated': True},
            {'name': '15. Missing Patches', 'endpoint': '/api/1.4/patch/missingpatches', 'data_key': 'patches', 'paginated': True},
            {'name': '22. SoM Summary', 'endpoint': '/api/1.4/som/summary', 'paginated': False},
            {'name': '23. SoM Computers', 'endpoint': '/api/1.4/som/computers', 'data_key': 'computers', 'paginated': True},
            {'name': '24. SoM Remote Office', 'endpoint': '/api/1.4/som/remoteoffice', 'data_key': 'remoteoffice', 'paginated': True},
        ]

        for ep in endpoints:
            success = self.test_endpoint(
                name=ep['name'],
                endpoint=ep['endpoint'],
                data_key=ep.get('data_key'),
                is_paginated=ep.get('paginated', False)
            )

            if not success:
                print(f"\n🛑 STOPPING: Endpoint failed. Fix issue before continuing.")
                break

            # Small delay between tests
            time.sleep(0.5)

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ PASSED: {len(self.passed)} endpoints")
        print(f"❌ FAILED: {len(self.failed)} endpoints")

        if self.failed:
            print("\nFailed Endpoints:")
            for f in self.failed:
                print(f"  - {f['name']}: {f['error']}")
            return False
        else:
            print("\n🎉 ALL ENDPOINTS VALIDATED - Ready for full extraction!")
            return True


if __name__ == '__main__':
    tester = EndpointTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
