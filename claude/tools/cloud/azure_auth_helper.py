#!/usr/bin/env python3
"""
Azure Authentication Helper

Provides authentication status checking and helper functions for Azure CLI access.
Used by agents to verify Azure access before attempting operations.

Usage:
    python3 claude/tools/cloud/azure_auth_helper.py status
    python3 claude/tools/cloud/azure_auth_helper.py subscription
    python3 claude/tools/cloud/azure_auth_helper.py verify
"""

import json
import subprocess
import sys
from typing import Dict, Optional


VS_ENTERPRISE_SUBSCRIPTION_ID = "9b8e7b3f-d3e7-4da9-a22a-9bf7c8ee4dde"
VS_ENTERPRISE_SUBSCRIPTION_NAME = "Visual Studio Enterprise Subscription – MPN"


def run_az_command(args: list) -> tuple[bool, str, str]:
    """
    Run an Azure CLI command and return success status and output.

    Args:
        args: Command arguments (without 'az' prefix)

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["az"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "Azure CLI not installed"
    except Exception as e:
        return False, "", str(e)


def check_auth_status() -> Dict[str, any]:
    """
    Check Azure CLI authentication status.

    Returns:
        Dictionary with authentication status details
    """
    success, stdout, stderr = run_az_command(["account", "show", "--output", "json"])

    if not success:
        return {
            "authenticated": False,
            "error": stderr or "Not authenticated",
            "subscription": None
        }

    try:
        account_info = json.loads(stdout)
        return {
            "authenticated": True,
            "subscription_id": account_info.get("id"),
            "subscription_name": account_info.get("name"),
            "tenant_id": account_info.get("tenantId"),
            "user": account_info.get("user", {}).get("name"),
            "is_default": account_info.get("isDefault"),
            "is_vs_enterprise": account_info.get("id") == VS_ENTERPRISE_SUBSCRIPTION_ID,
            "error": None
        }
    except json.JSONDecodeError:
        return {
            "authenticated": False,
            "error": "Failed to parse account information",
            "subscription": None
        }


def get_subscription_info() -> Optional[Dict[str, any]]:
    """
    Get VS Enterprise subscription information.

    Returns:
        Subscription details or None if not found
    """
    success, stdout, stderr = run_az_command(["account", "list", "--output", "json"])

    if not success:
        return None

    try:
        accounts = json.loads(stdout)
        for account in accounts:
            if account.get("id") == VS_ENTERPRISE_SUBSCRIPTION_ID:
                return account
        return None
    except json.JSONDecodeError:
        return None


def verify_access() -> Dict[str, any]:
    """
    Verify full Azure access by testing common operations.

    Returns:
        Dictionary with verification results
    """
    results = {
        "auth_check": False,
        "subscription_check": False,
        "resource_list_check": False,
        "errors": []
    }

    # Check authentication
    auth_status = check_auth_status()
    if auth_status["authenticated"]:
        results["auth_check"] = True
    else:
        results["errors"].append(f"Auth failed: {auth_status['error']}")
        return results

    # Check VS Enterprise subscription
    if auth_status["is_vs_enterprise"]:
        results["subscription_check"] = True
    else:
        results["errors"].append(
            f"Wrong subscription: {auth_status['subscription_name']} "
            f"(expected {VS_ENTERPRISE_SUBSCRIPTION_NAME})"
        )

    # Test resource listing
    success, stdout, stderr = run_az_command(["group", "list", "--output", "json"])
    if success:
        results["resource_list_check"] = True
    else:
        results["errors"].append(f"Resource list failed: {stderr}")

    return results


def print_status():
    """Print authentication status in human-readable format."""
    auth_status = check_auth_status()

    print("=== Azure Authentication Status ===\n")

    if auth_status["authenticated"]:
        print(f"✅ Authenticated: Yes")
        print(f"   User: {auth_status['user']}")
        print(f"   Subscription: {auth_status['subscription_name']}")
        print(f"   Subscription ID: {auth_status['subscription_id']}")
        print(f"   Tenant ID: {auth_status['tenant_id']}")
        print(f"   Is Default: {auth_status['is_default']}")
        print(f"   Is VS Enterprise: {'✅ Yes' if auth_status['is_vs_enterprise'] else '❌ No'}")

        if not auth_status['is_vs_enterprise']:
            print(f"\n⚠️  Current subscription is not VS Enterprise.")
            print(f"   Run: az account set --subscription '{VS_ENTERPRISE_SUBSCRIPTION_ID}'")
    else:
        print(f"❌ Authenticated: No")
        print(f"   Error: {auth_status['error']}")
        print(f"\n📝 To authenticate:")
        print(f"   az login --use-device-code")
        print(f"   az account set --subscription '{VS_ENTERPRISE_SUBSCRIPTION_ID}'")


def print_subscription():
    """Print VS Enterprise subscription information."""
    sub_info = get_subscription_info()

    print("=== VS Enterprise Subscription ===\n")

    if sub_info:
        print(f"Name: {sub_info.get('name')}")
        print(f"ID: {sub_info.get('id')}")
        print(f"State: {sub_info.get('state')}")
        print(f"Tenant: {sub_info.get('tenantDisplayName')} ({sub_info.get('tenantId')})")
        print(f"User: {sub_info.get('user', {}).get('name')}")
        print(f"Is Default: {sub_info.get('isDefault')}")
    else:
        print("❌ VS Enterprise subscription not found")
        print("\nAvailable subscriptions:")
        success, stdout, _ = run_az_command(["account", "list", "--output", "table"])
        if success:
            print(stdout)


def print_verify():
    """Print verification results."""
    results = verify_access()

    print("=== Azure Access Verification ===\n")
    print(f"Authentication: {'✅ Pass' if results['auth_check'] else '❌ Fail'}")
    print(f"Subscription: {'✅ Pass' if results['subscription_check'] else '❌ Fail'}")
    print(f"Resource Access: {'✅ Pass' if results['resource_list_check'] else '❌ Fail'}")

    if results['errors']:
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"   - {error}")
    else:
        print(f"\n✅ All checks passed - Azure access is configured correctly")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: azure_auth_helper.py {status|subscription|verify}")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "status":
        print_status()
    elif command == "subscription":
        print_subscription()
    elif command == "verify":
        print_verify()
    else:
        print(f"Unknown command: {command}")
        print("Usage: azure_auth_helper.py {status|subscription|verify}")
        sys.exit(1)


if __name__ == "__main__":
    main()
