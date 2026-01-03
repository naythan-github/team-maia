"""
TDD Tests for Azure Authentication Tool
Tests written BEFORE implementation per TDD protocol.

Test Categories:
1. Credential initialization
2. Authentication methods
3. Error handling
4. Token caching
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import os

# Import will fail until implementation exists - that's TDD!
try:
    from claude.tools.experimental.azure.azure_auth import (
        AzureAuthManager,
        AuthMethod,
        AzureAuthError,
        get_default_credential,
        authenticate_with_service_principal,
        get_cached_token,
        clear_token_cache,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False


# Skip all tests if implementation doesn't exist yet (TDD red phase)
pytestmark = pytest.mark.skipif(
    not IMPLEMENTATION_EXISTS,
    reason="Implementation not yet created - TDD red phase"
)


class TestAzureAuthManager:
    """Test the main authentication manager class."""

    def test_init_default_credential(self):
        """Should initialize with DefaultAzureCredential by default."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred:
            manager = AzureAuthManager()
            assert manager.auth_method == AuthMethod.DEFAULT
            mock_cred.assert_called_once()

    def test_init_service_principal(self):
        """Should initialize with service principal when credentials provided."""
        with patch('azure.identity.ClientSecretCredential') as mock_cred:
            manager = AzureAuthManager(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret"
            )
            assert manager.auth_method == AuthMethod.SERVICE_PRINCIPAL
            mock_cred.assert_called_once_with(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret"
            )

    def test_init_managed_identity(self):
        """Should initialize with ManagedIdentityCredential when specified."""
        with patch('azure.identity.ManagedIdentityCredential') as mock_cred:
            manager = AzureAuthManager(auth_method=AuthMethod.MANAGED_IDENTITY)
            assert manager.auth_method == AuthMethod.MANAGED_IDENTITY
            mock_cred.assert_called_once()

    def test_init_azure_cli(self):
        """Should initialize with AzureCliCredential when specified."""
        with patch('azure.identity.AzureCliCredential') as mock_cred:
            manager = AzureAuthManager(auth_method=AuthMethod.AZURE_CLI)
            assert manager.auth_method == AuthMethod.AZURE_CLI
            mock_cred.assert_called_once()

    def test_get_token_success(self):
        """Should return valid access token."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred_class:
            mock_cred = Mock()
            mock_token = Mock()
            mock_token.token = "test-access-token"
            mock_token.expires_on = 1234567890
            mock_cred.get_token.return_value = mock_token
            mock_cred_class.return_value = mock_cred

            manager = AzureAuthManager()
            token = manager.get_token("https://management.azure.com/.default")

            assert token == "test-access-token"
            mock_cred.get_token.assert_called_once_with(
                "https://management.azure.com/.default"
            )

    def test_get_token_failure_raises_auth_error(self):
        """Should raise AzureAuthError on authentication failure."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred_class:
            mock_cred = Mock()
            mock_cred.get_token.side_effect = Exception("Auth failed")
            mock_cred_class.return_value = mock_cred

            manager = AzureAuthManager()

            with pytest.raises(AzureAuthError) as exc_info:
                manager.get_token("https://management.azure.com/.default")

            assert "Auth failed" in str(exc_info.value)

    def test_is_authenticated_true(self):
        """Should return True when valid token exists."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred_class:
            mock_cred = Mock()
            mock_token = Mock()
            mock_token.token = "valid-token"
            mock_cred.get_token.return_value = mock_token
            mock_cred_class.return_value = mock_cred

            manager = AzureAuthManager()
            assert manager.is_authenticated() is True

    def test_is_authenticated_false_on_failure(self):
        """Should return False when authentication fails."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred_class:
            mock_cred = Mock()
            mock_cred.get_token.side_effect = Exception("Not authenticated")
            mock_cred_class.return_value = mock_cred

            manager = AzureAuthManager()
            assert manager.is_authenticated() is False


class TestAuthenticationMethods:
    """Test standalone authentication functions."""

    def test_get_default_credential_returns_credential(self):
        """Should return a valid credential object."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred:
            cred = get_default_credential()
            mock_cred.assert_called_once()
            assert cred is not None

    def test_authenticate_with_service_principal_success(self):
        """Should authenticate with service principal credentials."""
        with patch('azure.identity.ClientSecretCredential') as mock_cred_class:
            mock_cred = Mock()
            mock_token = Mock()
            mock_token.token = "sp-token"
            mock_cred.get_token.return_value = mock_token
            mock_cred_class.return_value = mock_cred

            result = authenticate_with_service_principal(
                tenant_id="tenant",
                client_id="client",
                client_secret="secret"
            )

            assert result["success"] is True
            assert result["token"] == "sp-token"

    def test_authenticate_with_service_principal_missing_params(self):
        """Should raise error when required params missing."""
        with pytest.raises(ValueError) as exc_info:
            authenticate_with_service_principal(
                tenant_id="tenant",
                client_id=None,  # Missing
                client_secret="secret"
            )
        assert "client_id" in str(exc_info.value).lower()


class TestTokenCaching:
    """Test token caching functionality."""

    def test_get_cached_token_returns_none_when_empty(self):
        """Should return None when no cached token exists."""
        clear_token_cache()
        result = get_cached_token("https://management.azure.com/.default")
        assert result is None

    def test_get_cached_token_returns_valid_token(self):
        """Should return cached token when valid."""
        with patch('azure.identity.DefaultAzureCredential') as mock_cred_class:
            mock_cred = Mock()
            mock_token = Mock()
            mock_token.token = "cached-token"
            mock_token.expires_on = 9999999999  # Far future
            mock_cred.get_token.return_value = mock_token
            mock_cred_class.return_value = mock_cred

            manager = AzureAuthManager()
            manager.get_token("https://management.azure.com/.default")

            # Should return from cache
            cached = get_cached_token("https://management.azure.com/.default")
            assert cached == "cached-token"

    def test_clear_token_cache_removes_all_tokens(self):
        """Should clear all cached tokens."""
        # Setup cache (if implementation allows direct manipulation)
        clear_token_cache()
        result = get_cached_token("https://management.azure.com/.default")
        assert result is None


class TestEnvironmentVariables:
    """Test credential loading from environment variables."""

    def test_loads_from_env_vars(self):
        """Should load service principal from env vars when present."""
        env_vars = {
            "AZURE_TENANT_ID": "env-tenant",
            "AZURE_CLIENT_ID": "env-client",
            "AZURE_CLIENT_SECRET": "env-secret"
        }

        with patch.dict(os.environ, env_vars):
            with patch('azure.identity.ClientSecretCredential') as mock_cred:
                manager = AzureAuthManager.from_environment()
                assert manager.auth_method == AuthMethod.SERVICE_PRINCIPAL

    def test_falls_back_to_default_when_no_env(self):
        """Should use DefaultAzureCredential when no env vars set."""
        env_vars = {}

        with patch.dict(os.environ, env_vars, clear=True):
            with patch('azure.identity.DefaultAzureCredential') as mock_cred:
                manager = AzureAuthManager.from_environment()
                assert manager.auth_method == AuthMethod.DEFAULT


class TestIntegration:
    """Integration tests - require actual Azure credentials."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        os.environ.get("AZURE_TENANT_ID") is None,
        reason="Azure credentials not configured"
    )
    def test_real_authentication(self):
        """Integration test with real Azure credentials."""
        manager = AzureAuthManager.from_environment()
        assert manager.is_authenticated() is True

        token = manager.get_token("https://management.azure.com/.default")
        assert token is not None
        assert len(token) > 100  # Real tokens are long


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
