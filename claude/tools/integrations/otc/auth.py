"""
OTC API Authentication Module

Handles credential storage and retrieval from macOS Keychain.
Credentials are NEVER stored in code or config files.

Usage:
    # Store credentials (one-time setup)
    from claude.tools.integrations.otc.auth import set_credentials
    set_credentials('CloudTicket-Sync', 'your-password')

    # Retrieve credentials (used by client)
    from claude.tools.integrations.otc.auth import get_credentials
    username, password = get_credentials()
"""

import keyring
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Keychain configuration
KEYCHAIN_SERVICE = "maia-otc"
USERNAME_KEY = "otc-username"
PASSWORD_KEY = "otc-password"


def get_credentials() -> Tuple[str, str]:
    """
    Retrieve OTC API credentials from macOS Keychain.

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If credentials not found in Keychain
    """
    logger.debug("Retrieving OTC credentials from Keychain")

    username = keyring.get_password(KEYCHAIN_SERVICE, USERNAME_KEY)
    password = keyring.get_password(KEYCHAIN_SERVICE, PASSWORD_KEY)

    if not username or not password:
        raise ValueError(
            "OTC credentials not found in macOS Keychain.\n\n"
            "To set up credentials:\n"
            "  from claude.tools.integrations.otc import set_credentials\n"
            "  set_credentials('CloudTicket-Sync', 'your-password')\n\n"
            "Or run the setup command:\n"
            "  python3 -m claude.tools.integrations.otc.auth --setup\n\n"
            "Or use the security command:\n"
            f"  security add-generic-password -s '{KEYCHAIN_SERVICE}' -a '{USERNAME_KEY}' -w 'username'\n"
            f"  security add-generic-password -s '{KEYCHAIN_SERVICE}' -a '{PASSWORD_KEY}' -w 'password'"
        )

    logger.debug("OTC credentials retrieved successfully")
    return username, password


def set_credentials(username: str, password: str) -> None:
    """
    Store OTC API credentials in macOS Keychain.

    Args:
        username: OTC API username
        password: OTC API password
    """
    logger.info("Storing OTC credentials in Keychain")

    keyring.set_password(KEYCHAIN_SERVICE, USERNAME_KEY, username)
    keyring.set_password(KEYCHAIN_SERVICE, PASSWORD_KEY, password)

    logger.info("OTC credentials stored successfully")
    print("✅ OTC credentials stored in macOS Keychain")


def delete_credentials() -> None:
    """
    Delete OTC API credentials from macOS Keychain.
    """
    logger.info("Deleting OTC credentials from Keychain")

    try:
        keyring.delete_password(KEYCHAIN_SERVICE, USERNAME_KEY)
        keyring.delete_password(KEYCHAIN_SERVICE, PASSWORD_KEY)
        logger.info("OTC credentials deleted successfully")
        print("✅ OTC credentials deleted from macOS Keychain")
    except keyring.errors.PasswordDeleteError:
        logger.warning("OTC credentials not found in Keychain")
        print("⚠️  OTC credentials not found in Keychain")


def credentials_exist() -> bool:
    """
    Check if OTC credentials are stored in Keychain.

    Returns:
        True if both username and password are stored
    """
    username = keyring.get_password(KEYCHAIN_SERVICE, USERNAME_KEY)
    password = keyring.get_password(KEYCHAIN_SERVICE, PASSWORD_KEY)
    return bool(username and password)


def interactive_setup() -> None:
    """
    Interactive credential setup via command line.
    """
    import getpass

    print("\n🔐 OTC Credential Setup")
    print("=" * 40)
    print("Credentials will be stored securely in macOS Keychain.\n")

    username = input("Username [CloudTicket-Sync]: ").strip()
    if not username:
        username = "CloudTicket-Sync"

    password = getpass.getpass("Password: ")
    if not password:
        print("❌ Password cannot be empty")
        return

    set_credentials(username, password)
    print("\n✅ Setup complete. You can now use the OTC client.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        interactive_setup()
    elif len(sys.argv) > 1 and sys.argv[1] == "--delete":
        delete_credentials()
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        if credentials_exist():
            print("✅ OTC credentials are configured")
        else:
            print("❌ OTC credentials not found")
    else:
        print("OTC Authentication Manager")
        print("")
        print("Usage:")
        print("  python3 -m claude.tools.integrations.otc.auth --setup   # Configure credentials")
        print("  python3 -m claude.tools.integrations.otc.auth --check   # Verify credentials exist")
        print("  python3 -m claude.tools.integrations.otc.auth --delete  # Remove credentials")
