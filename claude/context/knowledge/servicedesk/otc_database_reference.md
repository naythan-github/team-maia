# OTC ServiceDesk Database Reference

**Database:** `servicedesk` (PostgreSQL)
**Purpose:** Analytics and reporting for OTC (Orro Ticket Cloud) ServiceDesk data
**Last Updated:** 2026-01-08

---

## Quick Start for Analysts

### Connection

**Infrastructure:** PostgreSQL 15 running in Docker container `servicedesk-postgres`

**Prerequisites:**
```bash
# 1. Start Docker Desktop (if not already running)
open -a Docker

# 2. Verify container status (wait ~5s for Docker to start)
docker ps --filter "name=servicedesk-postgres"
# Expected output: servicedesk-postgres   Up XX seconds   0.0.0.0:5432->5432/tcp
```

**Python Connection:**
```python
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='servicedesk',
    user='servicedesk_user',
    password='ServiceDesk2025!SecurePass'
)
```

**Troubleshooting:**
- **Connection refused** → Docker Desktop not running: `open -a Docker`
- **Could not connect** → Container still starting, wait 10s and retry
- **Container not found** → Start container: `docker start servicedesk-postgres`

### Most Common Queries

**Engineering team unassigned backlog:**
```sql
SELECT * FROM servicedesk.get_team_backlog('Cloud - Infrastructure');
```

**User's current workload:**
```sql
SELECT * FROM servicedesk.get_user_workload('Dion Jewell');
```

**Recent activity (30 days):**
```sql
SELECT * FROM servicedesk.v_user_activity;
```

---

## Core Tables

### servicedesk.tickets
**Primary Table** - All ServiceDesk tickets (188,452 tickets as of Jan 2026)

**Key Columns:**
- `TKT-Ticket ID` (INTEGER, PRIMARY KEY) - Unique ticket identifier
- `TKT-Title` (TEXT) - Ticket summary
- `TKT-Status` (TEXT) - Current status
  - **Active:** 'Open', 'In Progress', 'Pending', etc.
  - **Closed:** 'Closed', 'Incident Resolved'
- `TKT-Team` (TEXT) - **Team responsible** ⚠️ CRITICAL FIELD
  - Examples: 'Cloud - Infrastructure', 'Cloud - Security', 'NOC', 'AP BAU'
  - **USE THIS FOR TEAM QUERIES, NOT TKT-Category!**
- `TKT-Category` (TEXT) - **Ticket type** ⚠️ NOT team name!
  - Examples: 'Alert', 'Incident', 'Service Request', 'Support Tickets'
  - Describes WHAT KIND of ticket, not WHO is responsible
- `TKT-Assigned To User` (TEXT) - Full name or ' PendingAssignment'
- `TKT-Created Time` (TIMESTAMP) - When ticket was created
- `TKT-Modified Time` (TIMESTAMP) - Last modification time
- `TKT-Account Name` (TEXT) - Customer/client
- `TKT-Client Name` (TEXT) - End user

**Common Field Confusion:**
```sql
-- ❌ WRONG - This queries ticket TYPES, not teams
WHERE "TKT-Category" = 'Cloud - Infrastructure'

-- ✅ CORRECT - This queries tickets assigned to Cloud Infrastructure TEAM
WHERE "TKT-Team" = 'Cloud - Infrastructure'
```

**Indexes:**
- PRIMARY KEY on `TKT-Ticket ID`
- `idx_tickets_team` - Team queries
- `idx_tickets_status` - Status filtering
- `idx_tickets_status_team` - Combined (fastest)
- `idx_tickets_assigned_user` - Assignment queries
- `idx_tickets_modified_time` - Recent activity
- `idx_tickets_created_time` - Age/creation date

### servicedesk.timesheets
**Work logs** - Time tracking entries (850,727 entries as of Jan 2026)

**Key Columns:**
- `TS-Crm ID` (INTEGER) - References `tickets.TKT-Ticket ID`
- `TS-User Full Name` (TEXT) - Full name (e.g., "Dion Jewell")
- `TS-Date` (TIMESTAMP) - Work date
- `TS-Hours` (NUMERIC) - Hours logged
- `TS-Description` (TEXT) - Work description
- `TS-Category` (TEXT) - Work category
- `TS-Sub Category` (TEXT) - Work subcategory

**Indexes:**
- `idx_timesheets_crm_id` - Join to tickets ⚠️ CRITICAL
- `idx_timesheets_user` - User queries
- `idx_timesheets_date` - Date range queries
- `idx_timesheets_user_date` - User activity by date (fastest)

**Orphaned Data Warning:**
- 97% of timesheet entries reference tickets not in database
- Due to API retention mismatch (timesheets: 18 months, tickets: 10-day modification window)
- Will improve after manual historical import

### servicedesk.comments
**Ticket comments/notes** (317,601 comments as of Jan 2026)

**Key Columns:**
- `comment_id` (INTEGER, PRIMARY KEY)
- `ticket_id` (INTEGER) - References `tickets.TKT-Ticket ID`
- `comment_text` (TEXT) - Comment content
- `user_name` (TEXT) - **Short username** (e.g., "djewell") ⚠️ Different from tickets!
- `created_time` (TIMESTAMP) - When comment was added
- `visible_to_customer` (TEXT) - Customer visibility

**Indexes:**
- PRIMARY KEY on `comment_id`
- `idx_comments_ticket_id` - Join to tickets
- `idx_comments_user_name` - User activity
- `idx_comments_created_time` - Date filtering

**Username Format:**
- Comments use **short usernames**: "djewell", "lbooth", "aziadeh"
- Tickets use **full names**: "Dion Jewell", "Llewellyn Booth"
- Use `servicedesk.user_lookup` to translate

### servicedesk.user_lookup
**Username translation table** (350 users)

**Key Columns:**
- `id` (INTEGER, PRIMARY KEY)
- `short_username` (TEXT, UNIQUE) - Short form ("djewell")
- `full_name` (TEXT, UNIQUE) - Full form ("Dion Jewell")
- `email` (TEXT) - Email address
- `team` (TEXT) - Team assignment (for engineering team members)
- `source` (TEXT) - How mapping was discovered
  - 'manual' - Manually added
  - 'auto_etl' - Auto-discovered during ETL
  - 'auto_timesheet' - From timesheets
  - 'auto_ticket' - From tickets

**Helper Functions:**
```sql
-- Get full name from short username
SELECT servicedesk.get_full_name('djewell');
→ 'Dion Jewell'

-- Get short username from full name
SELECT servicedesk.get_short_username('Dion Jewell');
→ 'djewell'
```

---

## Reporting Views

### servicedesk.v_data_freshness
**Data staleness monitoring** - Shows when each view was last loaded

```sql
SELECT * FROM servicedesk.v_data_freshness;
```

**Columns:**
- `view_name` - tickets/comments/timesheets
- `last_loaded` - Last ETL run
- `age` - Time since last load
- `latest_data_date` - Newest data in view
- `total_records` - Total fetched

### servicedesk.v_orphaned_data
**Data quality monitoring** - Shows records without matching tickets

```sql
SELECT * FROM servicedesk.v_orphaned_data;
```

**Current State:**
- Comments: 108,129 orphaned (89%)
- Timesheets: 145,266 orphaned (97%)

**Note:** High orphan rate expected due to API retention mismatch. Will improve after manual import.

### servicedesk.v_user_activity
**30-day activity summary** - Shows user work patterns

```sql
SELECT * FROM servicedesk.v_user_activity
ORDER BY total_hours DESC;
```

**Columns:**
- `full_name` - User name
- `short_username` - Short username (if known)
- `team` - Team assignment
- `tickets_worked` - Unique tickets touched
- `total_hours` - Hours logged
- `days_active` - Days with activity
- `last_activity` - Most recent work

### servicedesk.v_engineering_tickets
**Engineering team workload** - Pre-filtered to Engineering team

```sql
SELECT * FROM servicedesk.v_engineering_tickets
WHERE "TKT-Status" NOT IN ('Closed', 'Incident Resolved');
```

**Filter:** Tickets where:
- `TKT-Team` IN ('Cloud - Infrastructure', 'Cloud - Security', 'Cloud - L3 Escalation')
- OR ticket assigned to Engineering team member

---

## Helper Functions

### servicedesk.get_user_workload(user_full_name TEXT)
**Returns:** User's open tickets with age

```sql
SELECT * FROM servicedesk.get_user_workload('Dion Jewell');
```

**Returns:**
- `ticket_id` - Ticket ID
- `title` - Ticket title
- `status` - Current status
- `team` - Team responsible
- `created_time` - Creation timestamp
- `age_days` - Days since creation

**Filters:**
- Status NOT IN ('Closed', 'Incident Resolved')
- Assigned to specified user

### servicedesk.get_team_backlog(team_name TEXT)
**Returns:** Team's unassigned open tickets with age

```sql
SELECT * FROM servicedesk.get_team_backlog('Cloud - Infrastructure');
```

**Returns:**
- `ticket_id` - Ticket ID
- `title` - Ticket title
- `status` - Current status
- `category` - Ticket category/type
- `created_time` - Creation timestamp
- `age_days` - Days since creation

**Filters:**
- Team matches specified name
- Status NOT IN ('Closed', 'Incident Resolved')
- Assigned To User LIKE '%PendingAssignment%'

---

## Common Query Patterns

### Engineering Team Workload
```sql
-- Total workload (assigned + unassigned)
SELECT
    "TKT-Team",
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE "TKT-Status" NOT IN ('Closed', 'Incident Resolved')) as open,
    COUNT(*) FILTER (WHERE "TKT-Assigned To User" LIKE '%PendingAssignment%'
                     AND "TKT-Status" NOT IN ('Closed', 'Incident Resolved')) as unassigned
FROM servicedesk.tickets
WHERE "TKT-Team" IN ('Cloud - Infrastructure', 'Cloud - Security', 'Cloud - L3 Escalation')
GROUP BY "TKT-Team";
```

### User Work Patterns (Last 30 Days)
```sql
SELECT
    ul.full_name,
    COUNT(DISTINCT ts."TS-Crm ID") as tickets_worked,
    SUM(ts."TS-Hours") as total_hours,
    COUNT(DISTINCT DATE(ts."TS-Date")) as days_active
FROM servicedesk.user_lookup ul
JOIN servicedesk.timesheets ts ON ul.full_name = ts."TS-User Full Name"
WHERE ts."TS-Date" >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ul.full_name
ORDER BY total_hours DESC;
```

### Ticket Age Distribution
```sql
SELECT
    CASE
        WHEN age_days < 1 THEN '< 1 day'
        WHEN age_days < 7 THEN '1-7 days'
        WHEN age_days < 30 THEN '1-4 weeks'
        WHEN age_days < 90 THEN '1-3 months'
        ELSE '> 3 months'
    END as age_bucket,
    COUNT(*) as count
FROM (
    SELECT EXTRACT(DAY FROM NOW() - "TKT-Created Time") as age_days
    FROM servicedesk.tickets
    WHERE "TKT-Team" = 'Cloud - Infrastructure'
      AND "TKT-Status" NOT IN ('Closed', 'Incident Resolved')
) age_calc
GROUP BY age_bucket
ORDER BY
    CASE age_bucket
        WHEN '< 1 day' THEN 1
        WHEN '1-7 days' THEN 2
        WHEN '1-4 weeks' THEN 3
        WHEN '1-3 months' THEN 4
        ELSE 5
    END;
```

### Comments Activity by User
```sql
SELECT
    ul.full_name,
    COUNT(*) as comment_count,
    MAX(c.created_time) as last_comment
FROM servicedesk.comments c
JOIN servicedesk.user_lookup ul ON c.user_name = ul.short_username
WHERE c.created_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ul.full_name
ORDER BY comment_count DESC;
```

---

## Data Quality & Known Issues

### API Retention Limits
- **Tickets:** Last 10 days of **modifications** (NOT creations!)
  - Ticket created 6 months ago but not modified in 10 days = NOT in database
  - This causes high orphaned data rates
- **Comments:** Last 10 days
- **Timesheets:** Last 18 months

### Manual Import Required
To get complete historical data:
1. Export full ticket history from OTC dashboard
2. Load via ETL with `load_to_postgres.py`
3. Orphaned data will drop significantly

### Field Naming Gotchas
1. **TKT-Team vs TKT-Category** - Most common confusion!
   - TKT-Team = WHO is responsible
   - TKT-Category = WHAT kind of ticket
2. **Hyphenated column names** - Must quote: `"TKT-Team"` not `TKT-Team`
3. **Username formats** - Comments use short, tickets use full

---

## ETL & Data Loading

### Option 1: XLSX Import (Recommended for bulk loads)
**Script:** `claude/tools/integrations/otc/xlsx_to_postgres.py`

```bash
# Load all three files
python3 -m claude.tools.integrations.otc.xlsx_to_postgres \
    --comments ~/Downloads/exports/Cloud-Ticket-Comments.xlsx \
    --tickets ~/Downloads/exports/Tickets-All-6Months.xlsx \
    --timesheets ~/Downloads/exports/Timesheet-18Months.xlsx

# Load individual files
python3 -m claude.tools.integrations.otc.xlsx_to_postgres \
    --tickets ~/Downloads/exports/Tickets-All-6Months.xlsx
```

**XLSX Column Format (Jan 2026+):**
- Comments: `TKTCT-*` columns (e.g., `TKTCT-CommentID`, `TKTCT-TicketID`)
- Tickets: `TKT-*` columns (unchanged)
- Timesheets: `TS-*` columns (unchanged)

### Option 2: API Import (Incremental updates)
**Script:** `claude/tools/integrations/otc/load_to_postgres.py`

```bash
python3 -m claude.tools.integrations.otc.load_to_postgres all
python3 -m claude.tools.integrations.otc.load_to_postgres tickets
python3 -m claude.tools.integrations.otc.load_to_postgres comments
python3 -m claude.tools.integrations.otc.load_to_postgres timesheets
```

**API Process:**
1. Fetches data from OTC API (limited retention)
2. Validates with Pydantic models
3. Loads to PostgreSQL (upsert with conflict handling)
4. Auto-updates user_lookup table

---

## Engineering Team Configuration

**Team Members:** (from `/Users/YOUR_USERNAME/maia/claude/data/user_preferences.json`)
- Trevor Harte
- Llewellyn Booth
- Dion Jewell
- Michael Villaflor
- Olli Ojala
- Abdallah Ziadeh
- Alex Olver
- Josh James
- Taylor Barkle
- Steve Daalmeyer
- Daniel Dignadice

**Team Assignments:**
- Cloud - Infrastructure
- Cloud - Security
- Cloud - L3 Escalation

---

## Performance Notes

- **Indexed queries:** Sub-millisecond performance
- **Join queries:** < 10ms for typical date ranges
- **Best practice:** Always filter by status before assignment checks

**Query Optimization:**
```sql
-- ✅ FAST - Uses idx_tickets_status_team
WHERE "TKT-Team" = 'Cloud - Infrastructure'
  AND "TKT-Status" NOT IN ('Closed', 'Incident Resolved')

-- ❌ SLOW - Scans all tickets first
WHERE "TKT-Assigned To User" = 'Dion Jewell'
  AND "TKT-Status" NOT IN ('Closed', 'Incident Resolved')
```

---

## References

- **ETL Implementation:** `claude/tools/integrations/otc/`
- **Data Models:** `claude/tools/integrations/otc/models.py`
- **View Definitions:** `claude/tools/integrations/otc/views.py`
- **Tests:** `tests/integrations/test_otc_schema_improvements.py`
- **Schema Documentation:** `/Users/YOUR_USERNAME/Downloads/otc_api_exports/IMPLEMENTATION_COMPLETE.md`
