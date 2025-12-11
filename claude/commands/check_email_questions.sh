#!/bin/bash
# Check for unanswered email questions manually

# Auto-detect MAIA_ROOT from script location if not set
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIA_ROOT="${MAIA_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

python3 "$MAIA_ROOT/claude/tools/email_question_monitor.py" --days "${1:-7}"
