#!/usr/bin/env python3
"""
PMP Endpoint Validator v2 - Environment-Aware

Tests all PMP REST API endpoints with environment isolation.
Requires PMP_ENV=TEST or PMP_ENV=PROD to be set.

Usage:
    PMP_ENV=TEST python3 pmp_endpoint_validator_v2.py
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager_v2 import PMPOAuthManagerV2


class PMPEndpointValidatorV2:
    """Environment-aware PMP REST API endpoint validator"""

    def __init__(self):
        # This will fail if PMP_ENV not set (safety!)
        self.oauth_manager = PMPOAuthManagerV2()
        self.environment = self.oauth_manager.environment
        self.base_url = self.oauth_manager.server_url
        self.results = []

    def fetch_json(self, endpoint: str, page: Optional[int] = None,
                   max_retries: int = 3) -> Optional[Dict]:
        """Fetch JSON data from API endpoint with retry logic"""
        import requests

        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {"Authorization": f"Zoho-oauthtoken {token}"}
                url = f"{self.base_url}{endpoint}"

                params = {'page': page} if page is not None else None

                response = requests.get(url, headers=headers, params=params, timeout=(10, 30))

                if response.status_code == 200:
                    content = response.text
                    if content.strip().startswith('<') or '<!DOCTYPE' in content or '<html' in content.lower():
                        print(f"   ⚠️  [{self.environment}] HTML throttling response. Waiting 60s...")
                        time.sleep(60)
                        continue

                    try:
                        data = response.json()
                        if 'message_response' in data:
                            return data['message_response']
                        return data
                    except ValueError:
                        print(f"   ⚠️  [{self.environment}] JSON parse error. Waiting 60s...")
                        time.sleep(60)
                        continue

                elif response.status_code == 401:
                    return {"error": "Unauthorized", "status_code": 401}
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"   ⚠️  [{self.environment}] Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                else:
                    return {"error": f"HTTP {response.status_code}", "status_code": response.status_code}

            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": str(e), "status_code": 0}

        return None

    def find_data_field(self, data: Dict, expected_keys: List[str]) -> Tuple[Optional[str], Optional[List]]:
        """Find which field contains the data array"""
        for key in expected_keys:
            if key in data and isinstance(data.get(key), list):
                return (key, data[key])

        for fallback in ['data', 'records', 'items']:
            if fallback in data and isinstance(data.get(fallback), list):
                return (fallback, data[fallback])

        return (None, None)

    def test_endpoint(self, name: str, endpoint: str, expected_keys: List[str],
                      is_paginated: bool = True) -> Dict:
        """Test a single endpoint and return results"""
        print(f"\n{'='*80}")
        print(f"[{self.environment}] Testing: {name}")
        print(f"Endpoint: {endpoint}")
        print(f"Type: {'Paginated' if is_paginated else 'Simple'}")
        print(f"{'='*80}")

        result = {
            'name': name,
            'endpoint': endpoint,
            'environment': self.environment,
            'type': 'paginated' if is_paginated else 'simple',
            'expected_keys': expected_keys,
            'status': 'unknown',
            'tested_at': datetime.now().isoformat()
        }

        data = self.fetch_json(endpoint, page=1 if is_paginated else None)

        if data is None:
            result['status'] = 'failed'
            result['error'] = 'No response from API'
            print(f"❌ [{self.environment}] FAILED: No response")
            return result

        if 'error' in data:
            result['status'] = 'failed'
            result['error'] = data['error']
            result['status_code'] = data.get('status_code')
            print(f"❌ [{self.environment}] FAILED: {data['error']} (HTTP {data.get('status_code')})")
            return result

        result['response_fields'] = list(data.keys())
        result['total'] = data.get('total', 'N/A')

        if is_paginated:
            field_name, records = self.find_data_field(data, expected_keys)

            if field_name and records:
                result['status'] = 'success'
                result['data_field'] = field_name
                result['sample_count'] = len(records)
                result['sample_record'] = records[0] if records else None

                total_str = f"{result['total']:,}" if isinstance(result['total'], int) else str(result['total'])
                print(f"✅ [{self.environment}] SUCCESS")
                print(f"   Total records: {total_str}")
                print(f"   Data field: '{field_name}'")
                print(f"   Sample size: {len(records)} records")
                if records:
                    print(f"   Sample keys: {list(records[0].keys())[:10]}...")
            elif result['total'] == 0 or (isinstance(result['total'], int) and result['total'] == 0):
                # Empty but valid - common for trial instances
                result['status'] = 'success'
                result['data_field'] = None
                result['sample_count'] = 0
                print(f"✅ [{self.environment}] SUCCESS (empty dataset - normal for trial)")
                print(f"   Total records: 0")
            else:
                result['status'] = 'empty'
                result['error'] = f"No data found in expected fields: {expected_keys}"
                print(f"⚠️  [{self.environment}] EMPTY: Found {result['total']} total but no data in: {expected_keys}")
                print(f"   Available fields: {result['response_fields']}")
        else:
            result['status'] = 'success'
            result['sample_record'] = data
            print(f"✅ [{self.environment}] SUCCESS")
            print(f"   Response fields: {result['response_fields']}")
            print(f"   Top-level keys: {list(data.keys())[:20]}")

        return result

    def run_validation(self):
        """Test all known PMP endpoints"""
        cfg = self.oauth_manager.config
        color = cfg['color']
        reset = self.oauth_manager.RESET_COLOR

        print(f"{color}{'='*80}{reset}")
        print(f"{color}PMP ENDPOINT VALIDATION - {self.environment}{reset}")
        print(f"{color}{'='*80}{reset}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Server: {self.base_url}")
        print()

        # All known endpoints
        endpoints = [
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

        for name, endpoint, expected_keys, is_paginated in endpoints:
            result = self.test_endpoint(name, endpoint, expected_keys, is_paginated)
            self.results.append(result)
            time.sleep(0.5)  # Rate limiting

        self.print_summary()

    def print_summary(self):
        """Print validation summary"""
        cfg = self.oauth_manager.config
        color = cfg['color']
        reset = self.oauth_manager.RESET_COLOR

        print(f"\n{color}{'='*80}{reset}")
        print(f"{color}VALIDATION SUMMARY - {self.environment}{reset}")
        print(f"{color}{'='*80}{reset}")

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
                    total_str = f"{r['total']:,}" if isinstance(r.get('total'), int) else str(r.get('total', 'N/A'))
                    count = r.get('sample_count', 0)
                    field = r.get('data_field', 'N/A')
                    print(f"   - {r['name']}: {count} records (field: '{field}', total: {total_str})")
                else:
                    fields = len(r.get('response_fields', []))
                    print(f"   - {r['name']}: Single response ({fields} fields)")

        if failed:
            print(f"\n❌ Failed Endpoints ({len(failed)}):")
            for r in failed:
                print(f"   - {r['name']}: {r['error']}")

        if empty:
            print(f"\n⚠️  Empty Endpoints ({len(empty)}):")
            for r in empty:
                print(f"   - {r['name']}: {r['error']}")

        # Save results with environment in filename
        output_file = Path(f'/tmp/pmp_endpoint_validation_{self.environment}.json')
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved: {output_file}")


if __name__ == '__main__':
    env = os.environ.get('PMP_ENV', '')
    if not env:
        print("="*60)
        print("🛑 SAFETY: PMP_ENV must be set!")
        print("="*60)
        print("\nUsage:")
        print("  PMP_ENV=TEST python3 pmp_endpoint_validator_v2.py")
        print("  PMP_ENV=PROD python3 pmp_endpoint_validator_v2.py")
        sys.exit(1)

    print(f"PMP Endpoint Validator v2 - Environment: {env}")
    print("Testing all known endpoints with sample extractions")
    print()

    try:
        validator = PMPEndpointValidatorV2()
        validator.run_validation()
        print("\n✅ Validation complete!")
    except ValueError as e:
        print(str(e))
        sys.exit(1)
