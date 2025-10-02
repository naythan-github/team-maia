#!/bin/bash
# Maia Production Monitoring Cron Jobs

# Run intelligence engine monitoring every 5 minutes
*/5 * * * * cd /Users/naythan/git/maia && python3 claude/services/intelligence_engine_service.py --health-check

# Run comprehensive system backup daily at 2 AM
0 2 * * * cd /Users/naythan/git/maia && python3 claude/scripts/backup_production_data.py create daily

# Run comprehensive backup manager weekly at 3 AM on Sundays
0 3 * * 0 cd /Users/naythan/git/maia && python3 claude/tools/core/backup_manager.py backup --type weekly

# Cleanup old backups monthly at 4 AM on 1st of month
0 4 1 * * cd /Users/naythan/git/maia && python3 claude/scripts/backup_production_data.py cleanup

# Run system health check every hour
0 * * * * cd /Users/naythan/git/maia && python3 claude/services/health_monitor_service.py --check
