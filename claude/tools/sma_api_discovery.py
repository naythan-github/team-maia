#!/usr/bin/env python3
"""
SonicWall SMA 500 API Discovery Tool
Tests all known/potential endpoints to map the exact API structure

Environment Variables:
    SMA_VERIFY_SSL: Set to 'false' to disable SSL verification (default: true)
    SMA_CA_BUNDLE: Path to custom CA bundle for self-signed certs
"""

import os
import requests
import json
import sys
import argparse
from urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth
from datetime import datetime

# Only disable warnings if SSL verification is explicitly disabled
if os.environ.get('SMA_VERIFY_SSL', 'true').lower() == 'false':
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class SMAAPIDiscovery:
    def __init__(self, hostname, username, password, timeout=10):
        self.hostname = hostname
        self.username = username
        self.auth = HTTPBasicAuth(f"local\\{username}", password)
        self.timeout = timeout

        # SSL verification configuration (B501 fix)
        self.verify_ssl = os.environ.get('SMA_VERIFY_SSL', 'true').lower() == 'true'
        self.ca_bundle = os.environ.get('SMA_CA_BUNDLE', None)
        # Use CA bundle if provided, otherwise use verify_ssl boolean
        self.ssl_verify = self.ca_bundle if self.ca_bundle else self.verify_ssl

        self.results = {
            "discovery_date": datetime.now().isoformat(),
            "appliance": hostname,
            "working_endpoints": [],
            "failed_endpoints": [],
            "requires_auth": [],
            "not_found": []
        }

    def test_endpoint(self, url, method="GET", description=""):
        """Test a single endpoint and categorize result"""
        try:
            if method == "GET":
                response = requests.get(url, auth=self.auth, verify=self.ssl_verify, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, auth=self.auth, verify=self.ssl_verify, timeout=self.timeout)

            result = {
                "url": url,
                "method": method,
                "status": response.status_code,
                "description": description,
                "content_type": response.headers.get('content-type', 'unknown'),
                "content_length": len(response.content),
                "auth_required": True  # We're always using auth
            }

            # Try to parse response
            if 'json' in result['content_type']:
                try:
                    result['sample_data'] = response.json()
                    if isinstance(result['sample_data'], dict):
                        result['keys'] = list(result['sample_data'].keys())[:10]  # First 10 keys
                except:
                    result['sample_data'] = "JSON parse failed"
            elif result['content_length'] < 1000:  # Small text response
                result['sample_data'] = response.text[:500]  # First 500 chars

            # Categorize
            if response.status_code == 200:
                self.results['working_endpoints'].append(result)
                return "✅", result
            elif response.status_code == 401:
                self.results['requires_auth'].append(result)
                return "🔒", result
            elif response.status_code == 404:
                self.results['not_found'].append(result)
                return "❌", result
            else:
                self.results['failed_endpoints'].append(result)
                return "⚠️ ", result

        except requests.exceptions.Timeout:
            return "⏱️ ", {"url": url, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return "🔌", {"url": url, "error": "Connection failed"}
        except Exception as e:
            return "❌", {"url": url, "error": str(e)}

    def discover_console_endpoints(self):
        """Test Console API endpoints (port 8443)"""
        base = f"https://{self.hostname}:8443"

        print("\n" + "="*70)
        print("🔍 PHASE 1: Testing Console API Endpoints (Port 8443)")
        print("="*70 + "\n")

        # Confirmed working endpoints from documentation
        confirmed = [
            ("/Console/SystemStatus", "System status and health"),
            ("/Console/UserSessions", "Active user sessions"),
            ("/Console/Extensions", "Installed extensions"),
            ("/Console/Licensing/FeatureLicenses", "License information"),
            ("/Console/Agents/ConnectTunnel/Branding", "ConnectTunnel branding"),
        ]

        # Potential endpoints to discover
        potential = [
            ("/Console/Users", "User management"),
            ("/Console/Groups", "User groups"),
            ("/Console/Configuration", "Configuration settings"),
            ("/Console/Configuration/Export", "Configuration export"),
            ("/Console/NetExtender", "NetExtender configuration"),
            ("/Console/NetExtender/Settings", "NetExtender settings"),
            ("/Console/NetExtender/Routes", "NetExtender client routes"),
            ("/Console/Bookmarks", "User bookmarks"),
            ("/Console/Authentication", "Authentication servers"),
            ("/Console/Authentication/Servers", "AD/LDAP servers"),
            ("/Console/Policies", "Access policies"),
            ("/Console/AccessPolicies", "Access policies (alt)"),
            ("/Console/Network", "Network settings"),
            ("/Console/Network/Interfaces", "Network interfaces"),
            ("/Console/VPN", "VPN settings"),
            ("/Console/SSL", "SSL settings"),
            ("/Console/Certificates", "SSL certificates"),
            ("/Console/Logs", "System logs"),
            ("/Console/Help", "API help/documentation"),
        ]

        print("Testing CONFIRMED endpoints:")
        print("-" * 70)
        for endpoint, desc in confirmed:
            url = base + endpoint
            status, result = self.test_endpoint(url, description=desc)
            print(f"{status} {endpoint:45} | {desc}")

        print("\n\nTesting POTENTIAL endpoints:")
        print("-" * 70)
        for endpoint, desc in potential:
            url = base + endpoint
            status, result = self.test_endpoint(url, description=desc)
            print(f"{status} {endpoint:45} | {desc}")

    def discover_management_api(self):
        """Test Management API endpoints (RESTful API)"""
        base = f"https://{self.hostname}"

        print("\n" + "="*70)
        print("🔍 PHASE 2: Testing Management API Endpoints (RESTful)")
        print("="*70 + "\n")

        endpoints = [
            ("/api/v1/management/doc.json", "API documentation schema"),
            ("/api/v1/management/system/config", "System configuration"),
            ("/api/v1/management/system/status", "System status"),
            ("/api/v1/management/users", "User management"),
            ("/api/v1/management/groups", "Group management"),
            ("/api/v1/management/authentication", "Authentication settings"),
            ("/api/v1/management/netextender", "NetExtender configuration"),
            ("/api/v1/management/netextender/settings", "NetExtender settings"),
            ("/api/v1/management/netextender/routes", "NetExtender routes"),
            ("/api/v1/management/bookmarks", "User bookmarks"),
            ("/api/v1/management/access/policies", "Access policies"),
            ("/api/v1/management/licenses", "License information"),
            ("/api/v1/management/certificates", "SSL certificates"),
            ("/api/v1/management/network", "Network settings"),
        ]

        for endpoint, desc in endpoints:
            url = base + endpoint
            status, result = self.test_endpoint(url, description=desc)
            print(f"{status} {endpoint:50} | {desc}")

    def discover_setup_api(self):
        """Test Setup API endpoints"""
        base = f"https://{self.hostname}:8443"

        print("\n" + "="*70)
        print("🔍 PHASE 3: Testing Setup API Endpoints")
        print("="*70 + "\n")

        endpoints = [
            ("/Setup/Help", "Setup API documentation"),
            ("/Setup/System", "System setup"),
            ("/Setup/Network", "Network setup"),
        ]

        for endpoint, desc in endpoints:
            url = base + endpoint
            status, result = self.test_endpoint(url, description=desc)
            print(f"{status} {endpoint:45} | {desc}")

    def discover_alternative_paths(self):
        """Test alternative API structures"""

        print("\n" + "="*70)
        print("🔍 PHASE 4: Testing Alternative API Structures")
        print("="*70 + "\n")

        # Try different base paths
        bases = [
            (f"https://{self.hostname}:8443/api", "API v1"),
            (f"https://{self.hostname}:8443/api/v2", "API v2"),
            (f"https://{self.hostname}/api/management", "Management API alt"),
            (f"https://{self.hostname}:443/Console", "Console on 443"),
        ]

        for base, desc in bases:
            status, result = self.test_endpoint(base, description=desc)
            print(f"{status} {base:50} | {desc}")

    def test_config_export(self):
        """Test configuration export endpoints"""

        print("\n" + "="*70)
        print("🔍 PHASE 5: Testing Configuration Export Methods")
        print("="*70 + "\n")

        endpoints = [
            (f"https://{self.hostname}:8443/Console/Configuration/Export", "Console config export"),
            (f"https://{self.hostname}/api/v1/management/system/config/export", "API config export"),
            (f"https://{self.hostname}:8443/api/management/backup", "Backup endpoint"),
            (f"https://{self.hostname}:8443/backup", "Direct backup"),
        ]

        for url, desc in endpoints:
            status, result = self.test_endpoint(url, description=desc)
            print(f"{status} {url:65} | {desc}")

    def generate_report(self, output_file="sma_api_discovery_report.json"):
        """Generate detailed discovery report"""

        print("\n" + "="*70)
        print("📊 DISCOVERY SUMMARY")
        print("="*70 + "\n")

        print(f"✅ Working endpoints:     {len(self.results['working_endpoints'])}")
        print(f"🔒 Auth required:         {len(self.results['requires_auth'])}")
        print(f"❌ Not found (404):       {len(self.results['not_found'])}")
        print(f"⚠️  Failed (other):       {len(self.results['failed_endpoints'])}")

        # Save detailed report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved: {output_file}")

        # Print working endpoints with data samples
        if self.results['working_endpoints']:
            print("\n" + "="*70)
            print("✅ WORKING ENDPOINTS (Use these for extraction)")
            print("="*70 + "\n")

            for endpoint in self.results['working_endpoints']:
                print(f"\n{endpoint['url']}")
                print(f"  Description: {endpoint['description']}")
                print(f"  Content-Type: {endpoint['content_type']}")
                print(f"  Size: {endpoint['content_length']} bytes")

                if 'keys' in endpoint:
                    print(f"  JSON Keys: {', '.join(endpoint['keys'])}")

                if 'sample_data' in endpoint and isinstance(endpoint['sample_data'], str):
                    print(f"  Sample: {endpoint['sample_data'][:200]}...")

        return self.results

    def run_full_discovery(self):
        """Run complete API discovery"""
        print("\n" + "="*70)
        print("🚀 SonicWall SMA 500 API Discovery Tool")
        print("="*70)
        print(f"Target: {self.hostname}")
        print(f"User: {self.username}")
        print(f"Timeout: {self.timeout}s")

        # Test connectivity first
        print("\n🔌 Testing connectivity...")
        status, result = self.test_endpoint(
            f"https://{self.hostname}:8443/Console/SystemStatus",
            description="Connectivity test"
        )

        if status != "✅":
            print(f"\n❌ Cannot connect to SMA appliance at {self.hostname}")
            print("   Verify:")
            print("   1. Hostname/IP is correct")
            print("   2. Port 8443 is open")
            print("   3. SMA appliance is powered on")
            print("   4. Username/password are correct")
            sys.exit(1)

        print("✅ Connected successfully!\n")

        # Run discovery phases
        self.discover_console_endpoints()
        self.discover_management_api()
        self.discover_setup_api()
        self.discover_alternative_paths()
        self.test_config_export()

        # Generate report
        self.generate_report()

        print("\n" + "="*70)
        print("✅ Discovery complete!")
        print("="*70)
        print("\n📋 NEXT STEPS:")
        print("1. Review sma_api_discovery_report.json for working endpoints")
        print("2. I'll create a custom extractor using YOUR working endpoints")
        print("3. Run extractor to get structured configuration data")
        print("4. Transform to Azure VPN Gateway configuration")
        print("\n")

def main():
    parser = argparse.ArgumentParser(
        description='Discover SonicWall SMA 500 API endpoints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 sma_api_discovery.py 192.168.1.100 admin MyPassword
  python3 sma_api_discovery.py sma.company.com admin MyPassword --timeout 15
        """
    )

    parser.add_argument('hostname', help='SMA hostname or IP address')
    parser.add_argument('username', help='Admin username (without "local\\" prefix)')
    parser.add_argument('password', help='Admin password')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--output', default='sma_api_discovery_report.json', help='Output report file')

    args = parser.parse_args()

    discovery = SMAAPIDiscovery(args.hostname, args.username, args.password, args.timeout)
    discovery.run_full_discovery()

if __name__ == "__main__":
    main()
