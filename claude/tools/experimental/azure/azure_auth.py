"""
Azure Authentication Tool

Provides authentication handling for Azure Portal API access.
Supports multiple authentication methods:
- DefaultAzureCredential (recommended for development)
- Service Principal (recommended for production)
- Managed Identity (for Azure-hosted applications)
- Azure CLI credentials

TDD Implementation - Tests in tests/test_azure_auth.py
"""

from enum import Enum
from typing import Optional, Dict, Any
import os
import time
import logging

logger = logging.getLogger(__name__)

# Token cache for performance
_token_cache: Dict[str, Dict[str, Any]] = {}


class AuthMethod(Enum):
    """Supported authentication methods."""
    DEFAULT = "default"
    SERVICE_PRINCIPAL = "service_principal"
    MANAGED_IDENTITY = "managed_identity"
    AZURE_CLI = "azure_cli"


class AzureAuthError(Exception):
    """Raised when Azure authentication fails."""
    pass


class AzureAuthManager:
    """
    Manages Azure authentication with support for multiple credential types.

    Usage:
        # Default credentials (tries multiple methods)
        manager = AzureAuthManager()

        # Service Principal
        manager = AzureAuthManager(
            tenant_id="...",
            client_id="...",
            client_secret="..."
        )

        # From environment variables
        manager = AzureAuthManager.from_environment()
    """

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        auth_method: Optional[AuthMethod] = None,
        credential: Optional[Any] = None
    ):
        """
        Initialize Azure authentication manager.

        Args:
            tenant_id: Azure tenant ID (required for service principal)
            client_id: Azure client/application ID (required for service principal)
            client_secret: Azure client secret (required for service principal)
            auth_method: Specific authentication method to use
            credential: Pre-configured credential object
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._credential = credential

        # Determine auth method
        if credential is not None:
            self.auth_method = auth_method or AuthMethod.DEFAULT
        elif all([tenant_id, client_id, client_secret]):
            self.auth_method = AuthMethod.SERVICE_PRINCIPAL
        elif auth_method:
            self.auth_method = auth_method
        else:
            self.auth_method = AuthMethod.DEFAULT

        # Initialize credential if not provided
        if self._credential is None:
            self._credential = self._create_credential()

    def _create_credential(self) -> Any:
        """Create the appropriate credential based on auth method."""
        try:
            if self.auth_method == AuthMethod.SERVICE_PRINCIPAL:
                from azure.identity import ClientSecretCredential
                return ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            elif self.auth_method == AuthMethod.MANAGED_IDENTITY:
                from azure.identity import ManagedIdentityCredential
                return ManagedIdentityCredential()
            elif self.auth_method == AuthMethod.AZURE_CLI:
                from azure.identity import AzureCliCredential
                return AzureCliCredential()
            else:
                from azure.identity import DefaultAzureCredential
                return DefaultAzureCredential()
        except ImportError as e:
            raise AzureAuthError(
                f"Azure SDK not installed. Run: pip install azure-identity azure-mgmt-resource"
            ) from e
        except Exception as e:
            raise AzureAuthError(f"Failed to create credential: {e}") from e

    @classmethod
    def from_environment(cls) -> "AzureAuthManager":
        """
        Create AzureAuthManager from environment variables.

        Looks for:
            AZURE_TENANT_ID
            AZURE_CLIENT_ID
            AZURE_CLIENT_SECRET

        Falls back to DefaultAzureCredential if not set.
        """
        tenant_id = os.environ.get("AZURE_TENANT_ID")
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")

        if all([tenant_id, client_id, client_secret]):
            return cls(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            return cls(auth_method=AuthMethod.DEFAULT)

    @property
    def credential(self) -> Any:
        """Get the underlying credential object."""
        return self._credential

    def get_token(self, scope: str = "https://management.azure.com/.default") -> str:
        """
        Get an access token for the specified scope.

        Args:
            scope: The resource scope (default: Azure Management API)

        Returns:
            Access token string

        Raises:
            AzureAuthError: If authentication fails
        """
        try:
            # Check cache first
            cached = get_cached_token(scope)
            if cached:
                return cached

            # Get new token
            token = self._credential.get_token(scope)

            # Cache it
            _token_cache[scope] = {
                "token": token.token,
                "expires_on": token.expires_on
            }

            return token.token
        except Exception as e:
            raise AzureAuthError(f"Authentication failed: {e}") from e

    def is_authenticated(self) -> bool:
        """
        Check if current credentials are valid.

        Returns:
            True if authentication succeeds, False otherwise
        """
        try:
            self.get_token()
            return True
        except AzureAuthError:
            return False

    def get_subscription_client(self) -> Any:
        """Get a SubscriptionClient for listing subscriptions."""
        try:
            from azure.mgmt.resource import SubscriptionClient
            return SubscriptionClient(self._credential)
        except ImportError as e:
            raise AzureAuthError(
                "azure-mgmt-resource not installed. Run: pip install azure-mgmt-resource"
            ) from e

    def get_resource_client(self, subscription_id: str) -> Any:
        """Get a ResourceManagementClient for the given subscription."""
        try:
            from azure.mgmt.resource import ResourceManagementClient
            return ResourceManagementClient(self._credential, subscription_id)
        except ImportError as e:
            raise AzureAuthError(
                "azure-mgmt-resource not installed. Run: pip install azure-mgmt-resource"
            ) from e


def get_default_credential() -> Any:
    """
    Get a DefaultAzureCredential instance.

    This credential tries multiple authentication methods in order:
    1. Environment variables
    2. Managed Identity
    3. Azure CLI
    4. Interactive browser

    Returns:
        DefaultAzureCredential instance
    """
    try:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential()
    except ImportError as e:
        raise AzureAuthError(
            "azure-identity not installed. Run: pip install azure-identity"
        ) from e


def authenticate_with_service_principal(
    tenant_id: str,
    client_id: str,
    client_secret: str
) -> Dict[str, Any]:
    """
    Authenticate using service principal credentials.

    Args:
        tenant_id: Azure tenant ID
        client_id: Application/Client ID
        client_secret: Client secret

    Returns:
        Dict with success status and token

    Raises:
        ValueError: If required parameters are missing
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not client_id:
        raise ValueError("client_id is required")
    if not client_secret:
        raise ValueError("client_secret is required")

    try:
        from azure.identity import ClientSecretCredential

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        token = credential.get_token("https://management.azure.com/.default")

        return {
            "success": True,
            "token": token.token,
            "expires_on": token.expires_on
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_cached_token(scope: str) -> Optional[str]:
    """
    Get a cached token if valid.

    Args:
        scope: The resource scope

    Returns:
        Token string if valid cached token exists, None otherwise
    """
    if scope not in _token_cache:
        return None

    cached = _token_cache[scope]

    # Check if expired (with 5 minute buffer)
    if cached["expires_on"] < time.time() + 300:
        return None

    return cached["token"]


def clear_token_cache() -> None:
    """Clear all cached tokens."""
    global _token_cache
    _token_cache = {}


# Convenience function for CLI usage
def main():
    """CLI interface for authentication testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Azure Authentication Tool")
    parser.add_argument("--method", choices=["default", "sp", "cli", "mi"],
                       default="default", help="Authentication method")
    parser.add_argument("--tenant-id", help="Tenant ID (for service principal)")
    parser.add_argument("--client-id", help="Client ID (for service principal)")
    parser.add_argument("--client-secret", help="Client secret (for service principal)")
    parser.add_argument("--test", action="store_true", help="Test authentication")

    args = parser.parse_args()

    # Create manager based on method
    if args.method == "sp":
        if not all([args.tenant_id, args.client_id, args.client_secret]):
            print("Error: Service principal requires --tenant-id, --client-id, --client-secret")
            return 1
        manager = AzureAuthManager(
            tenant_id=args.tenant_id,
            client_id=args.client_id,
            client_secret=args.client_secret
        )
    elif args.method == "cli":
        manager = AzureAuthManager(auth_method=AuthMethod.AZURE_CLI)
    elif args.method == "mi":
        manager = AzureAuthManager(auth_method=AuthMethod.MANAGED_IDENTITY)
    else:
        manager = AzureAuthManager.from_environment()

    if args.test:
        print(f"Testing authentication with method: {manager.auth_method.value}")
        if manager.is_authenticated():
            print("Authentication successful!")
            return 0
        else:
            print("Authentication failed!")
            return 1

    # Default: show authentication status
    print(f"Auth method: {manager.auth_method.value}")
    print(f"Authenticated: {manager.is_authenticated()}")
    return 0


if __name__ == "__main__":
    exit(main())
