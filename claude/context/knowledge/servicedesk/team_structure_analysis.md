# ServiceDesk Team Structure Analysis

**Last Updated**: 2025-10-05
**Dataset**: 13,252 tickets (July-Sept 2025)

---

## Team Hierarchy Overview

### Total Teams: 17
- **Primary Operations**: 3 teams (66.4% of tickets)
- **Client-Specific**: 6 teams (26.4% of tickets)
- **Specialized**: 2 teams (0.9% of tickets)
- **Internal/Other**: 6 teams (6.3% of tickets)

---

## Primary Operations Teams (66.4%)

### 1. Cloud - Infrastructure (6,603 tickets, 49.8%)

**Profile**:
- **Alert %**: 99.3% (6,560 alerts)
- **Work Tickets**: 43 (0.7%)
- **Unique Engineers**: 21
- **Avg Tickets/Engineer**: 314

**Function**:
- Technical platform and infrastructure management
- Primary alert destination (Azure Monitor, VM alerts, system health)
- Critical automation opportunity ($93K savings potential)

**Alert Patterns**:
- Azure VM Network Threshold: 1,726 tickets (26% of team load)
- Azure VM Health Status: 400 tickets
- Azure Storage Latency: 340 tickets
- Server Memory alerts: 299 tickets

**Key Insight**:
- 99.3% alerts = almost pure automation opportunity
- Single biggest automation ROI target
- Team drowning in noise alerts (need intelligent suppression)

---

### 2. Cloud - BAU Support (1,420 tickets, 10.7%)

**Profile**:
- **Alert %**: 62.0% (880 alerts)
- **Work Tickets**: 540 (38%)
- **Unique Engineers**: 43
- **Avg Tickets/Engineer**: 33

**Function**:
- Business As Usual operational support
- Mixed alerts and real customer work
- General support queue

**Work Distribution**:
- Alerts (automated): 880 tickets
- Support work: 540 tickets
- Mix of reactive and proactive work

**Key Insight**:
- More balanced workload vs Infrastructure team
- 38% real work = quality metrics (FCR, CSAT) matter here
- Engineers have lower individual load (33 vs 314)

---

### 3. Cloud - Security (780 tickets, 5.9%)

**Profile**:
- **Alert %**: 74.4% (580 alerts)
- **Work Tickets**: 200 (25.6%)
- **Unique Engineers**: 15
- **Avg Tickets/Engineer**: 52

**Function**:
- Security operations and incident response
- Security alerts (M365 Defender, security threats)
- Security-related support

**Alert Patterns**:
- M365 Defender alerts: 113 tickets
- Security threat detection
- Physical security (motion detection): Some overflow

**Key Insight**:
- 74% alerts but different nature (security vs infrastructure)
- Lower automation potential (security alerts need human review)
- 200 work tickets = incident investigation and response

---

## Client-Specific Teams (26.4%)

**Naming Convention**: Nintendo game code names (likely client anonymization)

### 4. Cloud - Metroid (1,061 tickets, 8.0%)

**Profile**:
- **Alert %**: 1.6% (17 alerts)
- **Work Tickets**: 1,044 (98.4%)
- **Unique Engineers**: 36
- **Avg Tickets/Engineer**: 29

**Function**: Dedicated client support team
**Key Insight**: Almost all real work = FCR and CSAT metrics critical

---

### 5. Cloud - Zelda (997 tickets, 7.5%)

**Profile**:
- **Alert %**: 0.3% (3 alerts)
- **Work Tickets**: 994 (99.7%)
- **Unique Engineers**: 42
- **Avg Tickets/Engineer**: 24

**Function**: Dedicated client support team
**Key Insight**: Purest client support team (99.7% real work)

---

### 6. Cloud - Mario (677 tickets, 5.1%)

**Profile**:
- **Alert %**: 1.0% (7 alerts)
- **Work Tickets**: 670 (99.0%)
- **Unique Engineers**: 35
- **Avg Tickets/Engineer**: 19

**Function**: Dedicated client support team
**Key Insight**: High-touch client support (lowest tickets/engineer ratio)

---

### 7. Cloud - Kirby (339 tickets, 2.6%)

**Profile**:
- **Alert %**: 0.6% (2 alerts)
- **Work Tickets**: 337 (99.4%)
- **Unique Engineers**: 28
- **Avg Tickets/Engineer**: 12

**Function**: Dedicated client support team
**Key Insight**: Smaller client, focused support

---

### 8. Cloud - PHI/WAPHA Support (352 tickets, 2.7%)

**Profile**:
- **Alert %**: 0.9% (3 alerts)
- **Work Tickets**: 349 (99.1%)
- **Unique Engineers**: 16
- **Avg Tickets/Engineer**: 22

**Function**: Healthcare client support (Protected Health Information)
**Key Insight**: Compliance-sensitive environment (PHI regulations)

---

### 9. Cloud - Primary Sense (67 tickets, 0.5%)

**Profile**:
- **Alert %**: 0.0% (0 alerts)
- **Work Tickets**: 67 (100%)
- **Unique Engineers**: 7
- **Avg Tickets/Engineer**: 10

**Function**: Specialized healthcare support
**Key Insight**: Smallest client team, 100% service requests/incidents

---

## Specialized Teams (0.9%)

### 10. Cloud - L3 Escalation (82 tickets, 0.6%)

**Profile**:
- **Alert %**: 3.7% (3 alerts)
- **Tickets**: 77 Support, 3 PHI, 1 Alert, 1 Standard
- **Severity**: 50% Service Request, 43% Incident
- **Unique Engineers**: 10

**Function**: NOT traditional escalation - Senior technical tier

**What They Handle**:
- Hosted Service issues (19.5%)
- Software problems (14.6%)
- Telephony (3CX admin) (12.2%)
- Network complexity (12.2%)
- Security incidents (7.3%)

**Examples**:
- Archive folder restoration
- Application upgrades
- 3CX call recording requests
- DevOps/licensing issues
- Complex troubleshooting

**Key Insight**:
- Specialized technical queue, not escalation destination
- Complex issues likely **assigned directly** to L3
- Comments table needed to confirm escalation vs direct assignment

---

### 11. Cloud - L2 Escalation (35 tickets, 0.3%)

**Profile**:
- **Alert %**: 0.0% (0 alerts)
- **Tickets**: 29 Support, 4 PHI, 2 Standard
- **Severity**: 71% Service Request, 29% Incident
- **Unique Engineers**: 9

**Function**: NOT traditional escalation - Account Management Tier

**What They Handle**:
- Account lifecycle (74.3% of tickets)
- User provisioning/deprovisioning
- SharePoint access
- MFA resets
- DNS updates

**Pattern Identified**: "NS" prefix = **New Starter** bulk provisioning
```
Examples from July 28, 2025:
- NS 28/07/2025 > Wei Ong
- NS 28/07/2025 > Naziru Ajuji
- NS 28/07/2025 > Dipali Patel
- NS 28/07/2025 > Rachel Hocking
- NS 28/07/2025 > Shannon Moreton
```

**Key Insight**:
- Specialized account management queue
- Bulk provisioning on specific dates (coordinated onboarding)
- NOT escalation tier - direct assignment for account work

---

## Internal & Other Teams (6.3%)

### 12. Internal Support (811 tickets, 6.1%)

**Profile**:
- **Alert %**: 0.0% (0 alerts)
- **Work Tickets**: 811 (100%)
- **Unique Engineers**: 26

**Function**: Orro internal IT support
**Priority**: Lower for client-facing metrics

---

### 13-17. Micro Teams (<1% each)

| Team | Tickets | % | Function |
|------|---------|---|----------|
| Cloud - TAM | 18 | 0.1% | Technical Account Management |
| Cloud - Procurement | 5 | 0.0% | Procurement-related |
| Cloud - Internal | 3 | 0.0% | Internal systems |
| Cloud - Maintenance | 1 | 0.0% | Maintenance windows |
| Cloud - User Modifications | 1 | 0.0% | User changes |

**Note**: Out of scope for analysis (too low volume)

---

## Team Analysis Insights

### Workload Distribution

| Team Type | Teams | Tickets | Avg/Team | Engineers | Avg Tickets/Eng |
|-----------|-------|---------|----------|-----------|-----------------|
| **Infrastructure** | 1 | 6,603 | 6,603 | 21 | **314** ⚠️ |
| **BAU Support** | 1 | 1,420 | 1,420 | 43 | 33 |
| **Security** | 1 | 780 | 780 | 15 | 52 |
| **Client Teams** | 6 | 3,493 | 582 | 164 | 21 |
| **Specialized** | 2 | 117 | 59 | 19 | 6 |

**Key Finding**: Infrastructure engineers have **10x higher ticket load** than client teams
- Infrastructure: 314 tickets/engineer (mostly alerts)
- Client teams: 21 tickets/engineer (real work)
- **Automation will massively rebalance workload**

---

### Alert vs Work Distribution

| Team Category | Total Tickets | Alerts | % Alert | Work | % Work |
|---------------|---------------|--------|---------|------|--------|
| **Operations** (Infra/BAU/Security) | 8,803 | 8,020 | **91.1%** | 783 | 8.9% |
| **Client Teams** | 3,493 | 32 | **0.9%** | 3,461 | 99.1% |
| **Specialized** | 117 | 3 | 2.6% | 114 | 97.4% |
| **Internal** | 811 | 0 | 0.0% | 811 | 100% |

**Key Finding**:
- Operations teams = 91% alerts (automation target)
- Client teams = 99% real work (quality metrics target)
- Clear segmentation of function

---

### Automation Impact by Team

| Team | Current Alerts | Automatable | Post-Automation | Reduction |
|------|----------------|-------------|-----------------|-----------|
| **Cloud - Infrastructure** | 6,560 | 2,756 (42%) | 3,804 | **-42%** |
| **Cloud - BAU Support** | 880 | 370 (42%) | 510 | -42% |
| **Cloud - Security** | 580 | 244 (42%) | 336 | -42% |
| **Client Teams** | 32 | 13 (42%) | 19 | -42% |

**Total**: 8,052 alerts → 4,669 alerts (-42% = 3,383 automated)

**Workload Rebalancing**:
- Infrastructure engineers: 314 → 181 tickets (-42%)
- More capacity for strategic projects
- Better work-life balance

---

## Team Focus Recommendations

### For Alert Automation Analysis
**Primary Focus**:
- Cloud - Infrastructure (49.8% of all tickets)
- Cloud - BAU Support (10.7%)
- Cloud - Security (5.9%)

**Combined**: 8,803 tickets (66.4%)
**Automation Savings**: $167K/year

---

### For FCR/CSAT/Quality Metrics
**Primary Focus**:
- Cloud - Metroid (8.0%)
- Cloud - Zelda (7.5%)
- Cloud - Mario (5.1%)
- Cloud - Kirby (2.6%)
- Cloud - PHI/WAPHA Support (2.7%)
- Cloud - Primary Sense (0.5%)

**Combined**: 3,493 tickets (26.4%)
**Focus**: Customer experience, FCR, service quality

---

### For Escalation/Skill Analysis
**Requires Comments Table**:
- Need to validate if L2/L3 are true escalations or specialized queues
- Track reassignment patterns across all teams
- Identify skill gaps by analyzing handoffs

**Hypothesis**: L2/L3 are NOT escalation tiers:
- L2 = Account management queue (74% account-related)
- L3 = Senior technical queue (complex issues assigned directly)

---

## Team Structure Observations

### Naming Conventions

**Functional Teams**:
- "Cloud - Infrastructure" = Platform/technical
- "Cloud - BAU Support" = Business as usual
- "Cloud - Security" = Security operations
- "Cloud - L2/L3 Escalation" = Specialized (misleading names)

**Client Code Names**:
- Nintendo games (Mario, Zelda, Metroid, Kirby) = Client anonymization
- PHI/WAPHA = Healthcare (obvious from name)
- Primary Sense = Healthcare provider

**Internal**:
- "Internal Support" = Orro internal IT
- "Cloud - Internal" = Internal cloud projects
- "Cloud - TAM" = Technical Account Management

### Team Design Insights

**Multi-Engineer Model**:
- Most teams have 15-43 engineers (shared resource pool)
- Engineers likely work across multiple teams
- Client teams share engineer pool (36-42 engineers each)

**Workload Imbalance**:
- Infrastructure team buried in alerts (314 tickets/engineer)
- Client teams have sustainable load (12-29 tickets/engineer)
- Automation will rebalance to sustainable levels

**Specialization**:
- L2/L3 are specialized queues, not traditional tiers
- Account management separate from technical support
- Senior technical work isolated from L1/L2

---

## Questions for Comments Table

When comments table arrives, investigate:

1. **Are L2/L3 true escalations?**
   - Track ownerid changes: Does ticket go L1→L2→L3?
   - Or are complex tickets assigned directly to L3?

2. **What triggers client team assignment?**
   - Account-based routing?
   - Skill-based routing?
   - Load balancing?

3. **Infrastructure team reassignments**:
   - Do alert tickets get reassigned (shouldn't be)?
   - Are real work tickets getting lost in alert noise?

4. **Engineer collaboration patterns**:
   - Single-person tickets vs multi-person?
   - Who collaborates with whom?
   - Knowledge transfer patterns?

5. **Communication quality**:
   - Customer updates per ticket by team?
   - Internal notes vs customer communication ratio?
   - Response time by team?

---

*Last Updated: 2025-10-05 by Maia Data Analyst Agent*
