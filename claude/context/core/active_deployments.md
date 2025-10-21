# Active Deployments - Maia System Registry

**Last Updated**: 2025-10-21
**Purpose**: Central registry of all deployed systems and services across Maia environment

---

## Production Systems

### ServiceDesk Dashboard
- **Status**: ✅ Active (Production)
- **Architecture Doc**: [infrastructure/servicedesk-dashboard/ARCHITECTURE.md](../../infrastructure/servicedesk-dashboard/ARCHITECTURE.md)
- **Access**: http://localhost:3000 (Grafana UI)
- **Database**: `docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk`
- **Owner**: Naythan Dawe
- **Last Deployed**: 2025-10-19
- **Components**:
  - PostgreSQL 15 (servicedesk-postgres:5432)
  - Grafana 10.2.0 (localhost:3000)
- **Purpose**: Real-time analytics dashboards for ServiceDesk operations (23 metrics, 4 dashboards)
- **Dependencies**: Docker Desktop
- **Health Check**: `docker ps | grep servicedesk`

---

## Development/Staging Systems

None currently deployed.

---

## Scheduled Jobs/Automation

### ServiceDesk Data Import
- **Schedule**: On-demand (quarterly or as needed)
- **Purpose**: Import XLSX exports from ServiceDesk system to PostgreSQL
- **Command**: `python3 claude/tools/sre/incremental_import_servicedesk.py`
- **Monitoring**: Check `import_metadata` table for last import timestamp
- **Last Run**: 2025-10-19
- **Dependencies**:
  - servicedesk-postgres container running
  - XLSX files in expected location
  - Python 3.9+ with pandas, openpyxl

### ServiceDesk Comment Quality Analysis
- **Schedule**: On-demand (after data imports)
- **Purpose**: LLM-powered analysis of comment quality (6,319 human comments)
- **Command**: `python3 claude/tools/sre/servicedesk_quality_analyzer_postgres.py --sample-size 6319`
- **Monitoring**: Check `comment_quality` table row count
- **Last Run**: 2025-10-20
- **Dependencies**:
  - Ollama running (localhost:11434)
  - llama3.1:8b model downloaded
  - servicedesk-postgres container running
- **Duration**: ~10 hours (10 sec/comment)

---

## External Integrations

### Ollama (Local LLM Inference)
- **Type**: Local HTTP API service
- **Authentication**: None (localhost only)
- **Endpoint**: http://localhost:11434
- **Purpose**: LLM inference for comment quality analysis and code generation
- **Models Used**:
  - llama3.1:8b (comment quality analysis)
  - deepseek-coder:6.7b (code generation)
  - starcoder2:7b (code completion)
- **Rate Limits**: None (local deployment)
- **Documentation**: [Ollama Documentation](https://github.com/ollama/ollama)
- **Health Check**: `curl http://localhost:11434/api/tags`
- **Status**: ✅ Active

---

## Infrastructure Components

### Docker Desktop
- **Version**: Latest stable
- **Purpose**: Container runtime for PostgreSQL, Grafana, and other services
- **Status**: ✅ Active
- **Health Check**: `docker ps`

### PostgreSQL Databases

#### servicedesk-postgres (Docker)
- **Version**: PostgreSQL 15 (Alpine)
- **Container**: servicedesk-postgres
- **Port**: 5432 (Docker network only)
- **Database**: servicedesk
- **Schema**: servicedesk (7 tables, 266K rows)
- **Storage**: Docker volume `servicedesk_postgres_data`
- **Backup Location**: Manual backups via `docker exec ... pg_dump`
- **Status**: ✅ Active
- **Last Backup**: [Manual - no automated backups]

---

## Deprecated Systems

None currently.

---

## System Dependencies Map

```
┌─────────────────┐
│ Docker Desktop  │ (Infrastructure Foundation)
└────────┬────────┘
         │
         ├─> servicedesk-postgres (PostgreSQL 15)
         │   └─> Grafana (dashboards)
         │
         └─> [Future containers]

┌─────────────────┐
│ Ollama          │ (Standalone Service)
└────────┬────────┘
         │
         └─> servicedesk_quality_analyzer_postgres.py
```

---

## Quick Access Commands

### ServiceDesk Dashboard
```bash
# Start system
cd infrastructure/servicedesk-dashboard && docker-compose up -d

# Access Grafana
open http://localhost:3000

# Access PostgreSQL
docker exec -it servicedesk-postgres psql -U servicedesk_user -d servicedesk

# Stop system
cd infrastructure/servicedesk-dashboard && docker-compose down
```

### Ollama
```bash
# Check status
curl http://localhost:11434/api/tags

# List models
ollama list

# Run inference
ollama run llama3.1:8b "Analyze this text..."
```

---

## Maintenance Schedule

### Weekly
- None currently

### Monthly
- Review Docker container logs for errors
- Check disk usage for Docker volumes
- Validate Grafana dashboard functionality

### Quarterly
- ServiceDesk data import (XLSX → PostgreSQL)
- Comment quality re-analysis (if significant new data)
- Review and update dashboards based on stakeholder feedback
- Backup PostgreSQL database

---

## Emergency Contacts

### ServiceDesk Dashboard Issues
- **Primary**: Naythan Dawe
- **Escalation**: Maia System (AI agent)
- **Documentation**: [ARCHITECTURE.md](../../infrastructure/servicedesk-dashboard/ARCHITECTURE.md)

### Infrastructure Issues
- **Primary**: Naythan Dawe
- **Documentation**: Docker Desktop troubleshooting guides

---

## Change Log

| Date | System | Change | Owner |
|------|--------|--------|-------|
| 2025-10-21 | Global | Created active_deployments.md registry | Maia System |
| 2025-10-20 | ServiceDesk | Completed comment quality analysis (6,319 comments) | Maia System |
| 2025-10-19 | ServiceDesk | Deployed 4 Grafana dashboards to production | UI Systems Agent |
| 2025-10-19 | ServiceDesk | Migrated data to PostgreSQL (Phase 1 complete) | SRE Agent |

---

**Review Frequency**: Monthly (or after major deployments)
**Next Review**: 2025-11-21
