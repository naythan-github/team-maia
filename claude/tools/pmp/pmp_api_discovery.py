#!/usr/bin/env python3
"""
PMP API Discovery Tool - Comprehensive Endpoint Testing
Test all documented ManageEngine PMP API endpoints to discover available data

Purpose:
- Identify which endpoints return JSON vs HTML
- Document response schemas for working endpoints
- Map OAuth scope limitations
- Build foundation for detailed data extraction

Author: Patch Manager Plus API Specialist Agent
Date: 2025-11-25
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
except ImportError:
    from pmp_oauth_manager import PMPOAuthManager


class PMPAPIDiscovery:
    """
    Comprehensive API endpoint discovery tool

    Tests all documented PMP API endpoints to determine:
    - Which endpoints are accessible with current OAuth scopes
    - Response format (JSON, HTML, error)
    - Data schema for working endpoints
    """

    # All documented PMP API endpoints (from official ManageEngine API documentation)
    # Updated 2025-11-25 with correct paths from pmp_cloud_api_reference.md
    ENDPOINTS_TO_TEST = [
        # === PATCH MANAGEMENT APIs ===

        # Summary & Reporting
        ("GET", "/api/1.4/patch/summary", {}, "Patch Summary (aggregate metrics)"),
        ("GET", "/api/1.4/patch/systemreport", {"resid": "95000011194313"}, "System Report (per-system patch details)"),

        # Patch Queries
        ("GET", "/api/1.4/patch/allpatches", {}, "All Patches (complete list)"),
        ("GET", "/api/1.4/patch/allpatchdetails", {"patchid": "1"}, "Patch Details (patch-to-computers mapping)"),
        ("GET", "/api/1.4/patch/supportedpatches", {}, "Supported Patches (master catalog)"),

        # System Queries
        ("GET", "/api/1.4/patch/allsystems", {}, "All Systems (complete list)"),

        # Configuration & Policy
        ("GET", "/api/1.4/patch/deploymentpolicies", {}, "Deployment Policies"),
        ("GET", "/api/1.4/patch/healthpolicy", {}, "System Health Policy"),
        ("GET", "/api/1.4/patch/viewconfig", {}, "View Configurations"),
        ("GET", "/api/1.4/patch/approvalsettings", {}, "Approval Settings"),

        # Patch Actions (READ endpoints only for discovery)
        ("GET", "/api/1.4/patch/updatedbstatus", {}, "Patch Database Update Status"),

        # Scan Operations
        ("GET", "/api/1.4/patch/scandetails", {}, "Scan Details (all systems with scan status)"),

        # === ENHANCED DCAPI ENDPOINTS ===

        # Enhanced Patch Queries
        ("GET", "/dcapi/threats/patches", {"page": 1, "pageLimit": 10}, "Enhanced Patch Queries (DCAPI)"),
        ("GET", "/dcapi/threats/systemreport/patches", {"page": 1, "pageLimit": 10}, "Enhanced System-Patch Mapping (DCAPI)"),

        # === SYSTEM ON MANAGEMENT (SoM) APIs ===

        # SoM Summary & Queries
        ("GET", "/api/1.4/som/summary", {}, "SoM Summary (agent metrics)"),
        ("GET", "/api/1.4/som/computers", {}, "SoM Computers (agent details)"),
        ("GET", "/api/1.4/som/remoteoffice", {}, "SoM Remote Office (branch configs)"),

        # === SUPPORTING ENDPOINTS ===

        # Server Properties (needed for filter values)
        ("GET", "/api/1.4/desktop/serverproperties", {}, "Server Properties (domain/branch/group lists)"),
    ]

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize API discovery tool"""
        self.oauth_manager = PMPOAuthManager()

        if output_dir is None:
            output_dir = Path.home() / "work_projects/pmp_reports"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = []

    def test_endpoint(self, method: str, endpoint: str, params: Dict, description: str) -> Dict:
        """
        Test a single API endpoint and categorize response

        Returns:
            Dict with test results (status, format, schema, sample)
        """
        print(f"\n🧪 Testing: {method} {endpoint}")
        print(f"   Description: {description}")
        print(f"   Params: {params}")

        result = {
            "method": method,
            "endpoint": endpoint,
            "params": params,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status_code": None,
            "response_format": None,
            "is_accessible": False,
            "schema": None,
            "sample_data": None,
            "error_message": None
        }

        try:
            response = self.oauth_manager.api_request(method, endpoint, params=params)
            result["status_code"] = response.status_code

            # Check if JSON response
            try:
                data = response.json()
                result["response_format"] = "JSON"
                result["is_accessible"] = True

                # Extract schema (top-level keys)
                if isinstance(data, dict):
                    result["schema"] = self._extract_schema(data)
                    # Sample data (first 500 chars)
                    result["sample_data"] = json.dumps(data, indent=2)[:500]
                elif isinstance(data, list):
                    result["schema"] = {"type": "list", "count": len(data)}
                    if data:
                        result["schema"]["item_schema"] = self._extract_schema(data[0])
                    result["sample_data"] = json.dumps(data[:2], indent=2)[:500]

                print(f"   ✅ SUCCESS: JSON response")
                print(f"   Schema: {result['schema']}")

            except json.JSONDecodeError:
                # Not JSON - check if HTML
                text = response.text[:200]
                if "<html" in text.lower() or "<!doctype" in text.lower():
                    result["response_format"] = "HTML"
                    result["is_accessible"] = False
                    result["error_message"] = "OAuth scope limitation (HTML login page)"
                    print(f"   ❌ FAILED: HTML response (OAuth scope issue)")
                else:
                    result["response_format"] = "TEXT"
                    result["sample_data"] = text
                    print(f"   ⚠️  WARNING: Non-JSON text response")

        except Exception as e:
            result["error_message"] = str(e)
            result["is_accessible"] = False
            print(f"   ❌ ERROR: {e}")

        return result

    def _extract_schema(self, data: Dict, max_depth: int = 2) -> Dict:
        """Extract schema from JSON response (nested keys and types)"""
        if max_depth == 0:
            return {"type": type(data).__name__}

        schema = {}
        for key, value in data.items():
            if isinstance(value, dict):
                schema[key] = self._extract_schema(value, max_depth - 1)
            elif isinstance(value, list):
                schema[key] = {
                    "type": "list",
                    "count": len(value),
                    "item_type": type(value[0]).__name__ if value else None
                }
            else:
                schema[key] = type(value).__name__

        return schema

    def run_discovery(self) -> List[Dict]:
        """
        Run comprehensive API discovery

        Tests all endpoints and categorizes results
        """
        print("=" * 80)
        print("🔍 PMP API DISCOVERY - Comprehensive Endpoint Testing")
        print("=" * 80)
        print(f"Testing {len(self.ENDPOINTS_TO_TEST)} endpoints...")
        print(f"OAuth Scopes: {self.oauth_manager.SCOPES}")
        print("=" * 80)

        for method, endpoint, params, description in self.ENDPOINTS_TO_TEST:
            result = self.test_endpoint(method, endpoint, params, description)
            self.results.append(result)

            # Rate limiting: small delay between requests
            time.sleep(0.5)

        return self.results

    def save_results(self) -> Path:
        """Save discovery results to JSON file"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_path = self.output_dir / f"pmp_api_discovery_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {output_path}")
        return output_path

    def print_summary(self):
        """Print summary of discovery results"""
        accessible = [r for r in self.results if r["is_accessible"]]
        html_responses = [r for r in self.results if r["response_format"] == "HTML"]
        errors = [r for r in self.results if r["error_message"] and r["response_format"] != "HTML"]

        print("\n" + "=" * 80)
        print("📊 DISCOVERY SUMMARY")
        print("=" * 80)
        print(f"Total Endpoints Tested: {len(self.results)}")
        print(f"✅ Accessible (JSON): {len(accessible)}")
        print(f"❌ OAuth Scope Limited (HTML): {len(html_responses)}")
        print(f"⚠️  Errors: {len(errors)}")
        print("=" * 80)

        if accessible:
            print("\n✅ ACCESSIBLE ENDPOINTS (JSON):")
            for r in accessible:
                print(f"   • {r['method']} {r['endpoint']}")
                print(f"     → {r['description']}")
                if r['schema']:
                    print(f"     → Schema: {list(r['schema'].keys())[:5]}")

        if html_responses:
            print(f"\n❌ OAUTH SCOPE LIMITED ENDPOINTS (HTML - {len(html_responses)}):")
            for r in html_responses[:5]:  # Show first 5
                print(f"   • {r['method']} {r['endpoint']}")
                print(f"     → {r['description']}")
            if len(html_responses) > 5:
                print(f"   ... and {len(html_responses) - 5} more")

        if errors:
            print(f"\n⚠️  ERROR ENDPOINTS:")
            for r in errors:
                print(f"   • {r['method']} {r['endpoint']}")
                print(f"     → Error: {r['error_message']}")

        print("\n" + "=" * 80)
        print("💡 NEXT STEPS:")
        if accessible:
            print(f"   ✅ {len(accessible)} endpoints are accessible - can build detailed extraction")
        if html_responses:
            print(f"   ⚠️  {len(html_responses)} endpoints require broader OAuth scopes")
            print("      → Contact ManageEngine support to request additional scopes")
            print("      → Or explore alternative data sources (CSV export, database)")
        print("=" * 80)


def main():
    """CLI interface for API discovery"""
    import argparse

    parser = argparse.ArgumentParser(description="PMP API Discovery Tool")
    parser.add_argument('--output', type=str,
                       help='Output directory for results (default: ~/work_projects/pmp_reports/)')

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    discovery = PMPAPIDiscovery(output_dir=output_dir)

    # Run discovery
    results = discovery.run_discovery()

    # Save results
    results_path = discovery.save_results()

    # Print summary
    discovery.print_summary()

    print(f"\n📄 Full results: {results_path}")


if __name__ == '__main__':
    main()
