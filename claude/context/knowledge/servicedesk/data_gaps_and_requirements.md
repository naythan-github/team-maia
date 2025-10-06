# ServiceDesk Data Gaps & Requirements Analysis

**Last Updated**: 2025-10-05
**Purpose**: Document missing fields and data requirements for complete ServiceDesk analytics

---

## Critical Data Gaps Summary

### 🔴 Priority 1: Cannot Measure Core KPIs

**Missing Fields** (6 fields needed immediately):

1. **First Call Resolution (FCR)** - Boolean
   - Target: 70-80% industry standard
   - Current: CANNOT MEASURE
   - Impact: Core ServiceDesk KPI invisible

2. **Customer Satisfaction (CSAT)** - Integer (1-5 rating)
   - Target: >4.0 industry standard
   - Current: CANNOT MEASURE
   - Impact: No customer experience visibility

3. **Number of Reassignments** - Integer (auto-calculated)
   - Target: <1 avg (minimize ping-pong)
   - Current: CANNOT MEASURE
   - Impact: Cannot identify skill gaps

4. **Number of Users Affected** - Integer
   - Purpose: Impact-based prioritization
   - Current: CANNOT MEASURE
   - Impact: No business impact weighting

5. **Auto-Resolved Flag** - Boolean
   - Purpose: Automation ROI tracking
   - Current: CANNOT MEASURE
   - Impact: Cannot prove $167K automation savings

6. **Billable/Non-Billable** - Boolean (on tickets)
   - Note: Exists in timesheets but not tickets
   - Current: INCOMPLETE
   - Impact: Cannot calculate cost per ticket

---

## Comments Table - CRITICAL REQUEST

### Why Critical
- Unlocks FCR calculation (reassignment tracking via ownerid changes)
- Enables communication quality metrics
- Provides precise response time tracking
- Shows collaboration patterns

### Schema
```sql
commentid          int(19) PRIMARY KEY
ticketid           int(19)              -- Links to tickets table
comments           longtext             -- Comment text
ownerid            varchar(20)          -- User who wrote comment
ownertype          varchar(10)          -- agent/customer distinction
createdtime        datetime             -- Timestamp
visible_to_customer tinyint(1)          -- Public vs internal
type               varchar(20)          -- comments/system/worknotes
```

### Priority Fields (if cannot get all)
🔴 **MUST HAVE**: ticketid, ownerid, createdtime
🟡 **SHOULD HAVE**: ownertype, visible_to_customer, type
🟢 **NICE TO HAVE**: comments (for text analysis - can skip if size issue)

### Expected Volume
- ~13,000 tickets × 6 comments avg = **~80,000 rows**
- With text: 50-100MB CSV
- Without text: 5-10MB CSV

### What It Enables

**FCR Calculation**:
```sql
SELECT
    ticketid,
    COUNT(DISTINCT ownerid) as handlers,
    CASE
        WHEN COUNT(DISTINCT ownerid) = 1 THEN 'FCR - Yes'
        ELSE 'FCR - No'
    END as fcr_status
FROM comments
WHERE ownertype = 'agent'
GROUP BY ticketid
```

**Reassignment Rate**:
```sql
SELECT
    ticketid,
    COUNT(DISTINCT ownerid) - 1 as reassignment_count
FROM comments
WHERE ownertype = 'agent'
GROUP BY ticketid
```

**Communication Quality**:
```sql
SELECT
    ticketid,
    SUM(CASE WHEN visible_to_customer = 1 THEN 1 ELSE 0 END) as customer_updates,
    SUM(CASE WHEN visible_to_customer = 0 THEN 1 ELSE 0 END) as internal_notes
FROM comments
GROUP BY ticketid
```

---

## Missing Fields by Category

### 1. Customer Impact & Satisfaction (7 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Customer Impact Level | Enum | Prioritization (Minor/Moderate/Major/Critical) | 🟡 HIGH |
| Number of Users Affected | Integer | Business impact weighting | 🔴 CRITICAL |
| Business Function Affected | Enum | Finance/HR/Sales/Operations | 🟢 MEDIUM |
| CSAT Rating | Integer (1-5) | Customer satisfaction tracking | 🔴 CRITICAL |
| Customer Feedback | Text | Qualitative feedback | 🟢 MEDIUM |
| VIP Customer Flag | Boolean | Priority handling | 🟢 MEDIUM |
| Revenue Impact | Decimal | Financial impact | 🔵 LOW |

### 2. First Call Resolution (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| First Call Resolution | Boolean | Core KPI (70-80% target) | 🔴 CRITICAL |
| Number of Reassignments | Integer | Efficiency tracking | 🔴 CRITICAL |
| Reassignment Reason | Text | Root cause analysis | 🟡 HIGH |
| Escalation Level | Enum (L1/L2/L3) | Skill gap identification | 🟡 HIGH |
| Ownership Changes Count | Integer | Ping-pong detection | 🔴 CRITICAL |
| Time to First Response | Calculated | Response efficiency | 🟡 HIGH |

*Note: Comments table can provide most of these*

### 3. Problem/Incident Relationships (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Related Problem ID | Integer | Problem management | 🟡 HIGH |
| Recurring Incident Flag | Boolean | Pattern detection | 🟡 HIGH |
| Knowledge Base Article Used | Text/ID | KB effectiveness | 🟡 HIGH |
| Knowledge Base Article Created | Text/ID | Knowledge capture | 🟢 MEDIUM |
| Similar Ticket References | Text/IDs | Pattern matching | 🟢 MEDIUM |
| Pattern/Trend Category | Text | Automation opportunity | 🟡 HIGH |

### 4. Automation & Self-Service (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Auto-Resolved Flag | Boolean | Automation ROI proof | 🔴 CRITICAL |
| Self-Service Portal Used | Boolean | Portal adoption tracking | 🟢 MEDIUM |
| Automation Runbook Executed | Text/ID | Runbook effectiveness | 🟡 HIGH |
| Manual Intervention Required | Boolean | Automation success rate | 🟡 HIGH |
| Automation Candidate Flag | Boolean | Opportunity pipeline | 🟢 MEDIUM |
| Repetitive Pattern Score | Integer | Auto-detection scoring | 🟢 MEDIUM |

### 5. Workload & Capacity Planning (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Engineer Workload Score | Integer | Load balancing | 🟡 HIGH |
| Team Capacity Utilization % | Decimal | Capacity planning | 🟡 HIGH |
| Peak Hours/Days Analysis | Calculated | Staffing optimization | 🟢 MEDIUM |
| Concurrent Open Tickets | Integer | Burnout prevention | 🟡 HIGH |
| Engineer Shift/Availability | Text | Resource planning | 🟢 MEDIUM |
| After-Hours Flag | Boolean | After-hours tracking | 🟢 MEDIUM |

### 6. Financial & Billing (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Billable/Non-Billable | Boolean | Already in timesheets, add to tickets | 🔴 CRITICAL |
| Billing Rate | Decimal | Cost calculation | 🟡 HIGH |
| Actual Cost | Decimal | hours × rate | 🟡 HIGH |
| Budget Code | Text | Budget tracking | 🟢 MEDIUM |
| Contract Type | Enum | T&M/Fixed/Managed | 🟢 MEDIUM |
| SLA Penalty Amount | Decimal | Financial impact | 🔵 LOW |

### 7. Quality & Compliance (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Peer Review Completed | Boolean | Quality assurance | 🟢 MEDIUM |
| Documentation Quality Score | Integer (1-5) | Doc compliance | 🟢 MEDIUM |
| Solution Accuracy | Boolean | Customer verified | 🟡 HIGH |
| Compliance Check Passed | Boolean | Process adherence | 🟢 MEDIUM |
| Change Approval Status | Text | Change management | 🟢 MEDIUM |
| Post-Implementation Review | Boolean | PIR completion | 🔵 LOW |

### 8. Collaboration & Handoffs (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Number of Internal Updates | Integer | Communication tracking | 🟢 MEDIUM |
| Number of Customer Updates | Integer | Customer engagement | 🟡 HIGH |
| Vendor/Third-Party Involved | Boolean | Vendor tracking | 🟡 HIGH |
| Vendor Name | Text | Vendor performance | 🟡 HIGH |
| Vendor Response Time | Integer | Vendor SLA | 🟢 MEDIUM |
| Waiting Time | Integer | Bottleneck detection | 🟡 HIGH |

*Note: Comments table can provide many of these*

### 9. Agent Performance Metrics (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Engineer Skill Level | Enum | Junior/Mid/Senior | 🟡 HIGH |
| Engineer Specialization Tags | Text | Skill-based routing | 🟡 HIGH |
| Training Completed Date | Date | Training ROI | 🟢 MEDIUM |
| Certification Level | Text | Skill verification | 🟢 MEDIUM |
| Peer Rating | Integer (1-5) | 360 feedback | 🔵 LOW |
| Manager Rating | Integer (1-5) | Performance review | 🔵 LOW |

### 10. Technical Infrastructure (6 fields)

| Field | Type | Purpose | Priority |
|-------|------|---------|----------|
| Technology Stack | Enum | Azure/M365/Network/Security | 🟡 HIGH |
| Service Component | Text | VM/Database/Network/App | 🟡 HIGH |
| Environment | Enum | Production/UAT/Dev | 🟡 HIGH |
| Configuration Item Details | Text | Asset tracking | 🔴 CRITICAL |
| Change Request Link | Text/ID | Change correlation | 🟢 MEDIUM |
| Monitoring Alert ID | Text/ID | Alert correlation | 🟡 HIGH |

*Note: TKT-Related CI exists but 0.0% populated - enforce usage!*

---

## Existing Field Issues

### 1. Related CI (Configuration Item) - 0.0% Populated
- **Status**: Field exists, not used
- **Impact**: No asset failure tracking
- **Solution**: Enforce population, provide training
- **Priority**: 🔴 CRITICAL

### 2. Parent ID - 2.2% Populated
- **Status**: Rarely used
- **Impact**: Cannot track incident relationships
- **Solution**: Enforce for related incidents
- **Priority**: 🟡 HIGH

### 3. Job#/Ref# - 13.2% Populated
- **Status**: Inconsistent usage
- **Impact**: External reference tracking incomplete
- **Solution**: Standardize usage policy
- **Priority**: 🟢 MEDIUM

### 4. SLA Breach Comment - 2.1% Populated
- **Status**: Not consistently documented
- **Impact**: Root cause of breaches unclear
- **Solution**: Make mandatory on SLA breach
- **Priority**: 🟡 HIGH

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1-2)
**6 fields, low effort, immediate value**:
1. ✅ First Call Resolution (Yes/No checkbox)
2. ✅ CSAT Rating (1-5 stars dropdown)
3. ✅ Number of Reassignments (auto-calculated from comments)
4. ✅ Users Affected (integer field)
5. ✅ Auto-Resolved Flag (Yes/No checkbox)
6. ✅ Billable (add to tickets, already in timesheets)

**ROI**: Enables FCR tracking (70-80% target), CSAT measurement, automation proof

### Phase 2: Problem Management (Month 2-3)
**6 fields, medium effort**:
1. Related Problem ID
2. Recurring Incident Flag (auto-detect)
3. Knowledge Base Article Used
4. Escalation Level (L1/L2/L3)
5. Technology Stack (Azure/M365/Network/Security)
6. Environment (Production/UAT/Dev)

**ROI**: Recurring issue detection, KB effectiveness, infrastructure reliability

### Phase 3: Advanced Analytics (Month 4-6)
**6 fields, higher effort**:
1. Customer Impact Level (Minor/Moderate/Major/Critical)
2. Business Function Affected
3. Vendor Involved (Yes/No + vendor name)
4. Engineer Skill Level (Junior/Mid/Senior)
5. Peak Hours Flag (auto-calculated)
6. Concurrent Tickets Count (auto-calculated)

**ROI**: Capacity planning, vendor SLA tracking, skill-based routing

---

## Data Quality Metrics

### Current State

| Metric | Status | Coverage |
|--------|--------|----------|
| Ticket ID uniqueness | ✅ Perfect | 100% |
| Created timestamp | ✅ Perfect | 100% |
| Team assignment | ✅ Perfect | 100% |
| Status tracking | ✅ Perfect | 100% |
| SLA compliance | ✅ Good | 92.8% met |
| Resolution time | ⚠️ Moderate | 53.5% have data |
| Timesheet coverage | ❌ Poor | 33.5% coverage |
| Asset tracking (CI) | ❌ Missing | 0.0% populated |
| FCR tracking | ❌ Missing | Cannot calculate |
| CSAT tracking | ❌ Missing | No field |

### Target State (Post-Implementation)

| Metric | Target | Enabler |
|--------|--------|---------|
| FCR tracking | 70-80% target | Comments table OR FCR field |
| CSAT tracking | >4.0 target | CSAT field added |
| Reassignment rate | <1 avg | Comments table |
| Timesheet coverage | >80% | Process enforcement |
| Asset tracking | >90% | CI field enforcement |
| Cost per ticket | Calculated | Billable field on tickets |

---

## Analysis Capability Matrix

### With Current Data

| Capability | Available | Coverage |
|------------|-----------|----------|
| Alert pattern analysis | ✅ Yes | 8,079 alerts |
| SLA compliance tracking | ✅ Yes | 92.8% compliant |
| Team workload distribution | ✅ Yes | 100% |
| Resolution time trends | ✅ Partial | 53.5% |
| First Call Resolution | ❌ No | Need comments table |
| Customer satisfaction | ❌ No | Need CSAT field |
| Reassignment patterns | ❌ No | Need comments table |
| Cost per ticket | ❌ No | Need billable field |

### With Comments Table Added

| Capability | Status | Impact |
|------------|--------|--------|
| FCR calculation | ✅ Enabled | Core KPI unlocked |
| Reassignment tracking | ✅ Enabled | Skill gap identification |
| Communication quality | ✅ Enabled | Customer engagement metrics |
| Precise response time | ✅ Enabled | Better than current |
| Collaboration patterns | ✅ Enabled | Team efficiency |
| Ticket complexity scoring | ✅ Enabled | Multi-person = complex |

### With Phase 1 Fields Added

| Capability | Status | Impact |
|------------|--------|--------|
| FCR target tracking | ✅ Enabled | 70-80% benchmark |
| CSAT measurement | ✅ Enabled | >4.0 target |
| Automation ROI proof | ✅ Enabled | $167K validated |
| Impact-based prioritization | ✅ Enabled | Users affected weighting |
| Cost per ticket | ✅ Enabled | Profitability analysis |
| Complete ServiceDesk analytics | ✅ Enabled | Industry-standard reporting |

---

## Request Template

### For Comments Table Export

**To**: ServiceDesk System Administrator
**Subject**: Request for Comments Table Export

**Request**: Please export the comments/notes table for tickets created July-Sept 2025.

**Required Fields** (Priority Order):
1. 🔴 ticketid (link to tickets)
2. 🔴 ownerid (user who wrote comment)
3. 🔴 createdtime (timestamp)
4. 🟡 ownertype (agent/customer)
5. 🟡 visible_to_customer (public/internal flag)
6. 🟡 type (comment/system/worknote)
7. 🟢 comments (text - optional if size issue)

**Expected Volume**: ~80,000 rows
**File Format**: CSV preferred
**Purpose**: Enable First Call Resolution tracking and reassignment analysis

### For New Fields Implementation

**Phase 1 Fields** (Quick Wins - 1-2 weeks):
1. First Call Resolution (Boolean) - Add to closure form
2. CSAT Rating (1-5 integer) - Add to closure email
3. Number of Users Affected (Integer) - Add to ticket form
4. Auto-Resolved Flag (Boolean) - Add to ticket template
5. Billable (Boolean) - Add to tickets (already in timesheets)
6. Reassignment Count (Integer) - Auto-calculate from comments

---

## Success Criteria

### Data Quality Targets

**3 Months Post-Implementation**:
- FCR rate visible: Target 70-80%
- CSAT tracked: Target >4.0
- Timesheet coverage: Target >80% (up from 33.5%)
- Related CI populated: Target >90% (up from 0.0%)
- Comments table: 100% coverage for new tickets

### Analytics Capability Targets

**6 Months Post-Implementation**:
- Core KPIs dashboard live (FCR, CSAT, SLA, AHT)
- Automation ROI reporting ($167K tracked)
- Team performance benchmarking
- Customer impact prioritization
- Problem management maturity (recurring issue tracking)

---

*Last Updated: 2025-10-05 by Maia Data Analyst Agent*
