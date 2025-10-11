# Schedule-Aware Health Check - Project Plan

**Date**: 2025-10-10
**Phase**: 103 Week 3 Enhancement
**Status**: Planning Complete, Ready for Implementation

---

## Problem Statement

**Current Issue**: LaunchAgent health monitor treats all services equally:
- **Continuous services** (whisper-server, unified-dashboard) should always have a PID
- **Scheduled services** (email-rag-indexer, daily-briefing) should NOT have a PID between runs
- **Current logic**: `availability = running / total` where running = has PID
- **Result**: 5 continuous services running + 8 scheduled services idle = 29.4% availability ❌

**This is misleading**: Scheduled services in IDLE state are healthy, not unavailable.

---

## Solution: Schedule-Aware Health Check

**Approach**: Health check determines service type from plist, then applies appropriate health criteria:

### Service Type Detection
- **CONTINUOUS**: `KeepAlive=true` → expect PID always
- **INTERVAL**: `StartInterval=3600` → expect run every N seconds
- **CALENDAR**: `StartCalendarInterval` → expect run at specific time (daily at 7am)
- **TRIGGER**: `WatchPaths` → expect run when files change
- **ONE_SHOT**: `RunAtLoad` only → expect run once after load

### Health Calculation by Type

**CONTINUOUS**:
```
HEALTHY: has PID
FAILED: no PID
```

**INTERVAL**:
```
Get last_run_time from log file mtime
time_since_run = now - last_run_time
expected_interval = StartInterval

HEALTHY: time_since_run < interval * 1.5 (grace period)
DEGRADED: time_since_run < interval * 3 (missed 1-2 runs)
FAILED: time_since_run >= interval * 3 (missed 3+ runs)
```

**CALENDAR**:
```
Parse StartCalendarInterval (Hour=7, Minute=0)
Calculate next_expected_run
time_since_expected = now - next_expected_run

HEALTHY: time_since_expected < 15 minutes (on schedule or hasn't missed)
DEGRADED: time_since_expected < 2 hours (late but might catch up)
FAILED: time_since_expected >= 2 hours (missed scheduled run)
```

**TRIGGER / ONE_SHOT**:
```
Check launchctl "runs" count and "last exit code"

HEALTHY: runs > 0 and last_exit_code = 0
UNKNOWN: never triggered yet or no info
FAILED: runs > 0 and last_exit_code != 0
```

### Metrics Separation

**Current (broken)**:
- SLI: `running / total` = 29.4%
- Target: 99.9%
- Gap: 70.5% below target ❌

**Schedule-Aware (accurate)**:
- **Continuous SLI**: `running_continuous / total_continuous` = 5/5 = 100% ✅
- **Scheduled SLI**: `on_schedule / total_scheduled` = 8/8 = 100% ✅
- **Overall Health**: Both categories at target
- **Target**: Continuous 99.9%, Scheduled 95%

---

## Implementation Plan

### Phase 1: Add plist Parser for Schedule Extraction (30 min)

**Goal**: Extract schedule configuration from LaunchAgent plist files

**Implementation**:
```python
import plistlib
from pathlib import Path

class ServiceScheduleParser:
    def parse_plist(self, plist_path: Path) -> Dict:
        with open(plist_path, 'rb') as f:
            plist_data = plistlib.load(f)

        schedule_info = {
            'service_name': plist_data.get('Label'),
            'service_type': self._determine_type(plist_data),
            'schedule_config': {}
        }

        if 'KeepAlive' in plist_data:
            schedule_info['service_type'] = 'CONTINUOUS'
            schedule_info['schedule_config']['keep_alive'] = plist_data['KeepAlive']

        if 'StartInterval' in plist_data:
            schedule_info['service_type'] = 'INTERVAL'
            schedule_info['schedule_config']['interval_seconds'] = plist_data['StartInterval']

        if 'StartCalendarInterval' in plist_data:
            schedule_info['service_type'] = 'CALENDAR'
            schedule_info['schedule_config']['calendar'] = plist_data['StartCalendarInterval']

        if 'WatchPaths' in plist_data:
            schedule_info['service_type'] = 'TRIGGER'
            schedule_info['schedule_config']['watch_paths'] = plist_data['WatchPaths']

        return schedule_info
```

**Files Modified**: `claude/tools/sre/launchagent_health_monitor.py`

**Testing**:
- Parse all 17 Maia LaunchAgent plists
- Verify service type detection accuracy
- Confirm schedule extraction (intervals, calendar times)

---

### Phase 2: Add Log File Mtime Checker (20 min)

**Goal**: Determine when service last ran by checking log file modification time

**Implementation**:
```python
from datetime import datetime
import os

class LogFileChecker:
    def get_last_run_time(self, log_path: Path) -> Optional[datetime]:
        if not log_path.exists():
            return None

        try:
            mtime = os.path.getmtime(log_path)
            return datetime.fromtimestamp(mtime)
        except (OSError, ValueError):
            return None

    def get_time_since_last_run(self, log_path: Path) -> Optional[float]:
        last_run = self.get_last_run_time(log_path)
        if not last_run:
            return None

        return (datetime.now() - last_run).total_seconds()
```

**Files Modified**: `claude/tools/sre/launchagent_health_monitor.py`

**Testing**:
- Check log file locations for all services
- Verify mtime extraction
- Handle missing log files gracefully

---

### Phase 3: Implement Schedule-Aware Health Logic (60 min)

**Goal**: Calculate health based on service type and schedule compliance

**Implementation**:
```python
class ScheduleAwareHealthChecker:
    def calculate_health(self, service_name: str, schedule_info: Dict,
                        launchctl_data: Dict, log_path: Path) -> Dict:
        service_type = schedule_info['service_type']
        has_pid = launchctl_data.get('pid') is not None
        last_exit_code = launchctl_data.get('last_exit_code')
        runs_count = launchctl_data.get('runs', 0)

        if service_type == 'CONTINUOUS':
            health = 'HEALTHY' if has_pid else 'FAILED'
            reason = 'Has PID' if has_pid else 'No PID (should be continuous)'

        elif service_type == 'INTERVAL':
            interval = schedule_info['schedule_config']['interval_seconds']
            time_since_run = self.log_checker.get_time_since_last_run(log_path)

            if time_since_run is None:
                health = 'UNKNOWN'
                reason = 'No log file found'
            elif time_since_run < interval * 1.5:
                health = 'HEALTHY'
                reason = f'Ran {time_since_run//60:.0f}m ago (expected every {interval//60}m)'
            elif time_since_run < interval * 3:
                health = 'DEGRADED'
                reason = f'Missed 1-2 runs ({time_since_run//60:.0f}m since last run)'
            else:
                health = 'FAILED'
                reason = f'Missed 3+ runs ({time_since_run//60:.0f}m since last run)'

        elif service_type == 'CALENDAR':
            calendar_config = schedule_info['schedule_config']['calendar']
            next_run = self._calculate_next_run(calendar_config)
            time_since_expected = (datetime.now() - next_run).total_seconds()

            if time_since_expected < 0:
                health = 'HEALTHY'
                reason = 'Not yet scheduled to run'
            elif time_since_expected < 900:  # 15 minutes
                health = 'HEALTHY'
                reason = 'On schedule'
            elif time_since_expected < 7200:  # 2 hours
                health = 'DEGRADED'
                reason = f'Late by {time_since_expected//60:.0f}m'
            else:
                health = 'FAILED'
                reason = f'Missed scheduled run by {time_since_expected//3600:.1f}h'

        elif service_type in ['TRIGGER', 'ONE_SHOT']:
            if runs_count > 0 and last_exit_code == 0:
                health = 'HEALTHY'
                reason = 'Ran successfully'
            elif runs_count > 0 and last_exit_code != 0:
                health = 'FAILED'
                reason = f'Last run failed (exit {last_exit_code})'
            else:
                health = 'UNKNOWN'
                reason = 'Never triggered/run'

        return {
            'health': health,
            'reason': reason,
            'service_type': service_type
        }
```

**Files Modified**: `claude/tools/sre/launchagent_health_monitor.py`

**Testing**:
- Test each service type calculation
- Verify grace periods work correctly
- Test edge cases (brand new service, missing logs)

---

### Phase 4: Update Metrics (Continuous vs Scheduled SLIs) (30 min)

**Goal**: Separate availability metrics by service type

**Implementation**:
```python
def generate_health_report(self) -> Dict:
    statuses = self.get_all_services_status()

    # Separate by service type
    continuous = [s for s in statuses if s['service_type'] == 'CONTINUOUS']
    scheduled = [s for s in statuses if s['service_type'] in ['INTERVAL', 'CALENDAR']]
    other = [s for s in statuses if s['service_type'] in ['TRIGGER', 'ONE_SHOT']]

    # Calculate continuous availability (traditional SLI)
    continuous_running = len([s for s in continuous if s['health'] == 'HEALTHY'])
    continuous_availability = (continuous_running / len(continuous) * 100) if continuous else 0

    # Calculate scheduled health (on-schedule percentage)
    scheduled_healthy = len([s for s in scheduled if s['health'] == 'HEALTHY'])
    scheduled_health = (scheduled_healthy / len(scheduled) * 100) if scheduled else 0

    report = {
        'summary': {
            'continuous_services': {
                'total': len(continuous),
                'healthy': continuous_running,
                'availability_pct': round(continuous_availability, 1),
                'slo_target': 99.9,
                'slo_met': continuous_availability >= 99.9
            },
            'scheduled_services': {
                'total': len(scheduled),
                'on_schedule': scheduled_healthy,
                'health_pct': round(scheduled_health, 1),
                'slo_target': 95.0,
                'slo_met': scheduled_health >= 95.0
            },
            'other_services': {
                'total': len(other)
            }
        },
        'services': statuses
    }

    return report
```

**Files Modified**: `claude/tools/sre/launchagent_health_monitor.py`

**Testing**:
- Verify metric separation
- Confirm SLO targets are checked correctly
- Test dashboard output formatting

---

### Phase 5: Grace Periods & Edge Cases (optional, future enhancement)

**Not implementing initially**, but documented for future:

**System Sleep Detection**:
```python
# Check pmset logs for sleep/wake events
# Adjust grace periods if system was asleep during expected run
```

**First Run Grace Period**:
```python
# Check plist creation time
# If service age < interval, mark PENDING not FAILED
```

**Complex Calendar Schedules**:
```python
# Support multiple calendar intervals
# Support day-of-week restrictions
```

---

## Testing Plan

### Unit Tests
1. **Service Type Detection**: Parse 17 LaunchAgent plists, verify correct type assignment
2. **Log File mtime**: Create test log files with known timestamps, verify calculation
3. **Health Logic**: Mock scenarios for each service type, verify health status
4. **Metrics Calculation**: Verify continuous vs scheduled separation

### Integration Tests
1. **Current System**: Run against live services, verify no breakage
2. **Scheduled Service**: Wait for email-rag-indexer to run, verify HEALTHY status
3. **Missed Run**: Manually stop scheduled service, verify DEGRADED → FAILED progression
4. **Continuous Service**: Verify whisper-server shows HEALTHY with PID

### Acceptance Criteria
- ✅ Continuous services: 100% availability (5/5 running)
- ✅ Scheduled services: 100% on-schedule (8/8 running on time)
- ✅ Overall health: HEALTHY (no degraded/failed services)
- ✅ Dashboard shows separate metrics for continuous vs scheduled
- ✅ No false positives (services incorrectly marked unhealthy)

---

## Constraints & Mitigations

### Constraint 1: Log File Dependency
**Risk**: Service doesn't write logs or writes elsewhere
**Mitigation**: Fallback to launchctl "runs" count + "last exit code"

### Constraint 2: Clock Skew / System Sleep
**Risk**: False positives when system sleeps
**Mitigation**: Add generous grace periods (1.5x for intervals, 2h for calendar)

### Constraint 3: First Run Detection
**Risk**: New service marked unhealthy before first run
**Mitigation**: Check launchctl "runs" count, if 0 mark PENDING not FAILED

### Constraint 4: Complex Schedules
**Risk**: Hard to calculate next run for complex calendar rules
**Mitigation**: Start with simple schedules (single time), expand later

### Constraint 5: plist Parsing Overhead
**Risk**: Slower health checks
**Mitigation**: Cache plist data, only re-parse on service reload

---

## Expected Outcomes

### Before (Current State)
```
Service Availability: 29.4% (5/17)
SLO Target: 99.9%
Status: 🔴 CRITICAL (70.5% below target)

Continuous: 5 HEALTHY, counted as 5/17 = 29.4%
Scheduled: 8 IDLE, counted as 0/17 = 0% ❌
```

### After (Schedule-Aware)
```
Continuous Services: 100% (5/5)
SLO Target: 99.9%
Status: ✅ HEALTHY (meets target)

Scheduled Services: 100% (8/8 on schedule)
SLO Target: 95%
Status: ✅ HEALTHY (meets target)

Overall: ✅ HEALTHY
```

### Improvements
- ✅ Accurate availability metrics (no false low availability)
- ✅ Early detection of missed scheduled runs
- ✅ Proper SLO tracking by service type
- ✅ Better observability (see WHY service is healthy/unhealthy)

---

## Files Modified

**Primary**:
- `claude/tools/sre/launchagent_health_monitor.py` - Add schedule-aware logic

**Documentation**:
- `claude/context/tools/available.md` - Update SRE Tools section with new capabilities
- `SYSTEM_STATE.md` - Document enhancement when complete

**Testing**:
- Manual testing against live services
- Verification of all 17 LaunchAgent service types

---

## Estimated Effort

- **Phase 1** (plist parser): 30 minutes
- **Phase 2** (log file mtime): 20 minutes
- **Phase 3** (health logic): 60 minutes
- **Phase 4** (metrics update): 30 minutes
- **Testing**: 20 minutes
- **Documentation**: 20 minutes

**Total**: ~3 hours

---

## Success Criteria

1. ✅ All continuous services show correct health (HEALTHY if PID, FAILED if no PID)
2. ✅ All scheduled services show correct health (HEALTHY if ran on schedule)
3. ✅ Metrics separated: Continuous SLI (availability) vs Scheduled SLI (on-schedule %)
4. ✅ Dashboard shows service type and schedule info
5. ✅ No false positives (services incorrectly marked unhealthy)
6. ✅ Detects missed runs within grace period (early warning system)

---

**Status**: Ready for implementation - proceed with Phase 1
