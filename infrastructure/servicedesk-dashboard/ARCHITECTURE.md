# ServiceDesk Dashboard - System Architecture

**Status**: Production
**Last Updated**: 2025-10-21
**Primary Maintainer**: Naythan Dawe

---

## Overview

Production-ready analytics dashboard system providing real-time ServiceDesk operations insights through Grafana visualizations powered by PostgreSQL data warehouse.

**Key Capabilities**:
- 4 Grafana dashboards (Executive, Operations, Quality, Team Performance)
- 23 operational metrics across 6 categories
- 7-table PostgreSQL database (266,622 rows)
- LLM-powered comment quality analysis
- Real-time + batch data refresh

---

## Deployment Model

### Runtime Environment
- **Platform**: Docker Compose
- **Operating System**: macOS (container-based, portable to Linux)
- **Dependencies**: Docker Desktop, Python 3.9+

### Services/Containers

| Service | Container | Port | Purpose | Status |
|---------|-----------|------|---------|--------|
| PostgreSQL 15 | servicedesk-postgres | 5432 | Data warehouse | ✅ Running |
| Grafana 10.x | grafana | 3000 | Visualization platform | ✅ Running |

### Configuration Files
- `docker-compose.yml` - Container orchestration
- `.env` - Secrets (database passwords, Grafana admin)
- `grafana/provisioning/` - Datasources and dashboards
- `postgres/init/` - Database initialization scripts

---

## System Topology

### Architecture Diagram

```
┌─────────────┐
│ XLSX Files  │ (Manual export from ServiceDesk system)
│ (Quarterly) │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────────────────┐
│ ETL Pipeline (Python Scripts - On-Demand)           │
│                                                      │
│  1. Validator    → 40 quality rules                 │
│  2. Cleaner      → Date standardization, NULL conv  │
│  3. Profiler     → Circuit breaker, type detection  │
│  4. Quality      → LLM analysis (6,319 comments)    │
│  5. Migrator     → SQLite → PostgreSQL              │
└─────────────┬───────────────────────────────────────┘
              │
              v
       ┌─────────────┐
       │ PostgreSQL  │ (Docker: servicedesk-postgres:5432)
       │ Database    │
       │             │ Schema: servicedesk
       │ 7 Tables:   │ - tickets (10,939 rows)
       │             │ - comments (108,129 rows)
       │             │ - timesheets (141,062 rows)
       │             │ - comment_quality (6,319 rows)
       │             │ - comment_sentiment (109 rows)
       │             │ - cloud_team_roster (48 rows)
       │             │ - import_metadata (16 rows)
       └─────────────┤
                     │
              ┌──────┴──────┐
              │             │
              v             v
       ┌──────────┐   ┌────────────┐
       │ Grafana  │   │ Python     │
       │ (Docker) │   │ Analytics  │
       │          │   │ Tools      │
       │ Port:3000│   └────────────┘
       │          │
       │ 10 Dashboards:
       │ - Phase 2 (4): Executive, Operations,
       │                Quality, Team Performance
       │ - Automation (6): Exec Overview, Alert
       │                   Analysis, Support Patterns,
       │                   Improvement Tracking,
       │                   Incident Classification,
       │                   Customer Sentiment
       └──────────┘

Access:
- Grafana UI: http://localhost:3000
- Database: docker exec (see Operational Commands)
```

### Component Descriptions

**PostgreSQL Container (servicedesk-postgres)**:
- **Purpose**: Data warehouse for ticket, comment, timesheet, and quality data
- **Technology**: PostgreSQL 15-alpine in Docker container
- **Database**: `servicedesk` (schema: `servicedesk`)
- **Tables**: 7 tables, 143 columns total, 19 indexes, 266,622 rows
- **Dependencies**: None (isolated container)
- **Scalability**: Vertical (currently handles 266K rows, can scale to millions)
- **Persistence**: Docker volume `servicedesk_postgres_data`
- **Schema Documentation**: [SERVICEDESK_DATABASE_SCHEMA.md](../../claude/data/SERVICEDESK_DATABASE_SCHEMA.md) (complete schema, validated 2025-10-21)

**Grafana Container (grafana)**:
- **Purpose**: Web-based analytics and visualization platform
- **Technology**: Grafana 10.x in Docker container
- **Dependencies**: PostgreSQL datasource connection
- **Scalability**: Vertical (dashboard rendering, not data storage)
- **Persistence**: Docker volume `grafana_data`

**ETL Pipeline (Python Scripts)**:
- **Purpose**: Extract-Transform-Load from XLSX → SQLite → PostgreSQL
- **Technology**: Python 3.9+ with pandas, psycopg2, ollama
- **Dependencies**: Ollama (for LLM quality analysis), PostgreSQL container
- **Scalability**: Single-machine batch processing (260K rows in <25 min)
- **Execution**: On-demand via CLI (not automated)

---

## Data Flow

### Primary Data Flows

#### 1. **Quarterly Data Import**: XLSX → PostgreSQL (ETL V2 Pipeline)
- **Trigger**: Manual (quarterly ServiceDesk export)
- **Frequency**: Quarterly (or on-demand for updates)
- **Volume**: ~10K tickets, ~100K comments, ~140K timesheets per import
- **SLA**: 25-30 minutes (validated, excludes quality analysis)
- **Reference**: [ETL Operational Runbook](../../claude/data/SERVICEDESK_ETL_OPERATIONAL_RUNBOOK.md)

**Prerequisites** (5-10 minutes):
```bash
# Gate 0: Pre-flight checks and backups
1. python3 claude/tools/sre/servicedesk_etl_preflight.py \
     --source /path/to/servicedesk_tickets.db
   → Validates: Disk space (≥2GB), PostgreSQL connection, dependencies
   → Exit criteria: All checks PASS

2. python3 claude/tools/sre/servicedesk_etl_backup.py backup \
     --source /path/to/servicedesk_tickets.db \
     --output /backups/
   → Creates: Time-stamped backup with MD5 checksum
   → Enables: Safe rollback if migration fails

3. docker exec servicedesk-postgres pg_dump -U servicedesk_user \
     -d servicedesk -n servicedesk -F c \
     -f /backups/servicedesk_schema_$(date +%Y%m%d_%H%M%S).backup
   → Backs up: PostgreSQL schema (for rollback)
```

**Deployment** (25-30 minutes):
```bash
# Gate 1: Data Profiling (5 minutes)
4. python3 claude/tools/sre/servicedesk_etl_data_profiler.py \
     --source /path/to/servicedesk_tickets.db \
     --use-validator \
     --use-scorer
   → Type detection with circuit breaker
   → Halts if: >20% corrupt dates OR >10% type mismatches
   → Quality scoring: 0-100 scale
   → Embeds: servicedesk_etl_validator.py (40 rules)
   → Embeds: servicedesk_quality_scorer.py (quality metrics)

# Gate 2: Data Cleaning (15 minutes for 260K rows)
5. python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
     --source /path/to/servicedesk_tickets.db \
     --output /path/to/servicedesk_tickets_clean.db \
     --min-quality 80
   → Date standardization: DD/MM/YYYY → YYYY-MM-DD (ISO format)
   → Empty strings → NULL (for date/numeric columns)
   → PostgreSQL ROUND() casting: Add ::numeric
   → Transaction safety: Rollback on failure

# Gate 3: PostgreSQL Migration (5 minutes)
6. python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
     --source /path/to/servicedesk_tickets_clean.db \
     --mode canary
   → Quality gate: Minimum 80/100 score required
   → Canary deployment: Test 10% sample before full migration
   → Blue-green option: --mode blue-green (zero-downtime cutover)
   → Idempotent: Safe to retry on failure
```

**Post-Deployment Validation** (5-10 minutes):
```bash
# Verify row counts match
7. sqlite3 /path/to/servicedesk_tickets_clean.db "SELECT COUNT(*) FROM tickets;"
   docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk \
     -c "SELECT COUNT(*) FROM servicedesk.tickets;"

# Sample data verification
8. docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk \
     -c "SELECT \"TKT-Created Time\", \"TKT-Resolved Time\"
         FROM servicedesk.tickets LIMIT 5;"

# Grafana smoke test
9. Open http://localhost:3000 → Verify all dashboards load with data
```

**Result**: SQLite data migrated to PostgreSQL, dashboards auto-refresh

#### 2. **Dashboard Refresh**: PostgreSQL → Grafana
- **Trigger**: Automatic (Grafana query refresh)
- **Frequency**: 5 minutes (configurable per dashboard)
- **Volume**: 100+ metrics across 10 operational dashboards
- **SLA**: <2 seconds dashboard load, <500ms per query

**Flow**:
```
1. User opens Grafana dashboard (http://localhost:3000)
2. Grafana executes SQL queries against PostgreSQL
3. Results rendered in panels (KPI cards, charts, tables)
4. Auto-refresh every hour (configurable per dashboard)
```

#### 3. **Comment Quality Analysis**: Comments → LLM → PostgreSQL (Optional, Post-Migration)
- **Trigger**: Manual (on-demand via servicedesk_quality_analyzer_postgres.py)
- **Frequency**: After each data import (optional enhancement)
- **Volume**: 6,319 human comments analyzed (filters user_name != 'brian')
- **SLA**: 6-10 hours for full analysis (~10 sec/comment)
- **When**: Run AFTER successful PostgreSQL migration (Gate 3 complete)

**Flow**:
```bash
# Run quality analysis (optional, after migration complete)
python3 claude/tools/sre/servicedesk_quality_analyzer_postgres.py \
  --batch-size 100 \
  --max-comments 6000

# Process:
1. Reads comments from servicedesk.comments table (PostgreSQL)
2. Filters system user "brian" (66,046 automation comments excluded)
3. Sends human comments to Ollama (llama3.1:8b model) for LLM analysis
4. LLM scores: professionalism, clarity, empathy, actionability (1-5 scale)
5. Writes results to servicedesk.comment_quality table
6. Grafana Quality Dashboard (UID: servicedesk-quality) reflects new data immediately
```

**Note**: Quality analysis is optional and runs independently after migration. Does NOT block ETL pipeline.

---

## ETL Tool Inventory

### Core ETL Pipeline (Required for Data Import)

**Location**: `/Users/naythandawe/git/maia/claude/tools/sre/`

| Script | Purpose | Execution Time | When to Use |
|--------|---------|----------------|-------------|
| **servicedesk_etl_preflight.py** | Environment validation | 1 min | Before every deployment (Gate 0) |
| **servicedesk_etl_backup.py** | Backup with MD5 verification | 1-2 min | Before every deployment (Gate 0) |
| **servicedesk_etl_data_profiler.py** | Type detection + circuit breaker | 5 min | Every deployment (Gate 1) |
| **servicedesk_etl_data_cleaner_enhanced.py** | Date/NULL cleaning | 15 min | Every deployment (Gate 2) |
| **migrate_sqlite_to_postgres_enhanced.py** | PostgreSQL migration | 5 min | Every deployment (Gate 3) |

**Total Pipeline Time**: 25-30 minutes (validated on 260K rows)

**Usage**:
```bash
# Complete ETL pipeline (sequential execution)
cd /Users/naythandawe/git/maia

# Gate 0: Prerequisites
python3 claude/tools/sre/servicedesk_etl_preflight.py --source /path/to/servicedesk_tickets.db
python3 claude/tools/sre/servicedesk_etl_backup.py backup --source /path/to/servicedesk_tickets.db --output /backups/

# Gate 1: Profiling
python3 claude/tools/sre/servicedesk_etl_data_profiler.py --source /path/to/servicedesk_tickets.db --use-validator --use-scorer

# Gate 2: Cleaning
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py --source /path/to/servicedesk_tickets.db --output /path/to/servicedesk_tickets_clean.db --min-quality 80

# Gate 3: Migration
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py --source /path/to/servicedesk_tickets_clean.db --mode canary
```

---

### Quality Analysis Tools (Optional Post-Migration)

**Location**: `/Users/naythandawe/git/maia/claude/tools/sre/`

| Script | Purpose | Execution Time | When to Use |
|--------|---------|----------------|-------------|
| **servicedesk_quality_analyzer_postgres.py** | LLM comment analysis | 6-10 hours | After migration, quarterly |
| **servicedesk_comment_quality_analyzer.py** | Batch quality analysis | Variable | Ad-hoc quality audits |
| **servicedesk_complete_quality_analyzer.py** | Comprehensive analysis | Variable | Full quality review |
| **servicedesk_quality_monitoring.py** | Quality metrics tracking | Real-time | Ongoing monitoring |

**Usage**:
```bash
# Run quality analysis after successful migration
python3 claude/tools/sre/servicedesk_quality_analyzer_postgres.py \
  --batch-size 100 \
  --max-comments 6000
```

---

### Support & Analysis Tools (Ad-hoc Operations)

**Location**: `/Users/naythandawe/git/maia/claude/tools/sre/`

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **servicedesk_discovery_analyzer.py** | Pattern discovery, automation opportunities | Strategic planning |
| **servicedesk_operations_intelligence.py** | Operations insights | Capacity planning |
| **servicedesk_ops_intel_hybrid.py** | Hybrid intelligence | Advanced analytics |
| **servicedesk_agent_quality_coach.py** | Training recommendations | Agent coaching |
| **servicedesk_best_practice_library.py** | Best practice catalog | Knowledge management |

---

### ETL Infrastructure (Embedded in Core Tools)

**Location**: `/Users/naythandawe/git/maia/claude/tools/sre/`

| Script | Purpose | Called By |
|--------|---------|-----------|
| **servicedesk_etl_validator.py** | 40 data quality rules | Data profiler (embedded) |
| **servicedesk_quality_scorer.py** | Quality scoring (0-100 scale) | Data profiler (embedded) |
| **servicedesk_etl_observability.py** | Structured logging + Prometheus metrics | All ETL tools |

**Note**: These are NOT standalone scripts - they're imported and called by the core ETL pipeline tools.

---

### Migration Scripts

**Location**: `/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/migration/`

| Script | Purpose | Size | Status |
|--------|---------|------|--------|
| **migrate_sqlite_to_postgres_enhanced.py** | Canary + blue-green migration | 29 KB | ✅ Production (ETL V2) |
| **migrate_sqlite_to_postgres.py** | Basic migration | 11 KB | ⚠️ Legacy (superseded) |

---

### RAG & Indexing Tools (Experimental)

**Location**: `/Users/naythandawe/git/maia/claude/tools/sre/`

| Script | Purpose | Size |
|--------|---------|------|
| **servicedesk_gpu_rag_indexer.py** | GPU-accelerated RAG indexing | 27 KB |
| **servicedesk_multi_rag_indexer.py** | Multi-model RAG | 14 KB |
| **servicedesk_parallel_rag_indexer.py** | Parallel RAG processing | 18 KB |

**Note**: RAG tools are experimental and not part of core ETL pipeline.

---

### Complete Documentation References

**ETL Process Documentation**:
- **Operational Runbook**: [SERVICEDESK_ETL_OPERATIONAL_RUNBOOK.md](../../claude/data/SERVICEDESK_ETL_OPERATIONAL_RUNBOOK.md) (850 lines)
- **Monitoring Guide**: [SERVICEDESK_ETL_MONITORING_GUIDE.md](../../claude/data/SERVICEDESK_ETL_MONITORING_GUIDE.md) (450 lines)
- **Best Practices**: [SERVICEDESK_ETL_BEST_PRACTICES.md](../../claude/data/SERVICEDESK_ETL_BEST_PRACTICES.md) (400 lines)
- **Final Status**: [SERVICEDESK_ETL_V2_FINAL_STATUS.md](../../claude/data/SERVICEDESK_ETL_V2_FINAL_STATUS.md) (300 lines)

**Database Schema**:
- **Complete Schema**: [SERVICEDESK_DATABASE_SCHEMA.md](../../claude/data/SERVICEDESK_DATABASE_SCHEMA.md) (549 lines, validated 2025-10-21)

---

### Data Transformations

**ETL Cleaner Transformations**:
- **Input Format**: SQLite database (from XLSX import)
- **Validation**: 40 rules (see servicedesk_etl_validator.py)
- **Transformations**:
  - Date format: DD/MM/YYYY → YYYY-MM-DD HH:MM:SS (TIMESTAMP)
  - Empty strings → NULL (for date/numeric columns)
  - ROUND() casting: Add ::numeric for PostgreSQL compatibility
- **Output Format**: Cleaned SQLite → PostgreSQL via migration script

**Quality Analysis Transformations**:
- **Input Format**: Raw comment text from PostgreSQL
- **Processing**: LLM analysis (llama3.1:8b via Ollama)
- **Output Format**: Structured quality scores (1-5 scale, 4 dimensions)

---

## Integration Points

### Python Tools → PostgreSQL (PRIMARY METHOD)

**Connection Method**: `docker exec` via PostgreSQL CLI

**Implementation**:
```bash
# Write data to PostgreSQL
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "
INSERT INTO servicedesk.comment_quality (comment_id, quality_score, ...)
VALUES (12345, 3.5, ...);
"

# Read data from PostgreSQL
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "
SELECT * FROM servicedesk.tickets WHERE \"TKT-Status\" = 'Closed';
"
```

**Authentication**:
- Method: Username/password from .env file
- Location: `.env` (gitignored) - `POSTGRES_USER`, `POSTGRES_PASSWORD`

**Error Handling**:
- Retry Strategy: No automatic retry (manual re-run)
- Fallback: Check container status (`docker ps | grep servicedesk-postgres`)
- Logging: ETL tools use servicedesk_etl_observability.py (structured JSON logs)

**NOT Supported** ⚠️:
- ❌ Direct psycopg2 connection from host (`psycopg2.connect(host='localhost', ...)`)
  - **Why**: PostgreSQL runs in isolated Docker container
  - **Symptom**: Connection refused errors
  - **Solution**: Use `docker exec` commands

### Grafana → PostgreSQL

**Connection Method**: Grafana PostgreSQL datasource plugin

**Implementation**:
- **Datasource Name**: "ServiceDesk PostgreSQL"
- **Host**: `servicedesk-postgres:5432` (Docker network)
- **Database**: `servicedesk`
- **User**: `servicedesk_user`
- **SSL Mode**: Disable (trusted Docker network)

**Authentication**:
- Method: Username/password from Grafana provisioning
- Location: `grafana/provisioning/datasources/postgres.yml`

**Query Pattern**:
```sql
-- All queries use schema-qualified table names
SELECT
    ROUND(AVG(quality_score)::numeric, 2) as avg_quality
FROM servicedesk.comment_quality
WHERE quality_score IS NOT NULL;
```

**Performance**:
- Query timeout: 30 seconds
- Cache: 5 minutes per panel
- Expected P95 latency: <100ms

### Ollama (LLM) → PostgreSQL

**Connection Method**: Python script with Ollama library + docker exec

**Implementation**:
```python
# 1. Ollama analysis
from ollama import Client
client = Client(host='http://localhost:11434')
response = client.chat(model='llama3.1:8b', messages=[...])

# 2. Write results via docker exec
subprocess.run([
    'docker', 'exec', 'servicedesk-postgres',
    'psql', '-U', 'servicedesk_user', '-d', 'servicedesk',
    '-c', f"INSERT INTO servicedesk.comment_quality ..."
])
```

**Authentication**:
- Ollama: No authentication (localhost)
- PostgreSQL: Via docker exec (see above)

**Error Handling**:
- LLM errors: Retry 3 times with exponential backoff
- Database errors: Log and continue to next comment
- Overall failure: Resume from last processed comment_id

---

## Database Schema

### Schema Overview

**Database**: `servicedesk` (PostgreSQL 15-alpine)
**Schema**: `servicedesk`
**Total Tables**: 7
**Total Rows**: 266,622
**Total Columns**: 143
**Total Indexes**: 19

**Complete Documentation**: [SERVICEDESK_DATABASE_SCHEMA.md](../../claude/data/SERVICEDESK_DATABASE_SCHEMA.md) (549 lines, validated 2025-10-21)

---

### Table Summary

| Table | Rows | Columns | Indexes | Purpose |
|-------|------|---------|---------|---------|
| **tickets** | 10,939 | 60 | 10 | Ticket data warehouse (primary table) |
| **comments** | 108,129 | 10 | 2 | Comment history and customer feedback |
| **timesheets** | 141,062 | 21 | 2 | Task-level time tracking |
| **comment_quality** | 6,319 | 17 | 2 | LLM quality analysis scores |
| **comment_sentiment** | 109 | 13 | 4 | Sentiment analysis results |
| **cloud_team_roster** | 48 | 3 | 0 | Team member directory |
| **import_metadata** | 16 | 9 | 0 | ETL run tracking and metadata |

**Total**: 266,622 rows across 7 tables

---

### Key Tables Detail

#### tickets (Primary Table)

**Rows**: 10,939
**Columns**: 60 (complete ServiceDesk export)
**Indexes**: 10 (optimized for query performance)

**Critical Columns**:
- **Timestamps** (TIMESTAMP type):
  - `TKT-Created Time` - Ticket creation
  - `TKT-Resolved Time` - Resolution timestamp
  - `TKT-Closed Time` - Closure timestamp
  - `TKT-Last Modified Time` - Last update

- **Categorical Fields**:
  - `TKT-Status` - Current status (Open, Closed, PendingAssignment, etc.)
  - `TKT-Category` - Incident type (Incident, Service Request, Change, etc.)
  - `TKT-Priority` - Priority level (1-5)
  - `TKT-Assigned To` - Current assignee

- **SLA Fields**:
  - `SLA-1 Compliance` - First response SLA compliance
  - `SLA-2 Compliance` - Resolution SLA compliance

**Key Indexes**:
1. `idx_tickets_created_time` - Time-series queries
2. `idx_tickets_category` - Category filtering
3. `idx_tickets_resolution_dates` - Resolution time calculations
4. `idx_tickets_status_category` - Performance metrics

**Used By**: All 10 Grafana dashboards

---

#### comments (Comment History)

**Rows**: 108,129 (66,046 automation + 42,083 human)
**Columns**: 10
**Indexes**: 2

**Key Columns**:
- `comment_id` - Unique identifier
- `ticket_id` - Foreign key to tickets table
- `comment_text` - Full comment text
- `user_name` - Author (filter "brian" for automation)
- `created_time` - Comment timestamp
- `is_public` - Customer-facing flag

**Filter Pattern**: `WHERE user_name != 'brian'` (exclude automation comments)

**Used By**: Dashboard 7 (Customer Sentiment), Quality Dashboard

---

#### timesheets (Task-Level Time Tracking)

**Rows**: 141,062
**Columns**: 21
**Indexes**: 2

**Key Columns**:
- `ticket_id` - Foreign key to tickets table
- `task_type` - Categorization (Communication, Technical, Administrative)
- `hours_logged` - Time spent
- `assignee` - Team member

**Coverage**: 9.6% of tickets have timesheet entries (762/7,969)

**Used By**: Dashboard 4 (Team Performance & Task-Level)

---

#### comment_quality (LLM Analysis Results)

**Rows**: 6,319 (analyzed comments, 5.8% coverage)
**Columns**: 17
**Indexes**: 2

**Key Columns**:
- `comment_id` - Foreign key to comments table
- `professionalism_score` - 1-5 scale
- `clarity_score` - 1-5 scale
- `empathy_score` - 1-5 scale
- `actionability_score` - 1-5 scale
- `quality_tier` - Excellent/Good/Fair/Poor
- `analysis_timestamp` - LLM processing time

**LLM Model**: Ollama llama3.1:8b
**Processing Time**: ~10 sec/comment

**Used By**: Quality Dashboard

---

### Database Access Patterns

**Read Access** (Grafana):
- Connection: Grafana PostgreSQL datasource plugin
- Method: Direct SQL queries via datasource proxy
- Authentication: servicedesk_user (from provisioning config)

**Write Access** (Python ETL Tools):
- Connection: `docker exec` via PostgreSQL CLI
- Method: SQL INSERT/UPDATE via psql
- Authentication: servicedesk_user (from .env)
- **NOT SUPPORTED**: Direct psycopg2 connections (container isolation)

**Example Write Pattern**:
```bash
docker exec servicedesk-postgres psql \
  -U servicedesk_user \
  -d servicedesk \
  -c "INSERT INTO servicedesk.comment_quality (comment_id, quality_score, ...)
      VALUES (12345, 3.5, ...);"
```

---

### Schema Management

**Migrations**: Manual (via migrate_sqlite_to_postgres_enhanced.py)
**Backups**:
- Database: docker exec pg_dump (before each ETL run)
- Retention: 30 days (manual cleanup)

**Schema Changes**:
- Frequency: Rare (7 tables stable since Oct 2025)
- Process: Test in blue-green schema, canary deployment
- Rollback: Restore from backup (pg_dump archives)

---

### Performance Characteristics

**Query Performance** (tested on 266K rows):
- Simple aggregations (COUNT, AVG): 25-40ms
- Time-series queries: 40-80ms
- Pattern matching (ILIKE): 150-180ms
- Complex joins (3+ tables): 200-350ms
- Full dashboard load (10+ queries): 1.2-1.5 seconds

**All queries meet <500ms SLA** ✅

**Optimization Potential**:
- Materialized views for pattern matching (90% faster: 200ms → <20ms)
- Table partitioning if dataset exceeds 100K tickets (50-70% faster)

---

## Grafana Dashboards

### Dashboard Inventory (10 Operational Dashboards)

**Total Deployed**: 10 dashboards (organized in 2 sets)
**Access**: http://localhost:3000
**Auto-Refresh**: 5 minutes (configurable)
**Data Source**: ServiceDesk PostgreSQL (UID: P6BECECF7273D15EE)

---

### Set 1: Phase 2 Stakeholder Dashboards (4 Dashboards)

**Purpose**: Multi-audience analytics for different organizational roles
**Created**: Phase 2 (Oct 19, 2025)
**Documentation**: See `claude/data/SERVICEDESK_DASHBOARD_PHASE_2_COMPLETE.md`

#### 1. ServiceDesk Executive Dashboard
- **UID**: `servicedesk-executive`
- **URL**: http://localhost:3000/d/servicedesk-executive
- **Audience**: Executives, C-level
- **Panels**: 6 stat panels
- **Metrics**: 5 KPIs (total tickets, avg resolution time, SLA compliance, team size, quality score)
- **Purpose**: High-level performance summary for executive oversight

#### 2. ServiceDesk Operations Dashboard
- **UID**: `servicedesk-operations`
- **URL**: http://localhost:3000/d/servicedesk-operations
- **Audience**: Operations Managers
- **Panels**: 8 panels (time-series, tables, stat panels)
- **Metrics**: 13 operational metrics (ticket volume trends, category distribution, SLA tracking, backlog)
- **Purpose**: Day-to-day operational monitoring and capacity planning

#### 3. ServiceDesk Quality Dashboard
- **UID**: `servicedesk-quality`
- **URL**: http://localhost:3000/d/servicedesk-quality
- **Audience**: Quality Managers, Training Teams
- **Panels**: 8 panels (quality scores, trends, agent rankings)
- **Metrics**: 6 quality metrics (professionalism, clarity, empathy, actionability, quality tiers)
- **Purpose**: Agent performance evaluation and training needs identification

#### 4. ServiceDesk Team Performance Dashboard
- **UID**: `servicedesk-team-performance`
- **URL**: http://localhost:3000/d/servicedesk-team-performance
- **Audience**: Team Leads, Individual Agents
- **Panels**: 4 panels (workload distribution, resolution time, close rates)
- **Metrics**: 8 team metrics (tickets per assignee, avg resolution, close rates, performance rankings)
- **Purpose**: Individual and team performance tracking

---

### Set 2: Automation Analytics Suite (6 Dashboards)

**Purpose**: Automation opportunity identification and ROI tracking
**Created**: Phase 132-134 (Oct 19-20, 2025)
**Documentation**: See `README_DASHBOARDS.md`, `DASHBOARD_DELIVERY_SUMMARY.md`

#### 5. Dashboard 1: Automation Executive Overview
- **UID**: `servicedesk-automation-exec`
- **URL**: http://localhost:3000/d/servicedesk-automation-exec
- **Tags**: automation, executive, roi, servicedesk
- **Panels**: 9 panels
- **Key Metrics**:
  - 10,939 tickets analyzed
  - 4,842 automation opportunities (82.2% coverage)
  - $952K annual savings potential
  - 960 quick wins (motion/sensor alerts)
- **Purpose**: Single-pane-of-glass automation opportunity summary for decision makers

#### 6. Dashboard 2: Alert Analysis Deep-Dive
- **UID**: `servicedesk-alert-analysis`
- **URL**: http://localhost:3000/d/servicedesk-alert-analysis
- **Tags**: alerts, automation, patterns, servicedesk
- **Panels**: 9 panels (time-series, heatmaps, tables)
- **Alert Patterns**: 5 categories
  - Motion/Sensor alerts: 960 tickets ($268K/year savings)
  - Patch failures: 555 tickets ($155K/year)
  - Network/VPN: 490 tickets
  - Azure Resource Health: 678 tickets ($189K/year)
  - SSL/Certificate: 248 tickets ($87K/year)
- **Purpose**: Detailed alert pattern analysis for automation scoping

#### 7. Dashboard 3: Support Ticket Pattern Analysis
- **UID**: `servicedesk-support-patterns`
- **URL**: http://localhost:3000/d/servicedesk-support-patterns
- **Tags**: automation, patterns, support, servicedesk
- **Panels**: 8 panels (time-series, pie charts, tables)
- **Support Patterns**: 5 categories
  - Access/Permissions: 908 tickets ($253K/year) - Medium complexity
  - Email issues: 526 tickets ($147K/year) - High complexity
  - Password reset: 196 tickets ($91K/year) - Low complexity (quick win)
  - License management: 94 tickets
  - Software installation: 125 tickets
- **Purpose**: Support automation opportunities with complexity ratings

#### 8. Dashboard 5: Improvement Tracking & ROI Calculator
- **UID**: `servicedesk-improvement-tracking`
- **URL**: http://localhost:3000/d/servicedesk-improvement-tracking
- **Tags**: baseline, improvement, roi, servicedesk, tracking
- **Panels**: 13 panels (baseline KPIs, trends, ROI calculators, implementation status)
- **Features**:
  - Baseline metrics (pre-automation snapshot)
  - Post-automation placeholders (populate after deployment)
  - ROI calculator (estimated vs actual savings by pattern)
  - Cumulative ROI tracker ($952K estimated vs $0 actual)
- **Purpose**: Before/after comparison framework for automation ROI tracking

#### 9. Dashboard 6: Incident Classification Breakdown
- **UID**: `servicedesk-incident-classification`
- **URL**: http://localhost:3000/d/servicedesk-incident-classification
- **Tags**: classification, cloud, networking, servicedesk, telecommunications
- **Panels**: 11 panels
- **Classifications**:
  - 6,903 incidents analyzed
  - Technology stack distribution (Azure, AWS, On-Prem, Telecommunications)
  - Incident type breakdown (Cloud, Networking, Telecommunications)
  - Time-series trends by category
- **Purpose**: Infrastructure incident analysis and technology stack insights

#### 10. Dashboard 7: Customer Sentiment & Team Performance
- **UID**: `servicedesk-sentiment-team-performance`
- **URL**: http://localhost:3000/d/servicedesk-sentiment-team-performance
- **Tags**: sentiment, customer-satisfaction, performance, servicedesk, team-ranking
- **Panels**: 11 panels (stat panels, tables, charts, time-series)
- **Key Features**:
  - 16,620 customer-facing comments analyzed
  - Positive sentiment rate: 50.6%
  - Team performance composite scores (SLA + speed + sentiment)
  - Top 20 team member rankings
  - Recent positive/negative comment tables
- **Purpose**: Customer satisfaction analysis and sentiment-based team performance rankings
- **Methodology**: TDD (20/20 tests passing)

---

### Dashboard Files on Disk

**Location**: `/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards/`

**Phase 2 Dashboards** (4 files):
- `executive_dashboard.json` (293 lines)
- `operations_dashboard.json` (333 lines)
- `quality_dashboard.json` (504 lines)
- `team_performance_dashboard.json` (267 lines)

**Automation Suite** (7 files):
- `1_automation_executive_overview.json` (642 lines)
- `2_alert_analysis_deepdive.json` (551 lines)
- `3_support_pattern_analysis.json` (527 lines)
- `4_team_performance_tasklevel.json` (548 lines) ⚠️ **NOT YET IMPORTED**
- `5_improvement_tracking_roi.json` (752 lines)
- `6_incident_classification_breakdown.json` (587 lines)
- `7_customer_sentiment_team_performance.json` (1,114 lines)

**Total**: 11 dashboard JSON files (6,118 lines)
**Deployed**: 10/11 dashboards (Dashboard 4 pending re-import)

---

### Dashboard Import/Update

**Automated Import** (All dashboards):
```bash
cd /Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard
bash scripts/import_dashboards.sh
```

**Manual Import** (Single dashboard):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -u "admin:${GRAFANA_ADMIN_PASSWORD}" \
  -d @grafana/dashboards/[dashboard_name].json \
  http://localhost:3000/api/dashboards/db
```

**Verify Import**:
```bash
# Via API (list all dashboards)
curl -s -u "admin:${GRAFANA_ADMIN_PASSWORD}" \
  'http://localhost:3000/api/search?type=dash-db' | python3 -m json.tool

# Via Browser
open http://localhost:3000/dashboards
```

---

### Dashboard Performance

**Query Performance** (tested on 266K rows):
- Simple aggregations: 25-40ms
- Time-series queries: 40-80ms
- Pattern matching: 150-180ms
- Complex joins: 200-350ms
- Full dashboard load: 1.2-1.5 seconds

**All dashboards meet <2 second load time SLA** ✅

---

### Dashboard Maintenance

**Weekly**:
- Verify all panels display data correctly
- Check query performance (no queries >500ms)

**Monthly**:
- Update time range if new data imported
- Review dashboard usage analytics
- Backup dashboard JSON files

**Quarterly**:
- Review automation ROI metrics (Dashboard 5)
- Update hourly rate assumptions if changed
- Add new automation patterns if identified

---

## Operational Commands

### Start System
```bash
cd infrastructure/servicedesk-dashboard
docker-compose up -d

# Verify containers running
docker ps | grep servicedesk
```

### Stop System
```bash
cd infrastructure/servicedesk-dashboard
docker-compose down

# To remove volumes (destructive - deletes data):
docker-compose down -v
```

### Access Components

**PostgreSQL Database**:
```bash
# Interactive psql shell
docker exec -it servicedesk-postgres psql -U servicedesk_user -d servicedesk

# Single query
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT COUNT(*) FROM servicedesk.tickets;"

# Export data
docker exec servicedesk-postgres pg_dump -U servicedesk_user servicedesk > backup.sql
```

**Grafana UI**:
```bash
# Open in browser
open http://localhost:3000

# Credentials
# Username: admin
# Password: See .env file (GRAFANA_ADMIN_PASSWORD)
```

**ETL Pipeline**:
```bash
# Validate data quality
python3 claude/tools/sre/servicedesk_etl_validator.py --source servicedesk_tickets.db

# Clean data
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source servicedesk_tickets.db \
  --output servicedesk_tickets_cleaned.db

# Analyze comment quality
python3 claude/tools/sre/servicedesk_quality_analyzer_postgres.py \
  --sample-size 6319 \
  --batch-size 10

# Migrate to PostgreSQL
python3 infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source servicedesk_tickets_cleaned.db \
  --canary
```

### Health Checks

**Container Health**:
```bash
# All containers running?
docker ps | grep servicedesk

# PostgreSQL ready?
docker exec servicedesk-postgres pg_isready -U servicedesk_user

# Grafana responsive?
curl -s http://localhost:3000/api/health | jq
```

**Data Quality**:
```bash
# Row counts
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "
SELECT
    'tickets' as table_name, COUNT(*) as row_count FROM servicedesk.tickets
UNION ALL
SELECT 'comments', COUNT(*) FROM servicedesk.comments
UNION ALL
SELECT 'comment_quality', COUNT(*) FROM servicedesk.comment_quality;
"

# Quality score distribution
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "
SELECT quality_tier, COUNT(*) as count
FROM servicedesk.comment_quality
GROUP BY quality_tier
ORDER BY count DESC;
"
```

**Dashboard Availability**:
```bash
# List dashboards
curl -s -u admin:${GRAFANA_PASSWORD} http://localhost:3000/api/search | jq '.[].title'
```

### Backup/Restore

**Backup**:
```bash
# Database backup
docker exec servicedesk-postgres pg_dump -U servicedesk_user servicedesk > \
  backups/servicedesk-$(date +%Y%m%d).sql

# Full system backup (including Grafana config)
docker-compose down
tar -czf backups/servicedesk-dashboard-$(date +%Y%m%d).tar.gz \
  infrastructure/servicedesk-dashboard
docker-compose up -d
```

**Restore**:
```bash
# Database restore
docker exec -i servicedesk-postgres psql -U servicedesk_user -d servicedesk < \
  backups/servicedesk-20251021.sql

# Full system restore
tar -xzf backups/servicedesk-dashboard-20251021.tar.gz
cd infrastructure/servicedesk-dashboard
docker-compose up -d
```

---

## Common Issues & Solutions

### Issue: Can't Connect to PostgreSQL from Python
**Symptoms**: `psycopg2.OperationalError: could not connect to server`
**Cause**: Database runs in isolated Docker container, not accessible via localhost direct connection
**Solution**: Use `docker exec` commands instead of direct psycopg2.connect()

```bash
# ❌ Wrong (fails with connection refused)
python3 -c "import psycopg2; psycopg2.connect(host='localhost', port=5432, ...)"

# ✅ Correct (via container)
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "SELECT 1;"
```

### Issue: Grafana Dashboards Show "No Data"
**Symptoms**: Panels display "No data" despite PostgreSQL having data
**Cause**: Datasource configuration incorrect or database credentials wrong
**Solution**:
```bash
# 1. Verify PostgreSQL has data
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c \
  "SELECT COUNT(*) FROM servicedesk.tickets;"

# 2. Test Grafana datasource
curl -u admin:${GRAFANA_PASSWORD} http://localhost:3000/api/datasources

# 3. Check datasource health
# In Grafana UI: Configuration → Data Sources → ServiceDesk PostgreSQL → Test
```

### Issue: Quality Analysis Takes Too Long
**Symptoms**: Comment quality analysis runs for 24+ hours
**Cause**: Processing all 108K comments instead of just human comments
**Solution**: Filter system user "brian" (66,046 automation comments)

```python
# ✅ Correct filter
SELECT * FROM comments
WHERE comment_type = 'comments'
  AND user_name != 'brian'  -- Exclude automation
  AND visible_to_customer = 'Yes';
```

### Issue: ETL Pipeline Fails with Type Errors
**Symptoms**: `ERROR: column "TKT-Created Time" is of type timestamp without time zone but expression is of type text`
**Cause**: Date columns contain DD/MM/YYYY format or empty strings
**Solution**: Run data cleaner before migration

```bash
# Run cleaner first
python3 claude/tools/sre/servicedesk_etl_data_cleaner_enhanced.py \
  --source servicedesk_tickets.db \
  --output servicedesk_tickets_cleaned.db

# Then migrate
python3 infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source servicedesk_tickets_cleaned.db
```

### Issue: Dashboard Queries Fail with ROUND() Error
**Symptoms**: `ERROR: function round(double precision, integer) does not exist`
**Cause**: PostgreSQL requires explicit `::numeric` cast for ROUND() on REAL columns
**Solution**: Use `ROUND(column::numeric, 2)` in queries

```sql
-- ❌ Wrong
SELECT ROUND(AVG(quality_score), 2) FROM comment_quality;

-- ✅ Correct
SELECT ROUND(AVG(quality_score)::numeric, 2) FROM comment_quality;
```

---

## Performance Characteristics

### Expected Performance
- **Dashboard Load Time**: <1 second ✅ (target: <2 seconds)
- **Individual Query Time**: <100ms ✅ (target: <500ms)
- **ETL Pipeline**: <25 minutes for 260K rows ✅
- **Quality Analysis**: ~10 seconds per comment (~10 hours for 6,319 comments)

### Resource Requirements
- **Disk Space**: 5GB minimum (database + Docker images)
- **Memory**: 8GB RAM recommended (4GB minimum)
- **CPU**: 4 cores recommended (2 cores minimum for LLM analysis)

### Current Capacity
- **Tickets**: 10,939 (handles up to 100K+)
- **Comments**: 108,129 (handles up to 1M+)
- **Timesheets**: 141,062 (handles up to 1M+)
- **Quality Analysis**: 6,319 (limited by LLM processing time)

### Scaling Limits
- **Database**: Vertical scaling (PostgreSQL can handle millions of rows)
- **Grafana**: Vertical scaling (dashboard rendering, not data storage)
- **ETL Pipeline**: Vertical scaling (single-machine batch processing)
- **Bottleneck**: Quality analysis (10 sec/comment = 300 comments/hour)

### Scaling Strategy
- **Short-term**: Increase batch size for quality analysis
- **Medium-term**: GPU acceleration for LLM inference
- **Long-term**: Distributed processing (Spark/Dask) for ETL

---

## Security Considerations

### Authentication

**PostgreSQL**:
- **Method**: Username/password authentication
- **Storage**: .env file (gitignored)
- **Credentials**: `POSTGRES_USER`, `POSTGRES_PASSWORD`
- **Access**: Only via Docker network (not exposed to host)

**Grafana**:
- **Method**: Username/password (admin account)
- **Storage**: .env file (gitignored)
- **Credentials**: `GRAFANA_ADMIN_PASSWORD`
- **Access**: HTTP on localhost:3000 (not exposed externally)

**Ollama**:
- **Method**: No authentication (localhost only)
- **Access**: HTTP on localhost:11434 (not exposed externally)

### Network Security

**Exposed Ports**:
- `3000` - Grafana UI (localhost only)
- `5432` - PostgreSQL (Docker network only, not exposed to host)
- `11434` - Ollama (localhost only)

**Firewall Rules**:
- None required (all services localhost/Docker network)

**Encryption**:
- None (trusted local environment)
- For production: Enable SSL/TLS for PostgreSQL and Grafana

### Secrets Management

**Storage**: `.env` file (gitignored)
**Rotation**: Manual (no automated rotation)
**Access Control**: File system permissions (600 - owner read/write only)

**Example .env**:
```bash
POSTGRES_USER=servicedesk_user
POSTGRES_PASSWORD=<secure-password>
GRAFANA_ADMIN_PASSWORD=<secure-password>
```

---

## Related Documentation

### Architecture Documentation
- **Database Schema**: [SERVICEDESK_DATABASE_SCHEMA.md](../../claude/data/SERVICEDESK_DATABASE_SCHEMA.md) - Complete 7-table schema
- **ADRs**: See [ADRs/](ADRs/) directory
  - [ADR-001: PostgreSQL Docker Container](ADRs/001-postgres-docker.md)
  - [ADR-002: Grafana Visualization Platform](ADRs/002-grafana-visualization.md)

### Implementation Documentation
- **Dashboard Design**: [SERVICEDESK_DASHBOARD_PHASE_2_COMPLETE.md](../../claude/data/SERVICEDESK_DASHBOARD_PHASE_2_COMPLETE.md)
- **Quality Analysis**: [SERVICEDESK_QUALITY_COMPLETE.md](../../claude/data/SERVICEDESK_QUALITY_COMPLETE.md)
- **Metrics Catalog**: [SERVICEDESK_METRICS_CATALOG.md](../../claude/data/SERVICEDESK_METRICS_CATALOG.md)
- **ETL Pipeline**: [SERVICEDESK_ETL_V2_FINAL_STATUS.md](../../claude/data/SERVICEDESK_ETL_V2_FINAL_STATUS.md)

### Operational Documentation
- **ETL Runbook**: [SERVICEDESK_ETL_OPERATIONAL_RUNBOOK.md](../../claude/data/SERVICEDESK_ETL_OPERATIONAL_RUNBOOK.md)
- **Monitoring Guide**: [SERVICEDESK_ETL_MONITORING_GUIDE.md](../../claude/data/SERVICEDESK_ETL_MONITORING_GUIDE.md)
- **Best Practices**: [SERVICEDESK_ETL_BEST_PRACTICES.md](../../claude/data/SERVICEDESK_ETL_BEST_PRACTICES.md)

---

**Last Review**: 2025-10-21
**Next Review**: 2026-01-21 (Quarterly)
**Reviewers**: Naythan Dawe, Maia System
