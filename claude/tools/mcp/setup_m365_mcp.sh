#!/bin/bash
# Setup Microsoft 365 MCP Server
# Uses official Microsoft Graph SDK with enterprise security

set -e

echo "🚀 Setting up Microsoft 365 MCP Server"
echo "========================================"

# Install Python dependencies
echo "📦 Installing Microsoft Graph SDK..."
pip3 install azure-identity msgraph-sdk mcp

# Create configuration directory
CONFIG_DIR="${MAIA_ROOT:-$HOME/.maia}/config/m365"
mkdir -p "$CONFIG_DIR"

echo ""
echo "✅ Dependencies installed"
echo ""
echo "📋 Azure AD App Registration Required"
echo "======================================"
echo ""
echo "Follow these steps to configure Microsoft 365 authentication:"
echo ""
echo "1. Go to Azure Portal: https://portal.azure.com"
echo "2. Navigate to: Azure Active Directory → App registrations → New registration"
echo ""
echo "   Name: Maia M365 Integration"
echo "   Supported account types: Accounts in this organizational directory only (Orro Group)"
echo "   Redirect URI: Public client/native → http://localhost"
echo ""
echo "3. After registration, note:"
echo "   - Application (client) ID"
echo "   - Directory (tenant) ID"
echo ""
echo "4. Configure API permissions:"
echo "   Microsoft Graph → Delegated permissions:"
echo "     - Mail.ReadWrite"
echo "     - Calendars.ReadWrite"
echo "     - Team.ReadBasic.All"
echo "     - ChannelMessage.Send"
echo "     - OnlineMeetings.ReadWrite"
echo "     - User.Read"
echo ""
echo "5. Grant admin consent for Orro Group"
echo ""
echo "6. Set environment variables:"
echo ""

# Create .env template
ENV_FILE="$CONFIG_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# Microsoft 365 MCP Server Configuration
# Copy this to your shell environment or .zshrc/.bashrc

export M365_TENANT_ID="your-tenant-id-here"
export M365_CLIENT_ID="your-client-id-here"

# Optional: Enable read-only mode for safe testing
export M365_READ_ONLY="true"

# Optional: Use client secret instead of device code (for service accounts)
# export M365_CLIENT_SECRET="your-client-secret-here"
EOF
    echo "   Template created: $ENV_FILE"
    echo ""
    echo "   Edit this file with your Azure AD credentials:"
    echo "   code $ENV_FILE"
else
    echo "   Configuration exists: $ENV_FILE"
fi

echo ""
echo "7. Load configuration:"
echo "   source $ENV_FILE"
echo ""
echo "8. Test MCP server:"
echo "   python3 ${MAIA_ROOT:-$(pwd)}/claude/tools/mcp/m365_graph_server.py"
echo ""
echo "9. Add to Claude Code MCP configuration:"
echo "   See: claude/tools/mcp/m365_mcp_config.json"
echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Complete Azure AD app registration"
echo "   2. Configure environment variables"
echo "   3. Test with read-only mode first"
echo "   4. Create Microsoft 365 Integration Agent"
