# LaunchAgent Inventory

**Purpose**: Track all Maia LaunchAgent automation (replaces cron-based automation)
**Location**: `~/Library/LaunchAgents/com.maia.*.plist`
**Last Updated**: 2025-11-26 (Phase 192+ architecture review)

---

## Active LaunchAgents

### ✅ **Production Services** (Confirmed Running)

| Service | Type | Schedule | Status | Logs | Purpose |
|---------|------|----------|--------|------|---------|
| **system-state-etl-backup** | Scheduled | Daily 2:00 AM | ✅ Running | `~/.maia/logs/etl_daily_backup.log` | Database ETL sync (Phase 192) |
| **security-orchestrator** | Continuous | Always (KeepAlive) | ✅ Running | `claude/data/logs/security_orchestrator_*.log` | Security scanning & compliance |
| **whisper-server** | Continuous | Always | ✅ Running | N/A | Voice dictation service |
| **intelligent-downloads-router** | Continuous | Always | ✅ Running | N/A | Download automation |
| **vtt-watcher** | Continuous | Always | ✅ Running | N/A | VTT file processing |
| **downloads-vtt-mover** | Continuous | Always | ✅ Running | N/A | VTT file organization |

### ⏸️ **Scheduled Services** (Status Unknown)

| Service | Type | Schedule | Logs | Purpose |
|---------|------|----------|------|---------|
| **daily-briefing** | Scheduled | Daily (time TBD) | N/A | Morning intelligence briefing |
| **morning-email-intelligence** | Scheduled | Daily morning | N/A | Email intelligence processing |
| **strategic-briefing** | Scheduled | TBD | N/A | Strategic analysis briefing |
| **weekly-review-reminder** | Scheduled | Weekly | N/A | Weekly review automation |
| **weekly-backlog-review** | Scheduled | Weekly | N/A | Backlog grooming |
| **downloads-organizer-scheduler** | Scheduled | TBD | N/A | Download organization |
| **backup-pruning** | Scheduled | TBD | N/A | Backup cleanup |
| **disaster-recovery** | Scheduled | TBD | N/A | DR validation |
| **system-state-archiver** | Scheduled | TBD | N/A | Archive old phases |
| **trello-status-tracker** | Scheduled | TBD | N/A | Trello integration |
| **email-rag-indexer** | Scheduled | TBD | N/A | Email RAG updates |
| **email-question-monitor** | Scheduled | TBD | N/A | Email command processing |
| **email-vtt-extractor** | Scheduled | TBD | N/A | VTT extraction from email |
| **whisper-health** | Scheduled | TBD | N/A | Whisper service health check |

### 🔍 **Monitoring Services**

| Service | Type | Schedule | Purpose |
|---------|------|----------|---------|
| **health-monitor** | Scheduled | TBD | System health monitoring |
| **health_monitor** | Scheduled | TBD | Duplicate? (needs investigation) |
| **sre-health-monitor** | Scheduled | TBD | SRE-specific health checks |
| **auto-capture** | Scheduled | TBD | Automatic data capture |
| **confluence-sync** | Scheduled | TBD | Confluence integration |

---

## Management Commands

### Check Service Status
```bash
# List all Maia services
launchctl list | grep -i maia

# Check specific service
launchctl list com.maia.system-state-etl-backup

# View service logs
tail -f ~/.maia/logs/etl_daily_backup.log
```

### Load/Unload Services
```bash
# Load service
launchctl load ~/Library/LaunchAgents/com.maia.system-state-etl-backup.plist

# Unload service
launchctl unload ~/Library/LaunchAgents/com.maia.system-state-etl-backup.plist

# Reload after plist changes
launchctl unload ~/Library/LaunchAgents/com.maia.SERVICE.plist
launchctl load ~/Library/LaunchAgents/com.maia.SERVICE.plist
```

### Health Monitoring
```bash
# Comprehensive LaunchAgent health check
python3 claude/tools/sre/launchagent_health_monitor.py --dashboard

# Check specific service
python3 claude/tools/sre/launchagent_health_monitor.py --service com.maia.system-state-etl-backup

# List all services with status
python3 claude/tools/sre/launchagent_health_monitor.py --list
```

---

## LaunchAgent Best Practices

### Continuous Services (KeepAlive: true)
- Use for: Long-running processes (servers, watchers, monitors)
- Example: security-orchestrator, whisper-server
- Auto-restart: Yes (ThrottleInterval for crash recovery)

### Scheduled Services (StartCalendarInterval)
- Use for: Periodic tasks (daily backups, weekly reviews)
- Example: system-state-etl-backup (daily 2 AM)
- Auto-restart: No (runs at scheduled time only)

### Logging Best Practices
- StandardOutPath: `~/.maia/logs/{service}_stdout.log`
- StandardErrorPath: `~/.maia/logs/{service}_error.log`
- Rotate logs: Use system log rotation or manual cleanup

### Environment Variables
Always include PATH:
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/Developer/CommandLineTools/usr/bin</string>
</dict>
```

---

## Migration from Cron (DEPRECATED)

**Historical Note**: Maia previously used cron for automation (documented in `automation_schedule.md`).

**Why migrated to LaunchAgents** (Phase 192+):
- ✅ Better macOS integration (native system service)
- ✅ Automatic restart on crash (KeepAlive support)
- ✅ Better logging and monitoring
- ✅ No crontab access required
- ✅ More reliable scheduling

**Status**: All cron jobs migrated to LaunchAgents. No active cron jobs exist.

---

## Troubleshooting

### Service Not Running
```bash
# Check if service is loaded
launchctl list | grep com.maia.SERVICE

# Check logs for errors
tail -50 ~/.maia/logs/SERVICE_error.log

# Reload service
launchctl unload ~/Library/LaunchAgents/com.maia.SERVICE.plist
launchctl load ~/Library/LaunchAgents/com.maia.SERVICE.plist
```

### Service Keeps Crashing
```bash
# Check crash logs
tail -100 ~/.maia/logs/SERVICE_error.log

# Increase ThrottleInterval (in plist)
<key>ThrottleInterval</key>
<integer>60</integer>  <!-- Wait 60s before restart -->

# Verify ProgramArguments paths exist
ls -la /path/to/script.py
```

### Scheduled Service Not Running
```bash
# Verify schedule in plist
cat ~/Library/LaunchAgents/com.maia.SERVICE.plist | grep -A 5 StartCalendarInterval

# Check if RunAtLoad is set (runs at boot if true)
cat ~/Library/LaunchAgents/com.maia.SERVICE.plist | grep RunAtLoad

# Force run now (for testing)
launchctl start com.maia.SERVICE
```

---

## Audit Status (TODO)

**Action Items**:
1. ⏸️ **Verify all scheduled services** - Determine which are actually needed vs obsolete
2. ⏸️ **Consolidate health monitors** - Investigate health-monitor vs health_monitor duplication
3. ⏸️ **Document service schedules** - Fill in TBD schedule times from plist files
4. ⏸️ **Test service restarts** - Validate all services start successfully after system reboot
5. ⏸️ **Add service monitoring** - Create daily LaunchAgent health dashboard automation

---

**Version**: 1.0
**Status**: Active - Replaces deprecated automation_schedule.md
**Next Review**: Phase 195 (comprehensive service audit)
