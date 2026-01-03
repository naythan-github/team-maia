#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Maia Fresh Repository Migration Script
#
# Creates a clean copy of Maia without git history.
# Use this when starting fresh to avoid personal data in history.
#
# Usage:
#   ./scripts/migrate-to-fresh-repo.sh /path/to/new/maia
#
# What it does:
#   1. Copies all tracked files to new location
#   2. Excludes personal data, databases, and caches
#   3. Initializes fresh git repository
#   4. Creates initial commit
#
# After running:
#   1. cd /path/to/new/maia
#   2. git remote add origin git@github.com:ORG/maia.git
#   3. git push -u origin main
# ═══════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get source directory (this script's parent's parent)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 /path/to/new/maia${NC}"
    echo ""
    echo "Example:"
    echo "  $0 ~/maia-clean"
    echo "  $0 /tmp/maia-fresh"
    exit 1
fi

TARGET_DIR="$1"

# Validate source
if [ ! -f "$SOURCE_DIR/CLAUDE.md" ]; then
    echo -e "${RED}Error: Not running from Maia repository${NC}"
    exit 1
fi

# Check target doesn't exist
if [ -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Target directory already exists: $TARGET_DIR${NC}"
    echo "Remove it first or choose a different path."
    exit 1
fi

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════════"
echo "               MAIA FRESH REPOSITORY MIGRATION"
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 1: Create target directory
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Step 1: Creating target directory...${NC}"
mkdir -p "$TARGET_DIR"
echo -e "  ${GREEN}✓${NC} Created $TARGET_DIR"

# ───────────────────────────────────────────────────────────────────
# Step 2: Copy files (respecting .gitignore)
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 2: Copying files...${NC}"

# Use git ls-files to get tracked files, plus untracked but not ignored
cd "$SOURCE_DIR"

# Get list of files to copy (tracked + staged)
git ls-files --cached > /tmp/maia_files_to_copy.txt

# Also include important untracked files that should be in fresh repo
for f in .github/* .github/**/* scripts/* scripts/**/*; do
    if [ -f "$f" ]; then
        echo "$f" >> /tmp/maia_files_to_copy.txt
    fi
done

# Sort and deduplicate
sort -u /tmp/maia_files_to_copy.txt > /tmp/maia_files_unique.txt

# Copy files preserving directory structure
file_count=0
while IFS= read -r file; do
    if [ -f "$SOURCE_DIR/$file" ]; then
        # Create parent directory
        mkdir -p "$TARGET_DIR/$(dirname "$file")"
        # Copy file
        cp "$SOURCE_DIR/$file" "$TARGET_DIR/$file"
        ((file_count++))
    fi
done < /tmp/maia_files_unique.txt

echo -e "  ${GREEN}✓${NC} Copied $file_count files"

# ───────────────────────────────────────────────────────────────────
# Step 3: Remove any personal data that slipped through
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 3: Scrubbing personal data...${NC}"

# Remove any user-specific files that shouldn't be in fresh repo
rm -rf "$TARGET_DIR/claude/data/databases/user/" 2>/dev/null || true
rm -rf "$TARGET_DIR/claude/data/user_preferences.json" 2>/dev/null || true
rm -rf "$TARGET_DIR/claude/context/personal/" 2>/dev/null || true
rm -f "$TARGET_DIR"/*_naythan*.* 2>/dev/null || true
rm -f "$TARGET_DIR"/claude/data/*_naythan*.* 2>/dev/null || true

# Remove any .db files (should regenerate)
find "$TARGET_DIR" -name "*.db" -delete 2>/dev/null || true
find "$TARGET_DIR" -name "*.db-*" -delete 2>/dev/null || true

# Remove cache files
rm -f "$TARGET_DIR/claude/data/capability_cache.json" 2>/dev/null || true
rm -f "$TARGET_DIR/claude/data/context_state.json" 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Scrubbed personal data and caches"

# ───────────────────────────────────────────────────────────────────
# Step 4: Create placeholder directories
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 4: Creating placeholder directories...${NC}"

# Create directories that should exist but be empty
mkdir -p "$TARGET_DIR/claude/context/personal"
touch "$TARGET_DIR/claude/context/personal/.gitkeep"

mkdir -p "$TARGET_DIR/claude/data/databases/user"
touch "$TARGET_DIR/claude/data/databases/user/.gitkeep"

mkdir -p "$TARGET_DIR/claude/data/databases/system"
touch "$TARGET_DIR/claude/data/databases/system/.gitkeep"

mkdir -p "$TARGET_DIR/claude/data/databases/intelligence"
touch "$TARGET_DIR/claude/data/databases/intelligence/.gitkeep"

mkdir -p "$TARGET_DIR/claude/tools/experimental"
touch "$TARGET_DIR/claude/tools/experimental/.gitkeep"

mkdir -p "$TARGET_DIR/claude/extensions"
touch "$TARGET_DIR/claude/extensions/.gitkeep"

echo -e "  ${GREEN}✓${NC} Created placeholder directories"

# ───────────────────────────────────────────────────────────────────
# Step 5: Initialize git repository
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 5: Initializing git repository...${NC}"

cd "$TARGET_DIR"
git init
git add -A

# Create initial commit
git commit -m "$(cat <<'EOF'
Initial commit: Maia v2.0.0 - Multi-user collaboration ready

Maia (My AI Agent) - Personal AI infrastructure with 200+ tools and 49 agents.

Features:
- Multi-user collaboration support (CODEOWNERS, CI/CD, hooks)
- Portable path resolution (PathManager)
- Performance baseline monitoring
- Defense-in-depth security gates
- Emergency rollback workflow

Setup:
  ./scripts/setup-team-member.sh

Documentation:
  .github/CONTRIBUTING.md

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"

echo -e "  ${GREEN}✓${NC} Git repository initialized with initial commit"

# ───────────────────────────────────────────────────────────────────
# Step 6: Final scan
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Step 6: Final personal data scan...${NC}"

# Check for any remaining personal data
if grep -r "naythandawe\|/Users/naythan\|naythan.dev" "$TARGET_DIR" --include="*.py" --include="*.md" 2>/dev/null | grep -v "CODEOWNERS\|CONTRIBUTING\|\.gitignore" | head -5; then
    echo -e "  ${YELLOW}⚠️${NC} Some personal references found - review manually"
else
    echo -e "  ${GREEN}✓${NC} No personal data detected"
fi

# ───────────────────────────────────────────────────────────────────
# Complete!
# ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    MIGRATION COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Fresh repository created at: $TARGET_DIR"
echo ""
echo "Next steps:"
echo ""
echo "  1. Review the new repo:"
echo "     cd $TARGET_DIR"
echo "     git log --oneline"
echo ""
echo "  2. Create new GitHub repository (github.com/new)"
echo ""
echo "  3. Push to GitHub:"
echo "     git remote add origin git@github.com:YOUR-ORG/maia.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "  4. Configure GitHub:"
echo "     - Enable branch protection for main"
echo "     - Create teams: maia-core, maia-sre, maia-security"
echo "     - Add ADMIN_PAT secret"
echo ""
echo "  5. Invite team members to clone and run:"
echo "     ./scripts/setup-team-member.sh"
echo ""

# Cleanup
rm -f /tmp/maia_files_to_copy.txt /tmp/maia_files_unique.txt
