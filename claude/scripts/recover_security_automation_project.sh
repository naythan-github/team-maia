#!/bin/bash
# Security Automation Project Recovery Script
# Purpose: Quickly restore context for Security Automation Enhancement Project
# Usage: ./recover_security_automation_project.sh [checkpoint_number]
# Created: 2025-10-13

set -e

PROJECT_ID="SECURITY_AUTO_001"
PROJECT_FILE="$HOME/git/maia/claude/data/SECURITY_AUTOMATION_PROJECT.md"
CHECKPOINT_DIR="$HOME/git/maia/claude/data/implementation_checkpoints/$PROJECT_ID"
EXPERIMENTAL_DIR="$HOME/git/maia/claude/extensions/experimental"

echo "🔄 Security Automation Project Recovery"
echo "========================================"
echo ""

# Check if project file exists
if [ ! -f "$PROJECT_FILE" ]; then
    echo "❌ Error: Project file not found at $PROJECT_FILE"
    exit 1
fi

echo "📋 PROJECT OVERVIEW"
echo "-------------------"
echo "Project ID: $PROJECT_ID"
echo "Project File: $PROJECT_FILE"
echo "Status: $(grep '^**Current Phase**:' $PROJECT_FILE | cut -d: -f2)"
echo ""

echo "📊 PROJECT PHASES"
echo "-----------------"
grep "^### Phase [0-9]:" "$PROJECT_FILE" | sed 's/### //'
echo ""

echo "✅ CHECKPOINT STATUS"
echo "--------------------"
if [ -d "$CHECKPOINT_DIR" ]; then
    echo "Checkpoints found:"
    ls -1 "$CHECKPOINT_DIR" 2>/dev/null || echo "No checkpoint files yet"
else
    echo "⚠️  No checkpoints directory yet (will be created during implementation)"
fi
echo ""

echo "🔬 EXPERIMENTAL FILES"
echo "---------------------"
if [ -d "$EXPERIMENTAL_DIR" ]; then
    SECURITY_FILES=$(find "$EXPERIMENTAL_DIR" -name "security_*" 2>/dev/null)
    if [ -n "$SECURITY_FILES" ]; then
        echo "Security-related experimental files:"
        find "$EXPERIMENTAL_DIR" -name "security_*" -exec ls -lh {} \;
    else
        echo "⚠️  No security experimental files yet (Phase 1 not started)"
    fi
else
    echo "⚠️  Experimental directory not found"
fi
echo ""

echo "🛡️ EXISTING SECURITY TOOLS"
echo "---------------------------"
SECURITY_TOOL_DIR="$HOME/git/maia/claude/tools/security"
if [ -d "$SECURITY_TOOL_DIR" ]; then
    echo "Production security tools:"
    ls -lh "$SECURITY_TOOL_DIR"/*.py 2>/dev/null | grep -v "^total" | awk '{print $9, "("$5")"}'
else
    echo "⚠️  Security tools directory not found"
fi
echo ""

echo "📈 CURRENT SECURITY STATUS"
echo "--------------------------"
SCANNER="$HOME/git/maia/claude/tools/security/local_security_scanner.py"
if [ -f "$SCANNER" ]; then
    echo "Running quick security scan..."
    python3 "$SCANNER" --quick 2>/dev/null || echo "⚠️  Scanner execution failed (may need dependencies)"
else
    echo "⚠️  Security scanner not found at $SCANNER"
fi
echo ""

echo "🔧 BACKGROUND SERVICES"
echo "----------------------"
echo "Checking for security-related LaunchAgents..."
launchctl list | grep -i "maia.*security" || echo "⚠️  No security services currently running"
echo ""

echo "➡️  NEXT STEPS"
echo "---------------"
echo "1. Read project plan: cat $PROJECT_FILE"
echo "2. Review current phase details"
echo "3. Check experimental directory for work in progress"
echo "4. Continue from last completed checkpoint"
echo ""

echo "📚 QUICK COMMANDS"
echo "-----------------"
echo "View full project plan:"
echo "  less $PROJECT_FILE"
echo ""
echo "View specific phase:"
echo "  grep -A 20 '^### Phase 1:' $PROJECT_FILE"
echo ""
echo "Start Phase 1:"
echo "  # Begin implementation following Phase 1 tasks in project plan"
echo ""
echo "Save checkpoint:"
echo "  # Create checkpoint file after completing each phase"
echo "  mkdir -p $CHECKPOINT_DIR"
echo "  echo 'Phase X complete' > $CHECKPOINT_DIR/checkpoint_X.md"
echo ""

echo "✅ Recovery script complete!"
echo ""
echo "💡 TIP: If this is your first time seeing this project,"
echo "        start by reading the full project plan:"
echo "        less $PROJECT_FILE"
