#!/bin/bash
# Maia Team Repository Preparation Script
# Purpose: Clean personal/sensitive data from Maia for team sharing
# Version: 1.0
# Created: 2025-10-21

set -e

echo "========================================"
echo "Maia Team Repository Preparation"
echo "========================================"
echo ""

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_MAIA_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Configuration
ORIGINAL_REPO="${1:-${MAIA_ROOT:-$DEFAULT_MAIA_ROOT}}"
CLEAN_REPO="${2:-$HOME/maia-team-share}"
YOUR_NAME="${3:-YOUR_USERNAME}"
YOUR_ORG="${4:-YOUR_ORG}"

echo "📁 Source Repository: $ORIGINAL_REPO"
echo "📁 Clean Repository: $CLEAN_REPO"
echo "👤 Removing references to: $YOUR_NAME"
echo "🏢 Removing references to: $YOUR_ORG"
echo ""

# Step 1: Clone the repository
echo "1️⃣  Cloning repository..."
if [ -d "$CLEAN_REPO" ]; then
    echo "   ⚠️  Clean repository already exists. Removing..."
    rm -rf "$CLEAN_REPO"
fi

# Create parent directory if needed
mkdir -p "$(dirname "$CLEAN_REPO")"

# Copy the repository (preserving git history)
echo "   Copying repository..."
cp -R "$ORIGINAL_REPO" "$CLEAN_REPO"
cd "$CLEAN_REPO"

# Initialize as a new git repository if not already one
if [ ! -d ".git" ] || [ ! -f ".git/config" ]; then
    echo "   Initializing new git repository..."
    git init
    git add -A
    git commit -m "Initial commit from team preparation script" || true
fi

echo "   ✅ Repository copied"
echo ""

# Step 2: Remove personal databases
echo "2️⃣  Removing personal databases..."
find claude/data -name "*.db" -type f -exec rm -f {} \;
find claude/data -name "*.db-shm" -type f -exec rm -f {} \;
find claude/data -name "*.db-wal" -type f -exec rm -f {} \;

echo "   ✅ Removed $(find claude/data -name "*.db*" -type f 2>/dev/null | wc -l | tr -d ' ') database files"
echo ""

# Step 3: Remove credentials and secrets
echo "3️⃣  Removing credentials and secrets..."
rm -f claude/tools/production_api_credentials.py
rm -f credentials.vault.enc
rm -f .env
rm -f claude/infrastructure/**/.env
find . -name ".env" -type f -exec rm -f {} \;
find . -name "*.pem" -type f -exec rm -f {} \;
find . -name "*.key" -type f -exec rm -f {} \;

echo "   ✅ Credentials removed"
echo ""

# Step 4: Remove personal configurations
echo "4️⃣  Removing personal configurations..."
rm -f .claude/settings.local.json
rm -f .claude/hooks.local.json

echo "   ✅ Personal configs removed"
echo ""

# Step 5: Remove logs
echo "5️⃣  Removing log files..."
find claude/logs -type f -name "*.log" -exec rm -f {} \;
find claude/logs -type f -name "*.json" -exec rm -f {} \;

echo "   ✅ Logs removed"
echo ""

# Step 6: Remove temporary/cache files
echo "6️⃣  Removing temporary and cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -type f -exec rm -f {} \;
find . -name "*.pyo" -type f -exec rm -f {} \;
find . -name ".DS_Store" -type f -exec rm -f {} \;
find . -name "*.swp" -type f -exec rm -f {} \;
find . -name ".vscode" -type d -exec rm -rf {} + 2>/dev/null || true

echo "   ✅ Temp files removed"
echo ""

# Step 7: Replace personal references with placeholders
echo "7️⃣  Replacing personal references..."

# Create list of files to search (excluding git and binary files)
FILES_TO_CLEAN=$(find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.sh" -o -name "*.json" \) ! -path "./.git/*")

# Replace personal name
echo "   Replacing $YOUR_NAME → YOUR_USERNAME..."
for file in $FILES_TO_CLEAN; do
    if grep -q "$YOUR_NAME" "$file" 2>/dev/null; then
        sed -i '' "s|$YOUR_NAME|YOUR_USERNAME|g" "$file" 2>/dev/null || sed -i "s|$YOUR_NAME|YOUR_USERNAME|g" "$file"
    fi
done

# Replace organization name
echo "   Replacing $YOUR_ORG → YOUR_ORG..."
for file in $FILES_TO_CLEAN; do
    if grep -q "$YOUR_ORG" "$file" 2>/dev/null; then
        sed -i '' "s|$YOUR_ORG|YOUR_ORG|g" "$file" 2>/dev/null || sed -i "s|$YOUR_ORG|YOUR_ORG|g" "$file"
    fi
done

# Replace full paths
echo "   Replacing /Users/$YOUR_NAME → /Users/YOUR_USERNAME..."
for file in $FILES_TO_CLEAN; do
    if grep -q "/Users/$YOUR_NAME" "$file" 2>/dev/null; then
        sed -i '' "s|/Users/$YOUR_NAME|/Users/YOUR_USERNAME|g" "$file" 2>/dev/null || sed -i "s|/Users/$YOUR_NAME|/Users/YOUR_USERNAME|g" "$file"
    fi
done

echo "   ✅ Personal references replaced"
echo ""

# Step 8: Create placeholder files with instructions
echo "8️⃣  Creating placeholder files..."

# Create placeholder credentials file
cat > claude/tools/production_api_credentials.py << 'EOF'
"""
Production API Credentials - PLACEHOLDER

This file should contain your API credentials.
DO NOT commit real credentials to version control.

Example structure:
ANTHROPIC_API_KEY = "your-api-key-here"
CONFLUENCE_API_TOKEN = "your-token-here"
CONFLUENCE_BASE_URL = "https://your-org.atlassian.net/wiki"
"""

# Add your credentials here
ANTHROPIC_API_KEY = ""
CONFLUENCE_API_TOKEN = ""
CONFLUENCE_BASE_URL = ""
EOF

# Create placeholder .env
cat > .env.example << 'EOF'
# Maia Environment Variables - Example

# Anthropic API
ANTHROPIC_API_KEY=your-api-key-here

# Confluence
CONFLUENCE_API_TOKEN=your-token-here
CONFLUENCE_BASE_URL=https://your-org.atlassian.net/wiki

# OneDrive (customize for your environment)
MAIA_ONEDRIVE_PATH=/Users/YOUR_USERNAME/Library/CloudStorage/OneDrive-YOUR_ORG

# Optional: Vault password for credentials backup
MAIA_VAULT_PASSWORD=your-secure-password-here
EOF

# Create README for team
cat > TEAM_SETUP_README.md << 'EOF'
# Maia Team Setup

Welcome to Maia! This repository has been prepared for team sharing with personal data removed.

## Quick Start

### For Windows Laptops (WSL)

1. **Run prerequisite setup**:
   ```powershell
   # In PowerShell (Admin):
   cd claude/tools/sre
   .\setup_wsl_prerequisites.ps1
   ```

2. **Follow onboarding guide**:
   - Read: `claude/tools/sre/TEAM_ONBOARDING_WSL.md`

3. **Install dependencies**:
   ```bash
   cd ~/maia
   pip3 install -r requirements.txt
   ```

4. **Configure credentials**:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and credentials
   - OR create `claude/tools/production_api_credentials.py` with your credentials

### For macOS

1. **Clone this repository**:
   ```bash
   git clone [repo-url] ~/git/maia
   cd ~/git/maia
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure credentials**:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and credentials

## What's Missing (Intentionally)

- ❌ **Databases** - Personal data removed. You'll create fresh databases or restore from backup.
- ❌ **Credentials** - Use `.env.example` as template
- ❌ **Personal configurations** - Customize `.claude/settings.local.json` for your environment
- ❌ **Logs** - Fresh start

## Documentation

- **System Overview**: `CLAUDE.md`
- **Recent Changes**: `SYSTEM_STATE.md`
- **WSL Onboarding**: `claude/tools/sre/TEAM_ONBOARDING_WSL.md`
- **WSL Technical Guide**: `claude/tools/sre/WSL_RESTORE_GUIDE.md`
- **Capabilities**: `claude/context/core/capability_index.md`

## Getting Help

1. Check the documentation above
2. Review troubleshooting in `TEAM_ONBOARDING_WSL.md`
3. Ask your team lead

Welcome to the team! 🎉
EOF

echo "   ✅ Placeholder files created"
echo ""

# Step 9: Create .gitignore for sensitive files
echo "9️⃣  Updating .gitignore..."

cat >> .gitignore << 'EOF'

# Personal/Sensitive Data (added by team prep script)
claude/tools/production_api_credentials.py
credentials.vault.enc
.env
claude/infrastructure/**/.env
*.pem
*.key

# Personal Configurations
.claude/settings.local.json
.claude/hooks.local.json

# Databases
claude/data/*.db
claude/data/*.db-shm
claude/data/*.db-wal

# Logs
claude/logs/**/*.log
claude/logs/**/*.json

# IDE
.vscode/
.idea/

# Python
__pycache__/
*.pyc
*.pyo

# macOS
.DS_Store
EOF

echo "   ✅ .gitignore updated"
echo ""

# Step 10: Git cleanup
echo "🔟 Cleaning git history references..."

# Remove any accidental commits of sensitive files from history (optional, aggressive)
# Uncomment if you want to clean git history:
# git filter-branch --force --index-filter \
#   'git rm --cached --ignore-unmatch claude/tools/production_api_credentials.py credentials.vault.enc' \
#   --prune-empty --tag-name-filter cat -- --all

# Reset to clean state
git add -A
git commit -m "🧹 Team Preparation: Remove personal data and credentials

- Removed personal databases
- Removed credentials and secrets
- Removed personal configurations
- Replaced personal references with placeholders
- Created team setup documentation
- Added .env.example and credential templates

This version is ready for team sharing.
" || echo "No changes to commit (already clean)"

echo "   ✅ Git cleaned"
echo ""

# Step 11: Summary
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "✅ Clean repository created at: $CLEAN_REPO"
echo ""
echo "📊 Statistics:"
du -sh "$CLEAN_REPO" | awk '{print "   Repository size: " $1}'
find "$CLEAN_REPO" -type f | wc -l | awk '{print "   Total files: " $1}'
echo ""
echo "📋 Next Steps:"
echo "   1. Review the cleaned repository:"
echo "      cd $CLEAN_REPO"
echo ""
echo "   2. Test that nothing sensitive remains:"
echo "      grep -r 'YOUR_SENSITIVE_DATA' ."
echo ""
echo "   3. Create a new git repository for team:"
echo "      cd $CLEAN_REPO"
echo "      git remote remove origin"
echo "      git remote add origin [NEW_TEAM_REPO_URL]"
echo "      git push -u origin main"
echo ""
echo "   4. Or create a tar.gz for distribution:"
echo "      cd /tmp"
echo "      tar -czf maia-team-$(date +%Y%m%d).tar.gz maia-team-share/"
echo ""
echo "🎉 Team repository preparation complete!"
echo ""
