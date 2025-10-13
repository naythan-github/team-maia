#!/bin/bash
# Retrieve vault password from macOS Keychain
security find-generic-password -a "maia" -s "maia_vault_password" -w 2>/dev/null
