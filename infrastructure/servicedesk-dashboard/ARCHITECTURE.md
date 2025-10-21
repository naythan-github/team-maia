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
       │ 4 Dashboards:
       │ - Executive (5 KPIs)
       │ - Operations (13 metrics)
       │ - Quality (6 metrics)
       │ - Team Performance (8 metrics)
       └──────────┘

Access:
- Grafana UI: http://localhost:3000
- Database: docker exec (see Operational Commands)
```

### Component Descriptions

**PostgreSQL Container (servicedesk-postgres)**:
- **Purpose**: Data warehouse for ticket, comment, timesheet, and quality data
- **Technology**: PostgreSQL 15 in Docker container
- **Dependencies**: None (isolated container)
- **Scalability**: Vertical (currently handles 266K rows, can scale to millions)
- **Persistence**: Docker volume `servicedesk_postgres_data`

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

#### 1. **Quarterly Data Import**: XLSX → PostgreSQL
- **Trigger**: Manual (quarterly ServiceDesk export)
- **Frequency**: Quarterly (or on-demand for updates)
- **Volume**: ~10K tickets, ~100K comments, ~140K timesheets per import
- **SLA**: <2 hours end-to-end (including quality analysis)

**Flow**:
```
1. Export XLSX from ServiceDesk system (manual)
2. Run incremental_import_servicedesk.py
   → Loads XLSX to SQLite (servicedesk_tickets.db)
   → Runs servicedesk_etl_validator.py (40 quality rules)
   → Runs servicedesk_quality_scorer.py (quality metrics)
3. Run servicedesk_etl_data_cleaner_enhanced.py
   → Date standardization (DD/MM/YYYY → YYYY-MM-DD)
   → Empty string → NULL conversion
4. Run servicedesk_quality_analyzer_postgres.py
   → LLM analysis of comments (10 sec/comment)
   → Writes to comment_quality table
5. Run migrate_sqlite_to_postgres_enhanced.py
   → SQLite → PostgreSQL migration
   → Canary deployment (10% validation)
   → Blue-green schema cutover
6. Grafana dashboards auto-refresh from PostgreSQL
```

#### 2. **Dashboard Refresh**: PostgreSQL → Grafana
- **Trigger**: Automatic (Grafana query refresh)
- **Frequency**: Hourly (real-time metrics), Daily (quality metrics)
- **Volume**: 23 metrics across 4 dashboards
- **SLA**: <2 seconds dashboard load, <100ms per query

**Flow**:
```
1. User opens Grafana dashboard (http://localhost:3000)
2. Grafana executes SQL queries against PostgreSQL
3. Results rendered in panels (KPI cards, charts, tables)
4. Auto-refresh every hour (configurable per dashboard)
```

#### 3. **Comment Quality Analysis**: Comments → LLM → PostgreSQL
- **Trigger**: Manual (on-demand via servicedesk_quality_analyzer_postgres.py)
- **Frequency**: After each data import
- **Volume**: 6,319 human comments (filtered: user_name != 'brian')
- **SLA**: ~10 hours for full analysis (10 sec/comment)

**Flow**:
```
1. servicedesk_quality_analyzer_postgres.py reads comments from PostgreSQL
2. Filters system user "brian" (66,046 automation comments)
3. Sends to Ollama (llama3.1:8b) for analysis
4. LLM returns quality scores (professionalism, clarity, empathy, actionability)
5. Writes to comment_quality table in PostgreSQL
6. Grafana Quality Dashboard reflects new data immediately
```

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
