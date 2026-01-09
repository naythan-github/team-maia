#!/bin/bash
# Quick Deploy: Sandbox VM Idle Shutdown
# Usage: ./deploy_sandbox_idle_shutdown.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Sandbox VM Idle Shutdown - Quick Deploy              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: win11-vscode VM"
echo "Cost Savings: ~\$47/month (for 8h/day usage)"
echo ""

# Check for PowerShell
if ! command -v pwsh &> /dev/null; then
    echo "❌ PowerShell (pwsh) not found"
    echo ""
    echo "Install PowerShell:"
    echo "  macOS:   brew install powershell"
    echo "  Linux:   https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-linux"
    echo "  Windows: Already installed"
    echo ""
    exit 1
fi

# Check for Az module
echo "Checking Azure PowerShell module..."
pwsh -NoProfile -Command "if (!(Get-Module -ListAvailable -Name Az.Accounts)) { Write-Host '❌ Az module not installed'; exit 1 }" || {
    echo ""
    echo "❌ Azure PowerShell module not installed"
    echo ""
    echo "Install with:"
    echo "  pwsh -Command 'Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force'"
    echo ""
    exit 1
}

echo "✅ Prerequisites met"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if setup script exists
SETUP_SCRIPT="$SCRIPT_DIR/Setup-SandboxVMIdleShutdown.ps1"
if [ ! -f "$SETUP_SCRIPT" ]; then
    echo "❌ Setup script not found: $SETUP_SCRIPT"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running PowerShell setup script..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run PowerShell setup
pwsh -NoProfile -File "$SETUP_SCRIPT"

RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ Deployment Complete!                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next Steps:"
    echo "  1. Test:   pwsh -File $SCRIPT_DIR/Manage-VMIdleShutdown.ps1 -Action Test -ResourceGroup DEV-RG -VMName win11-vscode"
    echo "  2. Status: pwsh -File $SCRIPT_DIR/Manage-VMIdleShutdown.ps1 -Action Status -ResourceGroup DEV-RG -VMName win11-vscode"
    echo ""
    echo "Docs: $SCRIPT_DIR/SANDBOX_DEPLOYMENT_GUIDE.md"
    echo ""
else
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ❌ Deployment Failed                        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Check error messages above for details."
    echo ""
    exit 1
fi
