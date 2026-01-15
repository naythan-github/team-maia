# Disaster Recovery Backup System Hardening Project

**Project ID**: Phase 134
**Status**: In Progress
**Priority**: CRITICAL
**Created**: 2025-10-20
**SRE Owner**: SRE Principal Engineer Agent

---

## Executive Summary

**Problem**: Maia's disaster recovery backup system has critical reliability gaps:
- Broken LaunchAgent configuration (5 days without backups)
- No monitoring/alerting on backup failures
- No automated validation or restore testing
- Manual retention policy enforcement

**Impact**:
- Current RPO: 5 days (target: 24 hours) = **80% SLA violation**
- Silent failure risk = undetected data loss potential
- No validation = corrupted backups could go undetected

**Solution**: SRE-harden the backup system with automated monitoring, validation, and self-healing capabilities.

**Expected Outcomes**:
- RPO restored to <24 hours (100% SLA compliance)
- 100% backup success rate with automated alerting
- Automated restore testing every 7 days
- Zero-touch retention management

---

## Current State Assessment

### Backup System Components

**Working ✅**:
- `disaster_recovery_system.py` - Full backup implementation (883 lines)
- OneDrive sync integration (auto-detection, chunking)
- Encrypted credentials vault (AES-256-CBC)
- Self-contained restoration script generation
- Large database chunking (50MB chunks)
- 8-component backup coverage (code, databases, LaunchAgents, dependencies, shell configs, secrets)

**Broken ❌**:
- LaunchAgent configuration (syntax error in ProgramArguments)
- Automated daily execution (hasn't run since Oct 15)
- Backup health monitoring (no alerts)
- Retention pruning automation (manual only)
- Restore validation (no testing)

### Evidence

**Last Successful Backup**: Oct 15 03:00 (5 days ago)
```
Backup ID: full_20251015_030001
Location: OneDrive-YOUR_ORG/MaiaBackups/full_20251015_030001
Size: 1.39 GB (187 MB code + 811 KB small DBs + 1.2 GB servicedesk_tickets.db)
Components: 38 small DBs, 1 large DB (25 chunks), 23 LaunchAgents, credentials vault
Status: ✅ Complete (manual execution)
```

**Broken LaunchAgent**:
```xml
<!-- CURRENT (BROKEN) -->
<string>python3 /Users/YOUR_USERNAME/git/maia/claude/tools/sre/get_vault_password.sh)"</string>

Issues:
1. Unmatched closing parenthesis )"
2. Running .sh with python3 (wrong interpreter)
3. File doesn't exist (get_vault_password.sh)
4. No error logging/alerting
```

**Service Status**:
```bash
$ launchctl list | grep disaster-recovery
-	0	com.maia.disaster-recovery
# Exit code 0 = loaded but NOT executing
```

---

## SRE Reliability Metrics

| Metric | Current | Target | Gap | Priority |
|--------|---------|--------|-----|----------|
| **RPO** (Recovery Point) | 5 days | 24 hours | -80% | P0 |
| **Backup Success Rate** | 0% (auto) | 100% | -100% | P0 |
| **MTTD** (Mean Time to Detect) | Unknown | <15 min | N/A | P0 |
| **Backup Validation** | 0% | 100% | -100% | P1 |
| **Restore Testing** | Never | Weekly | N/A | P1 |
| **Retention Compliance** | Manual | Automated | N/A | P2 |
| **Alerting Coverage** | 0% | 100% | -100% | P0 |
| **OneDrive Sync** | 100% | 100% | ✅ | - |

**Overall SLA Compliance**: **20%** (2/10 passing)

---

## Project Phases

### **Phase 1: Emergency Repair (P0 - Today)** ⚠️ CRITICAL

**Goal**: Restore automated daily backups to 100% success rate

**Deliverables**:
1. Fixed LaunchAgent configuration
   - Correct vault password retrieval (macOS Keychain)
   - Proper error handling and logging
   - Validated syntax
2. Keychain integration for vault password
3. Manual test execution (verify backup completes)
4. LaunchAgent reload and verification
5. Next-run confirmation (tonight 3 AM)

**Success Criteria**:
- ✅ LaunchAgent loads without errors
- ✅ Manual backup execution succeeds
- ✅ Tomorrow's automated backup completes
- ✅ Logs show successful execution

**Time Estimate**: 1-2 hours

---

### **Phase 2: Monitoring & Alerting (P0 - Today/Tomorrow)** 🚨

**Goal**: Zero silent failures through comprehensive monitoring

**Deliverables**:
1. Backup health monitor integration
   - Add backup status check to `automated_health_monitor.py`
   - Check last backup age (<36 hours = healthy, >36 hours = alert)
   - Verify backup integrity (manifest exists, components present)
2. Alert integration
   - Email alerts on backup failure
   - Slack/PagerDuty integration (if configured)
   - Dashboard widget showing backup health
3. Enhanced logging
   - Structured logging with severity levels
   - Backup duration tracking
   - Component-level success/failure reporting

**Success Criteria**:
- ✅ Health monitor detects backup age >36 hours
- ✅ Alert fires on backup failure within 15 minutes
- ✅ Dashboard shows real-time backup status
- ✅ Logs include full execution trace

**Time Estimate**: 2-3 hours

---

### **Phase 3: Automated Validation (P1 - This Week)** 🧪

**Goal**: Ensure backups are restorable before disaster strikes

**Deliverables**:
1. Backup validation script
   - SHA256 verification of all components
   - Manifest completeness check
   - Database integrity validation (SQLite PRAGMA integrity_check)
   - Chunk reassembly verification
2. Automated restore testing
   - Weekly restore test to temporary directory
   - Validate code extraction
   - Validate database restoration
   - Validate LaunchAgent path updates
3. Validation reporting
   - Pass/fail status per backup
   - Integration with health dashboard
   - Alert on validation failure

**Success Criteria**:
- ✅ All backups validated within 10 minutes of creation
- ✅ Restore test completes successfully every 7 days
- ✅ Corrupted backups detected immediately
- ✅ Validation failures trigger alerts

**Time Estimate**: 3-4 hours

---

### **Phase 4: Automated Retention (P2 - This Week)** 🗂️

**Goal**: Zero-touch retention policy enforcement

**Deliverables**:
1. Retention policy automation
   - Schedule daily pruning at 4 AM (after backup)
   - Policy: 7 daily, 4 weekly, 12 monthly
   - Add to LaunchAgent or cron
2. OneDrive space monitoring
   - Track MaiaBackups directory size
   - Alert if >80% of quota (if available)
   - Suggest manual cleanup if policy insufficient
3. Pruning reporting
   - Log deleted backups with reasoning
   - Dashboard showing retention compliance
   - Historical trend tracking

**Success Criteria**:
- ✅ Pruning runs automatically after each backup
- ✅ Retention policy enforced correctly (7/4/12)
- ✅ Old backups removed within 24 hours of expiry
- ✅ Space usage trends visible in dashboard

**Time Estimate**: 2-3 hours

---

### **Phase 5: Advanced Reliability (P2 - Next Sprint)** 🎯

**Goal**: Production-grade backup system with self-healing

**Deliverables**:
1. Backup performance tracking
   - Duration per component
   - OneDrive sync time
   - Compression ratio metrics
2. Self-healing capabilities
   - Automatic retry on transient failures (3 attempts)
   - Circuit breaker for repeated failures
   - Graceful degradation (skip optional components)
3. Disaster recovery runbooks
   - Step-by-step restoration guide
   - Common failure scenarios
   - Recovery time estimates
4. Backup versioning strategy
   - Track Maia version in manifest
   - Compatibility matrix (backup version → Maia version)
   - Migration guides for breaking changes

**Success Criteria**:
- ✅ Backup duration baseline established
- ✅ 95% of transient failures auto-recover
- ✅ Runbook tested and validated
- ✅ Version compatibility tracked

**Time Estimate**: 4-6 hours

---

## Implementation Plan

### Phase 1 Implementation Details

#### 1.1 Keychain Setup for Vault Password

**Create keychain entry**:
```bash
# Store vault password securely
security add-generic-password \
  -s "maia_vault_password" \
  -a "$(whoami)" \
  -w "YOUR_VAULT_PASSWORD_HERE" \
  -U

# Test retrieval
security find-generic-password -w -s "maia_vault_password" -a "$(whoami)"
```

#### 1.2 Fixed LaunchAgent Configuration

**File**: `~/Library/LaunchAgents/com.maia.disaster-recovery.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maia.disaster-recovery</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /Users/YOUR_USERNAME/git/maia &amp;&amp; python3 claude/tools/sre/disaster_recovery_system.py backup --vault-password $(security find-generic-password -w -s "maia_vault_password" -a "$(whoami)")</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>/Users/YOUR_USERNAME/git/maia</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/git/maia/claude/logs/production/disaster_recovery.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/git/maia/claude/logs/production/disaster_recovery.error.log</string>

    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/git/maia</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

#### 1.3 Manual Test & Reload

```bash
# Unload existing (broken) agent
launchctl unload ~/Library/LaunchAgents/com.maia.disaster-recovery.plist

# Test manual execution
cd /Users/YOUR_USERNAME/git/maia
python3 claude/tools/sre/disaster_recovery_system.py backup \
  --vault-password $(security find-generic-password -w -s "maia_vault_password" -a "$(whoami)")

# If successful, reload agent
launchctl load ~/Library/LaunchAgents/com.maia.disaster-recovery.plist

# Verify loaded
launchctl list | grep disaster-recovery

# Check next run time
launchctl print user/$(id -u)/com.maia.disaster-recovery | grep "next activation"
```

---

### Phase 2 Implementation Details

#### 2.1 Backup Health Monitor Integration

**File**: `claude/tools/sre/automated_health_monitor.py`

**Add backup health check**:
```python
def check_backup_health(self) -> Dict[str, Any]:
    """Check disaster recovery backup system health"""
    onedrive_path = self._detect_onedrive_path()
    backup_dir = Path(onedrive_path) / "MaiaBackups"

    if not backup_dir.exists():
        return {
            'status': 'critical',
            'message': 'Backup directory not found',
            'last_backup': None,
            'age_hours': None
        }

    # Find latest backup
    manifests = list(backup_dir.glob("*/backup_manifest.json"))
    if not manifests:
        return {
            'status': 'critical',
            'message': 'No backups found',
            'last_backup': None,
            'age_hours': None
        }

    latest_manifest = max(manifests, key=lambda p: p.stat().st_mtime)
    with open(latest_manifest) as f:
        manifest = json.load(f)

    created_at = datetime.fromisoformat(manifest['created_at'])
    age_hours = (datetime.now() - created_at).total_seconds() / 3600

    # Determine status
    if age_hours > 36:
        status = 'critical'
        message = f'Backup is {age_hours:.1f} hours old (target: <36h)'
    elif age_hours > 25:
        status = 'warning'
        message = f'Backup is {age_hours:.1f} hours old (approaching threshold)'
    else:
        status = 'healthy'
        message = f'Backup is {age_hours:.1f} hours old'

    return {
        'status': status,
        'message': message,
        'last_backup': manifest['backup_id'],
        'age_hours': age_hours,
        'size_gb': self._calculate_backup_size_gb(latest_manifest.parent),
        'components': len(manifest.get('components', {})),
        'onedrive_synced': manifest.get('onedrive_sync_verified', False)
    }
```

#### 2.2 Alert Integration

**Add to health monitor**:
```python
def send_backup_alert(self, health_status: Dict):
    """Send alert if backup is unhealthy"""
    if health_status['status'] in ['critical', 'warning']:
        subject = f"🚨 Maia Backup {health_status['status'].upper()}"
        body = f"""
Disaster Recovery Backup Alert

Status: {health_status['status'].upper()}
Message: {health_status['message']}
Last Backup: {health_status['last_backup']}
Age: {health_status['age_hours']:.1f} hours

Action Required:
1. Check LaunchAgent: launchctl list | grep disaster-recovery
2. Review logs: tail -50 ~/git/maia/claude/logs/production/disaster_recovery.log
3. Manual backup: cd ~/git/maia && python3 claude/tools/sre/disaster_recovery_system.py backup

Dashboard: http://localhost:8065/backup-health
        """

        self.send_email_alert(subject, body)
        self.send_slack_alert(subject, body)  # If configured
```

---

### Phase 3 Implementation Details

#### 3.1 Backup Validation Script

**New file**: `claude/tools/sre/backup_validator.py`

**Key validations**:
1. Manifest exists and is valid JSON
2. All component files exist
3. SHA256 checksums match
4. Large database chunks reassemble correctly
5. SQLite databases pass integrity check
6. Tar archives extract without errors

#### 3.2 Automated Restore Testing

**New file**: `claude/tools/sre/backup_restore_tester.py`

**Test workflow**:
1. Create temporary test directory
2. Run restore_maia.sh in test mode
3. Verify code extraction completes
4. Verify databases are readable
5. Verify LaunchAgent paths updated
6. Clean up test directory
7. Report pass/fail with detailed logs

**Schedule**: Weekly via LaunchAgent (Sunday 2 AM)

---

### Phase 4 Implementation Details

#### 4.1 Retention Policy Automation

**New LaunchAgent**: `com.maia.backup-pruning.plist`

**Schedule**: Daily at 4 AM (after backup at 3 AM)

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>4</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

**Command**:
```bash
python3 /Users/YOUR_USERNAME/git/maia/claude/tools/sre/disaster_recovery_system.py prune
```

---

## Testing Strategy

### Phase 1 Testing
- [ ] Manual backup execution succeeds
- [ ] Keychain retrieval works in LaunchAgent context
- [ ] LaunchAgent loads without errors
- [ ] Logs show successful execution path
- [ ] Next scheduled run confirmed

### Phase 2 Testing
- [ ] Health check detects old backups (>36h)
- [ ] Alert fires within 15 minutes of detection
- [ ] Dashboard shows accurate backup status
- [ ] Email/Slack notifications received

### Phase 3 Testing
- [ ] Validator detects corrupted components
- [ ] Restore test completes in <30 minutes
- [ ] Restored Maia is functional
- [ ] Validation failures trigger alerts

### Phase 4 Testing
- [ ] Pruning removes correct backups
- [ ] Retention policy enforced (7/4/12)
- [ ] No accidental deletion of recent backups
- [ ] Space usage tracked correctly

---

## Rollback Plan

If backup system changes cause issues:

1. **Revert LaunchAgent** to manual backup approach:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.maia.disaster-recovery.plist
   # Use manual backup until fixed
   ```

2. **Emergency manual backup**:
   ```bash
   cd ~/git/maia
   python3 claude/tools/sre/disaster_recovery_system.py backup
   ```

3. **Disable monitoring** if generating false positives:
   ```python
   # Comment out backup health check in automated_health_monitor.py
   ```

---

## Success Metrics

**Before Hardening**:
- RPO: 5 days
- Backup success rate: 0% (automated)
- MTTD: Unknown
- Alerting: 0%
- Validation: 0%

**After Phase 1**:
- RPO: <24 hours ✅
- Backup success rate: 100% (target)
- MTTD: Still unknown
- Alerting: 0%
- Validation: 0%

**After Phase 2**:
- RPO: <24 hours ✅
- Backup success rate: 100% ✅
- MTTD: <15 minutes ✅
- Alerting: 100% ✅
- Validation: 0%

**After Phase 3**:
- RPO: <24 hours ✅
- Backup success rate: 100% ✅
- MTTD: <15 minutes ✅
- Alerting: 100% ✅
- Validation: 100% ✅

**After Phase 4**:
- All metrics at 100% ✅
- Retention: Automated ✅
- Zero-touch operations ✅

---

## Documentation Updates Required

1. **SYSTEM_STATE.md** - Phase 134 entry
2. **capability_index.md** - Backup hardening tools
3. **available.md** - New tools (validator, restore tester)
4. **CLAUDE.md** - No changes (backup process transparent to users)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Keychain access fails in LaunchAgent | Low | High | Test in LaunchAgent context before deployment |
| Backup validation false positives | Medium | Medium | Tune thresholds, manual review initially |
| Restore test corrupts production data | Low | Critical | Use isolated test directory, read-only operations |
| Alert fatigue from frequent notifications | Medium | Low | Smart alerting (dedupe, snooze, escalation) |
| OneDrive sync delays cause false alerts | Medium | Medium | Increase threshold to 36 hours (1.5x schedule) |

---

## Next Steps

**Immediate (Phase 1)**:
1. ✅ Create project plan (DONE)
2. Set up keychain password
3. Fix LaunchAgent configuration
4. Test manual execution
5. Reload and verify

**This Week (Phase 2-4)**:
6. Add monitoring integration
7. Implement validation
8. Automate retention
9. End-to-end testing

**Documentation**:
10. Update SYSTEM_STATE.md
11. Update capability_index.md
12. Update available.md

---

**Project Owner**: SRE Principal Engineer Agent
**Review Schedule**: Daily during Phase 1, weekly thereafter
**Escalation Path**: User notification if automated recovery fails
