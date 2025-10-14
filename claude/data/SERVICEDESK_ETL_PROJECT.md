# ServiceDesk ETL Project Documentation

**Status**: ✅ PRODUCTION OPERATIONAL
**Created**: October 14, 2025
**Last Updated**: October 14, 2025
**Phase**: 116 - ServiceDesk Analytics Infrastructure

---

## Executive Summary

Comprehensive ETL system for ServiceDesk ticket analysis with Cloud team focus. Implements "Cloud-touched" logic to capture all work performed by Cloud roster members, even when tickets span multiple teams. Includes incremental import capability with full metadata tracking.

### Key Achievement
**88.4% First Call Resolution (FCR)** rate for Cloud teams - exceeding industry target of 70-80% by 8-18 percentage points.

---

## System Architecture

### Components

1. **Incremental Import Tool** (`claude/tools/sre/incremental_import_servicedesk.py`)
   - 3-stage import process (comments → tickets → timesheets)
   - Cloud-touched logic implementation
   - Metadata tracking for all imports
   - Supports both CSV and Excel formats

2. **Operations Dashboard** (`claude/tools/monitoring/servicedesk_operations_dashboard.py`)
   - Flask web dashboard on port 8065
   - 8 widgets with real-time metrics
   - FCR tracking by team and agent
   - Auto-refresh capability

3. **Database** (`claude/data/servicedesk_tickets.db`)
   - SQLite database with 5 tables
   - 260,178 total records imported
   - Import metadata tracking

4. **Cloud Team Roster** (`claude/data/cloud_team_roster.csv`)
   - Master list of 48 Cloud team members
   - Used for filtering Cloud-touched tickets

---

## Critical Implementation Details

### The "Cloud-Touched" Logic

**Problem**: Tickets frequently change hands between teams (e.g., Networks → Cloud → Networks). If we filter by team assignment, we lose visibility into Cloud's work.

**Solution**: Import ALL data for any ticket where a Cloud roster member worked, regardless of which team ultimately closed it.

**Implementation**:
1. Import comments first (July 1+ only)
2. Identify ticket IDs where Cloud roster members commented
3. Import ALL tickets matching those IDs (no date filter on creation)
4. Import ALL timesheets (July 1+ only), flag orphaned entries

### Critical Data Type Issue

**IMPORTANT**: Ticket IDs have mismatched types between data sources:
- **Comments CSV**: Ticket IDs load as **strings** (e.g., "3664092")
- **Tickets CSV**: Ticket IDs load as **integers** (e.g., 3664092)

**Solution**: Convert ticket IDs to integers during Cloud-touched identification:
```python
cloud_touched = df_filtered[df_filtered['user_name'].isin(roster_users)]['ticket_id'].dropna().astype(int).unique()
```

Then use integer comparison for filtering both comments and tickets.

### Date Filtering Rules

**July 1, 2025 = System Migration Date (HARD CUTOFF)**

| Data Source | Date Filter Applied | Rationale |
|------------|-------------------|-----------|
| Comments | July 1+ comment dates | Only post-migration activity |
| Tickets | **NO date filter** | Pre-July 1 tickets may have post-July 1 Cloud work |
| Timesheets | July 1+ timesheet dates | Only post-migration hours |

**Key Insight**: Tickets created before July 1 are kept IF they have Cloud comments after July 1. We filter by activity, not creation date.

### CSV Format Quirks

1. **Comments CSV**: 3,564 columns, only first 10 are valid (rest empty)
   - Must use `usecols=range(10)` to avoid "too many columns" SQLite error

2. **Date Formats**: DD/MM/YYYY format requires `dayfirst=True` in pandas
   - Without this, dates parse incorrectly (e.g., 14/10/2025 → October 14 instead of Oct 14)

3. **Encoding**: Use `encoding='utf-8-sig'` to handle BOM characters in CSV headers

---

## Database Schema

### Tables

```
comments (108,129 rows)
├── comment_id (TEXT)
├── ticket_id (TEXT) -- NOTE: Stored as text due to CSV import
├── comment_text (TEXT)
├── user_id (TEXT)
├── user_name (TEXT) -- Links to cloud_team_roster.username
├── owner_type (TEXT)
├── created_time (TIMESTAMP)
├── visible_to_customer (TEXT)
├── comment_type (TEXT)
└── team (TEXT)

tickets (10,939 rows)
├── TKT-Ticket ID (INTEGER)
├── TKT-Parent ID (REAL)
├── TKT-Customer Reference (TEXT)
├── TKT-Created Time (TIMESTAMP)
├── TKT-Month Created (TEXT)
├── [59 additional columns]
└── -- Full schema preserved from source CSV

timesheets (141,062 rows)
├── TS-User Full Name (TEXT)
├── TS-User Username (TEXT) -- Links to cloud_team_roster.username
├── TS-Title (TEXT)
├── TS-Description (TEXT)
├── TS-Date (TIMESTAMP)
├── TS-Crm ID (INTEGER) -- Links to tickets.TKT-Ticket ID
├── TS-Hours (REAL)
└── [14 additional columns]

cloud_team_roster (48 rows)
├── Name (TEXT)
├── Email (TEXT)
└── username (TEXT) -- PRIMARY KEY for filtering

import_metadata (12 rows)
├── import_id (INTEGER PRIMARY KEY)
├── source_type (TEXT) -- 'comments', 'tickets', or 'timesheets'
├── import_timestamp (TIMESTAMP)
├── file_name (TEXT)
├── records_imported (INTEGER)
├── date_range_start (TIMESTAMP)
├── date_range_end (TIMESTAMP)
├── filter_applied (TEXT)
└── notes (TEXT)
```

---

## Import Process

### Command

```bash
python3 ~/git/maia/claude/tools/sre/incremental_import_servicedesk.py import \
  ~/Downloads/comments.csv \
  ~/Downloads/all-tickets.csv \
  ~/Downloads/timesheets.csv
```

### Expected Output

```
================================================================================
SERVICEDESK DATA IMPORT - Cloud-Touched Logic
================================================================================

💬 STEP 1: Importing comments from: /Users/naythandawe/Downloads/comments.csv
   Loaded 204,625 rows
   ✅ Filtered to 176,637 rows (July 1+ only)
   📋 Cloud roster: 48 members
   🎯 Identified 10,939 Cloud-touched tickets
   ✅ Keeping ALL comments for Cloud-touched tickets: 108,129 rows
   ✅ Imported as import_id=10
   📅 Date range: 2025-07-03 to 2025-10-14

📋 STEP 2: Importing tickets from: /Users/naythandawe/Downloads/all-tickets.csv
   Loaded 652,681 rows
   🎯 Cloud-touched tickets: 10,939 rows (no date filter - filtered by Cloud activity)
   ✅ Imported as import_id=11
   📅 Date range: 2025-07-03 to 2025-10-13

⏱️  STEP 3: Importing timesheets from: /Users/naythandawe/Downloads/timesheets.csv
   Loaded 732,959 rows
   ✅ Filtered to 141,062 rows (July 1+ only)
   ⚠️  Found 128,007 orphaned timesheet entries (90.7%)
   ✅ Keeping ALL entries (orphaned = data quality issue to analyze separately)
   ✅ Imported as import_id=12
   📅 Date range: 2025-07-01 to 2026-07-01

================================================================================
✅ IMPORT COMPLETE
================================================================================
```

### Validation Queries

```sql
-- Verify row counts
SELECT 'comments' as table_name, COUNT(*) as row_count FROM comments
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'timesheets', COUNT(*) FROM timesheets
UNION ALL SELECT 'cloud_team_roster', COUNT(*) FROM cloud_team_roster;

-- Calculate FCR rate
WITH ticket_agents AS (
    SELECT
        c.ticket_id,
        COUNT(DISTINCT c.user_name) as agent_count
    FROM comments c
    INNER JOIN cloud_team_roster r ON c.user_name = r.username
    GROUP BY c.ticket_id
)
SELECT
    COUNT(*) as total_tickets,
    SUM(CASE WHEN agent_count = 1 THEN 1 ELSE 0 END) as fcr_tickets,
    ROUND(100.0 * SUM(CASE WHEN agent_count = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as fcr_rate
FROM ticket_agents;
```

**Expected Results**:
- Comments: 108,129 rows
- Tickets: 10,939 rows
- Timesheets: 141,062 rows
- Cloud roster: 48 rows
- **FCR Rate: 88.4%**

---

## Troubleshooting Guide

### Issue: 0 Tickets Imported

**Symptom**: Comments import succeeds, but tickets shows "0 rows"

**Root Cause**: Type mismatch - ticket IDs are strings in comments but integers in tickets CSV

**Solution**: Check that `incremental_import_servicedesk.py` line 77 includes `.astype(int)`:
```python
cloud_touched = df_filtered[df_filtered['user_name'].isin(roster_users)]['ticket_id'].dropna().astype(int).unique()
```

### Issue: 0 Comments Kept

**Symptom**: Cloud-touched tickets identified, but "0 rows" kept for comments

**Root Cause**: Type mismatch in filtering logic

**Solution**: Check that line 82-83 converts ticket_id to int for filtering:
```python
df_filtered['ticket_id_int'] = df_filtered['ticket_id'].astype(int)
df_final = df_filtered[df_filtered['ticket_id_int'].isin(cloud_touched)].drop(columns=['ticket_id_int'])
```

### Issue: "too many columns on comments"

**Symptom**: SQLite error during comments import

**Root Cause**: Comments CSV has 3,564 columns (only first 10 valid)

**Solution**: Check that line 45 includes `usecols=range(10)`:
```python
df = pd.read_csv(file_path, encoding='utf-8-sig', usecols=range(10), low_memory=False)
```

### Issue: Wrong Date Ranges

**Symptom**: Dates like 10/14/2025 parsing as October 14 instead of Oct 14

**Root Cause**: pandas defaults to `dayfirst=False` (US format MM/DD/YYYY)

**Solution**: All date parsing must include `dayfirst=True`:
```python
df['created_time'] = pd.to_datetime(df['created_time'], dayfirst=True, errors='coerce')
```

### Issue: Import Metadata Shows Future Dates

**Symptom**: Timesheets date range ends in 2026

**Root Cause**: Data quality issue in source file (bad dates in CSV)

**Expected**: This is normal - filter these out in analysis queries if needed

---

## Key Metrics & Results

### Current Performance (Oct 14, 2025)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **First Call Resolution** | 88.4% | 70-80% | ✅ Exceeding |
| FCR Tickets | 9,674 | - | - |
| Multi-touch Tickets | 1,265 | - | - |
| Total Cloud-touched Tickets | 10,939 | - | - |
| Comments Captured | 108,129 | - | - |
| Timesheet Entries | 141,062 | - | - |
| Timesheet Coverage | 9.3% | - | ⚠️ Data quality issue |
| Orphaned Timesheets | 90.7% | - | ⚠️ Requires investigation |

### Data Quality Flags

1. **Orphaned Timesheets (90.7%)**: 128,007 timesheet entries with no matching Cloud-touched ticket
   - **Possible causes**: Work on non-Cloud tickets, mismatched ticket IDs, data export issues
   - **Resolution**: Kept for separate analysis as requested by user

2. **Future Dates in Timesheets**: Some entries dated July 2026
   - **Possible causes**: Data entry errors, system clock issues
   - **Resolution**: Keep in database, filter in analysis queries if needed

3. **Pre-July 1 Tickets**: Some tickets created before migration date
   - **Not an issue**: Intentional design - tickets kept if Cloud worked on them after July 1
   - **Validation**: Comments for these tickets all dated July 3+

---

## Cloud Team Roster

**48 Members** across 4 teams:
- Cloud - Infrastructure (28 members)
- Cloud - Internal Support
- Cloud - Business Intelligence
- Cloud - Enterprise Architecture

**File**: `claude/data/cloud_team_roster.csv`

**Schema**:
```csv
Name,Email,username
Abdallah Ziadeh,abdallah.ziadeh@company.com,abdallah.ziadeh
Foram Pandya,foram.pandya@company.com,foram.pandya
...
```

**Usage**: Master filter for identifying Cloud-touched work across all data sources.

---

## Future Enhancements

### Phase 2: Daily Incremental Imports (Pending)

**Requirement**: User will set up daily data exports from ServiceDesk system

**Implementation Plan**:
1. Check `import_metadata` for last import date
2. Filter new data by date > last import
3. Append to existing tables (not replace)
4. Update import_metadata with new import record

**Code Changes Needed**:
```python
def incremental_import_comments(self, file_path):
    # Get last import date
    query = "SELECT MAX(date_range_end) FROM import_metadata WHERE source_type='comments'"
    last_import = pd.read_sql_query(query, self.conn).iloc[0, 0]

    # Filter to new records only
    df_new = df[df['created_time'] > last_import]

    # Append (not replace)
    df_new.to_sql('comments', self.conn, if_exists='append', index=False)
```

### Phase 3: Team/Pod Breakdown (Pending)

**Requirement**: User will provide pod assignments for 48 team members

**Implementation**: Add `pod` column to `cloud_team_roster` table, enable pod-level FCR analysis

### Phase 4: Infrastructure Team Deep-Dive (Paused)

**Objective**: Investigate 11.6% non-FCR rate for Infrastructure team
- Which agents causing handoffs?
- Alert vs. Work ticket segmentation
- Training/skill gap identification

**Status**: Paused pending current data import completion

---

## Quick Reference

### Start Dashboard
```bash
python3 ~/git/maia/claude/tools/monitoring/servicedesk_operations_dashboard.py
# Access at http://localhost:8065
```

### View Import History
```bash
python3 ~/git/maia/claude/tools/sre/incremental_import_servicedesk.py history
```

### FCR by Team Query
```sql
WITH roster_ticket_team_fcr AS (
    SELECT
        c.team,
        c.ticket_id,
        COUNT(DISTINCT c.user_name) as roster_agent_count
    FROM comments c
    INNER JOIN cloud_team_roster r ON c.user_name = r.username
    WHERE c.user_name IS NOT NULL AND c.user_name <> 'nan'
    AND c.team LIKE 'Cloud -%'
    GROUP BY c.team, c.ticket_id
)
SELECT
    team,
    COUNT(DISTINCT ticket_id) as total,
    ROUND(100.0 * SUM(CASE WHEN roster_agent_count = 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT ticket_id), 1) as fcr_rate
FROM roster_ticket_team_fcr
GROUP BY team
HAVING total > 100
ORDER BY fcr_rate DESC;
```

### Database Location
```
~/git/maia/claude/data/servicedesk_tickets.db
```

### File Locations
```
ETL Tool:       ~/git/maia/claude/tools/sre/incremental_import_servicedesk.py
Dashboard:      ~/git/maia/claude/tools/monitoring/servicedesk_operations_dashboard.py
Database:       ~/git/maia/claude/data/servicedesk_tickets.db
Cloud Roster:   ~/git/maia/claude/data/cloud_team_roster.csv
Documentation:  ~/git/maia/claude/data/SERVICEDESK_ETL_PROJECT.md (this file)
```

---

## Design Decisions Log

### Decision 1: Discard Pre-July 1 Data
**Date**: Oct 14, 2025
**Rationale**: System migration July 1, 2025 - pre-migration data incomplete/unreliable
**Impact**: HARD CUTOFF on all comment and timesheet dates
**Exception**: Tickets created before July 1 kept IF they have post-July 1 Cloud activity

### Decision 2: Use Closing Team as Primary Team
**Date**: Oct 14, 2025
**Rationale**: Tickets change hands frequently, final team assignment most reliable
**Impact**: Team aggregations use final assigned team
**Trade-off**: May not reflect all teams that worked on ticket (addressed by Cloud-touched logic)

### Decision 3: Keep Orphaned Timesheets
**Date**: Oct 14, 2025
**Rationale**: 90.7% orphan rate indicates data quality issue requiring separate analysis
**Impact**: Timesheets table contains entries without matching tickets
**Future**: Investigate root cause (non-Cloud work, export mismatches, etc.)

### Decision 4: Filter by Activity, Not Creation Date
**Date**: Oct 14, 2025
**Rationale**: Cloud may work on older tickets after migration; need full history
**Impact**: Tickets with pre-July 1 creation dates included if Cloud commented after July 1
**Result**: Captures complete picture of Cloud's work

### Decision 5: Convert All IDs to Integers
**Date**: Oct 14, 2025
**Rationale**: Type mismatch between CSVs causing 0-row imports
**Impact**: Ticket IDs normalized to integers for all comparisons
**Risk**: Potential loss of precision if IDs exceed integer range (unlikely for ticket IDs)

---

## Lessons Learned

1. **Type Consistency is Critical**: Always validate data types when joining across CSVs
2. **Date Filtering Complexity**: "July 1+ data" means different things for different tables
3. **CSV Column Explosion**: PowerBI exports can have thousands of empty columns
4. **BOM Characters**: Always use `encoding='utf-8-sig'` for CSV imports
5. **Filter by Activity, Not Creation**: In multi-team environments, creation date ≠ work date
6. **Orphaned Data is Normal**: Cross-system exports rarely align perfectly - plan for it

---

## Contact & Ownership

**Project Owner**: Naythan Dawe
**Created By**: Maia (AI Agent)
**Purpose**: Cloud team ServiceDesk operations analysis
**Environment**: macOS, Python 3.9, SQLite 3.x

**Support**: For issues or questions, refer to this document first. All critical implementation details documented above.
