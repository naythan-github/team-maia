# ServiceDesk Operations Intelligence Database - Project Plan

**Project Code**: SDM-OPS-INTEL-001
**Created**: 2025-10-18
**Status**: APPROVED - Ready for Implementation
**Owner**: Service Desk Manager Agent + SRE Principal Engineer Agent
**Estimated Effort**: 6-8 hours implementation

---

## 🎯 Project Overview

**Purpose**: Build dedicated operational intelligence system for ServiceDesk Manager Agent to remember insights, track recommendations, measure outcomes, and continuously improve service delivery.

**Problem Solved**:
- Context amnesia: Agent forgets past analyses across conversation resets
- No institutional memory: Repeated analysis of same problems
- Missing feedback loop: Can't learn which interventions work
- No evidence base: Recommendations not backed by proven patterns

**Success Criteria**:
1. ✅ Remember all insights + recommendations across sessions
2. ✅ Track outcomes (FCR improvement, escalation reduction, CSAT increase)
3. ✅ Enable learning ("Azure training worked in Q3 → recommend for AWS")
4. ✅ Provide evidence-based recommendations

---

## 🗄️ Database Schema Design

### **Core Architecture**: 6 Tables (SQLite)

**Database Location**: `~/git/maia/claude/data/servicedesk_operations_intelligence.db`

---

### **Table 1: operational_insights**
**Purpose**: Record identified problems/patterns from analysis

```sql
CREATE TABLE operational_insights (
    insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type TEXT NOT NULL, -- complaint_pattern, escalation_bottleneck, fcr_opportunity, skill_gap, client_at_risk
    title TEXT NOT NULL,
    description TEXT,
    identified_date TEXT NOT NULL,
    severity TEXT, -- critical, high, medium, low
    affected_clients TEXT, -- JSON array: ["Acme Corp", "Beta Inc"]
    affected_categories TEXT, -- JSON array: ["Azure", "M365", "Exchange"]
    affected_ticket_ids TEXT, -- JSON array: [12345, 12346, 12347]
    root_cause TEXT, -- 5-Whys analysis result
    business_impact TEXT, -- e.g., "$180K contract at risk", "SLA breaches"
    status TEXT DEFAULT 'active', -- active, resolved, monitoring, archived
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_insights_type ON operational_insights(insight_type);
CREATE INDEX idx_insights_status ON operational_insights(status);
CREATE INDEX idx_insights_date ON operational_insights(identified_date);
```

**Example Record**:
```json
{
  "insight_id": 1,
  "insight_type": "escalation_bottleneck",
  "title": "Azure hybrid tickets have 70% escalation rate",
  "description": "Exchange hybrid tickets require excessive Microsoft support escalations due to L2 knowledge gap",
  "identified_date": "2025-10-18",
  "severity": "high",
  "affected_clients": "[\"Client A\", \"Client B\", \"Client C\"]",
  "affected_categories": "[\"Exchange\", \"M365\"]",
  "affected_ticket_ids": "[12345, 12346, 12350, 12355]",
  "root_cause": "L2 team lacks Exchange hybrid troubleshooting training → excessive Microsoft escalations → 5.2 avg handoffs",
  "business_impact": "70% escalation rate (4.7x baseline), avg 18h resolution vs 6h target",
  "status": "active"
}
```

---

### **Table 2: recommendations**
**Purpose**: Track recommended interventions with effort/impact estimates

```sql
CREATE TABLE recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    recommendation_type TEXT NOT NULL, -- training, process_change, staffing, tooling, knowledge_base, skill_routing, customer_communication
    title TEXT NOT NULL,
    description TEXT,
    estimated_effort TEXT, -- e.g., "2 weeks", "4 hours", "1 month"
    estimated_impact TEXT, -- e.g., "Reduce escalation rate from 70% to 30%"
    priority TEXT, -- critical, high, medium, low
    status TEXT DEFAULT 'proposed', -- proposed, approved, in_progress, completed, abandoned
    assigned_to TEXT, -- Person/team responsible
    due_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES operational_insights(insight_id)
);

CREATE INDEX idx_recommendations_insight ON recommendations(insight_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_recommendations_priority ON recommendations(priority);
```

**Example Record**:
```json
{
  "recommendation_id": 1,
  "insight_id": 1,
  "recommendation_type": "training",
  "title": "Exchange Hybrid Training for L2 Team",
  "description": "4-hour Microsoft Exchange hybrid troubleshooting training for L2 team (Rachel S., Tom K.)",
  "estimated_effort": "1 week to schedule + deliver",
  "estimated_impact": "Reduce Exchange escalation rate from 70% to 30%, improve resolution time from 18h to 8h",
  "priority": "high",
  "status": "approved",
  "assigned_to": "Training Coordinator",
  "due_date": "2025-10-25"
}
```

---

### **Table 3: actions_taken**
**Purpose**: Log actual interventions performed

```sql
CREATE TABLE actions_taken (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- ticket_assignment, customer_communication, training_session, kb_article, process_update, tool_implementation
    action_date TEXT NOT NULL,
    performed_by TEXT,
    details TEXT,
    ticket_ids TEXT, -- JSON array of affected tickets
    artifacts TEXT, -- JSON: {"kb_url": "...", "email_sent": true, "training_attendance": 8}
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
);

CREATE INDEX idx_actions_recommendation ON actions_taken(recommendation_id);
CREATE INDEX idx_actions_date ON actions_taken(action_date);
```

**Example Record**:
```json
{
  "action_id": 1,
  "recommendation_id": 1,
  "action_type": "training_session",
  "action_date": "2025-10-20",
  "performed_by": "Training Coordinator",
  "details": "Delivered 4-hour Exchange Hybrid troubleshooting training. Topics: mailbox migration, hybrid authentication, mail flow troubleshooting, common issues.",
  "artifacts": "{\"attendance\": 8, \"materials_url\": \"https://confluence/training/exchange-hybrid\", \"quiz_avg_score\": 85}"
}
```

---

### **Table 4: outcomes**
**Purpose**: Measure impact of recommendations over time

```sql
CREATE TABLE outcomes (
    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id INTEGER NOT NULL,
    measurement_date TEXT NOT NULL,
    metric_type TEXT NOT NULL, -- fcr_rate, escalation_rate, csat_score, resolution_time_avg, sla_compliance, client_complaints
    baseline_value REAL, -- Value before intervention
    current_value REAL, -- Value after intervention
    improvement_pct REAL, -- Calculated: ((current - baseline) / baseline) * 100
    target_value REAL, -- Original goal
    measurement_period TEXT, -- e.g., "30 days post-training", "Q4 2025"
    sample_size INTEGER, -- Number of tickets/interactions measured
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
);

CREATE INDEX idx_outcomes_recommendation ON outcomes(recommendation_id);
CREATE INDEX idx_outcomes_metric ON outcomes(metric_type);
CREATE INDEX idx_outcomes_date ON outcomes(measurement_date);
```

**Example Record**:
```json
{
  "outcome_id": 1,
  "recommendation_id": 1,
  "measurement_date": "2025-11-20",
  "metric_type": "escalation_rate",
  "baseline_value": 70.0,
  "current_value": 28.0,
  "improvement_pct": -60.0,
  "target_value": 30.0,
  "measurement_period": "30 days post-training",
  "sample_size": 45,
  "notes": "Exceeded target! Exchange hybrid escalation rate dropped from 70% to 28% (45 tickets measured). Training highly effective."
}
```

---

### **Table 5: patterns**
**Purpose**: Track recurring patterns for proactive detection

```sql
CREATE TABLE patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL, -- recurring_complaint, escalation_hotspot, client_at_risk, seasonal_spike, technician_bottleneck
    pattern_description TEXT NOT NULL,
    first_observed TEXT NOT NULL,
    last_observed TEXT NOT NULL,
    frequency TEXT, -- e.g., "Weekly", "Monthly", "Quarterly"
    occurrence_count INTEGER DEFAULT 1,
    related_insights TEXT, -- JSON array of insight_ids
    related_tickets TEXT, -- JSON array of ticket_ids
    trigger_conditions TEXT, -- e.g., "Exchange hybrid tickets from specific clients"
    status TEXT DEFAULT 'active', -- active, resolved, monitoring
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_status ON patterns(status);
```

**Example Record**:
```json
{
  "pattern_id": 1,
  "pattern_type": "escalation_hotspot",
  "pattern_description": "Exchange hybrid tickets consistently escalate to Microsoft support",
  "first_observed": "2025-07-15",
  "last_observed": "2025-10-18",
  "frequency": "Weekly",
  "occurrence_count": 15,
  "related_insights": "[1, 3, 7]",
  "related_tickets": "[12345, 12346, 12350, 12355, ...]",
  "trigger_conditions": "Category=Exchange AND Description contains 'hybrid'",
  "status": "resolved"
}
```

---

### **Table 6: learning_log**
**Purpose**: Capture institutional knowledge ("what worked, what didn't, why")

```sql
CREATE TABLE learning_log (
    learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER,
    recommendation_id INTEGER,
    learning_type TEXT, -- success, partial_success, failure, unexpected_outcome
    what_worked TEXT,
    what_didnt_work TEXT,
    why_analysis TEXT, -- Root cause of success/failure
    confidence_before REAL, -- 0-100: How confident were we in recommendation?
    confidence_after REAL, -- 0-100: How confident are we now?
    would_recommend_again BOOLEAN,
    similar_situations TEXT, -- When to apply this learning
    tags TEXT, -- JSON array: ["training", "exchange", "escalation_reduction"]
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insight_id) REFERENCES operational_insights(insight_id),
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
);

CREATE INDEX idx_learning_type ON learning_log(learning_type);
CREATE INDEX idx_learning_tags ON learning_log(tags);
```

**Example Record**:
```json
{
  "learning_id": 1,
  "insight_id": 1,
  "recommendation_id": 1,
  "learning_type": "success",
  "what_worked": "4-hour focused training on Exchange hybrid troubleshooting with hands-on labs and real ticket examples",
  "what_didnt_work": "N/A - training exceeded expectations",
  "why_analysis": "Hands-on approach + real ticket examples made training immediately applicable. Team members could apply learnings same day.",
  "confidence_before": 75,
  "confidence_after": 95,
  "would_recommend_again": true,
  "similar_situations": "Any category with >50% escalation rate due to knowledge gap. Hands-on training > theory for technical skills.",
  "tags": "[\"training_effectiveness\", \"exchange\", \"escalation_reduction\", \"hands_on_learning\"]"
}
```

---

## 🛠️ CLI Tool Design

**Tool Name**: `servicedesk_operations_intelligence.py`
**Location**: `~/git/maia/claude/tools/sre/servicedesk_operations_intelligence.py`

### **Command Structure**:

```bash
# Add new insight
python3 servicedesk_operations_intelligence.py add-insight \
  --type escalation_bottleneck \
  --title "Azure tickets have 70% escalation rate" \
  --severity high \
  --clients "Acme Corp,Beta Inc" \
  --categories "Azure,M365" \
  --root-cause "L2 team lacks Azure hybrid training"

# Record recommendation
python3 servicedesk_operations_intelligence.py add-recommendation \
  --insight-id 1 \
  --type training \
  --title "Azure Hybrid Training for L2" \
  --effort "1 week" \
  --impact "Reduce escalation 70% → 30%" \
  --priority high \
  --assigned-to "Training Coordinator"

# Log action taken
python3 servicedesk_operations_intelligence.py log-action \
  --rec-id 1 \
  --type training_session \
  --date 2025-10-20 \
  --performed-by "Training Coordinator" \
  --details "4-hour Azure hybrid training, 8 attendees"

# Track outcome
python3 servicedesk_operations_intelligence.py track-outcome \
  --rec-id 1 \
  --metric escalation_rate \
  --baseline 70 \
  --current 28 \
  --target 30 \
  --period "30 days post-training" \
  --sample-size 45

# Record learning
python3 servicedesk_operations_intelligence.py add-learning \
  --rec-id 1 \
  --type success \
  --what-worked "Hands-on training with real ticket examples" \
  --confidence-before 75 \
  --confidence-after 95 \
  --would-repeat true

# Query past work
python3 servicedesk_operations_intelligence.py search "Azure escalation"
python3 servicedesk_operations_intelligence.py show-insights --status active
python3 servicedesk_operations_intelligence.py show-recommendations --priority high
python3 servicedesk_operations_intelligence.py show-learning --tags training
python3 servicedesk_operations_intelligence.py show-outcomes --metric escalation_rate

# Dashboard/Reports
python3 servicedesk_operations_intelligence.py dashboard
python3 servicedesk_operations_intelligence.py monthly-report --month 2025-10
```

---

## 🔄 Integration with SDM Agent Workflow

### **Automated Intelligence Capture**:

**During Complaint Analysis**:
```python
# SDM Agent identifies pattern
insight_id = ops_intel.add_insight(
    insight_type="complaint_pattern",
    title="Exchange hybrid tickets slow",
    severity="high",
    affected_clients=["Acme Corp", "Beta Inc"],
    root_cause="L2 lacks Exchange hybrid training → Microsoft escalations"
)

# SDM Agent generates recommendations
rec_id = ops_intel.add_recommendation(
    insight_id=insight_id,
    rec_type="training",
    title="Exchange Hybrid Training",
    estimated_impact="Reduce escalation 70% → 30%",
    priority="high"
)
```

**During Follow-up (30 days later)**:
```python
# SDM Agent measures outcome
ops_intel.track_outcome(
    recommendation_id=rec_id,
    metric_type="escalation_rate",
    baseline_value=70.0,
    current_value=28.0,
    measurement_period="30 days post-training"
)

# SDM Agent records learning
ops_intel.add_learning(
    recommendation_id=rec_id,
    learning_type="success",
    what_worked="Hands-on training exceeded expectations",
    confidence_after=95,
    would_recommend_again=True
)
```

---

## 📊 Expected Benefits

### **Immediate Benefits** (Week 1):
- ✅ Zero context amnesia: All insights persist across conversations
- ✅ Resume work instantly: "What insights do we have about Azure?" → instant answer
- ✅ Avoid duplicate analysis: Check existing insights before re-analyzing

### **Short-term Benefits** (Month 1):
- ✅ Evidence-based recommendations: "Training worked for Exchange (60% improvement) → recommend for AWS"
- ✅ Track implementation: Know which recommendations are in-progress vs completed
- ✅ Measure ROI: Prove value of data-driven operations with metrics

### **Long-term Benefits** (Quarter 1):
- ✅ Continuous improvement: Learning log builds institutional knowledge
- ✅ Pattern recognition: "Similar complaint patterns detected → proactive intervention"
- ✅ Predictive insights: "Client X showing early warning signs based on past patterns"

---

## 🎯 Implementation Plan

### **Phase 1: Core Database (2-3 hours)** - SRE Agent
- [ ] Design and validate schema (6 tables)
- [ ] Create database with indexes
- [ ] Add sample data for testing
- [ ] Performance benchmarks (query speed)

### **Phase 2: CLI Tool (3-4 hours)** - SRE Agent
- [ ] Build CLI interface (add, search, show commands)
- [ ] Implement CRUD operations for all tables
- [ ] Add query/search functionality
- [ ] Build simple dashboard/reporting

### **Phase 3: SDM Agent Integration (1-2 hours)** - SDM Agent
- [ ] Import ops intelligence tool into SDM workflow
- [ ] Auto-capture insights during analysis
- [ ] Auto-generate recommendations
- [ ] Track outcomes during follow-up

### **Phase 4: Bootstrap with Historical Data (1 hour)** - SDM Agent
- [ ] Populate with October 2025 insights from upcoming analysis
- [ ] Add known patterns (Exchange hybrid, Azure escalations)
- [ ] Record past recommendations (if any)

---

## ✅ Success Metrics

**Week 1**:
- Database operational with 5+ insights captured
- CLI commands working (add, search, show)
- SDM Agent successfully captures first insight

**Month 1**:
- 20+ insights tracked
- 15+ recommendations with outcomes
- First learning log entries ("training worked because...")
- Monthly report generated

**Quarter 1**:
- 50+ insights with trend analysis
- Proven ROI: 3+ recommendations with measurable improvements
- Pattern recognition: 5+ recurring patterns identified
- Evidence-based operations: All recommendations backed by data

---

**Status**: APPROVED - Proceeding to implementation with SRE Principal Engineer Agent
**Next Step**: Load SRE Agent for Phase 1-2 implementation
