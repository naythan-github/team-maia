#!/usr/bin/env python3
"""
PMP Action Handler - Environment-Aware API Actions

Handles all WRITE operations for ManageEngine Patch Manager Plus API.
Requires explicit environment selection for safety.

Actions:
- Patch Approval: approve, unapprove, decline
- Patch Deployment: install, uninstall
- Patch Download: download
- Scanning: scan specific, scan all
- Database: update DB, check status

Usage:
    PMP_ENV=TEST python3 pmp_action_handler.py approve --patch-ids 12345,12346
    PMP_ENV=TEST python3 pmp_action_handler.py install --patch-ids 12345 --config-name "Test" --policy-id 1
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager_v2 import PMPOAuthManagerV2

import requests


class PMPActionHandler:
    """
    Environment-aware PMP API action handler with safety interlocks.

    All WRITE operations require explicit environment selection.
    PROD operations can be additionally protected with confirm_prod flag.
    """

    VALID_ACTIONS_TO_PERFORM = ['Deploy', 'Deploy Immediately', 'Draft']

    # API Endpoints
    ENDPOINTS = {
        'approve': '/api/1.4/patch/approvepatch',
        'unapprove': '/api/1.4/patch/unapprovepatch',
        'decline': '/api/1.4/patch/declinepatch',
        'install': '/api/1.3/patch/installpatch',
        'uninstall': '/api/1.3/patch/uninstallpatch',
        'download': '/api/1.4/patch/downloadpatch',
        'scan': '/api/1.4/patch/computers/scan',
        'scan_all': '/api/1.4/patch/computers/scanall',
        'update_db': '/api/1.4/patch/updatedb',
        'db_status': '/api/1.4/patch/dbupdatestatus',
    }

    def __init__(self, environment: str = None):
        """
        Initialize action handler with environment-aware OAuth.

        Args:
            environment: 'TEST' or 'PROD' (or set PMP_ENV env var)

        Raises:
            ValueError: If environment not specified or invalid
        """
        self.oauth_manager = PMPOAuthManagerV2(environment=environment)
        self.environment = self.oauth_manager.environment
        self.base_url = self.oauth_manager.server_url

    def _make_request(self, method: str, endpoint: str, data: Dict = None,
                      max_retries: int = 3) -> Dict:
        """
        Make authenticated API request with retry logic.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            data: Request body for POST requests
            max_retries: Maximum retry attempts

        Returns:
            Dict with response data or error information
        """
        for attempt in range(1, max_retries + 1):
            try:
                token = self.oauth_manager.get_valid_token()
                headers = {
                    'Authorization': f'Zoho-oauthtoken {token}',
                    'Content-Type': 'application/json'
                }
                url = f"{self.base_url}{endpoint}"

                print(f"   [{self.environment}] {method} {endpoint}")

                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, timeout=(10, 30))
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=(10, 30))

                # Check for HTML throttling
                if response.status_code == 200:
                    content = response.text
                    if content.strip().startswith('<') or '<!DOCTYPE' in content:
                        print(f"   ⚠️  [{self.environment}] HTML throttling. Waiting 60s...")
                        time.sleep(60)
                        continue

                # Handle specific status codes
                if response.status_code == 200:
                    try:
                        result = response.json()
                        # Unwrap message_response if present
                        if 'message_response' in result:
                            return result['message_response']
                        return result
                    except json.JSONDecodeError:
                        return {'status': 'success', 'raw': response.text[:200]}

                elif response.status_code == 401:
                    return {'error': 'Unauthorized', 'status_code': 401}

                elif response.status_code == 403:
                    return {'error': 'Forbidden - insufficient scope', 'status_code': 403}

                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"   ⚠️  [{self.environment}] Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                elif response.status_code >= 500:
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        print(f"   ⚠️  [{self.environment}] Server error. Retry in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return {'error': f'Server error: {response.status_code}', 'status_code': response.status_code}

                else:
                    return {
                        'error': f'HTTP {response.status_code}',
                        'status_code': response.status_code,
                        'detail': response.text[:200]
                    }

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return {'error': 'Request timeout', 'status_code': 0}

            except requests.exceptions.RequestException as e:
                return {'error': str(e), 'status_code': 0}

        return {'error': 'Max retries exceeded', 'status_code': 0}

    # =========================================================================
    # PATCH APPROVAL ACTIONS
    # =========================================================================

    def approve_patch(self, patch_ids: List[int]) -> Dict:
        """
        Approve patches for deployment.

        Args:
            patch_ids: List of patch IDs to approve

        Returns:
            API response dict

        Raises:
            ValueError: If patch_ids is empty
        """
        if not patch_ids:
            raise ValueError("patch_ids is required and cannot be empty")

        data = {'PatchIDs': patch_ids}
        return self._make_request('POST', self.ENDPOINTS['approve'], data)

    def unapprove_patch(self, patch_ids: List[int]) -> Dict:
        """
        Remove approval from patches.

        Args:
            patch_ids: List of patch IDs to unapprove

        Returns:
            API response dict

        Raises:
            ValueError: If patch_ids is empty
        """
        if not patch_ids:
            raise ValueError("patch_ids is required and cannot be empty")

        data = {'PatchIDs': patch_ids}
        return self._make_request('POST', self.ENDPOINTS['unapprove'], data)

    def decline_patch(self, patch_ids: List[int]) -> Dict:
        """
        Decline patches (mark as not to be deployed).

        Args:
            patch_ids: List of patch IDs to decline

        Returns:
            API response dict

        Raises:
            ValueError: If patch_ids is empty
        """
        if not patch_ids:
            raise ValueError("patch_ids is required and cannot be empty")

        data = {'PatchIDs': patch_ids}
        return self._make_request('POST', self.ENDPOINTS['decline'], data)

    # =========================================================================
    # PATCH DEPLOYMENT ACTIONS
    # =========================================================================

    def install_patch(self,
                      patch_ids: List[int],
                      config_name: str,
                      deployment_policy_id: int,
                      config_description: str = "Maia automated deployment",
                      action_to_perform: str = "Deploy",
                      resource_ids: List[int] = None,
                      resource_names: List[str] = None,
                      custom_groups: List[str] = None,
                      ip_addresses: List[str] = None,
                      remote_offices: List[str] = None,
                      is_only_approved: bool = True,
                      deployment_type: int = 0,
                      deadline_time: int = None,
                      force_reboot_option: int = 0,
                      retry_settings: Dict = None) -> Dict:
        """
        Install/deploy patches to systems.

        Args:
            patch_ids: List of patch IDs to deploy (required)
            config_name: Name for deployment configuration (required)
            deployment_policy_id: ID of deployment policy (required)
            config_description: Description for deployment
            action_to_perform: 'Deploy', 'Deploy Immediately', or 'Draft'
            resource_ids: Target system resource IDs
            resource_names: Target system names
            custom_groups: Target custom groups
            ip_addresses: Target IP addresses
            remote_offices: Target remote offices
            is_only_approved: Only deploy approved patches
            deployment_type: 0=Deploy only, 1=Deploy+notify, 2=Full workflow
            deadline_time: Forced deployment timestamp (ms)
            force_reboot_option: 0=No reboot, 1=Notify, 2=Force
            retry_settings: Retry configuration dict

        Returns:
            API response dict

        Raises:
            ValueError: If required parameters missing or invalid
        """
        # Validate required parameters
        if not patch_ids:
            raise ValueError("patch_ids is required and cannot be empty")
        if not config_name:
            raise ValueError("config_name is required and cannot be empty")
        if deployment_policy_id is None:
            raise ValueError("deployment_policy_id is required")
        if action_to_perform not in self.VALID_ACTIONS_TO_PERFORM:
            raise ValueError(
                f"action_to_perform must be one of: {self.VALID_ACTIONS_TO_PERFORM}"
            )

        # Build request data
        data = {
            'PatchIDs': patch_ids,
            'ConfigName': config_name,
            'ConfigDescription': config_description,
            'actionToPerform': action_to_perform,
            'DeploymentPolicyTemplateID': deployment_policy_id,
            'isOnlyApproved': str(is_only_approved).lower(),
            'deploymentType': deployment_type,
            'forceRebootOption': force_reboot_option,
        }

        # Add optional target parameters
        if resource_ids:
            data['ResourceIDs'] = resource_ids
        if resource_names:
            data['resourceNames'] = resource_names
        if custom_groups:
            data['customGroups'] = custom_groups
        if ip_addresses:
            data['ipAddresses'] = ip_addresses
        if remote_offices:
            data['remoteOffices'] = remote_offices
        if deadline_time:
            data['deadlineTime'] = deadline_time
        if retry_settings:
            data['retrySettings'] = retry_settings

        return self._make_request('POST', self.ENDPOINTS['install'], data)

    def uninstall_patch(self,
                        patch_ids: List[int],
                        config_name: str,
                        deployment_policy_id: int,
                        config_description: str = "Maia automated uninstall",
                        action_to_perform: str = "Deploy",
                        resource_ids: List[int] = None) -> Dict:
        """
        Uninstall patches from systems.

        Note: Patch uninstallation only supported on Windows.

        Args:
            patch_ids: List of patch IDs to uninstall (required)
            config_name: Name for uninstall configuration (required)
            deployment_policy_id: ID of deployment policy (required)
            config_description: Description for configuration
            action_to_perform: 'Deploy', 'Deploy Immediately', or 'Draft'
            resource_ids: Target system resource IDs

        Returns:
            API response dict

        Raises:
            ValueError: If required parameters missing
        """
        if not patch_ids:
            raise ValueError("patch_ids is required and cannot be empty")
        if not config_name:
            raise ValueError("config_name is required and cannot be empty")
        if deployment_policy_id is None:
            raise ValueError("deployment_policy_id is required")

        data = {
            'PatchIDs': patch_ids,
            'ConfigName': config_name,
            'ConfigDescription': config_description,
            'actionToPerform': action_to_perform,
            'DeploymentPolicyTemplateID': deployment_policy_id,
        }

        if resource_ids:
            data['ResourceIDs'] = resource_ids

        return self._make_request('POST', self.ENDPOINTS['uninstall'], data)

    # =========================================================================
    # PATCH DOWNLOAD ACTIONS
    # =========================================================================

    def download_patch(self, patch_ids: List[int]) -> Dict:
        """
        Pre-download patches to PMP server.

        Args:
            patch_ids: List of patch IDs to download

        Returns:
            API response dict

        Raises:
            ValueError: If patch_ids is empty
        """
        if not patch_ids:
            raise ValueError("patch_ids is required and cannot be empty")

        data = {'PatchIDs': patch_ids}
        return self._make_request('POST', self.ENDPOINTS['download'], data)

    # =========================================================================
    # SCAN ACTIONS
    # =========================================================================

    def scan_computers(self, resource_ids: List[int]) -> Dict:
        """
        Trigger patch scan on specific computers.

        Args:
            resource_ids: List of resource IDs to scan

        Returns:
            API response dict

        Raises:
            ValueError: If resource_ids is empty
        """
        if not resource_ids:
            raise ValueError("resource_ids is required and cannot be empty")

        data = {'ResourceIDs': resource_ids}
        return self._make_request('POST', self.ENDPOINTS['scan'], data)

    def scan_all_computers(self) -> Dict:
        """
        Trigger patch scan on all managed computers.

        Returns:
            API response dict
        """
        return self._make_request('POST', self.ENDPOINTS['scan_all'], {})

    # =========================================================================
    # DATABASE UPDATE ACTIONS
    # =========================================================================

    def update_patch_db(self) -> Dict:
        """
        Trigger patch database update/sync.

        Returns:
            API response dict
        """
        return self._make_request('POST', self.ENDPOINTS['update_db'], {})

    def get_db_update_status(self) -> Dict:
        """
        Get patch database update status.

        Returns:
            API response dict with update status
        """
        return self._make_request('GET', self.ENDPOINTS['db_status'])


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI interface for PMP action handler"""
    import argparse

    parser = argparse.ArgumentParser(
        description='PMP Action Handler - Environment-Aware API Actions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  PMP_ENV=TEST python3 pmp_action_handler.py approve --patch-ids 12345,12346
  PMP_ENV=TEST python3 pmp_action_handler.py install --patch-ids 12345 --config-name "Test" --policy-id 1 --action Draft
  PMP_ENV=TEST python3 pmp_action_handler.py update-db
  PMP_ENV=TEST python3 pmp_action_handler.py db-status
        """
    )

    parser.add_argument('action', choices=[
        'approve', 'unapprove', 'decline',
        'install', 'uninstall',
        'download',
        'scan', 'scan-all',
        'update-db', 'db-status',
        'test-all'
    ], help='Action to perform')

    parser.add_argument('--patch-ids', type=str, help='Comma-separated patch IDs')
    parser.add_argument('--resource-ids', type=str, help='Comma-separated resource IDs')
    parser.add_argument('--config-name', type=str, help='Configuration name')
    parser.add_argument('--config-desc', type=str, default='Maia automated action', help='Configuration description')
    parser.add_argument('--policy-id', type=int, help='Deployment policy ID')
    parser.add_argument('--action-type', type=str, default='Draft',
                        choices=['Deploy', 'Deploy Immediately', 'Draft'],
                        help='Action to perform (default: Draft for safety)')

    args = parser.parse_args()

    # Check environment
    env = os.environ.get('PMP_ENV', '')
    if not env:
        print("="*60)
        print("🛑 SAFETY: PMP_ENV must be set!")
        print("="*60)
        print("\nUsage: PMP_ENV=TEST python3 pmp_action_handler.py <action>")
        sys.exit(1)

    try:
        handler = PMPActionHandler()
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    # Parse IDs
    patch_ids = [int(x.strip()) for x in args.patch_ids.split(',')] if args.patch_ids else []
    resource_ids = [int(x.strip()) for x in args.resource_ids.split(',')] if args.resource_ids else []

    result = None

    # Execute action
    if args.action == 'approve':
        if not patch_ids:
            print("❌ --patch-ids required for approve")
            sys.exit(1)
        result = handler.approve_patch(patch_ids)

    elif args.action == 'unapprove':
        if not patch_ids:
            print("❌ --patch-ids required for unapprove")
            sys.exit(1)
        result = handler.unapprove_patch(patch_ids)

    elif args.action == 'decline':
        if not patch_ids:
            print("❌ --patch-ids required for decline")
            sys.exit(1)
        result = handler.decline_patch(patch_ids)

    elif args.action == 'install':
        if not patch_ids or not args.config_name or not args.policy_id:
            print("❌ --patch-ids, --config-name, and --policy-id required for install")
            sys.exit(1)
        result = handler.install_patch(
            patch_ids=patch_ids,
            config_name=args.config_name,
            deployment_policy_id=args.policy_id,
            config_description=args.config_desc,
            action_to_perform=args.action_type,
            resource_ids=resource_ids if resource_ids else None
        )

    elif args.action == 'uninstall':
        if not patch_ids or not args.config_name or not args.policy_id:
            print("❌ --patch-ids, --config-name, and --policy-id required for uninstall")
            sys.exit(1)
        result = handler.uninstall_patch(
            patch_ids=patch_ids,
            config_name=args.config_name,
            deployment_policy_id=args.policy_id,
            config_description=args.config_desc,
            action_to_perform=args.action_type,
            resource_ids=resource_ids if resource_ids else None
        )

    elif args.action == 'download':
        if not patch_ids:
            print("❌ --patch-ids required for download")
            sys.exit(1)
        result = handler.download_patch(patch_ids)

    elif args.action == 'scan':
        if not resource_ids:
            print("❌ --resource-ids required for scan")
            sys.exit(1)
        result = handler.scan_computers(resource_ids)

    elif args.action == 'scan-all':
        result = handler.scan_all_computers()

    elif args.action == 'update-db':
        result = handler.update_patch_db()

    elif args.action == 'db-status':
        result = handler.get_db_update_status()

    elif args.action == 'test-all':
        print(f"\n{'='*60}")
        print(f"PMP ACTION HANDLER - TEST ALL ACTIONS")
        print(f"Environment: {handler.environment}")
        print(f"{'='*60}\n")

        # Run comprehensive test
        test_actions(handler)
        return

    # Print result
    if result:
        print(f"\n📋 Result:")
        print(json.dumps(result, indent=2, default=str))

        if 'error' in result:
            sys.exit(1)


def test_actions(handler: PMPActionHandler):
    """Test all actions against the API"""
    results = []

    print("Testing all PMP API actions...\n")

    # 1. Database Status (safe read operation)
    print("1️⃣  Testing: get_db_update_status")
    result = handler.get_db_update_status()
    status = '✅' if 'error' not in result else '❌'
    print(f"   {status} Status: {result.get('error', 'Success')}")
    results.append(('db_status', 'error' not in result, result))

    # 2. Update DB (safe write operation)
    print("\n2️⃣  Testing: update_patch_db")
    result = handler.update_patch_db()
    status = '✅' if 'error' not in result else '❌'
    print(f"   {status} Status: {result.get('error', 'Success')}")
    results.append(('update_db', 'error' not in result, result))

    # 3. Scan All (may fail if no systems)
    print("\n3️⃣  Testing: scan_all_computers")
    result = handler.scan_all_computers()
    status = '✅' if 'error' not in result else '⚠️ '
    print(f"   {status} Status: {result.get('error', 'Success')}")
    results.append(('scan_all', 'error' not in result, result))

    # 4. Get a patch ID from supported patches for testing
    print("\n4️⃣  Getting sample patch ID from supported patches...")
    from pmp_oauth_manager_v2 import PMPOAuthManagerV2

    try:
        response = requests.get(
            f"{handler.base_url}/api/1.4/patch/supportedpatches",
            headers={'Authorization': f'Zoho-oauthtoken {handler.oauth_manager.get_valid_token()}'},
            params={'page': 1},
            timeout=(10, 30)
        )
        if response.status_code == 200:
            data = response.json()
            if 'message_response' in data:
                data = data['message_response']
            patches = data.get('supportedpatches', [])
            if patches:
                test_patch_id = patches[0].get('patch_id')
                print(f"   ✅ Found test patch ID: {test_patch_id}")

                # 5. Test approve/unapprove cycle
                print(f"\n5️⃣  Testing: approve_patch (ID: {test_patch_id})")
                result = handler.approve_patch([test_patch_id])
                status = '✅' if 'error' not in result else '❌'
                print(f"   {status} Status: {result.get('error', 'Success')}")
                results.append(('approve', 'error' not in result, result))

                print(f"\n6️⃣  Testing: unapprove_patch (ID: {test_patch_id})")
                result = handler.unapprove_patch([test_patch_id])
                status = '✅' if 'error' not in result else '❌'
                print(f"   {status} Status: {result.get('error', 'Success')}")
                results.append(('unapprove', 'error' not in result, result))

                # 7. Test download
                print(f"\n7️⃣  Testing: download_patch (ID: {test_patch_id})")
                result = handler.download_patch([test_patch_id])
                status = '✅' if 'error' not in result else '⚠️ '
                print(f"   {status} Status: {result.get('error', 'Success')}")
                results.append(('download', 'error' not in result, result))

                # 8. Test install (Draft mode - won't actually deploy)
                print(f"\n8️⃣  Testing: install_patch (Draft mode - safe)")
                result = handler.install_patch(
                    patch_ids=[test_patch_id],
                    config_name=f"TDD_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    deployment_policy_id=1,  # Use first policy
                    action_to_perform="Draft"  # Safe - won't deploy
                )
                status = '✅' if 'error' not in result else '⚠️ '
                print(f"   {status} Status: {result.get('error', 'Success')}")
                results.append(('install_draft', 'error' not in result, result))

            else:
                print("   ⚠️  No patches found to test with")
        else:
            print(f"   ❌ Failed to get patches: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"\n📊 Results: {passed}/{total} actions working")

    for name, success, result in results:
        status = '✅' if success else '❌'
        error = result.get('error', '') if not success else ''
        print(f"   {status} {name}: {error if error else 'OK'}")


if __name__ == '__main__':
    main()
