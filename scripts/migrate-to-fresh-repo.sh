#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Maia Fresh Repository Migration Script v2.0
#
# Creates a clean copy of Maia following the MIGRATION_MANIFEST.md spec.
# Properly separates: REPO (shared), USER (~/.maia), REGEN (databases)
#
# Usage:
#   ./scripts/migrate-to-fresh-repo.sh /path/to/new/maia
#
# See scripts/MIGRATION_MANIFEST.md for detailed file categorization.
# ═══════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get source directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 /path/to/new/maia${NC}"
    echo ""
    echo "Example:"
    echo "  $0 ~/maia-clean"
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
    echo "Remove it first: rm -rf $TARGET_DIR"
    exit 1
fi

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════════"
echo "          MAIA FRESH REPOSITORY MIGRATION v2.0"
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo ""

cd "$SOURCE_DIR"

# Counters
COPIED=0
SKIPPED=0
TEMPLATED=0

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Create target structure
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}Step 1: Creating target directory structure...${NC}"
mkdir -p "$TARGET_DIR"

# Create all required directories
mkdir -p "$TARGET_DIR"/{.github/workflows,scripts/hooks,tests/core,tests/sre,tests/security}
mkdir -p "$TARGET_DIR"/claude/{agents,commands,hooks/tests,extensions,tools/experimental}
mkdir -p "$TARGET_DIR"/claude/context/{core,tools/mcp,tools/monitoring,personal}
mkdir -p "$TARGET_DIR"/claude/data/{project_status/active,project_status/archive,ab_tests}
mkdir -p "$TARGET_DIR"/claude/data/databases/{system,intelligence,user}
mkdir -p "$TARGET_DIR"/claude/tools/{core,sre/tests,security,automation,business,communication}
mkdir -p "$TARGET_DIR"/claude/tools/{dashboards,monitoring,servicedesk,document_conversion}
mkdir -p "$TARGET_DIR"/claude/tools/{interview,scripts/tests,archive,orchestration}
mkdir -p "$TARGET_DIR"/claude/infrastructure

echo -e "  ${GREEN}✓${NC} Created directory structure"

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Copy REPO files (shared, goes in git)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 2: Copying REPO files (shared code)...${NC}"

copy_file() {
    local src="$1"
    local dst="$2"
    if [ -f "$SOURCE_DIR/$src" ]; then
        mkdir -p "$(dirname "$TARGET_DIR/$dst")"
        cp "$SOURCE_DIR/$src" "$TARGET_DIR/$dst"
        ((COPIED++))
        return 0
    fi
    return 1
}

copy_dir() {
    local src="$1"
    local dst="${2:-$1}"
    if [ -d "$SOURCE_DIR/$src" ]; then
        mkdir -p "$TARGET_DIR/$dst"
        # Copy files but exclude patterns
        find "$SOURCE_DIR/$src" -type f \
            ! -name "*.db" \
            ! -name "*.db-*" \
            ! -name "*_naythan*" \
            ! -name "*.pyc" \
            ! -path "*/__pycache__/*" \
            ! -path "*/session/*" \
            -exec sh -c '
                src_file="$1"
                src_base="$2"
                tgt_base="$3"
                rel_path="${src_file#$src_base/}"
                mkdir -p "$(dirname "$tgt_base/$rel_path")"
                cp "$src_file" "$tgt_base/$rel_path"
            ' _ {} "$SOURCE_DIR/$src" "$TARGET_DIR/$dst" \;
        return 0
    fi
    return 1
}

# Root level files
echo -e "  ${CYAN}Root files...${NC}"
for f in CLAUDE.md SYSTEM_STATE.md VERSION CHANGELOG.md requirements.txt requirements-dev.txt .gitignore setup.sh pytest.ini; do
    copy_file "$f" "$f" && echo -e "    ${GREEN}✓${NC} $f"
done

# .github (CI/CD, CODEOWNERS)
echo -e "  ${CYAN}.github/...${NC}"
copy_dir ".github" ".github"
echo -e "    ${GREEN}✓${NC} .github/ (workflows, CODEOWNERS, CONTRIBUTING)"

# Scripts
echo -e "  ${CYAN}scripts/...${NC}"
copy_dir "scripts" "scripts"
echo -e "    ${GREEN}✓${NC} scripts/ (hooks, setup, migration)"

# Tests
echo -e "  ${CYAN}tests/...${NC}"
copy_dir "tests" "tests"
echo -e "    ${GREEN}✓${NC} tests/"

# Agents (all shared)
echo -e "  ${CYAN}claude/agents/...${NC}"
copy_dir "claude/agents" "claude/agents"
echo -e "    ${GREEN}✓${NC} claude/agents/ (all agent definitions)"

# Commands (all shared)
echo -e "  ${CYAN}claude/commands/...${NC}"
copy_dir "claude/commands" "claude/commands"
echo -e "    ${GREEN}✓${NC} claude/commands/"

# Hooks (all shared)
echo -e "  ${CYAN}claude/hooks/...${NC}"
copy_dir "claude/hooks" "claude/hooks"
echo -e "    ${GREEN}✓${NC} claude/hooks/"

# Context - CORE (shared)
echo -e "  ${CYAN}claude/context/core/...${NC}"
copy_file "claude/context/ufc_system.md" "claude/context/ufc_system.md"
copy_dir "claude/context/core" "claude/context/core"
echo -e "    ${GREEN}✓${NC} claude/context/core/"

# Context - TOOLS (shared)
echo -e "  ${CYAN}claude/context/tools/...${NC}"
copy_dir "claude/context/tools" "claude/context/tools"
echo -e "    ${GREEN}✓${NC} claude/context/tools/"

# Tools - ALL subdirectories (shared code)
echo -e "  ${CYAN}claude/tools/...${NC}"
for tool_dir in core sre security automation business communication dashboards monitoring servicedesk document_conversion interview scripts ir archive experimental orchestration learning; do
    if [ -d "$SOURCE_DIR/claude/tools/$tool_dir" ]; then
        copy_dir "claude/tools/$tool_dir" "claude/tools/$tool_dir"
    fi
done
# Also copy root-level tools
for f in "$SOURCE_DIR"/claude/tools/*.py; do
    if [ -f "$f" ]; then
        fname=$(basename "$f")
        copy_file "claude/tools/$fname" "claude/tools/$fname"
    fi
done
echo -e "    ${GREEN}✓${NC} claude/tools/ (all tool directories)"

# Data - project_status (shared documentation)
echo -e "  ${CYAN}claude/data/project_status/...${NC}"
copy_dir "claude/data/project_status" "claude/data/project_status"
echo -e "    ${GREEN}✓${NC} claude/data/project_status/"

# Data - ab_tests (shared test scenarios)
echo -e "  ${CYAN}claude/data/ab_tests/...${NC}"
copy_dir "claude/data/ab_tests" "claude/data/ab_tests"
echo -e "    ${GREEN}✓${NC} claude/data/ab_tests/"

# Infrastructure (shared)
echo -e "  ${CYAN}claude/infrastructure/...${NC}"
copy_dir "claude/infrastructure" "claude/infrastructure"
# Remove any .env files
find "$TARGET_DIR/claude/infrastructure" -name ".env" -delete 2>/dev/null || true
find "$TARGET_DIR/claude/infrastructure" -name "*.env" -delete 2>/dev/null || true
echo -e "    ${GREEN}✓${NC} claude/infrastructure/ (without .env files)"

echo -e "  ${GREEN}✓${NC} Copied $COPIED files"

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Create TEMPLATES (for user-specific files)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 3: Creating templates for user files...${NC}"

# Profile template
cat > "$TARGET_DIR/claude/context/personal/TEMPLATE_profile.md" << 'TEMPLATE'
# Personal Profile

## Identity
- **Name**: [Your Full Name]
- **Role**: [Your Role/Title]
- **Team**: [Your Team]
- **Location**: [Your Location]

## Technical Focus
- **Primary Areas**: [e.g., Azure, Security, SRE]
- **Certifications**: [e.g., AZ-104, AZ-500]
- **Languages**: [e.g., Python, PowerShell, Terraform]

## Preferences
- **Default Agent**: sre_principal_engineer_agent
- **Working Style**: [e.g., "Prefer detailed explanations", "Concise responses"]
- **Communication**: [e.g., "Technical, direct"]

## Context
<!-- Add any personal notes or context Maia should know -->
<!-- This file lives at ~/.maia/context/personal/profile.md -->
<!-- It is NOT committed to the shared repository -->

TEMPLATE
((TEMPLATED++))
echo -e "  ${GREEN}✓${NC} Created TEMPLATE_profile.md"

# User preferences template
cat > "$TARGET_DIR/claude/data/TEMPLATE_user_preferences.json" << 'TEMPLATE'
{
  "default_agent": "sre_principal_engineer_agent",
  "fallback_agent": "sre_principal_engineer_agent",
  "model_preference": "sonnet",
  "version": "1.0",
  "description": "User-specific Maia preferences - copy to ~/.maia/data/user_preferences.json",
  "settings": {
    "verbose_mode": false,
    "auto_commit": false,
    "theme": "default"
  }
}
TEMPLATE
((TEMPLATED++))
echo -e "  ${GREEN}✓${NC} Created TEMPLATE_user_preferences.json"

# .gitkeep for personal directory
touch "$TARGET_DIR/claude/context/personal/.gitkeep"

echo -e "  ${GREEN}✓${NC} Created $TEMPLATED templates"

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Skip USER files (document what's not copied)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 4: Skipping USER files (will be in ~/.maia/)...${NC}"

echo -e "  ${CYAN}Skipped (user creates own):${NC}"
echo -e "    - claude/context/personal/profile.md"
echo -e "    - claude/data/user_preferences.json"
echo -e "    - claude/data/databases/user/*.db"
echo -e "    - claude/data/transcripts/"
echo -e "    - claude/data/email_commands/"
echo -e "    - Session files (/tmp/maia_*)"

((SKIPPED+=10))
echo -e "  ${GREEN}✓${NC} Documented skipped USER files"

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Remove REGEN files (databases that regenerate)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 5: Removing REGEN files (will regenerate locally)...${NC}"

# Remove any databases that slipped through
find "$TARGET_DIR" -name "*.db" -type f -delete 2>/dev/null || true
find "$TARGET_DIR" -name "*.db-wal" -type f -delete 2>/dev/null || true
find "$TARGET_DIR" -name "*.db-shm" -type f -delete 2>/dev/null || true
find "$TARGET_DIR" -name "*.db-journal" -type f -delete 2>/dev/null || true

# Remove cache files
rm -f "$TARGET_DIR/claude/data/capability_cache.json" 2>/dev/null || true
rm -f "$TARGET_DIR/claude/data/context_state.json" 2>/dev/null || true
rm -f "$TARGET_DIR/claude/data/llm_routing_log.jsonl" 2>/dev/null || true
rm -f "$TARGET_DIR/claude/data/model_usage_log.txt" 2>/dev/null || true

# Remove session/temp directories
rm -rf "$TARGET_DIR/claude/context/session" 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Removed regenerable databases and caches"

# ═══════════════════════════════════════════════════════════════════
# STEP 6: Remove DELETE files (temp, logs, obsolete)
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 6: Removing DELETE files (temp/obsolete)...${NC}"

# Remove Python cache
find "$TARGET_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TARGET_DIR" -name "*.pyc" -delete 2>/dev/null || true

# Remove log files
find "$TARGET_DIR" -name "*.log" -delete 2>/dev/null || true

# Remove .env files
find "$TARGET_DIR" -name ".env" -delete 2>/dev/null || true
find "$TARGET_DIR" -name ".env.*" ! -name ".env.example" -delete 2>/dev/null || true

# Remove PID files
find "$TARGET_DIR" -name "*.pid" -delete 2>/dev/null || true

# Remove any remaining personal data files
rm -rf "$TARGET_DIR/claude/data/transcripts" 2>/dev/null || true
rm -rf "$TARGET_DIR/claude/data/email_commands" 2>/dev/null || true
rm -rf "$TARGET_DIR/claude/data/ir_findings" 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Removed temp and obsolete files"

# ═══════════════════════════════════════════════════════════════════
# STEP 7: Create .gitkeep files for empty directories
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 7: Creating .gitkeep for empty directories...${NC}"

for dir in \
    "claude/context/personal" \
    "claude/data/databases/user" \
    "claude/data/databases/system" \
    "claude/data/databases/intelligence" \
    "claude/tools/experimental" \
    "claude/extensions"
do
    mkdir -p "$TARGET_DIR/$dir"
    touch "$TARGET_DIR/$dir/.gitkeep"
done

echo -e "  ${GREEN}✓${NC} Created .gitkeep files"

# ═══════════════════════════════════════════════════════════════════
# STEP 8: Final personal data scan and scrub
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 8: Final personal data scan...${NC}"

# Patterns to search for (comprehensive from PII_REDACTION_CHECKLIST.md)
PERSONAL_PATTERNS="naythandawe|naythan\.dev|naythan\.general|naythan\.dawe|naythan\.me|nd25@|/Users/naythan|@orro\.group|Naythan Dawe|\"Naythan\""

# Find any remaining personal data
FOUND_PERSONAL=$(grep -rlE "$PERSONAL_PATTERNS" "$TARGET_DIR" \
    --include="*.py" --include="*.md" --include="*.json" --include="*.yml" \
    2>/dev/null | grep -v "CODEOWNERS\|CONTRIBUTING\|MIGRATION_MANIFEST\|\.gitignore\|PII_REDACTION" || true)

if [ -n "$FOUND_PERSONAL" ]; then
    echo -e "  ${YELLOW}⚠️  Found personal data in:${NC}"
    echo "$FOUND_PERSONAL" | while read -r f; do
        echo -e "    - ${f#$TARGET_DIR/}"
    done
    echo ""
    echo -e "  ${YELLOW}Attempting automatic scrub...${NC}"

    # Scrub common patterns (comprehensive - 16 patterns from checklist)
    find "$TARGET_DIR" -type f \( -name "*.py" -o -name "*.md" -o -name "*.json" \) \
        -exec sed -i '' \
            -e 's/naythandawe/USER/g' \
            -e 's/naythan-orro/USER-ORG/g' \
            -e 's/naythan\.dev+maia@gmail\.com/maia-inbox@example.com/g' \
            -e 's/naythan\.dev@gmail\.com/user@example.com/g' \
            -e 's/naythan\.general@icloud\.com/user@example.com/g' \
            -e 's/naythan\.general@gmail\.com/user@example.com/g' \
            -e 's/naythan\.dawe@orro\.group/user@company.com/g' \
            -e 's/naythan\.dawe@nwcomputing\.com\.au/user@company.com/g' \
            -e 's/naythan\.me@londonxyz\.com/test@example.com/g' \
            -e 's/nd25@londonxyz\.com/user@example.com/g' \
            -e 's/@orro\.group/@company.com/g' \
            -e 's/"Naythan Dawe"/"User Name"/g' \
            -e 's/"Naythan"/"User"/g' \
            -e "s/owner=\"Naythan\"/owner=None/g" \
            -e "s/default=\"Naythan\"/default=None/g" \
            -e 's/user_id="naythan"/user_id="user"/g' \
            {} \; 2>/dev/null || true

    echo -e "  ${GREEN}✓${NC} Scrubbed personal data patterns (16 replacements)"
else
    echo -e "  ${GREEN}✓${NC} No personal data detected"
fi

# ═══════════════════════════════════════════════════════════════════
# STEP 9: Initialize git repository
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}Step 9: Initializing git repository...${NC}"

cd "$TARGET_DIR"
git init -q
git add -A

# Count files
FILE_COUNT=$(git ls-files | wc -l | tr -d ' ')

git commit -q -m "$(cat <<'EOF'
Initial commit: Maia v2.0.0 - Multi-user collaboration ready

Maia (My AI Agent) - Personal AI infrastructure with 200+ tools and 49 agents.

Architecture:
- Shared repo (maia/) - tools, agents, context, CI/CD
- Personal data (~/.maia/) - profile, preferences, user databases
- Work outputs (~/work_projects/) - NOT in either repo

Features:
- Multi-user collaboration (CODEOWNERS, branch protection)
- Portable path resolution (PathManager)
- Defense-in-depth security gates (pre-commit → CI → CODEOWNERS)
- Performance baseline monitoring
- Emergency rollback workflow (<5 min MTTR)

Setup:
  ./scripts/setup-team-member.sh

Documentation:
  .github/CONTRIBUTING.md
  scripts/MIGRATION_MANIFEST.md

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"

echo -e "  ${GREEN}✓${NC} Git repository initialized ($FILE_COUNT files)"

# ═══════════════════════════════════════════════════════════════════
# COMPLETE!
# ═══════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    MIGRATION COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Summary:"
echo "  Files copied:    $COPIED"
echo "  Files skipped:   $SKIPPED (user-specific)"
echo "  Templates:       $TEMPLATED"
echo "  Total in repo:   $FILE_COUNT"
echo ""
echo "Fresh repository: $TARGET_DIR"
echo ""
echo -e "${CYAN}Directory structure:${NC}"
echo "  $TARGET_DIR/              ← Shared repo (git)"
echo "  ~/.maia/                  ← Personal data (NOT in git)"
echo "  ~/work_projects/          ← Work outputs (NOT in git)"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo ""
echo "  1. Review the new repo:"
echo "     cd $TARGET_DIR"
echo "     ls -la"
echo "     git log --oneline"
echo ""
echo "  2. Create new GitHub repository"
echo "     https://github.com/new"
echo ""
echo "  3. Push to GitHub:"
echo "     cd $TARGET_DIR"
echo "     git remote add origin git@github.com:YOUR-ORG/maia.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "  4. Configure GitHub:"
echo "     • Branch protection: Require PR reviews for main"
echo "     • Teams: maia-core, maia-sre, maia-security"
echo "     • Secret: ADMIN_PAT (for emergency rollback)"
echo ""
echo "  5. Team members clone and run:"
echo "     git clone git@github.com:YOUR-ORG/maia.git"
echo "     cd maia"
echo "     ./scripts/setup-team-member.sh"
echo ""
