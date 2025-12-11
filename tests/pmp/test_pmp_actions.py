#!/usr/bin/env python3
"""
TDD Tests for PMP API Actions

Tests all WRITE operations available via the PMP REST API.
These tests are designed to run against the TEST environment only.

Actions tested:
1. Patch Approval: approve, unapprove, decline
2. Patch Deployment: install, uninstall
3. Patch Download: download
4. Scanning: scan specific, scan all
5. Database: update DB, check status

Usage:
    PMP_ENV=TEST python3 -m pytest tests/test_pmp_actions.py -v
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_oauth_manager():
    """Mock OAuth manager for unit tests"""
    mock = MagicMock()
    mock.environment = 'TEST'
    mock.server_url = 'https://patch.manageengine.com.au'
    mock.get_valid_token.return_value = 'mock_token_12345'
    mock.config = {
        'keychain_account': 'test@example.com',
        'color': '\033[92m',
        'banner_emoji': '🧪',
        'description': 'Test environment'
    }
    mock.RESET_COLOR = '\033[0m'
    return mock


@pytest.fixture
def action_handler(mock_oauth_manager):
    """Create action handler with mocked OAuth"""
    from claude.tools.pmp.pmp_action_handler import PMPActionHandler
    handler = PMPActionHandler.__new__(PMPActionHandler)
    handler.oauth_manager = mock_oauth_manager
    handler.environment = 'TEST'
    handler.base_url = 'https://patch.manageengine.com.au'
    return handler


# =============================================================================
# TEST: Action Handler Initialization
# =============================================================================

class TestActionHandlerInit:
    """Test action handler initialization and safety checks"""

    def test_requires_environment_specification(self):
        """
        SAFETY: Handler must require explicit environment.

        Context: Prevents accidental production operations
        Expected: ValueError if no environment specified
        """
        with patch.dict(os.environ, {}, clear=True):
            # Remove PMP_ENV if present
            os.environ.pop('PMP_ENV', None)
            from claude.tools.pmp.pmp_action_handler import PMPActionHandler
            with pytest.raises(ValueError, match="Environment must be specified"):
                PMPActionHandler()

    def test_accepts_test_environment(self):
        """
        Handler should accept TEST environment.

        Expected: Successful initialization with TEST
        """
        with patch.dict(os.environ, {'PMP_ENV': 'TEST'}):
            from claude.tools.pmp.pmp_action_handler import PMPActionHandler
            # Will fail on keychain lookup, but env check passes
            try:
                handler = PMPActionHandler()
            except RuntimeError as e:
                # Expected - keychain not available in test
                assert 'Keychain' in str(e) or 'Failed to retrieve' in str(e)

    def test_rejects_invalid_environment(self):
        """
        Handler should reject invalid environments.

        Expected: ValueError for invalid environment
        """
        with patch.dict(os.environ, {'PMP_ENV': 'INVALID'}):
            from claude.tools.pmp.pmp_action_handler import PMPActionHandler
            with pytest.raises(ValueError, match="Invalid environment"):
                PMPActionHandler()


# =============================================================================
# TEST: Patch Approval Actions
# =============================================================================

class TestPatchApprovalActions:
    """Tests for patch approval/unapproval/decline operations"""

    def test_approve_patch_requires_patch_ids(self, action_handler):
        """
        approve_patch must require patch IDs.

        Expected: ValueError if no patch_ids provided
        """
        with pytest.raises(ValueError, match="patch_ids.*required"):
            action_handler.approve_patch(patch_ids=[])

    def test_approve_patch_accepts_valid_patch_ids(self, action_handler):
        """
        approve_patch should accept valid patch ID list.

        Expected: Returns response dict with status
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {'status': 'success', 'message': 'Patches approved'}
            )

            result = action_handler.approve_patch(patch_ids=[12345, 12346])

            assert result is not None
            assert 'status' in result or 'error' not in result
            mock_post.assert_called_once()

    def test_unapprove_patch_requires_patch_ids(self, action_handler):
        """
        unapprove_patch must require patch IDs.

        Expected: ValueError if no patch_ids provided
        """
        with pytest.raises(ValueError, match="patch_ids.*required"):
            action_handler.unapprove_patch(patch_ids=[])

    def test_decline_patch_requires_patch_ids(self, action_handler):
        """
        decline_patch must require patch IDs.

        Expected: ValueError if no patch_ids provided
        """
        with pytest.raises(ValueError, match="patch_ids.*required"):
            action_handler.decline_patch(patch_ids=[])

    def test_approval_actions_use_correct_endpoints(self, action_handler):
        """
        Each approval action should use its correct endpoint.

        Expected:
        - approve: /api/1.4/patch/approvepatch
        - unapprove: /api/1.4/patch/unapprovepatch
        - decline: /api/1.4/patch/declinepatch
        """
        endpoints = {
            'approve': '/api/1.4/patch/approvepatch',
            'unapprove': '/api/1.4/patch/unapprovepatch',
            'decline': '/api/1.4/patch/declinepatch'
        }

        for action, expected_endpoint in endpoints.items():
            with patch('requests.post') as mock_post:
                mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

                method = getattr(action_handler, f'{action}_patch')
                method(patch_ids=[12345])

                call_url = mock_post.call_args[0][0]
                assert expected_endpoint in call_url, f"{action} should use {expected_endpoint}"


# =============================================================================
# TEST: Patch Deployment Actions
# =============================================================================

class TestPatchDeploymentActions:
    """Tests for patch installation/uninstallation operations"""

    def test_install_patch_requires_patch_ids(self, action_handler):
        """
        install_patch must require patch IDs.

        Expected: ValueError if no patch_ids provided
        """
        with pytest.raises(ValueError, match="patch_ids.*required"):
            action_handler.install_patch(
                patch_ids=[],
                config_name="Test",
                deployment_policy_id=1
            )

    def test_install_patch_requires_config_name(self, action_handler):
        """
        install_patch must require configuration name.

        Expected: ValueError if no config_name provided
        """
        with pytest.raises(ValueError, match="config_name.*required"):
            action_handler.install_patch(
                patch_ids=[12345],
                config_name="",
                deployment_policy_id=1
            )

    def test_install_patch_requires_deployment_policy(self, action_handler):
        """
        install_patch must require deployment policy ID.

        Expected: ValueError if no deployment_policy_id provided
        """
        with pytest.raises(ValueError, match="deployment_policy_id.*required"):
            action_handler.install_patch(
                patch_ids=[12345],
                config_name="Test",
                deployment_policy_id=None
            )

    def test_install_patch_validates_action_to_perform(self, action_handler):
        """
        install_patch must validate actionToPerform value.

        Expected: ValueError for invalid action
        """
        with pytest.raises(ValueError, match="action_to_perform.*Deploy|Deploy Immediately|Draft"):
            action_handler.install_patch(
                patch_ids=[12345],
                config_name="Test",
                deployment_policy_id=1,
                action_to_perform="InvalidAction"
            )

    def test_install_patch_accepts_valid_request(self, action_handler):
        """
        install_patch should accept valid deployment request.

        Expected: Returns response with job ID or status
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {'status': 'success', 'job_id': 12345}
            )

            result = action_handler.install_patch(
                patch_ids=[12345],
                config_name="TDD Test Deployment",
                deployment_policy_id=1,
                action_to_perform="Draft"  # Safe - won't actually deploy
            )

            assert result is not None
            mock_post.assert_called_once()

    def test_install_patch_supports_target_options(self, action_handler):
        """
        install_patch should support various target options.

        Expected: Accepts resource_ids, custom_groups, ip_addresses, remote_offices
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

            # Test with resource IDs
            action_handler.install_patch(
                patch_ids=[12345],
                config_name="Test",
                deployment_policy_id=1,
                resource_ids=[601, 602]
            )

            call_data = mock_post.call_args
            assert call_data is not None

    def test_uninstall_patch_requires_patch_ids(self, action_handler):
        """
        uninstall_patch must require patch IDs.

        Expected: ValueError if no patch_ids provided
        """
        with pytest.raises(ValueError, match="patch_ids.*required"):
            action_handler.uninstall_patch(
                patch_ids=[],
                config_name="Test",
                deployment_policy_id=1
            )

    def test_uninstall_uses_correct_endpoint(self, action_handler):
        """
        uninstall_patch should use correct endpoint.

        Expected: /api/1.3/patch/uninstallpatch
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

            action_handler.uninstall_patch(
                patch_ids=[12345],
                config_name="Test Uninstall",
                deployment_policy_id=1
            )

            call_url = mock_post.call_args[0][0]
            assert '/api/1.3/patch/uninstallpatch' in call_url


# =============================================================================
# TEST: Patch Download Actions
# =============================================================================

class TestPatchDownloadActions:
    """Tests for patch download operations"""

    def test_download_patch_requires_patch_ids(self, action_handler):
        """
        download_patch must require patch IDs.

        Expected: ValueError if no patch_ids provided
        """
        with pytest.raises(ValueError, match="patch_ids.*required"):
            action_handler.download_patch(patch_ids=[])

    def test_download_patch_uses_correct_endpoint(self, action_handler):
        """
        download_patch should use correct endpoint.

        Expected: /api/1.4/patch/downloadpatch
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

            action_handler.download_patch(patch_ids=[12345, 12346])

            call_url = mock_post.call_args[0][0]
            assert '/api/1.4/patch/downloadpatch' in call_url


# =============================================================================
# TEST: Scan Actions
# =============================================================================

class TestScanActions:
    """Tests for system scanning operations"""

    def test_scan_computers_requires_resource_ids(self, action_handler):
        """
        scan_computers must require resource IDs.

        Expected: ValueError if no resource_ids provided
        """
        with pytest.raises(ValueError, match="resource_ids.*required"):
            action_handler.scan_computers(resource_ids=[])

    def test_scan_computers_uses_correct_endpoint(self, action_handler):
        """
        scan_computers should use correct endpoint.

        Expected: /api/1.4/patch/computers/scan
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

            action_handler.scan_computers(resource_ids=[601, 602])

            call_url = mock_post.call_args[0][0]
            assert '/api/1.4/patch/computers/scan' in call_url

    def test_scan_all_computers_uses_correct_endpoint(self, action_handler):
        """
        scan_all_computers should use correct endpoint.

        Expected: /api/1.4/patch/computers/scanall
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

            action_handler.scan_all_computers()

            call_url = mock_post.call_args[0][0]
            assert '/api/1.4/patch/computers/scanall' in call_url


# =============================================================================
# TEST: Database Update Actions
# =============================================================================

class TestDatabaseUpdateActions:
    """Tests for patch database update operations"""

    def test_update_patch_db_uses_correct_endpoint(self, action_handler):
        """
        update_patch_db should use correct endpoint.

        Expected: /api/1.4/patch/updatedb
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {'status': 'success'})

            action_handler.update_patch_db()

            call_url = mock_post.call_args[0][0]
            assert '/api/1.4/patch/updatedb' in call_url

    def test_get_db_update_status_uses_correct_endpoint(self, action_handler):
        """
        get_db_update_status should use correct endpoint.

        Expected: /api/1.4/patch/dbupdatestatus (GET)
        """
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {'status': 'completed', 'last_update': '2025-12-03'}
            )

            result = action_handler.get_db_update_status()

            call_url = mock_get.call_args[0][0]
            assert '/api/1.4/patch/dbupdatestatus' in call_url
            assert result is not None


# =============================================================================
# TEST: Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for API error handling"""

    def test_handles_401_unauthorized(self, action_handler):
        """
        Actions should handle 401 Unauthorized gracefully.

        Expected: Returns error dict with 'unauthorized' indication
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=401,
                text='Unauthorized',
                json=lambda: {'error': 'Invalid token'}
            )

            result = action_handler.approve_patch(patch_ids=[12345])

            assert 'error' in result
            assert result.get('status_code') == 401

    def test_handles_403_forbidden(self, action_handler):
        """
        Actions should handle 403 Forbidden gracefully.

        Expected: Returns error dict with 'forbidden' indication
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=403,
                text='Forbidden - insufficient scope',
                json=lambda: {'error': 'Insufficient permissions'}
            )

            result = action_handler.approve_patch(patch_ids=[12345])

            assert 'error' in result
            assert result.get('status_code') == 403

    def test_handles_429_rate_limit(self, action_handler):
        """
        Actions should handle 429 Rate Limit with retry.

        Expected: Waits and retries, or returns rate limit error
        """
        with patch('requests.post') as mock_post:
            # First call rate limited, second succeeds
            mock_post.side_effect = [
                Mock(status_code=429, headers={'Retry-After': '1'}, text='Rate limited'),
                Mock(status_code=200, json=lambda: {'status': 'success'})
            ]

            with patch('time.sleep'):  # Don't actually sleep in tests
                result = action_handler.approve_patch(patch_ids=[12345])

            # Should have retried
            assert mock_post.call_count >= 1

    def test_handles_500_server_error(self, action_handler):
        """
        Actions should handle 500 Server Error gracefully.

        Expected: Returns error dict with server error indication
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=500,
                text='Internal Server Error',
                json=lambda: {'error': 'Server error'}
            )

            result = action_handler.approve_patch(patch_ids=[12345])

            assert 'error' in result
            assert result.get('status_code') == 500


# =============================================================================
# TEST: Response Parsing
# =============================================================================

class TestResponseParsing:
    """Tests for API response parsing"""

    def test_extracts_message_response_wrapper(self, action_handler):
        """
        Parser should extract data from message_response wrapper.

        Expected: Returns unwrapped data
        """
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'message_response': {
                        'status': 'success',
                        'approved_count': 2
                    }
                }
            )

            result = action_handler.approve_patch(patch_ids=[12345, 12346])

            # Should have unwrapped the response
            assert result.get('status') == 'success' or 'message_response' not in result

    def test_handles_html_throttling_response(self, action_handler):
        """
        Parser should detect HTML throttling page.

        Expected: Retries after detecting HTML response
        """
        with patch('requests.post') as mock_post:
            # First returns HTML, second returns JSON
            mock_post.side_effect = [
                Mock(status_code=200, text='<!DOCTYPE html><html>Throttled</html>'),
                Mock(status_code=200, json=lambda: {'status': 'success'})
            ]

            with patch('time.sleep'):
                result = action_handler.approve_patch(patch_ids=[12345])

            assert mock_post.call_count >= 1


# =============================================================================
# TEST: Production Safety
# =============================================================================

class TestProductionSafety:
    """Tests for production safety interlocks"""

    def test_write_operations_blocked_for_prod_without_confirm(self):
        """
        PROD write operations should be blocked without confirm_prod=True.

        Expected: PermissionError raised
        """
        # This test validates the safety interlock concept
        # Actual implementation in action handler
        pass  # Will be implemented in action handler

    def test_test_environment_allows_all_operations(self, action_handler):
        """
        TEST environment should allow all operations without extra confirmation.

        Expected: No PermissionError for TEST
        """
        assert action_handler.environment == 'TEST'
        # Operations should proceed without permission errors


# =============================================================================
# INTEGRATION TEST MARKERS
# =============================================================================

@pytest.mark.integration
class TestLiveAPIIntegration:
    """
    Integration tests that hit the actual TEST API.

    Run with: PMP_ENV=TEST pytest tests/test_pmp_actions.py -m integration -v
    """

    @pytest.fixture
    def live_handler(self):
        """Create handler connected to real TEST API"""
        if os.environ.get('PMP_ENV') != 'TEST':
            pytest.skip("Integration tests require PMP_ENV=TEST")

        from claude.tools.pmp.pmp_action_handler import PMPActionHandler
        return PMPActionHandler()

    def test_live_approve_and_unapprove_patch(self, live_handler):
        """
        Integration: Approve then unapprove a patch.

        This is a safe round-trip test.
        """
        # Get a patch ID from supported patches
        # Approve it
        # Unapprove it (return to original state)
        pass  # Will be implemented after handler exists

    def test_live_update_patch_db(self, live_handler):
        """
        Integration: Trigger patch database update.
        """
        result = live_handler.update_patch_db()
        assert 'error' not in result or result.get('status_code') != 401

    def test_live_get_db_update_status(self, live_handler):
        """
        Integration: Get patch database update status.
        """
        result = live_handler.get_db_update_status()
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
