# Dashboard Rebuild Plan

**Created:** 2026-01-09
**Status:** In Progress - Paused for reboot
**Context ID:** 55374

---

## Current State

### Data Available (PostgreSQL - servicedesk schema)
| Table | Records | Notes |
|-------|---------|-------|
| tickets | 188,452 | 10,653 open / 177,798 closed |
| timesheets | 850,727 | 615,673 orphaned (72%) |
| comments | 317,601 | 9,591 orphaned |
| user_lookup | ~350 | Username translation |

### Key Schema Fields
- `"TKT-Team"` - Team responsible (NOT TKT-Category!)
- `"TKT-Status"` - Open/Closed/Incident Resolved/etc
- `"TKT-Category"` - Ticket type (Alert, Incident, etc)
- `"TKT-Assigned To User"` - Full name or ' PendingAssignment'
- `"TKT-Created Time"` / `"TKT-Modified Time"` - Timestamps

### Engineering Team (from user_preferences.json)
- Cloud - Infrastructure
- Cloud - Security  
- Cloud - L3 Escalation

Team members: Trevor Harte, Llewellyn Booth, Dion Jewell, Michael Villaflor, 
Olli Ojala, Abdallah Ziadeh, Alex Olver, Josh James, Taylor Barkle, 
Steve Daalmeyer, Daniel Dignadice

---

## New Panels Added (Operations Dashboard)

| ID | Panel | Status | Notes |
|----|-------|--------|-------|
| 9 | SLA Risk Indicator | CHECK | Safe/Warning/Critical buckets |
| 10 | Open Ticket Age Distribution | CHECK | Bar chart by age bucket |
| 11 | Resolution Time Distribution | CHECK | Bar chart by resolution time |
| 12 | Recurring Alert Patterns | CHECK | Table with grouped patterns |
| 13 | Team Queue Capacity Status | CHECK | Table with unassigned % |
| 14 | Data Quality: Orphaned Records | CHECK | Stat showing orphan count |

---

## Old Panels to Review/Rebuild

Many original panels may have stale queries or reference outdated team structures.

**Recommended approach:**
1. Audit each existing panel against current schema
2. Update team filter to include all relevant teams (not just Cloud teams)
3. Verify queries return data with current data set
4. Remove panels that no longer apply

---

## Key Insights from Analysis

### Critical Issues
1. **Alert Fatigue**: 94% of Orro Cloud tickets are alerts
   - Azure memory (2,335 occurrences) - threshold too low (50%)
   - whephdc1 VM (2,018 occurrences) - single VM creating noise
   
2. **Assignment Bottleneck**: Cloud Infrastructure 78.8% unassigned
   - 201 tickets with no owner
   
3. **Resolution Time**: 41.6% take >7 days
   - Only 12.5% resolved in <1 hour

4. **Queue Age**: 52% of open tickets are >30 days old

### Top Alert Patterns (for root cause)
```sql
SELECT 
  CASE 
    WHEN "TKT-Title" ILIKE '%azure%memory%' THEN 'Azure Memory'
    WHEN "TKT-Title" ILIKE '%cusf%network%' THEN 'CUSF Network'
    WHEN "TKT-Title" ILIKE '%whephdc1%' THEN 'whephdc1 VM'
    WHEN "TKT-Title" ILIKE '%disk%' THEN 'Disk Alerts'
    ELSE 'Other'
  END as pattern, COUNT(*)
FROM servicedesk.tickets
WHERE "TKT-Category" = 'Alert'
GROUP BY 1 ORDER BY 2 DESC;
```

---

## Resume Instructions

1. Run `/init` to reload UFC + SRE agent
2. Read this file: `claude/infrastructure/servicedesk-dashboard/DASHBOARD_REBUILD_PLAN.md`
3. Verify Grafana running: `curl http://localhost:3000/api/health`
4. Verify PostgreSQL: `docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT COUNT(*) FROM servicedesk.tickets"`
5. Continue with panel audit/rebuild

---

## Grafana Access
- URL: http://localhost:3000
- User: admin / admin
- Datasource UID: P6BECECF7273D15EE

## Docker Status
```bash
docker ps --filter "name=servicedesk"
# Should show: servicedesk-postgres, servicedesk-grafana
```
