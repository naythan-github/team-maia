#!/bin/bash
# Setup Maia Disaster Recovery Vault Password in Keychain
# This script stores the vault password securely for automated backups

set -e

echo "🔐 Maia Disaster Recovery - Keychain Setup"
echo "=========================================="
echo ""
echo "This will store your vault password securely in macOS Keychain."
echo "The password is used to encrypt credentials during backup."
echo ""

# Prompt for password
read -s -p "Enter vault password: " VAULT_PASSWORD
echo ""
read -s -p "Confirm vault password: " VAULT_PASSWORD_CONFIRM
echo ""

if [ "$VAULT_PASSWORD" != "$VAULT_PASSWORD_CONFIRM" ]; then
    echo "❌ Passwords do not match. Please try again."
    exit 1
fi

if [ -z "$VAULT_PASSWORD" ]; then
    echo "❌ Password cannot be empty."
    exit 1
fi

# Check if password already exists
if security find-generic-password -s "maia_vault_password" -a "$(whoami)" &>/dev/null; then
    echo "⚠️  Vault password already exists in keychain."
    read -p "Replace existing password? (y/N): " REPLACE
    if [ "$REPLACE" != "y" ]; then
        echo "❌ Cancelled."
        exit 0
    fi

    # Delete existing password
    security delete-generic-password -s "maia_vault_password" -a "$(whoami)"
    echo "✅ Existing password removed."
fi

# Add password to keychain
security add-generic-password \
    -s "maia_vault_password" \
    -a "$(whoami)" \
    -w "$VAULT_PASSWORD" \
    -U

echo "✅ Vault password stored securely in keychain"
echo ""

# Test retrieval
echo "🔍 Testing password retrieval..."
TEST_PASSWORD=$(security find-generic-password -w -s "maia_vault_password" -a "$(whoami)" 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Password retrieval successful"
    echo ""
    echo "🎉 Keychain setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Fix LaunchAgent configuration"
    echo "  2. Test manual backup execution"
    echo "  3. Reload LaunchAgent"
else
    echo "❌ Failed to retrieve password from keychain"
    echo "Error: $TEST_PASSWORD"
    exit 1
fi
