#!/bin/bash
# Move VTT Files from Downloads to Processing Folder
# Command wrapper for Downloads VTT Mover automation

MAIA_ROOT="$HOME/git/maia"

# Manual trigger for immediate move
python3 "$MAIA_ROOT/claude/tools/downloads_vtt_mover.py"
