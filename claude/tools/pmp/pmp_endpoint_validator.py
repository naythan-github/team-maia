#!/usr/bin/env python3
"""
PMP Endpoint Validator - Test All Known Endpoints

Tests all 14 PMP REST API endpoints with sample extractions (first page only)
to confirm what data is available and validate all bug fixes.

Usage:
    python3 pmp_endpoint_validator.py
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager import PMPOAuthManager


class PMPEndpointValidator:
    """Validate all PMP REST API endpoints with sample extractions"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.base_url = self.oauth_manager.server_url
        self.results = []

    def fetch_json(self, endpoint: str, page: Optional[int] = None,
                   max_retries: int = 3) -> Optional[Dict]:
        """
        Fetch JSON data from API endpoint with retry logic.
        Includes all bug fixes: Zoho auth, HTML detection, JSON parse handling.
        """
        import requests

        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {"Authorization": f"Zoho-oauthtoken {token}"}  # FIX: Zoho format
                url = f"{self.base_url}{endpoint}"

                # Build params
                params = {'page': page} if page is not None else None

                response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

                if response.status_code == 200:
                    # FIX: Check for HTML throttling page
                    content = response.text
                    if content.strip().startswith('<') or '<!DOCTYPE' in content or '<html' in content.lower():
                        print(f"   ⚠️  HTML throttling response. Waiting 60s...")
                        import time
                        time.sleep(60)
                        continue

                    try:
                        data = response.json()
                        # Extract message_response wrapper if present
                        if 'message_response' in data:
                            return data['message_response']
                        return data
                    except ValueError as e:
                        # FIX: JSON parse error handling
                        print(f"   ⚠️  JSON parse error. Waiting 60s...")
                        import time
                        time.sleep(60)
                        continue

                elif response.status_code == 401:
                    return {"error": "Unauthorized", "status_code": 401}
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"   ⚠️  Rate limited. Waiting {retry_after}s...")
                    import time
                    time.sleep(retry_after)
                    continue
                else:
                    return {"error": f"HTTP {response.status_code}", "status_code": response.status_code}

            except Exception as e:
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return {"error": str(e), "status_code": 0}

        return None

    def find_data_field(self, data: Dict, expected_keys: List[str]) -> Tuple[Optional[str], Optional[List]]:
        """
        Find which field contains the data array.
        Returns: (field_name, records)

        FIX: Multi-field checking for API response variability
        """
        # Try expected keys first
        for key in expected_keys:
            if key in data and isinstance(data.get(key), list):
                return (key, data[key])

        # Try common fallbacks
        for fallback in ['data', 'records', 'items']:
            if fallback in data and isinstance(data.get(fallback), list):
                return (fallback, data[fallback])

        return (None, None)

    def test_endpoint(self, name: str, endpoint: str, expected_keys: List[str],
                     is_paginated: bool = True) -> Dict:
        """Test a single endpoint and return results"""
        print(f"\n{'='*80}")
        print(f"Testing: {name}")
        print(f"Endpoint: {endpoint}")
        print(f"Type: {'Paginated' if is_paginated else 'Simple'}")
        print(f"{'='*80}")

        result = {
            'name': name,
            'endpoint': endpoint,
            'type': 'paginated' if is_paginated else 'simple',
            'expected_keys': expected_keys,
            'status': 'unknown',
            'tested_at': datetime.now().isoformat()
        }

        # Fetch first page (or single response)
        data = self.fetch_json(endpoint, page=1 if is_paginated else None)

        if data is None:
            result['status'] = 'failed'
            result['error'] = 'No response from API'
            print("❌ FAILED: No response")
            return result

        if 'error' in data:
            result['status'] = 'failed'
            result['error'] = data['error']
            result['status_code'] = data.get('status_code')
            print(f"❌ FAILED: {data['error']} (HTTP {data.get('status_code')})")
            return result

        # Analyze response
        result['response_fields'] = list(data.keys())
        result['total'] = data.get('total', 'N/A')

        if is_paginated:
            # Find data field
            field_name, records = self.find_data_field(data, expected_keys)

            if field_name and records:
                result['status'] = 'success'
                result['data_field'] = field_name
                result['sample_count'] = len(records)
                result['sample_record'] = records[0] if records else None

                print(f"✅ SUCCESS")
                print(f"   Total records: {result['total']:,}")
                print(f"   Data field: '{field_name}'")
                print(f"   Sample size: {len(records)} records")
                print(f"   All fields: {result['response_fields']}")
                if records:
                    print(f"   Sample keys: {list(records[0].keys())[:10]}...")
            else:
                result['status'] = 'empty'
                result['error'] = f"No data found in expected fields: {expected_keys}"
                print(f"⚠️  EMPTY: Found {result['total']} total but no data in: {expected_keys}")
                print(f"   Available fields: {result['response_fields']}")
        else:
            # Simple (non-paginated) response
            result['status'] = 'success'
            result['sample_record'] = data
            print(f"✅ SUCCESS")
            print(f"   Response fields: {result['response_fields']}")
            print(f"   Top-level keys: {list(data.keys())[:20]}")

        return result

    def run_validation(self):
        """Test all known PMP endpoints"""
        print("="*80)
        print("PMP ENDPOINT VALIDATION - COMPREHENSIVE TEST")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Define all endpoints from API documentation
        endpoints = [
            # Paginated endpoints
            ("1. Patch Summary", "/api/1.4/patch/summary", [], False),
            ("2. All Patches", "/api/1.4/patch/allpatches", ['allpatches', 'patches', 'data'], True),
            ("3. Supported Patches", "/api/1.4/patch/supportedpatches", ['supportedpatch', 'supportedpatches', 'patches', 'data'], True),
            ("4. All Systems", "/api/1.4/patch/allsystems", ['allsystems', 'computers', 'systems', 'data'], True),
            ("5. Deployment Policies", "/api/1.4/patch/deploymentpolicies", ['deploymentpolicies', 'deploymenttemplate', 'policies', 'data'], True),
            ("6. Health Policy", "/api/1.4/patch/healthpolicy", [], False),
            ("7. View Configurations", "/api/1.4/patch/viewconfig", ['viewconfig', 'configs', 'data'], True),
            ("8. Approval Settings", "/api/1.4/patch/approvalsettings", [], False),
            ("9. Scan Details", "/api/1.4/patch/scandetails", ['scandetails', 'computers', 'systems', 'data'], True),
            ("10. Installed Patches", "/api/1.4/patch/installedpatches", ['installedpatches', 'patches', 'data'], True),
            ("11. Missing Patches", "/api/1.4/patch/missingpatches", ['missingpatches', 'patches', 'data'], True),
            ("12. SoM Summary", "/api/1.4/som/summary", [], False),
            ("13. SoM Computers", "/api/1.4/som/computers", ['computers', 'systems', 'data'], True),
            ("14. SoM Remote Office", "/api/1.4/som/remoteoffice", ['remoteoffice', 'offices', 'data'], True),
        ]

        # Test each endpoint
        for name, endpoint, expected_keys, is_paginated in endpoints:
            result = self.test_endpoint(name, endpoint, expected_keys, is_paginated)
            self.results.append(result)

            # Rate limiting between tests
            import time
            time.sleep(1.0)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)

        success = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'failed']
        empty = [r for r in self.results if r['status'] == 'empty']

        print(f"\n📊 Results:")
        print(f"   ✅ Success: {len(success)}/{len(self.results)}")
        print(f"   ❌ Failed: {len(failed)}/{len(self.results)}")
        print(f"   ⚠️  Empty: {len(empty)}/{len(self.results)}")

        if success:
            print(f"\n✅ Working Endpoints ({len(success)}):")
            for r in success:
                if r['type'] == 'paginated':
                    print(f"   - {r['name']}: {r['sample_count']} records (field: '{r['data_field']}', total: {r['total']:,})")
                else:
                    print(f"   - {r['name']}: Single response ({len(r['response_fields'])} fields)")

        if failed:
            print(f"\n❌ Failed Endpoints ({len(failed)}):")
            for r in failed:
                print(f"   - {r['name']}: {r['error']}")

        if empty:
            print(f"\n⚠️  Empty Endpoints ({len(empty)}):")
            for r in empty:
                print(f"   - {r['name']}: {r['error']}")

        # Save detailed results (B108: Use tempfile instead of hardcoded /tmp)
        output_file = Path(tempfile.gettempdir()) / 'pmp_endpoint_validation_results.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved: {output_file}")


if __name__ == '__main__':
    print("PMP Endpoint Validator")
    print("Testing all known endpoints with sample extractions")
    print()

    validator = PMPEndpointValidator()
    validator.run_validation()

    print("\n✅ Validation complete!")
