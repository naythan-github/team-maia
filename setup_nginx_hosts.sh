#!/bin/bash
# Setup /etc/hosts for Maia dashboard mesh
# Requires sudo to modify /etc/hosts

echo "🔧 Setting up /etc/hosts for Maia dashboard mesh..."
echo ""

# Backup current hosts file
sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backed up /etc/hosts"

# Add Maia dashboard entries if they don't exist
if ! grep -q "hub.maia.local" /etc/hosts; then
    echo "📝 Adding Maia dashboard entries to /etc/hosts..."

    sudo bash -c 'cat >> /etc/hosts << EOF

# Maia Dashboard Mesh - Added $(date +%Y-%m-%d)
127.0.0.1    hub.maia.local
127.0.0.1    ai.maia.local
127.0.0.1    dora.maia.local
127.0.0.1    governance.maia.local
127.0.0.1    status.maia.local
127.0.0.1    performance.maia.local
127.0.0.1    tokens.maia.local
127.0.0.1    backlog.maia.local
EOF'

    echo "✅ Added Maia dashboard entries"
else
    echo "✅ Maia dashboard entries already exist"
fi

echo ""
echo "🎯 Configured domains:"
echo "  http://hub.maia.local        → Unified Hub (8100)"
echo "  http://ai.maia.local         → AI Business Intelligence (8050)"
echo "  http://dora.maia.local       → DORA Metrics (8060)"
echo "  http://governance.maia.local → Governance (8070)"
echo ""
echo "✅ /etc/hosts setup complete!"
