#!/bin/bash
# Automated Backup Script for Maia
# Orchestrates production backup and system checkpoints

set -euo pipefail

# Configuration
BACKUP_TYPE="${1:-daily}"
MAIA_ROOT="/Users/naythan/git/maia"
LOG_DIR="$MAIA_ROOT/claude/logs/backups"
LOG_FILE="$LOG_DIR/backup_${BACKUP_TYPE}_$(date +%Y%m%d_%H%M%S).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Redirect all output to log file and console
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "Maia Automated Backup System"
echo "========================================="
echo "Backup Type: $BACKUP_TYPE"
echo "Started: $(date)"
echo "Maia Root: $MAIA_ROOT"
echo ""

# Change to Maia root directory
cd "$MAIA_ROOT"

# Function to handle errors
handle_error() {
    echo "❌ ERROR: $1"
    echo "Backup failed at $(date)"

    # TODO: Send alert via autonomous_alert_system when integrated
    # python3 claude/tools/autonomous_alert_system.py \
    #   --title "Backup Failure" \
    #   --message "$1" \
    #   --category "system_health" \
    #   --priority "high"

    exit 1
}

# Step 1: Run production backup (databases, config, tools, agents)
echo "📦 Step 1: Creating production backup..."
echo ""

if python3 claude/tools/scripts/backup_production_data.py create "$BACKUP_TYPE"; then
    echo "✅ Production backup completed"
    echo ""
else
    handle_error "Production backup failed (backup_production_data.py)"
fi

# Step 2: Create system checkpoint for weekly/monthly backups
if [ "$BACKUP_TYPE" = "weekly" ] || [ "$BACKUP_TYPE" = "monthly" ]; then
    echo "📦 Step 2: Creating system checkpoint..."
    echo ""

    CHECKPOINT_NAME="automated_${BACKUP_TYPE}_$(date +%Y%m%d)"
    CHECKPOINT_DESC="Automated $BACKUP_TYPE checkpoint created by cron"

    if python3 claude/tools/system_backup_manager.py create-checkpoint "$CHECKPOINT_NAME" "$CHECKPOINT_DESC"; then
        echo "✅ System checkpoint created"
        echo ""
    else
        handle_error "System checkpoint failed (system_backup_manager.py)"
    fi
else
    echo "ℹ️  Step 2: Skipping system checkpoint (not weekly/monthly backup)"
    echo ""
fi

# Step 3: Verify backup was created
echo "🔍 Step 3: Verifying backup..."
echo ""

# Get latest backup from production backup system
LATEST_BACKUP=$(python3 -c "
import sys
sys.path.insert(0, '$MAIA_ROOT')
from claude.tools.scripts.backup_production_data import ProductionBackupSystem
backup_system = ProductionBackupSystem()
backups = backup_system.list_backups()
if backups:
    print(backups[0]['name'])
else:
    sys.exit(1)
" 2>/dev/null)

if [ -n "$LATEST_BACKUP" ]; then
    echo "✅ Backup verified: $LATEST_BACKUP"
    echo ""
else
    handle_error "Backup verification failed - no recent backup found"
fi

# Step 4: Cleanup old backups (retention policy)
echo "🧹 Step 4: Cleaning up old backups..."
echo ""

if python3 claude/tools/scripts/backup_production_data.py cleanup; then
    echo "✅ Cleanup completed"
    echo ""
else
    echo "⚠️  Cleanup had issues (non-fatal)"
    echo ""
fi

# Summary
echo "========================================="
echo "✅ Backup completed successfully"
echo "========================================="
echo "Backup Type: $BACKUP_TYPE"
echo "Latest Backup: $LATEST_BACKUP"
echo "Completed: $(date)"
echo "Log File: $LOG_FILE"
echo ""
echo "Next scheduled backups:"
echo "  Daily:   Every day at 2:00 AM"
echo "  Weekly:  Every Sunday at 3:00 AM"
echo "  Monthly: 1st of each month at 4:00 AM"
echo ""

exit 0