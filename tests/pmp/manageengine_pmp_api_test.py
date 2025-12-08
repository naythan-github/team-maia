#!/usr/bin/env python3
"""
ManageEngine Patch Manager Plus - API Access Test
Tests authentication and basic API operations
"""

import requests
import base64
import json
import os
from datetime import datetime

# Configuration
import sys
import getpass

SERVER_URL = "https://patch.manageengine.com.au"

# Get credentials from environment, command line, or prompt
if len(sys.argv) >= 3:
    USERNAME = sys.argv[1]
    PASSWORD = sys.argv[2]
elif len(sys.argv) == 2:
    USERNAME = sys.argv[1]
    PASSWORD = getpass.getpass(f"Enter password for {USERNAME}: ")
else:
    USERNAME = os.getenv('PMP_USERNAME')
    PASSWORD = os.getenv('PMP_PASSWORD')

    if not USERNAME:
        USERNAME = input("Enter username: ")
    if not PASSWORD:
        PASSWORD = getpass.getpass(f"Enter password for {USERNAME}: ")

if not USERNAME or not PASSWORD:
    print("ERROR: Credentials required")
    sys.exit(1)

# Disable SSL warnings for testing (enable verification in production)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_authentication():
    """
    Test 1: Authenticate and get authtoken
    """
    print("\n" + "="*60)
    print("TEST 1: AUTHENTICATION")
    print("="*60)

    auth_url = f"{SERVER_URL}/api/1.3/desktop/authentication"

    # Base64 encode password
    password_b64 = base64.b64encode(PASSWORD.encode()).decode()

    # Try local authentication first
    params = {
        'username': USERNAME,
        'password': password_b64,
        'auth_type': 'local_authentication'
    }

    try:
        print(f"Authenticating as: {USERNAME}")
        print(f"Server: {SERVER_URL}")

        response = requests.get(
            auth_url,
            params=params,
            timeout=30,
            verify=False  # For testing - enable in production
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            authtoken = data.get('message_response', {}).get('authentication', {}).get('authtoken')

            if authtoken:
                print(f"✅ Authentication SUCCESS")
                print(f"Auth Token: {authtoken[:20]}... (truncated)")
                return authtoken
            else:
                print(f"❌ No authtoken in response")
                print(f"Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print(f"❌ Authentication FAILED")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None

def test_server_properties(authtoken):
    """
    Test 2: Get server properties
    """
    print("\n" + "="*60)
    print("TEST 2: SERVER PROPERTIES")
    print("="*60)

    url = f"{SERVER_URL}/api/1.4/desktop/serverproperties"
    headers = {'Authorization': authtoken}

    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server Properties Retrieved")
            print(f"Response:\n{json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Failed to get server properties")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None

def test_patch_listing(authtoken):
    """
    Test 3: List patches (first 5 only)
    """
    print("\n" + "="*60)
    print("TEST 3: PATCH LISTING (Sample)")
    print("="*60)

    url = f"{SERVER_URL}/api/1.4/patch/allpatches"
    headers = {'Authorization': authtoken}
    params = {
        'limit': 5,  # Only get 5 patches for testing
        'page': 1
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            total_patches = data.get('message_response', {}).get('total', 0)
            patches = data.get('message_response', {}).get('allpatches', [])

            print(f"✅ Patch Listing Retrieved")
            print(f"Total Patches Available: {total_patches}")
            print(f"Sample Patches Retrieved: {len(patches)}")

            if patches:
                print(f"\nSample Patch Details:")
                for i, patch in enumerate(patches[:3], 1):
                    print(f"\n  Patch {i}:")
                    print(f"    ID: {patch.get('patchid')}")
                    print(f"    Name: {patch.get('patch_name')}")
                    print(f"    Severity: {patch.get('severity')}")
                    print(f"    Bulletin ID: {patch.get('bulletinid')}")
                    print(f"    Missing: {patch.get('missing', 0)} endpoints")

            return data
        else:
            print(f"❌ Failed to list patches")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None

def test_approval_settings(authtoken):
    """
    Test 4: Get approval settings
    """
    print("\n" + "="*60)
    print("TEST 4: APPROVAL SETTINGS")
    print("="*60)

    url = f"{SERVER_URL}/api/1.4/patch/approvalsettings"
    headers = {'Authorization': authtoken}

    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            approval_mode = data.get('message_response', {}).get('approvalsettings', {}).get('patch_approval', 'unknown')

            print(f"✅ Approval Settings Retrieved")
            print(f"Approval Mode: {approval_mode}")
            print(f"Response:\n{json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Failed to get approval settings")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None

def test_deployment_policies(authtoken):
    """
    Test 5: List deployment policies
    """
    print("\n" + "="*60)
    print("TEST 5: DEPLOYMENT POLICIES")
    print("="*60)

    url = f"{SERVER_URL}/api/1.4/patch/deploymentpolicies"
    headers = {'Authorization': authtoken}

    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Deployment Policies Retrieved")
            print(f"Response:\n{json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Failed to get deployment policies")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("MANAGEENGINE PATCH MANAGER PLUS - API ACCESS TEST")
    print(f"Timestamp: {datetime.now()}")
    print("="*60)

    # Test 1: Authentication
    authtoken = test_authentication()

    if not authtoken:
        print("\n❌ CRITICAL: Authentication failed - cannot proceed with API tests")
        print("\nTroubleshooting:")
        print("  1. Verify username and password are correct")
        print("  2. Confirm account has API access enabled in Patch Manager Plus")
        print("  3. Check if account is 'local' or 'AD' (may need auth_type=ad_authentication)")
        print("  4. Verify server URL is correct (https://patch.manageengine.com.au)")
        return

    # Test 2: Server Properties
    test_server_properties(authtoken)

    # Test 3: Patch Listing
    test_patch_listing(authtoken)

    # Test 4: Approval Settings
    test_approval_settings(authtoken)

    # Test 5: Deployment Policies
    test_deployment_policies(authtoken)

    print("\n" + "="*60)
    print("API ACCESS TEST COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("  1. Review test results above")
    print("  2. If all tests passed, API access is working correctly")
    print("  3. You can now use the Patch Manager Plus API Specialist Agent")
    print("  4. Set environment variables for automation:")
    print(f"     export PMP_USERNAME='{USERNAME}'")
    print(f"     export PMP_PASSWORD='your_password'  # Store securely")

if __name__ == "__main__":
    main()
