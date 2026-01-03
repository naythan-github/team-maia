#!/usr/bin/env python3
"""
PMP API Endpoint Inventory Tool

Systematically queries every available API endpoint and builds a definitive catalog
of available data, fields, counts, and relationships.

Usage:
    python3 pmp_api_inventory.py
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager import PMPOAuthManager


class PMPAPIInventory:
    """Comprehensive API endpoint inventory tool"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.base_url = self.oauth_manager.server_url
        self.catalog = {}

    def _get_endpoint_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Return endpoint configuration dictionary.

        Returns:
            Dict mapping endpoint names to their configurations.
        """
        return {
            # ===== SYSTEM ENDPOINTS =====
            'System Inventory': {
                'endpoint': '/api/1.4/patch/scandetails',
                'description': 'System inventory with scan metadata',
                'params': {'page': 1, 'pageLimit': 1}
            },

            # ===== PATCH ENDPOINTS =====
            'All Patches': {
                'endpoint': '/api/1.4/patch/allpatches',
                'description': 'Complete patch catalog',
                'params': {'page': 1, 'pageLimit': 1}
            },
            'Installed Patches': {
                'endpoint': '/api/1.4/patch/installedpatches',
                'description': 'Installed patch summary',
                'params': {'page': 1, 'pageLimit': 1}
            },
            'Missing Patches': {
                'endpoint': '/api/1.4/patch/missingpatches',
                'description': 'Missing patch summary',
                'params': {'page': 1, 'pageLimit': 1}
            },
            'Supported Patches': {
                'endpoint': '/api/1.4/patch/supportedpatches',
                'description': 'Supported patches catalog',
                'params': {'page': 1, 'pageLimit': 1}
            },

            # ===== DCAPI ENDPOINTS =====
            'DCAPI Patch Mappings': {
                'endpoint': '/dcapi/threats/systemreport/patches',
                'description': 'System-patch mappings (bulk)',
                'params': {'page': 1, 'pageLimit': 1}
            },

            # ===== POLICY/CONFIG ENDPOINTS =====
            'Deployment Policies': {
                'endpoint': '/api/1.4/patch/deploymentpolicies',
                'description': 'Patch deployment policies',
                'params': {}
            },
            'Health Policy': {
                'endpoint': '/api/1.4/patch/healthpolicy',
                'description': 'Patch health policy',
                'params': {}
            },
            'Approval Settings': {
                'endpoint': '/api/1.4/patch/approvalsettings',
                'description': 'Patch approval settings',
                'params': {}
            },

            # ===== VULNERABILITY ENDPOINTS =====
            'Vulnerabilities': {
                'endpoint': '/api/1.4/patch/vulnerabilities',
                'description': 'Vulnerability data',
                'params': {'page': 1, 'pageLimit': 1}
            },

            # ===== POTENTIAL ADDITIONAL ENDPOINTS =====
            'Patch Groups': {
                'endpoint': '/api/1.4/patch/patchgroups',
                'description': 'Patch groups/collections',
                'params': {}
            },
            'Deployment Tasks': {
                'endpoint': '/api/1.4/patch/deploymenttasks',
                'description': 'Deployment task history',
                'params': {'page': 1, 'pageLimit': 1}
            },
            'Scan History': {
                'endpoint': '/api/1.4/patch/scanhistory',
                'description': 'Patch scan history',
                'params': {'page': 1, 'pageLimit': 1}
            },
        }

    def _test_all_endpoints(self, endpoints: Dict[str, Dict]) -> tuple:
        """
        Test all endpoints and collect results.

        Args:
            endpoints: Dict of endpoint configurations

        Returns:
            Tuple of (results_dict, (success_count, empty_count, error_count))
        """
        results = {}
        success_count = 0
        empty_count = 0
        error_count = 0

        for name, config in endpoints.items():
            print(f"Testing: {name}")
            print(f"  Endpoint: {config['endpoint']}")

            result = self.test_endpoint(config['endpoint'], config.get('params'))
            results[name] = {
                **config,
                **result
            }

            # Print immediate feedback
            if result['status'] == 'success':
                print(f"  ✅ SUCCESS: {result['total_records']:,} records")
                fields_preview = result.get('all_fields', [])[:10]
                suffix = '...' if len(result.get('all_fields', [])) > 10 else ''
                print(f"     Fields: {', '.join(fields_preview)}{suffix}")
                success_count += 1
            elif result['status'] == 'empty':
                print(f"  ⚠️  EMPTY: No data available")
                empty_count += 1
            elif result['status'] == 'unauthorized':
                print(f"  🔒 UNAUTHORIZED: {result.get('error_message', 'N/A')}")
                error_count += 1
            elif result['status'] == 'error':
                print(f"  ❌ ERROR: {result.get('error_message', 'N/A')}")
                error_count += 1

            print(f"     Response time: {result.get('response_time_ms', 0):.2f}ms\n")

            # Rate limiting
            time.sleep(0.25)

        return results, (success_count, empty_count, error_count)

    def _print_inventory_summary(self, total_endpoints: int, success_count: int,
                                  empty_count: int, error_count: int) -> None:
        """
        Print inventory summary statistics.

        Args:
            total_endpoints: Total number of endpoints tested
            success_count: Number of successful endpoints
            empty_count: Number of empty endpoints
            error_count: Number of failed endpoints
        """
        print("=" * 80)
        print("INVENTORY SUMMARY")
        print("=" * 80)
        print(f"Total endpoints tested: {total_endpoints}")
        print(f"✅ Success: {success_count}")
        print(f"⚠️  Empty: {empty_count}")
        print(f"❌ Errors/Unauthorized: {error_count}")
        print()

    def test_endpoint(self, endpoint: str, params: Optional[Dict] = None, method: str = "GET") -> Dict[str, Any]:
        """
        Test a single API endpoint and extract metadata.

        Returns:
            {
                'status': 'success' | 'empty' | 'error' | 'unauthorized',
                'http_code': 200,
                'total_records': 123,
                'sample_record': {...},
                'all_fields': ['field1', 'field2', ...],
                'response_time_ms': 123.45,
                'error_message': '...' (if error)
            }
        """
        try:
            token = self.oauth_manager.get_valid_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Default params
            if params is None:
                params = {"page": 1, "pageLimit": 1}  # Get just 1 record for sampling

            url = f"{self.base_url}{endpoint}"

            import requests
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response_time_ms = (time.time() - start_time) * 1000

            result = {
                'http_code': response.status_code,
                'response_time_ms': round(response_time_ms, 2)
            }

            if response.status_code == 401:
                result['status'] = 'unauthorized'
                result['error_message'] = 'INVALID_OAUTHSCOPE or token issue'
                return result

            if response.status_code != 200:
                result['status'] = 'error'
                result['error_message'] = f"HTTP {response.status_code}: {response.text[:200]}"
                return result

            # Check if response is empty
            if not response.text or response.text.strip() == '':
                result['status'] = 'empty'
                result['error_message'] = 'Empty response body'
                return result

            # Try to parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                result['status'] = 'error'
                result['error_message'] = f"JSON decode error: {str(e)}"
                result['raw_response'] = response.text[:500]
                return result

            # Extract message_response wrapper (common pattern)
            if 'message_response' in data:
                data = data['message_response']

            # Detect data structure
            total_records = None
            sample_record = None
            all_fields = []
            data_key = None

            # Pattern 1: {total: N, data_key: [...]}
            if 'total' in data:
                total_records = data['total']

                # Find the array key (scandetails, patches, installedpatches, etc.)
                for key in data.keys():
                    if isinstance(data[key], list) and len(data[key]) > 0:
                        data_key = key
                        sample_record = data[key][0]
                        all_fields = list(sample_record.keys())
                        break

            # Pattern 2: Direct array
            elif isinstance(data, list) and len(data) > 0:
                total_records = len(data)
                sample_record = data[0]
                all_fields = list(sample_record.keys())

            # Pattern 3: Single object (policies, settings)
            elif isinstance(data, dict):
                total_records = 1
                sample_record = data
                all_fields = list(data.keys())

            if total_records == 0 or (total_records is None and not sample_record):
                result['status'] = 'empty'
                result['total_records'] = 0
            else:
                result['status'] = 'success'
                result['total_records'] = total_records
                result['sample_record'] = sample_record
                result['all_fields'] = all_fields
                result['data_key'] = data_key

            return result

        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'response_time_ms': 0
            }

    def run_full_inventory(self) -> Dict[str, Any]:
        """
        Run comprehensive inventory of all known endpoints.

        Phase 230: Refactored to use helper functions for maintainability.

        Returns catalog dict with endpoint results.
        """
        print("=" * 80)
        print("PMP API ENDPOINT INVENTORY")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get endpoint definitions and test them
        endpoints = self._get_endpoint_definitions()
        results, (success_count, empty_count, error_count) = self._test_all_endpoints(endpoints)

        # Print summary
        self._print_inventory_summary(len(endpoints), success_count, empty_count, error_count)

        # Build catalog
        self.catalog = {
            'timestamp': datetime.now().isoformat(),
            'server_url': self.base_url,
            'summary': {
                'total_endpoints': len(endpoints),
                'success_count': success_count,
                'empty_count': empty_count,
                'error_count': error_count
            },
            'endpoints': results
        }

        return self.catalog

    def save_catalog(self, output_path: str):
        """Save catalog to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.catalog, f, indent=2)
        print(f"💾 Catalog saved to: {output_path}")

    def print_field_catalog(self):
        """Print detailed field catalog for all successful endpoints"""
        print("\n" + "=" * 80)
        print("FIELD CATALOG (Successful Endpoints)")
        print("=" * 80 + "\n")

        for name, result in self.catalog['endpoints'].items():
            if result['status'] == 'success':
                print(f"📋 {name}")
                print(f"   Endpoint: {result['endpoint']}")
                print(f"   Total Records: {result['total_records']:,}")
                print(f"   Fields ({len(result['all_fields'])}):")

                for field in result['all_fields']:
                    sample_value = result['sample_record'].get(field)
                    value_type = type(sample_value).__name__

                    # Truncate long values
                    if isinstance(sample_value, str) and len(sample_value) > 50:
                        sample_value = sample_value[:47] + "..."
                    elif isinstance(sample_value, (list, dict)):
                        sample_value = f"{value_type} (length: {len(sample_value)})"

                    print(f"      - {field}: {value_type} = {sample_value}")

                print()


def main():
    """Main entry point"""
    inventory = PMPAPIInventory()

    # Run full inventory
    catalog = inventory.run_full_inventory()

    # Save to file
    output_path = Path.home() / "work_projects" / "pmp_intelligence" / "pmp_api_catalog.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    inventory.save_catalog(str(output_path))

    # Print detailed field catalog
    inventory.print_field_catalog()

    print("\n✅ API inventory complete!")
    print(f"📄 Full catalog: {output_path}")


if __name__ == "__main__":
    main()
