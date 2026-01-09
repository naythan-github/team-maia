#!/bin/bash
# Checkpoint Skill - Wrapper for checkpoint generation
# Invoked by /checkpoint command in Claude Code

set -euo pipefail

# Get MAIA_ROOT
MAIA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$MAIA_ROOT"

echo "========================================"
echo "📋 CHECKPOINT GENERATOR"
echo "========================================"
echo ""

# Execute checkpoint generation
# Always use --auto mode for skill invocation (non-interactive)
python3 claude/tools/sre/checkpoint.py --auto

echo ""
echo "📝 Checkpoint saved in auto mode"
echo "   Edit /tmp/CHECKPOINT_PHASE_*.md to add phase-specific details"
echo ""
