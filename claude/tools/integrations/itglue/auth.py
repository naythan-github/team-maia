"""
Authentication module for ITGlue API

Handles API key storage and retrieval from macOS Keychain.
"""

import keyring
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Keychain service name
KEYCHAIN_SERVICE = "maia-itglue"


def get_api_key(instance: str = 'sandbox') -> str:
    """
    Retrieve ITGlue API key from macOS Keychain.

    Args:
        instance: 'sandbox' or 'production'

    Returns:
        API key string

    Raises:
        ValueError: If API key not found in Keychain
    """
    username = f"itglue-api-key-{instance}"

    logger.info(f"Retrieving ITGlue API key for instance: {instance}")

    api_key = keyring.get_password(KEYCHAIN_SERVICE, username)

    if not api_key:
        raise ValueError(
            f"ITGlue API key not found in macOS Keychain.\n\n"
            f"To set it up:\n"
            f"  python3 -c \"import keyring; keyring.set_password('{KEYCHAIN_SERVICE}', '{username}', 'YOUR_API_KEY')\"\n\n"
            f"Or use the security command:\n"
            f"  security add-generic-password -s '{KEYCHAIN_SERVICE}' -a '{username}' -w 'YOUR_API_KEY'"
        )

    logger.debug(f"API key retrieved successfully for {instance}")
    return api_key


def set_api_key(api_key: str, instance: str = 'sandbox') -> None:
    """
    Store ITGlue API key in macOS Keychain.

    Args:
        api_key: The API key to store
        instance: 'sandbox' or 'production'
    """
    username = f"itglue-api-key-{instance}"

    logger.info(f"Storing ITGlue API key for instance: {instance}")

    keyring.set_password(KEYCHAIN_SERVICE, username, api_key)

    logger.info(f"API key stored successfully for {instance}")


def delete_api_key(instance: str = 'sandbox') -> None:
    """
    Delete ITGlue API key from macOS Keychain.

    Args:
        instance: 'sandbox' or 'production'
    """
    username = f"itglue-api-key-{instance}"

    logger.info(f"Deleting ITGlue API key for instance: {instance}")

    try:
        keyring.delete_password(KEYCHAIN_SERVICE, username)
        logger.info(f"API key deleted successfully for {instance}")
    except keyring.errors.PasswordDeleteError:
        logger.warning(f"API key not found for {instance}")


def list_stored_keys() -> list:
    """
    List all stored ITGlue API keys (instances only, not actual keys).

    Returns:
        List of instance names that have stored API keys
    """
    instances = []

    for instance in ['sandbox', 'production']:
        username = f"itglue-api-key-{instance}"
        if keyring.get_password(KEYCHAIN_SERVICE, username):
            instances.append(instance)

    return instances
