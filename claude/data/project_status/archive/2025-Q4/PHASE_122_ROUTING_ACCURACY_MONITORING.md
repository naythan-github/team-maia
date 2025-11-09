# Phase 122: Routing Accuracy Monitoring System

**Status**: UP NEXT
**Priority**: HIGH
**Estimated Time**: 8-12 hours
**Dependencies**: Phase 121 (Automatic Agent Routing)

---

## Executive Summary

Build automated monitoring system to track Phase 121 routing suggestion accuracy, agent acceptance rates, and identify patterns where coordinator recommendations are overridden. Enables data-driven optimization of intent classification and agent selection algorithms.

---

## Problem Statement

Phase 121 automatic agent routing is operational but we have no visibility into:
- **Accuracy**: Are routing suggestions correct? (accepted by Maia vs overridden)
- **Patterns**: Which query types have high/low accuracy?
- **Agent Fit**: Are suggested agents actually optimal for queries?
- **Improvement**: How to refine intent classification and agent selection?

Without accuracy monitoring, we're flying blind on routing effectiveness.

---

## Success Criteria

1. ✅ Track routing suggestion acceptance rate (target: >80%)
2. ✅ Identify query patterns with low accuracy (<60%)
3. ✅ Measure agent selection precision (suggested vs actually used)
4. ✅ Generate weekly accuracy reports with improvement recommendations
5. ✅ Dashboard showing real-time accuracy metrics

---

## Technical Design

### Architecture

```
User Query
    ↓
Coordinator suggests agents (logged)
    ↓
Maia accepts or overrides (logged)
    ↓
Actual agents used (logged)
    ↓
Accuracy Calculator
    ↓
Metrics Database
    ↓
Accuracy Dashboard
```

### Data Schema

**routing_decisions.db** (SQLite):

```sql
CREATE TABLE routing_suggestions (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    query TEXT,
    query_hash TEXT,

    -- Intent classification
    intent_category TEXT,
    intent_domains TEXT, -- JSON array
    complexity INTEGER,
    confidence FLOAT,

    -- Coordinator suggestion
    suggested_agents TEXT, -- JSON array
    suggested_strategy TEXT, -- single_agent, swarm, chain
    suggestion_reasoning TEXT,

    -- Actual execution
    accepted BOOLEAN, -- Did Maia accept suggestion?
    actual_agents TEXT, -- JSON array of agents actually used
    override_reason TEXT, -- Why was suggestion overridden?

    -- Outcome
    execution_success BOOLEAN,
    execution_time_ms FLOAT,
    user_satisfaction INTEGER -- 1-5 scale (future: user feedback)
);

CREATE TABLE accuracy_metrics (
    id INTEGER PRIMARY KEY,
    date DATE,
    total_suggestions INTEGER,
    accepted_count INTEGER,
    override_count INTEGER,
    acceptance_rate FLOAT,

    -- By category
    technical_accuracy FLOAT,
    strategic_accuracy FLOAT,
    operational_accuracy FLOAT,

    -- By complexity
    simple_accuracy FLOAT, -- complexity 1-3
    medium_accuracy FLOAT, -- complexity 4-7
    complex_accuracy FLOAT -- complexity 8-10
);

CREATE TABLE override_patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT, -- domain_mismatch, complexity_error, etc.
    count INTEGER,
    example_query TEXT,
    suggested_agents TEXT,
    actual_agents TEXT,
    improvement_suggestion TEXT
);
```

---

## Implementation Plan

### Week 1: Data Collection Infrastructure (4 hours)

**Task 1.1: Routing Decision Logger** (2 hours)
- Create `routing_decision_logger.py`
- Log all coordinator suggestions with full context
- Log Maia's actual agent usage
- Detect accepts vs overrides via agent comparison
- Store in SQLite database

**Task 1.2: Integration with Coordinator** (1 hour)
- Modify `coordinator_agent.py` to log suggestions
- Add logging hooks to agent execution paths
- Capture override reasons when available

**Task 1.3: Acceptance Detection** (1 hour)
- Compare suggested_agents vs actual_agents
- Fuzzy matching (e.g., "azure_architect" vs "Azure Architect Agent")
- Detect partial matches (1 of 2 suggested agents used)

### Week 2: Accuracy Analysis Engine (4 hours)

**Task 2.1: Accuracy Calculator** (2 hours)
- `accuracy_analyzer.py`
- Calculate overall acceptance rate
- Break down by category, complexity, domain
- Identify low-accuracy patterns

**Task 2.2: Pattern Recognition** (1 hour)
- Detect common override patterns
- Group similar overrides (e.g., "always overrides financial queries")
- Generate improvement suggestions

**Task 2.3: Weekly Report Generator** (1 hour)
- `weekly_accuracy_report.py`
- Summary statistics
- Top override patterns
- Improvement recommendations
- Email/Slack delivery (future)

### Week 3: Accuracy Dashboard (3 hours)

**Task 3.1: Web Dashboard** (2 hours)
- Add accuracy section to agent performance dashboard
- Real-time acceptance rate gauge
- Accuracy trends over time (chart)
- Override patterns table

**Task 3.2: API Endpoints** (1 hour)
- `/api/accuracy` - Current metrics
- `/api/accuracy/trends` - Historical data
- `/api/overrides` - Override patterns

### Week 4: Optimization Loop (1 hour)

**Task 4.1: Feedback Integration**
- Use accuracy data to improve intent classification
- Adjust agent selection thresholds
- Update domain keyword mappings
- Document optimization process

---

## Deliverables

### Code Components
1. **routing_decision_logger.py** (200 lines)
   - Logs all routing decisions and outcomes
   - SQLite database management
   - Acceptance detection logic

2. **accuracy_analyzer.py** (250 lines)
   - Calculate acceptance rates
   - Pattern recognition
   - Statistical analysis

3. **weekly_accuracy_report.py** (150 lines)
   - Generate weekly reports
   - Improvement recommendations
   - Trend analysis

4. **Accuracy Dashboard Section** (200 lines)
   - Real-time metrics
   - Historical trends
   - Override patterns visualization

### Databases
- **routing_decisions.db** - All routing decisions and outcomes
- **accuracy_metrics.db** - Aggregated accuracy statistics

### Documentation
- **Accuracy Monitoring Guide** - How to interpret metrics
- **Optimization Playbook** - How to use data to improve routing

---

## Success Metrics

### Immediate (Week 1-2)
- Data collection: 100% of routing decisions logged
- Database: All suggestions and outcomes captured
- Acceptance detection: >95% accuracy in detecting accepts vs overrides

### Short-term (Month 1)
- Acceptance rate baseline established
- Low-accuracy patterns identified (target: find 3-5 patterns)
- First optimization implemented based on data

### Long-term (Month 2-3)
- Acceptance rate improvement: +10-15% from baseline
- Override patterns: Reduced by 30%
- Quality improvement: Measurable +10-15% from better routing

---

## Example Metrics

### Weekly Accuracy Report (Example)

```
📊 Routing Accuracy Report - Week of Oct 15-21, 2025

Overall Metrics:
- Total Suggestions: 245
- Accepted: 198 (80.8%)
- Overridden: 47 (19.2%)

By Category:
- Technical: 87.3% accuracy ✅
- Strategic: 71.2% accuracy ⚠️
- Operational: 89.5% accuracy ✅

Top Override Patterns:
1. Financial queries → Suggested Financial Advisor, used Azure Architect (12 instances)
   Improvement: Add "cost" keyword to Azure domain

2. Complex multi-domain → Suggested single agent, used swarm (8 instances)
   Improvement: Lower complexity threshold for swarm strategy (7 → 6)

3. Security reviews → Suggested Cloud Security, used Code Security (6 instances)
   Improvement: Disambiguate "code review" vs "cloud review"

Recommended Actions:
✅ Implement keyword mapping updates (1 hour)
✅ Adjust swarm threshold (15 minutes)
✅ Add security domain clarification (30 minutes)
```

---

## Risk Mitigation

### Risk 1: False Positives in Override Detection
**Mitigation**: Manual validation of first 50 decisions to calibrate detection logic

### Risk 2: Privacy Concerns with Query Logging
**Mitigation**: Hash queries for pattern matching, don't log sensitive content

### Risk 3: Data Volume Growth
**Mitigation**: Retention policy (keep raw data 30 days, aggregates forever)

---

## Integration Points

- **Phase 121**: Coordinator Agent (add logging hooks)
- **Performance Monitoring**: Share database for unified metrics
- **Agent Performance Dashboard**: Add accuracy section
- **Weekly Review**: Include accuracy report in weekly briefing

---

## Future Enhancements

- **User Feedback**: Explicit thumbs up/down on routing suggestions
- **A/B Testing**: Test intent classification algorithm variants
- **ML Optimization**: Train model on acceptance patterns
- **Confidence Calibration**: Adjust confidence scores based on accuracy

---

## Estimated ROI

**Investment**: 12 hours development + 2 hours/week monitoring

**Return**:
- Routing accuracy improvement: 80% → 90% (+10%)
- Quality improvement from better routing: +5-10% (on top of +25-40% from Phase 121)
- Time saved from fewer routing mistakes: 30 min/week
- Compounding benefit: Better routing = better agent learning

**Payback**: Immediate (accuracy visibility alone valuable), full ROI in 4-6 weeks

---

## Status: READY FOR IMPLEMENTATION

All dependencies met. Phase 121 operational. Can start Week 1 immediately.
