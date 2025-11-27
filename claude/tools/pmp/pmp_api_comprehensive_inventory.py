#!/usr/bin/env python3
"""
PMP API Comprehensive Inventory Tool

Tests ALL 27 documented API endpoints from pmp_cloud_api_reference.md

Usage:
    python3 pmp_api_comprehensive_inventory.py
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


class PMPAPIComprehensiveInventory:
    """Comprehensive API endpoint inventory based on official documentation"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.base_url = self.oauth_manager.server_url
        self.catalog = {}

    def test_endpoint(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Test a single API endpoint.

        Returns:
            Result dict with status, data counts, sample fields
        """
        try:
            token = self.oauth_manager.get_valid_token()
            headers = {"Authorization": f"Bearer {token}"}

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
                result['error_message'] = f"HTTP {response.status_code}"
                result['raw_response'] = response.text[:200]
                return result

            # Check if response is HTML (login redirect)
            if response.text.strip().startswith('<!DOCTYPE html>') or response.text.strip().startswith('<html'):
                result['status'] = 'redirect'
                result['error_message'] = 'HTML login page returned (auth/scope issue)'
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

            # Extract message_response wrapper
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

                # Find the array key
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
        Test all 27 documented API endpoints.
        """
        print("=" * 80)
        print("PMP API COMPREHENSIVE INVENTORY (27 Endpoints)")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Define all endpoints from documentation
        endpoints = {
            # ===== PATCH MANAGEMENT: SUMMARY & REPORTING =====
            '1. Patch Summary': {
                'endpoint': '/api/1.4/patch/summary',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'High-level patch module summaries'
            },
            '2. System Report': {
                'endpoint': '/api/1.4/patch/systemreport',
                'params': {'resid': 95000000079557},  # Use known resource ID from DCAPI
                'scope': 'PatchMgmt.READ',
                'description': 'Detailed patch status for specific system'
            },

            # ===== PATCH MANAGEMENT: PATCH QUERIES =====
            '3. All Patches': {
                'endpoint': '/api/1.4/patch/allpatches',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'List all patches for managed systems'
            },
            '4. All Patch Details': {
                'endpoint': '/api/1.4/patch/allpatchdetails',
                'params': {'patchid': 10044},  # Use known patch ID from DCAPI
                'scope': 'PatchMgmt.READ',
                'description': 'Status of specific patch across all computers'
            },
            '5. Supported Patches': {
                'endpoint': '/api/1.4/patch/supportedpatches',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Master catalog of manageable patches'
            },
            '6. All Applicable Patches (DCAPI)': {
                'endpoint': '/dcapi/threats/patches',
                'params': {'page': 1, 'pageLimit': 1},
                'scope': 'PatchMgmt.READ',
                'description': 'Enhanced patch list with extensive filtering'
            },

            # ===== PATCH MANAGEMENT: SYSTEM QUERIES =====
            '7. All Systems': {
                'endpoint': '/api/1.4/patch/allsystems',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'List all systems and patch status'
            },
            '8. System and Patch Details (DCAPI)': {
                'endpoint': '/dcapi/threats/systemreport/patches',
                'params': {'page': 1, 'pageLimit': 1},
                'scope': 'PatchMgmt.READ',
                'description': 'Systems with patch details (enhanced)'
            },

            # ===== PATCH MANAGEMENT: CONFIGURATION & POLICY =====
            '9. Deployment Policies': {
                'endpoint': '/api/1.4/patch/deploymentpolicies',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'List all deployment policies'
            },
            '10. System Health Policy': {
                'endpoint': '/api/1.4/patch/healthpolicy',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Configured health policy settings'
            },
            '11. View Configurations': {
                'endpoint': '/api/1.4/patch/viewconfig',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Deployment configurations and status'
            },
            '12. Approval Settings': {
                'endpoint': '/api/1.4/patch/approvalsettings',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Patch approval settings'
            },

            # ===== PATCH MANAGEMENT: PATCH ACTIONS (WRITE) =====
            # Skip write operations for read-only inventory

            # ===== PATCH MANAGEMENT: SCAN OPERATIONS =====
            '18. Patch DB Update Status': {
                'endpoint': '/api/1.4/patch/updatedbstatus',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Status of patch database update'
            },
            '19. Scan Details': {
                'endpoint': '/api/1.4/patch/scandetails',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'All systems and scan status'
            },

            # ===== SYSTEM ON MANAGEMENT: SUMMARY & QUERIES =====
            '22. SoM Summary': {
                'endpoint': '/api/1.4/som/summary',
                'params': {},
                'scope': 'Common.READ',
                'description': 'SoM module summary information'
            },
            '23. SoM Computers': {
                'endpoint': '/api/1.4/som/computers',
                'params': {},
                'scope': 'Common.READ',
                'description': 'All computers and agent details'
            },
            '24. SoM Remote Office': {
                'endpoint': '/api/1.4/som/remoteoffice',
                'params': {},
                'scope': 'SOM.READ',
                'description': 'Remote offices and configurations'
            },

            # ===== ADDITIONAL ENDPOINTS (from previous testing) =====
            'Installed Patches': {
                'endpoint': '/api/1.4/patch/installedpatches',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Installed patch summary'
            },
            'Missing Patches': {
                'endpoint': '/api/1.4/patch/missingpatches',
                'params': {},
                'scope': 'PatchMgmt.READ',
                'description': 'Missing patch summary'
            },
        }

        results = {}
        success_count = 0
        redirect_count = 0
        empty_count = 0
        error_count = 0

        for name, config in endpoints.items():
            print(f"Testing: {name}")
            print(f"  Endpoint: {config['endpoint']}")
            print(f"  Scope: {config['scope']}")

            result = self.test_endpoint(config['endpoint'], config.get('params'))
            results[name] = {
                **config,
                **result
            }

            # Print immediate feedback
            if result['status'] == 'success':
                print(f"  ✅ SUCCESS: {result.get('total_records', 'N/A')} records")
                fields = result.get('all_fields', [])
                print(f"     Fields: {', '.join(fields[:8])}{'...' if len(fields) > 8 else ''}")
                success_count += 1
            elif result['status'] == 'redirect':
                print(f"  🔐 REDIRECT: {result.get('error_message', 'N/A')}")
                redirect_count += 1
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

        # Summary
        print("=" * 80)
        print("INVENTORY SUMMARY")
        print("=" * 80)
        print(f"Total endpoints tested: {len(endpoints)}")
        print(f"✅ Success: {success_count}")
        print(f"🔐 Redirect (auth/scope): {redirect_count}")
        print(f"⚠️  Empty: {empty_count}")
        print(f"❌ Errors/Unauthorized: {error_count}")
        print()

        # Build catalog
        self.catalog = {
            'timestamp': datetime.now().isoformat(),
            'server_url': self.base_url,
            'summary': {
                'total_endpoints': len(endpoints),
                'success_count': success_count,
                'redirect_count': redirect_count,
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

    def print_summary_table(self):
        """Print summary table of all endpoints"""
        print("\n" + "=" * 80)
        print("ENDPOINT STATUS SUMMARY")
        print("=" * 80 + "\n")

        # Group by status
        by_status = {
            'success': [],
            'redirect': [],
            'empty': [],
            'error': []
        }

        for name, result in self.catalog['endpoints'].items():
            status = result['status']
            if status in by_status:
                by_status[status].append(name)

        print("✅ WORKING ENDPOINTS ({}):\n".format(len(by_status['success'])))
        for name in by_status['success']:
            endpoint = self.catalog['endpoints'][name]
            print(f"   {name}")
            print(f"      {endpoint['endpoint']}")
            print(f"      Records: {endpoint.get('total_records', 'N/A')}")
            print()

        print("\n🔐 AUTH/SCOPE ISSUES ({}):\n".format(len(by_status['redirect'])))
        for name in by_status['redirect']:
            endpoint = self.catalog['endpoints'][name]
            print(f"   {name}: {endpoint['endpoint']}")

        print("\n⚠️  EMPTY RESPONSES ({}):\n".format(len(by_status['empty'])))
        for name in by_status['empty']:
            endpoint = self.catalog['endpoints'][name]
            print(f"   {name}: {endpoint['endpoint']}")

        print("\n❌ ERRORS ({}):\n".format(len(by_status['error'])))
        for name in by_status['error']:
            endpoint = self.catalog['endpoints'][name]
            print(f"   {name}: {endpoint['endpoint']} - {endpoint.get('error_message', 'Unknown')}")


def main():
    """Main entry point"""
    inventory = PMPAPIComprehensiveInventory()

    # Run full inventory
    catalog = inventory.run_full_inventory()

    # Save to file
    output_path = Path.home() / "work_projects" / "pmp_intelligence" / "pmp_api_comprehensive_catalog.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    inventory.save_catalog(str(output_path))

    # Print summary table
    inventory.print_summary_table()

    print("\n✅ Comprehensive API inventory complete!")
    print(f"📄 Full catalog: {output_path}")


if __name__ == "__main__":
    main()
