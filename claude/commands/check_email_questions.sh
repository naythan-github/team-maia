#!/bin/bash
# Check for unanswered email questions manually

python3 /Users/naythandawe/git/maia/claude/tools/email_question_monitor.py --days "${1:-7}"
