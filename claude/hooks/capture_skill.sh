#!/bin/bash
# Capture Skill - Wrapper for pre-compaction learning capture
# Invoked by /capture command in Claude Code

set -euo pipefail

# Get MAIA_ROOT
MAIA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$MAIA_ROOT"

# Get context ID
CONTEXT_ID=$(python3 claude/hooks/swarm_auto_loader.py get_context_id)

echo "========================================"
echo "🔍 LEARNING CAPTURE"
echo "========================================"
echo ""
echo "Context ID: $CONTEXT_ID"
echo ""

# Execute learning capture
python3 claude/hooks/pre_compaction_learning_capture.py <<EOF
{
  "session_id": "$CONTEXT_ID",
  "transcript_path": "",
  "trigger": "skill",
  "hook_event_name": "Capture"
}
EOF

echo ""
echo "========================================"
echo "✅ CAPTURE COMPLETE"
echo "========================================"
echo ""
echo "📋 Verify capture:"
echo "   tail -5 ~/.maia/logs/pre_compaction_debug.log"
echo ""
