# Architecture Documentation Standards - Maia System

## Purpose
Eliminate architecture amnesia and trial-and-error implementations by establishing clear standards for documenting system architecture, deployment topology, and technical decisions.

## Problem Solved
**Without these standards**:
- 10-20 minutes lost per task searching "how does X work?"
- Trial-and-error implementations (5+ attempts to find correct method)
- Breaking changes from unknown dependencies
- Context window waste loading irrelevant documentation

**With these standards**:
- 1-2 minutes to understand system architecture
- First implementation attempt succeeds (known patterns)
- Safe refactoring (dependencies documented)
- Efficient context loading (architecture in one place)

---

## 🚨 **MANDATORY DOCUMENTATION TRIGGERS**

### When to Create ARCHITECTURE.md

Create or update project ARCHITECTURE.md when **ANY** of these occur:

1. ✅ **New Infrastructure Deployed**
   - Docker containers/compose
   - Database servers (PostgreSQL, MySQL, MongoDB, etc.)
   - Web servers (Nginx, Apache, etc.)
   - Message queues (RabbitMQ, Redis, etc.)
   - Any service that runs persistently

2. ✅ **External Service Integration**
   - Third-party APIs (Stripe, Twilio, etc.)
   - External databases
   - SaaS platforms (Grafana Cloud, Datadog, etc.)
   - Authentication providers (OAuth, SAML, etc.)

3. ✅ **Multi-Component Systems**
   - 2+ interacting components
   - Data flows between services
   - Microservices architecture
   - Client-server applications

4. ✅ **Production Deployments**
   - Anything beyond prototype scripts
   - User-facing systems
   - Scheduled/automated processes
   - Critical infrastructure

### When to Create ADR (Architectural Decision Record)

Create ADR when making **ANY** significant technical decision:

1. ✅ **Technology Choices**
   - Why PostgreSQL vs MySQL vs MongoDB?
   - Why Docker vs local installation?
   - Why Grafana vs Tableau vs custom?

2. ✅ **Architecture Patterns**
   - Why monolith vs microservices?
   - Why REST vs GraphQL vs gRPC?
   - Why ETL vs ELT vs streaming?

3. ✅ **Infrastructure Decisions**
   - Why cloud vs on-premise?
   - Why Kubernetes vs Docker Compose?
   - Why managed service vs self-hosted?

4. ✅ **Integration Approaches**
   - Why API vs file-based integration?
   - Why synchronous vs asynchronous?
   - Why direct DB access vs API layer?

---

## 📁 **File Structure Standards**

### Project-Level Architecture Documentation

```
project_root/
├── ARCHITECTURE.md ⭐ MANDATORY for multi-component systems
│   ├── System Topology (what's running where)
│   ├── Deployment Model (how to run it)
│   ├── Data Flow Diagrams (how data moves)
│   ├── Integration Points (how components connect)
│   └── Operational Commands (how to use it)
│
├── ADRs/ ⭐ RECOMMENDED for significant decisions
│   ├── 001-postgres-docker.md
│   ├── 002-grafana-choice.md
│   └── 003-etl-pipeline-design.md
│
├── docker-compose.yml (if using Docker)
├── README.md (project overview)
└── [implementation files]
```

### Global Architecture Registry

```
claude/context/core/
├── architecture_standards.md (this file)
└── active_deployments.md ⭐ Global registry of running systems
```

---

## 📝 **ARCHITECTURE.md Template**

### Required Sections

```markdown
# [Project Name] - System Architecture

**Status**: [Development / Testing / Production]
**Last Updated**: YYYY-MM-DD
**Primary Maintainer**: [Name/Team]

---

## Overview
[1-2 sentence description of what this system does]

## Deployment Model

### Runtime Environment
- **Platform**: [Docker / Local / Cloud / Hybrid]
- **Operating System**: [macOS / Linux / Windows / Container]
- **Dependencies**: [List critical dependencies]

### Services/Containers
| Service | Container/Process | Port | Purpose |
|---------|------------------|------|---------|
| PostgreSQL | servicedesk-postgres | 5432 | Data storage |
| Grafana | grafana | 3000 | Visualization |

### Configuration Files
- `docker-compose.yml` - Container orchestration
- `.env` - Environment variables (secrets)
- `config/*.yml` - Service configurations

---

## System Topology

### Architecture Diagram
```
[ASCII or Mermaid diagram showing components and connections]

Example:
┌─────────┐      ┌──────────┐      ┌───────────┐
│  XLSX   │─────>│ ETL      │─────>│PostgreSQL │
│  Files  │      │ Pipeline │      │ (Docker)  │
└─────────┘      └──────────┘      └─────┬─────┘
                                         │
                                         v
                                   ┌─────────┐
                                   │ Grafana │
                                   │ (Docker)│
                                   └─────────┘
```

### Component Descriptions
**[Component Name]**:
- **Purpose**: What it does
- **Technology**: Implementation details
- **Dependencies**: What it needs
- **Scalability**: Horizontal/vertical limits

---

## Data Flow

### Primary Data Flows
1. **[Flow Name]**: Source → Processing → Destination
   - **Trigger**: [Event/Schedule/Manual]
   - **Frequency**: [Real-time/Hourly/Daily/On-demand]
   - **Volume**: [Records per execution]
   - **SLA**: [Performance requirements]

### Data Transformations
- **Input Format**: [CSV/JSON/XML/Database]
- **Validation**: [Rules applied]
- **Enrichment**: [Data added]
- **Output Format**: [Final format]

---

## Integration Points

### [Component A] → [Component B]

**Connection Method**: [docker exec / HTTP API / Database / File / Message Queue]

**Implementation**:
```bash
# Example: PostgreSQL Write
docker exec servicedesk-postgres psql -U servicedesk_user -d servicedesk -c "INSERT..."
```

**Authentication**:
- Method: [Password / Token / Certificate / None]
- Location: [.env file / Secrets manager / Hardcoded]

**Error Handling**:
- Retry Strategy: [Exponential backoff / Fixed delay / No retry]
- Fallback: [Alternative method / Alert only / Fail gracefully]

**NOT Supported** ⚠️:
- [Anti-patterns that don't work]
- Example: Direct psycopg2 connection (database in isolated container)

---

## Operational Commands

### Start System
```bash
cd infrastructure/[project]
docker-compose up -d
```

### Stop System
```bash
docker-compose down
```

### Access Components
```bash
# PostgreSQL
docker exec -it servicedesk-postgres psql -U servicedesk_user -d servicedesk

# Grafana
open http://localhost:3000
```

### Health Checks
```bash
# Verify containers running
docker ps | grep servicedesk

# Check database connectivity
docker exec servicedesk-postgres pg_isready
```

### Backup/Restore
```bash
# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh backup-YYYYMMDD.tar.gz
```

---

## Common Issues & Solutions

### Issue: [Problem Description]
**Symptoms**: [What you see]
**Cause**: [Root cause]
**Solution**:
```bash
[Fix commands]
```

### Issue: Can't Connect to Database
**Symptoms**: Connection refused, timeout errors
**Cause**: Database runs in isolated Docker container
**Solution**: Use `docker exec` commands, NOT direct connections
```bash
# ❌ Wrong (direct connection fails)
psql -h localhost -U servicedesk_user

# ✅ Correct (via container)
docker exec servicedesk-postgres psql -U servicedesk_user
```

---

## Performance Characteristics

### Expected Performance
- **Database Queries**: <100ms (P95)
- **Dashboard Load Time**: <2 seconds
- **ETL Pipeline**: <25 minutes for 260K rows

### Resource Requirements
- **Disk Space**: [Minimum GB required]
- **Memory**: [Minimum RAM required]
- **CPU**: [Minimum cores required]

### Scaling Limits
- **Current Capacity**: [Max users/requests/data]
- **Scaling Strategy**: [Vertical/Horizontal]
- **Bottlenecks**: [Known limitations]

---

## Security Considerations

### Authentication
- **Database**: Username/password in .env
- **Web UI**: [Auth method]
- **APIs**: [Auth method]

### Network Security
- **Exposed Ports**: [List public ports]
- **Firewall Rules**: [Required rules]
- **Encryption**: [TLS/SSL configuration]

### Secrets Management
- **Storage**: .env files (gitignored)
- **Rotation**: [How/when secrets are rotated]
- **Access Control**: [Who can access secrets]

---

## Related Documentation
- **ADRs**: See [ADRs/](ADRs/) directory
- **Database Schema**: [Link to schema doc]
- **API Documentation**: [Link to API docs]
- **Deployment Guide**: [Link to deployment docs]

---

**Last Review**: YYYY-MM-DD
**Next Review**: [Quarterly / After major changes]
```

---

## 📋 **ADR (Architectural Decision Record) Template**

### File Naming Convention
`ADRs/NNN-short-title.md`

Examples:
- `ADRs/001-postgres-docker.md`
- `ADRs/002-grafana-visualization.md`
- `ADRs/003-etl-pipeline-design.md`

### ADR Template

```markdown
# ADR-NNN: [Decision Title]

**Status**: [Proposed / Accepted / Rejected / Superseded / Deprecated]
**Date**: YYYY-MM-DD
**Deciders**: [Names of people involved in decision]
**Technical Story**: [Ticket/issue reference if applicable]

---

## Context

[Describe the problem or situation requiring a decision]

**Background**:
- Current state: [What exists now]
- Problem: [What needs to be solved]
- Constraints: [Technical/business/time limitations]
- Requirements: [What the solution must achieve]

---

## Decision

[State the decision clearly and concisely]

**We will**: [Chosen approach]

**Implementation approach**:
- [Key implementation detail 1]
- [Key implementation detail 2]
- [Key implementation detail 3]

---

## Alternatives Considered

### Option A: [Alternative Name]
**Pros**:
- ✅ [Benefit 1]
- ✅ [Benefit 2]

**Cons**:
- ❌ [Drawback 1]
- ❌ [Drawback 2]

**Why rejected**: [Reasoning]

### Option B: [Alternative Name]
[Same structure]

### Option C: [Alternative Name]
[Same structure]

---

## Rationale

[Detailed explanation of why the decision was made]

**Key factors**:
1. [Factor 1 with explanation]
2. [Factor 2 with explanation]
3. [Factor 3 with explanation]

**Decision criteria**:
- [Criterion 1]: Decision scores [High/Medium/Low]
- [Criterion 2]: Decision scores [High/Medium/Low]

---

## Consequences

### Positive Consequences
- ✅ [Benefit 1 with impact]
- ✅ [Benefit 2 with impact]
- ✅ [Benefit 3 with impact]

### Negative Consequences / Tradeoffs
- ❌ [Tradeoff 1 with mitigation strategy]
- ❌ [Tradeoff 2 with mitigation strategy]

### Risks
- ⚠️ [Risk 1]: [Mitigation]
- ⚠️ [Risk 2]: [Mitigation]

---

## Implementation Notes

### Required Changes
- [Change 1 in component X]
- [Change 2 in component Y]

### Integration Points Affected
- [Integration point 1]: [How it changes]
- [Integration point 2]: [How it changes]

### Operational Impact
- **Deployment**: [Changes to deployment process]
- **Monitoring**: [New metrics/alerts needed]
- **Maintenance**: [Ongoing maintenance requirements]

---

## Validation

### How We'll Know This Works
- [Success metric 1]: [Target value]
- [Success metric 2]: [Target value]

### Rollback Plan
[If this decision doesn't work out, how do we revert?]

---

## Related Decisions
- ADR-XXX: [Related decision that influenced this]
- Supersedes: ADR-YYY (if applicable)
- Superseded by: ADR-ZZZ (if applicable)

---

## References
- [Link 1]: [Description]
- [Link 2]: [Description]
- [Documentation]: [Description]

---

**Review Date**: [When this decision should be reviewed]
**Reviewers**: [Who should review this periodically]
```

---

## 🌍 **Active Deployments Registry**

### File: `claude/context/core/active_deployments.md`

**Purpose**: Global registry of all running systems across Maia environment

**Template**:
```markdown
# Active Deployments - Maia System Registry

**Last Updated**: YYYY-MM-DD
**Purpose**: Central registry of all deployed systems and services

---

## Production Systems

### [System Name]
- **Status**: Active / Maintenance / Deprecated
- **Architecture Doc**: [Link to ARCHITECTURE.md]
- **Access**: [URL / Command / Connection method]
- **Owner**: [Primary maintainer]
- **Last Deployed**: YYYY-MM-DD

---

## Development/Staging Systems

[Same structure as production]

---

## Scheduled Jobs/Automation

### [Job Name]
- **Schedule**: [Cron expression / Frequency]
- **Purpose**: [What it does]
- **Monitoring**: [How to check status]
- **Last Run**: YYYY-MM-DD HH:MM

---

## External Integrations

### [Service Name]
- **Type**: API / Database / SaaS / etc.
- **Authentication**: [Method]
- **Rate Limits**: [If applicable]
- **Documentation**: [Link]
```

---

## 🔄 **Integration with Existing Workflows**

### Documentation Workflow Updates

Add to `documentation_workflow.md` checklist:

```markdown
## DOCUMENTATION CHECKLIST

### ALWAYS UPDATE THESE FILES:
- [ ] SYSTEM_STATE.md
- [ ] capability_index.md
- [ ] claude/context/tools/available.md
- [ ] **ARCHITECTURE.md (if infrastructure/deployment changes)** ⭐ NEW
- [ ] **active_deployments.md (if new system deployed)** ⭐ NEW
- [ ] Relevant command/agent documentation

### CREATE ADR IF:
- [ ] **Made significant technical decision** ⭐ NEW
- [ ] **Chose one technology over alternatives** ⭐ NEW
- [ ] **Designed new architecture pattern** ⭐ NEW
```

### TDD Development Protocol Updates

Add to Phase 1 (Requirements Discovery):

```markdown
**Phase 1: Requirements Discovery**

0. **Pre-Discovery: Architecture Review** ⭐ NEW
   - Read project ARCHITECTURE.md if it exists
   - Understand deployment model and integration points
   - Review relevant ADRs for context
   - Identify architectural constraints

1. **Core Purpose Discovery**
   [existing content]
```

---

## 📊 **Success Metrics**

### Quantitative Metrics
- **Architecture lookup time**: <2 minutes (vs 10-20 minutes previously)
- **First implementation success rate**: >90% (vs <20% trial-and-error)
- **Breaking change incidents**: 0 (from unknown dependencies)

### Qualitative Metrics
- New contributors understand system without extensive guidance
- Confident refactoring (dependencies known)
- No "how does X work?" searches during development

### ROI Calculation
- **Time saved**: 8-18 min/task × 20 tasks/month = 2.7-6 hours/month
- **Investment**: 2-3 hours initial + 15 min/project ongoing
- **Payback**: First month

---

## 🎯 **Enforcement Mechanisms**

### Automated Checks (Future)
- Pre-commit hook: Detect infrastructure changes without ARCHITECTURE.md update
- CI/CD gate: Require ADR for technology changes
- Documentation linter: Validate ARCHITECTURE.md structure

### Review Checklist
When reviewing changes:
- [ ] Does this add/modify infrastructure? → ARCHITECTURE.md updated?
- [ ] Does this make a technical choice? → ADR created?
- [ ] Does this deploy a new system? → active_deployments.md updated?

---

## 📚 **Examples**

### Good Architecture Documentation
See: `infrastructure/servicedesk-dashboard/ARCHITECTURE.md`
- Complete deployment model (Docker containers listed)
- Clear integration points (docker exec vs direct connection)
- Operational commands (start/stop/access)
- Common issues documented

### Good ADR
See: `infrastructure/servicedesk-dashboard/ADRs/001-postgres-docker.md`
- Clear problem statement
- 3 alternatives considered with pros/cons
- Rationale for decision
- Consequences documented (both positive and negative)

---

## 🔄 **Maintenance**

### Quarterly Review
- Review all ARCHITECTURE.md files for accuracy
- Update ADRs marked as "Proposed" to final status
- Archive deprecated ADRs
- Update active_deployments.md

### When to Update
- **ARCHITECTURE.md**: Every infrastructure change
- **ADRs**: When decisions change or new context emerges
- **active_deployments.md**: When systems are deployed/decommissioned

---

## 📖 **References**

### External Standards
- [Michael Nygard's ADR template](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
- [C4 Model for Architecture](https://c4model.com/)
- [arc42 Architecture Documentation](https://arc42.org/)

### Internal Documents
- `documentation_workflow.md` - General documentation standards
- `documentation_standards.md` - Component-level documentation
- `tdd_development_protocol.md` - Development workflow

---

**Status**: ✅ Production Standard - Mandatory Enforcement
**Created**: 2025-10-21
**Last Updated**: 2025-10-21
**Owner**: Maia System
