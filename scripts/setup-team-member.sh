#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Maia Team Member Setup Script
#
# Sets up a new team member's local environment for Maia development.
# Run this once after cloning the repository.
#
# Usage: ./scripts/setup-team-member.sh
# ═══════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════════"
echo "                    MAIA TEAM MEMBER SETUP                          "
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Get script directory and MAIA_ROOT
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "MAIA_ROOT: $MAIA_ROOT"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 1: Verify prerequisites
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Step 1: Verifying prerequisites...${NC}"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
python_major=$(echo "$python_version" | cut -d'.' -f1)
python_minor=$(echo "$python_version" | cut -d'.' -f2)

if [ "$python_major" -lt 3 ] || { [ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]; }; then
    echo -e "${RED}❌ Python 3.9+ required (found $python_version)${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python $python_version"

# Check git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git installed"

# ───────────────────────────────────────────────────────────────────
# Step 2: Create local data directory (~/.maia/)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 2: Creating local data directory...${NC}"

mkdir -p ~/.maia/{data/databases/user,data/checkpoints,context/personal,sessions,projects}

echo -e "  ${GREEN}✓${NC} Created ~/.maia/ directory structure"

# ───────────────────────────────────────────────────────────────────
# Step 3: Create personal profile (if not exists)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 3: Setting up personal profile...${NC}"

if [ ! -f ~/.maia/context/personal/profile.md ]; then
    cat > ~/.maia/context/personal/profile.md << 'PROFILE'
# Personal Profile

## Identity
- **Name**: [Your Full Name]
- **Role**: [Your Role/Title]
- **Team**: [Your Team]

## Preferences
- **Default Agent**: sre_principal_engineer_agent
- **Working Style**: [e.g., "Prefer detailed explanations"]
- **Focus Areas**: [e.g., "Azure", "Security", "SRE"]

## Notes
<!-- Add any personal notes or context Maia should know -->

PROFILE
    echo -e "  ${GREEN}✓${NC} Created profile template"
    echo -e "  ${YELLOW}→${NC} Edit ~/.maia/context/personal/profile.md with your details"
else
    echo -e "  ${GREEN}✓${NC} Profile already exists"
fi

# ───────────────────────────────────────────────────────────────────
# Step 4: Create user preferences (if not exists)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 4: Setting up user preferences...${NC}"

if [ ! -f ~/.maia/data/user_preferences.json ]; then
    cat > ~/.maia/data/user_preferences.json << PREFS
{
  "default_agent": "sre_principal_engineer_agent",
  "fallback_agent": "sre_principal_engineer_agent",
  "version": "1.0",
  "description": "User-specific Maia preferences",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "user": "$USER"
}
PREFS
    echo -e "  ${GREEN}✓${NC} Created user preferences"
else
    echo -e "  ${GREEN}✓${NC} User preferences already exists"
fi

# ───────────────────────────────────────────────────────────────────
# Step 5: Install Git hooks
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 5: Installing Git hooks...${NC}"

HOOKS_DIR="$MAIA_ROOT/.git/hooks"
HOOKS_SRC="$MAIA_ROOT/scripts/hooks"

# Pre-commit hook
if [ -f "$HOOKS_SRC/pre-commit" ]; then
    cp "$HOOKS_SRC/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo -e "  ${GREEN}✓${NC} Installed pre-commit hook"
else
    echo -e "  ${YELLOW}⚠${NC} pre-commit hook source not found (skipping)"
fi

# Pre-push hook
if [ -f "$HOOKS_SRC/pre-push" ]; then
    cp "$HOOKS_SRC/pre-push" "$HOOKS_DIR/pre-push"
    chmod +x "$HOOKS_DIR/pre-push"
    echo -e "  ${GREEN}✓${NC} Installed pre-push hook"
else
    echo -e "  ${YELLOW}⚠${NC} pre-push hook source not found (skipping)"
fi

# Post-merge hook
if [ -f "$HOOKS_SRC/post-merge" ]; then
    cp "$HOOKS_SRC/post-merge" "$HOOKS_DIR/post-merge"
    chmod +x "$HOOKS_DIR/post-merge"
    echo -e "  ${GREEN}✓${NC} Installed post-merge hook"
else
    echo -e "  ${YELLOW}⚠${NC} post-merge hook source not found (skipping)"
fi

# ───────────────────────────────────────────────────────────────────
# Step 6: Install Python dependencies
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 6: Installing Python dependencies...${NC}"

cd "$MAIA_ROOT"

if [ -f "requirements.txt" ]; then
    pip3 install -q -r requirements.txt 2>/dev/null || {
        echo -e "  ${YELLOW}⚠${NC} Some dependencies may have failed (non-critical)"
    }
    echo -e "  ${GREEN}✓${NC} Installed requirements.txt"
fi

if [ -f "requirements-dev.txt" ]; then
    pip3 install -q -r requirements-dev.txt 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Installed requirements-dev.txt"
fi

# ───────────────────────────────────────────────────────────────────
# Step 7: Generate local databases
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 7: Generating local databases...${NC}"

# Capabilities database
if [ -f "$MAIA_ROOT/claude/tools/sre/capabilities_registry.py" ]; then
    if python3 "$MAIA_ROOT/claude/tools/sre/capabilities_registry.py" scan --quiet 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Capabilities database generated"
    else
        echo -e "  ${YELLOW}⚠${NC} Capabilities database will generate on first use"
    fi
fi

# System state database
if [ -f "$MAIA_ROOT/claude/tools/sre/system_state_etl.py" ]; then
    if python3 "$MAIA_ROOT/claude/tools/sre/system_state_etl.py" --recent all --quiet 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} System state database generated"
    else
        echo -e "  ${YELLOW}⚠${NC} System state database will generate on first use"
    fi
fi

# ───────────────────────────────────────────────────────────────────
# Step 8: Verify setup
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 8: Verifying setup...${NC}"

# Check path resolution
if python3 -c "from claude.tools.core.paths import PathManager; print(PathManager.get_maia_root())" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Path resolution working"
else
    echo -e "  ${YELLOW}⚠${NC} Path resolution may need MAIA_ROOT env var"
fi

# ───────────────────────────────────────────────────────────────────
# Complete!
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    SETUP COMPLETE!                                 ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit your profile:"
echo "     vim ~/.maia/context/personal/profile.md"
echo ""
echo "  2. Start Maia:"
echo "     Open Claude Code in $MAIA_ROOT"
echo "     Type: load"
echo ""
echo "  3. To contribute:"
echo "     git checkout -b feature/your-feature"
echo "     # make changes"
echo "     git add . && git commit -m 'your message'"
echo "     git push -u origin feature/your-feature"
echo "     # create PR on GitHub"
echo ""
echo "Documentation: .github/CONTRIBUTING.md"
echo ""
