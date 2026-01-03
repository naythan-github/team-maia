# Architecture Documentation Standards v2.3 (Compressed)

**Purpose**: Eliminate architecture amnesia via clear documentation standards
**Impact**: 10-20 min search → 1-2 min | Trial-and-error → First attempt success

---

## Documentation Triggers

### When to Create ARCHITECTURE.md
- **Infrastructure**: Docker, databases, web servers, message queues
- **Integration**: Third-party APIs, external services, auth providers
- **Multi-Component**: 2+ interacting components, microservices
- **Production**: User-facing, scheduled, critical systems

### When to Create ADR
- **Technology Choices**: Why PostgreSQL vs MySQL? Docker vs local?
- **Architecture Patterns**: Monolith vs microservices? REST vs GraphQL?
- **Infrastructure**: Cloud vs on-prem? Managed vs self-hosted?
- **Integration**: API vs file-based? Sync vs async?

---

## File Structure

```
project_root/
├── ARCHITECTURE.md        # System topology, deployment, data flow
├── ADRs/                  # Decision records (001-postgres.md)
├── docker-compose.yml     # Container config
└── README.md              # Overview

claude/context/core/
├── architecture_standards.md  # This file
└── active_deployments.md      # Global registry
```

---

## ARCHITECTURE.md Template

```markdown
# [Project] - System Architecture

**Status**: [Development/Testing/Production] | **Updated**: YYYY-MM-DD

## Overview
[1-2 sentence description]

## Deployment Model

### Services
| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| PostgreSQL | db-postgres | 5432 | Storage |
| Grafana | grafana | 3000 | Viz |

### Configuration
- `docker-compose.yml` - Orchestration
- `.env` - Secrets (gitignored)

## System Topology

```
┌─────────┐     ┌─────────┐     ┌───────────┐
│  Input  │────>│ Process │────>│  Storage  │
└─────────┘     └─────────┘     └─────┬─────┘
                                      v
                                ┌─────────┐
                                │ Output  │
                                └─────────┘
```

## Data Flow
1. **[Flow Name]**: Source → Processing → Destination
   - **Trigger**: Event/Schedule | **Frequency**: Daily | **SLA**: <5s

## Integration Points

### [Component A] → [Component B]
**Method**: docker exec / HTTP API / Database
**Auth**: Password in .env | **Retry**: Exponential backoff
**NOT Supported**: [Anti-patterns that don't work]

## Operational Commands
```bash
# Start/Stop
docker-compose up -d && docker-compose down

# Access
docker exec -it db-postgres psql -U user -d db
open http://localhost:3000

# Health Check
docker ps | grep project && docker exec db-postgres pg_isready
```

## Common Issues
### Issue: Can't Connect to Database
**Cause**: Database in isolated container
**Solution**: Use `docker exec`, NOT direct connection

## Performance
- **Queries**: <100ms P95 | **Dashboard**: <2s | **ETL**: <25min/260K rows
- **Resources**: Disk [X GB] | Memory [X GB] | CPU [X cores]

## Security
- **Auth**: DB password in .env, Web [method], API [method]
- **Secrets**: .env files (gitignored), rotate [schedule]
```

---

## ADR Template

**File**: `ADRs/NNN-short-title.md`

```markdown
# ADR-NNN: [Decision Title]

**Status**: Proposed/Accepted/Rejected | **Date**: YYYY-MM-DD

## Context
[Problem requiring decision]
- Current state | Problem | Constraints | Requirements

## Decision
**We will**: [Chosen approach]
- Implementation detail 1
- Implementation detail 2

## Alternatives Considered

### Option A
✅ Benefit 1, ✅ Benefit 2 | ❌ Drawback 1 | **Rejected**: [reason]

### Option B
[Same structure]

## Consequences
✅ Positive 1, ✅ Positive 2 | ❌ Tradeoff 1 (mitigation) | ⚠️ Risk 1 (mitigation)

## Implementation Notes
- Required changes | Integration points affected | Operational impact

## Validation
- Success metric 1: [target] | Rollback plan: [method]
```

---

## Active Deployments Registry

**File**: `claude/context/core/active_deployments.md`

```markdown
# Active Deployments

## Production Systems
### [System]
- **Status**: Active | **Doc**: [ARCHITECTURE.md link]
- **Access**: [URL/Command] | **Owner**: [name] | **Deployed**: YYYY-MM-DD

## Scheduled Jobs
### [Job]
- **Schedule**: [cron] | **Purpose**: [what] | **Last Run**: YYYY-MM-DD
```

---

## Review Checklist

When reviewing changes:
- [ ] Infrastructure change? → ARCHITECTURE.md updated?
- [ ] Technical choice? → ADR created?
- [ ] New system? → active_deployments.md updated?

---

## Success Metrics
- Architecture lookup: <2 min (vs 10-20 min)
- First implementation success: >90% (vs <20%)
- Breaking change incidents: 0

---

*v2.3 | 663→~200 lines (~70% reduction) | Templates preserved*
