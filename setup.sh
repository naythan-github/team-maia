#!/bin/bash
# Maia Setup Script - Run this after cloning to get started
# This script sets up your environment for Maia development/usage
#
# Usage: ./setup.sh [--skip-optional]
#   --skip-optional: Skip optional features (Ollama, Docker checks)

set -e

# Parse arguments
SKIP_OPTIONAL=false
for arg in "$@"; do
    case $arg in
        --skip-optional)
            SKIP_OPTIONAL=true
            ;;
    esac
done

echo "========================================"
echo "  Maia Setup v2.0"
echo "========================================"
echo ""

# Get the directory where this script is located (= MAIA_ROOT)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MAIA_ROOT="$SCRIPT_DIR"

echo "MAIA_ROOT: $MAIA_ROOT"
echo ""

# Define user data directory
MAIA_USER_DIR="$HOME/.maia"

#=============================================================================
# Step 1: Check Python version
#=============================================================================
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "   WARNING: Python 3.11+ recommended (found $PYTHON_VERSION)"
    echo "   Some features may not work correctly."
else
    echo "   OK: Python $PYTHON_VERSION"
fi
echo ""

#=============================================================================
# Step 2: Install Python dependencies
#=============================================================================
echo "2. Installing Python dependencies..."
if [ -f "$MAIA_ROOT/requirements.txt" ]; then
    pip3 install -r "$MAIA_ROOT/requirements.txt" --quiet 2>/dev/null || pip3 install -r "$MAIA_ROOT/requirements.txt"
    echo "   OK: Dependencies installed"
else
    echo "   SKIP: requirements.txt not found"
fi
echo ""

#=============================================================================
# Step 3: Create project directories
#=============================================================================
echo "3. Creating project directories..."
mkdir -p "$MAIA_ROOT/claude/data/logs"
mkdir -p "$MAIA_ROOT/claude/data/databases/intelligence"
mkdir -p "$MAIA_ROOT/claude/data/databases/system"
mkdir -p "$MAIA_ROOT/claude/data/databases/user"
mkdir -p "$MAIA_ROOT/claude/data/project_status/active"
mkdir -p "$MAIA_ROOT/claude/data/project_status/archive"
echo "   OK: Project directories created"
echo ""

#=============================================================================
# Step 4: Create ~/.maia/ user directory structure
#=============================================================================
echo "4. Creating user directories (~/.maia/)..."
mkdir -p "$MAIA_USER_DIR/data/databases/user"
mkdir -p "$MAIA_USER_DIR/data/checkpoints"
mkdir -p "$MAIA_USER_DIR/sessions"
mkdir -p "$MAIA_USER_DIR/memory"
mkdir -p "$MAIA_USER_DIR/context/personal"
mkdir -p "$MAIA_USER_DIR/projects"
mkdir -p "$MAIA_USER_DIR/mcp_credentials"
echo "   OK: User directories created at $MAIA_USER_DIR"
echo ""

#=============================================================================
# Step 5: Initialize user preferences
#=============================================================================
echo "5. Initializing user preferences..."
USER_PREFS_PATH="$MAIA_USER_DIR/data/user_preferences.json"
if [ ! -f "$USER_PREFS_PATH" ]; then
    cat > "$USER_PREFS_PATH" << 'EOF'
{
  "default_agent": "sre_principal_engineer_agent",
  "fallback_agent": "sre_principal_engineer_agent",
  "handoffs_enabled": true,
  "handoffs_max": 5,
  "version": "1.1"
}
EOF
    echo "   OK: User preferences created at $USER_PREFS_PATH"
else
    echo "   SKIP: User preferences already exist"
fi
echo ""

#=============================================================================
# Step 6: Create personal profile template
#=============================================================================
echo "6. Creating personal profile template..."
PROFILE_PATH="$MAIA_USER_DIR/context/personal/profile.md"
if [ ! -f "$PROFILE_PATH" ]; then
    cat > "$PROFILE_PATH" << 'EOF'
# Personal Profile

## Identity
- Name: [To be filled]
- Role: [To be filled]
- Team: [To be filled]
- Email: [To be filled]

## Preferences
- Default Agent: sre_principal_engineer_agent
- Working Style: [To be filled]
- Focus Areas: [To be filled]
- Timezone: [To be filled]

## Notes
[Add any personal notes or preferences here]
EOF
    echo "   OK: Personal profile created at $PROFILE_PATH"
else
    echo "   SKIP: Personal profile already exists"
fi
echo ""

#=============================================================================
# Step 7: Set up shell environment
#=============================================================================
echo "7. Setting up shell environment..."
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    # Add MAIA_ROOT
    if ! grep -q "export MAIA_ROOT=" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Maia environment" >> "$SHELL_RC"
        echo "export MAIA_ROOT=\"$MAIA_ROOT\"" >> "$SHELL_RC"
        echo "   OK: Added MAIA_ROOT to $SHELL_RC"
    else
        echo "   SKIP: MAIA_ROOT already in $SHELL_RC"
    fi

    # Add PYTHONPATH
    if ! grep -q "PYTHONPATH.*MAIA_ROOT" "$SHELL_RC" 2>/dev/null; then
        echo "export PYTHONPATH=\"\$MAIA_ROOT:\$PYTHONPATH\"" >> "$SHELL_RC"
        echo "   OK: Added PYTHONPATH to $SHELL_RC"
    else
        echo "   SKIP: PYTHONPATH already configured"
    fi
else
    echo "   NOTE: Add to your shell profile:"
    echo "         export MAIA_ROOT=\"$MAIA_ROOT\""
    echo "         export PYTHONPATH=\"\$MAIA_ROOT:\$PYTHONPATH\""
fi
echo ""

#=============================================================================
# Step 8: Install Git hooks
#=============================================================================
echo "8. Installing Git hooks..."
GIT_HOOKS_DIR="$MAIA_ROOT/.git/hooks"
SOURCE_HOOKS_DIR="$MAIA_ROOT/scripts/hooks"

if [ -d "$GIT_HOOKS_DIR" ] && [ -d "$SOURCE_HOOKS_DIR" ]; then
    # Install pre-commit hook
    if [ -f "$SOURCE_HOOKS_DIR/pre-commit" ]; then
        cp "$SOURCE_HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
        chmod +x "$GIT_HOOKS_DIR/pre-commit"
        echo "   OK: pre-commit hook installed"
    fi

    # Install pre-push hook if exists
    if [ -f "$SOURCE_HOOKS_DIR/pre-push" ]; then
        cp "$SOURCE_HOOKS_DIR/pre-push" "$GIT_HOOKS_DIR/pre-push"
        chmod +x "$GIT_HOOKS_DIR/pre-push"
        echo "   OK: pre-push hook installed"
    fi

    # Install post-merge hook if exists
    if [ -f "$SOURCE_HOOKS_DIR/post-merge" ]; then
        cp "$SOURCE_HOOKS_DIR/post-merge" "$GIT_HOOKS_DIR/post-merge"
        chmod +x "$GIT_HOOKS_DIR/post-merge"
        echo "   OK: post-merge hook installed"
    fi
else
    echo "   SKIP: Git hooks directory or source hooks not found"
fi
echo ""

#=============================================================================
# Step 9: Set up Claude Code configuration
#=============================================================================
echo "9. Setting up Claude Code configuration..."
CLAUDE_DIR="$MAIA_ROOT/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"

# Create .claude directory if it doesn't exist
mkdir -p "$COMMANDS_DIR"

# Create settings.local.json if it doesn't exist
SETTINGS_PATH="$CLAUDE_DIR/settings.local.json"
if [ ! -f "$SETTINGS_PATH" ]; then
    cat > "$SETTINGS_PATH" << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(ls:*)",
      "Bash(git:*)",
      "Bash(pytest:*)",
      "Bash(pip3:*)",
      "Bash(mkdir:*)",
      "Bash(cat:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(echo:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(wc:*)",
      "Bash(sort:*)",
      "Bash(sqlite3:*)",
      "Bash(PYTHONPATH=:*)",
      "Skill(init)",
      "Skill(init:*)",
      "Skill(close-session)",
      "Skill(close-session:*)",
      "Skill(capture)",
      "Skill(capture:*)",
      "Skill(checkpoint)",
      "Skill(checkpoint:*)",
      "Skill(handoff-status)",
      "Skill(handoff-status:*)"
    ],
    "additionalDirectories": [
      "~/.maia/sessions"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/claude/hooks/user-prompt-submit"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/tool_output_capture.py",
            "timeout": 5000
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/post_compaction_restore.py",
            "timeout": 2000
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/pre_compaction_learning_capture.py",
            "timeout": 5000
          }
        ]
      },
      {
        "matcher": "manual",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/claude/hooks/pre_compaction_learning_capture.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
EOF
    echo "   OK: Created settings.local.json with hooks configuration"
else
    echo "   SKIP: settings.local.json already exists"
fi

# Create skill symlinks
create_skill_link() {
    local skill_name="$1"
    local source="$MAIA_ROOT/claude/commands/${skill_name}.md"
    local target="$COMMANDS_DIR/${skill_name}.md"

    if [ -f "$source" ] && [ ! -e "$target" ]; then
        ln -s "$source" "$target" 2>/dev/null || cp "$source" "$target"
        echo "   OK: Linked skill /${skill_name}"
    fi
}

# Create skill files if they don't exist
create_skill_file() {
    local skill_name="$1"
    local content="$2"
    local target="$COMMANDS_DIR/${skill_name}.md"

    if [ ! -e "$target" ]; then
        echo "$content" > "$target"
        echo "   OK: Created skill /${skill_name}"
    fi
}

# Link skills from claude/commands/
create_skill_link "init"
create_skill_link "handoff-status"

# Create local skill files
if [ ! -e "$COMMANDS_DIR/close-session.md" ]; then
    cat > "$COMMANDS_DIR/close-session.md" << 'EOF'
---
name: close-session
description: End agent session and capture learning
---

End the current agent session:
1. Capture any learnings from this session
2. Clear session state
3. Ready for next session

Run: python3 -c "from claude.tools.learning.session import get_session_manager; m=get_session_manager(); m.end_session()"
EOF
    echo "   OK: Created skill /close-session"
fi

if [ ! -e "$COMMANDS_DIR/capture.md" ]; then
    cat > "$COMMANDS_DIR/capture.md" << 'EOF'
---
name: capture
description: Capture learning from current work
---

Capture learnings from the current session.
Use this when you want to save insights without ending the session.
EOF
    echo "   OK: Created skill /capture"
fi

if [ ! -e "$COMMANDS_DIR/checkpoint.md" ]; then
    cat > "$COMMANDS_DIR/checkpoint.md" << 'EOF'
---
name: checkpoint
description: Create progress checkpoint
---

Create a checkpoint of current progress.
Use this before complex operations or at phase boundaries.
EOF
    echo "   OK: Created skill /checkpoint"
fi

# Create local LLM skill files
for skill in codellama starcoder local; do
    if [ ! -e "$COMMANDS_DIR/${skill}.md" ]; then
        cat > "$COMMANDS_DIR/${skill}.md" << EOF
---
name: ${skill}
description: Route query to ${skill} local LLM
---

Route the following query to the ${skill} local LLM via Ollama.
Requires Ollama to be running with the ${skill} model available.
EOF
        echo "   OK: Created skill /${skill}"
    fi
done

echo ""

#=============================================================================
# Step 10: Initialize/verify databases
#=============================================================================
echo "10. Initializing databases..."

# Check if capabilities.db exists and has data
CAPS_DB="$MAIA_ROOT/claude/data/databases/system/capabilities.db"
if [ -f "$CAPS_DB" ]; then
    COUNT=$(sqlite3 "$CAPS_DB" "SELECT COUNT(*) FROM capabilities;" 2>/dev/null || echo "0")
    if [ "$COUNT" -gt 0 ]; then
        echo "   OK: capabilities.db exists with $COUNT entries"
    else
        echo "   NOTE: capabilities.db exists but empty - run: python3 claude/tools/sre/capabilities_registry.py scan"
    fi
else
    echo "   NOTE: capabilities.db not found - run: python3 claude/tools/sre/capabilities_registry.py scan"
fi

# Check system_state.db
STATE_DB="$MAIA_ROOT/claude/data/databases/system/system_state.db"
if [ -f "$STATE_DB" ]; then
    echo "   OK: system_state.db exists"
else
    echo "   NOTE: system_state.db not found - run: python3 claude/tools/sre/system_state_etl.py --recent all"
fi

echo ""

#=============================================================================
# Step 11: Verify core imports
#=============================================================================
echo "11. Verifying installation..."
export PYTHONPATH="$MAIA_ROOT:$PYTHONPATH"

if python3 -c "from claude.tools.core.paths import MAIA_ROOT; print(f'   Paths module: {MAIA_ROOT}')" 2>/dev/null; then
    echo "   OK: Core paths module working"
else
    echo "   WARNING: Core paths module failed to import"
fi

if python3 -c "from claude.hooks.swarm_auto_loader import get_context_id; print('   Swarm loader: OK')" 2>/dev/null; then
    echo "   OK: Swarm auto loader working"
else
    echo "   WARNING: Swarm auto loader failed to import"
fi

if python3 -c "from claude.tools.learning.session import get_session_manager; print('   Learning system: OK')" 2>/dev/null; then
    echo "   OK: Learning system working"
else
    echo "   WARNING: Learning system failed to import"
fi

echo ""

#=============================================================================
# Step 12: Check optional dependencies
#=============================================================================
if [ "$SKIP_OPTIONAL" = false ]; then
    echo "12. Checking optional features..."

    # Ollama for local LLMs
    if command -v ollama &> /dev/null; then
        echo "   OK: Ollama installed"
        if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
            echo "   OK: nomic-embed-text embedding model available"
        else
            echo "   NOTE: Run 'ollama pull nomic-embed-text' for RAG features"
        fi
    else
        echo "   NOTE: Install Ollama for local LLM features (brew install ollama)"
    fi

    # Docker for ServiceDesk dashboard
    if command -v docker &> /dev/null; then
        echo "   OK: Docker installed"
    else
        echo "   NOTE: Install Docker for ServiceDesk dashboard features"
    fi
    echo ""
else
    echo "12. Skipping optional features check (--skip-optional)"
    echo ""
fi

#=============================================================================
# Summary
#=============================================================================
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Quick Start:"
echo "  1. Source your shell: source $SHELL_RC"
echo "  2. Run Maia tests:    pytest tests/ -v --tb=short"
echo "  3. Use with Claude Code"
echo ""
echo "Skills available:"
echo "  /init           - Initialize session with agent"
echo "  /close-session  - End session and capture learning"
echo "  /capture        - Capture learning"
echo "  /checkpoint     - Create progress checkpoint"
echo "  /handoff-status - View agent handoff status"
echo ""
echo "Optional setup (run separately if needed):"
echo "  - M365 MCP:     ./claude/tools/mcp/setup_m365_mcp.sh"
echo "  - Vault setup:  ./claude/tools/sre/setup_backup_keychain.sh"
echo "  - Regen DBs:    python3 claude/tools/sre/capabilities_registry.py scan"
echo ""
echo "Documentation:"
echo "  - System overview:    CLAUDE.md"
echo "  - Capabilities:       claude/context/core/capability_index.md"
echo "  - Recent changes:     SYSTEM_STATE.md"
echo ""
